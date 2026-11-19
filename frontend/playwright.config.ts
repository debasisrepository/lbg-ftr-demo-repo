import { defineConfig, devices } from '@playwright/test'
import { existsSync } from 'fs'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'

/**
 * Playwright configuration for E2E tests
 * See https://playwright.dev/docs/test-configuration
 */

const __dirname = dirname(fileURLToPath(import.meta.url))

// Determine the Python executable from venv
function getPythonPath(): string {
  const backendDir = join(__dirname, '..', 'backend')
  const windowsPath = join(backendDir, '.venv', 'Scripts', 'python.exe')
  const unixPath = join(backendDir, '.venv', 'bin', 'python')
  
  if (existsSync(windowsPath)) {
    return windowsPath
  } else if (existsSync(unixPath)) {
    return unixPath
  }
  
  // Fallback to system python
  return process.env.E2E_PYTHON ?? 'python'
}

export default defineConfig({
  testDir: './src/e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: 'html',
  timeout: Number(process.env.E2E_TEST_TIMEOUT ?? 30_000),

  use: {
    baseURL: `http://127.0.0.1:${process.env.E2E_FRONTEND_PORT ?? '5173'}`,
    trace: 'on-first-retry',
    actionTimeout: Number(process.env.E2E_ACTION_TIMEOUT ?? 10_000),
    navigationTimeout: Number(process.env.E2E_NAVIGATION_TIMEOUT ?? 15_000),
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  webServer: [
    // Backend server
    {
      command: (() => {
        const python = getPythonPath()
        const backendPort = process.env.E2E_BACKEND_PORT ?? '9000'
        const backendDir = join(__dirname, '..', 'backend')
        
        return `cd "${backendDir}" && "${python}" -m alembic upgrade head && "${python}" -m app.seed && "${python}" -m uvicorn app.main:app --host 127.0.0.1 --port ${backendPort}`
      })(),
      url: `http://127.0.0.1:${process.env.E2E_BACKEND_PORT ?? '9000'}/api/v1/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 180_000,
      stdout: 'pipe',
      stderr: 'pipe',
      env: {
        DATABASE_URL: process.env.E2E_DATABASE_URL ?? 'sqlite:///./e2e.db',
      },
    },
    // Frontend dev server
    {
      command: `npm run dev -- --host 127.0.0.1 --port ${process.env.E2E_FRONTEND_PORT ?? '5173'} --strictPort`,
      url: `http://127.0.0.1:${process.env.E2E_FRONTEND_PORT ?? '5173'}`,
      reuseExistingServer: !process.env.CI,
      timeout: 180_000,
      stdout: 'pipe',
      stderr: 'pipe',
      env: {
        BACKEND_PORT: process.env.E2E_BACKEND_PORT ?? '9000',
      },
    },
  ],
})

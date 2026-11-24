import { defineConfig, devices } from '@playwright/test'

const E2E_BACKEND_PORT = process.env.E2E_BACKEND_PORT ?? '9000'
const E2E_FRONTEND_PORT = process.env.E2E_FRONTEND_PORT ?? '5173'
const E2E_PYTHON = process.env.E2E_PYTHON ?? 'python'
const E2E_DATABASE_URL = process.env.E2E_DATABASE_URL ?? 'sqlite:///./e2e_test.db'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: 'list',
  timeout: Number(process.env.E2E_TEST_TIMEOUT ?? 30_000),
  use: {
    baseURL: `http://127.0.0.1:${E2E_FRONTEND_PORT}`,
    trace: 'on-first-retry',
    actionTimeout: Number(process.env.E2E_ACTION_TIMEOUT ?? 10_000),
    navigationTimeout: Number(process.env.E2E_NAVIGATION_TIMEOUT ?? 15_000),
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  webServer: [
    {
      // Backend: install dependencies, delete old db, migrate, seed, start uvicorn
      command: `cd ../backend && ([ -d .venv ] || ${E2E_PYTHON} -m venv .venv) && .venv/bin/python -m pip install -q -e . && rm -f e2e_test.db && .venv/bin/python -m alembic upgrade head && .venv/bin/python app/cli.py seed && .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port ${E2E_BACKEND_PORT}`,
      url: `http://127.0.0.1:${E2E_BACKEND_PORT}/health`,
      reuseExistingServer: !!process.env.E2E_REUSE_SERVER,
      timeout: 180_000,
      stdout: 'pipe',
      stderr: 'pipe',
      env: {
        DATABASE_URL: E2E_DATABASE_URL,
      },
    },
    {
      // Frontend: dev server with backend proxy
      command: `npm run dev -- --host 127.0.0.1 --port ${E2E_FRONTEND_PORT} --strictPort`,
      url: `http://127.0.0.1:${E2E_FRONTEND_PORT}`,
      reuseExistingServer: !!process.env.E2E_REUSE_SERVER,
      timeout: 180_000,
      stdout: 'pipe',
      stderr: 'pipe',
      env: {
        BACKEND_PORT: E2E_BACKEND_PORT,
      },
    },
  ],
})

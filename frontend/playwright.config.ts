import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for E2E tests
 * Uses ports from environment variables set by the pipeline
 */
export default defineConfig({
  testDir: './e2e',
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
  },
  
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  
  webServer: [
    {
      command: (() => {
        const python = process.env.E2E_PYTHON ?? 'python';
        const backendPort = process.env.E2E_BACKEND_PORT ?? '9000';
        
        return [
          `cd ../backend`,
          `${python} -m alembic upgrade head`,
          `${python} -m app.seed`,
          `${python} -m uvicorn app.main:app --host 127.0.0.1 --port ${backendPort}`,
        ].join(' && ');
      })(),
      cwd: '../backend',
      port: Number(process.env.E2E_BACKEND_PORT ?? 9000),
      timeout: 180_000,
      reuseExistingServer: !process.env.CI,
      stdout: 'pipe',
      stderr: 'pipe',
      env: {
        DATABASE_URL: process.env.E2E_DATABASE_URL ?? 'sqlite:///./e2e.db',
      },
    },
    {
      command: (() => {
        const frontendPort = process.env.E2E_FRONTEND_PORT ?? '5173';
        
        return `npm run dev -- --host 127.0.0.1 --port ${frontendPort} --strictPort`;
      })(),
      port: Number(process.env.E2E_FRONTEND_PORT ?? 5173),
      timeout: 180_000,
      reuseExistingServer: !process.env.CI,
      stdout: 'pipe',
      stderr: 'pipe',
      env: {
        BACKEND_PORT: process.env.E2E_BACKEND_PORT ?? '9000',
      },
    },
  ],
});

import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for end-to-end tests.
 * Uses environment variables set by the pipeline:
 * - E2E_BACKEND_PORT: Backend server port
 * - E2E_FRONTEND_PORT: Frontend dev server port
 * - E2E_DATABASE_URL: Test database URL
 * - E2E_PYTHON: Python interpreter path
 * - E2E_TEST_TIMEOUT: Test timeout in milliseconds
 * - E2E_ACTION_TIMEOUT: Action timeout in milliseconds
 * - E2E_NAVIGATION_TIMEOUT: Navigation timeout in milliseconds
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
      // Backend server with migrations and seed
      command: 'bash run_e2e_server.sh',
      cwd: '../backend',
      url: `http://127.0.0.1:${process.env.E2E_BACKEND_PORT ?? '9000'}/health`,
      env: {
        DATABASE_URL: process.env.E2E_DATABASE_URL ?? 'sqlite:///./e2e.db',
        SECRET_KEY: 'test-secret-key-for-e2e-testing-min-32-characters',
        JWT_ALGORITHM: 'HS256',
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES: '60',
        JWT_INACTIVITY_TIMEOUT_MINUTES: '15',
        CORS_ORIGINS: `http://127.0.0.1:${process.env.E2E_FRONTEND_PORT ?? '5173'}`,
        RATE_LIMIT_ENABLED: 'false',
        BCRYPT_COST_FACTOR: '12',
        E2E_BACKEND_PORT: process.env.E2E_BACKEND_PORT ?? '9000',
      },
      reuseExistingServer: false,
      timeout: 180_000,
      stdout: 'pipe',
      stderr: 'pipe',
    },
    {
      // Frontend dev server
      command: `npm run dev -- --host 127.0.0.1 --port ${process.env.E2E_FRONTEND_PORT ?? '5173'} --strictPort`,
      url: `http://127.0.0.1:${process.env.E2E_FRONTEND_PORT ?? '5173'}`,
      env: {
        BACKEND_PORT: process.env.E2E_BACKEND_PORT ?? '9000',
      },
      reuseExistingServer: false,
      timeout: 180_000,
      stdout: 'pipe',
      stderr: 'pipe',
    },
  ],
});

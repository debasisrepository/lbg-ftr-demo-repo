import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  // '' loads every variable, including the process environment start.sh sets.
  const env = loadEnv(mode, process.cwd(), '');
  const backendPort = env.BACKEND_PORT || '9000';

  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        // No `rewrite`: the backend mounts its routes under /api, so the path goes through unchanged.
        '/api': {
          target: `http://127.0.0.1:${backendPort}`,
          changeOrigin: true,
        },
      },
    },
  };
});

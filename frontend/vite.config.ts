import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(() => {
  // Read BACKEND_PORT from process environment (set by start.sh)
  const backendPort = process.env.BACKEND_PORT || '9000';
  
  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        // Forward /api to backend without rewriting the path
        '/api': {
          target: `http://127.0.0.1:${backendPort}`,
          changeOrigin: true,
        },
      },
    },
  };
});

import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig(({ mode }) => {
    // Load all env vars including BACKEND_PORT set by start.sh
    const env = loadEnv(mode, process.cwd(), '');
    return {
        plugins: [react()],
        server: {
            port: 5173,
            proxy: {
                // Forward /api to backend without path rewrite
                '/api': {
                    target: `http://127.0.0.1:${env.BACKEND_PORT || 9000}`,
                    changeOrigin: true,
                },
            },
        },
    };
});

import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig(function (_a) {
    var mode = _a.mode;
    // Load all env vars including those set by start.sh
    var env = loadEnv(mode, process.cwd(), '');
    return {
        plugins: [react()],
        server: {
            port: 5173,
            proxy: {
                // Forward /api to backend without rewriting the path
                '/api': {
                    target: "http://127.0.0.1:".concat(env.BACKEND_PORT || 9000),
                    changeOrigin: true,
                },
            },
        },
        test: {
            globals: true,
            environment: 'jsdom',
            setupFiles: './src/test/setup.ts',
            exclude: ['node_modules', 'e2e'],
        },
    };
});

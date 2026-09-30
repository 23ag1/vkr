import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// Proxy target for the /api dev proxy.
// - Local `npm run dev`: defaults to http://localhost:8000 (backend on host).
// - Docker: overridable via VITE_PROXY_TARGET (compose injects the backend
//   container hostname). process.env covers container `environment:` vars;
//   loadEnv covers a local .env file. Neither alone covers both.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_');
  const proxyTarget =
    process.env.VITE_PROXY_TARGET || env.VITE_PROXY_TARGET || 'http://localhost:8000';

  return {
    plugins: [react()],
    server: {
      host: '0.0.0.0',
      port: 5173,
      proxy: {
        '/api': { target: proxyTarget, changeOrigin: true },
      },
    },
  };
});

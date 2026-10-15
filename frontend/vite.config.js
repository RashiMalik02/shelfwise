import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// In dev, `npm run dev` proxies /api to a backend running on :8000 (uvicorn or docker compose).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': process.env.API_PROXY_TARGET || 'http://localhost:8000' },
  },
});

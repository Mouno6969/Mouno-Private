/// <reference types="vitest/config" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// The Flask backend serves the production SPA from `frontend/build`
// (see web_repo/api/main.py), so we keep Vite's output directory as `build`
// instead of the default `dist` to avoid touching the backend.
export default defineConfig({
  plugins: [react()],
  // Re-run dependency pre-bundling on startup to keep the optimizer cache fresh.
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom', 'sonner', 'swr', 'axios'],
  },
  resolve: {
    // Resolve the "@/*" path alias from tsconfig.json natively.
    tsconfigPaths: true,
  },
  server: {
    port: 3000,
    host: true,
    // Proxy API + websocket traffic to the Flask dev server so the SPA can
    // talk to the backend during development without CORS headaches.
    proxy: {
      '/api': {
        target: process.env.VITE_DEV_API_PROXY || 'http://localhost:5001',
        changeOrigin: true,
      },
      '/socket.io': {
        target: process.env.VITE_DEV_API_PROXY || 'http://localhost:5001',
        changeOrigin: true,
        ws: true,
      },
    },
  },
  build: {
    outDir: 'build',
    sourcemap: true,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/setupTests.ts'],
    css: true,
  },
});

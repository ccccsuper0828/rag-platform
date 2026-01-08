import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    headers: {
      "Content-Security-Policy": "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob:;",
    },
    // API 代理 - 连接到 RAG 后端
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/v1': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
    watch: {
      usePolling: true,
      interval: 100,
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
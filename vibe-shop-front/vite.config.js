import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      // Proxy API to Python FastAPI on 8000, strip /api prefix
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      // Serve product images from backend in dev (be specific to avoid clashing with frontend public/images)
      '/images/tees': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})

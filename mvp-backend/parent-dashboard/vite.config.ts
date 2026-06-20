import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Parent web dashboard. Mirrors cms/vite.config.ts: served under a base path,
// dev proxy forwards the API paths we use to the live backend on :8904.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: '/dashboard/',
  server: {
    port: 5174,
    proxy: {
      '/auth': 'http://localhost:8904',
      '/research': 'http://localhost:8904',
      '/cos': 'http://localhost:8904',
      '/content': 'http://localhost:8904',
      '/profile': 'http://localhost:8904',
    },
  },
  build: {
    outDir: 'dist',
  },
})

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: '/cms/',
  server: {
    port: 5173,
    proxy: {
      '/content': 'http://localhost:8904',
      '/cms/articles': 'http://localhost:8904',
      '/cms/community-posts': 'http://localhost:8904',
      '/cms/categories': 'http://localhost:8904',
      '/cms/stats': 'http://localhost:8904',
      '/cms/export-parquet': 'http://localhost:8904',
      '/cms/email-sync': 'http://localhost:8904',
      '/cms/calendar-sync': 'http://localhost:8904',
    },
  },
  build: {
    outDir: 'dist',
  },
})

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://api.mohanish.online',
        changeOrigin: true,
        secure: true,
        credentials: true,
      },
    },
  },
})

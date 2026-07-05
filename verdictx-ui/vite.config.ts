import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      // Proxy all /api requests to the Flask backend
      '/api': {
        target: 'https://verdictx.onrender.com',
        changeOrigin: true,
      },
    },
  },
})

import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // Same-origin in development, so the generated client needs no base URL
    // and no CORS configuration is required on the backend.
    proxy: {
      '/api': 'http://localhost:8080',
      '/v3/api-docs': 'http://localhost:8080',
    },
  },
  test: {
    environment: 'jsdom',
    globals: false,
  },
})

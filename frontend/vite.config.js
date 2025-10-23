import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

 
export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,         // para usar expect, describe, test sin importar importarlos
    environment: 'jsdom',  setupFiles: "./vitest.setup.js",
    css: true, // permite importar css en tests
      // necesario para tests de React
    include: [
      'src/**/*.test.jsx',       // tests actuales
      'tests/**/*.test.jsx'      // tests si los movés a tests/
    ],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],  // consola + HTML
      exclude: [
        'src/main.jsx',
        'src/App.jsx',
        'src/containers/App/HomePage.jsx',
        'src/services/wsService.js'
      ]
    }
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api')
      }
    }
  }
 
})

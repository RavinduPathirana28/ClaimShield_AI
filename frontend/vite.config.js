import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': `${import.meta.dirname}/src`
    }
  },
  build: {
    rolldownOptions: {
      output: {
        codeSplitting: {
          groups: [
            { name: 'framework', test: /node_modules[\\/](react|react-dom|scheduler|react-router)[\\/]/ },
            { name: 'radix', test: /node_modules[\\/](radix-ui|@radix-ui)[\\/]/ },
            { name: 'icons', test: /node_modules[\\/]lucide-react[\\/]/ }
          ]
        }
      }
    }
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})

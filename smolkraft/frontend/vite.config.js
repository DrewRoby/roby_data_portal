import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],

  // In production, assets are served from Django's static files at this path.
  base: '/static/smolkraft/',

  build: {
    outDir: 'dist',
    rollupOptions: {
      output: {
        // Fixed filenames so Django templates can reference them without hashes.
        entryFileNames: 'assets/smolkraft.js',
        chunkFileNames: 'assets/[name].js',
        assetFileNames: 'assets/[name].[ext]',
      },
    },
  },

  server: {
    port: 5173,
    // Proxy API calls to Django during local dev (vite dev server only).
    proxy: {
      '/smolkraft/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on('error', (err) => console.error('proxy error', err))
        },
      },
      '/login': { target: 'http://localhost:8000', changeOrigin: true },
      '/logout': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
})

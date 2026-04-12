import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ command }) => ({
  plugins: [vue()],

  // Dev server: base is / so `npm run dev` works at localhost:5173/smolkraft/
  // Production build: assets reference /static/smolkraft/ where Django serves them
  base: command === 'serve' ? '/' : '/static/smolkraft/',

  build: {
    // Output directly into the app's static directory so AppDirectoriesFinder
    // picks up the files automatically — no STATICFILES_DIRS tuple needed.
    outDir: '../sk_backend/backend_api/static/smolkraft',
    emptyOutDir: true,
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
    // Proxy API and auth calls to Django during local dev.
    proxy: {
      '/smolkraft/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on('error', (err) => console.error('proxy error', err))
        },
      },
      '/login':  { target: 'http://localhost:8000', changeOrigin: true },
      '/logout': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
}))

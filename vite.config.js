import { resolve } from 'path'
import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  root: '.',
  build: {
    outDir: "./core/static/dist",
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, './core/static/src/js/main.js'),
      }
    }
  },
  plugins: [
    tailwindcss(),
  ],
})

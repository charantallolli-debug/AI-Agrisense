import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/static/',
  build: {
    outDir: path.resolve(__dirname, '../app/static'),
    emptyOutDir: true,
  }
})

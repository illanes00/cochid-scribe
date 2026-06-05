import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
// base relativo: la app se sirve bajo /api/v1/medicamentos/dev/v6/app/
export default defineConfig({ plugins: [react()], base: './', build: { outDir: 'dist', chunkSizeWarningLimit: 1500 } })

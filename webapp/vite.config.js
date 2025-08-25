import { defineConfig } from 'vite'
import path from 'path'
export default defineConfig({
base: '/app/', // must match settings.WEBAPP_PATH
build: { outDir: 'dist' },
resolve: { alias: { '@': path.resolve(__dirname, 'src') } }
})

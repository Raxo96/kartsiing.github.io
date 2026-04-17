import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'url'
import { resolve, dirname } from 'path'
import { copyFileSync, readdirSync, existsSync, mkdirSync } from 'fs'

const __dirname = dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  plugins: [
    react(),
    {
      name: 'copy-data-json',
      buildStart() {
        const src = resolve(__dirname, '../data')
        const dest = resolve(__dirname, 'public/data')
        if (!existsSync(src)) return
        mkdirSync(dest, { recursive: true })
        readdirSync(src)
          .filter(f => f.endsWith('.json'))
          .forEach(f => copyFileSync(resolve(src, f), resolve(dest, f)))
      },
    },
  ],
  base: '/',
  build: {
    outDir: '../dist',
    emptyOutDir: true,
  },
})

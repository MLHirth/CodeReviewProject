import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss(),],
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  server: {
    host: '0.0.0.0',  // This allows Vite to be accessible from outside Docker
    port: 5173,        // Use 5173 inside the container
    strictPort: true,
    watch: {
      usePolling: true, // Ensures it updates inside Docker
    },
  },
  preview: {
    host: '0.0.0.0',
    port: 4173,
  },
})

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  test: { // Vitest configuration
    globals: true,
    environment: 'happy-dom', // Using happy-dom as it's generally faster
    coverage: { // Optional: basic coverage configuration
      provider: 'v8', // or 'istanbul'
      reporter: ['text', 'json', 'html'],
    },
  },
})

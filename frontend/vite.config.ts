import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const configuredBasePath = env.VITE_BASE_PATH?.trim() || '/'
  const normalizedBasePath =
    configuredBasePath === '/'
      ? '/'
      : `/${configuredBasePath.replace(/^\/+|\/+$/g, '')}/`

  return {
    base: normalizedBasePath,
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    build: {
      chunkSizeWarningLimit: 1500,
    },
    server: {
      host: '0.0.0.0',
      port: 5173,
    },
  }
})

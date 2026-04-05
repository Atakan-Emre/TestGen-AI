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
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (!id.includes('node_modules')) {
              return undefined
            }
            const [, modulePath] = id.split('node_modules/')
            if (!modulePath) {
              return 'vendor-misc'
            }
            const parts = modulePath.split('/')
            if (parts[0] === 'antd' && parts[1] === 'es' && parts[2]) {
              return `vendor-antd-${parts[2]}`
            }
            const packageName = parts[0].startsWith('@')
              ? `${parts[0]}-${parts[1]}`
              : parts[0]
            return `vendor-${packageName.replace(/[^a-zA-Z0-9_-]/g, '-')}`
          },
        },
      },
    },
    server: {
      host: '0.0.0.0',
      port: 5173,
    },
  }
})

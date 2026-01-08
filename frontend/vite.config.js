import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  
  return {
    plugins: [
      vue(),
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      }
    },
    // 开发环境 API 代理
    server: {
      port: 5173,
      proxy: {
        '/v1': {
          target: env.VITE_API_URL || 'http://localhost:8000',
          changeOrigin: true,
        },
        '/rag': {
          target: env.VITE_API_URL || 'http://localhost:8000',
          changeOrigin: true,
        },
        '/api': {
          target: env.VITE_API_URL || 'http://localhost:8000',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, '')
        }
      }
    },
    // 生产环境构建优化
    build: {
      rollupOptions: {
        output: {
          manualChunks: {
            'vendor': ['vue', 'axios'],
            'pdf': ['pdfjs-dist']
          }
        }
      }
    },
    // 定义环境变量
    define: {
      __API_URL__: JSON.stringify(env.VITE_API_URL || '')
    }
  }
})


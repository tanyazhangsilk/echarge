import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import viteCompression from 'vite-plugin-compression'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    viteCompression({ algorithm: 'gzip' }),
    viteCompression({ algorithm: 'brotliCompress', ext: '.br' }),
  ],
  server: {
    proxy: {
      // 将 /api 前缀的请求代理到 FastAPI 后端，避免浏览器 CORS
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})

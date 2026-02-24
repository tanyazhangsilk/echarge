import axios from 'axios'

const http = axios.create({
  // 开发环境：通过 Vite 代理转发到后端，避免浏览器 CORS 限制
  // - 若设置了 VITE_API_BASE_URL，则直接使用（适合生产环境）
  // - 否则默认使用相对路径 /api/v1，由 Vite 代理到 http://localhost:8000/api/v1
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 10000,
})

export default http


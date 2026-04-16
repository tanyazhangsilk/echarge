import axios from 'axios'
import { getCurrentUserContext } from '../config/permissions'

const http = axios.create({
  // 开发环境：通过 Vite 代理转发到后端，避免浏览器 CORS 限制
  // - 若设置了 VITE_API_BASE_URL，则直接使用（适合生产环境）
  // - 否则默认使用相对路径 /api/v1，由 Vite 代理到 http://localhost:8000/api/v1
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 8000,
})

http.interceptors.request.use((config) => {
  const { role, operatorId } = getCurrentUserContext()
  config.headers = config.headers || {}
  config.headers['x-role'] = role
  config.headers['x-operator-id'] = operatorId
  return config
})

http.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error?.config
    const isTimeout = error?.code === 'ECONNABORTED'
    const canRetry =
      config &&
      String(config.method || 'get').toLowerCase() === 'get' &&
      config.retry === true &&
      !config.__retryOnce

    if (canRetry && isTimeout) {
      config.__retryOnce = true
      return http(config)
    }
    return Promise.reject(error)
  },
)

export default http


import axios from 'axios'
import { getCurrentUserContext } from '../config/permissions'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 15000,
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
  (error) => {
    const status = error?.response?.status
    const backendMessage = error?.response?.data?.message
    const isTimeout =
      error?.code === 'ECONNABORTED' || String(error?.message || '').toLowerCase().includes('timeout')

    if (backendMessage) {
      error.message = backendMessage
      return Promise.reject(error)
    }

    if (isTimeout) {
      error.message = '请求超时，请确认后端服务已启动，且数据库连接与主链接口响应正常'
      return Promise.reject(error)
    }

    if (status >= 500) {
      error.message = '后端服务暂时不可用，请稍后重试'
      return Promise.reject(error)
    }

    if (!error?.response) {
      error.message = '无法连接后端服务，请确认后端已启动'
    }

    return Promise.reject(error)
  },
)

export default http

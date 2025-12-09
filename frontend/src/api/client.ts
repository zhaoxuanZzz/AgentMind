import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API Error:', error)
    
    // 处理网络错误
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      error.message = '请求超时，请检查网络连接'
    } else if (error.message === 'Network Error') {
      error.message = '网络错误，请检查后端服务是否运行'
    }
    
    // 处理HTTP错误
    if (error.response) {
      const status = error.response.status
      const data = error.response.data
      
      if (status === 500) {
        error.message = data?.detail || data?.message || '服务器内部错误'
      } else if (status === 404) {
        error.message = '接口不存在，请检查API路径'
      } else if (status === 401) {
        error.message = '未授权，请检查API密钥配置'
      } else if (status === 403) {
        error.message = '禁止访问，请检查权限配置'
      }
      
      // 保留原始错误信息
      error.response.data = {
        ...data,
        originalError: error.message
      }
    }
    
    return Promise.reject(error)
  }
)

export default apiClient


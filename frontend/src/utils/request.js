import axios from 'axios'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

// 创建axios实例（自动关联你的接口前缀）
const request = axios.create({
  baseURL: '/', // 已匹配你的/api请求转发
  timeout: 10000
})

// 路由实例（用于跳转登录页）
const router = useRouter()

// 请求拦截器：自动添加Token
request.interceptors.request.use(
  config => {
    // 从本地缓存取登录时存储的Token
    const token = localStorage.getItem('token')
    if (token) {
      // 格式：Bearer + 空格 + Token（和后端拦截器一致）
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

// 响应拦截器：401未授权时跳登录页
request.interceptors.response.use(
  response => response,
  error => {
    if (error.response && error.response.status === 401) {
      // 清除无效Token
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      // 跳登录页，并记录当前页面（登录后自动返回）
      router.push({
        path: '/login',
        query: { redirect: router.currentRoute.value.fullPath }
      })
      ElMessage.error('请先登录~')
    }
    return Promise.reject(error)
  }
)

export default request

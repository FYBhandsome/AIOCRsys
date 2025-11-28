/**
 * API服务模块 - 精简版
 * 
 * 功能：
 * - 统一的错误处理
 * - 请求重试机制
 * - Loading状态管理
 */

import axios from 'axios'
import { ElMessage, ElLoading } from 'element-plus'
import { API_CONFIG } from '@/constants'

// 全局Loading状态管理
let loadingInstance = null
let loadingCount = 0

// Loading工具函数
const showLoading = () => {
  loadingCount++
  if (loadingCount === 1) {
    loadingInstance = ElLoading.service({
      lock: true,
      text: '加载中...',
      background: 'rgba(0, 0, 0, 0.7)'
    })
  }
}

const hideLoading = () => {
  loadingCount--
  if (loadingCount <= 0) {
    loadingCount = 0
    loadingInstance?.close()
    loadingInstance = null
  }
}

// 创建axios实例
const api = axios.create({
  baseURL: API_CONFIG.BASE_URL,
  timeout: API_CONFIG.TIMEOUT,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 显示Loading
    if (config.showLoading !== false) {
      showLoading()
    }
    
    // 添加认证Token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // 添加请求ID
    config.headers['X-Request-ID'] = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    
    // 开发环境日志
    if (import.meta.env.DEV) {
      console.log(`[API Request] ${config.method.toUpperCase()} ${config.url}`, config)
    }
    
    return config
  },
  error => {
    hideLoading()
    console.error('[API Request Error]', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    // 隐藏Loading
    if (response.config.showLoading !== false) {
      hideLoading()
    }
    
    // 开发环境日志
    if (import.meta.env.DEV) {
      console.log(`[API Response] ${response.config.url}`, response.data)
    }
    
    return response.data
  },
  async error => {
    // 隐藏Loading
    if (error.config?.showLoading !== false) {
      hideLoading()
    }
    
    // 错误处理
    return handleErrorResponse(error)
  }
)

// 错误处理函数
const handleErrorResponse = async (error) => {
  const { response, config, message } = error
  
  // 日志记录
  console.error('[API Error]', {
    url: config?.url,
    method: config?.method,
    error: error,
    response: response?.data
  })
  
  // 网络错误
  if (!response) {
    const errorMsg = message.includes('timeout') ? '请求超时，请检查网络连接' :
                     message.includes('Network Error') ? '网络连接失败，请检查网络' :
                     '请求失败，请稍后重试'
    ElMessage.error(errorMsg)
    return Promise.reject(error)
  }
  
  // HTTP状态码错误
  const { status, data } = response
  const errorMsg = data?.error?.message || getErrorMessage(status)
  
  // 特殊处理401未授权
  if (status === 401) {
    localStorage.removeItem('token')
    setTimeout(() => {
      window.location.href = '/login'
    }, 1000)
  }
  
  ElMessage.error(errorMsg)
  
  // 请求重试机制
  if (config?.retry && (config.__retryCount || 0) < config.retry) {
    config.__retryCount = (config.__retryCount || 0) + 1
    const delay = config.retryDelay || 1000
    const backoff = delay * Math.pow(2, config.__retryCount - 1)
    
    console.log(`[API Retry] 第 ${config.__retryCount} 次重试，延迟 ${backoff}ms`)
    
    await new Promise(resolve => setTimeout(resolve, backoff))
    return api(config)
  }
  
  return Promise.reject(error)
}

// 根据状态码获取错误消息
const getErrorMessage = (status) => {
  const errorMap = {
    400: '请求参数错误',
    401: '未授权，请先登录',
    403: '权限不足，无法访问',
    404: '请求的资源不存在',
    422: '请求参数验证失败',
    429: '请求过于频繁，请稍后再试',
    500: '服务器内部错误',
    502: '网关错误，服务暂时不可用',
    503: '服务暂时不可用，请稍后重试'
  }
  
  return errorMap[status] || `请求失败 (${status})`
}

// 创建带重试的请求配置
const createRetryConfig = (config, retryCount = 3, retryDelay = 1000) => {
  return {
    ...config,
    retry: retryCount,
    retryDelay: retryDelay,
    __retryCount: 0
  }
}

// ==================== 认证API ====================
export const authAPI = {
  // 用户登录
  login: (username, password) => {
    return api.post('/v1/auth/login', {
      username,
      password
    })
  },
  
  // 用户注册
  register: (userData) => {
    return api.post('/v1/auth/register', userData)
  },
  
  // 获取当前用户信息
  getUserInfo: () => {
    return api.get('/v1/auth/me')
  },
  
  // 请求密码重置
  requestPasswordReset: (email) => {
    return api.post('/v1/auth/password/reset-request', {
      email
    })
  },
  
  // 确认密码重置
  confirmPasswordReset: (email, verificationCode, newPassword) => {
    return api.post('/v1/auth/password/reset-confirm', {
      email,
      verification_code: verificationCode,
      new_password: newPassword
    })
  }
}

// ==================== 学生API ====================
export const studentAPI = {
  // 上传证书
  uploadCertificate: (file, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)
    
    return api.post('/v1/student/certificate/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: progressEvent => {
        if (onProgress) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percentCompleted)
        }
      },
      timeout: 60000,
      ...createRetryConfig({}, 2, 2000)
    })
  },
  
  // 查看成绩摘要
  getScoresSummary: () => {
    return api.get('/v1/student/scores/summary')
  },
  
  // 查看成绩详情
  getScoresDetail: () => {
    return api.get('/v1/student/scores/detail')
  },
  
  // 获取上传历史
  getUploadHistory: () => {
    return api.get('/v1/student/uploads')
  },
  
  // 获取综合分析数据
  getComprehensiveAnalysis: () => {
    return api.get('/v1/student/comprehensive/analysis')
  },
  
  // 获取成绩趋势数据
  getScoreTrend: () => {
    return api.get('/v1/student/scores/trend')
  }
}

// ==================== 教师API ====================
export const teacherAPI = {
  // 上传成绩单
  uploadScores: (file, classId, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('class_id', classId)
    
    return api.post('/v1/teacher/scores/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: progressEvent => {
        if (onProgress) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percentCompleted)
        }
      },
      timeout: 60000,
      ...createRetryConfig({}, 2, 2000)
    })
  },
  

  
  // 查看学生列表
  getStudents: (classId) => {
    return api.get('/v1/teacher/students', {
      params: { class_id: classId }
    })
  },
  
  // 查看学生成绩
  getStudentScores: (studentId) => {
    return api.get(`/v1/teacher/students/${studentId}/scores`)
  },
  
  // 获取班级列表
  getClasses: () => {
    return api.get('/v1/teacher/classes')
  },
  
  // 获取班级列表（别名）
  getClassList: () => {
    return api.get('/v1/teacher/classes')
  },
  
  // ============ 学生管理 ============
  
  // 学生列表
  getStudentList: (params) => {
    return api.get('/v1/teacher/students', { params });
  },
  
  // 获取学生详情
  getStudentDetail: (studentId) => {
    return api.get(`/v1/teacher/students/${studentId}`)
  },
  
  // 创建学生
  createStudent: (studentData) => {
    return api.post('/v1/teacher/students', studentData)
  },
  
  // 更新学生信息
  updateStudent: (studentId, studentData) => {
    return api.put(`/v1/teacher/students/${studentId}`, studentData)
  },
  
  // 删除学生
  deleteStudent: (studentId) => {
    return api.delete(`/v1/teacher/students/${studentId}`)
  },
  
  // 重置学生密码
  resetStudentPassword: (studentId) => {
    return api.post(`/v1/teacher/students/${studentId}/reset-password`)
  },
  
  // 更新学生状态
  updateStudentStatus: (studentId, status) => {
    return api.patch(`/v1/teacher/students/${studentId}/status`, { status })
  },
  
  // 批量导入学生
  importStudents: (formData) => {
    return api.post('/v1/teacher/students/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  
  // 导出学生数据
  exportStudents: (params) => {
    return api.get('/v1/teacher/students/export', { 
      params,
      responseType: 'blob'
    })
  },
  
  // 获取班级统计信息
  getClassStats: (classId) => {
    return api.get('/v1/teacher/classes/stats', {
      params: { class_id: classId }
    })
  },
  
  // 获取班级排名
  getClassRanking: (classId) => {
    return api.get('/v1/teacher/classes/ranking', {
      params: { class_id: classId }
    })
  },
  
  // ============ 成绩可视化分析 ============
  
  // 获取成绩分布数据
  getScoreDistribution: (params) => {
    return api.get('/v1/teacher/analysis/distribution', { params })
  },
  
  // 获取科目成绩对比数据
  getSubjectComparison: (params) => {
    return api.get('/v1/teacher/analysis/subject-comparison', { params })
  },
  
  // 获取成绩趋势数据
  getScoreTrend: (params) => {
    return api.get('/v1/teacher/analysis/trend', { params })
  },
  
  // 获取班级对比数据
  getClassComparison: (params) => {
    return api.get('/v1/teacher/analysis/class-comparison', { params })
  },
  
  // 获取成绩相关性数据
  getScoreCorrelation: (params) => {
    return api.get('/v1/teacher/analysis/correlation', { params })
  },
  
  // 获取学生成绩详情
  getStudentScoreDetail: (studentId) => {
    return api.get(`/v1/teacher/students/${studentId}/score-detail`)
  },
  
  // 导出成绩分析数据
  exportAnalysisData: (params) => {
    return api.get('/v1/teacher/analysis/export', { 
      params,
      responseType: 'blob'
    })
  },
  
  // ============ 班级排名 ============
  
  // 获取班级学生排名
  getClassStudentRanking: (classId) => {
    return api.get(`/v1/teacher/classes/${classId}/student-ranking`)
  },
  
  // 导出班级排名数据
  exportClassRanking: (params) => {
    return api.get('/v1/teacher/classes/ranking/export', { 
      params,
      responseType: 'blob'
    })
  }
}

// ==================== 管理员API ====================
export const adminAPI = {
  // 上传综测规则文档
  uploadRuleDocument: (file, description, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)
    if (description) {
      formData.append('description', description)
    }
    
    return api.post('/v1/admin/rules/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: progressEvent => {
        if (onProgress) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percentCompleted)
        }
      },
      timeout: 60000,
      ...createRetryConfig({}, 2, 2000)
    })
  },
  
  // 获取规则文档列表
  getRuleDocuments: (enabledOnly = false) => {
    return api.get('/v1/admin/rules/list', {
      params: { enabled_only: enabledOnly }
    })
  },
  
  // 启用/停用规则文档
  updateRuleStatus: (docId, enabled) => {
    return api.patch(`/v1/admin/rules/${docId}/status`, {
      enabled
    })
  },
  
  // 删除规则文档
  deleteRuleDocument: (docId, deleteFile = false) => {
    return api.delete(`/v1/admin/rules/${docId}`, {
      params: { delete_file: deleteFile }
    })
  },
  
  // 获取AI配置
  getAIConfig: () => {
    return api.get('/v1/admin/ai/config')
  },
  
  // 更新AI配置
  updateAIConfig: (config) => {
    return api.put('/v1/admin/ai/config', config)
  },
  
  // 测试AI连接
  testAIConnection: () => {
    return api.post('/v1/admin/ai/config/test')
  },
  
  // 获取系统设置
  getSystemSettings: () => {
    return api.get('/v1/admin/settings')
  },
  
  // 更新系统设置
  updateSystemSettings: (settings) => {
    return api.put('/v1/admin/settings', settings)
  },
  
  // 获取用户列表
  getUsers: () => {
    return api.get('/v1/admin/users')
  },
  
  // 创建用户
  createUser: (userData) => {
    return api.post('/v1/admin/users', userData)
  },
  
  // 更新用户
  updateUser: (userId, userData) => {
    return api.put(`/v1/admin/users/${userId}`, userData)
  },
  
  // 删除用户
  deleteUser: (userId) => {
    return api.delete(`/v1/admin/users/${userId}`)
  },
  
  // ============ Prompt管理 ============
  
  // 获取Prompt配置
  getPrompts: () => {
    return api.get('/v1/admin/prompts')
  },
  
  // 更新Prompt配置
  updatePrompts: (prompts) => {
    return api.put('/v1/admin/prompts', prompts)
  },
  
  // 重置Prompt为默认值
  resetPrompts: () => {
    return api.post('/v1/admin/prompts/reset')
  },
  
  // ============ 向量数据库管理 ============
  
  // 获取向量数据库统计
  getVectorDBStats: () => {
    return api.get('/v1/admin/vector-db/stats')
  },
  
  // 重置向量数据库
  resetVectorDB: (confirm = true, rebuild = false) => {
    return api.post('/v1/admin/vector-db/reset', null, {
      params: { confirm, rebuild }
    })
  },
  
  // 重建向量数据库
  rebuildVectorDB: () => {
    return api.post('/v1/admin/vector-db/rebuild')
  },
  
  // ============ RAG系统信息 ============
  
  // 获取RAG系统统计
  getRAGStats: () => {
    return api.get('/v1/admin/rag/stats')
  },
  
  // RAG系统健康检查
  ragHealthCheck: () => {
    return api.get('/v1/admin/rag/health')
  },
  
  // 重置AI配置
  resetAIConfig: () => {
    return api.post('/v1/admin/ai/config/reset')
  },
  
  // 验证AI配置
  validateAIConfig: () => {
    return api.get('/v1/admin/ai/config/validate')
  }
}

// ==================== 通用API ====================
export const commonAPI = {
  // GET请求
  get: (url, config) => {
    return api.get(url, config)
  },
  
  // POST请求
  post: (url, data, config) => {
    return api.post(url, data, config)
  },
  
  // PUT请求
  put: (url, data, config) => {
    return api.put(url, data, config)
  },
  
  // DELETE请求
  delete: (url, config) => {
    return api.delete(url, config)
  },
  
  // PATCH请求
  patch: (url, data, config) => {
    return api.patch(url, data, config)
  }
}

// 导出工具函数
export const showGlobalLoading = showLoading
export const hideGlobalLoading = hideLoading
export { createRetryConfig }

// 默认导出axios实例
export default api
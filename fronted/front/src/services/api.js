/**
 * API服务模块 - 完整版
 * 
 * 功能：
 * - 统一的错误处理
 * - 请求重试机制
 * - Loading状态管理
 * - 支持多个后端服务
 */

import axios from 'axios'
import { ElMessage, ElLoading } from 'element-plus'
import { API_CONFIG, API_ENDPOINTS } from '@/constants'

let loadingInstance = null
let loadingCount = 0

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

const createApiInstance = (baseURL) => axios.create({
  baseURL,
  timeout: API_CONFIG.TIMEOUT,
  headers: {
    'Content-Type': 'application/json'
  }
})

const api = createApiInstance(API_CONFIG.BASE_URL)
const ragApi = createApiInstance(API_CONFIG.RAG_BASE_URL)

const setupInterceptors = (instance, name = 'API') => {
  instance.interceptors.request.use(
    config => {
      if (config.showLoading !== false) {
        showLoading()
      }
      
      const token = localStorage.getItem('token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      
      config.headers['X-Request-ID'] = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      
      if (import.meta.env.DEV) {
        console.log(`[${name} Request] ${config.method.toUpperCase()} ${config.url}`, config)
      }
      
      return config
    },
    error => {
      hideLoading()
      console.error(`[${name} Request Error]`, error)
      return Promise.reject(error)
    }
  )

  instance.interceptors.response.use(
    response => {
      if (response.config.showLoading !== false) {
        hideLoading()
      }
      
      if (import.meta.env.DEV) {
        console.log(`[${name} Response] ${response.config.url}`, response.data)
      }
      
      return response.data
    },
    async error => {
      if (error.config?.showLoading !== false) {
        hideLoading()
      }
      
      return handleErrorResponse(error, name)
    }
  )
}

setupInterceptors(api, 'Main API')
setupInterceptors(ragApi, 'RAG API')

const handleErrorResponse = async (error, name = 'API') => {
  const { response, config, message } = error
  
  console.error(`[${name} Error]`, {
    url: config?.url,
    method: config?.method,
    error: error,
    response: response?.data
  })
  
  if (!response) {
    const errorMsg = message.includes('timeout') ? '请求超时，请检查网络连接' :
                     message.includes('Network Error') ? '网络连接失败，请检查网络' :
                     '请求失败，请稍后重试'
    ElMessage.error(errorMsg)
    return Promise.reject(error)
  }
  
  const { status, data } = response
  const errorMsg = data?.error?.message || data?.message || getErrorMessage(status)
  
  if (status === 401) {
    localStorage.removeItem('token')
    setTimeout(() => {
      window.location.href = '/login'
    }, 1000)
  }
  
  ElMessage.error(errorMsg)
  
  if (config?.retry && (config.__retryCount || 0) < config.retry) {
    config.__retryCount = (config.__retryCount || 0) + 1
    const delay = config.retryDelay || 1000
    const backoff = delay * Math.pow(2, config.__retryCount - 1)
    
    console.log(`[${name} Retry] 第 ${config.__retryCount} 次重试，延迟 ${backoff}ms`)
    
    await new Promise(resolve => setTimeout(resolve, backoff))
    return api(config)
  }
  
  return Promise.reject(error)
}

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

const createRetryConfig = (config, retryCount = 3, retryDelay = 1000) => {
  return {
    ...config,
    retry: retryCount,
    retryDelay: retryDelay,
    __retryCount: 0
  }
}

export const authAPI = {
  login: (username, password) => api.post(API_ENDPOINTS.AUTH.LOGIN, { username, password }),
  register: (userData) => api.post(API_ENDPOINTS.AUTH.REGISTER, userData),
  getUserInfo: () => api.get(API_ENDPOINTS.AUTH.ME),
  requestPasswordReset: (email) => api.post(API_ENDPOINTS.AUTH.PASSWORD_RESET, { email }),
  confirmPasswordReset: (email, verificationCode, newPassword) => 
    api.post(API_ENDPOINTS.AUTH.PASSWORD_CONFIRM, {
      email,
      verification_code: verificationCode,
      new_password: newPassword
    })
}

export const studentAPI = {
  uploadCertificate: (file, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)
    
    return api.post(API_ENDPOINTS.STUDENT.CERTIFICATE_UPLOAD, formData, {
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
  
  getScoresSummary: () => api.get(API_ENDPOINTS.STUDENT.SCORES_SUMMARY),
  getScoresDetail: () => api.get(API_ENDPOINTS.STUDENT.SCORES_DETAIL),
  getUploadHistory: () => api.get(API_ENDPOINTS.STUDENT.UPLOAD_HISTORY),
  getComprehensiveAnalysis: () => api.get(API_ENDPOINTS.STUDENT.ANALYSIS),
  getScoreTrend: () => api.get(API_ENDPOINTS.STUDENT.TREND)
}

export const teacherAPI = {
  uploadScores: (file, classId, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('class_id', classId)
    
    return api.post(API_ENDPOINTS.TEACHER.SCORES_UPLOAD, formData, {
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
  
  getStudents: (classId) => api.get(API_ENDPOINTS.TEACHER.STUDENTS, { params: { class_id: classId } }),
  getStudentScores: (studentId) => api.get(`${API_ENDPOINTS.TEACHER.STUDENTS}/${studentId}/scores`),
  getClasses: () => api.get(API_ENDPOINTS.TEACHER.CLASSES),
  getClassList: () => api.get(API_ENDPOINTS.TEACHER.CLASSES),
  
  getStudentList: (params) => api.get(API_ENDPOINTS.TEACHER.STUDENTS, { params }),
  getStudentDetail: (studentId) => api.get(`${API_ENDPOINTS.TEACHER.STUDENTS}/${studentId}`),
  createStudent: (studentData) => api.post(API_ENDPOINTS.TEACHER.STUDENTS, studentData),
  updateStudent: (studentId, studentData) => api.put(`${API_ENDPOINTS.TEACHER.STUDENTS}/${studentId}`, studentData),
  deleteStudent: (studentId) => api.delete(`${API_ENDPOINTS.TEACHER.STUDENTS}/${studentId}`),
  resetStudentPassword: (studentId) => api.post(`${API_ENDPOINTS.TEACHER.STUDENTS}/${studentId}/reset-password`),
  updateStudentStatus: (studentId, status) => api.patch(`${API_ENDPOINTS.TEACHER.STUDENTS}/${studentId}/status`, { status }),
  importStudents: (formData) => api.post(`${API_ENDPOINTS.TEACHER.STUDENTS}/import`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  exportStudents: (params) => api.get(`${API_ENDPOINTS.TEACHER.STUDENTS}/export`, { params, responseType: 'blob' }),
  
  getClassStats: (classId) => api.get(API_ENDPOINTS.TEACHER.CLASS_STATS, { params: { class_id: classId } }),
  getClassRanking: (classId) => api.get(API_ENDPOINTS.TEACHER.CLASS_RANKING, { params: { class_id: classId } }),
  
  getScoreDistribution: (params) => api.get('/v1/teacher/analysis/distribution', { params }),
  getSubjectComparison: (params) => api.get('/v1/teacher/analysis/subject-comparison', { params }),
  getScoreTrend: (params) => api.get('/v1/teacher/analysis/trend', { params }),
  getClassComparison: (params) => api.get('/v1/teacher/analysis/class-comparison', { params }),
  getScoreCorrelation: (params) => api.get('/v1/teacher/analysis/correlation', { params }),
  getStudentScoreDetail: (studentId) => api.get(`${API_ENDPOINTS.TEACHER.STUDENTS}/${studentId}/score-detail`),
  exportAnalysisData: (params) => api.get('/v1/teacher/analysis/export', { params, responseType: 'blob' }),
  
  getClassStudentRanking: (classId) => api.get(`${API_ENDPOINTS.TEACHER.CLASSES}/${classId}/student-ranking`),
  exportClassRanking: (params) => api.get(`${API_ENDPOINTS.TEACHER.CLASSES}/ranking/export`, { params, responseType: 'blob' })
}

export const adminAPI = {
  uploadRuleDocument: (file, description, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)
    if (description) {
      formData.append('description', description)
    }
    
    return api.post(API_ENDPOINTS.ADMIN.RULES_UPLOAD, formData, {
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
  
  getRuleDocuments: (enabledOnly = false) => api.get(API_ENDPOINTS.ADMIN.RULES_LIST, { params: { enabled_only: enabledOnly } }),
  updateRuleStatus: (docId, enabled) => api.patch(`${API_ENDPOINTS.ADMIN.RULES_UPLOAD.replace('/upload', '')}/${docId}/status`, { enabled }),
  deleteRuleDocument: (docId, deleteFile = false) => api.delete(`${API_ENDPOINTS.ADMIN.RULES_UPLOAD.replace('/upload', '')}/${docId}`, { params: { delete_file: deleteFile } }),
  
  getAIConfig: () => api.get(API_ENDPOINTS.ADMIN.AI_CONFIG),
  updateAIConfig: (config) => api.put(API_ENDPOINTS.ADMIN.AI_CONFIG, config),
  testAIConnection: () => api.post(API_ENDPOINTS.ADMIN.AI_CONFIG_TEST),
  resetAIConfig: () => api.post(`${API_ENDPOINTS.ADMIN.AI_CONFIG}/reset`),
  validateAIConfig: () => api.get(`${API_ENDPOINTS.ADMIN.AI_CONFIG}/validate`),
  
  getSystemSettings: () => api.get(API_ENDPOINTS.ADMIN.SETTINGS),
  updateSystemSettings: (settings) => api.put(API_ENDPOINTS.ADMIN.SETTINGS, settings),
  
  getUsers: () => api.get(API_ENDPOINTS.ADMIN.USERS),
  createUser: (userData) => api.post(API_ENDPOINTS.ADMIN.USERS, userData),
  updateUser: (userId, userData) => api.put(`${API_ENDPOINTS.ADMIN.USERS}/${userId}`, userData),
  deleteUser: (userId) => api.delete(`${API_ENDPOINTS.ADMIN.USERS}/${userId}`),
  
  getPrompts: () => api.get(API_ENDPOINTS.ADMIN.PROMPTS),
  updatePrompts: (prompts) => api.put(API_ENDPOINTS.ADMIN.PROMPTS, prompts),
  resetPrompts: () => api.post(`${API_ENDPOINTS.ADMIN.PROMPTS}/reset`),
  
  getVectorDBStats: () => ragApi.get(API_ENDPOINTS.ADMIN.VECTOR_DB_STATS),
  clearVectorDB: () => ragApi.post(API_ENDPOINTS.ADMIN.VECTOR_DB_CLEAR),
  resetVectorDB: (backup = true) => ragApi.post(API_ENDPOINTS.ADMIN.VECTOR_DB_RESET, null, { params: { backup } }),
  reindexVectorDB: () => ragApi.post(API_ENDPOINTS.ADMIN.VECTOR_DB_REINDEX),
  getVectorDBCollections: () => ragApi.get(API_ENDPOINTS.ADMIN.VECTOR_DB_COLLECTIONS),
  getVectorDBHealth: () => ragApi.get(API_ENDPOINTS.ADMIN.VECTOR_DB_HEALTH),
  rebuildVectorDB: () => ragApi.post(API_ENDPOINTS.ADMIN.VECTOR_DB_REINDEX),
  
  getRAGStats: () => api.get(API_ENDPOINTS.ADMIN.RAG_STATS),
  ragHealthCheck: () => api.get(API_ENDPOINTS.ADMIN.RAG_HEALTH)
}

export const ragAPI = {
  chat: (message, chatHistory = [], useRag = true) => 
    ragApi.post(API_ENDPOINTS.RAG.CHAT, { 
      message, 
      chat_history: chatHistory,
      use_rag: useRag 
    }),
  
  chatStream: async function* (message, chatHistory = []) {
    const response = await fetch(`${API_CONFIG.RAG_BASE_URL}${API_ENDPOINTS.RAG.CHAT_STREAM}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
      },
      body: JSON.stringify({ message, chat_history: chatHistory })
    })
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            yield data
          } catch (e) {
            console.error('Failed to parse SSE data:', e)
          }
        }
      }
    }
  },
  
  chatAsync: (message, chatHistory = []) => 
    ragApi.post(API_ENDPOINTS.RAG.CHAT_ASYNC, { message, chat_history: chatHistory }),
  
  getDocuments: (category, tags) => ragApi.get(API_ENDPOINTS.RAG.DOCUMENTS, { params: { category, tags } }),
  getDocument: (docId) => ragApi.get(`${API_ENDPOINTS.RAG.DOCUMENTS}/${docId}`),
  deleteDocument: (docId) => ragApi.delete(`${API_ENDPOINTS.RAG.DOCUMENTS}/${docId}`),
  
  getSystemInfo: () => ragApi.get(API_ENDPOINTS.RAG.SYSTEM_INFO),
  getSystemHealth: () => ragApi.get(API_ENDPOINTS.RAG.SYSTEM_HEALTH),
  
  getLLMConfig: () => ragApi.get(API_ENDPOINTS.RAG.LLM_CONFIG),
  updateLLMConfig: (config) => ragApi.put(API_ENDPOINTS.RAG.LLM_CONFIG, config),
  testLLMConnection: () => ragApi.post(API_ENDPOINTS.RAG.LLM_TEST),
  
  getVectorDBStats: () => ragApi.get(API_ENDPOINTS.RAG.VECTOR_DB_STATS),
  
  getPrompts: () => ragApi.get(API_ENDPOINTS.RAG.PROMPTS),
  updatePrompts: (prompts) => ragApi.put(API_ENDPOINTS.RAG.PROMPTS, prompts),
  resetPrompts: () => ragApi.post(`${API_ENDPOINTS.RAG.PROMPTS}/reset`),
  
  getCacheStats: () => ragApi.get(`${API_ENDPOINTS.RAG.CHAT}/cache/stats`),
  clearCache: () => ragApi.delete(`${API_ENDPOINTS.RAG.CHAT}/cache`)
}

export const commonAPI = {
  get: (url, config) => api.get(url, config),
  post: (url, data, config) => api.post(url, data, config),
  put: (url, data, config) => api.put(url, data, config),
  delete: (url, config) => api.delete(url, config),
  patch: (url, data, config) => api.patch(url, data, config)
}

export const dataImportAPI = {
  importExcel: (file, options = {}) => {
    const formData = new FormData()
    formData.append('file', file)
    if (options.academic_year) formData.append('academic_year', options.academic_year)
    if (options.semester) formData.append('semester', options.semester)
    if (options.class_id) formData.append('class_id', options.class_id)
    
    return api.post('/v1/data-import/excel', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000
    })
  },
  
  getTemplate: () => api.get('/v1/data-import/template'),
  
  previewExcel: (file, rows = 10) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('rows', rows)
    
    return api.post('/v1/data-import/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }
}

export const comprehensiveScoreAPI = {
  calculateStudentScore: (studentId, academicYear, semester, configId = null) => 
    api.post(`/v1/comprehensive-score/calculate/student/${studentId}`, null, {
      params: { academic_year: academicYear, semester, config_id: configId }
    }),
  
  calculateClassScores: (classId, academicYear, semester, configId = null) =>
    api.post(`/v1/comprehensive-score/calculate/class/${classId}`, null, {
      params: { academic_year: academicYear, semester, config_id: configId }
    }),
  
  getStudentScore: (studentId, academicYear, semester) =>
    api.get(`/v1/comprehensive-score/student/${studentId}`, {
      params: { academic_year: academicYear, semester }
    }),
  
  getClassRanking: (classId, academicYear, semester) =>
    api.get(`/v1/comprehensive-score/class/${classId}/ranking`, {
      params: { academic_year: academicYear, semester }
    }),
  
  addScoreDetail: (data) => api.post('/v1/comprehensive-score/detail', data),
  
  deleteScoreDetail: (detailId) => api.delete(`/v1/comprehensive-score/detail/${detailId}`),
  
  getConfigs: () => api.get('/v1/comprehensive-score/config/list'),
  
  createConfig: (config) => api.post('/v1/comprehensive-score/config', config),
  
  updateConfig: (configId, config) => api.put(`/v1/comprehensive-score/config/${configId}`, config),
  
  getClasses: () => api.get('/v1/comprehensive-score/classes'),
  
  getClassStats: (classId, academicYear, semester) =>
    api.get(`/v1/comprehensive-score/class/${classId}/stats`, {
      params: { academic_year: academicYear, semester }
    })
}

export const excelFillAPI = {
  fillFromTemplate: (templateFile, rawDataFile, options = {}) => {
    const formData = new FormData()
    formData.append('template_file', templateFile)
    formData.append('raw_data_file', rawDataFile)
    if (options.academic_year) formData.append('academic_year', options.academic_year)
    if (options.semester) formData.append('semester', options.semester)
    if (options.class_id) formData.append('class_id', options.class_id)
    
    return api.post('/v1/excel-fill/from-template', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 180000,
      responseType: 'blob'
    })
  },
  
  processOCR: (data) => api.post('/v1/excel-fill/process-ocr', data),
  
  batchProcess: (data) => api.post('/v1/excel-fill/batch-process', data),
  
  getWeightConfig: (academicYear, semester) => 
    api.get('/v1/excel-fill/weight-config', {
      params: { academic_year: academicYear, semester }
    }),
  
  analyzeCertificate: (certificateText, studentId = null, studentName = null) => {
    const formData = new FormData()
    formData.append('certificate_text', certificateText)
    if (studentId) formData.append('student_id', studentId)
    if (studentName) formData.append('student_name', studentName)
    
    return api.post('/v1/excel-fill/analyze-certificate', formData)
  },
  
  retrieveRules: (query) => {
    const formData = new FormData()
    formData.append('query', query)
    return api.post('/v1/excel-fill/retrieve-rules', formData)
  },
  
  calculateScore: (data) => {
    const formData = new FormData()
    formData.append('student_id', data.student_id)
    formData.append('student_name', data.student_name)
    formData.append('class_name', data.class_name)
    formData.append('academic_info', JSON.stringify(data.academic_info || {}))
    formData.append('certificate_info', JSON.stringify(data.certificate_info || []))
    formData.append('score_details', JSON.stringify(data.score_details || []))
    
    return api.post('/v1/excel-fill/calculate-score', formData)
  },
  
  getTemplateColumns: () => api.get('/v1/excel-fill/template-columns')
}

export const fieldMappingAPI = {
  processAndFill: (sourceFile, templateFile, options = {}) => {
    const formData = new FormData()
    formData.append('source_file', sourceFile)
    formData.append('template_file', templateFile)
    if (options.academic_year) formData.append('academic_year', options.academic_year)
    if (options.semester) formData.append('semester', options.semester)
    if (options.output_dir) formData.append('output_dir', options.output_dir)
    
    return api.post('/v1/field-mapping/process', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 180000
    })
  },
  
  processAndDownload: (sourceFile, templateFile, options = {}) => {
    const formData = new FormData()
    formData.append('source_file', sourceFile)
    formData.append('template_file', templateFile)
    if (options.academic_year) formData.append('academic_year', options.academic_year)
    if (options.semester) formData.append('semester', options.semester)
    
    return api.post('/v1/field-mapping/download', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 180000,
      responseType: 'blob'
    })
  },
  
  getSourceFields: () => api.get('/v1/field-mapping/source-fields'),
  
  getTargetFields: () => api.get('/v1/field-mapping/target-fields'),
  
  previewSource: (file, rows = 10) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('rows', rows)
    
    return api.post('/v1/field-mapping/preview-source', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }
}

export const scoreUploadAPI = {
  upload: (file, options) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('academic_year', options.academic_year)
    formData.append('semester', options.semester)
    formData.append('uploaded_by', options.uploaded_by)
    if (options.upload_role) formData.append('upload_role', options.upload_role)
    
    return api.post('/v1/score-upload/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000
    })
  },
  
  getHistory: (studentId, options = {}) => 
    api.get(`/v1/score-upload/history/${studentId}`, {
      params: { 
        academic_year: options.academic_year,
        semester: options.semester
      }
    }),
  
  getUploadRecords: (options = {}) => 
    api.get('/v1/score-upload/upload-records', {
      params: {
        upload_by: options.upload_by,
        status: options.status,
        limit: options.limit || 20
      }
    }),
  
  getFieldMapping: () => api.get('/v1/score-upload/field-mapping'),
  
  preview: (file, rows = 10) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('rows', rows)
    
    return api.post('/v1/score-upload/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }
}

export const certificateAPI = {
  upload: (files, options) => {
    const formData = new FormData()
    files.forEach(file => formData.append('files', file))
    formData.append('student_id', options.student_id)
    if (options.title) formData.append('title', options.title)
    if (options.certificate_type) formData.append('certificate_type', options.certificate_type)
    if (options.level) formData.append('level', options.level)
    if (options.issuer) formData.append('issuer', options.issuer)
    if (options.issue_date) formData.append('issue_date', options.issue_date)
    if (options.category) formData.append('category', options.category)
    if (options.sub_category) formData.append('sub_category', options.sub_category)
    if (options.score) formData.append('score', options.score)
    
    return api.post('/v1/certificate/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000
    })
  },
  
  getStudentCertificates: (studentId, options = {}) => 
    api.get(`/v1/certificate/student/${studentId}`, {
      params: { 
        status: options.status,
        category: options.category
      }
    }),
  
  getDetail: (certificateId) => 
    api.get(`/v1/certificate/${certificateId}`),
  
  delete: (certificateId, deletedBy = null) => 
    api.delete(`/v1/certificate/${certificateId}`, {
      params: { deleted_by: deletedBy }
    }),
  
  update: (certificateId, data) => {
    const formData = new FormData()
    Object.keys(data).forEach(key => {
      if (data[key] !== undefined && data[key] !== null) {
        formData.append(key, data[key])
      }
    })
    return api.put(`/v1/certificate/${certificateId}`, formData)
  },
  
  getStatistics: (studentId) => 
    api.get(`/v1/certificate/statistics/${studentId}`),
  
  batchUpdateStatus: (certificateIds, status, options = {}) => 
    api.post('/v1/certificate/batch-status', {
      certificate_ids: certificateIds,
      status: status,
      reviewed_by: options.reviewed_by,
      review_comment: options.review_comment
    })
}

export const fileManagementAPI = {
  upload: (file, options) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('file_type', options.file_type)
    formData.append('owner_id', options.owner_id)
    if (options.owner_type) formData.append('owner_type', options.owner_type)
    if (options.is_public) formData.append('is_public', options.is_public)
    if (options.metadata) formData.append('metadata', JSON.stringify(options.metadata))
    
    return api.post('/v1/file/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000
    })
  },
  
  uploadMultiple: (files, options) => {
    const formData = new FormData()
    files.forEach(file => formData.append('files', file))
    formData.append('file_type', options.file_type)
    formData.append('owner_id', options.owner_id)
    if (options.owner_type) formData.append('owner_type', options.owner_type)
    
    return api.post('/v1/file/upload-multiple', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 180000
    })
  },
  
  initChunkUpload: (filename, fileSize, fileType, ownerId, chunkSize = null) => 
    api.post('/v1/file/chunk/init', null, {
      params: {
        filename,
        file_size: fileSize,
        file_type: fileType,
        owner_id: ownerId,
        chunk_size: chunkSize
      }
    }),
  
  uploadChunk: (fileId, chunkIndex, chunk, options = {}) => {
    const formData = new FormData()
    formData.append('chunk', chunk)
    if (options.upload_ip) formData.append('upload_ip', options.upload_ip)
    
    return api.post(`/v1/file/chunk/${fileId}/${chunkIndex}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000
    })
  },
  
  completeChunkUpload: (fileId) => 
    api.post(`/v1/file/chunk/${fileId}/complete`),
  
  getUploadProgress: (fileId) => 
    api.get(`/v1/file/chunk/${fileId}/progress`),
  
  download: (fileId, options = {}) => 
    api.get(`/v1/file/download/${fileId}`, {
      params: {
        user_id: options.user_id,
        user_type: options.user_type || 'student'
      },
      responseType: 'blob'
    }),
  
  downloadResult: (fileId, options = {}) => 
    api.get(`/v1/file/download-result/${fileId}`, {
      params: {
        user_id: options.user_id,
        user_type: options.user_type || 'student'
      },
      responseType: 'blob'
    }),
  
  getInfo: (fileId) => 
    api.get(`/v1/file/info/${fileId}`),
  
  list: (options = {}) => 
    api.get('/v1/file/list', {
      params: {
        owner_id: options.owner_id,
        file_type: options.file_type,
        status: options.status,
        limit: options.limit || 20,
        offset: options.offset || 0
      }
    }),
  
  delete: (fileId, options = {}) => 
    api.delete(`/v1/file/${fileId}`, {
      params: {
        user_id: options.user_id,
        user_type: options.user_type || 'student',
        backup: options.backup !== false
      }
    }),
  
  getDownloadHistory: (options = {}) => 
    api.get('/v1/file/download-history', {
      params: {
        file_id: options.file_id,
        downloader_id: options.downloader_id,
        limit: options.limit || 50
      }
    }),
  
  getCategories: () => 
    api.get('/v1/file/categories')
}

export const showGlobalLoading = showLoading
export const hideGlobalLoading = hideGlobalLoading
export { createRetryConfig }

export default api

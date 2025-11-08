/**
 * 应用常量定义
 */

// API相关常量
// 优先读取环境变量，其次回退到开发时代理前缀 '/api'
const ENV_BASE_URL = import.meta?.env?.VITE_API_BASE_URL
const BASE_URL = ENV_BASE_URL && ENV_BASE_URL.trim() !== '' ? ENV_BASE_URL : '/api'

// 处理BASE_URL：如果是完整URL（http/https开头）则直接使用，否则确保以/开头
const NORMALIZED_BASE_URL = (BASE_URL.startsWith('http://') || BASE_URL.startsWith('https://')) 
  ? BASE_URL 
  : (BASE_URL.startsWith('/') ? BASE_URL : `/${BASE_URL}`)

// 开发环境下输出配置信息
if (import.meta.env.DEV) {
  console.log('[API Config] BASE_URL:', NORMALIZED_BASE_URL)
}

export const API_CONFIG = {
  BASE_URL: NORMALIZED_BASE_URL,
  TIMEOUT: 10000,
  RETRY_TIMES: 3
}

// 文件上传相关常量
export const UPLOAD_CONFIG = {
  MAX_SIZE: 10 * 1024 * 1024, // 10MB
  ALLOWED_TYPES: ['image/jpeg', 'image/png', 'image/gif', 'application/pdf'],
  ALLOWED_EXTENSIONS: ['.jpg', '.jpeg', '.png', '.gif', '.pdf']
}

// 任务状态常量
export const TASK_STATUS = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed'
}

export const TASK_STATUS_LABELS = {
  [TASK_STATUS.PENDING]: '等待处理',
  [TASK_STATUS.PROCESSING]: '处理中',
  [TASK_STATUS.COMPLETED]: '已完成',
  [TASK_STATUS.FAILED]: '处理失败'
}

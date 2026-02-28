/**
 * 应用常量定义
 */

const ENV_BASE_URL = import.meta?.env?.VITE_API_BASE_URL
const BASE_URL = ENV_BASE_URL && ENV_BASE_URL.trim() !== '' ? ENV_BASE_URL : '/api'

const NORMALIZED_BASE_URL = (BASE_URL.startsWith('http://') || BASE_URL.startsWith('https://')) 
  ? BASE_URL 
  : (BASE_URL.startsWith('/') ? BASE_URL : `/${BASE_URL}`)

if (import.meta.env.DEV) {
  console.log('[API Config] BASE_URL:', NORMALIZED_BASE_URL)
}

export const API_CONFIG = {
  BASE_URL: NORMALIZED_BASE_URL,
  TIMEOUT: 30000,
  RETRY_TIMES: 3,
  RAG_BASE_URL: '/rag-api'
}

export const UPLOAD_CONFIG = {
  MAX_SIZE: 10 * 1024 * 1024,
  ALLOWED_TYPES: ['image/jpeg', 'image/png', 'image/gif', 'application/pdf'],
  ALLOWED_EXTENSIONS: ['.jpg', '.jpeg', '.png', '.gif', '.pdf']
}

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

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/v1/auth/login',
    REGISTER: '/v1/auth/register',
    ME: '/v1/auth/me',
    LOGOUT: '/v1/auth/logout',
    PASSWORD_RESET: '/v1/auth/password/reset-request',
    PASSWORD_CONFIRM: '/v1/auth/password/reset-confirm'
  },
  STUDENT: {
    CERTIFICATE_UPLOAD: '/v1/student/certificate/upload',
    SCORES_SUMMARY: '/v1/student/scores/summary',
    SCORES_DETAIL: '/v1/student/scores/detail',
    UPLOAD_HISTORY: '/v1/student/uploads',
    ANALYSIS: '/v1/student/comprehensive/analysis',
    TREND: '/v1/student/scores/trend'
  },
  TEACHER: {
    SCORES_UPLOAD: '/v1/teacher/scores/upload',
    STUDENTS: '/v1/teacher/students',
    CLASSES: '/v1/teacher/classes',
    CLASS_STATS: '/v1/teacher/classes/stats',
    CLASS_RANKING: '/v1/teacher/classes/ranking'
  },
  ADMIN: {
    RULES_UPLOAD: '/v1/admin/rules/upload',
    RULES_LIST: '/v1/admin/rules/list',
    AI_CONFIG: '/v1/admin/ai/config',
    AI_CONFIG_TEST: '/v1/admin/ai/config/test',
    SETTINGS: '/v1/admin/settings',
    USERS: '/v1/admin/users',
    PROMPTS: '/v1/admin/prompts',
    VECTOR_DB_STATS: '/v1/vector-db/stats',
    VECTOR_DB_CLEAR: '/v1/vector-db/clear',
    VECTOR_DB_RESET: '/v1/vector-db/reset',
    VECTOR_DB_REINDEX: '/v1/vector-db/reindex',
    VECTOR_DB_COLLECTIONS: '/v1/vector-db/collections',
    VECTOR_DB_HEALTH: '/v1/vector-db/health',
    RAG_STATS: '/v1/admin/rag/stats',
    RAG_HEALTH: '/v1/admin/rag/health'
  },
  RAG: {
    CHAT: '/api/v1/chat',
    CHAT_STREAM: '/api/v1/chat/stream',
    CHAT_ASYNC: '/api/v1/chat/async',
    CHAT_STREAM_ASYNC: '/api/v1/chat/stream/async',
    DOCUMENTS: '/api/v1/documents',
    SYSTEM_INFO: '/api/v1/system/info',
    SYSTEM_HEALTH: '/api/v1/system/health',
    LLM_CONFIG: '/api/v1/system/llm/config',
    LLM_TEST: '/api/v1/system/llm/test',
    VECTOR_DB_STATS: '/api/v1/system/vector_db/stats',
    PROMPTS: '/api/v1/prompts'
  }
}

export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  UNPROCESSABLE_ENTITY: 422,
  TOO_MANY_REQUESTS: 429,
  INTERNAL_SERVER_ERROR: 500,
  BAD_GATEWAY: 502,
  SERVICE_UNAVAILABLE: 503
}

export const ERROR_CODES = {
  NETWORK_ERROR: 'NETWORK_ERROR',
  TIMEOUT: 'TIMEOUT',
  UNAUTHORIZED: 'UNAUTHORIZED',
  FORBIDDEN: 'FORBIDDEN',
  NOT_FOUND: 'NOT_FOUND',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  SERVER_ERROR: 'SERVER_ERROR',
  UNKNOWN: 'UNKNOWN'
}

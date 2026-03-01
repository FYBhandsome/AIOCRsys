/**
 * 统一日志工具
 * 
 * 功能:
 *   1. 统一的日志格式
 *   2. 发送日志到后端
 *   3. 本地存储日志
 *   4. 支持不同日志级别
 */

const LOG_LEVELS = {
  DEBUG: 0,
  INFO: 1,
  WARN: 2,
  ERROR: 3,
  FATAL: 4
}

const LOG_COLORS = {
  DEBUG: 'color: #6c757d',
  INFO: 'color: #28a745',
  WARN: 'color: #ffc107',
  ERROR: 'color: #dc3545',
  FATAL: 'color: #9c27b0'
}

class UnifiedLogger {
  constructor(options = {}) {
    this.serviceName = options.serviceName || 'frontend'
    this.level = options.level || 'INFO'
    this.enableConsole = options.enableConsole !== false
    this.enableRemote = options.enableRemote !== false
    this.enableStorage = options.enableStorage !== false
    this.maxStorageSize = options.maxStorageSize || 1000
    this.remoteUrl = options.remoteUrl || '/api/v1/logs'
    this.userId = null
    this.sessionId = null
    this.requestId = null
    this.logBuffer = []
    this.flushInterval = null
    
    this._init()
  }
  
  _init() {
    this.sessionId = this._generateId('session')
    
    if (this.enableStorage) {
      this._loadFromStorage()
    }
    
    if (this.enableRemote) {
      this.flushInterval = setInterval(() => this._flushLogs(), 5000)
      
      window.addEventListener('beforeunload', () => {
        this._flushLogs(true)
      })
    }
    
    window.addEventListener('error', (event) => {
      this.error('全局错误', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno
      })
    })
    
    window.addEventListener('unhandledrejection', (event) => {
      this.error('未处理的Promise拒绝', {
        reason: event.reason
      })
    })
  }
  
  _generateId(prefix = '') {
    const timestamp = Date.now().toString(36)
    const random = Math.random().toString(36).substring(2, 10)
    return prefix ? `${prefix}_${timestamp}${random}` : `${timestamp}${random}`
  }
  
  _formatTimestamp() {
    const now = new Date()
    return now.toISOString().replace('T', ' ').substring(0, 23)
  }
  
  _maskSensitiveData(data) {
    if (!data || typeof data !== 'object') {
      return data
    }
    
    const sensitiveKeys = ['password', 'token', 'secret', 'api_key', 'authorization', 'cookie']
    const masked = {}
    
    for (const [key, value] of Object.entries(data)) {
      const keyLower = key.toLowerCase()
      const isSensitive = sensitiveKeys.some(sk => keyLower.includes(sk))
      
      if (isSensitive) {
        masked[key] = '******'
      } else if (typeof value === 'object' && value !== null) {
        masked[key] = this._maskSensitiveData(value)
      } else if (typeof value === 'string' && value.length > 200) {
        masked[key] = value.substring(0, 200) + '...'
      } else {
        masked[key] = value
      }
    }
    
    return masked
  }
  
  _createLogEntry(level, message, data = null) {
    return {
      timestamp: this._formatTimestamp(),
      level,
      service: this.serviceName,
      message,
      data: data ? this._maskSensitiveData(data) : null,
      userId: this.userId,
      sessionId: this.sessionId,
      requestId: this.requestId,
      url: window.location.href,
      userAgent: navigator.userAgent
    }
  }
  
  _log(level, message, data = null) {
    if (LOG_LEVELS[level] < LOG_LEVELS[this.level]) {
      return
    }
    
    const entry = this._createLogEntry(level, message, data)
    
    if (this.enableConsole) {
      const style = LOG_COLORS[level] || ''
      const prefix = `%c[${entry.timestamp}] [${level}] [${this.serviceName}]`
      const logMethod = level === 'ERROR' || level === 'FATAL' ? 'error' : 
                       level === 'WARN' ? 'warn' : 'log'
      
      if (data) {
        console[logMethod](prefix, style, message, data)
      } else {
        console[logMethod](prefix, style, message)
      }
    }
    
    if (this.enableStorage || this.enableRemote) {
      this.logBuffer.push(entry)
      
      if (this.logBuffer.length > this.maxStorageSize) {
        this.logBuffer.shift()
      }
      
      if (this.enableStorage) {
        this._saveToStorage()
      }
    }
  }
  
  _loadFromStorage() {
    try {
      const stored = localStorage.getItem(`logs_${this.serviceName}`)
      if (stored) {
        this.logBuffer = JSON.parse(stored)
      }
    } catch (e) {
      this.logBuffer = []
    }
  }
  
  _saveToStorage() {
    try {
      localStorage.setItem(`logs_${this.serviceName}`, JSON.stringify(this.logBuffer))
    } catch (e) {
      if (e.name === 'QuotaExceededError') {
        this.logBuffer = this.logBuffer.slice(-Math.floor(this.maxStorageSize / 2))
        try {
          localStorage.setItem(`logs_${this.serviceName}`, JSON.stringify(this.logBuffer))
        } catch (e2) {
          // 忽略
        }
      }
    }
  }
  
  async _flushLogs(sync = false) {
    if (!this.enableRemote || this.logBuffer.length === 0) {
      return
    }
    
    const logsToSend = [...this.logBuffer]
    this.logBuffer = []
    
    try {
      if (sync && navigator.sendBeacon) {
        const blob = new Blob([JSON.stringify({ logs: logsToSend })], { type: 'application/json' })
        navigator.sendBeacon(this.remoteUrl, blob)
      } else {
        await fetch(this.remoteUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ logs: logsToSend })
        })
      }
    } catch (e) {
      this.logBuffer = [...logsToSend, ...this.logBuffer]
    }
  }
  
  setUserId(userId) {
    this.userId = userId
  }
  
  setRequestId(requestId) {
    this.requestId = requestId
  }
  
  debug(message, data = null) {
    this._log('DEBUG', message, data)
  }
  
  info(message, data = null) {
    this._log('INFO', message, data)
  }
  
  warn(message, data = null) {
    this._log('WARN', message, data)
  }
  
  error(message, data = null) {
    this._log('ERROR', message, data)
  }
  
  fatal(message, data = null) {
    this._log('FATAL', message, data)
  }
  
  logApiRequest(method, path, statusCode, duration, data = null) {
    const level = statusCode >= 500 ? 'ERROR' : statusCode >= 400 ? 'WARN' : 'INFO'
    this._log(level, `[API] ${method} ${path} -> ${statusCode}`, {
      method,
      path,
      statusCode,
      duration,
      ...data
    })
  }
  
  logUserAction(action, details = null) {
    this.info(`[用户操作] ${action}`, details)
  }
  
  logPageView(pageName, data = null) {
    this.info(`[页面访问] ${pageName}`, data)
  }
  
  logBusinessEvent(eventType, details = null) {
    this.info(`[业务事件] ${eventType}`, details)
  }
  
  getLogs() {
    return [...this.logBuffer]
  }
  
  clearLogs() {
    this.logBuffer = []
    if (this.enableStorage) {
      localStorage.removeItem(`logs_${this.serviceName}`)
    }
  }
  
  setLevel(level) {
    if (LOG_LEVELS[level] !== undefined) {
      this.level = level
    }
  }
}

const logger = new UnifiedLogger({
  serviceName: 'frontend',
  level: import.meta.env?.DEV ? 'DEBUG' : 'INFO',
  enableConsole: true,
  enableRemote: !import.meta.env?.DEV,
  enableStorage: true
})

export default logger

export {
  UnifiedLogger,
  LOG_LEVELS
}

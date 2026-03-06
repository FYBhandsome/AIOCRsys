import { describe, it, expect, vi, beforeEach } from 'vitest'
import MockAdapter from 'axios-mock-adapter'
import { authAPI, studentAPI, teacherAPI, adminAPI, ragAPI, commonAPI, dataImportAPI, comprehensiveScoreAPI, excelFillAPI, fieldMappingAPI, scoreUploadAPI, certificateAPI, fileManagementAPI } from '@/services/api'
import { API_ENDPOINTS } from '@/constants'
import api, { showGlobalLoading, hideGlobalLoading, ragApi as ragApiInstance } from '@/services/api'

describe('API服务基础功能测试', () => {
  let mock

  beforeEach(() => {
    mock = new MockAdapter(api)
    vi.clearAllMocks()
  })

  describe('Loading状态管理', () => {
    it('应该正确显示和隐藏加载状态', () => {
      expect(typeof showGlobalLoading).toBe('function')
      expect(typeof hideGlobalLoading).toBe('function')
    })
  })

  describe('commonAPI', () => {
    it('应该正确执行GET请求', async () => {
      const testData = { message: 'success' }
      mock.onGet('/test-url').reply(200, testData)
      
      const result = await commonAPI.get('/test-url')
      expect(result).toEqual(testData)
    })

    it('应该正确执行POST请求', async () => {
      const testData = { message: 'success' }
      const payload = { data: 'test' }
      mock.onPost('/test-url', payload).reply(200, testData)
      
      const result = await commonAPI.post('/test-url', payload)
      expect(result).toEqual(testData)
    })
  })
})

describe('认证API测试', () => {
  let mock

  beforeEach(() => {
    mock = new MockAdapter(api)
    vi.clearAllMocks()
  })

  describe('login', () => {
    it('应该成功登录并返回token', async () => {
      const mockResponse = { token: 'test-token', user: { username: 'test' } }
      mock.onPost(API_ENDPOINTS.AUTH.LOGIN).reply(200, mockResponse)
      
      const result = await authAPI.login('testuser', 'testpass')
      expect(result).toEqual(mockResponse)
    })

    it('应该处理登录失败', async () => {
      mock.onPost(API_ENDPOINTS.AUTH.LOGIN).reply(401, { error: 'Invalid credentials' })
      
      await expect(authAPI.login('wrong', 'wrong')).rejects.toThrow()
    })
  })

  describe('getUserInfo', () => {
    it('应该成功获取用户信息', async () => {
      const mockResponse = { username: 'testuser', role: 'admin' }
      mock.onGet(API_ENDPOINTS.AUTH.ME).reply(200, mockResponse)
      
      const result = await authAPI.getUserInfo()
      expect(result).toEqual(mockResponse)
    })
  })
})

describe('学生API测试', () => {
  let mock

  beforeEach(() => {
    mock = new MockAdapter(api)
    vi.clearAllMocks()
  })

  describe('getScoresSummary', () => {
    it('应该成功获取成绩摘要', async () => {
      const mockResponse = { gpa: 3.8, rank: 5 }
      mock.onGet(API_ENDPOINTS.STUDENT.SCORES_SUMMARY).reply(200, mockResponse)
      
      const result = await studentAPI.getScoresSummary()
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getScoresDetail', () => {
    it('应该成功获取成绩详情', async () => {
      const mockResponse = { scores: [{ subject: 'Math', score: 95 }] }
      mock.onGet(API_ENDPOINTS.STUDENT.SCORES_DETAIL).reply(200, mockResponse)
      
      const result = await studentAPI.getScoresDetail()
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getUploadHistory', () => {
    it('应该成功获取上传历史', async () => {
      const mockResponse = { history: [] }
      mock.onGet(API_ENDPOINTS.STUDENT.UPLOAD_HISTORY).reply(200, mockResponse)
      
      const result = await studentAPI.getUploadHistory()
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getComprehensiveAnalysis', () => {
    it('应该成功获取综合分析', async () => {
      const mockResponse = { analysis: {} }
      mock.onGet(API_ENDPOINTS.STUDENT.ANALYSIS).reply(200, mockResponse)
      
      const result = await studentAPI.getComprehensiveAnalysis()
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getScoreTrend', () => {
    it('应该成功获取成绩趋势', async () => {
      const mockResponse = { trend: [] }
      mock.onGet(API_ENDPOINTS.STUDENT.TREND).reply(200, mockResponse)
      
      const result = await studentAPI.getScoreTrend()
      expect(result).toEqual(mockResponse)
    })
  })
})

describe('教师API测试', () => {
  let mock

  beforeEach(() => {
    mock = new MockAdapter(api)
    vi.clearAllMocks()
  })

  describe('getClasses', () => {
    it('应该成功获取班级列表', async () => {
      const mockResponse = { classes: [{ id: 1, name: 'Class 1' }] }
      mock.onGet(API_ENDPOINTS.TEACHER.CLASSES).reply(200, mockResponse)
      
      const result = await teacherAPI.getClasses()
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getStudents', () => {
    it('应该成功获取学生列表', async () => {
      const mockResponse = { students: [{ id: 1, name: 'Student 1' }] }
      mock.onGet(API_ENDPOINTS.TEACHER.STUDENTS).reply(200, mockResponse)
      
      const result = await teacherAPI.getStudents(1)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getClassStats', () => {
    it('应该成功获取班级统计', async () => {
      const mockResponse = { stats: { average: 85 } }
      mock.onGet(API_ENDPOINTS.TEACHER.CLASS_STATS).reply(200, mockResponse)
      
      const result = await teacherAPI.getClassStats(1)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getClassRanking', () => {
    it('应该成功获取班级排名', async () => {
      const mockResponse = { ranking: [] }
      mock.onGet(API_ENDPOINTS.TEACHER.CLASS_RANKING).reply(200, mockResponse)
      
      const result = await teacherAPI.getClassRanking(1)
      expect(result).toEqual(mockResponse)
    })
  })
})

describe('管理员API测试', () => {
  let mock

  beforeEach(() => {
    mock = new MockAdapter(api)
    vi.clearAllMocks()
  })

  describe('getRuleDocuments', () => {
    it('应该成功获取规则文档列表', async () => {
      const mockResponse = { documents: [] }
      mock.onGet(API_ENDPOINTS.ADMIN.RULES_LIST).reply(200, mockResponse)
      
      const result = await adminAPI.getRuleDocuments()
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getAIConfig', () => {
    it('应该成功获取AI配置', async () => {
      const mockResponse = { config: {} }
      mock.onGet(API_ENDPOINTS.ADMIN.AI_CONFIG).reply(200, mockResponse)
      
      const result = await adminAPI.getAIConfig()
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getSystemSettings', () => {
    it('应该成功获取系统设置', async () => {
      const mockResponse = { settings: {} }
      mock.onGet(API_ENDPOINTS.ADMIN.SETTINGS).reply(200, mockResponse)
      
      const result = await adminAPI.getSystemSettings()
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getUsers', () => {
    it('应该成功获取用户列表', async () => {
      const mockResponse = { users: [] }
      mock.onGet(API_ENDPOINTS.ADMIN.USERS).reply(200, mockResponse)
      
      const result = await adminAPI.getUsers()
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getPrompts', () => {
    it('应该成功获取提示词', async () => {
      const mockResponse = { prompts: [] }
      mock.onGet(API_ENDPOINTS.ADMIN.PROMPTS).reply(200, mockResponse)
      
      const result = await adminAPI.getPrompts()
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getVectorDBStats', () => {
    it('应该成功获取向量数据库统计', async () => {
      const mockResponse = { stats: {} }
      mock.onGet(API_ENDPOINTS.ADMIN.VECTOR_DB_STATS).reply(200, mockResponse)
      
      const result = await adminAPI.getVectorDBStats()
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getRAGStats', () => {
    it('应该成功获取RAG统计', async () => {
      const mockResponse = { stats: {} }
      mock.onGet(API_ENDPOINTS.ADMIN.RAG_STATS).reply(200, mockResponse)
      
      const result = await adminAPI.getRAGStats()
      expect(result).toEqual(mockResponse)
    })
  })
})

describe('RAG API测试', () => {
  let mock

  beforeEach(() => {
    mock = new MockAdapter(ragApiInstance)
    vi.clearAllMocks()
  })

  describe('chat', () => {
    it('应该成功进行AI对话', async () => {
      const mockResponse = { answer: '这是回答', sources: [] }
      mock.onPost(API_ENDPOINTS.RAG.CHAT).reply(200, mockResponse)
      
      const result = await ragAPI.chat('你好', [], true)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getDocuments', () => {
    it('应该成功获取文档列表', async () => {
      const mockResponse = { documents: [] }
      mock.onGet(API_ENDPOINTS.RAG.DOCUMENTS).reply(200, mockResponse)
      
      const result = await ragAPI.getDocuments()
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getSystemInfo', () => {
    it('应该成功获取系统信息', async () => {
      const mockResponse = { info: {} }
      mock.onGet(API_ENDPOINTS.RAG.SYSTEM_INFO).reply(200, mockResponse)
      
      const result = await ragAPI.getSystemInfo()
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getSystemHealth', () => {
    it('应该成功获取系统健康状态', async () => {
      const mockResponse = { healthy: true }
      mock.onGet(API_ENDPOINTS.RAG.SYSTEM_HEALTH).reply(200, mockResponse)
      
      const result = await ragAPI.getSystemHealth()
      expect(result).toEqual(mockResponse)
    })
  })
})

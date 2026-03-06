import { describe, it, expect, vi, beforeEach } from 'vitest'
import MockAdapter from 'axios-mock-adapter'
import api from '@/services/api'
import { 
  dataImportAPI, 
  comprehensiveScoreAPI, 
  excelFillAPI, 
  fieldMappingAPI, 
  scoreUploadAPI, 
  certificateAPI, 
  fileManagementAPI 
} from '@/services/api'

describe('数据导入API测试', () => {
  let mock

  beforeEach(() => {
    mock = new MockAdapter(api)
    vi.clearAllMocks()
  })

  describe('importExcel', () => {
    it('应该成功导入Excel文件', async () => {
      const mockResponse = { success: true, imported: 10 }
      const file = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mock.onPost('/v1/data-import/excel').reply(200, mockResponse)
      
      const result = await dataImportAPI.importExcel(file, { academic_year: '2024', semester: '1' })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getTemplate', () => {
    it('应该成功获取导入模板', async () => {
      const mockResponse = { template: 'base64-data' }
      mock.onGet('/v1/data-import/template').reply(200, mockResponse)
      
      const result = await dataImportAPI.getTemplate()
      expect(result).toEqual(mockResponse)
    })
  })

  describe('previewExcel', () => {
    it('应该成功预览Excel数据', async () => {
      const mockResponse = { preview: [] }
      const file = new File(['test'], 'test.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mock.onPost('/v1/data-import/preview').reply(200, mockResponse)
      
      const result = await dataImportAPI.previewExcel(file, 10)
      expect(result).toEqual(mockResponse)
    })
  })
})

describe('综合成绩API测试', () => {
  let mock

  beforeEach(() => {
    mock = new MockAdapter(api)
    vi.clearAllMocks()
  })

  describe('calculateStudentScore', () => {
    it('应该成功计算学生综合成绩', async () => {
      const mockResponse = { score: 95, details: {} }
      mock.onPost('/v1/comprehensive-score/calculate/student/1').reply(200, mockResponse)
      
      const result = await comprehensiveScoreAPI.calculateStudentScore(1, '2024', '1')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getStudentScore', () => {
    it('应该成功获取学生综合成绩', async () => {
      const mockResponse = { score: 90 }
      mock.onGet('/v1/comprehensive-score/student/1').reply(200, mockResponse)
      
      const result = await comprehensiveScoreAPI.getStudentScore(1, '2024', '1')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getClassRanking', () => {
    it('应该成功获取班级排名', async () => {
      const mockResponse = { ranking: [] }
      mock.onGet('/v1/comprehensive-score/class/1/ranking').reply(200, mockResponse)
      
      const result = await comprehensiveScoreAPI.getClassRanking(1, '2024', '1')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getConfigs', () => {
    it('应该成功获取配置列表', async () => {
      const mockResponse = { configs: [] }
      mock.onGet('/v1/comprehensive-score/config/list').reply(200, mockResponse)
      
      const result = await comprehensiveScoreAPI.getConfigs()
      expect(result).toEqual(mockResponse)
    })
  })

  describe('createConfig', () => {
    it('应该成功创建配置', async () => {
      const mockResponse = { id: 1, name: 'Test Config' }
      const configData = { name: 'Test Config', weights: {} }
      mock.onPost('/v1/comprehensive-score/config').reply(201, mockResponse)
      
      const result = await comprehensiveScoreAPI.createConfig(configData)
      expect(result).toEqual(mockResponse)
    })
  })
})

describe('Excel填充API测试', () => {
  let mock

  beforeEach(() => {
    mock = new MockAdapter(api)
    vi.clearAllMocks()
  })

  describe('fillFromTemplate', () => {
    it('应该成功从模板填充数据', async () => {
      const templateFile = new File(['template'], 'template.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      const rawDataFile = new File(['data'], 'data.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      mock.onPost('/v1/excel-fill/from-template').reply(200, new Blob())
      
      const result = await excelFillAPI.fillFromTemplate(templateFile, rawDataFile)
      expect(result).toBeDefined()
    })
  })

  describe('analyzeCertificate', () => {
    it('应该成功分析证书文本', async () => {
      const mockResponse = { score: 5, category: '竞赛' }
      mock.onPost('/v1/excel-fill/analyze-certificate').reply(200, mockResponse)
      
      const result = await excelFillAPI.analyzeCertificate('证书文本', '1', '张三')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('calculateScore', () => {
    it('应该成功计算分数', async () => {
      const mockResponse = { total_score: 95 }
      const data = { student_id: '1', student_name: '张三', class_name: '一班' }
      mock.onPost('/v1/excel-fill/calculate-score').reply(200, mockResponse)
      
      const result = await excelFillAPI.calculateScore(data)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getTemplateColumns', () => {
    it('应该成功获取模板列', async () => {
      const mockResponse = { columns: [] }
      mock.onGet('/v1/excel-fill/template-columns').reply(200, mockResponse)
      
      const result = await excelFillAPI.getTemplateColumns()
      expect(result).toEqual(mockResponse)
    })
  })
})

describe('字段映射API测试', () => {
  let mock

  beforeEach(() => {
    mock = new MockAdapter(api)
    vi.clearAllMocks()
  })

  describe('processAndFill', () => {
    it('应该成功处理并填充', async () => {
      const sourceFile = new File(['source'], 'source.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      const templateFile = new File(['template'], 'template.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      const mockResponse = { success: true }
      mock.onPost('/v1/field-mapping/process').reply(200, mockResponse)
      
      const result = await fieldMappingAPI.processAndFill(sourceFile, templateFile)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getSourceFields', () => {
    it('应该成功获取源字段', async () => {
      const mockResponse = { fields: [] }
      mock.onGet('/v1/field-mapping/source-fields').reply(200, mockResponse)
      
      const result = await fieldMappingAPI.getSourceFields()
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getTargetFields', () => {
    it('应该成功获取目标字段', async () => {
      const mockResponse = { fields: [] }
      mock.onGet('/v1/field-mapping/target-fields').reply(200, mockResponse)
      
      const result = await fieldMappingAPI.getTargetFields()
      expect(result).toEqual(mockResponse)
    })
  })
})

describe('成绩上传API测试', () => {
  let mock

  beforeEach(() => {
    mock = new MockAdapter(api)
    vi.clearAllMocks()
  })

  describe('upload', () => {
    it('应该成功上传成绩', async () => {
      const file = new File(['data'], 'scores.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      const mockResponse = { id: 1, status: 'uploaded' }
      mock.onPost('/v1/score-upload/upload').reply(200, mockResponse)
      
      const result = await scoreUploadAPI.upload(file, { academic_year: '2024', semester: '1', uploaded_by: 'teacher1' })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getHistory', () => {
    it('应该成功获取上传历史', async () => {
      const mockResponse = { history: [] }
      mock.onGet('/v1/score-upload/history/1').reply(200, mockResponse)
      
      const result = await scoreUploadAPI.getHistory('1')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getUploadRecords', () => {
    it('应该成功获取上传记录', async () => {
      const mockResponse = { records: [] }
      mock.onGet('/v1/score-upload/upload-records').reply(200, mockResponse)
      
      const result = await scoreUploadAPI.getUploadRecords()
      expect(result).toEqual(mockResponse)
    })
  })

  describe('preview', () => {
    it('应该成功预览成绩', async () => {
      const file = new File(['data'], 'scores.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      const mockResponse = { preview: [] }
      mock.onPost('/v1/score-upload/preview').reply(200, mockResponse)
      
      const result = await scoreUploadAPI.preview(file, 10)
      expect(result).toEqual(mockResponse)
    })
  })
})

describe('证书API测试', () => {
  let mock

  beforeEach(() => {
    mock = new MockAdapter(api)
    vi.clearAllMocks()
  })

  describe('upload', () => {
    it('应该成功上传证书', async () => {
      const file = new File(['cert'], 'cert.jpg', { type: 'image/jpeg' })
      const mockResponse = { id: 1, status: 'uploaded' }
      mock.onPost('/v1/certificate/upload').reply(200, mockResponse)
      
      const result = await certificateAPI.upload([file], { student_id: '1' })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getStudentCertificates', () => {
    it('应该成功获取学生证书', async () => {
      const mockResponse = { certificates: [] }
      mock.onGet('/v1/certificate/student/1').reply(200, mockResponse)
      
      const result = await certificateAPI.getStudentCertificates('1')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getDetail', () => {
    it('应该成功获取证书详情', async () => {
      const mockResponse = { id: 1, title: '证书' }
      mock.onGet('/v1/certificate/1').reply(200, mockResponse)
      
      const result = await certificateAPI.getDetail('1')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('delete', () => {
    it('应该成功删除证书', async () => {
      const mockResponse = { success: true }
      mock.onDelete('/v1/certificate/1').reply(200, mockResponse)
      
      const result = await certificateAPI.delete('1')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('update', () => {
    it('应该成功更新证书', async () => {
      const mockResponse = { id: 1, title: '更新的证书' }
      const data = { title: '更新的证书' }
      mock.onPut('/v1/certificate/1').reply(200, mockResponse)
      
      const result = await certificateAPI.update('1', data)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getStatistics', () => {
    it('应该成功获取统计信息', async () => {
      const mockResponse = { total: 10, approved: 8 }
      mock.onGet('/v1/certificate/statistics/1').reply(200, mockResponse)
      
      const result = await certificateAPI.getStatistics('1')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('batchUpdateStatus', () => {
    it('应该成功批量更新状态', async () => {
      const mockResponse = { updated: 5 }
      mock.onPost('/v1/certificate/batch-status').reply(200, mockResponse)
      
      const result = await certificateAPI.batchUpdateStatus(['1', '2'], 'approved')
      expect(result).toEqual(mockResponse)
    })
  })
})

describe('文件管理API测试', () => {
  let mock

  beforeEach(() => {
    mock = new MockAdapter(api)
    vi.clearAllMocks()
  })

  describe('upload', () => {
    it('应该成功上传文件', async () => {
      const file = new File(['data'], 'file.txt', { type: 'text/plain' })
      const mockResponse = { id: 1, filename: 'file.txt' }
      mock.onPost('/v1/file/upload').reply(200, mockResponse)
      
      const result = await fileManagementAPI.upload(file, { file_type: 'document', owner_id: '1' })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('uploadMultiple', () => {
    it('应该成功上传多个文件', async () => {
      const files = [
        new File(['data1'], 'file1.txt', { type: 'text/plain' }),
        new File(['data2'], 'file2.txt', { type: 'text/plain' })
      ]
      const mockResponse = { uploaded: 2 }
      mock.onPost('/v1/file/upload-multiple').reply(200, mockResponse)
      
      const result = await fileManagementAPI.uploadMultiple(files, { file_type: 'document', owner_id: '1' })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('initChunkUpload', () => {
    it('应该成功初始化分片上传', async () => {
      const mockResponse = { file_id: '1', chunk_size: 1048576 }
      mock.onPost('/v1/file/chunk/init').reply(200, mockResponse)
      
      const result = await fileManagementAPI.initChunkUpload('largefile.zip', 10485760, 'application/zip', '1')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('download', () => {
    it('应该成功下载文件', async () => {
      mock.onGet('/v1/file/download/1').reply(200, new Blob())
      
      const result = await fileManagementAPI.download('1')
      expect(result).toBeDefined()
    })
  })

  describe('getInfo', () => {
    it('应该成功获取文件信息', async () => {
      const mockResponse = { id: 1, filename: 'test.txt' }
      mock.onGet('/v1/file/info/1').reply(200, mockResponse)
      
      const result = await fileManagementAPI.getInfo('1')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('list', () => {
    it('应该成功列出文件', async () => {
      const mockResponse = { files: [] }
      mock.onGet('/v1/file/list').reply(200, mockResponse)
      
      const result = await fileManagementAPI.list({ owner_id: '1' })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('delete', () => {
    it('应该成功删除文件', async () => {
      const mockResponse = { success: true }
      mock.onDelete('/v1/file/1').reply(200, mockResponse)
      
      const result = await fileManagementAPI.delete('1')
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getDownloadHistory', () => {
    it('应该成功获取下载历史', async () => {
      const mockResponse = { history: [] }
      mock.onGet('/v1/file/download-history').reply(200, mockResponse)
      
      const result = await fileManagementAPI.getDownloadHistory()
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getCategories', () => {
    it('应该成功获取文件分类', async () => {
      const mockResponse = { categories: [] }
      mock.onGet('/v1/file/categories').reply(200, mockResponse)
      
      const result = await fileManagementAPI.getCategories()
      expect(result).toEqual(mockResponse)
    })
  })
})

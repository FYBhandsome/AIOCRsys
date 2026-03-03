<template>
  <div class="score-upload">
    <FileUpload
      ref="fileUploadRef"
      title="上传成绩单"
      description="支持 Excel 文件或成绩单截图"
      accept-types=".xlsx,.xls,.jpg,.jpeg,.png"
      accept-tip="支持 .xlsx、.xls、.jpg、.jpeg 或 .png 格式的文件，单个文件不超过20MB"
      submit-button-text="上传并识别"
      :initial-form="initialForm"
      :submit-handler="submitHandler"
      :validator="validateForm"
      :max-size-m-b="20"
      :allowed-mime-types="allowedMimeTypes"
      @file-change="handleFileChange"
      @submit-success="handleSubmitSuccess"
      @upload-error="handleUploadError"
    >
      <template #form-fields="{ form }">
        <el-form-item label="学期">
          <el-select v-model="form.semester" placeholder="请选择学期">
            <el-option label="2023-2024学年第一学期" value="2023-1"></el-option>
            <el-option label="2023-2024学年第二学期" value="2023-2"></el-option>
            <el-option label="2024-2025学年第一学期" value="2024-1"></el-option>
            <el-option label="2024-2025学年第二学期" value="2024-2"></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="文件类型">
          <el-radio-group v-model="form.fileType">
            <el-radio label="excel">Excel 文件</el-radio>
            <el-radio label="image">成绩单截图</el-radio>
          </el-radio-group>
        </el-form-item>
      </template>
      
      <template #ai-info>
        <AIInfoCard
          title="AI 识别说明"
          :steps="dynamicSteps"
        />
      </template>
    </FileUpload>
    
    <el-card v-if="uploadResult" class="result-card">
      <template #header>
        <div class="result-header">
          <span>上传结果</span>
          <el-tag :type="uploadResult.success ? 'success' : 'danger'">
            {{ uploadResult.success ? '成功' : '部分失败' }}
          </el-tag>
        </div>
      </template>
      
      <el-row :gutter="20" class="result-stats">
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value">{{ uploadResult.total_count || 0 }}</div>
            <div class="stat-label">总记录数</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item success">
            <div class="stat-value">{{ uploadResult.success_count || 0 }}</div>
            <div class="stat-label">成功导入</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item error">
            <div class="stat-value">{{ uploadResult.failed_count || 0 }}</div>
            <div class="stat-label">导入失败</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value">{{ uploadResult.skipped_count || 0 }}</div>
            <div class="stat-label">跳过记录</div>
          </div>
        </el-col>
      </el-row>
      
      <div v-if="uploadResult.errors && uploadResult.errors.length > 0" class="error-list">
        <el-divider content-position="left">错误详情</el-divider>
        <el-table :data="paginatedErrors" style="width: 100%" max-height="300" border>
          <el-table-column prop="row" label="行号" width="80" align="center" />
          <el-table-column prop="field" label="字段" width="120" />
          <el-table-column prop="message" label="错误信息" min-width="200">
            <template #default="{ row }">
              <span>{{ row.message }}</span>
              <el-tooltip v-if="row.suggestion" :content="row.suggestion" placement="top">
                <el-icon class="suggestion-icon"><InfoFilled /></el-icon>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" align="center">
            <template #default="{ row }">
              <el-button type="primary" link size="small" @click="showErrorDetail(row)">
                详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <div v-if="uploadResult.errors.length > errorPageSize" class="pagination-container">
          <el-pagination
            v-model:current-page="errorCurrentPage"
            :page-size="errorPageSize"
            :total="uploadResult.errors.length"
            layout="total, prev, pager, next"
            small
          />
        </div>
      </div>
      
      <div v-if="uploadResult.preview && uploadResult.preview.length > 0" class="preview-actions">
        <el-divider />
        <el-button type="primary" @click="showPreviewDialog">
          <el-icon><View /></el-icon>
          查看导入数据预览
        </el-button>
      </div>
    </el-card>
    
    <el-dialog 
      v-model="previewDialogVisible" 
      title="导入数据预览（前10条）" 
      width="80%"
      destroy-on-close
    >
      <div class="preview-dialog-content">
        <el-alert 
          type="info" 
          :closable="false"
          show-icon
          style="margin-bottom: 16px;"
        >
          <template #title>
            共导入 {{ uploadResult?.total_count || 0 }} 条记录，以下展示前10条数据预览
          </template>
        </el-alert>
        
        <el-table 
          :data="previewDialogData" 
          style="width: 100%" 
          max-height="500" 
          border
          stripe
        >
          <el-table-column
            v-for="column in previewColumns"
            :key="column.prop"
            :prop="column.prop"
            :label="column.label"
            :min-width="column.width || 100"
            show-overflow-tooltip
            align="center"
          />
        </el-table>
      </div>
      
      <template #footer>
        <el-button @click="previewDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="exportPreviewData">
          <el-icon><Download /></el-icon>
          导出数据
        </el-button>
      </template>
    </el-dialog>
    
    <el-dialog 
      v-model="errorDetailDialogVisible" 
      title="错误详情" 
      width="500px"
    >
      <el-descriptions :column="1" border v-if="currentErrorDetail">
        <el-descriptions-item label="行号">{{ currentErrorDetail.row }}</el-descriptions-item>
        <el-descriptions-item label="字段">{{ currentErrorDetail.field }}</el-descriptions-item>
        <el-descriptions-item label="错误信息">{{ currentErrorDetail.message }}</el-descriptions-item>
        <el-descriptions-item label="当前值" v-if="currentErrorDetail.value">
          {{ currentErrorDetail.value }}
        </el-descriptions-item>
        <el-descriptions-item label="修正建议" v-if="currentErrorDetail.suggestion">
          <el-tag type="warning">{{ currentErrorDetail.suggestion }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>
      
      <template #footer>
        <el-button type="primary" @click="errorDetailDialogVisible = false">确定</el-button>
      </template>
    </el-dialog>
    
    <el-dialog 
      v-model="retryDialogVisible" 
      title="上传失败" 
      width="500px"
      :close-on-click-modal="false"
    >
      <div class="retry-dialog-content">
        <el-icon class="warning-icon"><WarningFilled /></el-icon>
        <p class="error-message">{{ retryErrorMessage }}</p>
        
        <el-divider v-if="retryCount > 0" />
        
        <div v-if="retryCount > 0" class="retry-info">
          <el-progress 
            :percentage="retryProgress" 
            :format="() => `已重试 ${retryCount}/${maxRetryCount} 次`"
            :status="retryCount >= maxRetryCount ? 'exception' : ''"
          />
        </div>
        
        <el-alert 
          v-if="retrySuggestion" 
          type="warning" 
          :closable="false"
          show-icon
          style="margin-top: 16px;"
        >
          <template #title>修正建议</template>
          {{ retrySuggestion }}
        </el-alert>
      </div>
      
      <template #footer>
        <el-button @click="cancelRetry">取消</el-button>
        <el-button 
          type="primary" 
          @click="handleRetry"
          :loading="isRetrying"
          :disabled="retryCount >= maxRetryCount"
        >
          {{ retryCount >= maxRetryCount ? '已达最大重试次数' : '重试' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { WarningFilled, InfoFilled, View, Download } from '@element-plus/icons-vue'
import FileUpload from '@/components/FileUpload.vue'
import AIInfoCard from '@/components/AIInfoCard.vue'
import { teacherAPI } from '@/services/api'

const initialForm = {
  semester: '',
  fileType: 'excel'
}

const allowedMimeTypes = [
  'image/jpeg',
  'image/png',
  'image/jpg',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-excel'
]

const fileUploadRef = ref(null)
const uploadResult = ref(null)
const previewData = ref([])
const previewColumns = ref([])
const retryDialogVisible = ref(false)
const retryErrorMessage = ref('')
const retrySuggestion = ref('')
const lastFormData = ref(null)
const lastFile = ref(null)
const isRetrying = ref(false)
const retryCount = ref(0)
const maxRetryCount = 3

const previewDialogVisible = ref(false)
const errorDetailDialogVisible = ref(false)
const currentErrorDetail = ref(null)
const errorCurrentPage = ref(1)
const errorPageSize = 10

const dynamicSteps = computed(() => {
  return [
    initialForm.fileType === 'excel' 
      ? '直接解析 Excel 文件中的成绩数据' 
      : '使用 OCR 技术识别成绩单截图中的文字信息',
    '通过大模型理解课程名称和成绩含义',
    '自动匹配综测规则中的学业成绩计算方式'
  ]
})

const retryProgress = computed(() => {
  return (retryCount.value / maxRetryCount) * 100
})

const paginatedErrors = computed(() => {
  if (!uploadResult.value?.errors) return []
  const start = (errorCurrentPage.value - 1) * errorPageSize
  const end = start + errorPageSize
  return uploadResult.value.errors.slice(start, end)
})

const previewDialogData = computed(() => {
  return uploadResult.value?.preview?.slice(0, 10) || []
})

const validateForm = (form) => {
  if (!form.semester) {
    ElMessage.warning('请选择学期')
    return false
  }
  return true
}

const parseSemester = (semester) => {
  if (!semester) return { academic_year: '', semester: '' }
  
  const parts = semester.split('-')
  if (parts.length === 2) {
    return {
      academic_year: parts[0],
      semester: parts[1]
    }
  }
  return { academic_year: semester, semester: '1' }
}

const submitHandler = async (form, file, onProgress) => {
  const { academic_year, semester } = parseSemester(form.semester)
  
  const formData = new FormData()
  formData.append('file', file)
  formData.append('academic_year', academic_year)
  formData.append('semester', semester)
  formData.append('file_type', form.fileType)
  
  lastFormData.value = { ...form }
  lastFile.value = file
  retryCount.value = 0
  
  return await executeUpload(formData, onProgress)
}

const executeUpload = async (formData, onProgress) => {
  try {
    const response = await teacherAPI.uploadScores(formData, onProgress)
    
    uploadResult.value = {
      success: response.success !== false,
      total_count: response.total_count || response.data?.total_count || 0,
      success_count: response.success_count || response.data?.success_count || 0,
      failed_count: response.failed_count || response.data?.failed_count || 0,
      skipped_count: response.skipped_count || response.data?.skipped_count || 0,
      errors: formatErrors(response.errors || response.data?.errors || []),
      preview: response.preview || response.data?.preview || [],
      message: response.message || response.data?.message || ''
    }
    
    if (uploadResult.value.preview && uploadResult.value.preview.length > 0) {
      setPreviewColumns(uploadResult.value.preview[0])
    }
    
    if (uploadResult.value.success) {
      ElMessage.success(uploadResult.value.message || '成绩上传成功')
    } else {
      ElMessage.warning(uploadResult.value.message || '部分数据导入失败，请查看错误详情')
    }
    
    return response
  } catch (error) {
    console.error('上传失败:', error)
    
    const errorInfo = getErrorInfo(error)
    retryErrorMessage.value = errorInfo.message
    retrySuggestion.value = errorInfo.suggestion
    
    if (shouldAutoRetry(error) && retryCount.value < maxRetryCount) {
      return await autoRetry(formData, onProgress)
    } else if (shouldShowRetryDialog(error)) {
      retryDialogVisible.value = true
    }
    
    throw error
  }
}

const formatErrors = (errors) => {
  if (!Array.isArray(errors)) return []
  
  return errors.map(error => {
    if (typeof error === 'string') {
      return { row: '-', field: '-', message: error, suggestion: '' }
    }
    return {
      row: error.row || error.line || '-',
      field: error.field || error.column || '-',
      message: error.message || error.error || '未知错误',
      value: error.value || null,
      suggestion: error.suggestion || getSuggestionForError(error)
    }
  })
}

const getSuggestionForError = (error) => {
  const field = (error.field || error.column || '').toLowerCase()
  const message = (error.message || error.error || '').toLowerCase()
  
  if (field.includes('student_id') || message.includes('学号')) {
    return '请检查学号格式，确保为有效的学号'
  }
  if (field.includes('score') || message.includes('成绩')) {
    return '成绩应为0-100之间的数字'
  }
  if (field.includes('credit') || message.includes('学分')) {
    return '学分应为正数'
  }
  if (message.includes('格式') || message.includes('format')) {
    return '请检查数据格式是否正确'
  }
  
  return null
}

const getErrorInfo = (error) => {
  if (error.formatted) {
    return {
      message: error.message || '上传失败',
      suggestion: error.suggestion || null,
      code: error.code || null,
      details: error.details || []
    }
  }
  
  if (error.response) {
    const { status, data } = error.response
    
    const errorMessages = {
      400: data?.detail || '请求参数错误，请检查文件格式',
      401: '登录已过期，请重新登录',
      403: '没有上传权限',
      404: '上传接口不存在',
      413: '文件大小超过服务器限制',
      422: data?.detail || '文件内容格式不正确，请检查数据格式',
      500: '服务器内部错误，请稍后重试',
      502: '服务暂时不可用，请稍后重试',
      503: '服务正在维护，请稍后重试'
    }
    
    const suggestions = {
      400: '请确保文件格式正确，支持 .xlsx、.xls、.jpg、.jpeg、.png 格式',
      413: '请压缩文件大小或分批上传',
      422: '请检查Excel文件中的数据格式，确保必填字段已填写'
    }
    
    return {
      message: errorMessages[status] || `上传失败 (${status})`,
      suggestion: suggestions[status] || data?.suggestion || null,
      code: `HTTP_${status}`,
      details: data?.details || []
    }
  }
  
  if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
    return {
      message: '上传超时，请检查网络连接或尝试上传较小的文件',
      suggestion: '建议检查网络连接，或尝试压缩文件后重新上传',
      code: 'TIMEOUT_ERROR'
    }
  }
  
  if (error.message?.includes('Network Error')) {
    return {
      message: '网络连接失败，请检查网络设置',
      suggestion: '请检查网络连接是否正常，然后重试',
      code: 'NETWORK_ERROR'
    }
  }
  
  return {
    message: error.message || '上传失败，请稍后重试',
    suggestion: null,
    code: 'UNKNOWN_ERROR'
  }
}

const shouldAutoRetry = (error) => {
  if (!error.response) {
    return error.code === 'ECONNABORTED' || 
           error.code === 'TIMEOUT_ERROR' ||
           error.code === 'NETWORK_ERROR' ||
           error.message?.includes('timeout') ||
           error.message?.includes('Network Error')
  }
  
  const autoRetryStatuses = [502, 503, 504]
  return autoRetryStatuses.includes(error.response.status)
}

const shouldShowRetryDialog = (error) => {
  if (retryCount.value >= maxRetryCount) return false
  
  if (!error.response) {
    return true
  }
  
  const retryableStatuses = [502, 503, 504, 408, 429]
  return retryableStatuses.includes(error.response.status)
}

const autoRetry = async (formData, onProgress) => {
  retryCount.value++
  
  ElMessage.info(`网络异常，正在自动重试 (${retryCount.value}/${maxRetryCount})...`)
  
  const delay = 1000 * Math.pow(2, retryCount.value - 1)
  await new Promise(resolve => setTimeout(resolve, delay))
  
  return await executeUpload(formData, onProgress)
}

const handleRetry = async () => {
  if (retryCount.value >= maxRetryCount) {
    ElMessage.warning('已达到最大重试次数')
    return
  }
  
  isRetrying.value = true
  retryCount.value++
  
  try {
    const { academic_year, semester } = parseSemester(lastFormData.value.semester)
    
    const formData = new FormData()
    formData.append('file', lastFile.value)
    formData.append('academic_year', academic_year)
    formData.append('semester', semester)
    formData.append('file_type', lastFormData.value.fileType)
    
    await executeUpload(formData, () => {})
    retryDialogVisible.value = false
  } catch (error) {
    console.error('重试失败:', error)
    
    const errorInfo = getErrorInfo(error)
    retryErrorMessage.value = errorInfo.message
    retrySuggestion.value = errorInfo.suggestion
    
    if (retryCount.value >= maxRetryCount) {
      ElMessage.error('已达到最大重试次数，请稍后再试或联系管理员')
    }
  } finally {
    isRetrying.value = false
  }
}

const cancelRetry = () => {
  retryDialogVisible.value = false
  retryCount.value = 0
}

const setPreviewColumns = (firstItem) => {
  if (!firstItem) {
    previewColumns.value = []
    return
  }
  
  const columns = Object.keys(firstItem).map(key => ({
    prop: key,
    label: formatColumnName(key),
    width: getColumnWidth(key)
  }))
  
  previewColumns.value = columns
}

const formatColumnName = (key) => {
  const nameMap = {
    student_id: '学号',
    student_name: '姓名',
    class_name: '班级',
    course_name: '课程名称',
    course_code: '课程代码',
    score: '成绩',
    credit: '学分',
    semester: '学期',
    academic_year: '学年',
    exam_type: '考试类型',
    course_type: '课程类型'
  }
  
  return nameMap[key] || key
}

const getColumnWidth = (key) => {
  const widthMap = {
    student_id: 120,
    student_name: 100,
    class_name: 150,
    course_name: 150,
    course_code: 120,
    score: 80,
    credit: 80
  }
  
  return widthMap[key] || 100
}

const showPreviewDialog = () => {
  previewDialogVisible.value = true
}

const showErrorDetail = (error) => {
  currentErrorDetail.value = error
  errorDetailDialogVisible.value = true
}

const exportPreviewData = () => {
  if (!uploadResult.value?.preview || uploadResult.value.preview.length === 0) {
    ElMessage.warning('没有可导出的数据')
    return
  }
  
  try {
    const data = uploadResult.value.preview
    const headers = Object.keys(data[0])
    
    let csvContent = '\uFEFF'
    csvContent += headers.map(h => formatColumnName(h)).join(',') + '\n'
    
    data.forEach(row => {
      csvContent += headers.map(h => {
        const value = row[h] ?? ''
        return typeof value === 'string' && value.includes(',') 
          ? `"${value}"` 
          : value
      }).join(',') + '\n'
    })
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    
    link.setAttribute('href', url)
    link.setAttribute('download', `成绩数据_${new Date().toISOString().slice(0, 10)}.csv`)
    link.style.visibility = 'hidden'
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success('数据导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('数据导出失败')
  }
}

const handleFileChange = (file, fileList) => {
  console.log('文件列表变化:', fileList)
  clearPreview()
  clearResult()
  retryCount.value = 0
}

const handleSubmitSuccess = () => {
  console.log('提交成功')
}

const handleUploadError = (error) => {
  console.error('上传错误:', error)
}

const clearPreview = () => {
  previewData.value = []
  previewColumns.value = []
}

const clearResult = () => {
  uploadResult.value = null
  errorCurrentPage.value = 1
}
</script>

<style scoped>
.score-upload {
  padding: 20px;
}

.result-card {
  margin-top: 20px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-stats {
  margin-bottom: 20px;
}

.stat-item {
  text-align: center;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.stat-item.success {
  background-color: #f0f9eb;
}

.stat-item.error {
  background-color: #fef0f0;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.stat-item.success .stat-value {
  color: #67c23a;
}

.stat-item.error .stat-value {
  color: #f56c6c;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 5px;
}

.error-list {
  margin-top: 20px;
}

.pagination-container {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.suggestion-icon {
  margin-left: 8px;
  color: #e6a23c;
  cursor: pointer;
}

.preview-actions {
  margin-top: 16px;
}

.preview-dialog-content {
  padding: 0 20px;
}

.retry-dialog-content {
  text-align: center;
  padding: 20px;
}

.warning-icon {
  font-size: 48px;
  color: #e6a23c;
  margin-bottom: 15px;
}

.error-message {
  font-size: 16px;
  color: #606266;
  margin: 0;
  word-break: break-word;
}

.retry-info {
  margin-top: 16px;
}
</style>

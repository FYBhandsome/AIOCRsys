<template>
  <div class="file-upload">
    <el-card class="upload-card">
      <template #header>
        <div class="card-header">
          <h2>{{ title }}</h2>
          <p>{{ description }}</p>
        </div>
      </template>
      
      <el-form :model="form" label-width="120px">
        <slot name="form-fields" :form="form"></slot>
        
        <el-form-item label="上传文件">
          <el-upload
            ref="uploadRef"
            class="upload-demo"
            drag
            :auto-upload="false"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            :before-upload="beforeUpload"
            :file-list="fileList"
            :accept="acceptTypes"
            :limit="1"
            :on-exceed="handleExceed"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              将文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                {{ acceptTip }}
              </div>
            </template>
          </el-upload>
          
          <div v-if="uploadProgress > 0 && uploadProgress < 100" class="progress-wrapper">
            <el-progress 
              :percentage="uploadProgress" 
              :status="uploadStatus === 'error' ? 'exception' : undefined"
              :stroke-width="8"
            />
            <span class="progress-text">{{ uploadProgress }}%</span>
          </div>
          
          <div v-if="errorMessage" class="error-message">
            <el-alert
              :title="errorMessage"
              :type="errorType"
              :closable="true"
              @close="clearError"
              show-icon
            />
          </div>
          
          <div v-if="uploadStatus === 'success'" class="success-message">
            <el-alert
              title="文件上传成功"
              type="success"
              :closable="true"
              @close="resetStatus"
              show-icon
            />
          </div>
        </el-form-item>
        
        <el-form-item>
          <el-button 
            type="primary" 
            @click="submitUpload" 
            :disabled="fileList.length === 0 || uploadStatus === 'uploading'"
            :loading="uploadStatus === 'uploading'"
          >
            {{ uploadStatus === 'uploading' ? '上传中...' : submitButtonText }}
          </el-button>
          <el-button @click="resetForm" :disabled="uploadStatus === 'uploading'">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <slot name="ai-info"></slot>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  description: {
    type: String,
    default: ''
  },
  acceptTypes: {
    type: String,
    default: '.jpg,.jpeg,.png,.pdf'
  },
  acceptTip: {
    type: String,
    default: '支持 jpg、png、pdf 格式，单个文件不超过10MB'
  },
  submitButtonText: {
    type: String,
    default: '上传并识别'
  },
  initialForm: {
    type: Object,
    default: () => ({})
  },
  submitHandler: {
    type: Function,
    required: true
  },
  validator: {
    type: Function,
    default: () => true
  },
  maxSizeMB: {
    type: Number,
    default: 10
  },
  allowedMimeTypes: {
    type: Array,
    default: () => [
      'image/jpeg',
      'image/png',
      'image/jpg',
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-excel'
    ]
  }
})

const emit = defineEmits(['file-change', 'submit-success', 'upload-progress', 'upload-error'])

const form = reactive({ ...props.initialForm })
const fileList = ref([])
const uploadRef = ref(null)
const uploadProgress = ref(0)
const uploadStatus = ref('idle')
const errorMessage = ref('')
const errorType = ref('error')

const allowedExtensions = computed(() => {
  return props.acceptTypes.split(',').map(ext => ext.trim().toLowerCase())
})

const maxFileSize = computed(() => props.maxSizeMB * 1024 * 1024)

const getFileExtension = (filename) => {
  const lastDot = filename.lastIndexOf('.')
  return lastDot !== -1 ? filename.substring(lastDot).toLowerCase() : ''
}

const validateFileType = (file) => {
  const extension = getFileExtension(file.name)
  const isValidExtension = allowedExtensions.value.includes(extension)
  
  const isValidMimeType = props.allowedMimeTypes.length === 0 || 
    props.allowedMimeTypes.includes(file.type) ||
    file.type === ''
  
  return isValidExtension && isValidMimeType
}

const validateFileSize = (file) => {
  return file.size <= maxFileSize.value
}

const getMimeTypeError = (file) => {
  const extension = getFileExtension(file.name)
  if (!allowedExtensions.value.includes(extension)) {
    return `不支持的文件扩展名 "${extension}"，仅支持 ${props.acceptTypes} 格式`
  }
  if (!props.allowedMimeTypes.includes(file.type) && file.type !== '') {
    return `不支持的文件类型 "${file.type || '未知'}"，请上传正确的文件`
  }
  return null
}

const beforeUpload = (file) => {
  return false
}

const handleFileChange = (file, files) => {
  clearError()
  
  if (files.length > 0) {
    const currentFile = file.raw || file
    
    if (!validateFileType(currentFile)) {
      const error = getMimeTypeError(currentFile)
      setError(error || '文件类型不支持', 'error')
      fileList.value = []
      emit('file-change', null, [])
      return
    }
    
    if (!validateFileSize(currentFile)) {
      setError(`文件大小超过限制（最大 ${props.maxSizeMB}MB），当前文件大小：${(currentFile.size / 1024 / 1024).toFixed(2)}MB`, 'error')
      fileList.value = []
      emit('file-change', null, [])
      return
    }
    
    fileList.value = [file]
    uploadStatus.value = 'idle'
    uploadProgress.value = 0
    emit('file-change', file, fileList.value)
  } else {
    fileList.value = []
  }
}

const handleFileRemove = (file, files) => {
  fileList.value = files
  clearError()
  resetStatus()
  emit('file-change', null, files)
}

const handleExceed = (files) => {
  ElMessage.warning('最多只能上传一个文件，请先删除已上传的文件')
}

const setError = (message, type = 'error') => {
  errorMessage.value = message
  errorType.value = type
  uploadStatus.value = 'error'
}

const clearError = () => {
  errorMessage.value = ''
  errorType.value = 'error'
}

const resetStatus = () => {
  uploadStatus.value = 'idle'
  uploadProgress.value = 0
  clearError()
}

const submitUpload = async () => {
  if (!props.validator(form)) {
    return
  }
  
  if (fileList.value.length === 0) {
    ElMessage.warning('请上传文件')
    return
  }
  
  const currentFile = fileList.value[0].raw || fileList.value[0]
  
  if (!validateFileType(currentFile)) {
    setError('文件类型验证失败，请重新选择文件', 'error')
    return
  }
  
  if (!validateFileSize(currentFile)) {
    setError('文件大小验证失败，请重新选择文件', 'error')
    return
  }
  
  uploadStatus.value = 'uploading'
  uploadProgress.value = 0
  clearError()
  
  try {
    const onProgress = (progress) => {
      uploadProgress.value = progress
      emit('upload-progress', progress)
    }
    
    await props.submitHandler(form, currentFile, onProgress)
    
    uploadProgress.value = 100
    uploadStatus.value = 'success'
    ElMessage.success('上传成功！')
    emit('submit-success')
    
    setTimeout(() => {
      resetForm()
    }, 2000)
    
  } catch (error) {
    uploadStatus.value = 'error'
    uploadProgress.value = 0
    
    let errorMsg = '上传失败，请稍后重试'
    
    if (error.response) {
      const status = error.response.status
      const data = error.response.data
      
      switch (status) {
        case 400:
          errorMsg = data?.detail || data?.message || '请求参数错误，请检查文件格式'
          break
        case 401:
          errorMsg = '登录已过期，请重新登录'
          break
        case 403:
          errorMsg = '没有上传权限'
          break
        case 413:
          errorMsg = '文件大小超过服务器限制'
          break
        case 422:
          errorMsg = data?.detail || '文件内容格式不正确'
          break
        case 500:
          errorMsg = '服务器内部错误，请稍后重试'
          break
        case 502:
        case 503:
          errorMsg = '服务暂时不可用，请稍后重试'
          break
        default:
          errorMsg = data?.detail || data?.message || `上传失败 (${status})`
      }
    } else if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      errorMsg = '上传超时，请检查网络连接或尝试上传较小的文件'
    } else if (error.message?.includes('Network Error')) {
      errorMsg = '网络连接失败，请检查网络设置'
    } else if (error.message) {
      errorMsg = error.message
    }
    
    setError(errorMsg, 'error')
    emit('upload-error', error)
    console.error('上传失败:', error)
  }
}

const resetForm = () => {
  Object.keys(form).forEach(key => {
    form[key] = props.initialForm[key] || ''
  })
  fileList.value = []
  resetStatus()
}

defineExpose({
  resetForm,
  form,
  fileList,
  uploadStatus,
  uploadProgress,
  setError,
  clearError
})
</script>

<style scoped>
.file-upload {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.upload-card {
  margin-bottom: 30px;
}

.card-header h2 {
  margin: 0 0 10px 0;
  color: #333;
}

.card-header p {
  margin: 0;
  color: #666;
}

.progress-wrapper {
  margin-top: 15px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.progress-wrapper .el-progress {
  flex: 1;
}

.progress-text {
  font-size: 14px;
  color: #409eff;
  font-weight: 500;
  min-width: 45px;
  text-align: right;
}

.error-message {
  margin-top: 15px;
}

.success-message {
  margin-top: 15px;
}

.upload-demo {
  width: 100%;
}

:deep(.el-upload-dragger) {
  width: 100%;
}
</style>

<template>
  <div class="certificate-upload">
    <el-card class="upload-card">
      <template #header>
        <div class="card-header">
          <h2>证书上传与识别</h2>
          <p>上传证书图片，AI将自动识别证书信息</p>
        </div>
      </template>
      
      <el-upload
        ref="uploadRef"
        class="upload-area"
        drag
        :auto-upload="false"
        :on-change="handleFileChange"
        :before-upload="beforeUpload"
        :file-list="fileList"
        accept="image/*"
        :limit="1"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          将证书图片拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 JPG、PNG 格式，文件大小不超过 10MB
          </div>
        </template>
      </el-upload>
      
      <div class="upload-actions">
        <el-button 
          type="primary" 
          @click="submitUpload" 
          :disabled="!selectedFile || isProcessing"
          :loading="isProcessing"
        >
          {{ isProcessing ? '识别中...' : '开始识别' }}
        </el-button>
        <el-button @click="resetForm" :disabled="isProcessing">重置</el-button>
      </div>
    </el-card>
    
    <!-- 任务状态显示 -->
    <el-card v-if="taskId" class="status-card">
      <template #header>
        <div class="card-header">
          <h3>识别进度</h3>
        </div>
      </template>
      
      <div class="status-content">
        <el-progress 
          :percentage="Math.round(progress * 100)" 
          :status="progressStatus"
          :stroke-width="8"
        />
        <p class="status-text">{{ statusText }}</p>
        
        <div v-if="taskStatus === 'completed'" class="result-actions">
          <el-button type="success" @click="viewResult">查看识别结果</el-button>
        </div>
      </div>
    </el-card>
    
    <!-- 识别结果展示 -->
    <el-card v-if="showResult && recognitionResult" class="result-card">
      <template #header>
        <div class="card-header">
          <h3>识别结果</h3>
          <el-button type="text" @click="showResult = false">收起</el-button>
        </div>
      </template>
      
      <div class="result-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="文件名">
            {{ recognitionResult.filename || recognitionResult.file_name }}
          </el-descriptions-item>
          <el-descriptions-item label="文件ID">
            {{ recognitionResult.file_id }}
          </el-descriptions-item>
          <el-descriptions-item label="姓名" v-if="recognitionResult.certificate_info?.name">
            {{ recognitionResult.certificate_info.name }}
          </el-descriptions-item>
          <el-descriptions-item label="获奖名称" v-if="recognitionResult.certificate_info?.award_name">
            {{ recognitionResult.certificate_info.award_name }}
          </el-descriptions-item>
          <el-descriptions-item label="获奖等级" v-if="recognitionResult.certificate_info?.award_level">
            {{ recognitionResult.certificate_info.award_level }}
          </el-descriptions-item>
          <el-descriptions-item label="综测加分" v-if="recognitionResult.certificate_info?.rag_score">
            <el-tag type="success" size="large">
              +{{ recognitionResult.certificate_info.rag_score.score }} 分
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="加分规则" v-if="recognitionResult.certificate_info?.rag_score" :span="2">
            {{ recognitionResult.certificate_info.rag_score.rules }}
          </el-descriptions-item>
          <el-descriptions-item label="识别置信度" v-if="recognitionResult.certificate_info?.confidence">
            {{ (recognitionResult.certificate_info.confidence * 100).toFixed(1) }}%
          </el-descriptions-item>
        </el-descriptions>
        
        <div class="raw-text-section">
          <h4>原始识别文本：</h4>
          <el-input
            :model-value="recognitionResult?.certificate_info?.raw_text || ''"
            type="textarea"
            :rows="6"
            readonly
            placeholder="暂无识别文本"
          />
        </div>
        
        <div class="ocr-results-section" v-if="recognitionResult?.recognition_results?.length > 0">
          <h4>OCR识别详情：</h4>
          <el-table :data="recognitionResult.recognition_results" border style="width: 100%">
            <el-table-column prop="text" label="识别文本" min-width="200" />
            <el-table-column label="置信度" width="100" align="center">
              <template #default="scope">
                {{ (scope.row.score * 100).toFixed(1) }}%
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onUnmounted, computed } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { studentAPI, commonAPI } from '@/services/api'

// 响应式数据
const uploadRef = ref()
const fileList = ref([])
const selectedFile = ref(null)
const isProcessing = ref(false)
const taskId = ref('')
const taskStatus = ref('')
const progress = ref(0)
const recognitionResult = ref(null)
const showResult = ref(false)

// 轮询定时器
let pollingTimer = null

// 计算属性
const progressStatus = computed(() => {
  if (taskStatus.value === 'failed') return 'exception'
  if (taskStatus.value === 'completed') return 'success'
  return ''
})

const statusText = computed(() => {
  switch (taskStatus.value) {
    case 'pending':
      return '任务已创建，等待处理...'
    case 'processing':
      return `正在识别中... (${Math.round(progress.value * 100)}%)`
    case 'completed':
      return '识别完成！'
    case 'failed':
      return '识别失败，请重试'
    default:
      return '未知状态'
  }
})

// 文件选择处理
const handleFileChange = (file, files) => {
  fileList.value = files
  selectedFile.value = file.raw
}

// 上传前验证
const beforeUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB!')
    return false
  }
  return false // 阻止自动上传
}

// 提交上传
const submitUpload = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }

  try {
    isProcessing.value = true
    taskId.value = ''
    recognitionResult.value = null
    showResult.value = false

    // 调用学生证书上传API
    const response = await studentAPI.uploadCertificate(selectedFile.value, (progress) => {
      // 上传进度回调
      console.log('Upload progress:', progress)
    })
    
    // 直接返回识别结果，不需要轮询
    recognitionResult.value = response
    taskStatus.value = 'completed'
    progress.value = 1.0
    showResult.value = true
    ElMessage.success('证书上传并识别成功！')
  } catch (error) {
    console.error('上传失败:', error)
    ElMessage.error(`上传失败: ${error.message || '未知错误'}`)
    isProcessing.value = false
  }
}

// 开始轮询任务状态
const startPolling = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
  }
  
  pollingTimer = setInterval(async () => {
    try {
      const response = await commonAPI.get(`/upload/task/${taskId.value}/status`)
      
      taskStatus.value = response.status
      // 后端 progress 为 0.0~1.0，前端展示用 0~1 范围
      progress.value = typeof response.progress === 'number' ? response.progress : (response.progress || 0) / 100
      
      if (response.status === 'completed') {
        clearInterval(pollingTimer)
        isProcessing.value = false
        ElMessage.success('识别完成！')
        
        // 获取识别结果
        await fetchResult()
      } else if (response.status === 'failed') {
        clearInterval(pollingTimer)
        isProcessing.value = false
        ElMessage.error(`识别失败: ${response.error || '未知错误'}`)
      }
    } catch (error) {
      console.error('查询任务状态失败:', error)
      clearInterval(pollingTimer)
      isProcessing.value = false
      ElMessage.error('查询任务状态失败')
    }
  }, 1000) // 每秒轮询一次
}

// 获取识别结果
const fetchResult = async () => {
  try {
    const response = await commonAPI.get(`/upload/task/${taskId.value}/result`)
    recognitionResult.value = response
    showResult.value = true
  } catch (error) {
    console.error('获取识别结果失败:', error)
    ElMessage.error('获取识别结果失败')
  }
}

// 查看结果
const viewResult = () => {
  showResult.value = true
}

// 重置表单
const resetForm = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
  }
  
  fileList.value = []
  selectedFile.value = null
  isProcessing.value = false
  taskId.value = ''
  taskStatus.value = ''
  progress.value = 0
  recognitionResult.value = null
  showResult.value = false
  
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

// 组件卸载时清理定时器
onUnmounted(() => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
  }
})
</script>

<style scoped>
.certificate-upload {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.upload-card,
.status-card,
.result-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2,
.card-header h3 {
  margin: 0;
  color: #333;
}

.card-header p {
  margin: 5px 0 0 0;
  color: #666;
  font-size: 14px;
}

.upload-area {
  margin: 20px 0;
}

.upload-actions {
  text-align: center;
  margin-top: 20px;
}

.status-content {
  padding: 20px 0;
}

.status-text {
  margin-top: 15px;
  text-align: center;
  color: #666;
}

.result-actions {
  text-align: center;
  margin-top: 15px;
}

.result-content {
  padding: 10px 0;
}

.raw-text-section {
  margin-top: 20px;
}

.raw-text-section h4,
.ocr-results-section h4 {
  margin: 0 0 10px 0;
  color: #333;
}

.ocr-results-section {
  margin-top: 20px;
}
</style>

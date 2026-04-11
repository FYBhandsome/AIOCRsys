<template>
  <div class="material-upload">
    <CertificateUpload />
    
    <FileUpload
      title="其他材料上传"
      description="支持社会实践证明、科研成果、志愿服务证明等各类材料"
      accept-types=".jpg,.jpeg,.png,.pdf"
      accept-tip="支持 jpg、png、pdf 格式，单个文件不超过10MB"
      submit-button-text="上传并AI识别"
      :initial-form="initialForm"
      :submit-handler="submitHandler"
      :validator="validateForm"
      @file-change="handleFileChange"
      @submit-success="handleSubmitSuccess"
    >
      <template #form-fields="{ form }">
        <el-form-item label="材料类型">
          <el-select v-model="form.type" placeholder="请选择材料类型">
            <el-option label="社会实践证明" value="practice"></el-option>
            <el-option label="科研成果" value="research"></el-option>
            <el-option label="志愿服务证明" value="volunteer"></el-option>
            <el-option label="其他材料" value="other"></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="材料描述">
          <el-input 
            v-model="form.description" 
            type="textarea" 
            placeholder="请输入材料描述，如：2023年暑期社会实践优秀个人"
          />
        </el-form-item>
      </template>
      
      <template #ai-info>
        <AIInfoCard
          title="AI 智能识别说明"
          :example="{
            input: '输入：2023年全国大学生英语竞赛省级二等奖',
            output: '输出：属于学科竞赛类别，应加 8 分'
          }"
        />
      </template>
    </FileUpload>
    
    <el-card class="upload-history" v-if="uploadHistory.length > 0">
      <template #header>
        <div class="card-header">
          <span>上传历史</span>
          <el-button type="text" @click="fetchUploadHistory">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>
      
      <el-table :data="uploadHistory" stripe v-loading="historyLoading">
        <el-table-column prop="file_name" label="文件名" min-width="200" />
        <el-table-column prop="type" label="材料类型" width="120">
          <template #default="{ row }">
            {{ getTypeText(row.type) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="上传时间" width="180" />
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="viewDetail(row)">
              查看
            </el-button>
            <el-button type="danger" size="small" @click="deleteMaterial(row.id, row.file_name)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 材料详情/预览对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      :title="`材料详情 - ${detailData?.filename || ''}`"
      width="70%"
      :close-on-click-modal="true"
      destroy-on-close
    >
      <div v-if="detailLoading" style="text-align: center; padding: 40px;">
        <el-icon class="is-loading" :size="40"><Loading /></el-icon>
        <p style="margin-top: 10px;">加载中...</p>
      </div>
      
      <div v-else-if="detailError" style="text-align: center; padding: 40px; color: #f56c6c;">
        <el-icon :size="48"><WarningFilled /></el-icon>
        <p style="margin-top: 10px;">{{ detailError }}</p>
      </div>
      
      <div v-else-if="detailData" class="material-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="文件名">{{ detailData.filename }}</el-descriptions-item>
          <el-descriptions-item label="文件类型">
            {{ getTypeText(detailData.file_type) }}
          </el-descriptions-item>
          <el-descriptions-item label="文件大小">
            {{ formatFileSize(detailData.file_size) }}
          </el-descriptions-item>
          <el-descriptions-item label="上传时间">
            {{ detailData.created_at || '-' }}
          </el-descriptions-item>
        </el-descriptions>
        
        <!-- 图片预览区域 -->
        <div class="preview-section" v-if="detailData.file_exists">
          <h4>📷 证书图片预览</h4>
          <div class="image-preview-container">
            <img
              :src="previewImageUrl"
              :alt="detailData.filename"
              class="preview-image"
              @load="onImageLoad"
              @error="onImageError"
            />
          </div>
        </div>
        
        <div v-else class="preview-error">
          <el-result
            icon="warning"
            title="文件不可预览"
            sub-title="原始文件可能已被删除或损坏"
          />
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
        <el-button 
          v-if="detailData?.file_exists" 
          type="primary" 
          @click="downloadMaterial"
        >
          <el-icon><Download /></el-icon>
          下载文件
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Loading, WarningFilled, Download } from '@element-plus/icons-vue'
import CertificateUpload from '@/components/CertificateUpload.vue'
import FileUpload from '@/components/FileUpload.vue'
import AIInfoCard from '@/components/AIInfoCard.vue'
import { studentAPI } from '@/services/api'

const initialForm = {
  type: '',
  description: ''
}

const uploadHistory = ref([])
const historyLoading = ref(false)

const showDetailDialog = ref(false)
const detailData = ref(null)
const detailLoading = ref(false)
const detailError = ref(null)

const validateForm = (form) => {
  if (!form.type) {
    ElMessage.warning('请选择材料类型')
    return false
  }
  return true
}

const submitHandler = async (form, file) => {
  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('material_type', form.type)
    formData.append('description', form.description)
    
    const response = await studentAPI.uploadMaterial(formData)
    
    if (response && response.success) {
      ElMessage.success('材料上传成功，AI正在识别中...')
      
      fetchUploadHistory()
    } else {
      throw new Error(response?.message || '上传失败')
    }
  } catch (error) {
    console.error('材料上传失败:', error)
    ElMessage.error(error.message || '材料上传失败')
    throw error
  }
}

const handleFileChange = (file, fileList) => {
  console.log('文件列表变化:', fileList)
}

const handleSubmitSuccess = () => {
  console.log('提交成功')
}

const getTypeText = (type) => {
  const types = {
    practice: '社会实践证明',
    research: '科研成果',
    volunteer: '志愿服务证明',
    other: '其他材料'
  }
  return types[type] || type
}

const getStatusType = (status) => {
  const types = {
    pending: 'warning',
    processing: 'info',
    completed: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return texts[status] || status
}

const fetchUploadHistory = async () => {
  historyLoading.value = true
  try {
    const response = await studentAPI.getMaterials()
    
    if (response && response.materials) {
      uploadHistory.value = response.materials.map(item => ({
        id: item.id,
        file_name: item.file_name || item.fileName,
        type: item.material_type || item.type,
        status: item.status || 'completed',
        create_time: item.create_time || item.createTime
      }))
    }
  } catch (error) {
    console.error('获取上传历史失败:', error)
  } finally {
    historyLoading.value = false
  }
}

const viewDetail = async (row) => {
  showDetailDialog.value = true
  detailData.value = null
  detailError.value = null
  detailLoading.value = true
  
  try {
    const result = await studentAPI.getMaterialDetail(row.id)
    detailData.value = result
  } catch (error) {
    console.error('获取材料详情失败:', error)
    detailError.value = error.response?.data?.detail || '获取材料详情失败'
  } finally {
    detailLoading.value = false
  }
}

const previewImageUrl = computed(() => {
  if (!detailData.value?.id) return ''
  return studentAPI.getMaterialPreviewUrl(detailData.value.id)
})

const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const onImageLoad = () => {
  console.log('图片加载成功')
}

const onImageError = (e) => {
  console.error('图片加载失败:', e)
  detailError.value = '图片加载失败，文件可能已损坏或格式不支持'
}

const downloadMaterial = () => {
  if (!previewImageUrl.value) return
  const link = document.createElement('a')
  link.href = previewImageUrl.value
  link.download = detailData.value?.filename || 'download'
  link.target = '_blank'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const deleteMaterial = async (materialId, fileName) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除材料 "${fileName}" 吗？删除后将无法恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )
    
    const result = await studentAPI.deleteMaterial(materialId)
    
    if (result && result.success) {
      ElMessage.success('删除成功')
      await fetchUploadHistory()
    } else {
      ElMessage.error(result?.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除材料失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除失败，请稍后重试')
    }
  }
}

onMounted(() => {
  fetchUploadHistory()
})
</script>

<style scoped>
.material-upload {
  padding: 20px;
}

.upload-history {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.material-detail {
  padding: 10px 0;
}

.preview-section {
  margin-top: 24px;
}

.preview-section h4 {
  margin-bottom: 16px;
  color: #303133;
  font-size: 16px;
}

.image-preview-container {
  text-align: center;
  background: #f5f7fa;
  border-radius: 8px;
  padding: 20px;
  max-height: 70vh;
  overflow: auto;
}

.preview-image {
  max-width: 100%;
  max-height: 60vh;
  object-fit: contain;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.preview-error {
  margin-top: 24px;
}
</style>

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
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="viewDetail(row)">
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
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

const viewDetail = (row) => {
  ElMessage.info(`查看材料详情: ${row.file_name}`)
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
</style>

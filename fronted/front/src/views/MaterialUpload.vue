<template>
  <div class="material-upload">
    <!-- 证书上传组件 -->
    <CertificateUpload />
    
    <!-- 使用通用文件上传组件 -->
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
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { ElMessage } from 'element-plus'
import CertificateUpload from '@/components/CertificateUpload.vue'
import FileUpload from '@/components/FileUpload.vue'
import AIInfoCard from '@/components/AIInfoCard.vue'

// 初始表单数据
const initialForm = {
  type: '',
  description: ''
}

// 表单验证
const validateForm = (form) => {
  if (!form.type) {
    ElMessage.warning('请选择材料类型')
    return false
  }
  return true
}

// 提交处理函数
const submitHandler = async (form, file) => {
  // 模拟上传过程
  ElMessage.success('材料上传成功，AI正在识别中...')
  return Promise.resolve()
}

// 文件变化处理
const handleFileChange = (file, fileList) => {
  console.log('文件列表变化:', fileList)
}

// 提交成功处理
const handleSubmitSuccess = () => {
  console.log('提交成功')
}
</script>

<style scoped>
.material-upload {
  padding: 20px;
}
</style>
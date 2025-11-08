<template>
  <div class="score-upload">
    <!-- 使用通用文件上传组件 -->
    <FileUpload
      title="上传成绩单"
      description="支持 Excel 文件或成绩单截图"
      accept-types=".xlsx,.xls,.jpg,.jpeg,.png"
      accept-tip="支持 .xlsx、.xls、.jpg、.jpeg 或 .png 格式的文件"
      submit-button-text="上传并识别"
      :initial-form="initialForm"
      :submit-handler="submitHandler"
      :validator="validateForm"
      @file-change="handleFileChange"
      @submit-success="handleSubmitSuccess"
    >
      <template #form-fields="{ form }">
        <el-form-item label="学期">
          <el-select v-model="form.semester" placeholder="请选择学期">
            <el-option label="2023-2024学年第一学期" value="2023-1"></el-option>
            <el-option label="2023-2024学年第二学期" value="2023-2"></el-option>
            <el-option label="2024-2025学年第一学期" value="2024-1"></el-option>
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
  </div>
</template>

<script setup>
import { reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import FileUpload from '@/components/FileUpload.vue'
import AIInfoCard from '@/components/AIInfoCard.vue'

// 初始表单数据
const initialForm = {
  semester: '',
  fileType: 'excel'
}

// 动态步骤说明
const dynamicSteps = computed(() => {
  return [
    initialForm.fileType === 'excel' 
      ? '直接解析 Excel 文件中的成绩数据' 
      : '使用 OCR 技术识别成绩单截图中的文字信息',
    '通过大模型理解课程名称和成绩含义',
    '自动匹配综测规则中的学业成绩计算方式'
  ]
})

// 表单验证
const validateForm = (form) => {
  if (!form.semester) {
    ElMessage.warning('请选择学期')
    return false
  }
  return true
}

// 提交处理函数
const submitHandler = async (form, file) => {
  // 模拟上传过程
  ElMessage.success('成绩单上传成功，AI正在识别中...')
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
.score-upload {
  padding: 20px;
}
</style>
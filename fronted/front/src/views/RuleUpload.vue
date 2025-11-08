<template>
  <div class="rule-upload">
    <!-- 使用通用文件上传组件 -->
    <FileUpload
      title="综测规则上传"
      description="上传综测评分规则文档，支持PDF或Word格式"
      accept-types=".pdf,.doc,.docx"
      accept-tip="支持 PDF、Word 格式，单个文件不超过10MB"
      submit-button-text="上传并解析"
      :initial-form="initialForm"
      :submit-handler="submitHandler"
      :validator="validateForm"
      @file-change="handleFileChange"
      @submit-success="handleSubmitSuccess"
    >
      <template #form-fields="{ form }">
        <el-form-item label="规则名称">
          <el-input 
            v-model="form.ruleName" 
            placeholder="请输入规则名称，如：2023-2024学年综测评分规则"
          />
        </el-form-item>
        
        <el-form-item label="适用学年">
          <el-select v-model="form.academicYear" placeholder="请选择适用学年">
            <el-option label="2023-2024学年" value="2023-2024"></el-option>
            <el-option label="2024-2025学年" value="2024-2025"></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="规则描述">
          <el-input 
            v-model="form.description" 
            type="textarea" 
            placeholder="请输入规则描述，如：本规则适用于2023-2024学年本科生综合素质测评"
          />
        </el-form-item>
      </template>
      
      <template #ai-info>
        <AIInfoCard
          title="AI 规则解析说明"
          :steps="[
            '使用文档解析技术提取规则内容',
            '通过大模型理解规则结构和评分标准',
            '自动识别各类加分项和扣分项',
            '生成结构化规则数据用于综测计算'
          ]"
          :tech-tags="[
            { text: '文档解析', type: 'primary' },
            { text: '大模型理解', type: 'success' },
            { text: '规则提取', type: 'warning' }
          ]"
        />
      </template>
    </FileUpload>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { ElMessage } from 'element-plus'
import FileUpload from '@/components/FileUpload.vue'
import AIInfoCard from '@/components/AIInfoCard.vue'

// 初始表单数据
const initialForm = {
  ruleName: '',
  academicYear: '',
  description: ''
}

// 表单验证
const validateForm = (form) => {
  if (!form.ruleName) {
    ElMessage.warning('请输入规则名称')
    return false
  }
  if (!form.academicYear) {
    ElMessage.warning('请选择适用学年')
    return false
  }
  return true
}

// 提交处理函数
const submitHandler = async (form, file) => {
  // 模拟上传过程
  ElMessage.success('规则文档上传成功，AI正在解析中...')
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
.rule-upload {
  padding: 20px;
}
</style>
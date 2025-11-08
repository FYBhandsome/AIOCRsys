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
        <!-- 动态表单项插槽 -->
        <slot name="form-fields" :form="form"></slot>
        
        <el-form-item label="上传文件">
          <el-upload
            class="upload-demo"
            drag
            :auto-upload="false"
            :on-change="handleFileChange"
            :file-list="fileList"
            :accept="acceptTypes"
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
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="submitUpload" :disabled="fileList.length === 0">
            {{ submitButtonText }}
          </el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- AI说明卡片插槽 -->
    <slot name="ai-info"></slot>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

// 定义props
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
  }
})

// 定义事件
const emit = defineEmits(['file-change', 'submit-success'])

// 响应式数据
const form = reactive({ ...props.initialForm })
const fileList = ref([])

// 文件变化处理
const handleFileChange = (file, files) => {
  fileList.value = files
  emit('file-change', file, files)
}

// 提交上传
const submitUpload = () => {
  // 验证表单
  if (!props.validator(form)) {
    return
  }
  
  if (fileList.value.length === 0) {
    ElMessage.warning('请上传文件')
    return
  }
  
  // 调用提交处理函数
  props.submitHandler(form, fileList.value[0].raw)
    .then(() => {
      emit('submit-success')
      resetForm()
    })
    .catch(error => {
      console.error('上传失败:', error)
    })
}

// 重置表单
const resetForm = () => {
  Object.keys(form).forEach(key => {
    form[key] = props.initialForm[key] || ''
  })
  fileList.value = []
}

// 暴露方法给父组件
defineExpose({
  resetForm,
  form,
  fileList
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
</style>
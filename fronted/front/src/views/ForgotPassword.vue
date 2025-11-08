<template>
  <div class="forgot-password-container">
    <div class="forgot-password-wrapper">
      <h1 class="title">忘记密码</h1>
      <p class="description">请输入您的注册邮箱，我们将向您发送密码重置链接。</p>
      
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="0"
        class="forgot-password-form"
      >
        <el-form-item prop="email">
          <el-input
            v-model="form.email"
            placeholder="请输入您的邮箱"
            prefix-icon="Message"
            size="large"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            class="submit-button"
            :loading="loading"
            @click="handleSubmit"
          >
            发送重置链接
          </el-button>
        </el-form-item>
        
        <el-form-item>
          <div class="back-to-login">
            <router-link to="/login">返回登录</router-link>
          </div>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'

// 表单引用
const formRef = ref(null)

// 加载状态
const loading = ref(false)

// 表单数据
const form = reactive({
  email: ''
})

// 表单验证规则
const rules = {
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: ['blur', 'change'] }
  ]
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    // 验证表单
    await formRef.value.validate()
    
    loading.value = true
    
    // 模拟API调用
    setTimeout(() => {
      loading.value = false
      ElMessage.success('密码重置链接已发送到您的邮箱，请查收')
      
      // 重置表单
      form.email = ''
      formRef.value.resetFields()
    }, 1500)
  } catch (error) {
    console.error('表单验证失败:', error)
  }
}
</script>

<style scoped>
.forgot-password-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #1976d2, #42a5f5, #64b5f6);
  padding: 20px;
}

.forgot-password-wrapper {
  width: 100%;
  max-width: 400px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 10px;
  padding: 40px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
}

.title {
  font-size: 28px;
  font-weight: bold;
  color: #333;
  text-align: center;
  margin-bottom: 10px;
}

.description {
  color: #666;
  text-align: center;
  margin-bottom: 30px;
  line-height: 1.5;
}

.forgot-password-form {
  width: 100%;
}

.submit-button {
  width: 100%;
  height: 50px;
  font-size: 16px;
  border-radius: 5px;
}

.back-to-login {
  text-align: center;
  margin-top: 20px;
}

.back-to-login a {
  color: #1976d2;
  text-decoration: none;
}

.back-to-login a:hover {
  text-decoration: underline;
}

@media (max-width: 768px) {
  .forgot-password-wrapper {
    padding: 30px 20px;
  }
  
  .title {
    font-size: 24px;
  }
}
</style>
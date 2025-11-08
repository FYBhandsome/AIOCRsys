<template>
  <div class="forgot-password-container">
    <div class="forgot-password-wrapper">
      <h1 class="title">🔐 忘记密码</h1>
      <p class="description">通过验证码重置您的密码</p>
      
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="0"
        class="forgot-password-form"
      >
        <!-- 邮箱输入 -->
        <el-form-item prop="email">
          <el-input
            v-model="form.email"
            placeholder="请输入您的注册邮箱"
            prefix-icon="Message"
            size="large"
            :disabled="codeSent"
          />
        </el-form-item>
        
        <!-- 验证码输入 -->
        <el-form-item prop="verificationCode" v-if="codeSent">
          <div class="code-input-wrapper">
            <el-input
              v-model="form.verificationCode"
              placeholder="请输入6位验证码"
              prefix-icon="Key"
              size="large"
              maxlength="6"
            />
            <el-button
              class="resend-button"
              :disabled="countdown > 0"
              @click="handleSendCode"
              size="large"
            >
              {{ countdown > 0 ? `${countdown}秒后重发` : '重新发送' }}
            </el-button>
          </div>
        </el-form-item>
        
        <!-- 新密码输入 -->
        <el-form-item prop="newPassword" v-if="codeSent">
          <el-input
            v-model="form.newPassword"
            type="password"
            placeholder="请输入新密码（至少6位）"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        
        <!-- 确认密码 -->
        <el-form-item prop="confirmPassword" v-if="codeSent">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="请再次输入新密码"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        
        <!-- 按钮 -->
        <el-form-item>
          <el-button
            v-if="!codeSent"
            type="primary"
            class="submit-button"
            :loading="loading"
            @click="handleSendCode"
          >
            发送验证码
          </el-button>
          <el-button
            v-else
            type="primary"
            class="submit-button"
            :loading="loading"
            @click="handleResetPassword"
          >
            重置密码
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
import { ref, reactive, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import api from '../services/api'

const router = useRouter()

// 表单引用
const formRef = ref(null)

// 加载状态
const loading = ref(false)

// 验证码发送状态
const codeSent = ref(false)

// 倒计时
const countdown = ref(0)
let countdownTimer = null

// 表单数据
const form = reactive({
  email: '',
  verificationCode: '',
  newPassword: '',
  confirmPassword: ''
})

// 自定义验证规则
const validateConfirmPassword = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== form.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

// 表单验证规则
const rules = {
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: ['blur', 'change'] }
  ],
  verificationCode: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { len: 6, message: '验证码必须为6位', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少为6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

// 开始倒计时
const startCountdown = () => {
  countdown.value = 120 // 2分钟
  countdownTimer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(countdownTimer)
      countdownTimer = null
    }
  }, 1000)
}

// 发送验证码
const handleSendCode = async () => {
  if (!formRef.value) return
  
  try {
    // 只验证邮箱字段
    await formRef.value.validateField('email')
    
    loading.value = true
    
    const response = await api.post('/auth/password/reset-request', {
      email: form.email
    })
    
    ElMessage.success('验证码已发送到您的邮箱，请查收（有效期2分钟）')
    codeSent.value = true
    startCountdown()
    
  } catch (error) {
    console.error('发送验证码失败:', error)
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('发送验证码失败，请稍后重试')
    }
  } finally {
    loading.value = false
  }
}

// 重置密码
const handleResetPassword = async () => {
  if (!formRef.value) return
  
  try {
    // 验证所有字段
    await formRef.value.validate()
    
    loading.value = true
    
    await api.post('/auth/password/reset-confirm', {
      email: form.email,
      verification_code: form.verificationCode,
      new_password: form.newPassword
    })
    
    ElMessage.success('密码重置成功！正在跳转到登录页...')
    
    // 延迟跳转到登录页
    setTimeout(() => {
      router.push('/login')
    }, 1500)
    
  } catch (error) {
    console.error('重置密码失败:', error)
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('重置密码失败，请稍后重试')
    }
  } finally {
    loading.value = false
  }
}

// 清理定时器
onUnmounted(() => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
  }
})
</script>

<style scoped>
.forgot-password-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.forgot-password-wrapper {
  width: 100%;
  max-width: 480px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 15px;
  padding: 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
}

.title {
  font-size: 32px;
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
  font-size: 14px;
}

.forgot-password-form {
  width: 100%;
}

.code-input-wrapper {
  display: flex;
  gap: 10px;
  width: 100%;
}

.code-input-wrapper .el-input {
  flex: 1;
}

.resend-button {
  flex-shrink: 0;
  min-width: 110px;
  height: 40px;
}

.submit-button {
  width: 100%;
  height: 48px;
  font-size: 16px;
  border-radius: 8px;
  font-weight: 500;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

.submit-button:hover {
  background: linear-gradient(135deg, #5568d3 0%, #6a3f8f 100%);
}

.back-to-login {
  text-align: center;
  margin-top: 20px;
}

.back-to-login a {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.3s;
}

.back-to-login a:hover {
  color: #764ba2;
  text-decoration: underline;
}

:deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 2px 12px rgba(102, 126, 234, 0.3);
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}

:deep(.el-form-item) {
  margin-bottom: 20px;
}

@media (max-width: 768px) {
  .forgot-password-wrapper {
    padding: 30px 20px;
    max-width: 100%;
  }
  
  .title {
    font-size: 26px;
  }
  
  .code-input-wrapper {
    flex-direction: column;
  }
  
  .resend-button {
    width: 100%;
    min-width: auto;
  }
}
</style>
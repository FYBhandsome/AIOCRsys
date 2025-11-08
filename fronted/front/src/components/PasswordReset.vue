<template>
  <div class="password-reset-container">
    <div class="reset-card">
      <!-- 步骤1: 请求重置 -->
      <div v-if="step === 1" class="card-content">
        <div class="card-header">
          <h2>🔒 重置密码</h2>
          <p>输入您的注册邮箱，我们将发送重置链接</p>
        </div>

        <el-form
          ref="requestFormRef"
          :model="requestForm"
          :rules="requestRules"
          class="reset-form"
        >
          <el-form-item prop="email">
            <el-input
              v-model="requestForm.email"
              placeholder="请输入注册邮箱"
              :prefix-icon="Message"
              type="email"
              size="large"
            />
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              :loading="loading"
              @click="handleRequestReset"
              style="width: 100%"
              size="large"
            >
              {{ loading ? '发送中...' : '发送重置邮件' }}
            </el-button>
          </el-form-item>

          <div class="back-link">
            <a @click="$router.push('/login')">返回登录</a>
          </div>
        </el-form>
      </div>

      <!-- 步骤2: 确认重置 -->
      <div v-else-if="step === 2" class="card-content">
        <div class="card-header">
          <h2>📧 邮件已发送</h2>
          <p>请查收您的邮箱，点击邮件中的链接重置密码</p>
        </div>

        <div class="info-box">
          <el-icon :size="48" color="#67c23a">
            <CircleCheck />
          </el-icon>
          <p>重置邮件已发送至：<strong>{{ requestForm.email }}</strong></p>
          <p class="tip">如果未收到邮件，请检查垃圾邮件文件夹</p>
          <el-button @click="step = 1" style="margin-top: 20px">
            重新发送
          </el-button>
        </div>
      </div>

      <!-- 步骤3: 设置新密码 -->
      <div v-else-if="step === 3" class="card-content">
        <div class="card-header">
          <h2>🔐 设置新密码</h2>
          <p>请输入您的新密码</p>
        </div>

        <el-form
          ref="confirmFormRef"
          :model="confirmForm"
          :rules="confirmRules"
          class="reset-form"
        >
          <el-form-item prop="newPassword">
            <el-input
              v-model="confirmForm.newPassword"
              type="password"
              placeholder="请输入新密码（至少6个字符）"
              :prefix-icon="Lock"
              show-password
              size="large"
            />
          </el-form-item>

          <el-form-item prop="confirmPassword">
            <el-input
              v-model="confirmForm.confirmPassword"
              type="password"
              placeholder="请再次输入新密码"
              :prefix-icon="Lock"
              show-password
              size="large"
            />
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              :loading="loading"
              @click="handleConfirmReset"
              style="width: 100%"
              size="large"
            >
              {{ loading ? '重置中...' : '确认重置' }}
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Message, Lock, CircleCheck } from '@element-plus/icons-vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../services/api'

const router = useRouter()
const route = useRoute()
const requestFormRef = ref(null)
const confirmFormRef = ref(null)
const loading = ref(false)
const step = ref(1)

const requestForm = reactive({
  email: ''
})

const confirmForm = reactive({
  newPassword: '',
  confirmPassword: '',
  token: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== confirmForm.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const requestRules = {
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ]
}

const confirmRules = {
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少为 6 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

// 处理请求重置
const handleRequestReset = async () => {
  if (!requestFormRef.value) return

  await requestFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await api.post('/auth/password/reset-request', {
          email: requestForm.email
        })

        ElMessage.success('重置邮件已发送，请查收邮箱')
        step.value = 2
      } catch (error) {
        console.error('请求重置失败:', error)
        const errorMsg = error.response?.data?.detail || '请求失败，请稍后重试'
        ElMessage.error(errorMsg)
      } finally {
        loading.value = false
      }
    }
  })
}

// 处理确认重置
const handleConfirmReset = async () => {
  if (!confirmFormRef.value) return

  await confirmFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await api.post('/auth/password/reset-confirm', {
          token: confirmForm.token,
          new_password: confirmForm.newPassword
        })

        ElMessage.success('密码重置成功！')
        
        // 延迟跳转到登录页
        setTimeout(() => {
          router.push('/login')
        }, 1500)
      } catch (error) {
        console.error('重置密码失败:', error)
        const errorMsg = error.response?.data?.detail || '重置失败，请重新请求重置链接'
        ElMessage.error(errorMsg)
      } finally {
        loading.value = false
      }
    }
  })
}

// 组件挂载时检查URL中的token
onMounted(() => {
  const token = route.query.token
  if (token) {
    confirmForm.token = token
    step.value = 3
  }
})
</script>

<style scoped>
.password-reset-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.reset-card {
  width: 100%;
  max-width: 450px;
  background: white;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.card-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 40px 30px;
  text-align: center;
}

.card-header h2 {
  margin: 0 0 10px 0;
  font-size: 28px;
  font-weight: 600;
}

.card-header p {
  margin: 0;
  opacity: 0.9;
  font-size: 14px;
}

.card-content {
  /* padding already in forms */
}

.reset-form {
  padding: 30px;
}

.info-box {
  padding: 40px 30px;
  text-align: center;
}

.info-box p {
  margin: 15px 0;
  color: #666;
  font-size: 14px;
}

.info-box strong {
  color: #333;
}

.info-box .tip {
  color: #999;
  font-size: 12px;
}

.back-link {
  text-align: center;
  margin-top: 20px;
}

.back-link a {
  color: #667eea;
  cursor: pointer;
  text-decoration: none;
  font-weight: 500;
  font-size: 14px;
}

.back-link a:hover {
  text-decoration: underline;
}

:deep(.el-input__wrapper) {
  border-radius: 8px;
}

:deep(.el-button) {
  border-radius: 8px;
  height: 45px;
  font-size: 16px;
  font-weight: 500;
}
</style>


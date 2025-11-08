<template>
  <div class="not-found-container">
    <div class="not-found-content">
      <h1 class="error-code">404</h1>
      <h2 class="error-title">页面未找到</h2>
      <p class="error-message">抱歉，您访问的页面不存在</p>
      <div class="actions">
        <el-button type="primary" @click="goHome">返回首页</el-button>
        <el-button @click="goBack">返回上一页</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store'

const router = useRouter()
const userStore = useUserStore()

const goHome = () => {
  if (userStore.isAuthenticated) {
    const role = userStore.userInfo.role
    const roleRoutes = {
      student: '/student/dashboard',
      teacher: '/teacher/dashboard',
      admin: '/admin/dashboard'
    }
    router.push(roleRoutes[role] || '/student/dashboard')
  } else {
    router.push('/login')
  }
}

const goBack = () => {
  router.go(-1)
}
</script>

<style scoped>
.not-found-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.not-found-content {
  text-align: center;
  color: white;
  padding: 40px;
}

.error-code {
  font-size: 120px;
  font-weight: 700;
  margin: 0;
  text-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  line-height: 1;
}

.error-title {
  font-size: 36px;
  font-weight: 600;
  margin: 20px 0 10px;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.error-message {
  font-size: 18px;
  margin: 20px 0 40px;
  opacity: 0.9;
}

.actions {
  display: flex;
  gap: 20px;
  justify-content: center;
}

@media (max-width: 768px) {
  .error-code {
    font-size: 80px;
  }
  
  .error-title {
    font-size: 28px;
  }
  
  .error-message {
    font-size: 16px;
  }
  
  .actions {
    flex-direction: column;
  }
}
</style>


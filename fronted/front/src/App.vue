<script setup>
import { onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import AIAssistant from './components/AIAssistant.vue'
import RoleSwitcher from './components/RoleSwitcher.vue'
import { useUserStore } from './store'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 判断是否为登录相关页面
const isLoginPage = computed(() => {
  const publicPages = ['/login', '/register', '/reset-password', '/forgot-password']
  return publicPages.includes(route.path)
})

// 页面加载时检查登录状态
onMounted(() => {
  // 初始化时检查认证状态（只检查，不自动跳转，让路由守卫处理）
  userStore.checkAuth()
})

// 退出登录
const handleLogout = () => {
  userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<template>
  <!-- 根据当前路由决定显示布局 -->
  <!-- 登录相关页面：显示登录布局 -->
  <div v-if="isLoginPage" class="login-layout">
    <router-view />
  </div>
  
  <!-- 已登录状态：显示主应用布局 -->
  <div v-else-if="userStore.isAuthenticated" class="app-root">
    <el-container class="layout-container">
      <el-header class="header">
        <div class="logo">
          <h2>🎓 综测计算助手</h2>
        </div>
        
        <div class="user-info">
          <!-- 身份切换器（仅开发模式） -->
          <RoleSwitcher />
          
          <span class="welcome-text">欢迎，{{ userStore.userInfo.name || '用户' }}</span>
          <el-button type="text" @click="handleLogout" class="logout-btn">
            退出登录
          </el-button>
        </div>
      </el-header>
      
      <el-container class="content-container">
        <el-main class="main-content">
          <router-view />
        </el-main>
      </el-container>
    </el-container>

    <!-- AI助手悬浮窗 -->
    <AIAssistant />
  </div>
  
  <!-- 未登录且不在登录页面：显示空白（路由守卫会处理跳转） -->
  <div v-else class="login-layout">
    <router-view />
  </div>
</template>

<style scoped>
.app-root {
  min-height: 100vh;
}

.layout-container {
  min-height: 100vh;
}

.layout-container > .el-container {
  flex: 1;
}

/* 头部样式 */
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0 30px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  height: 65px;
  position: relative;
}

.header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.1) 0%,
    rgba(255, 255, 255, 0) 100%
  );
  pointer-events: none;
}

.logo {
  position: relative;
  z-index: 1;
}

.logo h2 {
  margin: 0;
  font-weight: 700;
  font-size: 22px;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  letter-spacing: 0.5px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 20px;
  position: relative;
  z-index: 1;
}

.welcome-text {
  font-size: 15px;
  font-weight: 500;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.logout-btn {
  color: white;
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
  border-radius: 8px;
}

.logout-btn:hover {
  background-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
}

/* 登录页布局 */
.login-layout {
  width: 100%;
  height: 100vh;
}

/* 内容容器 */
.content-container {
  display: flex;
  flex: 1;
  min-height: calc(100vh - 65px);
}

.main-content {
  background: linear-gradient(135deg, #f5f7fa 0%, #e8f0fe 100%);
  padding: 0;
  flex: 1;
  width: 100%;
  min-width: 0;
  overflow-x: hidden;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .header {
    padding: 0 20px;
  }
  
  .logo h2 {
    font-size: 18px;
  }
}

@media (max-width: 768px) {
  .header {
    padding: 0 15px;
    height: 60px;
  }
  
  .logo h2 {
    font-size: 16px;
  }
  
  .welcome-text {
    display: none;
  }
  
  .content-container {
    min-height: calc(100vh - 60px);
  }
}

@media (max-width: 480px) {
  .header {
    padding: 0 10px;
  }
  
  .logo h2 {
    font-size: 14px;
  }
  
  .logout-btn {
    padding: 6px 12px;
    font-size: 13px;
  }
}
</style>

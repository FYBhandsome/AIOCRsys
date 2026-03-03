<script setup>
import { onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { SwitchButton, Fold, Expand } from '@element-plus/icons-vue'
import AIAssistant from './components/AIAssistant.vue'
import RoleSwitcher from './components/RoleSwitcher.vue'
import Sidebar from './components/Sidebar.vue'
import { useUserStore, useAppStore } from './store'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const appStore = useAppStore()

const isLoginPage = computed(() => {
  const publicPages = ['/login', '/register', '/reset-password', '/forgot-password']
  return publicPages.includes(route.path)
})

const isSidebarCollapsed = computed(() => appStore.sidebarCollapsed)

const isMobile = computed(() => window.innerWidth <= 768)

onMounted(() => {
  userStore.checkAuth()
})

const handleLogout = () => {
  userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}

const getRoleBadgeClass = (role) => {
  const classes = {
    admin: 'badge-error',
    teacher: 'badge-warning',
    student: 'badge-success'
  }
  return classes[role] || 'badge-primary'
}

const getRoleText = (role) => {
  const texts = {
    admin: '管理员',
    teacher: '教师',
    student: '学生'
  }
  return texts[role] || '用户'
}

const toggleMobileSidebar = () => {
  appStore.toggleSidebar()
}
</script>

<template>
  <div v-if="isLoginPage" class="login-layout">
    <router-view />
  </div>
  
  <div v-else-if="userStore.isAuthenticated" class="app-root">
    <el-container class="layout-container">
      <el-header class="app-header">
        <div class="header-content">
          <div class="header-left">
            <button class="hamburger-btn" @click="toggleMobileSidebar">
              <el-icon :size="20">
                <component :is="isSidebarCollapsed ? 'Expand' : 'Fold'" />
              </el-icon>
            </button>
            
            <div class="logo-section">
              <div class="logo-icon">
                <span class="logo-emoji">🎓</span>
              </div>
              <div class="logo-text">
                <h1 class="logo-title">综测计算助手</h1>
                <span class="logo-subtitle">智能综测评分系统</span>
              </div>
            </div>
          </div>
          
          <div class="header-actions">
            <RoleSwitcher />
            
            <div class="user-profile">
              <div class="user-avatar">
                {{ (userStore.userInfo.name || '用户').charAt(0) }}
              </div>
              <div class="user-details">
                <span class="user-name">{{ userStore.userInfo.name || '用户' }}</span>
                <span :class="['user-role', getRoleBadgeClass(userStore.userInfo.role)]">
                  {{ getRoleText(userStore.userInfo.role) }}
                </span>
              </div>
            </div>
            
            <el-button 
              class="logout-btn" 
              @click="handleLogout"
            >
              <el-icon><SwitchButton /></el-icon>
              退出
            </el-button>
          </div>
        </div>
        
        <div class="header-decoration">
          <div class="decoration-circle circle-1"></div>
          <div class="decoration-circle circle-2"></div>
          <div class="decoration-circle circle-3"></div>
        </div>
      </el-header>
      
      <el-container class="content-container">
        <el-aside :width="isSidebarCollapsed ? '64px' : '220px'" class="sidebar-aside">
          <Sidebar />
        </el-aside>
        <el-main class="main-content">
          <router-view v-slot="{ Component }">
            <transition name="fade-slide" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </el-main>
      </el-container>
    </el-container>

    <AIAssistant />
  </div>
  
  <div v-else class="login-layout">
    <router-view />
  </div>
</template>

<style scoped>
.app-root {
  min-height: 100vh;
  background: var(--bg-canvas);
}

.layout-container {
  min-height: 100vh;
}

.layout-container > .el-container {
  flex: 1;
}

.app-header {
  background: var(--gradient-primary);
  color: white;
  padding: 0;
  box-shadow: var(--shadow-lg);
  z-index: var(--z-sticky);
  height: 72px;
  position: relative;
  overflow: hidden;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 0 var(--spacing-8);
  position: relative;
  z-index: 2;
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
}

.hamburger-btn {
  display: none;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-lg);
  cursor: pointer;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}

.hamburger-btn:hover {
  background: rgba(255, 255, 255, 0.25);
}

.header-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  overflow: hidden;
}

.decoration-circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
}

.circle-1 {
  width: 200px;
  height: 200px;
  top: -100px;
  right: 10%;
  animation: float 6s ease-in-out infinite;
}

.circle-2 {
  width: 150px;
  height: 150px;
  top: -50px;
  right: 30%;
  animation: float 8s ease-in-out infinite reverse;
}

.circle-3 {
  width: 100px;
  height: 100px;
  bottom: -50px;
  left: 20%;
  animation: float 7s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50% { transform: translateY(-20px) rotate(180deg); }
}

.logo-section {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
}

.logo-icon {
  width: 48px;
  height: 48px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: var(--radius-xl);
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
}

.logo-emoji {
  font-size: 28px;
}

.logo-text {
  display: flex;
  flex-direction: column;
}

.logo-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  margin: 0;
  letter-spacing: var(--letter-spacing-tight);
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.logo-subtitle {
  font-size: var(--font-size-xs);
  opacity: 0.8;
  letter-spacing: var(--letter-spacing-wide);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-6);
}

.user-profile {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-2) var(--spacing-4);
  background: rgba(255, 255, 255, 0.15);
  border-radius: var(--radius-2xl);
  backdrop-filter: blur(10px);
}

.user-avatar {
  width: 36px;
  height: 36px;
  background: var(--gradient-accent);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-base);
  color: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.user-details {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.user-role {
  font-size: var(--font-size-xs);
  padding: 1px 8px;
  border-radius: var(--radius-full);
  background: rgba(255, 255, 255, 0.2);
  width: fit-content;
}

.user-role.badge-success {
  background: rgba(34, 197, 94, 0.3);
}

.user-role.badge-warning {
  background: rgba(245, 158, 11, 0.3);
}

.user-role.badge-error {
  background: rgba(239, 68, 68, 0.3);
}

.logout-btn {
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: var(--spacing-2) var(--spacing-4);
  border-radius: var(--radius-lg);
  font-weight: var(--font-weight-medium);
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  border-color: rgba(255, 255, 255, 0.5);
  transform: translateY(-2px);
}

.login-layout {
  width: 100%;
  min-height: 100vh;
}

.content-container {
  display: flex;
  flex: 1;
  min-height: calc(100vh - 72px);
}

.sidebar-aside {
  background: var(--bg-elevated, #fff);
  transition: width var(--transition-normal, 0.3s ease);
  overflow: hidden;
  flex-shrink: 0;
}

.main-content {
  background: var(--bg-canvas);
  padding: 0;
  flex: 1;
  width: 100%;
  min-width: 0;
  overflow-x: hidden;
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all var(--transition-normal);
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

@media (max-width: 1024px) {
  .header-content {
    padding: 0 var(--spacing-6);
  }
  
  .logo-subtitle {
    display: none;
  }
}

@media (max-width: 768px) {
  .app-header {
    height: 64px;
  }
  
  .header-content {
    padding: 0 var(--spacing-4);
  }
  
  .hamburger-btn {
    display: flex;
  }
  
  .logo-icon {
    width: 40px;
    height: 40px;
  }
  
  .logo-emoji {
    font-size: 22px;
  }
  
  .logo-title {
    font-size: var(--font-size-lg);
  }
  
  .user-details {
    display: none;
  }
  
  .user-profile {
    padding: var(--spacing-1);
    background: transparent;
  }
  
  .logout-btn {
    padding: var(--spacing-2);
  }
  
  .content-container {
    min-height: calc(100vh - 64px);
  }
  
  .sidebar-aside {
    position: fixed;
    left: 0;
    top: 64px;
    height: calc(100vh - 64px);
    z-index: var(--z-sticky, 100);
    width: 220px !important;
    transform: translateX(0);
    transition: transform var(--transition-normal, 0.3s ease);
  }
  
  .sidebar-aside:has(.sidebar.is-collapsed) {
    transform: translateX(-100%);
  }
}

@media (max-width: 480px) {
  .header-content {
    padding: 0 var(--spacing-3);
  }
  
  .logo-text {
    display: none;
  }
  
  .header-actions {
    gap: var(--spacing-3);
  }
}
</style>

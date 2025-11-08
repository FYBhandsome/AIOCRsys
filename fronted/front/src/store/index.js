import { defineStore } from 'pinia'

// 用户状态管理
export const useUserStore = defineStore('user', {
  state: () => ({
    userInfo: {
      id: '',
      username: '',
      name: '',
      role: '',
      roleName: '',
      avatar: ''
    },
    isAuthenticated: false
  }),
  
  getters: {
    // 简化的getter，直接通过state访问
    userRole: (state) => state.userInfo.role,
    userRoleName: (state) => state.userInfo.roleName,
    isLoggedIn: (state) => state.isAuthenticated,
    isStudent: (state) => state.userInfo.role === 'student',
    isTeacher: (state) => state.userInfo.role === 'teacher',
    isAdmin: (state) => state.userInfo.role === 'admin',
    // 权限检查
    hasPermission: (state) => (permission) => {
      const permissions = {
        student: ['upload:material', 'view:self'],
        teacher: ['upload:score', 'view:class', 'analyze:score'],
        admin: ['upload:rule', 'manage:system', 'view:all']
      }
      return permissions[state.userInfo.role]?.includes(permission) || false
    }
  },
  
  actions: {
    // 登录
    login(userInfo, token) {
      this.userInfo = userInfo
      this.isAuthenticated = true
      localStorage.setItem('token', token)
      localStorage.setItem('userInfo', JSON.stringify(userInfo))
    },
    
    // 登出
    logout() {
      this.userInfo = { id: '', username: '', name: '', role: '', roleName: '', avatar: '' }
      this.isAuthenticated = false
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
      localStorage.removeItem('rememberedUser')
    },
    
    // 检查登录状态并恢复用户信息
    checkAuth() {
      const token = localStorage.getItem('token')
      const userInfoStr = localStorage.getItem('userInfo')
      
      if (token && userInfoStr) {
        try {
          this.userInfo = JSON.parse(userInfoStr)
          this.isAuthenticated = true
          return true
        } catch (e) {
          console.error('Failed to parse user info:', e)
          this.logout()
          return false
        }
      }
      
      this.isAuthenticated = false
      return false
    },
    
    // 更新用户信息
    updateUserInfo(userInfo) {
      this.userInfo = { ...this.userInfo, ...userInfo }
      localStorage.setItem('userInfo', JSON.stringify(this.userInfo))
    },
    
    // 切换角色（仅开发模式）
    switchRole(userInfo) {
      this.userInfo = userInfo
      this.isAuthenticated = true
      localStorage.setItem('userInfo', JSON.stringify(userInfo))
      // 保持token不变
      if (!localStorage.getItem('token')) {
        localStorage.setItem('token', 'dev-token')
      }
    }
  }
})

// 应用状态管理
export const useAppStore = defineStore('app', {
  state: () => ({
    sidebarCollapsed: false,
    theme: 'light',
    loading: false
  }),
  
  actions: {
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed
    },
    
    setTheme(theme) {
      this.theme = theme
    },
    
    setLoading(status) {
      this.loading = status
    }
  }
})
import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store'
import { ElMessage } from 'element-plus'

// 开发模式配置：禁用认证（与后端保持一致）
const DISABLE_AUTH = import.meta.env.DEV && false  // 改为 true 以禁用认证

// 路由懒加载
const Login = () => import('../views/Login.vue')
const Home = () => import('../views/Home.vue')
const StudentDashboard = () => import('../views/StudentDashboard.vue')
const TeacherDashboard = () => import('../views/TeacherDashboard.vue')
const AdminDashboard = () => import('../views/AdminDashboard.vue')
const MaterialUpload = () => import('../views/MaterialUpload.vue')
const Analysis = () => import('../views/Analysis.vue')
const ResultList = () => import('../views/ResultList.vue')
const RuleUpload = () => import('../views/RuleUpload.vue')
const ScoreUpload = () => import('../views/ScoreUpload.vue')
const ScoreAnalysis = () => import('../views/ScoreAnalysis.vue')
const ForgotPassword = () => import('../views/ForgotPassword.vue')
const DatabaseManager = () => import('../components/DatabaseManager.vue')
const ComprehensiveScoreConfig = () => import('../views/ComprehensiveScoreConfig.vue')
const LicenseManagement = () => import('../views/LicenseManagement.vue')
const SystemMonitor = () => import('../views/SystemMonitor.vue')
const StudentList = () => import('../views/StudentList.vue')
const ScoreVisualization = () => import('../views/ScoreVisualization.vue')
const ClassRanking = () => import('../views/ClassRanking.vue')

// 路由配置
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: ForgotPassword,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Root',
    component: () => import('../views/Home.vue'),
    meta: { requiresAuth: true }
  },
  // 学生路由
  {
    path: '/student',
    meta: { requiresAuth: true, roles: ['student'] },
    children: [
      {
        path: 'dashboard',
        name: 'StudentDashboard',
        component: StudentDashboard,
        meta: { title: '学生主页', roles: ['student'] }
      }
    ]
  },
  // 教师路由
  {
    path: '/teacher',
    meta: { requiresAuth: true, roles: ['teacher'] },
    children: [
      {
        path: 'dashboard',
        name: 'TeacherDashboard',
        component: TeacherDashboard,
        meta: { title: '教师主页', roles: ['teacher'] }
      },
      {
        path: 'students',
        name: 'StudentList',
        component: StudentList,
        meta: { title: '学生列表', roles: ['teacher'] }
      },
      {
        path: 'visualization',
        name: 'ScoreVisualization',
        component: ScoreVisualization,
        meta: { title: '成绩可视化分析', roles: ['teacher'] }
      },
      {
        path: 'ranking',
        name: 'ClassRanking',
        component: ClassRanking,
        meta: { title: '班级排名', roles: ['teacher'] }
      }
    ]
  },
  // 管理员路由
  {
    path: '/admin',
    meta: { requiresAuth: true, roles: ['admin'] },
    children: [
      {
        path: 'dashboard',
        name: 'AdminDashboard',
        component: AdminDashboard,
        meta: { title: '管理员主页', roles: ['admin'] }
      },
      {
        path: 'database',
        name: 'DatabaseManager',
        component: DatabaseManager,
        meta: { title: '数据库管理', roles: ['admin'] }
      },
      {
        path: 'comprehensive-score-config',
        name: 'ComprehensiveScoreConfig',
        component: ComprehensiveScoreConfig,
        meta: { title: '综测配置管理', roles: ['admin'] }
      },
      {
        path: 'license',
        name: 'LicenseManagement',
        component: LicenseManagement,
        meta: { title: '授权码管理', roles: ['admin'] }
      },
      {
        path: 'system-monitor',
        name: 'SystemMonitor',
        component: SystemMonitor,
        meta: { title: '系统监控', roles: ['admin'] }
      }
    ]
  },
  // 通用路由（需要权限控制）
  {
    path: '/upload',
    name: 'Upload',
    redirect: '/upload/material',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'material',
        name: 'MaterialUpload',
        component: MaterialUpload,
        meta: { title: '材料上传', roles: ['student'] }
      },
      {
        path: 'rule',
        name: 'RuleUpload',
        component: RuleUpload,
        meta: { title: '规则上传', roles: ['admin'] }
      },
      {
        path: 'score',
        name: 'ScoreUpload',
        component: ScoreUpload,
        meta: { title: '成绩上传', roles: ['teacher'] }
      }
    ]
  },
  {
    path: '/analysis',
    name: 'Analysis',
    redirect: '/analysis/material',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'material',
        name: 'MaterialAnalysis',
        component: Analysis,
        meta: { title: '材料分析', roles: ['student', 'teacher', 'admin'] }
      },
      {
        path: 'score',
        name: 'ScoreAnalysis',
        component: ScoreAnalysis,
        meta: { title: '成绩分析', roles: ['teacher', 'admin'] }
      }
    ]
  },
  {
    path: '/results',
    name: 'ResultList',
    component: ResultList,
    meta: { requiresAuth: true, title: '结果列表', roles: ['student', 'teacher', 'admin'] }
  },
  // 404页面
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const isAuthenticated = userStore.checkAuth()
  
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - 综测系统` : '综测系统'
  
  // 🔓 开发模式：禁用认证
  if (DISABLE_AUTH) {
    // 自动设置为管理员用户（可以访问所有页面）
    if (!isAuthenticated) {
      userStore.login({
        id: 'dev_admin',
        username: 'dev_admin',
        name: '开发模式',
        role: 'admin',
        roleName: '管理员'
      }, 'dev-token')
    }
    
    // 跳过登录页，直接进入主页
    if (to.path === '/login' || to.path === '/') {
      next('/admin/dashboard')
      return
    }
    
    next()
    return
  }
  
  // 🔒 生产模式：正常认证流程
  
  // 根路径重定向到对应角色的首页
  if (to.path === '/' && isAuthenticated) {
    const role = userStore.userInfo.role
    const roleRoutes = {
      student: '/student/dashboard',
      teacher: '/teacher/dashboard',
      admin: '/admin/dashboard'
    }
    next(roleRoutes[role] || '/login')
    return
  }
  
  // 如果是登录页，已登录则跳转到对应的首页
  if (to.path === '/login' && isAuthenticated) {
    const role = userStore.userInfo.role
    const roleRoutes = {
      student: '/student/dashboard',
      teacher: '/teacher/dashboard',
      admin: '/admin/dashboard'
    }
    next(roleRoutes[role] || '/')
    return
  }
  
  // 需要认证的页面，未登录则跳转到登录页
  if (to.meta.requiresAuth && !isAuthenticated) {
    ElMessage.warning('请先登录')
    next('/login')
    return
  }
  
  // 角色权限检查
  if (to.meta.roles && isAuthenticated) {
    const userRole = userStore.userInfo.role
    if (!to.meta.roles.includes(userRole)) {
      ElMessage.error('您没有权限访问此页面')
      // 跳转回用户对应的首页
      const roleRoutes = {
        student: '/student/dashboard',
        teacher: '/teacher/dashboard',
        admin: '/admin/dashboard'
      }
      next(roleRoutes[userRole] || '/login')
      return
    }
  }
  
  next()
})

export default router
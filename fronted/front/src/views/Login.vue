<template>
  <div class="login-container">
    <!-- 视频背景 -->
    <video
      ref="videoElement"
      class="video-background"
      autoplay
      loop
      muted
      playsinline
      preload="auto"
    >
      <source src="/background.mp4" type="video/mp4">
    </video>
    
    <!-- 轻微遮罩层提升文字对比度 -->
    <div class="video-overlay"></div>
    
    <!-- 可滚动的内容区域 -->
    <div class="scrollable-content">
      <!-- Hero区域 - 登录表单 -->
      <div class="hero-section">
        <div class="login-wrapper">
          <div class="brand-intro">
            <h1 class="brand-title">综测计算助手</h1>
            <p class="brand-subtitle">智能化综合测评管理平台</p>
          </div>
          
          <div class="form-wrapper">
            <!-- 登录/注册选项卡 -->
            <div class="form-tabs">
              <button 
                :class="['tab-button', { active: activeTab === 'login' }]"
                @click="activeTab = 'login'"
              >
                登录
              </button>
              <button 
                :class="['tab-button', { active: activeTab === 'register' }]"
                @click="activeTab = 'register'"
              >
                注册
              </button>
            </div>
            
            <!-- 登录表单 -->
            <el-form
              v-if="activeTab === 'login'"
              ref="loginFormRef"
              :model="loginForm"
              :rules="loginRules"
              class="login-form"
            >
              <el-form-item prop="username">
                <el-input
                  v-model="loginForm.username"
                  placeholder="请输入用户名"
                  prefix-icon="User"
                  size="large"
                />
              </el-form-item>
              
              <el-form-item prop="password">
                <el-input
                  v-model="loginForm.password"
                  type="password"
                  placeholder="请输入密码"
                  prefix-icon="Lock"
                  size="large"
                  show-password
                />
              </el-form-item>
              
              <!-- 角色选择已移除，系统将根据用户信息自动识别角色 -->
              
              <el-form-item>
                <el-checkbox v-model="loginForm.remember">记住我</el-checkbox>
              </el-form-item>
              
              <el-form-item>
                <el-button
                  type="primary"
                  class="login-button"
                  :loading="loginLoading"
                  @click="handleLogin"
                >
                  登录
                </el-button>
              </el-form-item>
              
              <div class="form-footer">
                <router-link to="/forgot-password">忘记密码？</router-link>
              </div>
            </el-form>
            
            <!-- 注册表单 -->
            <el-form
              v-if="activeTab === 'register'"
              ref="registerFormRef"
              :model="registerForm"
              :rules="registerRules"
              class="login-form"
            >
              <el-form-item prop="username">
                <el-input
                  v-model="registerForm.username"
                  placeholder="请输入用户名"
                  prefix-icon="User"
                  size="large"
                />
              </el-form-item>
              
              <el-form-item prop="email">
                <el-input
                  v-model="registerForm.email"
                  placeholder="请输入邮箱"
                  prefix-icon="Message"
                  size="large"
                />
              </el-form-item>
              
              <el-form-item prop="password">
                <el-input
                  v-model="registerForm.password"
                  type="password"
                  placeholder="请输入密码"
                  prefix-icon="Lock"
                  size="large"
                  show-password
                />
              </el-form-item>
              
              <el-form-item prop="confirmPassword">
                <el-input
                  v-model="registerForm.confirmPassword"
                  type="password"
                  placeholder="请确认密码"
                  prefix-icon="Lock"
                  size="large"
                  show-password
                />
              </el-form-item>
              
              <el-form-item prop="role">
                <el-select
                  v-model="registerForm.role"
                  placeholder="请选择角色"
                  size="large"
                  style="width: 100%"
                >
                  <el-option label="学生" value="student" />
                  <el-option label="教师" value="teacher" />
                  <el-option label="管理员" value="admin" />
                </el-select>
              </el-form-item>
              
              <el-form-item>
                <el-button
                  type="primary"
                  class="login-button"
                  :loading="registerLoading"
                  @click="handleRegister"
                >
                  注册
                </el-button>
              </el-form-item>
              
              <div class="form-footer">
                已有账号？<a href="javascript:void(0)" @click="activeTab = 'login'">立即登录</a>
              </div>
            </el-form>
          </div>
        </div>
        
        <!-- 向下滚动提示 -->
        <div class="scroll-hint">
          <span>向下滚动了解更多</span>
          <el-icon class="scroll-icon"><ArrowDown /></el-icon>
        </div>
      </div>
      
      <!-- 核心功能部分 -->
      <div class="features-section">
        <h2 class="section-title">核心功能</h2>
        <p class="section-subtitle">基于AI技术的智能化综合测评解决方案</p>
        <el-row :gutter="30">
          <el-col :xs="24" :sm="12" :md="8">
            <div class="feature-card">
              <div class="feature-icon">
                <el-icon><Document /></el-icon>
              </div>
              <h3>规则文件上传</h3>
              <p>支持 Word/PDF 格式的学校综测实施细则，系统通过 RAG 技术构建可检索的知识库</p>
            </div>
          </el-col>
          
          <el-col :xs="24" :sm="12" :md="8">
            <div class="feature-card">
              <div class="feature-icon">
                <el-icon><Upload /></el-icon>
              </div>
              <h3>材料智能识别</h3>
              <p>支持上传成绩单、奖状照片等材料，通过 OCR + AI 大模型自动分类和提取关键信息</p>
            </div>
          </el-col>
          
          <el-col :xs="24" :sm="12" :md="8">
            <div class="feature-card">
              <div class="feature-icon">
                <el-icon><DataAnalysis /></el-icon>
              </div>
              <h3>智能计算分析</h3>
              <p>自动生成个人综测报告和班级汇总表，包含可视化图表和得分明细</p>
            </div>
          </el-col>
        </el-row>
      </div>
      
      <!-- 工作流程部分 -->
      <div class="process-section">
        <h2 class="section-title">工作流程</h2>
        <p class="section-subtitle">简单四步，轻松完成综合测评</p>
        <div class="steps-wrapper">
          <div class="step-item" v-for="(step, index) in workflowSteps" :key="index">
            <div class="step-number">{{ index + 1 }}</div>
            <div class="step-content">
              <h3>{{ step.title }}</h3>
              <p>{{ step.description }}</p>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 页脚 -->
      <div class="footer-section">
        <p>© 2025 综测计算助手. All rights reserved.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Message, Document, Upload, DataAnalysis, ArrowDown } from '@element-plus/icons-vue'
import { useUserStore } from '@/store'
import { authAPI } from '@/services/api'

const router = useRouter()
const userStore = useUserStore()

// 视频元素引用
const videoElement = ref(null)

// 标签页状态
const activeTab = ref('login')

// 登录表单
const loginFormRef = ref()
const loginForm = reactive({
  username: '',
  password: '',
  remember: false
})

// 注册表单
const registerFormRef = ref()
const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  role: ''
})

// 加载状态
const loginLoading = ref(false)
const registerLoading = ref(false)

// 工作流程步骤
const workflowSteps = [
  {
    title: '上传规则文件',
    description: '上传学校综测实施细则文件，系统自动解析规则'
  },
  {
    title: '上传个人材料',
    description: '上传成绩单、奖状等证明材料，系统自动识别提取'
  },
  {
    title: '智能计算分析',
    description: '系统根据规则自动计算综测得分，生成详细报告'
  },
  {
    title: '导出结果',
    description: '导出个人综测报告和班级汇总表，支持多种格式'
  }
]

// 登录表单验证规则
const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ]
}

// 注册表单验证规则
const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== registerForm.password) {
          callback(new Error('两次输入密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

// 登录处理
const handleLogin = async () => {
  const valid = await loginFormRef.value.validate().catch(() => false)
  if (!valid) return
  
  loginLoading.value = true
  
  try {
    // 调用后端登录API
    const response = await authAPI.login(loginForm.username, loginForm.password)
    
    const { access_token } = response
    
    // 先保存token
    localStorage.setItem('token', access_token)
    
    // 获取用户信息
    const userInfoResponse = await authAPI.getUserInfo()
    
    // 根据角色设置不同的用户信息
    const roleNames = {
      student: '学生',
      teacher: '教师',
      admin: '管理员'
    }
    
    // 构建用户信息
    const userInfo = {
      id: userInfoResponse.id || 'user_' + Date.now(),
      username: userInfoResponse.username,
      name: userInfoResponse.real_name || userInfoResponse.username,
      role: userInfoResponse.role,
      roleName: roleNames[userInfoResponse.role],
      email: userInfoResponse.email,
      studentId: userInfoResponse.student_id,
      classId: userInfoResponse.class_id,
      avatar: ''
    }
    
    // 使用store的login方法
    userStore.login(userInfo, access_token)
    
    // 如果选择了"记住我"，保存到localStorage
    if (loginForm.remember) {
      localStorage.setItem('rememberedUser', JSON.stringify({
        username: loginForm.username,
        role: userInfoResponse.role
      }))
    }
    
    ElMessage.success(`欢迎您，${roleNames[userInfoResponse.role]}：${userInfo.name}`)
    
    // 根据角色跳转到不同页面
    setTimeout(() => {
      const roleRoutes = {
        student: '/student/dashboard',
        teacher: '/teacher/dashboard',
        admin: '/admin/dashboard'
      }
      router.push(roleRoutes[userInfoResponse.role] || '/')
    }, 500)
  } catch (error) {
    console.error('Login error:', error)
    localStorage.removeItem('token')
    const errorMsg = error.response?.data?.detail || error.message || '登录失败，请检查用户名和密码'
    ElMessage.error(errorMsg)
  } finally {
    loginLoading.value = false
  }
}

// 注册处理
const handleRegister = async () => {
  const valid = await registerFormRef.value.validate().catch(() => false)
  if (!valid) return
  
  registerLoading.value = true
  
  try {
    // 调用后端注册API
    const userData = {
      username: registerForm.username,
      email: registerForm.email,
      password: registerForm.password,
      role: registerForm.role
    }
    
    await authAPI.register(userData)
    
    ElMessage.success('注册成功，请登录')
    activeTab.value = 'login'
    
    // 自动填充登录表单
    loginForm.username = registerForm.username
    
    // 清空注册表单
    registerForm.username = ''
    registerForm.email = ''
    registerForm.password = ''
    registerForm.confirmPassword = ''
    registerForm.role = ''
  } catch (error) {
    console.error('Register error:', error)
    const errorMsg = error.response?.data?.detail || '注册失败，请稍后再试'
    ElMessage.error(errorMsg)
  } finally {
    registerLoading.value = false
  }
}

// 组件挂载后
onMounted(() => {
  // 检查登录状态
  if (localStorage.getItem('isLoggedIn') === 'true') {
    router.push('/')
    return
  }
  
  // 初始化视频背景
  const video = videoElement.value
  if (!video) return
  
  // 尝试自动播放
  const playPromise = video.play()
  if (playPromise !== undefined) {
    playPromise.catch(() => {
      // 自动播放失败，静音后重试
      video.muted = true
      video.play().catch(() => {
        // 等待用户交互后播放
        document.addEventListener('click', () => video.play(), { once: true })
      })
    })
  }
})
</script>

<style scoped>
/* 容器和背景 */
.login-container {
  height: 100vh;
  width: 100vw;
  position: relative;
  overflow: hidden;
}

.video-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  object-fit: cover;
  background-color: #1976d2;
}

.video-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, 
    rgba(25, 118, 210, 0.15) 0%, 
    rgba(66, 165, 245, 0.1) 50%,
    rgba(187, 222, 251, 0.15) 100%);
  z-index: 2;
  pointer-events: none;
}

/* 可滚动内容区域 */
.scrollable-content {
  height: 100vh;
  overflow-y: auto;
  overflow-x: hidden;
  position: relative;
  z-index: 10;
  scroll-behavior: smooth;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.5) transparent;
}

.scrollable-content::-webkit-scrollbar {
  width: 8px;
}

.scrollable-content::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
}

.scrollable-content::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 4px;
}

.scrollable-content::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}

/* Hero区域 */
.hero-section {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 40px 20px;
  position: relative;
}

.login-wrapper {
  width: 100%;
  max-width: 480px;
  animation: fadeInUp 0.8s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 品牌介绍 */
.brand-intro {
  text-align: center;
  margin-bottom: 30px;
}

.brand-title {
  font-size: 42px;
  font-weight: 700;
  color: white;
  margin-bottom: 12px;
  text-shadow: 0 2px 20px rgba(0, 0, 0, 0.3);
  letter-spacing: 2px;
}

.brand-subtitle {
  font-size: 18px;
  color: rgba(255, 255, 255, 0.95);
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  font-weight: 400;
}

/* 表单容器 */
.form-wrapper {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

/* 选项卡 */
.form-tabs {
  display: flex;
  margin-bottom: 30px;
  background-color: rgba(240, 244, 248, 0.8);
  border-radius: 12px;
  padding: 4px;
}

.tab-button {
  flex: 1;
  padding: 12px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 500;
  color: #606266;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.tab-button.active {
  background: #409eff;
  color: white;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
}

/* 表单样式 */
.login-form {
  width: 100%;
}

:deep(.el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.95);
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  padding: 4px 15px;
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.25);
}

:deep(.el-input__inner) {
  color: #333;
  font-weight: 500;
}

:deep(.el-input__prefix-inner) {
  color: #409eff;
}

:deep(.el-checkbox__label) {
  color: #333;
  font-weight: 500;
}

:deep(.el-select .el-input .el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.95);
}

.login-button {
  width: 100%;
  padding: 14px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 10px;
  margin-top: 10px;
  box-shadow: 0 6px 20px rgba(64, 158, 255, 0.35);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(64, 158, 255, 0.45);
}

.login-button:active {
  transform: translateY(0);
}

.form-footer {
  text-align: center;
  margin-top: 20px;
  color: #606266;
  font-size: 14px;
}

.form-footer a {
  color: #409eff;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s ease;
}

.form-footer a:hover {
  color: #5cadff;
  text-decoration: underline;
}

/* 滚动提示 */
.scroll-hint {
  position: absolute;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  color: white;
  font-size: 14px;
  cursor: pointer;
  animation: bounce 2s infinite;
}

.scroll-hint span {
  margin-bottom: 8px;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

.scroll-icon {
  font-size: 24px;
}

@keyframes bounce {
  0%, 100% {
    transform: translateX(-50%) translateY(0);
  }
  50% {
    transform: translateX(-50%) translateY(-10px);
  }
}

/* 功能介绍区域 */
.features-section, .process-section {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 60px 40px;
  margin: 40px auto;
  max-width: 1200px;
  box-shadow: 0 15px 50px rgba(0, 0, 0, 0.1);
}

.section-title {
  text-align: center;
  font-size: 32px;
  font-weight: 700;
  color: #2c3e50;
  margin-bottom: 15px;
  position: relative;
}

.section-subtitle {
  text-align: center;
  font-size: 16px;
  color: #606266;
  margin-bottom: 40px;
}

.section-title::after {
  content: '';
  position: absolute;
  bottom: -15px;
  left: 50%;
  transform: translateX(-50%);
  width: 80px;
  height: 4px;
  background: linear-gradient(90deg, #409eff, #67c23a);
  border-radius: 2px;
}

/* 功能卡片 */
.feature-card {
  background: white;
  border-radius: 16px;
  padding: 35px 25px;
  text-align: center;
  height: 100%;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.feature-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 12px 40px rgba(64, 158, 255, 0.15);
}

.feature-icon {
  font-size: 48px;
  color: #409eff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 90px;
  height: 90px;
  background: rgba(64, 158, 255, 0.1);
  border-radius: 50%;
  margin: 0 auto 20px;
  transition: all 0.4s ease;
}

.feature-card:hover .feature-icon {
  transform: scale(1.1);
  background: rgba(64, 158, 255, 0.2);
}

.feature-card h3 {
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 15px;
}

.feature-card p {
  font-size: 14px;
  color: #606266;
  line-height: 1.8;
}

/* 工作流程步骤 */
.steps-wrapper {
  max-width: 800px;
  margin: 0 auto;
}

.step-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 30px;
  padding: 25px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
  cursor: pointer;
}

.step-item:hover {
  transform: translateX(10px);
  box-shadow: 0 8px 30px rgba(64, 158, 255, 0.15);
}

.step-item:last-child {
  margin-bottom: 0;
}

.step-number {
  flex-shrink: 0;
  width: 60px;
  height: 60px;
  background: #409eff;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 700;
  margin-right: 25px;
  box-shadow: 0 4px 15px rgba(64, 158, 255, 0.3);
}

.step-content {
  flex: 1;
  padding-top: 5px;
}

.step-content h3 {
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 10px;
}

.step-content p {
  font-size: 14px;
  color: #606266;
  line-height: 1.8;
}

/* 页脚 */
.footer-section {
  text-align: center;
  padding: 40px 20px;
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

/* 响应式调整 */
@media (max-width: 768px) {
  .hero-section {
    padding: 30px 15px;
  }
  
  .brand-title {
    font-size: 32px;
  }
  
  .brand-subtitle {
    font-size: 16px;
  }
  
  .form-wrapper {
    padding: 30px 25px;
  }
  
  .features-section, .process-section {
    padding: 40px 25px;
    margin: 30px 15px;
  }
  
  .section-title {
    font-size: 26px;
  }
  
  .section-subtitle {
    font-size: 14px;
  }
  
  .feature-card {
    margin-bottom: 20px;
    padding: 30px 20px;
  }
  
  .step-item {
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 20px;
  }
  
  .step-number {
    margin-right: 0;
    margin-bottom: 15px;
  }
  
  .step-item:hover {
    transform: translateY(-5px);
  }
}
</style>
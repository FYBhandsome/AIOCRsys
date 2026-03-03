<template>
  <div class="admin-dashboard">
    <!-- 欢迎区域 -->
    <div class="welcome-section">
      <div class="welcome-content">
        <h1 class="welcome-title">👨‍💼 欢迎，{{ userStore.userInfo.name }}管理员</h1>
        <p class="welcome-subtitle">管理系统规则，配置综测标准，确保评分公平公正</p>
      </div>
      <div class="welcome-stats">
        <el-card class="stat-card" v-loading="loading">
          <div class="stat-icon">📋</div>
          <div class="stat-info">
            <div class="stat-value">{{ ruleCount }}</div>
            <div class="stat-label">综测规则</div>
          </div>
        </el-card>
        <el-card class="stat-card" v-loading="loading">
          <div class="stat-icon">👥</div>
          <div class="stat-info">
            <div class="stat-value">{{ totalUsers }}</div>
            <div class="stat-label">系统用户</div>
          </div>
        </el-card>
        <el-card class="stat-card" v-loading="loading">
          <div class="stat-icon">✅</div>
          <div class="stat-info">
            <div class="stat-value">{{ approvedCount }}</div>
            <div class="stat-label">待审核</div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 快速操作 -->
    <div class="quick-actions">
      <h2 class="section-title">
        <el-icon><Lightning /></el-icon>
        快速操作
      </h2>
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="6">
          <el-card class="action-card" @click="activeTab = 'upload'">
            <div class="action-icon">📤</div>
            <h3 class="action-title">上传综测规则</h3>
            <p class="action-desc">上传新的综测评分规则文档</p>
            <el-button type="primary" size="small">立即上传</el-button>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-card class="action-card" @click="activeTab = 'manage'">
            <div class="action-icon">⚙️</div>
            <h3 class="action-title">规则管理</h3>
            <p class="action-desc">查看和编辑现有规则</p>
            <el-button type="success" size="small">管理规则</el-button>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-card class="action-card" @click="navigateToScoreConfig">
            <div class="action-icon">📊</div>
            <h3 class="action-title">综测配置</h3>
            <p class="action-desc">配置A/B/C类权重和成绩字段</p>
            <el-button type="danger" size="small">配置综测</el-button>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-card class="action-card" @click="activeTab = 'system'">
            <div class="action-icon">🔧</div>
            <h3 class="action-title">系统设置</h3>
            <p class="action-desc">配置系统参数和权限</p>
            <el-button type="warning" size="small">系统配置</el-button>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-card class="action-card" @click="navigateToSystemMonitor">
            <div class="action-icon">📈</div>
            <h3 class="action-title">系统监控</h3>
            <p class="action-desc">查看RAG系统和向量数据库状态</p>
            <el-button type="info" size="small">系统监控</el-button>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <el-tabs v-model="activeTab" class="content-tabs">
        <!-- 规则上传 -->
        <el-tab-pane label="规则上传" name="upload">
          <div class="tab-content">
            <h2 class="section-title">
              <el-icon><Upload /></el-icon>
              综测规则上传
            </h2>
            <RuleUpload />
          </div>
        </el-tab-pane>

        <!-- 规则管理 -->
        <el-tab-pane label="规则管理" name="manage">
          <div class="tab-content">
            <h2 class="section-title">
              <el-icon><DocumentCopy /></el-icon>
              规则列表
            </h2>
            <RuleList />
          </div>
        </el-tab-pane>

        <!-- 系统设置 -->
        <el-tab-pane label="系统设置" name="system">
          <div class="tab-content">
            <h2 class="section-title">
              <el-icon><Setting /></el-icon>
              系统配置
            </h2>
            <SystemSettings />
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- AI助手 -->
    <AIAssistant />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store'
import { Lightning, Upload, DocumentCopy, Setting } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import RuleUpload from '@/views/RuleUpload.vue'
import RuleList from '@/components/RuleList.vue'
import SystemSettings from '@/components/SystemSettings.vue'
import AIAssistant from '@/components/AIAssistant.vue'
import { adminAPI } from '@/services/api'

const router = useRouter()
const userStore = useUserStore()

// 统计数据
const ruleCount = ref(0)
const totalUsers = ref(0)
const approvedCount = ref(0)
const loading = ref(false)

// 当前激活的标签页
const activeTab = ref('upload')

// 规则文档列表
const ruleDocuments = ref([])

// 加载管理员数据
const loadAdminData = async () => {
  // 如果已有数据，不再重复加载
  if (ruleCount.value > 0 || totalUsers.value > 0) {
    return
  }
  
  loading.value = true
  try {
    // 并发加载多个数据，设置超时时间为5秒
    const timeoutPromise = new Promise((_, reject) => 
      setTimeout(() => reject(new Error('请求超时')), 5000)
    )
    
    const [rulesRes, usersRes] = await Promise.race([
      Promise.all([
        adminAPI.getRuleDocuments(false).catch(err => {
          console.warn('获取规则文档失败:', err)
          return []
        }),
        adminAPI.getUsers().catch(err => {
          console.warn('获取用户列表失败:', err)
          return []
        })
      ]),
      timeoutPromise
    ])
    
    // 更新规则文档数据
    const documents = rulesRes?.data?.documents || rulesRes?.documents || []
    ruleDocuments.value = Array.isArray(documents) ? documents : (Array.isArray(rulesRes) ? rulesRes : [])
    ruleCount.value = ruleDocuments.value.length
    
    // 更新用户数据
    totalUsers.value = usersRes?.length || 0
    
    // 计算待审核数量（这里可能需要根据实际业务调整）
    approvedCount.value = ruleDocuments.value.filter(doc => !doc.enabled).length
  } catch (error) {
    console.error('加载管理员数据失败:', error)
    // 静默失败，使用默认值
    ruleCount.value = 0
    totalUsers.value = 0
    approvedCount.value = 0
  } finally {
    loading.value = false
  }
}

// 刷新数据方法（供子组件调用）
const refreshData = () => {
  loadAdminData()
}

// 导航到综测配置页面
const navigateToScoreConfig = () => {
  router.push('/admin/comprehensive-score-config')
}

// 导航到系统监控页面
const navigateToSystemMonitor = () => {
  router.push('/admin/system-monitor')
}

// 暴露给子组件
defineExpose({
  refreshData
})

// 组件挂载时加载数据
onMounted(() => {
  // 延迟加载，避免切换角色时的阻塞
  setTimeout(() => {
    loadAdminData()
  }, 100)
})
</script>

<style scoped>
.admin-dashboard {
  padding: 30px;
  max-width: 1600px;
  margin: 0 auto;
  background: linear-gradient(135deg, #f5f7fa 0%, #fff3e0 100%);
  min-height: 100vh;
}

/* 欢迎区域 */
.welcome-section {
  background: linear-gradient(135deg, #ff6f00 0%, #ff9100 100%);
  border-radius: 20px;
  padding: 40px;
  margin-bottom: 30px;
  color: white;
  box-shadow: 0 10px 40px rgba(255, 111, 0, 0.4);
}

.welcome-content {
  margin-bottom: 30px;
}

.welcome-title {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 10px;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.welcome-subtitle {
  font-size: 16px;
  opacity: 0.95;
}

.welcome-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-5px);
  background: rgba(255, 255, 255, 0.25);
}

.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  padding: 20px;
}

.stat-icon {
  font-size: 48px;
  margin-right: 20px;
}

.stat-info {
  color: white;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
}

/* 区块标题 */
.section-title {
  display: flex;
  align-items: center;
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 20px;
  color: #2c3e50;
}

.section-title .el-icon {
  margin-right: 10px;
  font-size: 28px;
  color: #ff6f00;
}

/* 快速操作 */
.quick-actions {
  margin-bottom: 30px;
}

.action-card {
  text-align: center;
  cursor: pointer;
  border-radius: 16px;
  transition: all 0.3s ease;
  height: 100%;
}

.action-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 40px rgba(255, 111, 0, 0.25);
}

.action-card :deep(.el-card__body) {
  padding: 30px 20px;
}

.action-icon {
  font-size: 56px;
  margin-bottom: 15px;
}

.action-title {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 10px;
}

.action-desc {
  font-size: 14px;
  color: #606266;
  margin-bottom: 20px;
  line-height: 1.6;
}

/* 主内容区域 */
.main-content {
  background: white;
  border-radius: 20px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.content-tabs :deep(.el-tabs__header) {
  margin-bottom: 20px;
}

.content-tabs :deep(.el-tabs__item) {
  font-size: 16px;
  font-weight: 500;
}

.tab-content {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .admin-dashboard {
    padding: 20px 15px;
  }
  
  .welcome-section {
    padding: 25px 20px;
  }
  
  .welcome-title {
    font-size: 24px;
  }
  
  .welcome-subtitle {
    font-size: 14px;
  }
  
  .section-title {
    font-size: 20px;
  }
  
  .action-card {
    margin-bottom: 15px;
  }
}

/* 加载状态优化 */
:deep(.el-loading-mask) {
  background-color: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(2px);
}

:deep(.el-loading-spinner) {
  top: 50%;
  transform: translateY(-50%);
}

:deep(.el-loading-spinner .el-loading-text) {
  color: #ff6f00;
  font-size: 13px;
  margin-top: 8px;
}

:deep(.el-loading-spinner .path) {
  stroke: #ff6f00;
}
</style>


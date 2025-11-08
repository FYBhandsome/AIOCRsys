<template>
  <div class="teacher-dashboard">
    <!-- 欢迎区域 -->
    <div class="welcome-section">
      <div class="welcome-content">
        <h1 class="welcome-title">👨‍🏫 欢迎，{{ userStore.userInfo.name }}老师</h1>
        <p class="welcome-subtitle">管理班级成绩，分析学生表现，一切尽在掌握</p>
      </div>
      <div class="welcome-stats">
        <el-card class="stat-card">
          <div class="stat-icon">👥</div>
          <div class="stat-info">
            <div class="stat-value">{{ classCount }}</div>
            <div class="stat-label">管理班级</div>
          </div>
        </el-card>
        <el-card class="stat-card">
          <div class="stat-icon">📝</div>
          <div class="stat-info">
            <div class="stat-value">{{ studentCount }}</div>
            <div class="stat-label">学生总数</div>
          </div>
        </el-card>
        <el-card class="stat-card">
          <div class="stat-icon">📊</div>
          <div class="stat-info">
            <div class="stat-value">{{ avgScore }}</div>
            <div class="stat-label">班级平均分</div>
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
        <el-col :xs="24" :sm="12" :md="8">
          <el-card class="action-card" @click="activeTab = 'upload'">
            <div class="action-icon">📤</div>
            <h3 class="action-title">上传成绩单</h3>
            <p class="action-desc">批量导入学生成绩信息</p>
            <el-button type="primary" size="small">立即上传</el-button>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8">
          <el-card class="action-card" @click="activeTab = 'analysis'">
            <div class="action-icon">📈</div>
            <h3 class="action-title">成绩分析</h3>
            <p class="action-desc">查看班级成绩统计和可视化</p>
            <el-button type="success" size="small">查看分析</el-button>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8">
          <el-card class="action-card" @click="activeTab = 'students'">
            <div class="action-icon">👨‍🎓</div>
            <h3 class="action-title">学生列表</h3>
            <p class="action-desc">管理学生信息和成绩记录</p>
            <el-button type="info" size="small">查看学生</el-button>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <el-tabs v-model="activeTab" class="content-tabs">
        <!-- 成绩上传 -->
        <el-tab-pane label="成绩上传" name="upload">
          <div class="tab-content">
            <h2 class="section-title">
              <el-icon><Upload /></el-icon>
              上传学生成绩
            </h2>
            <ScoreUpload />
          </div>
        </el-tab-pane>

        <!-- 成绩分析 -->
        <el-tab-pane label="成绩分析" name="analysis">
          <div class="tab-content">
            <h2 class="section-title">
              <el-icon><TrendCharts /></el-icon>
              班级成绩分析
            </h2>
            <ScoreAnalysis />
          </div>
        </el-tab-pane>

        <!-- 学生列表 -->
        <el-tab-pane label="学生列表" name="students">
          <div class="tab-content">
            <h2 class="section-title">
              <el-icon><User /></el-icon>
              学生成绩列表
            </h2>
            <StudentList />
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
import { useUserStore } from '@/store'
import { Lightning, Upload, TrendCharts, User } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import ScoreUpload from '@/views/ScoreUpload.vue'
import ScoreAnalysis from '@/views/ScoreAnalysis.vue'
import StudentList from '@/components/StudentList.vue'
import AIAssistant from '@/components/AIAssistant.vue'
import { teacherAPI } from '@/services/api'

const userStore = useUserStore()

// 统计数据
const classCount = ref(0)
const studentCount = ref(0)
const avgScore = ref(0)
const loading = ref(false)

// 当前激活的标签页
const activeTab = ref('upload')

// 班级列表
const classList = ref([])
const selectedClassId = ref('')

// 加载教师数据
const loadTeacherData = async () => {
  loading.value = true
  try {
    // 获取班级列表
    const classes = await teacherAPI.getClasses().catch(err => {
      console.warn('获取班级列表失败:', err)
      return []
    })
    
    classList.value = classes || []
    classCount.value = classList.value.length
    
    // 如果有班级，默认选择第一个
    if (classList.value.length > 0) {
      selectedClassId.value = classList.value[0].id
      
      // 获取第一个班级的学生列表
      const students = await teacherAPI.getStudents(selectedClassId.value).catch(err => {
        console.warn('获取学生列表失败:', err)
        return []
      })
      
      studentCount.value = students?.length || 0
      
      // 计算平均分（如果有成绩数据）
      if (students && students.length > 0) {
        const totalScore = students.reduce((sum, student) => sum + (student.score || 0), 0)
        avgScore.value = (totalScore / students.length).toFixed(1)
      }
    }
  } catch (error) {
    console.error('加载教师数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadTeacherData()
})
</script>

<style scoped>
.teacher-dashboard {
  padding: 30px;
  max-width: 1600px;
  margin: 0 auto;
  background: linear-gradient(135deg, #f5f7fa 0%, #e3f2fd 100%);
  min-height: 100vh;
}

/* 欢迎区域 */
.welcome-section {
  background: linear-gradient(135deg, #1e88e5 0%, #1565c0 100%);
  border-radius: 20px;
  padding: 40px;
  margin-bottom: 30px;
  color: white;
  box-shadow: 0 10px 40px rgba(30, 136, 229, 0.4);
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
  color: #1e88e5;
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
  box-shadow: 0 12px 40px rgba(30, 136, 229, 0.25);
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
  .teacher-dashboard {
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
</style>


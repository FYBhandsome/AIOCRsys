<template>
  <div class="student-dashboard">
    <!-- 欢迎区域 -->
    <div class="welcome-section">
      <div class="welcome-content">
        <h1 class="welcome-title">👋 欢迎回来，{{ userStore.userInfo.name }}</h1>
        <p class="welcome-subtitle">上传您的证明材料，让AI智能计算您的综测成绩</p>
      </div>
      <div class="welcome-stats">
        <el-card class="stat-card">
          <div class="stat-icon">📁</div>
          <div class="stat-info">
            <div class="stat-value">{{ uploadCount }}</div>
            <div class="stat-label">已上传材料</div>
          </div>
        </el-card>
        <el-card class="stat-card">
          <div class="stat-icon">📊</div>
          <div class="stat-info">
            <div class="stat-value">{{ scoreValue }}</div>
            <div class="stat-label">当前综测分</div>
          </div>
        </el-card>
        <el-card class="stat-card">
          <div class="stat-icon">🏆</div>
          <div class="stat-info">
            <div class="stat-value">{{ ranking }}</div>
            <div class="stat-label">班级排名</div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 快速操作区域 -->
    <div class="quick-actions">
      <h2 class="section-title">
        <el-icon><Lightning /></el-icon>
        快速操作
      </h2>
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="8">
          <el-card class="action-card" @click="$router.push('/upload/material')">
            <div class="action-icon">📄</div>
            <h3 class="action-title">上传证明材料</h3>
            <p class="action-desc">上传获奖证书、实践证明等材料</p>
            <el-button type="primary" size="small">立即上传</el-button>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8">
          <el-card class="action-card" @click="showMyResults">
            <div class="action-icon">📈</div>
            <h3 class="action-title">查看我的成绩</h3>
            <p class="action-desc">查看综测成绩和详细报告</p>
            <el-button type="success" size="small">查看详情</el-button>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8">
          <el-card class="action-card" @click="showHistory">
            <div class="action-icon">🕐</div>
            <h3 class="action-title">历史记录</h3>
            <p class="action-desc">查看历史上传记录和审核状态</p>
            <el-button type="info" size="small">查看记录</el-button>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 材料上传区域 -->
    <div class="upload-section">
      <h2 class="section-title">
        <el-icon><Upload /></el-icon>
        材料上传
      </h2>
      <MaterialUpload />
    </div>

    <!-- AI助手悬浮窗 -->
    <AIAssistant />
    
    <!-- 成绩详情对话框 -->
    <el-dialog
      v-model="showScoresDialog"
      title="成绩详情"
      width="70%"
      :close-on-click-modal="false"
    >
      <div v-if="scoresDetail" class="scores-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="总分">
            <el-tag type="success" size="large">{{ scoresDetail.total_score || 0 }} 分</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="班级排名">
            {{ scoresDetail.ranking || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="学业成绩">
            {{ scoresDetail.academic_score || 0 }} 分
          </el-descriptions-item>
          <el-descriptions-item label="综合素质">
            {{ scoresDetail.quality_score || 0 }} 分
          </el-descriptions-item>
          <el-descriptions-item label="奖励加分">
            {{ scoresDetail.bonus_score || 0 }} 分
          </el-descriptions-item>
          <el-descriptions-item label="惩罚扣分">
            {{ scoresDetail.penalty_score || 0 }} 分
          </el-descriptions-item>
        </el-descriptions>
        
        <div v-if="scoresDetail.details && scoresDetail.details.length > 0" style="margin-top: 20px;">
          <h4>详细项目</h4>
          <el-table :data="scoresDetail.details" border style="width: 100%">
            <el-table-column prop="category" label="类别" width="120" />
            <el-table-column prop="item" label="项目" min-width="200" />
            <el-table-column prop="score" label="分数" width="100" align="center">
              <template #default="scope">
                <el-tag :type="scope.row.score > 0 ? 'success' : 'danger'">
                  {{ scope.row.score > 0 ? '+' : '' }}{{ scope.row.score }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="date" label="日期" width="120" />
          </el-table>
        </div>
      </div>
      <div v-else style="text-align: center; padding: 40px;">
        <el-empty description="暂无成绩数据" />
      </div>
    </el-dialog>
    
    <!-- 历史记录对话框 -->
    <el-dialog
      v-model="showHistoryDialog"
      title="上传历史"
      width="80%"
      :close-on-click-modal="false"
    >
      <el-table :data="uploadHistory" border style="width: 100%">
        <el-table-column prop="filename" label="文件名" min-width="200" />
        <el-table-column label="类型" width="120" align="center">
          <template #default="scope">
            <el-tag>{{ scope.row.type || '证书' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="加分" width="100" align="center">
          <template #default="scope">
            <span v-if="scope.row.score">+{{ scope.row.score }} 分</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="upload_time" label="上传时间" width="180" />
        <el-table-column label="操作" width="150" align="center" fixed="right">
          <template #default="scope">
            <el-button type="primary" size="small" text @click="viewUploadDetail(scope.row)">
              查看
            </el-button>
            <el-button type="danger" size="small" text @click="deleteUpload(scope.row.id)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div v-if="!uploadHistory || uploadHistory.length === 0" style="text-align: center; padding: 40px;">
        <el-empty description="暂无上传记录" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Lightning, Upload, TrendCharts, Document, Delete } from '@element-plus/icons-vue'
import MaterialUpload from '@/views/MaterialUpload.vue'
import AIAssistant from '@/components/AIAssistant.vue'
import { studentAPI, certificateAPI } from '@/services/api'

const router = useRouter()
const userStore = useUserStore()

// 统计数据
const uploadCount = ref(0)
const scoreValue = ref(0)
const ranking = ref('-')
const loading = ref(false)

// 成绩摘要数据
const scoresSummary = ref(null)
const scoresDetail = ref(null)
const uploadHistory = ref([])

// 显示成绩详情对话框
const showScoresDialog = ref(false)
const showHistoryDialog = ref(false)

// 加载学生数据
const loadStudentData = async () => {
  loading.value = true
  try {
    // 并发加载多个数据
    const [summaryRes, historyRes] = await Promise.all([
      studentAPI.getScoresSummary().catch(err => {
        console.warn('获取成绩摘要失败:', err)
        return null
      }),
      studentAPI.getUploadHistory().catch(err => {
        console.warn('获取上传历史失败:', err)
        return []
      })
    ])
    
    // 更新成绩摘要
    if (summaryRes) {
      scoresSummary.value = summaryRes
      scoreValue.value = summaryRes.total_score || 0
      ranking.value = summaryRes.ranking || '-'
    }
    
    // 更新上传历史
    uploadHistory.value = historyRes || []
    uploadCount.value = uploadHistory.value.length
  } catch (error) {
    console.error('加载学生数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 查看成绩详情
const showMyResults = async () => {
  try {
    const detail = await studentAPI.getScoresDetail()
    scoresDetail.value = detail
    showScoresDialog.value = true
  } catch (error) {
    console.error('获取成绩详情失败:', error)
    ElMessage.error('获取成绩详情失败')
  }
}

// 查看历史记录
const showHistory = () => {
  showHistoryDialog.value = true
}

// 删除上传记录
const deleteUpload = async (uploadId) => {
  try {
    await ElMessageBox.confirm('确定要删除这条上传记录吗？删除后将无法恢复。', '删除确认', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
      confirmButtonClass: 'el-button--danger'
    })
    
    // 调用后端删除API
    const result = await certificateAPI.delete(uploadId, userStore.userInfo.username)
    
    if (result.success) {
      ElMessage.success('删除成功')
      // 重新加载数据以更新显示
      await loadStudentData()
    } else {
      ElMessage.error(result.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除失败，请稍后重试')
    }
  }
}

// 获取状态类型
const getStatusType = (status) => {
  const typeMap = {
    'pending': 'info',
    'processing': 'warning',
    'completed': 'success',
    'failed': 'danger'
  }
  return typeMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const textMap = {
    'pending': '待处理',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败'
  }
  return textMap[status] || '未知'
}

// 查看上传详情
const viewUploadDetail = (record) => {
  ElMessageBox.alert(
    `<div>
      <p><strong>文件名：</strong>${record.filename}</p>
      <p><strong>类型：</strong>${record.type || '证书'}</p>
      <p><strong>状态：</strong>${getStatusText(record.status)}</p>
      <p><strong>加分：</strong>${record.score ? '+' + record.score + ' 分' : '无'}</p>
      <p><strong>上传时间：</strong>${record.upload_time || '-'}</p>
      ${record.remark ? `<p><strong>备注：</strong>${record.remark}</p>` : ''}
    </div>`,
    '上传详情',
    {
      dangerouslyUseHTMLString: true,
      confirmButtonText: '关闭'
    }
  )
}

// 组件挂载时加载数据
onMounted(() => {
  loadStudentData()
})
</script>

<style scoped>
.student-dashboard {
  padding: 30px;
  max-width: 1400px;
  margin: 0 auto;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8f0fe 100%);
  min-height: 100vh;
}

/* 欢迎区域 */
.welcome-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 20px;
  padding: 40px;
  margin-bottom: 30px;
  color: white;
  box-shadow: 0 10px 40px rgba(102, 126, 234, 0.4);
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
  color: #667eea;
}

/* 快速操作区域 */
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
  box-shadow: 0 12px 40px rgba(102, 126, 234, 0.25);
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

/* 上传区域 */
.upload-section {
  background: white;
  border-radius: 20px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

/* 成绩详情样式 */
.scores-detail h4 {
  margin: 20px 0 10px 0;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .student-dashboard {
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


<template>
  <div class="vector-db-manager">
    <el-card class="manager-card">
      <template #header>
        <div class="card-header">
          <div class="title-section">
            <el-icon><DataAnalysis /></el-icon>
            <span>向量数据库管理</span>
          </div>
          <div class="action-section">
            <el-button 
              type="info" 
              size="small" 
              @click="loadStats"
              :loading="loading"
            >
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <!-- 统计信息 -->
      <div class="stats-section" v-loading="loading">
        <el-row :gutter="20">
          <el-col :xs="24" :sm="12" :md="6">
            <div class="stat-item">
              <div class="stat-icon">📚</div>
              <div class="stat-content">
                <div class="stat-value">{{ stats.total_documents || 0 }}</div>
                <div class="stat-label">总文档数</div>
              </div>
            </div>
          </el-col>
          
          <el-col :xs="24" :sm="12" :md="6">
            <div class="stat-item">
              <div class="stat-icon">✅</div>
              <div class="stat-content">
                <div class="stat-value">{{ stats.enabled_documents || 0 }}</div>
                <div class="stat-label">启用文档</div>
              </div>
            </div>
          </el-col>
          
          <el-col :xs="24" :sm="12" :md="6">
            <div class="stat-item">
              <div class="stat-icon">🔮</div>
              <div class="stat-content">
                <div class="stat-value">{{ stats.embedding_model || 'N/A' }}</div>
                <div class="stat-label">嵌入模型</div>
              </div>
            </div>
          </el-col>
          
          <el-col :xs="24" :sm="12" :md="6">
            <div class="stat-item">
              <div class="stat-icon status-icon" :class="statusClass">
                {{ statusIcon }}
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ statusText }}</div>
                <div class="stat-label">数据库状态</div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 操作面板 -->
      <el-divider />
      
      <div class="operations-section">
        <h3 class="section-title">
          <el-icon><Tools /></el-icon>
          数据库操作
        </h3>

        <el-alert
          title="操作说明"
          type="warning"
          :closable="false"
          style="margin-bottom: 20px"
        >
          <p style="margin: 5px 0;">
            <strong>重建向量库</strong>：基于当前启用的文档重新构建向量索引，不删除现有数据
          </p>
          <p style="margin: 5px 0;">
            <strong>重置向量库</strong>：清空所有向量数据，可选择立即重建
          </p>
          <p style="margin: 5px 0; color: #f56c6c;">
            ⚠️ 重置操作会删除所有向量数据，请谨慎操作！
          </p>
        </el-alert>

        <div class="operation-buttons">
          <el-card class="operation-card">
            <div class="operation-icon">🔄</div>
            <h4 class="operation-title">重建向量库</h4>
            <p class="operation-desc">
              基于启用的文档重新构建向量索引，适用于文档更新或状态变更后
            </p>
            <el-button 
              type="primary" 
              size="large" 
              @click="handleRebuild"
              :loading="rebuilding"
              style="width: 100%; margin-top: 15px;"
            >
              <el-icon><RefreshRight /></el-icon>
              重建向量库
            </el-button>
          </el-card>

          <el-card class="operation-card">
            <div class="operation-icon">🗑️</div>
            <h4 class="operation-title">重置向量库</h4>
            <p class="operation-desc">
              清空所有向量数据，可选择立即重建
            </p>
            <el-checkbox 
              v-model="rebuildAfterReset" 
              style="margin-top: 10px; display: block;"
            >
              重置后立即重建
            </el-checkbox>
            <el-button 
              type="danger" 
              size="large" 
              @click="handleReset"
              :loading="resetting"
              style="width: 100%; margin-top: 15px;"
            >
              <el-icon><Delete /></el-icon>
              重置向量库
            </el-button>
          </el-card>
        </div>
      </div>

      <!-- 详细信息 -->
      <el-divider />
      
      <div class="details-section">
        <h3 class="section-title">
          <el-icon><InfoFilled /></el-icon>
          详细信息
        </h3>
        
        <el-descriptions :column="2" border>
          <el-descriptions-item label="LLM引擎">
            {{ stats.llm_engine || 'N/A' }}
          </el-descriptions-item>
          <el-descriptions-item label="嵌入模型">
            {{ stats.embedding_model || 'N/A' }}
          </el-descriptions-item>
          <el-descriptions-item label="总文档数">
            {{ stats.total_documents || 0 }}
          </el-descriptions-item>
          <el-descriptions-item label="启用文档数">
            {{ stats.enabled_documents || 0 }}
          </el-descriptions-item>
          <el-descriptions-item label="数据库状态">
            <el-tag :type="statusTagType">{{ statusText }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="最后更新">
            {{ lastUpdateTime }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  DataAnalysis, Refresh, Tools, RefreshRight, Delete, 
  InfoFilled 
} from '@element-plus/icons-vue'
import { adminAPI } from '@/services/api'

// 状态管理
const loading = ref(false)
const rebuilding = ref(false)
const resetting = ref(false)
const rebuildAfterReset = ref(true)

// 统计数据
const stats = reactive({
  total_documents: 0,
  enabled_documents: 0,
  embedding_model: '',
  llm_engine: '',
  status: 'unknown'
})

// 最后更新时间
const lastUpdateTime = ref('--')

// 状态相关计算属性
const statusText = computed(() => {
  const statusMap = {
    'ready': '正常',
    'loading': '加载中',
    'error': '错误',
    'unknown': '未知'
  }
  return statusMap[stats.status] || '未知'
})

const statusClass = computed(() => {
  return {
    'status-ready': stats.status === 'ready',
    'status-loading': stats.status === 'loading',
    'status-error': stats.status === 'error'
  }
})

const statusIcon = computed(() => {
  const iconMap = {
    'ready': '✅',
    'loading': '⏳',
    'error': '❌',
    'unknown': '❓'
  }
  return iconMap[stats.status] || '❓'
})

const statusTagType = computed(() => {
  const typeMap = {
    'ready': 'success',
    'loading': 'warning',
    'error': 'danger',
    'unknown': 'info'
  }
  return typeMap[stats.status] || 'info'
})

// 加载统计信息
const loadStats = async () => {
  loading.value = true
  try {
    const response = await adminAPI.getVectorDBStats()
    const data = response.data || response
    
    // 更新统计数据
    Object.assign(stats, {
      total_documents: data.total_documents || 0,
      enabled_documents: data.enabled_documents || 0,
      embedding_model: data.embedding_model || 'N/A',
      llm_engine: data.llm_engine || 'N/A',
      status: data.status || 'unknown'
    })
    
    // 更新时间
    lastUpdateTime.value = new Date().toLocaleString('zh-CN')
    
  } catch (error) {
    console.error('加载向量数据库统计失败:', error)
    ElMessage.error('加载统计信息失败')
    stats.status = 'error'
  } finally {
    loading.value = false
  }
}

// 重建向量库
const handleRebuild = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要重建向量数据库吗？此操作会基于当前启用的文档重新构建索引。',
      '确认重建',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    rebuilding.value = true
    stats.status = 'loading'
    
    const response = await adminAPI.rebuildVectorDB()
    const result = response.data || response
    
    ElMessage.success({
      message: `向量数据库重建成功！处理了 ${result.document_count || 0} 个文档`,
      duration: 3000
    })
    
    // 刷新统计信息
    await loadStats()
    
  } catch (error) {
    if (error === 'cancel') {
      ElMessage.info('已取消重建')
    } else {
      console.error('重建向量数据库失败:', error)
      ElMessage.error('重建向量数据库失败：' + (error.response?.data?.detail || error.message))
      stats.status = 'error'
    }
  } finally {
    rebuilding.value = false
  }
}

// 重置向量库
const handleReset = async () => {
  try {
    await ElMessageBox.confirm(
      '⚠️ 警告：此操作会清空所有向量数据，不可恢复！\n\n' +
      (rebuildAfterReset.value ? '重置后会自动重建向量库。' : '重置后需要手动重建向量库。') +
      '\n\n确定要继续吗？',
      '危险操作',
      {
        confirmButtonText: '确定重置',
        cancelButtonText: '取消',
        type: 'error',
        confirmButtonClass: 'el-button--danger'
      }
    )
    
    resetting.value = true
    stats.status = 'loading'
    
    const response = await adminAPI.resetVectorDB(true, rebuildAfterReset.value)
    const result = response.data || response
    
    if (result.rebuild) {
      ElMessage.success({
        message: `向量数据库已重置并重建！处理了 ${result.document_count || 0} 个文档`,
        duration: 3000
      })
    } else {
      ElMessage.success('向量数据库已重置')
    }
    
    // 刷新统计信息
    await loadStats()
    
  } catch (error) {
    if (error === 'cancel') {
      ElMessage.info('已取消重置')
    } else {
      console.error('重置向量数据库失败:', error)
      ElMessage.error('重置向量数据库失败：' + (error.response?.data?.detail || error.message))
      stats.status = 'error'
    }
  } finally {
    resetting.value = false
  }
}

// 组件挂载时加载统计信息
onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.vector-db-manager {
  padding: 20px;
}

.manager-card {
  border-radius: 12px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.title-section {
  display: flex;
  align-items: center;
}

.title-section .el-icon {
  margin-right: 8px;
  font-size: 20px;
  color: #409eff;
}

.action-section {
  display: flex;
  gap: 10px;
}

/* 统计信息 */
.stats-section {
  padding: 20px 0;
}

.stat-item {
  display: flex;
  align-items: center;
  padding: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.stat-item:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  font-size: 48px;
  margin-right: 15px;
}

.status-icon.status-ready {
  animation: pulse 2s ease-in-out infinite;
}

.status-icon.status-loading {
  animation: rotate 2s linear infinite;
}

.status-icon.status-error {
  animation: shake 0.5s ease-in-out;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-10px); }
  75% { transform: translateX(10px); }
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #2c3e50;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}

/* 区块标题 */
.section-title {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 15px;
  color: #2c3e50;
}

.section-title .el-icon {
  margin-right: 8px;
  color: #409eff;
}

/* 操作面板 */
.operations-section {
  padding: 20px 0;
}

.operation-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.operation-card {
  text-align: center;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.operation-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
}

.operation-icon {
  font-size: 56px;
  margin-bottom: 15px;
}

.operation-title {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 10px;
}

.operation-desc {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  min-height: 60px;
}

/* 详细信息 */
.details-section {
  padding: 20px 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .vector-db-manager {
    padding: 10px;
  }
  
  .card-header {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
  
  .action-section {
    width: 100%;
  }
  
  .stat-item {
    margin-bottom: 10px;
  }
  
  .operation-buttons {
    grid-template-columns: 1fr;
  }
}
</style>


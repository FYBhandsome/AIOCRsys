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
              <div class="stat-icon">💾</div>
              <div class="stat-content">
                <div class="stat-value">{{ stats.db_size_formatted || '0 B' }}</div>
                <div class="stat-label">数据库大小</div>
              </div>
            </div>
          </el-col>
          
          <el-col :xs="24" :sm="12" :md="6">
            <div class="stat-item">
              <div class="stat-icon">📁</div>
              <div class="stat-content">
                <div class="stat-value">{{ stats.collections?.length || 0 }}</div>
                <div class="stat-label">集合数量</div>
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
            <strong>重新索引</strong>：清空现有向量数据，重新加载规则文档并生成向量索引
          </p>
          <p style="margin: 5px 0;">
            <strong>清空数据</strong>：删除所有向量数据，但保留数据库结构
          </p>
          <p style="margin: 5px 0;">
            <strong>重置数据库</strong>：完全删除并重建数据库目录，可选择备份
          </p>
          <p style="margin: 5px 0; color: #f56c6c;">
            ⚠️ 清空和重置操作会删除所有向量数据，请谨慎操作！
          </p>
        </el-alert>

        <div class="operation-buttons">
          <el-card class="operation-card">
            <div class="operation-icon">🔄</div>
            <h4 class="operation-title">重新索引</h4>
            <p class="operation-desc">
              重新加载规则文档并生成向量索引，适用于文档更新后
            </p>
            <el-button 
              type="primary" 
              size="large" 
              @click="handleReindex"
              :loading="reindexing"
              style="width: 100%; margin-top: 15px;"
            >
              <el-icon><RefreshRight /></el-icon>
              重新索引
            </el-button>
          </el-card>

          <el-card class="operation-card">
            <div class="operation-icon">🗑️</div>
            <h4 class="operation-title">清空数据</h4>
            <p class="operation-desc">
              删除所有向量数据，保留数据库结构
            </p>
            <el-button 
              type="warning" 
              size="large" 
              @click="handleClear"
              :loading="clearing"
              style="width: 100%; margin-top: 15px;"
            >
              <el-icon><Delete /></el-icon>
              清空数据
            </el-button>
          </el-card>

          <el-card class="operation-card">
            <div class="operation-icon">⚠️</div>
            <h4 class="operation-title">重置数据库</h4>
            <p class="operation-desc">
              完全删除并重建数据库，可选择备份现有数据
            </p>
            <el-checkbox 
              v-model="backupBeforeReset" 
              style="margin-top: 10px; display: block;"
            >
              重置前备份
            </el-checkbox>
            <el-button 
              type="danger" 
              size="large" 
              @click="handleReset"
              :loading="resetting"
              style="width: 100%; margin-top: 15px;"
            >
              <el-icon><Warning /></el-icon>
              重置数据库
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
          <el-descriptions-item label="数据库路径">
            {{ stats.db_path || 'N/A' }}
          </el-descriptions-item>
          <el-descriptions-item label="数据库状态">
            <el-tag :type="stats.exists ? 'success' : 'danger'">
              {{ stats.exists ? '存在' : '不存在' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="总文档数">
            {{ stats.total_documents || 0 }}
          </el-descriptions-item>
          <el-descriptions-item label="数据库大小">
            {{ stats.db_size_formatted || '0 B' }}
          </el-descriptions-item>
          <el-descriptions-item label="最后修改">
            {{ stats.last_modified || '--' }}
          </el-descriptions-item>
          <el-descriptions-item label="集合列表">
            <el-tag v-for="coll in stats.collections" :key="coll.id" style="margin-right: 5px;">
              {{ coll.name }}
            </el-tag>
            <span v-if="!stats.collections?.length">无</span>
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 操作日志 -->
      <el-divider />
      
      <div class="log-section">
        <h3 class="section-title">
          <el-icon><Document /></el-icon>
          操作日志
        </h3>
        
        <div class="log-container">
          <div 
            v-for="(log, index) in operationLogs" 
            :key="index" 
            class="log-item"
            :class="log.type"
          >
            <span class="log-time">{{ log.time }}</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
          <div v-if="operationLogs.length === 0" class="log-empty">
            暂无操作日志
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  DataAnalysis, Refresh, Tools, RefreshRight, Delete, 
  InfoFilled, Document, Warning 
} from '@element-plus/icons-vue'
import { adminAPI } from '@/services/api'

const loading = ref(false)
const reindexing = ref(false)
const clearing = ref(false)
const resetting = ref(false)
const backupBeforeReset = ref(true)

const stats = reactive({
  db_path: '',
  exists: false,
  total_documents: 0,
  collections: [],
  db_size_bytes: 0,
  db_size_formatted: '0 B',
  last_modified: null
})

const operationLogs = ref([])

const addLog = (message, type = 'info') => {
  operationLogs.value.unshift({
    time: new Date().toLocaleTimeString('zh-CN'),
    message,
    type
  })
  if (operationLogs.value.length > 50) {
    operationLogs.value.pop()
  }
}

const statusText = computed(() => {
  if (!stats.exists) return '不存在'
  return '正常'
})

const statusClass = computed(() => {
  return {
    'status-ready': stats.exists,
    'status-error': !stats.exists
  }
})

const statusIcon = computed(() => {
  return stats.exists ? '✅' : '❌'
})

const loadStats = async () => {
  loading.value = true
  try {
    const response = await adminAPI.getVectorDBStats()
    const data = response.data || response
    
    Object.assign(stats, {
      db_path: data.db_path || '',
      exists: data.exists || false,
      total_documents: data.total_documents || 0,
      collections: data.collections || [],
      db_size_bytes: data.db_size_bytes || 0,
      db_size_formatted: data.db_size_formatted || '0 B',
      last_modified: data.last_modified || null
    })
    
    addLog('统计信息已刷新', 'success')
    
  } catch (error) {
    console.error('加载向量数据库统计失败:', error)
    ElMessage.error('加载统计信息失败: ' + (error.response?.data?.detail || error.message))
    addLog('加载统计信息失败: ' + error.message, 'error')
  } finally {
    loading.value = false
  }
}

const handleReindex = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要重新索引向量数据库吗？此操作会清空现有数据并重新加载规则文档。',
      '确认重新索引',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    reindexing.value = true
    addLog('开始重新索引...', 'info')
    
    const response = await adminAPI.reindexVectorDB()
    const result = response.data || response
    
    ElMessage.success({
      message: `重新索引成功！共${result.total_documents || 0}个文档`,
      duration: 3000
    })
    
    addLog(`重新索引完成: ${result.total_documents || 0}个文档`, 'success')
    await loadStats()
    
  } catch (error) {
    if (error === 'cancel') {
      addLog('已取消重新索引', 'info')
    } else {
      console.error('重新索引失败:', error)
      ElMessage.error('重新索引失败: ' + (error.response?.data?.detail || error.message))
      addLog('重新索引失败: ' + error.message, 'error')
    }
  } finally {
    reindexing.value = false
  }
}

const handleClear = async () => {
  try {
    await ElMessageBox.confirm(
      '⚠️ 警告：此操作会清空所有向量数据，不可恢复！\n\n确定要继续吗？',
      '危险操作',
      {
        confirmButtonText: '确定清空',
        cancelButtonText: '取消',
        type: 'error'
      }
    )
    
    clearing.value = true
    addLog('开始清空向量数据...', 'info')
    
    const response = await adminAPI.clearVectorDB()
    const result = response.data || response
    
    ElMessage.success({
      message: `清空成功！清除${result.cleared_documents || 0}个文档，释放${result.cleared_size_bytes ? formatSize(result.cleared_size_bytes) : '0 B'}`,
      duration: 3000
    })
    
    addLog(`清空完成: ${result.message}`, 'success')
    await loadStats()
    
  } catch (error) {
    if (error === 'cancel') {
      addLog('已取消清空操作', 'info')
    } else {
      console.error('清空失败:', error)
      ElMessage.error('清空失败: ' + (error.response?.data?.detail || error.message))
      addLog('清空失败: ' + error.message, 'error')
    }
  } finally {
    clearing.value = false
  }
}

const handleReset = async () => {
  try {
    const backupMsg = backupBeforeReset.value ? '\n\n将创建备份后再重置。' : '\n\n⚠️ 未选择备份，数据将无法恢复！'
    
    await ElMessageBox.confirm(
      '⚠️ 严重警告：此操作会完全删除向量数据库目录！' + backupMsg + '\n\n确定要继续吗？',
      '危险操作',
      {
        confirmButtonText: '确定重置',
        cancelButtonText: '取消',
        type: 'error'
      }
    )
    
    resetting.value = true
    addLog('开始重置向量数据库...', 'info')
    
    const response = await adminAPI.resetVectorDB(backupBeforeReset.value)
    const result = response.data || response
    
    let message = '向量数据库已重置'
    if (result.backup_path) {
      message += `，备份已保存到: ${result.backup_path}`
    }
    
    ElMessage.success({
      message,
      duration: 5000
    })
    
    addLog(`重置完成: ${result.message}`, 'success')
    await loadStats()
    
  } catch (error) {
    if (error === 'cancel') {
      addLog('已取消重置操作', 'info')
    } else {
      console.error('重置失败:', error)
      ElMessage.error('重置失败: ' + (error.response?.data?.detail || error.message))
      addLog('重置失败: ' + error.message, 'error')
    }
  } finally {
    resetting.value = false
  }
}

const formatSize = (bytes) => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
}

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

.status-icon.status-error {
  animation: shake 0.5s ease-in-out;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
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

.operations-section {
  padding: 20px 0;
}

.operation-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
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

.details-section {
  padding: 20px 0;
}

.log-section {
  padding: 20px 0;
}

.log-container {
  max-height: 300px;
  overflow-y: auto;
  background: #f5f7fa;
  border-radius: 8px;
  padding: 15px;
}

.log-item {
  padding: 8px 12px;
  margin-bottom: 8px;
  border-radius: 4px;
  font-size: 13px;
  display: flex;
  gap: 10px;
}

.log-item.success {
  background: #f0f9eb;
  color: #67c23a;
}

.log-item.error {
  background: #fef0f0;
  color: #f56c6c;
}

.log-item.info {
  background: #ecf5ff;
  color: #409eff;
}

.log-time {
  color: #909399;
  font-family: monospace;
}

.log-message {
  flex: 1;
}

.log-empty {
  text-align: center;
  color: #909399;
  padding: 20px;
}

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

<template>
  <div class="system-monitor">
    <h2>系统状态监控</h2>
    
    <el-row :gutter="20">
      <!-- RAG系统状态 -->
      <el-col :span="12">
        <el-card class="status-card">
          <template #header>
            <div class="card-header">
              <h3>RAG系统状态</h3>
              <el-button size="small" @click="refreshRAGStatus">刷新</el-button>
            </div>
          </template>
          
          <el-descriptions v-if="ragStats" :column="1" border>
            <el-descriptions-item label="状态">
              <el-tag :type="ragHealth?.status === 'healthy' ? 'success' : 'danger'">
                {{ ragHealth?.status || '未知' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="文档数量">{{ ragStats.document_count || 0 }}</el-descriptions-item>
            <el-descriptions-item label="向量数量">{{ ragStats.vector_count || 0 }}</el-descriptions-item>
            <el-descriptions-item label="索引大小">{{ formatSize(ragStats.index_size) }}</el-descriptions-item>
          </el-descriptions>
          
          <div v-if="ragHealth?.message" class="health-message">
            <el-alert :title="ragHealth.message" :type="ragHealth.status === 'healthy' ? 'success' : 'error'" :closable="false" />
          </div>
        </el-card>
      </el-col>
      
      <!-- 向量数据库状态 -->
      <el-col :span="12">
        <el-card class="status-card">
          <template #header>
            <div class="card-header">
              <h3>向量数据库状态</h3>
              <el-button size="small" @click="refreshVectorDBStatus">刷新</el-button>
            </div>
          </template>
          
          <el-descriptions v-if="vectorDBStats" :column="1" border>
            <el-descriptions-item label="集合数量">{{ vectorDBStats.collection_count || 0 }}</el-descriptions-item>
            <el-descriptions-item label="总向量数">{{ vectorDBStats.total_vectors || 0 }}</el-descriptions-item>
            <el-descriptions-item label="存储大小">{{ formatSize(vectorDBStats.storage_size) }}</el-descriptions-item>
            <el-descriptions-item label="内存使用">{{ formatSize(vectorDBStats.memory_usage) }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { adminAPI } from '@/services/api'

export default {
  name: 'SystemMonitor',
  setup() {
    const ragStats = ref(null)
    const ragHealth = ref(null)
    const vectorDBStats = ref(null)
    
    // 获取RAG系统统计
    const getRAGStats = async () => {
      try {
        const response = await adminAPI.getRAGStats()
        ragStats.value = response
      } catch (error) {
        ElMessage.error('获取RAG统计信息失败: ' + error.message)
      }
    }
    
    // 获取RAG系统健康状态
    const getRAGHealth = async () => {
      try {
        const response = await adminAPI.ragHealthCheck()
        ragHealth.value = response
      } catch (error) {
        ElMessage.error('获取RAG健康状态失败: ' + error.message)
      }
    }
    
    // 获取向量数据库统计
    const getVectorDBStats = async () => {
      try {
        const response = await adminAPI.getVectorDBStats()
        vectorDBStats.value = response
      } catch (error) {
        ElMessage.error('获取向量数据库统计失败: ' + error.message)
      }
    }
    
    // 刷新RAG状态
    const refreshRAGStatus = async () => {
      await Promise.all([getRAGStats(), getRAGHealth()])
    }
    
    // 刷新向量数据库状态
    const refreshVectorDBStatus = async () => {
      await getVectorDBStats()
    }
    
    // 格式化大小
    const formatSize = (bytes) => {
      if (!bytes) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }
    
    onMounted(() => {
      refreshRAGStatus()
      refreshVectorDBStatus()
    })
    
    return {
      ragStats,
      ragHealth,
      vectorDBStats,
      refreshRAGStatus,
      refreshVectorDBStatus,
      formatSize
    }
  }
}
</script>

<style scoped>
.system-monitor {
  padding: 20px;
}

.status-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
}

.health-message {
  margin-top: 15px;
}
</style>
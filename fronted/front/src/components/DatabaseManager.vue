<template>
  <div class="database-manager">
    <div class="page-header">
      <h1>数据库管理</h1>
      <p>查看和管理系统数据</p>
    </div>
    <div class="database-content">
        <!-- 统计信息 -->
        <el-row :gutter="20" class="stats-row">
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-icon" style="background: #409eff">
                <el-icon :size="30"><DataBoard /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ stats.total_records }}</div>
                <div class="stat-label">总记录数</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6" v-for="(info, tableName) in stats.tables" :key="tableName">
            <el-card class="stat-card">
              <div class="stat-icon" style="background: #67c23a">
                <el-icon :size="30"><Document /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ info.count }}</div>
                <div class="stat-label">{{ info.description }}</div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 表格列表 -->
        <el-card class="tables-card">
          <template #header>
            <div class="card-header-content">
              <span>数据表列表</span>
              <el-button
                type="danger"
                :icon="Delete"
                @click="handleClearAll"
                :loading="clearingAll"
              >
                清空所有数据
              </el-button>
            </div>
          </template>

          <el-table :data="tables" stripe style="width: 100%">
            <el-table-column prop="name" label="表名" width="200" />
            <el-table-column prop="description" label="描述" />
            <el-table-column prop="count" label="记录数" width="120" align="center">
              <template #default="{ row }">
                <el-tag>{{ row.count }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="350" align="center">
              <template #default="{ row }">
                <el-button
                  size="small"
                  type="primary"
                  :icon="View"
                  @click="viewTableData(row.name)"
                >
                  查看数据
                </el-button>
                <el-button
                  size="small"
                  type="warning"
                  :icon="Refresh"
                  @click="refreshTable(row.name)"
                  :loading="refreshingTables[row.name]"
                >
                  刷新
                </el-button>
                <el-button
                  size="small"
                  type="danger"
                  :icon="Delete"
                  @click="handleClearTable(row.name)"
                  :disabled="row.count === 0"
                >
                  清空
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <!-- 数据查看对话框 -->
        <el-dialog
          v-model="dataDialogVisible"
          :title="`${currentTable} - 数据详情`"
          width="90%"
          top="5vh"
        >
          <div class="data-dialog-content">
            <el-table :data="tableData" stripe max-height="500" border>
              <el-table-column
                v-for="column in dataColumns"
                :key="column"
                :prop="column"
                :label="column"
                :width="getColumnWidth(column)"
                show-overflow-tooltip
              />
              <el-table-column label="操作" width="100" fixed="right">
                <template #default="{ row }">
                  <el-button
                    size="small"
                    type="danger"
                    :icon="Delete"
                    @click="deleteRecord(row.id)"
                  >
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <el-pagination
              v-if="pagination.total > 0"
              style="margin-top: 20px"
              background
              layout="total, sizes, prev, pager, next"
              :total="pagination.total"
              :page-size="pagination.limit"
              :current-page="pagination.page"
              :page-sizes="[10, 50, 100, 200]"
              @size-change="handleSizeChange"
              @current-change="handlePageChange"
            />
          </div>

          <template #footer>
            <el-button @click="dataDialogVisible = false">关闭</el-button>
            <el-button type="primary" @click="refreshTableData">刷新数据</el-button>
          </template>
        </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, View, Refresh, DataBoard, Document } from '@element-plus/icons-vue'
import api from '../services/api'

const tables = ref([])
const stats = reactive({
  tables: {},
  total_records: 0
})

const dataDialogVisible = ref(false)
const currentTable = ref('')
const tableData = ref([])
const dataColumns = ref([])

const pagination = reactive({
  page: 1,
  limit: 50,
  total: 0
})

const clearingAll = ref(false)
const refreshingTables = reactive({})

// 加载数据表列表
const loadTables = async () => {
  try {
    const response = await api.get('/v1/admin/database/tables')
    tables.value = response.data
  } catch (error) {
    console.error('加载表列表失败:', error)
    ElMessage.error('加载表列表失败')
  }
}

// 加载统计信息
const loadStats = async () => {
  try {
    const response = await api.get('/v1/admin/database/stats')
    stats.tables = response.data.tables
    stats.total_records = response.data.total_records
  } catch (error) {
    console.error('加载统计信息失败:', error)
  }
}

// 查看表数据
const viewTableData = async (tableName) => {
  currentTable.value = tableName
  pagination.page = 1
  dataDialogVisible.value = true
  await loadTableData()
}

// 加载表数据
const loadTableData = async () => {
  try {
    const skip = (pagination.page - 1) * pagination.limit
    const response = await api.get(`/v1/admin/database/tables/${currentTable.value}/data`, {
      params: {
        skip,
        limit: pagination.limit
      }
    })

    tableData.value = response.data.data
    pagination.total = response.data.total

    // 提取列名
    if (tableData.value.length > 0) {
      dataColumns.value = Object.keys(tableData.value[0])
    }
  } catch (error) {
    console.error('加载表数据失败:', error)
    ElMessage.error('加载表数据失败')
  }
}

// 刷新表数据
const refreshTableData = async () => {
  await loadTableData()
  ElMessage.success('数据已刷新')
}

// 刷新单个表
const refreshTable = async (tableName) => {
  refreshingTables[tableName] = true
  try {
    await loadTables()
    await loadStats()
    ElMessage.success(`表 ${tableName} 已刷新`)
  } finally {
    refreshingTables[tableName] = false
  }
}

// 删除单条记录
const deleteRecord = async (recordId) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除记录 ID=${recordId} 吗？此操作无法撤销！`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await api.delete(`/v1/admin/database/tables/${currentTable.value}/records/${recordId}`)
    ElMessage.success('删除成功')
    await loadTableData()
    await loadTables()
    await loadStats()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除记录失败:', error)
      ElMessage.error('删除记录失败')
    }
  }
}

// 清空表
const handleClearTable = async (tableName) => {
  try {
    await ElMessageBox.prompt(
      `⚠️ 危险操作！\n\n确定要清空表 "${tableName}" 吗？\n所有数据将被永久删除！\n\n请在下方输入表名以确认：`,
      '确认清空表',
      {
        confirmButtonText: '确定清空',
        cancelButtonText: '取消',
        inputPlaceholder: `请输入表名: ${tableName}`,
        inputPattern: new RegExp(`^${tableName}$`),
        inputErrorMessage: '输入的表名不正确',
        type: 'error'
      }
    )

    await api.delete(`/v1/admin/database/tables/${tableName}/clear`, {
      params: { confirm: tableName }
    })

    ElMessage.success(`表 ${tableName} 已清空`)
    await loadTables()
    await loadStats()
    
    // 如果当前正在查看这个表的数据，关闭对话框
    if (currentTable.value === tableName) {
      dataDialogVisible.value = false
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清空表失败:', error)
      const errorMsg = error.response?.data?.detail || '清空表失败'
      ElMessage.error(errorMsg)
    }
  }
}

// 清空所有数据
const handleClearAll = async () => {
  try {
    await ElMessageBox.prompt(
      `⚠️⚠️⚠️ 极度危险操作！\n\n这将清空所有数据表中的所有数据！\n此操作无法撤销！\n\n请在下方输入 "DELETE_ALL_DATA" 以确认：`,
      '确认清空所有数据',
      {
        confirmButtonText: '确定清空所有数据',
        cancelButtonText: '取消',
        inputPlaceholder: '请输入: DELETE_ALL_DATA',
        inputPattern: /^DELETE_ALL_DATA$/,
        inputErrorMessage: '输入错误，请输入: DELETE_ALL_DATA',
        type: 'error'
      }
    )

    clearingAll.value = true
    await api.delete('/v1/admin/database/clear-all', {
      params: { confirm: 'DELETE_ALL_DATA' }
    })

    ElMessage.success('所有数据已清空')
    await loadTables()
    await loadStats()
    dataDialogVisible.value = false
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      console.error('清空所有数据失败:', error)
      const errorMsg = error.response?.data?.detail || error.message || '清空所有数据失败'
      ElMessage.error(errorMsg)
    }
  } finally {
    clearingAll.value = false
  }
}

// 分页处理
const handleSizeChange = (size) => {
  pagination.limit = size
  pagination.page = 1
  loadTableData()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadTableData()
}

// 获取列宽度
const getColumnWidth = (column) => {
  if (column === 'id') return 80
  if (column.includes('_at')) return 180
  if (column.includes('email')) return 200
  return 150
}

onMounted(() => {
  loadTables()
  loadStats()
})
</script>

<style scoped>
.database-manager {
  padding: 20px;
}

.page-header {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  margin-bottom: 20px;
  text-align: center;
}

.page-header h1 {
  font-size: 28px;
  color: #2c3e50;
  margin: 0 0 10px 0;
  font-weight: 600;
}

.page-header p {
  color: #606266;
  margin: 0;
  font-size: 16px;
}

.database-content {
  max-width: 1400px;
  margin: 0 auto;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 15px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin-right: 15px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.tables-card {
  margin-top: 20px;
}

.card-header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.data-dialog-content {
  padding: 0;
}

:deep(.el-card__body) {
  padding: 20px;
}
</style>


<template>
  <div class="rule-list">
    <div class="filter-bar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索规则名称"
        prefix-icon="Search"
        style="width: 300px; margin-right: 10px"
        clearable
        @clear="fetchRules"
        @keyup.enter="fetchRules"
      />
      <el-select v-model="filterStatus" placeholder="状态筛选" clearable style="width: 150px; margin-right: 10px">
        <el-option label="启用中" value="active" />
        <el-option label="已停用" value="inactive" />
        <el-option label="草稿" value="draft" />
      </el-select>
      <el-button type="primary" @click="fetchRules" :loading="loading">
        <el-icon><Search /></el-icon>
        查询
      </el-button>
      <el-button type="success" @click="createNewRule">
        <el-icon><Plus /></el-icon>
        新建规则
      </el-button>
    </div>

    <el-table 
      :data="filteredRules" 
      stripe 
      style="width: 100%; margin-top: 20px"
      v-loading="loading"
    >
      <el-table-column prop="id" label="规则ID" width="100" />
      <el-table-column prop="name" label="规则名称" min-width="200" />
      <el-table-column prop="academicYear" label="适用学年" width="150" />
      <el-table-column prop="college" label="学院名称" width="180" />
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="createTime" label="创建时间" width="180" />
      <el-table-column label="操作" width="250" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="viewRule(row)">
            查看
          </el-button>
          <el-button 
            :type="row.status === 'active' ? 'warning' : 'success'" 
            size="small" 
            @click="toggleRuleStatus(row)"
            :loading="row.updating"
          >
            {{ row.status === 'active' ? '停用' : '启用' }}
          </el-button>
          <el-button type="danger" size="small" @click="deleteRule(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="pagination.currentPage"
        v-model:page-size="pagination.pageSize"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        :total="pagination.total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <el-dialog
      v-model="showRuleDetail"
      :title="currentRule?.name || '规则详情'"
      width="60%"
    >
      <el-descriptions :column="2" border v-if="currentRule">
        <el-descriptions-item label="规则ID">{{ currentRule.id }}</el-descriptions-item>
        <el-descriptions-item label="规则名称">{{ currentRule.name }}</el-descriptions-item>
        <el-descriptions-item label="适用学年">{{ currentRule.academicYear }}</el-descriptions-item>
        <el-descriptions-item label="学院">{{ currentRule.college }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentRule.status)">
            {{ getStatusText(currentRule.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ currentRule.createTime }}</el-descriptions-item>
      </el-descriptions>
      
      <div v-if="currentRule?.content" class="rule-content">
        <h4>规则内容</h4>
        <div class="content-box">{{ currentRule.content }}</div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { adminAPI } from '@/services/api'

const searchQuery = ref('')
const filterStatus = ref('')
const loading = ref(false)
const rules = ref([])
const showRuleDetail = ref(false)
const currentRule = ref(null)

const pagination = reactive({
  currentPage: 1,
  pageSize: 20,
  total: 0
})

const filteredRules = computed(() => {
  let result = rules.value
  if (searchQuery.value) {
    result = result.filter(r => r.name.includes(searchQuery.value))
  }
  if (filterStatus.value) {
    result = result.filter(r => r.status === filterStatus.value)
  }
  return result
})

const getStatusType = (status) => {
  const types = {
    active: 'success',
    inactive: 'info',
    draft: 'warning'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    active: '启用中',
    inactive: '已停用',
    draft: '草稿'
  }
  return texts[status] || '未知'
}

const fetchRules = async () => {
  loading.value = true
  try {
    const response = await adminAPI.getRules({
      page: pagination.currentPage,
      page_size: pagination.pageSize,
      search: searchQuery.value,
      status: filterStatus.value
    })
    
    const rulesData = response.data?.documents || response.documents || response.rules || []
    const total = response.data?.total || response.total || rulesData.length
    
    if (rulesData && Array.isArray(rulesData)) {
      rules.value = rulesData.map(rule => ({
        id: rule.id || rule.doc_id || rule.document_id,
        name: rule.name || rule.filename || rule.title,
        academicYear: rule.academic_year || rule.academicYear || '',
        college: rule.college || rule.metadata?.college || '',
        status: rule.enabled === false ? 'inactive' : 'active',
        createTime: rule.create_time || rule.created_at || rule.uploaded_at || rule.createTime,
        content: rule.content || rule.description || ''
      }))
      pagination.total = total
    }
  } catch (error) {
    console.error('获取规则列表失败:', error)
    ElMessage.error('获取规则列表失败')
  } finally {
    loading.value = false
  }
}

const createNewRule = () => {
  ElMessage.info('跳转到规则创建页面...')
}

const viewRule = (row) => {
  currentRule.value = row
  showRuleDetail.value = true
}

const toggleRuleStatus = async (row) => {
  const action = row.status === 'active' ? '停用' : '启用'
  const newStatus = row.status === 'active' ? 'inactive' : 'active'
  
  try {
    await ElMessageBox.confirm(
      `确定要${action}规则"${row.name}"吗？`,
      `${action}确认`,
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    row.updating = true
    
    await adminAPI.updateRule(row.id, { status: newStatus })
    
    row.status = newStatus
    ElMessage.success(`${action}成功`)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('更新规则状态失败:', error)
      ElMessage.error(`${action}失败`)
    }
  } finally {
    row.updating = false
  }
}

const deleteRule = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除规则"${row.name}"吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await adminAPI.deleteRule(row.id)
    
    const index = rules.value.findIndex(r => r.id === row.id)
    if (index > -1) {
      rules.value.splice(index, 1)
    }
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除规则失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const handleSizeChange = (val) => {
  pagination.pageSize = val
  fetchRules()
}

const handleCurrentChange = (val) => {
  pagination.currentPage = val
  fetchRules()
}

onMounted(() => {
  fetchRules()
})
</script>

<style scoped>
.rule-list {
  padding: 20px;
}

.filter-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.el-table {
  border-radius: 8px;
  overflow: hidden;
}

.pagination-container {
  margin-top: 20px;
  text-align: right;
}

.rule-content {
  margin-top: 20px;
}

.rule-content h4 {
  margin-bottom: 10px;
  color: #303133;
}

.content-box {
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
  white-space: pre-wrap;
  line-height: 1.6;
}
</style>

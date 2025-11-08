<template>
  <div class="rule-list">
    <!-- 搜索栏 -->
    <div class="filter-bar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索规则名称"
        prefix-icon="Search"
        style="width: 300px; margin-right: 10px"
        clearable
      />
      <el-button type="primary" @click="createNewRule">
        <el-icon><Plus /></el-icon>
        新建规则
      </el-button>
    </div>

    <!-- 规则列表 -->
    <el-table :data="filteredRules" stripe style="width: 100%; margin-top: 20px">
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
          >
            {{ row.status === 'active' ? '停用' : '启用' }}
          </el-button>
          <el-button type="danger" size="small" @click="deleteRule(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const searchQuery = ref('')

// 模拟规则数据
const rules = ref([
  { id: 'R001', name: '2023-2024学年综测评分规则', academicYear: '2023-2024', college: '计算机学院', status: 'active', createTime: '2023-09-01 10:00' },
  { id: 'R002', name: '2024-2025学年综测评分规则', academicYear: '2024-2025', college: '软件学院', status: 'active', createTime: '2024-09-01 10:00' },
  { id: 'R003', name: '竞赛加分细则', academicYear: '2023-2024', college: '计算机学院', status: 'active', createTime: '2023-10-15 14:30' },
  { id: 'R004', name: '社会实践评分规则', academicYear: '2023-2024', college: '信息学院', status: 'inactive', createTime: '2023-08-20 09:00' },
  { id: 'R005', name: '科研创新加分规则', academicYear: '2024-2025', college: '人工智能学院', status: 'draft', createTime: '2024-08-01 16:00' },
])

// 过滤后的规则列表
const filteredRules = computed(() => {
  if (!searchQuery.value) return rules.value
  return rules.value.filter(r => r.name.includes(searchQuery.value))
})

// 获取状态类型
const getStatusType = (status) => {
  const types = {
    active: 'success',
    inactive: 'info',
    draft: 'warning'
  }
  return types[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const texts = {
    active: '启用中',
    inactive: '已停用',
    draft: '草稿'
  }
  return texts[status] || '未知'
}

// 新建规则
const createNewRule = () => {
  ElMessage.info('跳转到规则创建页面...')
}

// 查看规则
const viewRule = (row) => {
  ElMessage.info(`查看规则: ${row.name}`)
}

// 切换规则状态（启用/停用）
const toggleRuleStatus = (row) => {
  const action = row.status === 'active' ? '停用' : '启用'
  const newStatus = row.status === 'active' ? 'inactive' : 'active'
  
  ElMessageBox.confirm(
    `确定要${action}规则"${row.name}"吗？`,
    `${action}确认`,
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
    // 更新规则状态
    row.status = newStatus
    ElMessage.success(`${action}成功`)
  }).catch(() => {
    ElMessage.info(`已取消${action}`)
  })
}

// 删除规则
const deleteRule = (row) => {
  ElMessageBox.confirm(
    `确定要删除规则"${row.name}"吗？此操作不可恢复。`,
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
    // 从列表中删除
    const index = rules.value.findIndex(r => r.id === row.id)
    if (index > -1) {
      rules.value.splice(index, 1)
    }
    ElMessage.success('删除成功')
  }).catch(() => {
    ElMessage.info('已取消删除')
  })
}
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
</style>


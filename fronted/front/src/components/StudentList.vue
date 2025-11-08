<template>
  <div class="student-list">
    <!-- 搜索和筛选 -->
    <div class="filter-bar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索学生姓名或学号"
        prefix-icon="Search"
        style="width: 300px; margin-right: 10px"
        clearable
      />
      <el-select v-model="selectedClass" placeholder="选择班级" style="width: 200px; margin-right: 10px" clearable>
        <el-option label="全部班级" value="" />
        <el-option label="计算机2021-1班" value="cs2021-1" />
        <el-option label="计算机2021-2班" value="cs2021-2" />
        <el-option label="软件2021-1班" value="se2021-1" />
      </el-select>
      <el-button type="primary" @click="exportData">
        <el-icon><Download /></el-icon>
        导出数据
      </el-button>
    </div>

    <!-- 学生表格 -->
    <el-table
      :data="filteredStudents"
      stripe
      style="width: 100%; margin-top: 20px"
      :default-sort="{ prop: 'score', order: 'descending' }"
      @row-click="handleRowClick"
    >
      <el-table-column type="index" label="排名" width="80" align="center" />
      <el-table-column prop="studentId" label="学号" width="120" />
      <el-table-column prop="name" label="姓名" width="120" />
      <el-table-column prop="class" label="班级" width="150" />
      <el-table-column prop="score" label="综测分数" width="120" sortable>
        <template #default="{ row }">
          <el-tag :type="getScoreType(row.score)" effect="dark">
            {{ row.score }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="rank" label="班级排名" width="120" />
      <el-table-column prop="uploadCount" label="材料数" width="100" align="center" />
      <el-table-column prop="status" label="审核状态" width="120">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click.stop="viewDetail(row)">
            查看详情
          </el-button>
          <el-button type="success" size="small" @click.stop="viewReport(row)">
            成绩报告
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="totalCount"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'

// 搜索和筛选
const searchQuery = ref('')
const selectedClass = ref('')
const currentPage = ref(1)
const pageSize = ref(20)

// 模拟学生数据
const students = ref([
  { studentId: '2021001', name: '张三', class: '计算机2021-1班', score: 95.2, rank: '1/42', uploadCount: 15, status: 'approved' },
  { studentId: '2021002', name: '李四', class: '计算机2021-1班', score: 92.8, rank: '2/42', uploadCount: 14, status: 'approved' },
  { studentId: '2021003', name: '王五', class: '计算机2021-1班', score: 90.5, rank: '3/42', uploadCount: 13, status: 'pending' },
  { studentId: '2021004', name: '赵六', class: '计算机2021-2班', score: 88.3, rank: '4/42', uploadCount: 12, status: 'approved' },
  { studentId: '2021005', name: '钱七', class: '计算机2021-2班', score: 85.6, rank: '5/42', uploadCount: 11, status: 'approved' },
  { studentId: '2021006', name: '孙八', class: '软件2021-1班', score: 82.4, rank: '6/42', uploadCount: 10, status: 'pending' },
  { studentId: '2021007', name: '周九', class: '软件2021-1班', score: 80.1, rank: '7/42', uploadCount: 9, status: 'rejected' },
  { studentId: '2021008', name: '吴十', class: '计算机2021-1班', score: 78.5, rank: '8/42', uploadCount: 8, status: 'approved' },
])

// 过滤后的学生列表
const filteredStudents = computed(() => {
  let result = students.value
  
  // 按搜索关键词过滤
  if (searchQuery.value) {
    result = result.filter(s => 
      s.name.includes(searchQuery.value) || s.studentId.includes(searchQuery.value)
    )
  }
  
  // 按班级过滤
  if (selectedClass.value) {
    result = result.filter(s => s.class.includes(selectedClass.value))
  }
  
  return result
})

const totalCount = computed(() => filteredStudents.value.length)

// 获取分数标签类型
const getScoreType = (score) => {
  if (score >= 90) return 'success'
  if (score >= 80) return 'primary'
  if (score >= 70) return 'warning'
  return 'danger'
}

// 获取状态标签类型
const getStatusType = (status) => {
  const types = {
    approved: 'success',
    pending: 'warning',
    rejected: 'danger'
  }
  return types[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const texts = {
    approved: '已通过',
    pending: '待审核',
    rejected: '未通过'
  }
  return texts[status] || '未知'
}

// 行点击事件
const handleRowClick = (row) => {
  console.log('点击行:', row)
}

// 查看详情
const viewDetail = (row) => {
  ElMessage.info(`查看 ${row.name} 的详细信息`)
}

// 查看报告
const viewReport = (row) => {
  ElMessage.info(`查看 ${row.name} 的成绩报告`)
}

// 导出数据
const exportData = () => {
  ElMessage.success('数据导出中...')
}
</script>

<style scoped>
.student-list {
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

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

@media (max-width: 768px) {
  .filter-bar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filter-bar .el-input,
  .filter-bar .el-select {
    width: 100% !important;
  }
}
</style>


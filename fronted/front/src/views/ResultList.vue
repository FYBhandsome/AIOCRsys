<template>
  <div class="result-list">
    <el-card class="filter-card">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-select v-model="filterForm.class" placeholder="选择班级" clearable>
            <el-option label="计算机科学与技术1班" value="cs1"></el-option>
            <el-option label="计算机科学与技术2班" value="cs2"></el-option>
            <el-option label="软件工程1班" value="se1"></el-option>
            <el-option label="软件工程2班" value="se2"></el-option>
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filterForm.semester" placeholder="选择学期" clearable>
            <el-option label="2023-2024学年第一学期" value="2023-1"></el-option>
            <el-option label="2023-2024学年第二学期" value="2023-2"></el-option>
            <el-option label="2024-2025学年第一学期" value="2024-1"></el-option>
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-input v-model="filterForm.keyword" placeholder="搜索学生姓名或学号" clearable></el-input>
        </el-col>
        <el-col :span="6">
          <el-button type="primary" @click="searchResults">搜索</el-button>
        </el-col>
      </el-row>
    </el-card>
    
    <el-card class="result-card">
      <template #header>
        <div class="card-header">
          <h2>综测结果列表</h2>
          <div class="actions">
            <el-button type="success" @click="exportExcel">导出Excel</el-button>
          </div>
        </div>
      </template>
      
      <el-table :data="tableData" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="学号" width="120"></el-table-column>
        <el-table-column prop="name" label="姓名" width="100"></el-table-column>
        <el-table-column prop="class" label="班级" width="180"></el-table-column>
        <el-table-column prop="totalScore" label="总分" width="80" sortable>
          <template #default="scope">
            <span :class="getScoreClass(scope.row.totalScore)">{{ scope.row.totalScore }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="rank" label="排名" width="80" sortable></el-table-column>
        <el-table-column prop="academic" label="学业成绩" width="100"></el-table-column>
        <el-table-column prop="moral" label="德育表现" width="100"></el-table-column>
        <el-table-column prop="innovation" label="科研创新" width="100"></el-table-column>
        <el-table-column prop="sports" label="文体活动" width="100"></el-table-column>
        <el-table-column prop="practice" label="社会实践" width="100"></el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button size="small" type="primary" @click="viewDetail(scope.row)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.currentPage"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

const filterForm = reactive({
  class: '',
  semester: '',
  keyword: ''
})

const loading = ref(false)
const tableData = ref([])

const pagination = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0
})

// 模拟数据
const mockData = [
  { id: '2021001001', name: '张三', class: '计算机科学与技术1班', totalScore: 95.5, rank: 1, academic: 88, moral: 20, innovation: 15, sports: 12, practice: 10 },
  { id: '2021001002', name: '李四', class: '计算机科学与技术1班', totalScore: 92.0, rank: 2, academic: 85, moral: 18, innovation: 18, sports: 10, practice: 11 },
  { id: '2021001003', name: '王五', class: '计算机科学与技术1班', totalScore: 90.5, rank: 3, academic: 83, moral: 19, innovation: 12, sports: 15, practice: 11 },
  { id: '2021001004', name: '赵六', class: '计算机科学与技术1班', totalScore: 88.0, rank: 4, academic: 80, moral: 17, innovation: 10, sports: 18, practice: 13 },
  { id: '2021001005', name: '钱七', class: '计算机科学与技术1班', totalScore: 85.5, rank: 5, academic: 78, moral: 16, innovation: 14, sports: 12, practice: 15 },
  { id: '2021001006', name: '孙八', class: '计算机科学与技术1班', totalScore: 82.0, rank: 6, academic: 75, moral: 15, innovation: 12, sports: 10, practice: 15 },
  { id: '2021001007', name: '周九', class: '计算机科学与技术1班', totalScore: 80.5, rank: 7, academic: 73, moral: 14, innovation: 10, sports: 12, practice: 11 },
  { id: '2021001008', name: '吴十', class: '计算机科学与技术1班', totalScore: 78.0, rank: 8, academic: 70, moral: 13, innovation: 8, sports: 15, practice: 12 }
]

const searchResults = () => {
  loading.value = true
  // 模拟搜索过程
  setTimeout(() => {
    tableData.value = mockData
    pagination.total = mockData.length
    loading.value = false
    ElMessage.success('搜索完成')
  }, 500)
}

const exportExcel = () => {
  ElMessage.success('正在导出Excel文件...')
  // 模拟导出过程
  setTimeout(() => {
    ElMessage.success('Excel文件导出成功')
  }, 1000)
}

const viewDetail = (row) => {
  ElMessage.info(`查看 ${row.name} 的详细信息`)
}

const getScoreClass = (score) => {
  if (score >= 90) return 'excellent'
  if (score >= 80) return 'good'
  if (score >= 70) return 'average'
  return 'poor'
}

const handleSizeChange = (val) => {
  pagination.pageSize = val
  searchResults()
}

const handleCurrentChange = (val) => {
  pagination.currentPage = val
  searchResults()
}

onMounted(() => {
  searchResults()
})
</script>

<style scoped>
.result-list {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.filter-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  color: #333;
}

.actions {
  display: flex;
  gap: 10px;
}

.excellent {
  color: #67C23A;
  font-weight: bold;
}

.good {
  color: #409EFF;
}

.average {
  color: #E6A23C;
}

.poor {
  color: #F56C6C;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>
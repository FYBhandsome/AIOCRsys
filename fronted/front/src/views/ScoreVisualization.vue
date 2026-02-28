<template>
  <div class="score-visualization">
    <div class="page-header">
      <h1 class="page-title">成绩可视化分析</h1>
      <p class="page-subtitle">通过多维度图表分析班级成绩分布与学生表现</p>
    </div>

    <el-card class="filter-card">
      <el-form :model="filterForm" inline>
        <el-form-item label="班级">
          <el-select v-model="filterForm.classId" placeholder="选择班级" clearable style="width: 200px">
            <el-option
              v-for="item in classOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="学期">
          <el-select v-model="filterForm.semester" placeholder="选择学期" clearable style="width: 200px">
            <el-option
              v-for="item in semesterOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="applyFilter" :loading="loading">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="resetFilter">
            <el-icon><RefreshRight /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon average">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.average }}</div>
              <div class="stat-label">平均分</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon highest">
              <el-icon><Top /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.highest }}</div>
              <div class="stat-label">最高分</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon pass-rate">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.passRate }}%</div>
              <div class="stat-label">及格率</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon excellent-rate">
              <el-icon><Star /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.excellentRate }}%</div>
              <div class="stat-label">优秀率</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <h3>成绩分布直方图</h3>
            </div>
          </template>
          <div ref="distributionChart" class="chart-container"></div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <h3>班级排名对比</h3>
              <el-button size="small" @click="refreshRankingChart">
                <el-icon><RefreshRight /></el-icon>
                刷新
              </el-button>
            </div>
          </template>
          <div ref="rankingChart" class="chart-container"></div>
        </el-card>
      </el-col>

      <el-col :xs="24">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <h3>成绩趋势分析</h3>
            </div>
          </template>
          <div ref="trendChart" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <h3>学生成绩详情</h3>
          <div>
            <el-button type="success" @click="exportData">
              <el-icon><Download /></el-icon>
              导出数据
            </el-button>
          </div>
        </div>
      </template>
      
      <el-table :data="studentScores" v-loading="loading" stripe>
        <el-table-column prop="student_id" label="学号" width="120" />
        <el-table-column prop="student_name" label="姓名" width="100" />
        <el-table-column prop="class_name" label="班级" width="150" />
        <el-table-column prop="arithmetic_average" label="算术平均分" width="110" sortable>
          <template #default="scope">
            <span :class="getScoreClass(scope.row.arithmetic_average)">{{ scope.row.arithmetic_average?.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="weighted_average" label="加权平均分" width="110" sortable>
          <template #default="scope">
            <span>{{ scope.row.weighted_average?.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="average_gpa" label="平均GPA" width="100" sortable>
          <template #default="scope">
            <span>{{ scope.row.average_gpa?.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="pass_rate" label="及格率" width="100">
          <template #default="scope">
            <span>{{ scope.row.pass_rate ? (scope.row.pass_rate * 100).toFixed(1) + '%' : '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="scope">
            <el-button type="primary" size="small" @click="viewStudentDetail(scope.row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.currentPage"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="pagination.total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="showStudentDetail"
      title="学生成绩详情"
      width="70%"
      :close-on-click-modal="false"
    >
      <div v-if="currentStudent" class="student-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="学号">{{ currentStudent.student_id }}</el-descriptions-item>
          <el-descriptions-item label="姓名">{{ currentStudent.student_name }}</el-descriptions-item>
          <el-descriptions-item label="班级">{{ currentStudent.class_name }}</el-descriptions-item>
          <el-descriptions-item label="算术平均分">{{ currentStudent.arithmetic_average?.toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="加权平均分">{{ currentStudent.weighted_average?.toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="平均GPA">{{ currentStudent.average_gpa?.toFixed(2) }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Search, 
  RefreshRight, 
  TrendCharts, 
  Top, 
  CircleCheck, 
  Star, 
  Download 
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { teacherAPI } from '@/services/api'

let distributionChartInstance = null
let trendChartInstance = null
let rankingChartInstance = null

const loading = ref(false)
const showStudentDetail = ref(false)
const currentStudent = ref(null)

const filterForm = reactive({
  classId: '',
  semester: '',
  academicYear: ''
})

const stats = reactive({
  average: 0,
  highest: 0,
  passRate: 0,
  excellentRate: 0
})

const studentScores = ref([])
const classOptions = ref([])

const semesterOptions = ref([
  { label: '2023-2024学年第一学期', value: '1', academicYear: '2023-2024' },
  { label: '2023-2024学年第二学期', value: '2', academicYear: '2023-2024' },
  { label: '2024-2025学年第一学期', value: '1', academicYear: '2024-2025' },
  { label: '2024-2025学年第二学期', value: '2', academicYear: '2024-2025' }
])

const pagination = reactive({
  currentPage: 1,
  pageSize: 20,
  total: 0
})

const fetchClasses = async () => {
  try {
    const classes = await teacherAPI.getClasses()
    classOptions.value = classes.map(cls => ({
      label: cls.name,
      value: cls.id
    }))
  } catch (error) {
    console.error('获取班级列表失败:', error)
  }
}

const fetchScoreStats = async () => {
  try {
    loading.value = true
    const response = await teacherAPI.getClassStats(filterForm.classId)
    
    if (response && response.statistics) {
      stats.average = response.statistics.average_arithmetic || 0
      stats.highest = response.statistics.max_arithmetic || 0
      
      const total = response.total_students || 0
      if (total > 0 && response.distribution) {
        const passCount = (response.distribution['60-69'] || 0) + 
                         (response.distribution['70-79'] || 0) + 
                         (response.distribution['80-89'] || 0) + 
                         (response.distribution['90-100'] || 0)
        stats.passRate = Math.round((passCount / total) * 100)
        
        const excellentCount = response.distribution['90-100'] || 0
        stats.excellentRate = Math.round((excellentCount / total) * 100)
      }
      
      initDistributionChart(response.distribution)
    }
  } catch (error) {
    console.error('获取成绩统计失败:', error)
    ElMessage.error('获取成绩统计失败')
  } finally {
    loading.value = false
  }
}

const fetchStudentScores = async () => {
  try {
    loading.value = true
    const response = await teacherAPI.getClassRanking(
      filterForm.classId,
      filterForm.semester,
      filterForm.academicYear
    )
    
    if (response && response.rankings) {
      studentScores.value = response.rankings
      pagination.total = response.total_students || 0
      initRankingChart(response.rankings)
    }
  } catch (error) {
    console.error('获取学生成绩失败:', error)
    ElMessage.error('获取学生成绩失败')
  } finally {
    loading.value = false
  }
}

const initDistributionChart = (distribution) => {
  if (!distributionChart.value) return
  
  distributionChartInstance = echarts.init(distributionChart.value)
  
  const data = [
    { range: '0-59', count: distribution?.['0-59'] || 0 },
    { range: '60-69', count: distribution?.['60-69'] || 0 },
    { range: '70-79', count: distribution?.['70-79'] || 0 },
    { range: '80-89', count: distribution?.['80-89'] || 0 },
    { range: '90-100', count: distribution?.['90-100'] || 0 }
  ]
  
  const option = {
    title: {
      text: '成绩分布',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    xAxis: {
      type: 'category',
      data: data.map(item => item.range)
    },
    yAxis: {
      type: 'value',
      name: '人数'
    },
    series: [
      {
        name: '人数',
        type: 'bar',
        data: data.map(item => item.count),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#83bff6' },
            { offset: 0.5, color: '#188df0' },
            { offset: 1, color: '#188df0' }
          ])
        }
      }
    ]
  }
  
  distributionChartInstance.setOption(option)
}

const initRankingChart = (rankings) => {
  if (!rankingChart.value) return
  
  rankingChartInstance = echarts.init(rankingChart.value)
  
  const top10 = (rankings || []).slice(0, 10)
  
  const option = {
    title: {
      text: '学生成绩排名Top10',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    xAxis: {
      type: 'category',
      data: top10.map(item => item.student_name),
      axisLabel: {
        rotate: 30
      }
    },
    yAxis: {
      type: 'value',
      name: '分数'
    },
    series: [
      {
        name: '算术平均分',
        type: 'bar',
        data: top10.map(item => item.arithmetic_average),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#83bff6' },
            { offset: 0.5, color: '#188df0' },
            { offset: 1, color: '#188df0' }
          ])
        }
      }
    ]
  }
  
  rankingChartInstance.setOption(option)
}

const initTrendChart = () => {
  if (!trendChart.value) return
  
  trendChartInstance = echarts.init(trendChart.value)
  
  const option = {
    title: {
      text: '成绩趋势',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: ['2023-1', '2023-2', '2024-1', '2024-2']
    },
    yAxis: {
      type: 'value',
      name: '分数'
    },
    series: [
      {
        name: '班级平均分',
        type: 'line',
        data: [],
        smooth: true,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.5)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
          ])
        }
      }
    ]
  }
  
  trendChartInstance.setOption(option)
}

const getScoreClass = (score) => {
  if (!score) return ''
  if (score >= 90) return 'excellent-score'
  if (score >= 80) return 'good-score'
  if (score >= 70) return 'average-score'
  if (score >= 60) return 'pass-score'
  return 'fail-score'
}

const applyFilter = async () => {
  await fetchScoreStats()
  await fetchStudentScores()
}

const resetFilter = () => {
  filterForm.classId = ''
  filterForm.semester = ''
  filterForm.academicYear = ''
  applyFilter()
}

const refreshRankingChart = () => {
  fetchStudentScores()
}

const exportData = async () => {
  try {
    ElMessage.success('正在导出数据...')
    await teacherAPI.exportClassRanking({
      class_name: filterForm.classId,
      semester: filterForm.semester,
      academic_year: filterForm.academicYear
    })
    ElMessage.success('数据导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

const viewStudentDetail = (student) => {
  currentStudent.value = student
  showStudentDetail.value = true
}

const handleSizeChange = (val) => {
  pagination.pageSize = val
  fetchStudentScores()
}

const handleCurrentChange = (val) => {
  pagination.currentPage = val
  fetchStudentScores()
}

const handleResize = () => {
  distributionChartInstance?.resize()
  trendChartInstance?.resize()
  rankingChartInstance?.resize()
}

onMounted(async () => {
  await fetchClasses()
  await fetchScoreStats()
  await fetchStudentScores()
  await nextTick()
  initTrendChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  distributionChartInstance?.dispose()
  trendChartInstance?.dispose()
  rankingChartInstance?.dispose()
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.score-visualization {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.page-header {
  margin-bottom: 20px;
  text-align: center;
}

.page-title {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 10px;
}

.page-subtitle {
  font-size: 14px;
  color: #606266;
}

.filter-card {
  margin-bottom: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  height: 100px;
}

.stat-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  font-size: 24px;
  color: white;
}

.stat-icon.average {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.highest {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.pass-rate {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.excellent-rate {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}

.chart-row {
  margin-bottom: 20px;
}

.chart-card {
  height: 400px;
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.chart-container {
  width: 100%;
  height: 320px;
}

.table-card {
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  text-align: right;
}

.student-detail {
  padding: 20px 0;
}

.excellent-score {
  color: #67c23a;
  font-weight: bold;
}

.good-score {
  color: #409eff;
  font-weight: bold;
}

.average-score {
  color: #e6a23c;
}

.pass-score {
  color: #f56c6c;
}

.fail-score {
  color: #f56c6c;
  font-weight: bold;
}

@media (max-width: 768px) {
  .score-visualization {
    padding: 10px;
  }
  
  .stat-card {
    height: 80px;
    margin-bottom: 10px;
  }
  
  .stat-icon {
    width: 50px;
    height: 50px;
    font-size: 20px;
  }
  
  .stat-value {
    font-size: 20px;
  }
  
  .chart-card {
    height: 300px;
  }
  
  .chart-container {
    height: 220px;
  }
}
</style>

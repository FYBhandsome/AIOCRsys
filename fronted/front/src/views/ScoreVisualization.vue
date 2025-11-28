<template>
  <div class="score-visualization">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">成绩可视化分析</h1>
      <p class="page-subtitle">通过多维度图表分析班级成绩分布与学生表现</p>
    </div>

    <!-- 筛选条件 -->
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
        <el-form-item label="科目">
          <el-select v-model="filterForm.subject" placeholder="选择科目" clearable style="width: 200px">
            <el-option
              v-for="item in subjectOptions"
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

    <!-- 统计卡片 -->
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

    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-row">
      <!-- 成绩分布直方图 -->
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <h3>成绩分布直方图</h3>
              <el-button-group>
                <el-button size="small" :type="chartType === 'histogram' ? 'primary' : ''" @click="chartType = 'histogram'">直方图</el-button>
                <el-button size="small" :type="chartType === 'density' ? 'primary' : ''" @click="chartType = 'density'">密度图</el-button>
              </el-button-group>
            </div>
          </template>
          <div ref="distributionChart" class="chart-container"></div>
        </el-card>
      </el-col>

      <!-- 科目成绩对比雷达图 -->
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <h3>科目成绩对比雷达图</h3>
              <el-select v-model="radarChartType" size="small" style="width: 120px">
                <el-option label="班级平均" value="class" />
                <el-option label="个人成绩" value="student" />
              </el-select>
            </div>
          </template>
          <div ref="subjectRadarChart" class="chart-container"></div>
        </el-card>
      </el-col>

      <!-- 成绩趋势折线图 -->
      <el-col :xs="24">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <h3>成绩趋势分析</h3>
              <div>
                <el-select v-model="trendChartType" size="small" style="width: 120px; margin-right: 10px">
                  <el-option label="班级平均" value="class" />
                  <el-option label="个人成绩" value="student" />
                </el-select>
                <el-select v-model="trendPeriod" size="small" style="width: 120px">
                  <el-option label="按学期" value="semester" />
                  <el-option label="按月度" value="month" />
                </el-select>
              </div>
            </div>
          </template>
          <div ref="trendChart" class="chart-container"></div>
        </el-card>
      </el-col>

      <!-- 班级排名对比 -->
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

      <!-- 成绩相关性分析 -->
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <h3>成绩相关性分析</h3>
              <el-select v-model="correlationType" size="small" style="width: 150px">
                <el-option label="科目间相关性" value="subject" />
                <el-option label="成绩与出勤率" value="attendance" />
                <el-option label="成绩与作业提交率" value="homework" />
              </el-select>
            </div>
          </template>
          <div ref="correlationChart" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 详细数据表格 -->
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
        <el-table-column prop="studentId" label="学号" width="120" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="className" label="班级" width="150" />
        <el-table-column prop="chinese" label="语文" width="80" sortable />
        <el-table-column prop="math" label="数学" width="80" sortable />
        <el-table-column prop="english" label="英语" width="80" sortable />
        <el-table-column prop="physics" label="物理" width="80" sortable />
        <el-table-column prop="chemistry" label="化学" width="80" sortable />
        <el-table-column prop="biology" label="生物" width="80" sortable />
        <el-table-column prop="totalScore" label="总分" width="90" sortable>
          <template #default="scope">
            <span :class="getScoreClass(scope.row.totalScore)">{{ scope.row.totalScore }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="classRank" label="班级排名" width="100" sortable />
        <el-table-column prop="gradeRank" label="年级排名" width="100" sortable />
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

    <!-- 学生详情对话框 -->
    <el-dialog
      v-model="showStudentDetail"
      title="学生成绩详情"
      width="70%"
      :close-on-click-modal="false"
    >
      <div v-if="currentStudent" class="student-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="学号">{{ currentStudent.studentId }}</el-descriptions-item>
          <el-descriptions-item label="姓名">{{ currentStudent.name }}</el-descriptions-item>
          <el-descriptions-item label="班级">{{ currentStudent.className }}</el-descriptions-item>
          <el-descriptions-item label="总分">{{ currentStudent.totalScore }}</el-descriptions-item>
          <el-descriptions-item label="班级排名">{{ currentStudent.classRank }}</el-descriptions-item>
          <el-descriptions-item label="年级排名">{{ currentStudent.gradeRank }}</el-descriptions-item>
        </el-descriptions>
        
        <div class="student-chart-container">
          <div ref="studentRadarChart" class="chart-container"></div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick, watch } from 'vue'
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

// 图表实例
let distributionChartInstance = null
let subjectRadarChartInstance = null
let trendChartInstance = null
let rankingChartInstance = null
let correlationChartInstance = null
let studentRadarChartInstance = null

// 响应式数据
const loading = ref(false)
const showStudentDetail = ref(false)
const currentStudent = ref(null)

// 筛选表单
const filterForm = reactive({
  classId: '',
  semester: '',
  subject: ''
})

// 图表类型
const chartType = ref('histogram')
const radarChartType = ref('class')
const trendChartType = ref('class')
const trendPeriod = ref('semester')
const correlationType = ref('subject')

// 统计数据
const stats = reactive({
  average: 0,
  highest: 0,
  passRate: 0,
  excellentRate: 0
})

// 学生成绩数据
const studentScores = ref([])

// 分页数据
const pagination = reactive({
  currentPage: 1,
  pageSize: 20,
  total: 0
})

// 选项数据
const classOptions = ref([
  { label: '计算机科学与技术1班', value: 'cs1' },
  { label: '计算机科学与技术2班', value: 'cs2' },
  { label: '软件工程1班', value: 'se1' },
  { label: '软件工程2班', value: 'se2' }
])

const semesterOptions = ref([
  { label: '2023-2024学年第一学期', value: '2023-1' },
  { label: '2023-2024学年第二学期', value: '2023-2' },
  { label: '2024-2025学年第一学期', value: '2024-1' }
])

const subjectOptions = ref([
  { label: '语文', value: 'chinese' },
  { label: '数学', value: 'math' },
  { label: '英语', value: 'english' },
  { label: '物理', value: 'physics' },
  { label: '化学', value: 'chemistry' },
  { label: '生物', value: 'biology' }
])

// 获取成绩统计数据
const fetchScoreStats = async () => {
  try {
    loading.value = true
    const response = await teacherAPI.getClassStats(filterForm.classId)
    stats.average = response.average || 0
    stats.highest = response.highest || 0
    stats.passRate = response.passRate || 0
    stats.excellentRate = response.excellenceRate || 0
  } catch (error) {
    console.error('获取成绩统计失败:', error)
    ElMessage.error('获取成绩统计失败')
  } finally {
    loading.value = false
  }
}

// 获取学生成绩列表
const fetchStudentScores = async () => {
  try {
    loading.value = true
    const params = {
      page: pagination.currentPage,
      pageSize: pagination.pageSize,
      classId: filterForm.classId,
      semester: filterForm.semester,
      subject: filterForm.subject
    }
    const response = await teacherAPI.getStudentList(params)
    studentScores.value = response.data || []
    pagination.total = response.total || 0
  } catch (error) {
    console.error('获取学生成绩失败:', error)
    ElMessage.error('获取学生成绩失败')
  } finally {
    loading.value = false
  }
}

// 初始化成绩分布直方图
const initDistributionChart = () => {
  if (!distributionChart.value) return
  
  distributionChartInstance = echarts.init(distributionChart.value)
  
  // 模拟数据
  const data = [
    { range: '0-59', count: 5 },
    { range: '60-69', count: 15 },
    { range: '70-79', count: 30 },
    { range: '80-89', count: 35 },
    { range: '90-100', count: 15 }
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

// 初始化科目成绩雷达图
const initSubjectRadarChart = () => {
  if (!subjectRadarChart.value) return
  
  subjectRadarChartInstance = echarts.init(subjectRadarChart.value)
  
  // 模拟数据
  const data = {
    class: {
      name: '班级平均',
      value: [85, 78, 82, 75, 80, 76]
    },
    student: {
      name: '个人成绩',
      value: [90, 85, 88, 80, 82, 85]
    }
  }
  
  const currentData = radarChartType.value === 'class' ? data.class : data.student
  
  const option = {
    title: {
      text: currentData.name,
      left: 'center'
    },
    tooltip: {},
    radar: {
      indicator: [
        { name: '语文', max: 100 },
        { name: '数学', max: 100 },
        { name: '英语', max: 100 },
        { name: '物理', max: 100 },
        { name: '化学', max: 100 },
        { name: '生物', max: 100 }
      ]
    },
    series: [
      {
        name: '成绩',
        type: 'radar',
        data: [
          {
            value: currentData.value,
            name: currentData.name,
            areaStyle: {
              color: 'rgba(64, 158, 255, 0.3)'
            }
          }
        ]
      }
    ]
  }
  
  subjectRadarChartInstance.setOption(option)
}

// 初始化成绩趋势图
const initTrendChart = () => {
  if (!trendChart.value) return
  
  trendChartInstance = echarts.init(trendChart.value)
  
  // 模拟数据
  const data = {
    class: {
      name: '班级平均',
      data: [75, 78, 82, 80, 85, 88]
    },
    student: {
      name: '个人成绩',
      data: [80, 82, 85, 83, 88, 92]
    }
  }
  
  const currentData = trendChartType.value === 'class' ? data.class : data.student
  const xAxisData = trendPeriod.value === 'semester' 
    ? ['2023-1', '2023-2', '2024-1', '2024-2', '2025-1', '2025-2']
    : ['1月', '2月', '3月', '4月', '5月', '6月']
  
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
      data: xAxisData
    },
    yAxis: {
      type: 'value',
      name: '分数'
    },
    series: [
      {
        name: currentData.name,
        type: 'line',
        data: currentData.data,
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

// 初始化班级排名对比图
const initRankingChart = () => {
  if (!rankingChart.value) return
  
  rankingChartInstance = echarts.init(rankingChart.value)
  
  // 模拟数据
  const data = [
    { name: '计算机科学与技术1班', value: 85 },
    { name: '计算机科学与技术2班', value: 82 },
    { name: '软件工程1班', value: 88 },
    { name: '软件工程2班', value: 80 }
  ]
  
  const option = {
    title: {
      text: '班级平均分对比',
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
      data: data.map(item => item.name),
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: '平均分'
    },
    series: [
      {
        name: '平均分',
        type: 'bar',
        data: data.map(item => item.value),
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

// 初始化成绩相关性分析图
const initCorrelationChart = () => {
  if (!correlationChart.value) return
  
  correlationChartInstance = echarts.init(correlationChart.value)
  
  // 模拟数据
  const data = {
    subject: [
      [0, 0, 1, '语文'],
      [1, 0.6, 1, '数学'],
      [2, 0.7, 1, '英语'],
      [3, 0.5, 1, '物理'],
      [4, 0.6, 1, '化学'],
      [5, 0.4, 1, '生物']
    ],
    attendance: [
      [60, 50, 1, '60%'],
      [70, 65, 1, '70%'],
      [80, 75, 1, '80%'],
      [90, 85, 1, '90%'],
      [100, 92, 1, '100%']
    ],
    homework: [
      [50, 45, 1, '50%'],
      [60, 58, 1, '60%'],
      [70, 68, 1, '70%'],
      [80, 78, 1, '80%'],
      [90, 88, 1, '90%'],
      [100, 95, 1, '100%']
    ]
  }
  
  const currentData = data[correlationType.value]
  
  const option = {
    title: {
      text: correlationType.value === 'subject' ? '科目间相关性' : 
            correlationType.value === 'attendance' ? '成绩与出勤率相关性' : 
            '成绩与作业提交率相关性',
      left: 'center'
    },
    tooltip: {
      trigger: 'item',
      formatter: function(params) {
        return `${params.data[3]}: (${params.data[0]}, ${params.data[1]})`
      }
    },
    xAxis: {
      type: 'value',
      name: correlationType.value === 'subject' ? '科目' : 
            correlationType.value === 'attendance' ? '出勤率(%)' : 
            '作业提交率(%)'
    },
    yAxis: {
      type: 'value',
      name: '成绩'
    },
    series: [
      {
        name: '数据点',
        type: 'scatter',
        data: currentData,
        symbolSize: 20,
        itemStyle: {
          color: '#409EFF'
        }
      }
    ]
  }
  
  correlationChartInstance.setOption(option)
}

// 初始化学生详情雷达图
const initStudentRadarChart = () => {
  if (!studentRadarChart.value || !currentStudent.value) return
  
  studentRadarChartInstance = echarts.init(studentRadarChart.value)
  
  const data = [
    { name: '语文', value: currentStudent.value.chinese },
    { name: '数学', value: currentStudent.value.math },
    { name: '英语', value: currentStudent.value.english },
    { name: '物理', value: currentStudent.value.physics },
    { name: '化学', value: currentStudent.value.chemistry },
    { name: '生物', value: currentStudent.value.biology }
  ]
  
  const option = {
    title: {
      text: `${currentStudent.value.name} 的成绩雷达图`,
      left: 'center'
    },
    tooltip: {},
    radar: {
      indicator: [
        { name: '语文', max: 100 },
        { name: '数学', max: 100 },
        { name: '英语', max: 100 },
        { name: '物理', max: 100 },
        { name: '化学', max: 100 },
        { name: '生物', max: 100 }
      ]
    },
    series: [
      {
        name: '成绩',
        type: 'radar',
        data: [
          {
            value: data.map(item => item.value),
            name: '成绩',
            areaStyle: {
              color: 'rgba(64, 158, 255, 0.3)'
            }
          }
        ]
      }
    ]
  }
  
  studentRadarChartInstance.setOption(option)
}

// 获取成绩样式类
const getScoreClass = (score) => {
  if (score >= 90) return 'excellent-score'
  if (score >= 80) return 'good-score'
  if (score >= 70) return 'average-score'
  if (score >= 60) return 'pass-score'
  return 'fail-score'
}

// 应用筛选
const applyFilter = async () => {
  await fetchScoreStats()
  await fetchStudentScores()
  await nextTick()
  initAllCharts()
}

// 重置筛选
const resetFilter = () => {
  filterForm.classId = ''
  filterForm.semester = ''
  filterForm.subject = ''
  applyFilter()
}

// 刷新排名图表
const refreshRankingChart = () => {
  initRankingChart()
}

// 导出数据
const exportData = () => {
  ElMessage.success('正在导出数据...')
  // 实际应用中这里应该调用导出API
  setTimeout(() => {
    ElMessage.success('数据导出成功')
  }, 1000)
}

// 查看学生详情
const viewStudentDetail = (student) => {
  currentStudent.value = student
  showStudentDetail.value = true
  nextTick(() => {
    initStudentRadarChart()
  })
}

// 分页处理
const handleSizeChange = (val) => {
  pagination.pageSize = val
  fetchStudentScores()
}

const handleCurrentChange = (val) => {
  pagination.currentPage = val
  fetchStudentScores()
}

// 初始化所有图表
const initAllCharts = () => {
  initDistributionChart()
  initSubjectRadarChart()
  initTrendChart()
  initRankingChart()
  initCorrelationChart()
}

// 窗口大小变化时重新调整图表大小
const handleResize = () => {
  distributionChartInstance?.resize()
  subjectRadarChartInstance?.resize()
  trendChartInstance?.resize()
  rankingChartInstance?.resize()
  correlationChartInstance?.resize()
  studentRadarChartInstance?.resize()
}

// 监听图表类型变化
watch(chartType, () => {
  initDistributionChart()
})

watch(radarChartType, () => {
  initSubjectRadarChart()
})

watch(trendChartType, () => {
  initTrendChart()
})

watch(trendPeriod, () => {
  initTrendChart()
})

watch(correlationType, () => {
  initCorrelationChart()
})

// 组件挂载时初始化
onMounted(async () => {
  await fetchScoreStats()
  await fetchStudentScores()
  await nextTick()
  initAllCharts()
  window.addEventListener('resize', handleResize)
})

// 组件卸载时清理
onUnmounted(() => {
  distributionChartInstance?.dispose()
  subjectRadarChartInstance?.dispose()
  trendChartInstance?.dispose()
  rankingChartInstance?.dispose()
  correlationChartInstance?.dispose()
  studentRadarChartInstance?.dispose()
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.score-visualization {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

/* 页面标题 */
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

/* 筛选卡片 */
.filter-card {
  margin-bottom: 20px;
}

/* 统计卡片行 */
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

/* 图表行 */
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

/* 表格卡片 */
.table-card {
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  text-align: right;
}

/* 学生详情 */
.student-detail {
  padding: 20px 0;
}

.student-chart-container {
  margin-top: 20px;
}

/* 成绩样式 */
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

/* 响应式设计 */
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
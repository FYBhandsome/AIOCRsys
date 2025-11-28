<template>
  <div class="class-ranking">
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/teacher/dashboard' }">教师首页</el-breadcrumb-item>
        <el-breadcrumb-item>班级排名</el-breadcrumb-item>
      </el-breadcrumb>
      <h1 class="page-title">班级排名</h1>
    </div>

    <div class="filter-section">
      <el-card>
        <el-form :inline="true" :model="filterForm" class="filter-form">
          <el-form-item label="学期">
            <el-select v-model="filterForm.semester" placeholder="请选择学期" clearable @change="handleFilterChange">
              <el-option
                v-for="item in semesterOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="班级">
            <el-select v-model="filterForm.classId" placeholder="请选择班级" clearable @change="handleFilterChange">
              <el-option
                v-for="item in classOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="科目">
            <el-select v-model="filterForm.subject" placeholder="请选择科目" clearable @change="handleFilterChange">
              <el-option
                v-for="item in subjectOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleFilterChange">查询</el-button>
            <el-button @click="resetFilter">重置</el-button>
            <el-button type="success" @click="exportRankingData" :loading="exporting">导出数据</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <div class="ranking-content">
      <el-row :gutter="20">
        <el-col :span="16">
          <el-card class="ranking-table-card">
            <template #header>
              <div class="card-header">
                <span>班级排名</span>
                <el-radio-group v-model="rankingType" size="small" @change="handleRankingTypeChange">
                  <el-radio-button label="total">总分排名</el-radio-button>
                  <el-radio-button label="average">平均分排名</el-radio-button>
                  <el-radio-button label="pass">及格率排名</el-radio-button>
                </el-radio-group>
              </div>
            </template>
            <el-table
              :data="rankingData"
              style="width: 100%"
              :default-sort="{ prop: 'rank', order: 'ascending' }"
              v-loading="loading"
            >
              <el-table-column prop="rank" label="排名" width="80" sortable />
              <el-table-column prop="className" label="班级" min-width="120" />
              <el-table-column prop="totalScore" label="总分" width="100" sortable v-if="rankingType === 'total'">
                <template #default="scope">
                  <span :class="getScoreClass(scope.row.totalScore)">{{ scope.row.totalScore }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="averageScore" label="平均分" width="100" sortable v-if="rankingType === 'average'">
                <template #default="scope">
                  <span :class="getScoreClass(scope.row.averageScore)">{{ scope.row.averageScore }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="passRate" label="及格率" width="100" sortable v-if="rankingType === 'pass'">
                <template #default="scope">
                  <el-tag :type="getPassRateTagType(scope.row.passRate)">{{ scope.row.passRate }}%</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="excellentRate" label="优秀率" width="100" sortable>
                <template #default="scope">
                  <el-tag type="success">{{ scope.row.excellentRate }}%</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="studentCount" label="学生人数" width="100" />
              <el-table-column label="操作" width="120">
                <template #default="scope">
                  <el-button
                    link
                    type="primary"
                    size="small"
                    @click="viewClassDetail(scope.row)"
                  >
                    查看详情
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card class="ranking-chart-card">
            <template #header>
              <div class="card-header">
                <span>排名分布图</span>
              </div>
            </template>
            <div ref="rankingChart" class="chart-container"></div>
          </el-card>
          <el-card class="ranking-summary-card">
            <template #header>
              <div class="card-header">
                <span>排名统计</span>
              </div>
            </template>
            <div class="summary-content">
              <div class="summary-item">
                <div class="summary-label">参与班级</div>
                <div class="summary-value">{{ summaryData.totalClasses }}</div>
              </div>
              <div class="summary-item">
                <div class="summary-label">最高分</div>
                <div class="summary-value">{{ summaryData.highestScore }}</div>
              </div>
              <div class="summary-item">
                <div class="summary-label">最低分</div>
                <div class="summary-value">{{ summaryData.lowestScore }}</div>
              </div>
              <div class="summary-item">
                <div class="summary-label">平均分</div>
                <div class="summary-value">{{ summaryData.averageScore }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 班级详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="班级详情"
      width="70%"
      destroy-on-close
    >
      <div v-if="currentClass">
        <h3>{{ currentClass.className }} - 学生成绩排名</h3>
        <el-table
          :data="classStudentData"
          style="width: 100%"
          :default-sort="{ prop: 'rank', order: 'ascending' }"
          v-loading="detailLoading"
        >
          <el-table-column prop="rank" label="排名" width="80" sortable />
          <el-table-column prop="studentName" label="学生姓名" min-width="120" />
          <el-table-column prop="studentId" label="学号" width="120" />
          <el-table-column prop="totalScore" label="总分" width="100" sortable>
            <template #default="scope">
              <span :class="getScoreClass(scope.row.totalScore)">{{ scope.row.totalScore }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="averageScore" label="平均分" width="100" sortable>
            <template #default="scope">
              <span :class="getScoreClass(scope.row.averageScore)">{{ scope.row.averageScore }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="chineseScore" label="语文" width="80" sortable />
          <el-table-column prop="mathScore" label="数学" width="80" sortable />
          <el-table-column prop="englishScore" label="英语" width="80" sortable />
          <el-table-column prop="physicsScore" label="物理" width="80" sortable />
          <el-table-column prop="chemistryScore" label="化学" width="80" sortable />
          <el-table-column prop="biologyScore" label="生物" width="80" sortable />
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { teacherAPI } from '@/services/api'
import * as echarts from 'echarts'

// 响应式数据
const loading = ref(false)
const detailLoading = ref(false)
const exporting = ref(false)
const rankingData = ref([])
const classStudentData = ref([])
const detailDialogVisible = ref(false)
const currentClass = ref(null)
const rankingChart = ref(null)
const chartInstance = ref(null)
const rankingType = ref('total')

// 筛选表单
const filterForm = reactive({
  semester: '',
  classId: '',
  subject: ''
})

// 选项数据
const semesterOptions = ref([
  { label: '2023-2024学年 第一学期', value: '2023-1' },
  { label: '2023-2024学年 第二学期', value: '2023-2' },
  { label: '2024-2025学年 第一学期', value: '2024-1' }
])

const classOptions = ref([])
const subjectOptions = ref([
  { label: '总分', value: 'total' },
  { label: '语文', value: 'chinese' },
  { label: '数学', value: 'math' },
  { label: '英语', value: 'english' },
  { label: '物理', value: 'physics' },
  { label: '化学', value: 'chemistry' },
  { label: '生物', value: 'biology' }
])

// 统计数据
const summaryData = reactive({
  totalClasses: 0,
  highestScore: 0,
  lowestScore: 0,
  averageScore: 0
})

// 获取班级选项
const getClassOptions = async () => {
  try {
    const res = await teacherAPI.getClasses()
    if (res.success) {
      classOptions.value = res.data.map(item => ({
        label: item.className,
        value: item.classId
      }))
    }
  } catch (error) {
    console.error('获取班级选项失败:', error)
    ElMessage.error('获取班级选项失败')
  }
}

// 获取班级排名数据
const getRankingData = async () => {
  loading.value = true
  try {
    const params = {
      semester: filterForm.semester,
      class_id: filterForm.classId,
      subject: filterForm.subject,
      type: rankingType.value
    }
    
    const res = await teacherAPI.getClassRanking(params)
    if (res.success) {
      rankingData.value = res.data.ranking || []
      updateSummaryData(res.data.summary || {})
      renderRankingChart()
    } else {
      ElMessage.error(res.message || '获取班级排名数据失败')
    }
  } catch (error) {
    console.error('获取班级排名数据失败:', error)
    ElMessage.error('获取班级排名数据失败')
  } finally {
    loading.value = false
  }
}

// 获取班级学生详情
const getClassStudentDetail = async (classId) => {
  detailLoading.value = true
  try {
    const res = await teacherAPI.getClassStudentRanking(classId)
    if (res.success) {
      classStudentData.value = res.data || []
    } else {
      ElMessage.error(res.message || '获取班级学生详情失败')
    }
  } catch (error) {
    console.error('获取班级学生详情失败:', error)
    ElMessage.error('获取班级学生详情失败')
  } finally {
    detailLoading.value = false
  }
}

// 更新统计数据
const updateSummaryData = (data) => {
  summaryData.totalClasses = data.totalClasses || 0
  summaryData.highestScore = data.highestScore || 0
  summaryData.lowestScore = data.lowestScore || 0
  summaryData.averageScore = data.averageScore || 0
}

// 渲染排名图表
const renderRankingChart = () => {
  nextTick(() => {
    if (!rankingChart.value) return
    
    if (chartInstance.value) {
      chartInstance.value.dispose()
    }
    
    chartInstance.value = echarts.init(rankingChart.value)
    
    const chartData = rankingData.value.map(item => ({
      name: item.className,
      value: rankingType.value === 'total' ? item.totalScore : 
             rankingType.value === 'average' ? item.averageScore : 
             item.passRate
    }))
    
    const option = {
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c}'
      },
      xAxis: {
        type: 'category',
        data: chartData.map(item => item.name),
        axisLabel: {
          rotate: 45
        }
      },
      yAxis: {
        type: 'value',
        name: rankingType.value === 'pass' ? '及格率(%)' : '分数'
      },
      series: [
        {
          type: 'bar',
          data: chartData.map(item => item.value),
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
    
    chartInstance.value.setOption(option)
    
    // 响应式调整
    window.addEventListener('resize', () => {
      chartInstance.value && chartInstance.value.resize()
    })
  })
}

// 查看班级详情
const viewClassDetail = (classInfo) => {
  currentClass.value = classInfo
  detailDialogVisible.value = true
  getClassStudentDetail(classInfo.classId)
}

// 处理筛选条件变化
const handleFilterChange = () => {
  getRankingData()
}

// 处理排名类型变化
const handleRankingTypeChange = () => {
  getRankingData()
}

// 重置筛选条件
const resetFilter = () => {
  filterForm.semester = ''
  filterForm.classId = ''
  filterForm.subject = ''
  getRankingData()
}

// 导出排名数据
const exportRankingData = async () => {
  exporting.value = true
  try {
    const params = {
      semester: filterForm.semester,
      class_id: filterForm.classId,
      subject: filterForm.subject,
      type: rankingType.value
    }
    
    const res = await teacherAPI.exportClassRanking(params)
    
    // 创建下载链接
    const blob = new Blob([res])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `班级排名_${filterForm.semester || '全部'}_${new Date().toLocaleDateString()}.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

// 获取分数样式类
const getScoreClass = (score) => {
  if (score >= 90) return 'score-excellent'
  if (score >= 80) return 'score-good'
  if (score >= 60) return 'score-pass'
  return 'score-fail'
}

// 获取及格率标签类型
const getPassRateTagType = (passRate) => {
  if (passRate >= 90) return 'success'
  if (passRate >= 80) return ''
  if (passRate >= 60) return 'warning'
  return 'danger'
}

// 组件挂载时初始化数据
onMounted(() => {
  getClassOptions()
  getRankingData()
})
</script>

<style scoped>
.class-ranking {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-title {
  margin: 10px 0;
  font-size: 24px;
  font-weight: bold;
}

.filter-section {
  margin-bottom: 20px;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
}

.ranking-content {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ranking-table-card {
  margin-bottom: 20px;
}

.ranking-chart-card {
  margin-bottom: 20px;
}

.chart-container {
  height: 300px;
  width: 100%;
}

.ranking-summary-card {
  margin-bottom: 20px;
}

.summary-content {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.summary-label {
  font-weight: bold;
}

.summary-value {
  font-size: 18px;
  font-weight: bold;
  color: #409eff;
}

.score-excellent {
  color: #67c23a;
  font-weight: bold;
}

.score-good {
  color: #409eff;
  font-weight: bold;
}

.score-pass {
  color: #e6a23c;
}

.score-fail {
  color: #f56c6c;
  font-weight: bold;
}
</style>
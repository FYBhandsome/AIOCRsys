<template>
  <div class="score-analysis">
    <!-- 数据卡片 -->
    <el-row :gutter="20" class="data-cards">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="data-card card-primary">
          <div class="card-content">
            <div class="card-icon">📊</div>
            <div class="card-info">
              <div class="card-title">平均分</div>
              <div class="card-value">86.5</div>
              <div class="card-change positive">
                <el-icon><TrendCharts /></el-icon>
                +2.3%
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="data-card card-success">
          <div class="card-content">
            <div class="card-icon">🏆</div>
            <div class="card-info">
              <div class="card-title">最高分</div>
              <div class="card-value">98.5</div>
              <div class="card-change positive">
                <el-icon><Top /></el-icon>
                +1.2%
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="data-card card-warning">
          <div class="card-content">
            <div class="card-icon">✅</div>
            <div class="card-info">
              <div class="card-title">及格率</div>
              <div class="card-value">96.8%</div>
              <div class="card-change negative">
                <el-icon><Bottom /></el-icon>
                -0.5%
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="data-card card-info">
          <div class="card-content">
            <div class="card-icon">⭐</div>
            <div class="card-info">
              <div class="card-title">优秀率</div>
              <div class="card-value">42.3%</div>
              <div class="card-change positive">
                <el-icon><TrendCharts /></el-icon>
                +3.7%
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-tabs v-model="activeTab" class="analysis-tabs">
      <el-tab-pane name="radar">
        <template #label>
          <span class="tab-label">
            <el-icon><Compass /></el-icon>
            个人成长雷达图
          </span>
        </template>
        <div ref="radarChart" class="chart-container"></div>
      </el-tab-pane>
      <el-tab-pane name="ranking">
        <template #label>
          <span class="tab-label">
            <el-icon><Histogram /></el-icon>
            班级综测排行榜
          </span>
        </template>
        <div ref="rankingChart" class="chart-container"></div>
      </el-tab-pane>
      <el-tab-pane name="trend">
        <template #label>
          <span class="tab-label">
            <el-icon><TrendCharts /></el-icon>
            历史趋势对比
          </span>
        </template>
        <div ref="trendChart" class="chart-container"></div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { TrendCharts, Top, Bottom, Compass, Histogram } from '@element-plus/icons-vue'
import { studentAPI, teacherAPI } from '@/services/api'

const activeTab = ref('radar')
const radarChart = ref(null)
const rankingChart = ref(null)
const trendChart = ref(null)

// 数据状态
const loading = ref(false)
const error = ref(null)
const scoreStats = ref({
  average: 0,
  highest: 0,
  passRate: 0,
  excellenceRate: 0
})
const radarData = ref([])
const rankingData = ref([])
const trendData = ref([])

let radarChartInstance = null
let rankingChartInstance = null
let trendChartInstance = null

// 获取成绩统计数据
const fetchScoreStats = async () => {
  try {
    loading.value = true
    // 使用教师API获取班级成绩统计
    const response = await teacherAPI.getClassStats()
    scoreStats.value = {
      average: response.average || 0,
      highest: response.highest || 0,
      passRate: response.passRate || 0,
      excellenceRate: response.excellenceRate || 0
    }
  } catch (err) {
    console.error('获取成绩统计失败:', err)
    error.value = '获取成绩统计失败'
  } finally {
    loading.value = false
  }
}

// 获取雷达图数据
const fetchRadarData = async () => {
  try {
    // 使用学生API获取个人综测分析
    const response = await studentAPI.getComprehensiveAnalysis()
    radarData.value = response.dimensions || []
  } catch (err) {
    console.error('获取雷达图数据失败:', err)
    // 使用默认数据作为后备
    radarData.value = [
      { name: '学业成绩', value: 85, max: 100 },
      { name: '科研创新', value: 75, max: 100 },
      { name: '社会实践', value: 90, max: 100 },
      { name: '志愿服务', value: 95, max: 100 },
      { name: '文体活动', value: 80, max: 100 }
    ]
  }
}

// 获取班级排名数据
const fetchRankingData = async () => {
  try {
    // 使用教师API获取班级排名
    const response = await teacherAPI.getClassRanking()
    rankingData.value = response.ranking || []
  } catch (err) {
    console.error('获取班级排名数据失败:', err)
    // 使用默认数据作为后备
    rankingData.value = [
      { name: '张三', score: 95 },
      { name: '李四', score: 92 },
      { name: '王五', score: 90 },
      { name: '赵六', score: 88 },
      { name: '钱七', score: 85 },
      { name: '孙八', score: 82 },
      { name: '周九', score: 80 },
      { name: '吴十', score: 78 }
    ]
  }
}

// 获取趋势数据
const fetchTrendData = async () => {
  try {
    // 使用学生API获取历史趋势
    const response = await studentAPI.getScoreTrend()
    trendData.value = response.trend || []
  } catch (err) {
    console.error('获取趋势数据失败:', err)
    // 使用默认数据作为后备
    trendData.value = {
      current: [75, 78, 82, 85, 88, 90, 92, 93, 94, 95],
      previous: [70, 73, 76, 79, 82, 84, 86, 88, 90, 92]
    }
  }
}

// 初始化所有数据
const initData = async () => {
  await Promise.all([
    fetchScoreStats(),
    fetchRadarData(),
    fetchRankingData(),
    fetchTrendData()
  ])
}

const initChartWithRetry = (chartRef, initFn, maxRetries = 5) => {
  let retries = 0
  const tryInit = () => {
    if (!chartRef.value) {
      if (retries < maxRetries) {
        retries++
        setTimeout(tryInit, 100)
      }
      return
    }
    const { clientWidth, clientHeight } = chartRef.value
    if (clientWidth === 0 || clientHeight === 0) {
      if (retries < maxRetries) {
        retries++
        setTimeout(tryInit, 200)
      }
      return
    }
    initFn()
  }
  tryInit()
}

onMounted(async () => {
  await initData()
  await nextTick()
  setTimeout(() => {
    initChartWithRetry(radarChart, () => {
      radarChartInstance = echarts.init(radarChart.value)
      updateRadarChart()
    })
    initChartWithRetry(rankingChart, () => {
      rankingChartInstance = echarts.init(rankingChart.value)
      updateRankingChart()
    })
    initChartWithRetry(trendChart, () => {
      trendChartInstance = echarts.init(trendChart.value)
      updateTrendChart()
    })
  }, 100)
  
  const handleResize = () => {
    radarChartInstance?.resize()
    rankingChartInstance?.resize()
    trendChartInstance?.resize()
  }
  window.addEventListener('resize', handleResize)
  
  onUnmounted(() => {
    window.removeEventListener('resize', handleResize)
  })
})

// 更新雷达图
const updateRadarChart = () => {
  const indicators = radarData.value.map(item => ({
    name: item.name,
    max: item.max || 100
  }))
  
  const values = radarData.value.map(item => item.value || 0)
  
  radarChartInstance.setOption({
    title: {
      text: '个人成长雷达图',
      left: 'center'
    },
    radar: {
      indicator: indicators
    },
    series: [{
      type: 'radar',
      data: [{
        value: values,
        name: '个人综测'
      }]
    }]
  })
}

// 更新排行榜图
const updateRankingChart = () => {
  const names = rankingData.value.map(item => item.name)
  const scores = rankingData.value.map(item => item.score)
  
  rankingChartInstance.setOption({
    title: {
      text: '班级综测排行榜',
      left: 'center'
    },
    xAxis: {
      type: 'category',
      data: names
    },
    yAxis: {
      type: 'value'
    },
    series: [{
      data: scores,
      type: 'bar',
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#83bff6' },
          { offset: 0.5, color: '#188df0' },
          { offset: 1, color: '#188df0' }
        ])
      },
      emphasis: {
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#2378f7' },
            { offset: 0.7, color: '#2378f7' },
            { offset: 1, color: '#83bff6' }
          ])
        }
      }
    }]
  })
}

// 更新趋势图
const updateTrendChart = () => {
  const currentData = Array.isArray(trendData.value) ? trendData.value : trendData.value.current || []
  const previousData = Array.isArray(trendData.value) ? [] : trendData.value.previous || []
  
  trendChartInstance.setOption({
    title: {
      text: '历史趋势对比',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['当前学期', '上一学期']
    },
    xAxis: {
      type: 'category',
      data: ['9月', '10月', '11月', '12月', '1月', '2月', '3月', '4月', '5月', '6月']
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '当前学期',
        data: currentData,
        type: 'line',
        smooth: true
      },
      {
        name: '上一学期',
        data: previousData,
        type: 'line',
        smooth: true
      }
    ]
  })
}
</script>

<style scoped>
.score-analysis {
  padding: 20px;
}

/* 数据卡片 */
.data-cards {
  margin-bottom: 30px;
}

.data-card {
  border-radius: 16px;
  transition: all 0.3s ease;
  border: none;
  overflow: hidden;
}

.data-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.15);
}

.card-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.card-success {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.card-warning {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.card-info {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.data-card :deep(.el-card__body) {
  padding: 0;
}

.card-content {
  display: flex;
  align-items: center;
  padding: 25px;
  color: white;
}

.card-icon {
  font-size: 48px;
  margin-right: 20px;
  opacity: 0.9;
}

.card-info {
  flex: 1;
}

.card-title {
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 8px;
  font-weight: 500;
}

.card-value {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 5px;
}

.card-change {
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 4px;
  opacity: 0.95;
}

.card-change .el-icon {
  font-size: 16px;
}

.positive {
  color: rgba(255, 255, 255, 0.95);
}

.negative {
  color: rgba(255, 255, 255, 0.95);
}

/* 图表标签页 */
.analysis-tabs {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.analysis-tabs :deep(.el-tabs__header) {
  margin-bottom: 20px;
  border: none;
}

.analysis-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.analysis-tabs :deep(.el-tabs__item) {
  font-size: 15px;
  font-weight: 500;
  padding: 0 30px;
  height: 50px;
  line-height: 50px;
}

.analysis-tabs :deep(.el-tabs__item.is-active) {
  color: #667eea;
}

.analysis-tabs :deep(.el-tabs__active-bar) {
  height: 3px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  border-radius: 3px;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tab-label .el-icon {
  font-size: 18px;
}

/* 图表容器 */
.chart-container {
  width: 100%;
  height: 500px;
  border-radius: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .score-analysis {
    padding: 15px;
  }

  .data-card {
    margin-bottom: 15px;
  }

  .card-content {
    padding: 20px;
  }

  .card-icon {
    font-size: 36px;
    margin-right: 15px;
  }

  .card-value {
    font-size: 24px;
  }

  .chart-container {
    height: 350px;
  }

  .analysis-tabs :deep(.el-tabs__item) {
    padding: 0 15px;
    font-size: 13px;
  }

  .tab-label .el-icon {
    font-size: 16px;
  }
}
</style>
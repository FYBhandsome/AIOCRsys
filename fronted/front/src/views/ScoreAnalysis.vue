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
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { TrendCharts, Top, Bottom, Compass, Histogram } from '@element-plus/icons-vue'

const activeTab = ref('radar')
const radarChart = ref(null)
const rankingChart = ref(null)
const trendChart = ref(null)

let radarChartInstance = null
let rankingChartInstance = null
let trendChartInstance = null

onMounted(() => {
  // 初始化雷达图
  radarChartInstance = echarts.init(radarChart.value)
  radarChartInstance.setOption({
    title: {
      text: '个人成长雷达图',
      left: 'center'
    },
    radar: {
      indicator: [
        { name: '学业成绩', max: 100 },
        { name: '科研创新', max: 100 },
        { name: '社会实践', max: 100 },
        { name: '志愿服务', max: 100 },
        { name: '文体活动', max: 100 }
      ]
    },
    series: [{
      type: 'radar',
      data: [{
        value: [85, 75, 90, 95, 80],
        name: '个人综测'
      }]
    }]
  })
  
  // 初始化排行榜图
  rankingChartInstance = echarts.init(rankingChart.value)
  rankingChartInstance.setOption({
    title: {
      text: '班级综测排行榜',
      left: 'center'
    },
    xAxis: {
      type: 'category',
      data: ['张三', '李四', '王五', '赵六', '钱七', '孙八', '周九', '吴十']
    },
    yAxis: {
      type: 'value'
    },
    series: [{
      data: [95, 92, 90, 88, 85, 82, 80, 78],
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
  
  // 初始化趋势图
  trendChartInstance = echarts.init(trendChart.value)
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
        data: [75, 78, 82, 85, 88, 90, 92, 93, 94, 95],
        type: 'line',
        smooth: true
      },
      {
        name: '上一学期',
        data: [70, 73, 76, 79, 82, 84, 86, 88, 90, 92],
        type: 'line',
        smooth: true
      }
    ]
  })
  
  // 监听窗口大小变化，自适应图表
  const handleResize = () => {
    radarChartInstance?.resize()
    rankingChartInstance?.resize()
    trendChartInstance?.resize()
  }
  
  window.addEventListener('resize', handleResize)
  
  // 组件卸载时清理事件监听器
  onUnmounted(() => {
    window.removeEventListener('resize', handleResize)
  })
})
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
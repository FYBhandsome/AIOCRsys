<template>
  <div class="student-score-detail">
    <el-card class="score-summary-card">
      <template #header>
        <div class="card-header">
          <span>综测成绩总览</span>
          <el-button type="primary" size="small" @click="refreshData" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>
      
      <el-row :gutter="20" class="summary-row">
        <el-col :xs="12" :sm="6">
          <div class="summary-item">
            <div class="summary-icon total">
              <el-icon><Trophy /></el-icon>
            </div>
            <div class="summary-content">
              <div class="summary-value">{{ scoreData.total_score || 0 }}</div>
              <div class="summary-label">总分</div>
            </div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="6">
          <div class="summary-item">
            <div class="summary-icon academic">
              <el-icon><Reading /></el-icon>
            </div>
            <div class="summary-content">
              <div class="summary-value">{{ scoreData.b_total_score || 0 }}</div>
              <div class="summary-label">学业成绩</div>
            </div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="6">
          <div class="summary-item">
            <div class="summary-icon quality">
              <el-icon><Star /></el-icon>
            </div>
            <div class="summary-content">
              <div class="summary-value">{{ scoreData.a_total_score || 0 }}</div>
              <div class="summary-label">综合素质</div>
            </div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="6">
          <div class="summary-item">
            <div class="summary-icon bonus">
              <el-icon><Medal /></el-icon>
            </div>
            <div class="summary-content">
              <div class="summary-value">{{ scoreData.c_total_score || 0 }}</div>
              <div class="summary-label">奖励加分</div>
            </div>
          </div>
        </el-col>
      </el-row>
      
      <el-row :gutter="20" class="ranking-row">
        <el-col :span="12">
          <div class="ranking-info">
            <span class="ranking-label">班级排名：</span>
            <span class="ranking-value">{{ scoreData.ranking || '-' }}</span>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="ranking-info">
            <span class="ranking-label">学年学期：</span>
            <span class="ranking-value">{{ scoreData.academic_year || '-' }} 第{{ scoreData.semester || '-' }}学期</span>
          </div>
        </el-col>
      </el-row>
    </el-card>
    
    <el-card class="score-detail-card">
      <template #header>
        <div class="card-header">
          <span>成绩明细</span>
          <el-radio-group v-model="activeCategory" size="small">
            <el-radio-button label="all">全部</el-radio-button>
            <el-radio-button label="A">A类</el-radio-button>
            <el-radio-button label="B">B类</el-radio-button>
            <el-radio-button label="C">C类</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      
      <el-table :data="filteredDetails" v-loading="loading" stripe>
        <el-table-column prop="category_type" label="类别" width="80" align="center">
          <template #default="scope">
            <el-tag :type="getCategoryTagType(scope.row.category_type)">
              {{ scope.row.category_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="item_name" label="项目名称" min-width="200" />
        <el-table-column prop="description" label="说明" min-width="150" show-overflow-tooltip />
        <el-table-column prop="score" label="分数" width="100" align="center">
          <template #default="scope">
            <span :class="scope.row.score >= 0 ? 'score-positive' : 'score-negative'">
              {{ scope.row.score >= 0 ? '+' : '' }}{{ scope.row.score }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="记录时间" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
      
      <div v-if="!filteredDetails || filteredDetails.length === 0" class="empty-data">
        <el-empty description="暂无成绩明细" />
      </div>
    </el-card>
    
    <el-card class="score-trend-card">
      <template #header>
        <div class="card-header">
          <span>成绩趋势</span>
        </div>
      </template>
      
      <div ref="trendChartRef" class="trend-chart"></div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Trophy, Reading, Star, Medal } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { studentAPI } from '@/services/api'

const props = defineProps({
  studentId: {
    type: String,
    default: null
  },
  academicYear: {
    type: String,
    default: null
  },
  semester: {
    type: String,
    default: null
  }
})

const loading = ref(false)
const scoreData = ref({})
const scoreDetails = ref([])
const activeCategory = ref('all')
const trendChartRef = ref(null)
let trendChart = null

const filteredDetails = computed(() => {
  if (activeCategory.value === 'all') {
    return scoreDetails.value
  }
  return scoreDetails.value.filter(item => 
    item.category_type && item.category_type.startsWith(activeCategory.value)
  )
})

const loadScoreData = async () => {
  loading.value = true
  try {
    const params = {
      academic_year: props.academicYear,
      semester: props.semester
    }
    
    const [summaryRes, detailRes, trendRes] = await Promise.all([
      studentAPI.getScoresSummary().catch(() => null),
      studentAPI.getScoresDetail().catch(() => null),
      studentAPI.getScoreTrend().catch(() => null)
    ])
    
    if (summaryRes) {
      scoreData.value = summaryRes
    }
    
    if (detailRes && detailRes.details) {
      scoreDetails.value = detailRes.details
    }
    
    if (trendRes && trendRes.trend) {
      await nextTick()
      renderTrendChart(trendRes.trend)
    }
  } catch (error) {
    console.error('加载成绩数据失败:', error)
    ElMessage.error('加载成绩数据失败')
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  loadScoreData()
}

const getCategoryTagType = (category) => {
  const typeMap = {
    'A1': 'success',
    'A2': 'success',
    'A3': 'success',
    'B': 'primary',
    'C1': 'warning',
    'C2': 'warning',
    'C3': 'warning',
    'C4': 'warning'
  }
  return typeMap[category] || 'info'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const renderTrendChart = (trendData) => {
  if (!trendChartRef.value || !trendData) return
  
  if (trendChart) {
    trendChart.dispose()
  }
  
  trendChart = echarts.init(trendChartRef.value)
  
  const option = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['总分', '学业成绩', '综合素质', '奖励加分']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: trendData.map(item => item.academic_year)
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '总分',
        type: 'line',
        data: trendData.map(item => item.total_score),
        smooth: true,
        itemStyle: { color: '#409EFF' }
      },
      {
        name: '学业成绩',
        type: 'line',
        data: trendData.map(item => item.b_score),
        smooth: true,
        itemStyle: { color: '#67C23A' }
      },
      {
        name: '综合素质',
        type: 'line',
        data: trendData.map(item => item.a_score),
        smooth: true,
        itemStyle: { color: '#E6A23C' }
      },
      {
        name: '奖励加分',
        type: 'line',
        data: trendData.map(item => item.c_score),
        smooth: true,
        itemStyle: { color: '#F56C6C' }
      }
    ]
  }
  
  trendChart.setOption(option)
}

watch(() => [props.studentId, props.academicYear, props.semester], () => {
  loadScoreData()
})

onMounted(() => {
  loadScoreData()
})
</script>

<style scoped>
.student-score-detail {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.summary-row {
  margin-bottom: 20px;
}

.summary-item {
  display: flex;
  align-items: center;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.summary-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  font-size: 24px;
  color: white;
}

.summary-icon.total {
  background: linear-gradient(135deg, #409EFF, #66b1ff);
}

.summary-icon.academic {
  background: linear-gradient(135deg, #67C23A, #85ce61);
}

.summary-icon.quality {
  background: linear-gradient(135deg, #E6A23C, #ebb563);
}

.summary-icon.bonus {
  background: linear-gradient(135deg, #F56C6C, #f78989);
}

.summary-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.summary-label {
  font-size: 14px;
  color: #909399;
  margin-top: 5px;
}

.ranking-row {
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.ranking-info {
  display: flex;
  align-items: center;
}

.ranking-label {
  color: #909399;
  margin-right: 10px;
}

.ranking-value {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.score-detail-card {
  margin-top: 20px;
}

.score-positive {
  color: #67C23A;
  font-weight: bold;
}

.score-negative {
  color: #F56C6C;
  font-weight: bold;
}

.empty-data {
  padding: 40px;
}

.score-trend-card {
  margin-top: 20px;
}

.trend-chart {
  height: 300px;
}
</style>

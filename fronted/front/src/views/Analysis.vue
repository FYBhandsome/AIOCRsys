<template>
  <div class="analysis">
    <el-card class="result-card">
      <template #header>
        <div class="card-header">
          <h2>综测结果分析</h2>
          <p>个人成长雷达图 + 班级排名对比</p>
        </div>
      </template>
      
      <el-tabs v-model="activeTab" class="analysis-tabs">
        <el-tab-pane label="个人成长雷达图" name="radar">
          <div ref="radarChart" class="chart-container"></div>
        </el-tab-pane>
        <el-tab-pane label="班级排名对比" name="ranking">
          <div ref="rankingChart" class="chart-container"></div>
        </el-tab-pane>
        <el-tab-pane label="历史趋势分析" name="trend">
          <div ref="trendChart" class="chart-container"></div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
    
    <el-row :gutter="20" class="summary-cards">
      <el-col :span="8">
        <el-card class="summary-card">
          <div class="summary-content">
            <div class="summary-title">综测总分</div>
            <div class="summary-value">86.5</div>
            <div class="summary-change positive">+2.3分 ↑</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="summary-card">
          <div class="summary-content">
            <div class="summary-title">班级排名</div>
            <div class="summary-value">第8名</div>
            <div class="summary-change negative">↓ 2名</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="summary-card">
          <div class="summary-content">
            <div class="summary-title">年级排名</div>
            <div class="summary-value">前15%</div>
            <div class="summary-change positive">↑ 5% ↑</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-card class="details-card">
      <template #header>
        <div class="card-header">
          <h3>得分明细</h3>
        </div>
      </template>
      
      <el-table :data="scoreDetails" style="width: 100%">
        <el-table-column prop="category" label="类别" width="150"></el-table-column>
        <el-table-column prop="score" label="得分" width="100"></el-table-column>
        <el-table-column prop="details" label="详细说明">
          <template #default="scope">
            <div v-for="(detail, index) in scope.row.details" :key="index" class="detail-item">
              {{ detail }}
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'

const activeTab = ref('radar')
const radarChart = ref(null)
const rankingChart = ref(null)
const trendChart = ref(null)

const scoreDetails = ref([
  {
    category: '学业成绩',
    score: '85.0',
    details: [
      '第一学期平均分: 83.5',
      '第二学期平均分: 86.5',
      '学业进步加分: 2.0'
    ]
  },
  {
    category: '德育表现',
    score: '18.0',
    details: [
      '思想品德考核: 10.0',
      '集体活动参与: 5.0',
      '志愿服务时长(30小时): 3.0'
    ]
  },
  {
    category: '科研创新',
    score: '12.0',
    details: [
      '英语竞赛省级二等奖: 8.0',
      '校级科技创新项目参与: 4.0'
    ]
  },
  {
    category: '文体活动',
    score: '10.0',
    details: [
      '校运动会参与: 3.0',
      '文艺演出参与: 4.0',
      '社团活动表现: 3.0'
    ]
  },
  {
    category: '社会实践',
    score: '8.0',
    details: [
      '暑期社会实践: 5.0',
      '社会调研报告: 3.0'
    ]
  }
])

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
        { name: '德育表现', max: 30 },
        { name: '科研创新', max: 30 },
        { name: '文体活动', max: 20 },
        { name: '社会实践', max: 20 }
      ]
    },
    series: [{
      type: 'radar',
      data: [{
        value: [85, 18, 12, 10, 8],
        name: '个人综测',
        areaStyle: {
          color: new echarts.graphic.RadialGradient(0.1, 0.6, 1, [
            { color: 'rgba(102, 126, 234, 0.1)', offset: 0 },
            { color: 'rgba(118, 75, 162, 0.8)', offset: 1 }
          ])
        }
      }]
    }]
  })
  
  // 初始化排行榜图
  rankingChartInstance = echarts.init(rankingChart.value)
  rankingChartInstance.setOption({
    title: {
      text: '班级综测排名',
      left: 'center'
    },
    xAxis: {
      type: 'category',
      data: ['张三', '李四', '王五', '赵六', '钱七', '孙八', '周九', '你', '吴十']
    },
    yAxis: {
      type: 'value',
      name: '综测分数'
    },
    series: [{
      data: [95, 92, 90, 88, 85, 82, 80, 86.5, 78],
      type: 'bar',
      itemStyle: {
        color: function(params) {
          // 当前用户高亮显示
          return params.dataIndex === 7 ? '#409EFF' : '#667eea'
        }
      },
      barWidth: 40
    }]
  })
  
  // 初始化趋势图
  trendChartInstance = echarts.init(trendChart.value)
  trendChartInstance.setOption({
    title: {
      text: '综测分数历史趋势',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['你的分数', '班级平均分']
    },
    xAxis: {
      type: 'category',
      data: ['大一上', '大一下', '大二上', '大二下', '大三上']
    },
    yAxis: {
      type: 'value',
      name: '综测分数'
    },
    series: [
      {
        name: '你的分数',
        data: [75, 78, 82, 85, 86.5],
        type: 'line',
        smooth: true,
        itemStyle: { color: '#409EFF' }
      },
      {
        name: '班级平均分',
        data: [70, 73, 76, 79, 82],
        type: 'line',
        smooth: true,
        itemStyle: { color: '#667eea' }
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
})
</script>

<style scoped>
.analysis {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.result-card {
  margin-bottom: 30px;
}

.card-header h2 {
  margin: 0 0 10px 0;
  color: #333;
}

.card-header p {
  margin: 0;
  color: #666;
}

.chart-container {
  width: 100%;
  height: 500px;
  padding: 20px;
}

.summary-cards {
  margin-bottom: 30px;
}

.summary-card {
  text-align: center;
}

.summary-content {
  padding: 20px 0;
}

.summary-title {
  font-size: 16px;
  color: #666;
  margin-bottom: 10px;
}

.summary-value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
  margin-bottom: 10px;
}

.summary-change {
  font-size: 14px;
}

.positive {
  color: #67C23A;
}

.negative {
  color: #F56C6C;
}

.details-card {
  margin-top: 30px;
}

.detail-item {
  margin-bottom: 5px;
  color: #666;
}

.detail-item:last-child {
  margin-bottom: 0;
}
</style>
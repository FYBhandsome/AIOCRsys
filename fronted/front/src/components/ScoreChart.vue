<template>
  <div ref="chartRef" class="score-chart"></div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  // 图表数据
  data: {
    type: Object,
    default: () => ({})
  },
  // 图表类型：bar, line, pie, radar
  type: {
    type: String,
    default: 'bar'
  },
  // 图表标题
  title: {
    type: String,
    default: ''
  },
  // 图表高度
  height: {
    type: String,
    default: '400px'
  }
})

const chartRef = ref(null)
let chartInstance = null

// 初始化图表
const initChart = () => {
  if (!chartRef.value) return

  // 如果已存在实例，先销毁
  if (chartInstance) {
    chartInstance.dispose()
  }

  chartInstance = echarts.init(chartRef.value)
  updateChart()
}

// 更新图表
const updateChart = () => {
  if (!chartInstance) return

  let option = {}

  switch (props.type) {
    case 'bar':
      option = getBarOption()
      break
    case 'line':
      option = getLineOption()
      break
    case 'pie':
      option = getPieOption()
      break
    case 'radar':
      option = getRadarOption()
      break
    default:
      option = getBarOption()
  }

  chartInstance.setOption(option, true)
}

// 柱状图配置
const getBarOption = () => {
  return {
    title: {
      text: props.title,
      left: 'center',
      textStyle: {
        fontSize: 18,
        fontWeight: 600,
        color: '#2c3e50'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params) => {
        const item = params[0]
        return `${item.axisValue}<br/>${item.marker}${item.seriesName}: ${item.value}`
      }
    },
    legend: {
      bottom: 10,
      data: props.data.series?.map(s => s.name) || []
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: props.data.categories || [],
      axisLabel: {
        rotate: props.data.categories?.length > 10 ? 45 : 0,
        interval: 0,
        fontSize: 12
      }
    },
    yAxis: {
      type: 'value',
      name: props.data.yAxisName || '分数',
      nameTextStyle: {
        fontSize: 14,
        padding: [0, 0, 0, 50]
      }
    },
    series: (props.data.series || []).map(item => ({
      name: item.name,
      type: 'bar',
      data: item.data,
      itemStyle: {
        borderRadius: [8, 8, 0, 0],
        color: item.color || undefined
      },
      barMaxWidth: 40,
      emphasis: {
        focus: 'series',
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }))
  }
}

// 折线图配置
const getLineOption = () => {
  return {
    title: {
      text: props.title,
      left: 'center',
      textStyle: {
        fontSize: 18,
        fontWeight: 600,
        color: '#2c3e50'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      bottom: 10,
      data: props.data.series?.map(s => s.name) || []
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: props.data.categories || []
    },
    yAxis: {
      type: 'value',
      name: props.data.yAxisName || '分数'
    },
    series: (props.data.series || []).map(item => ({
      name: item.name,
      type: 'line',
      data: item.data,
      smooth: true,
      symbolSize: 8,
      lineStyle: {
        width: 3
      },
      itemStyle: {
        color: item.color || undefined
      },
      areaStyle: item.showArea ? {
        opacity: 0.3
      } : undefined
    }))
  }
}

// 饼图配置
const getPieOption = () => {
  return {
    title: {
      text: props.title,
      left: 'center',
      textStyle: {
        fontSize: 18,
        fontWeight: 600,
        color: '#2c3e50'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'horizontal',
      bottom: 10,
      data: props.data.data?.map(d => d.name) || []
    },
    series: [
      {
        name: props.data.name || '数据',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}: {d}%'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          },
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        },
        data: props.data.data || []
      }
    ]
  }
}

// 雷达图配置
const getRadarOption = () => {
  return {
    title: {
      text: props.title,
      left: 'center',
      textStyle: {
        fontSize: 18,
        fontWeight: 600,
        color: '#2c3e50'
      }
    },
    tooltip: {
      trigger: 'item'
    },
    legend: {
      bottom: 10,
      data: props.data.series?.map(s => s.name) || []
    },
    radar: {
      indicator: props.data.indicators || [],
      shape: 'polygon',
      splitNumber: 5,
      name: {
        textStyle: {
          fontSize: 14,
          color: '#666'
        }
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(0, 0, 0, 0.1)'
        }
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: ['rgba(64, 158, 255, 0.1)', 'rgba(64, 158, 255, 0.05)']
        }
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(0, 0, 0, 0.15)'
        }
      }
    },
    series: [
      {
        type: 'radar',
        data: (props.data.series || []).map(item => ({
          name: item.name,
          value: item.data,
          itemStyle: {
            color: item.color || undefined
          },
          lineStyle: {
            width: 2
          },
          areaStyle: {
            opacity: 0.5
          }
        }))
      }
    ]
  }
}

// 监听数据变化
watch(() => props.data, () => {
  updateChart()
}, { deep: true })

// 监听窗口大小变化
const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
  }
})
</script>

<style scoped>
.score-chart {
  width: 100%;
  height: v-bind(height);
  min-height: 300px;
}
</style>


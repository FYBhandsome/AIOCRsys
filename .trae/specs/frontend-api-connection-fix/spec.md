# 前后端API连接测试与前端优化规范

## Why

前端应用存在多个严重错误，包括Vue组件图表变量未定义、ECharts渲染失败、以及多个后端API返回500错误，导致系统无法正常运行。需要进行全面的API连接测试和前端代码优化。

## What Changes

- 修复ScoreVisualization.vue图表变量未定义错误
- 修复ScoreAnalysis.vue ECharts渲染问题
- 修复后端API 500错误（vector-db/stats、admin/ai/config、admin/prompts）
- 优化前端错误处理机制
- 确保开发模式下无认证障碍
- 提升前端加载性能和用户体验

## Impact

- Affected specs: 前端图表组件、后端API端点、错误处理机制
- Affected code:
  - `fronted/front/src/views/student/ScoreVisualization.vue` - 成绩可视化组件
  - `fronted/front/src/views/teacher/ScoreAnalysis.vue` - 成绩分析组件
  - `fronted/front/src/views/admin/VectorDBManager.vue` - 向量数据库管理
  - `fronted/front/src/views/admin/SystemSettings.vue` - 系统设置
  - `fronted/front/src/views/admin/PromptManager.vue` - Prompt管理
  - `visual_model/app/api/admin.py` - 管理员API
  - `visual_model/app/services/rag_client.py` - RAG客户端
  - `PaddleOCRRAG/app/api/system_routes.py` - RAG系统路由
  - `PaddleOCRRAG/app/api/vector_db_routes.py` - 向量数据库路由

## ADDED Requirements

### Requirement: 图表组件变量初始化

系统 SHALL 确保所有Vue组件中的图表变量在使用前正确初始化。

#### Scenario: ScoreVisualization图表初始化
- **WHEN** ScoreVisualization组件挂载时
- **THEN** rankingChart和trendChart变量应被正确初始化为null
- **AND** 图表实例应在DOM元素可用后创建
- **AND** 组件卸载时应正确销毁图表实例

#### Scenario: ScoreAnalysis图表初始化
- **WHEN** ScoreAnalysis组件挂载时
- **THEN** 所有ECharts实例应在DOM元素尺寸确定后初始化
- **AND** 应处理DOM元素尺寸为0的情况
- **AND** 应添加resize事件监听器

### Requirement: 后端API错误修复

系统 SHALL 确保所有后端API端点正确响应请求。

#### Scenario: 向量数据库统计API
- **WHEN** 前端请求 `/api/v1/vector-db/stats`
- **THEN** 后端应返回正确的统计信息
- **AND** 响应状态码应为200
- **AND** 数据格式应符合前端期望

#### Scenario: AI配置API
- **WHEN** 前端请求 `/v1/admin/ai/config`
- **THEN** 后端应正确调用RAG服务
- **AND** RAG服务应返回LLM配置
- **AND** 错误时应返回友好的错误信息

#### Scenario: Prompt配置API
- **WHEN** 前端请求 `/v1/admin/prompts`
- **THEN** 后端应正确调用RAG服务
- **AND** RAG服务应返回Prompt配置
- **AND** 错误时应返回友好的错误信息

### Requirement: 前端错误处理增强

系统 SHALL 提供完善的错误处理机制。

#### Scenario: API请求失败处理
- **WHEN** API请求失败时
- **THEN** 前端应显示友好的错误提示
- **AND** 不应在控制台产生未捕获的异常
- **AND** 应提供重试机制

#### Scenario: 图表渲染失败处理
- **WHEN** 图表渲染失败时
- **THEN** 应显示占位内容或错误提示
- **AND** 不应影响其他组件的正常运行
- **AND** 应记录错误日志

### Requirement: 开发模式无认证

系统 SHALL 在开发模式下无需认证即可访问所有功能。

#### Scenario: 开发模式API访问
- **WHEN** 系统以开发模式启动
- **THEN** 所有API应无需认证即可访问
- **AND** 应返回模拟用户数据
- **AND** 应在日志中标记开发模式

### Requirement: 前端性能优化

系统 SHALL 优化前端加载性能和用户体验。

#### Scenario: 组件懒加载
- **WHEN** 用户访问应用时
- **THEN** 非首屏组件应懒加载
- **AND** 应显示加载状态
- **AND** 首屏加载时间应小于3秒

#### Scenario: 图表性能优化
- **WHEN** 渲染大量数据图表时
- **THEN** 应使用数据采样或分页
- **AND** 应避免阻塞主线程
- **AND** 应提供数据导出功能

## MODIFIED Requirements

### Requirement: ScoreVisualization.vue图表变量定义

原 `fronted/front/src/views/student/ScoreVisualization.vue` SHALL 正确定义图表变量：

**修改前：**
```javascript
// 变量未定义或定义位置错误
const initRankingChart = () => {
  rankingChart.setOption({...})  // rankingChart未定义
}
```

**修改后：**
```javascript
// 在script setup顶部定义
let rankingChart = null
let trendChart = null

const initRankingChart = () => {
  if (!rankingChartRef.value) return
  rankingChart = echarts.init(rankingChartRef.value)
  rankingChart.setOption({...})
}

onUnmounted(() => {
  rankingChart?.dispose()
  trendChart?.dispose()
})
```

### Requirement: ScoreAnalysis.vue ECharts初始化

原 `fronted/front/src/views/teacher/ScoreAnalysis.vue` SHALL 正确处理ECharts初始化时机：

**修改前：**
```javascript
// 可能在DOM尺寸为0时初始化
onMounted(() => {
  initCharts()
})
```

**修改后：**
```javascript
onMounted(() => {
  nextTick(() => {
    // 确保DOM已渲染完成
    setTimeout(() => {
      initCharts()
    }, 100)
  })
})

const initCharts = () => {
  const dom = chartRef.value
  if (!dom || dom.clientWidth === 0 || dom.clientHeight === 0) {
    console.warn('图表容器尺寸为0，延迟初始化')
    setTimeout(initCharts, 200)
    return
  }
  // 初始化图表
}
```

## REMOVED Requirements

无移除的需求。

## 错误清单与优先级

### P0 - 严重问题（立即修复）

1. `ScoreVisualization.vue` - `rankingChart is not defined`
2. `ScoreVisualization.vue` - `trendChart is not defined`
3. `/api/v1/vector-db/stats` - 500错误
4. `/v1/admin/ai/config` - 500错误
5. `/v1/admin/prompts` - 500错误

### P1 - 高优先级（本周修复）

1. `ScoreAnalysis.vue` - ECharts DOM尺寸为0
2. `ScoreAnalysis.vue` - `Cannot read properties of undefined (reading 'push')`
3. 前端错误处理机制不完善

### P2 - 中优先级（两周内修复）

1. 前端组件懒加载优化
2. 图表性能优化
3. 开发模式体验优化

## 技术方案

### 1. 图表变量初始化修复

```javascript
// ScoreVisualization.vue
<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'

// 正确定义图表变量
let rankingChart = null
let trendChart = null

const rankingChartRef = ref(null)
const trendChartRef = ref(null)

const initRankingChart = () => {
  if (!rankingChartRef.value) return
  
  // 销毁旧实例
  rankingChart?.dispose()
  
  rankingChart = echarts.init(rankingChartRef.value)
  rankingChart.setOption({
    // 配置项
  })
}

onUnmounted(() => {
  rankingChart?.dispose()
  trendChart?.dispose()
})
</script>
```

### 2. ECharts初始化时机处理

```javascript
// ScoreAnalysis.vue
const initCharts = () => {
  const dom = chartRef.value
  if (!dom) {
    console.warn('图表DOM不存在')
    return
  }
  
  const { clientWidth, clientHeight } = dom
  if (clientWidth === 0 || clientHeight === 0) {
    console.warn('图表容器尺寸为0，延迟初始化')
    setTimeout(initCharts, 200)
    return
  }
  
  try {
    chart.value = echarts.init(dom)
    chart.value.setOption(option)
  } catch (error) {
    console.error('图表初始化失败:', error)
  }
}

onMounted(() => {
  nextTick(() => {
    setTimeout(initCharts, 100)
  })
})
```

### 3. API错误处理增强

```javascript
// api.js
const handleErrorResponse = async (error, name = 'API') => {
  const { response, config, message } = error
  
  // 记录详细错误信息
  console.error(`[${name} Error]`, {
    url: config?.url,
    method: config?.method,
    status: response?.status,
    message: message
  })
  
  // 开发模式下显示更详细的错误
  if (import.meta.env.DEV) {
    console.error('Response data:', response?.data)
  }
  
  // 友好的错误提示
  const errorMsg = getErrorMessage(response?.status, response?.data)
  ElMessage.error(errorMsg)
  
  return Promise.reject(error)
}
```

## 验收标准

1. ✅ 前端应用无控制台错误
2. ✅ 所有图表正确渲染
3. ✅ 所有API端点返回正确响应
4. ✅ 开发模式下无需认证
5. ✅ 错误提示友好且明确

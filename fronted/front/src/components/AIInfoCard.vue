<template>
  <div class="ai-info-card">
    <el-card class="info-card">
      <template #header>
        <div class="card-header">
          <h3>{{ title }}</h3>
        </div>
      </template>
      
      <div class="info-content">
        <p>{{ introText }}</p>
        <ol>
          <li v-for="step in steps" :key="step">{{ step }}</li>
        </ol>
        
        <div v-if="example" class="example">
          <h4>识别示例：</h4>
          <p>{{ example.input }}</p>
          <p>{{ example.output }}</p>
        </div>
        
        <div class="tech-stack">
          <el-tag 
            v-for="tag in techTags" 
            :key="tag.text" 
            :type="tag.type"
          >
            {{ tag.text }}
          </el-tag>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
// 定义props
const props = defineProps({
  title: {
    type: String,
    default: 'AI 智能识别说明'
  },
  introText: {
    type: String,
    default: '系统将通过以下方式处理您的证明材料：'
  },
  steps: {
    type: Array,
    default: () => [
      '使用 OCR 技术提取材料中的文字信息',
      '通过大模型理解材料内容和类型',
      '自动匹配综测规则中的对应加分项',
      '生成结构化数据用于综测计算'
    ]
  },
  example: {
    type: Object,
    default: null
  },
  techTags: {
    type: Array,
    default: () => [
      { text: 'OCR 识别', type: 'primary' },
      { text: '大模型分类', type: 'success' },
      { text: '规则匹配', type: 'warning' }
    ]
  }
})
</script>

<style scoped>
.ai-info-card {
  margin-bottom: 20px;
}

.info-card {
  background-color: #f8f9fa;
}

.info-content ol {
  padding-left: 20px;
}

.info-content li {
  margin-bottom: 10px;
  line-height: 1.6;
}

.example {
  background: white;
  padding: 15px;
  border-radius: 8px;
  margin: 20px 0;
}

.example h4 {
  margin-top: 0;
  color: #333;
}

.tech-stack {
  margin-top: 20px;
}

.tech-stack .el-tag {
  margin-right: 10px;
}
</style>
<template>
  <div class="home">
    <div class="hero-section">
      <h1 class="hero-title">🎓 综测计算助手</h1>
      <p class="hero-subtitle">让 AI 替你算综测：上传材料 → 自动识别 → 智能打分</p>
      
      <div class="hero-buttons">
        <el-button type="primary" size="large" @click="$router.push('/upload-rule')">
          上传综测规则
        </el-button>
        <el-button type="success" size="large" @click="$router.push('/upload-score')">
          上传成绩单
        </el-button>
        <el-button type="warning" size="large" @click="$router.push('/upload-material')">
          上传证明材料
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
// 移除了不再需要的图标导入
</script>

<style scoped>
.home {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.hero-section {
  text-align: center;
  padding: 60px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
  margin-bottom: 40px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.hero-title {
  font-size: 3rem;
  font-weight: 700;
  margin-bottom: 20px;
}

.hero-subtitle {
  font-size: 1.2rem;
  margin-bottom: 40px;
  opacity: 0.9;
}

.hero-buttons .el-button {
  margin: 0 10px;
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 2rem;
  }
  
  .hero-subtitle {
    font-size: 1rem;
  }
  
  .hero-buttons .el-button {
    display: block;
    margin: 10px auto;
    width: 80%;
  }
}
</style>
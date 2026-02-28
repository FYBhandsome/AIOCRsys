<template>
  <div class="home-page">
    <section class="hero-section">
      <div class="hero-background">
        <div class="hero-gradient"></div>
        <div class="hero-pattern"></div>
      </div>
      
      <div class="hero-content">
        <div class="hero-badge">
          <span class="badge-icon">✨</span>
          <span class="badge-text">AI 驱动的智能评分</span>
        </div>
        
        <h1 class="hero-title">
          <span class="title-emoji">🎓</span>
          <span class="title-text">综测计算助手</span>
        </h1>
        
        <p class="hero-subtitle">
          让 AI 替你算综测：上传材料 → 自动识别 → 智能打分
        </p>
        
        <div class="hero-features">
          <div class="feature-item">
            <div class="feature-icon">📤</div>
            <span class="feature-text">一键上传</span>
          </div>
          <div class="feature-item">
            <div class="feature-icon">🤖</div>
            <span class="feature-text">AI识别</span>
          </div>
          <div class="feature-item">
            <div class="feature-icon">📊</div>
            <span class="feature-text">智能评分</span>
          </div>
        </div>
        
        <div class="hero-actions">
          <el-button class="action-btn primary" size="large" @click="$router.push('/upload-rule')">
            <el-icon><Document /></el-icon>
            上传综测规则
          </el-button>
          <el-button class="action-btn success" size="large" @click="$router.push('/upload-score')">
            <el-icon><TrendCharts /></el-icon>
            上传成绩单
          </el-button>
          <el-button class="action-btn warning" size="large" @click="$router.push('/upload-material')">
            <el-icon><FolderOpened /></el-icon>
            上传证明材料
          </el-button>
        </div>
      </div>
    </section>
    
    <section class="stats-section">
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon gradient-purple">
            <el-icon><User /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">1,234</div>
            <div class="stat-label">活跃用户</div>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon gradient-blue">
            <el-icon><Document /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">5,678</div>
            <div class="stat-label">处理文档</div>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon gradient-green">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">98.5%</div>
            <div class="stat-label">识别准确率</div>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon gradient-orange">
            <el-icon><Timer /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">3s</div>
            <div class="stat-label">平均处理时间</div>
          </div>
        </div>
      </div>
    </section>
    
    <section class="guide-section">
      <h2 class="section-title">使用指南</h2>
      
      <div class="guide-grid">
        <div class="guide-card">
          <div class="guide-step">01</div>
          <h3 class="guide-title">上传综测规则</h3>
          <p class="guide-desc">上传学校综测规则文档，系统将自动解析并建立评分标准</p>
        </div>
        
        <div class="guide-card">
          <div class="guide-step">02</div>
          <h3 class="guide-title">上传成绩单</h3>
          <p class="guide-desc">上传学业成绩表格，系统自动计算学业成绩得分</p>
        </div>
        
        <div class="guide-card">
          <div class="guide-step">03</div>
          <h3 class="guide-title">上传证明材料</h3>
          <p class="guide-desc">上传竞赛证书、社会实践等证明材料，AI自动识别并评分</p>
        </div>
        
        <div class="guide-card">
          <div class="guide-step">04</div>
          <h3 class="guide-title">查看综测结果</h3>
          <p class="guide-desc">系统自动汇总各项得分，生成完整综测报告</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { Document, TrendCharts, FolderOpened, User, CircleCheck, Timer } from '@element-plus/icons-vue'
</script>

<style scoped>
.home-page {
  min-height: 100%;
  padding: var(--spacing-6);
}

.hero-section {
  position: relative;
  border-radius: var(--radius-3xl);
  overflow: hidden;
  margin-bottom: var(--spacing-8);
}

.hero-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--gradient-primary);
}

.hero-gradient {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at 30% 50%, rgba(255, 255, 255, 0.1) 0%, transparent 50%);
}

.hero-pattern {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    radial-gradient(circle at 20% 80%, rgba(255, 255, 255, 0.05) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(255, 255, 255, 0.08) 0%, transparent 40%);
  animation: pattern-float 20s ease-in-out infinite;
}

@keyframes pattern-float {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-20px) scale(1.05); }
}

.hero-content {
  position: relative;
  z-index: 1;
  padding: var(--spacing-16) var(--spacing-8);
  text-align: center;
  color: white;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-4);
  background: rgba(255, 255, 255, 0.15);
  border-radius: var(--radius-full);
  backdrop-filter: blur(10px);
  margin-bottom: var(--spacing-6);
}

.badge-icon {
  font-size: 16px;
}

.badge-text {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.hero-title {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-4);
  font-size: var(--font-size-5xl);
  font-weight: var(--font-weight-bold);
  margin-bottom: var(--spacing-4);
  text-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.title-emoji {
  font-size: 3.5rem;
  animation: bounce 2s ease-in-out infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.title-text {
  background: linear-gradient(135deg, #ffffff 0%, #e0e7ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: var(--font-size-xl);
  opacity: 0.9;
  margin-bottom: var(--spacing-8);
  max-width: 500px;
  margin-left: auto;
  margin-right: auto;
}

.hero-features {
  display: flex;
  justify-content: center;
  gap: var(--spacing-8);
  margin-bottom: var(--spacing-10);
}

.feature-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-2);
}

.feature-icon {
  font-size: 32px;
  background: rgba(255, 255, 255, 0.15);
  padding: var(--spacing-3);
  border-radius: var(--radius-xl);
  backdrop-filter: blur(10px);
}

.feature-text {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  opacity: 0.9;
}

.hero-actions {
  display: flex;
  justify-content: center;
  gap: var(--spacing-4);
  flex-wrap: wrap;
}

.action-btn {
  padding: var(--spacing-4) var(--spacing-6);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  border-radius: var(--radius-xl);
  border: none;
  transition: all var(--transition-fast);
}

.action-btn.primary {
  background: white;
  color: var(--color-primary-600);
}

.action-btn.primary:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.action-btn.success {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.action-btn.success:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-3px);
}

.action-btn.warning {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.action-btn.warning:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-3px);
}

.stats-section {
  margin-bottom: var(--spacing-8);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-4);
}

.stat-card {
  background: var(--bg-primary);
  border-radius: var(--radius-2xl);
  padding: var(--spacing-6);
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
  box-shadow: var(--shadow-md);
  border: 1px solid var(--border-light);
  transition: all var(--transition-normal);
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-xl);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-xl);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.stat-icon.gradient-purple {
  background: var(--gradient-primary);
}

.stat-icon.gradient-blue {
  background: var(--gradient-accent);
}

.stat-icon.gradient-green {
  background: var(--gradient-success);
}

.stat-icon.gradient-orange {
  background: var(--gradient-warning);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

.guide-section {
  background: var(--bg-primary);
  border-radius: var(--radius-3xl);
  padding: var(--spacing-8);
  box-shadow: var(--shadow-md);
  border: 1px solid var(--border-light);
}

.section-title {
  text-align: center;
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-8);
}

.guide-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-6);
}

.guide-card {
  text-align: center;
  padding: var(--spacing-6);
  border-radius: var(--radius-2xl);
  background: var(--bg-secondary);
  transition: all var(--transition-normal);
}

.guide-card:hover {
  background: var(--bg-tertiary);
  transform: translateY(-4px);
}

.guide-step {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background: var(--gradient-primary);
  color: white;
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  border-radius: 50%;
  margin-bottom: var(--spacing-4);
}

.guide-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-2);
}

.guide-desc {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  line-height: var(--line-height-relaxed);
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .guide-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .home-page {
    padding: var(--spacing-4);
  }
  
  .hero-content {
    padding: var(--spacing-10) var(--spacing-4);
  }
  
  .hero-title {
    font-size: var(--font-size-3xl);
    flex-direction: column;
  }
  
  .title-emoji {
    font-size: 2.5rem;
  }
  
  .hero-subtitle {
    font-size: var(--font-size-base);
  }
  
  .hero-features {
    gap: var(--spacing-4);
  }
  
  .feature-icon {
    font-size: 24px;
    padding: var(--spacing-2);
  }
  
  .hero-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .action-btn {
    width: 100%;
    max-width: 280px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .guide-grid {
    grid-template-columns: 1fr;
  }
  
  .guide-section {
    padding: var(--spacing-6);
  }
}

@media (max-width: 480px) {
  .hero-content {
    padding: var(--spacing-8) var(--spacing-3);
  }
  
  .hero-title {
    font-size: var(--font-size-2xl);
  }
  
  .hero-features {
    display: none;
  }
}
</style>

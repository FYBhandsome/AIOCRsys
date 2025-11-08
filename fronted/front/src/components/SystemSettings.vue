<template>
  <div class="system-settings">
    <!-- 标签页导航 -->
    <el-tabs v-model="activeTab" class="settings-tabs">
      <!-- 基础设置 -->
      <el-tab-pane label="基础设置" name="basic">
        <el-form :model="settings" label-width="180px" label-position="left">
          <el-card class="settings-card">
            <template #header>
              <div class="card-header">
                <el-icon><Setting /></el-icon>
                <span>基础配置</span>
              </div>
            </template>
            
            <el-form-item label="系统名称">
              <el-input v-model="settings.systemName" placeholder="综测计算助手" />
            </el-form-item>
            
            <el-form-item label="学校名称">
              <el-input v-model="settings.schoolName" placeholder="请输入学校名称" />
            </el-form-item>
            
            <el-form-item label="学期设置">
              <el-select v-model="settings.currentSemester" style="width: 100%">
                <el-option label="2023-2024学年第一学期" value="2023-1" />
                <el-option label="2023-2024学年第二学期" value="2023-2" />
                <el-option label="2024-2025学年第一学期" value="2024-1" />
                <el-option label="2024-2025学年第二学期" value="2024-2" />
              </el-select>
            </el-form-item>
          </el-card>

          <!-- 保存按钮 -->
          <div class="action-buttons">
            <el-button type="primary" size="large" @click="saveBasicSettings">
              <el-icon><Select /></el-icon>
              保存设置
            </el-button>
            <el-button size="large" @click="resetBasicSettings">
              重置
            </el-button>
          </div>
        </el-form>
      </el-tab-pane>

      <!-- AI大模型配置 -->
      <el-tab-pane label="AI大模型" name="ai">
        <el-form :model="aiConfig" label-width="180px" label-position="left" v-loading="aiLoading">
          <el-card class="settings-card">
            <template #header>
              <div class="card-header">
                <el-icon><MagicStick /></el-icon>
                <span>AI大模型配置</span>
                <div class="header-actions">
                  <el-button 
                    type="info" 
                    size="small" 
                    @click="loadAIConfig"
                    :loading="aiLoading"
                  >
                    <el-icon><Refresh /></el-icon>
                    刷新
                  </el-button>
                  <el-button 
                    type="success" 
                    size="small" 
                    @click="testAIConnection"
                    :loading="testing"
                  >
                    <el-icon><Connection /></el-icon>
                    测试连接
                  </el-button>
                </div>
              </div>
            </template>
            
            <el-form-item label="启用AI">
              <el-switch v-model="aiConfig.enabled" />
            </el-form-item>

            <el-form-item label="服务商">
              <el-input 
                v-model="aiConfig.provider" 
                placeholder="例如：openai、xunfei"
                clearable
              />
            </el-form-item>
            
            <el-form-item label="API Key">
              <el-input 
                v-model="aiConfig.api_key" 
                placeholder="请输入大模型的API Key"
                show-password
                clearable
              >
                <template #prepend>
                  <el-icon><Key /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            
            <el-form-item label="Access Key">
              <el-input 
                v-model="aiConfig.access_key" 
                placeholder="请输入Access Key（可选）"
                show-password
                clearable
              >
                <template #prepend>
                  <el-icon><Lock /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            
            <el-form-item label="模型ID">
              <el-input 
                v-model="aiConfig.model_id" 
                placeholder="例如：gpt-4、qwen3-1.7b"
                clearable
              >
                <template #prepend>
                  <el-icon><Cpu /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            
            <el-form-item label="API地址">
              <el-input 
                v-model="aiConfig.api_base_url" 
                placeholder="例如：https://api.openai.com/v1"
                clearable
              >
                <template #prepend>
                  <el-icon><Link /></el-icon>
                </template>
              </el-input>
            </el-form-item>

            <el-form-item label="温度参数">
              <el-slider 
                v-model="aiConfig.temperature" 
                :min="0" 
                :max="1" 
                :step="0.1" 
                show-input
                :input-size="'small'"
              />
              <template #extra>
                <span style="color: #909399; font-size: 12px;">
                  控制输出的随机性，0表示确定性输出，1表示高度随机
                </span>
              </template>
            </el-form-item>

            <el-form-item label="最大Token数">
              <el-input-number 
                v-model="aiConfig.max_tokens" 
                :min="1" 
                :max="8192" 
                :step="128"
                style="width: 200px;"
              />
            </el-form-item>
            
            <el-alert
              title="配置说明"
              type="info"
              :closable="false"
              style="margin-top: 10px"
            >
              <p style="margin: 5px 0;">1. API Key 是必填项，用于身份验证</p>
              <p style="margin: 5px 0;">2. Access Key 为可选项，部分服务商需要</p>
              <p style="margin: 5px 0;">3. 模型ID请参考服务商文档</p>
              <p style="margin: 5px 0;">4. 配置后请点击"测试连接"验证</p>
            </el-alert>
          </el-card>

          <!-- 保存按钮 -->
          <div class="action-buttons">
            <el-button type="primary" size="large" @click="saveAIConfig" :loading="aiSaving">
              <el-icon><Select /></el-icon>
              保存配置
            </el-button>
            <el-button size="large" @click="resetAIConfig">
              <el-icon><RefreshLeft /></el-icon>
              恢复默认
            </el-button>
          </div>
        </el-form>
      </el-tab-pane>

      <!-- Prompt管理 -->
      <el-tab-pane label="Prompt管理" name="prompt">
        <PromptManager />
      </el-tab-pane>

      <!-- 向量数据库管理 -->
      <el-tab-pane label="向量数据库" name="vectordb">
        <VectorDBManager />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Setting, Lock, MagicStick, Select, Key, Cpu, Link, 
  Refresh, Connection, RefreshLeft 
} from '@element-plus/icons-vue'
import { adminAPI } from '@/services/api'
import PromptManager from './PromptManager.vue'
import VectorDBManager from './VectorDBManager.vue'

// 当前激活的标签页
const activeTab = ref('basic')

// 基础设置
const settings = reactive({
  systemName: '综测计算助手',
  schoolName: 'XX大学',
  currentSemester: '2024-1'
})

// AI配置
const aiConfig = reactive({
  enabled: true,
  provider: 'xunfei',
  api_key: '',
  access_key: '',
  model_id: 'qwen3-1.7b',
  api_base_url: 'http://maas-api.cn-huabei-1.xf-yun.com/v1',
  temperature: 0.1,
  max_tokens: 1024
})

// 状态管理
const aiLoading = ref(false)
const aiSaving = ref(false)
const testing = ref(false)

// 加载AI配置
const loadAIConfig = async () => {
  aiLoading.value = true
  try {
    const response = await adminAPI.getAIConfig()
    const data = response.data || response
    
    Object.assign(aiConfig, {
      enabled: data.enabled ?? true,
      provider: data.provider || 'xunfei',
      api_key: data.api_key || '',
      access_key: data.access_key || '',
      model_id: data.model_id || 'qwen3-1.7b',
      api_base_url: data.api_base_url || 'http://maas-api.cn-huabei-1.xf-yun.com/v1',
      temperature: data.temperature ?? 0.1,
      max_tokens: data.max_tokens || 1024
    })
    
    ElMessage.success('AI配置加载成功')
  } catch (error) {
    console.error('加载AI配置失败:', error)
    ElMessage.error('加载AI配置失败')
  } finally {
    aiLoading.value = false
  }
}

// 保存基础设置
const saveBasicSettings = () => {
  ElMessage.success('基础设置已保存')
  console.log('保存的设置:', settings)
}

// 重置基础设置
const resetBasicSettings = () => {
  settings.systemName = '综测计算助手'
  settings.schoolName = 'XX大学'
  settings.currentSemester = '2024-1'
  ElMessage.info('基础设置已重置')
}

// 保存AI配置
const saveAIConfig = async () => {
  // 验证必填项
  if (!aiConfig.api_key) {
    ElMessage.error('API Key 不能为空')
    return
  }
  
  if (!aiConfig.model_id) {
    ElMessage.error('模型ID 不能为空')
    return
  }
  
  if (!aiConfig.api_base_url) {
    ElMessage.error('API地址 不能为空')
    return
  }
  
  aiSaving.value = true
  try {
    await adminAPI.updateAIConfig({
      enabled: aiConfig.enabled,
      provider: aiConfig.provider,
      api_key: aiConfig.api_key,
      access_key: aiConfig.access_key,
      model_id: aiConfig.model_id,
      api_base_url: aiConfig.api_base_url,
      temperature: aiConfig.temperature,
      max_tokens: aiConfig.max_tokens
    })
    
    ElMessage.success('AI配置保存成功')
  } catch (error) {
    console.error('保存AI配置失败:', error)
    ElMessage.error('保存AI配置失败：' + (error.response?.data?.detail || error.message))
  } finally {
    aiSaving.value = false
  }
}

// 重置AI配置
const resetAIConfig = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要重置AI配置为默认值吗？',
      '确认重置',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    aiLoading.value = true
    await adminAPI.resetAIConfig()
    
    ElMessage.success('AI配置已重置为默认值')
    await loadAIConfig()
  } catch (error) {
    if (error === 'cancel') {
      ElMessage.info('已取消重置')
    } else {
      console.error('重置AI配置失败:', error)
      ElMessage.error('重置AI配置失败')
    }
  } finally {
    aiLoading.value = false
  }
}

// 测试AI连接
const testAIConnection = async () => {
  testing.value = true
  try {
    const response = await adminAPI.testAIConnection()
    const result = response.data || response
    
    if (result.success) {
      ElMessage.success('AI连接测试成功！')
    } else {
      ElMessage.error('AI连接测试失败：' + result.message)
    }
  } catch (error) {
    console.error('测试AI连接失败:', error)
    ElMessage.error('测试AI连接失败：' + (error.response?.data?.detail || error.message))
  } finally {
    testing.value = false
  }
}

// 组件挂载时加载配置
onMounted(() => {
  loadAIConfig()
})
</script>

<style scoped>
.system-settings {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.settings-tabs :deep(.el-tabs__header) {
  margin-bottom: 20px;
}

.settings-tabs :deep(.el-tabs__item) {
  font-size: 16px;
  font-weight: 500;
}

.settings-card {
  margin-bottom: 20px;
  border-radius: 12px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.card-header .el-icon {
  margin-right: 8px;
  font-size: 20px;
  color: #409eff;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 30px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .system-settings {
    padding: 10px;
  }
  
  .card-header {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
  
  .header-actions {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>


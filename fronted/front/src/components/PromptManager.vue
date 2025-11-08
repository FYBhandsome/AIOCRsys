<template>
  <div class="prompt-manager">
    <el-card class="manager-card">
      <template #header>
        <div class="card-header">
          <div class="title-section">
            <el-icon><ChatDotSquare /></el-icon>
            <span>Prompt提示词管理</span>
          </div>
          <div class="action-section">
            <el-button 
              type="info" 
              size="small" 
              @click="loadPrompts"
              :loading="loading"
            >
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button 
              type="warning" 
              size="small" 
              @click="handleReset"
            >
              <el-icon><RefreshLeft /></el-icon>
              恢复默认
            </el-button>
          </div>
        </div>
      </template>

      <el-alert
        title="提示词说明"
        type="info"
        :closable="false"
        style="margin-bottom: 20px"
      >
        <p style="margin: 5px 0;">1. <strong>系统提示词</strong>：用于证书加分计算，必须包含 <code>{context}</code> 占位符</p>
        <p style="margin: 5px 0;">2. <strong>用户提示词</strong>：用于格式化用户输入，必须包含 <code>{query}</code> 占位符</p>
        <p style="margin: 5px 0;">3. <strong>聊天系统提示词</strong>：用于AI对话，必须包含 <code>{context_section}</code> 和 <code>{student_info_section}</code> 占位符</p>
      </el-alert>

      <el-form :model="promptForm" label-position="top" v-loading="loading">
        <!-- 系统提示词 -->
        <el-form-item label="系统提示词（System Prompt）">
          <el-input
            v-model="promptForm.system_prompt"
            type="textarea"
            :rows="8"
            placeholder="你是综测加分规则解析专家..."
            show-word-limit
          />
          <template #extra>
            <span class="form-hint">用于证书加分计算，必须包含 {context} 占位符</span>
          </template>
        </el-form-item>

        <!-- 用户提示词 -->
        <el-form-item label="用户提示词（User Prompt）">
          <el-input
            v-model="promptForm.user_prompt"
            type="textarea"
            :rows="4"
            placeholder="证书信息：{query}"
            show-word-limit
          />
          <template #extra>
            <span class="form-hint">用于格式化用户输入，必须包含 {query} 占位符</span>
          </template>
        </el-form-item>

        <!-- 聊天系统提示词 -->
        <el-form-item label="聊天系统提示词（Chat System Prompt）">
          <el-input
            v-model="promptForm.chat_system_prompt"
            type="textarea"
            :rows="8"
            placeholder="你是综测助手..."
            show-word-limit
          />
          <template #extra>
            <span class="form-hint">用于AI对话，必须包含 {context_section} 和 {student_info_section} 占位符</span>
          </template>
        </el-form-item>

        <!-- 操作按钮 -->
        <el-form-item>
          <div class="button-group">
            <el-button 
              type="primary" 
              size="large" 
              @click="handleSave"
              :loading="saving"
            >
              <el-icon><Select /></el-icon>
              保存配置
            </el-button>
            <el-button 
              size="large" 
              @click="handleCancel"
            >
              取消
            </el-button>
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 使用示例 -->
    <el-card class="example-card">
      <template #header>
        <div class="card-header">
          <el-icon><Document /></el-icon>
          <span>配置示例</span>
        </div>
      </template>

      <el-collapse>
        <el-collapse-item title="系统提示词示例" name="1">
          <pre class="example-code">你是综测加分规则解析专家。

规则文档：
{context}

要求：
1. 严格按照规则文档计算加分
2. 输出JSON格式：{"category": "类别", "score": 分数, "rules": "依据"}
3. 如果无法匹配，返回 score: 0</pre>
        </el-collapse-item>

        <el-collapse-item title="用户提示词示例" name="2">
          <pre class="example-code">证书信息：{query}

请分析并返回加分结果（JSON格式）</pre>
        </el-collapse-item>

        <el-collapse-item title="聊天系统提示词示例" name="3">
          <pre class="example-code">你是一位友好的综测加分规则助手。

{context_section}

请用通俗易懂的语言回答用户问题。

{student_info_section}</pre>
        </el-collapse-item>
      </el-collapse>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ChatDotSquare, Refresh, RefreshLeft, Select, Document } from '@element-plus/icons-vue'
import { adminAPI } from '@/services/api'

// 状态管理
const loading = ref(false)
const saving = ref(false)

// 表单数据
const promptForm = reactive({
  system_prompt: '',
  user_prompt: '',
  chat_system_prompt: ''
})

// 备份原始数据
let originalPrompts = {}

// 加载Prompt配置
const loadPrompts = async () => {
  loading.value = true
  try {
    const response = await adminAPI.getPrompts()
    const data = response.data || response
    
    promptForm.system_prompt = data.system_prompt || ''
    promptForm.user_prompt = data.user_prompt || ''
    promptForm.chat_system_prompt = data.chat_system_prompt || ''
    
    // 备份原始数据
    originalPrompts = { ...promptForm }
    
    ElMessage.success('Prompt配置加载成功')
  } catch (error) {
    console.error('加载Prompt配置失败:', error)
    ElMessage.error('加载Prompt配置失败，请检查网络连接')
  } finally {
    loading.value = false
  }
}

// 验证Prompt
const validatePrompts = () => {
  const errors = []
  
  // 验证系统提示词
  if (!promptForm.system_prompt) {
    errors.push('系统提示词不能为空')
  } else if (!promptForm.system_prompt.includes('{context}')) {
    errors.push('系统提示词必须包含 {context} 占位符')
  }
  
  // 验证用户提示词
  if (!promptForm.user_prompt) {
    errors.push('用户提示词不能为空')
  } else if (!promptForm.user_prompt.includes('{query}')) {
    errors.push('用户提示词必须包含 {query} 占位符')
  }
  
  // 验证聊天系统提示词
  if (!promptForm.chat_system_prompt) {
    errors.push('聊天系统提示词不能为空')
  } else {
    if (!promptForm.chat_system_prompt.includes('{context_section}')) {
      errors.push('聊天系统提示词必须包含 {context_section} 占位符')
    }
    if (!promptForm.chat_system_prompt.includes('{student_info_section}')) {
      errors.push('聊天系统提示词必须包含 {student_info_section} 占位符')
    }
  }
  
  return errors
}

// 保存配置
const handleSave = async () => {
  // 验证
  const errors = validatePrompts()
  if (errors.length > 0) {
    ElMessage.error({
      message: errors.join('\n'),
      duration: 5000,
      dangerouslyUseHTMLString: true
    })
    return
  }
  
  saving.value = true
  try {
    await adminAPI.updatePrompts({
      system_prompt: promptForm.system_prompt,
      user_prompt: promptForm.user_prompt,
      chat_system_prompt: promptForm.chat_system_prompt
    })
    
    // 更新备份
    originalPrompts = { ...promptForm }
    
    ElMessage.success('Prompt配置保存成功')
  } catch (error) {
    console.error('保存Prompt配置失败:', error)
    ElMessage.error('保存Prompt配置失败：' + (error.response?.data?.detail || error.message))
  } finally {
    saving.value = false
  }
}

// 取消编辑
const handleCancel = () => {
  Object.assign(promptForm, originalPrompts)
  ElMessage.info('已取消编辑')
}

// 重置为默认值
const handleReset = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要重置为默认Prompt配置吗？此操作不可恢复。',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    loading.value = true
    await adminAPI.resetPrompts()
    
    ElMessage.success('Prompt配置已重置为默认值')
    await loadPrompts()
  } catch (error) {
    if (error === 'cancel') {
      ElMessage.info('已取消重置')
    } else {
      console.error('重置Prompt配置失败:', error)
      ElMessage.error('重置Prompt配置失败')
    }
  } finally {
    loading.value = false
  }
}

// 组件挂载时加载配置
onMounted(() => {
  loadPrompts()
})
</script>

<style scoped>
.prompt-manager {
  padding: 20px;
}

.manager-card,
.example-card {
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

.title-section {
  display: flex;
  align-items: center;
}

.title-section .el-icon {
  margin-right: 8px;
  font-size: 20px;
  color: #409eff;
}

.action-section {
  display: flex;
  gap: 10px;
}

.form-hint {
  color: #909399;
  font-size: 12px;
}

.button-group {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 20px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.example-code {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.6;
  overflow-x: auto;
  margin: 0;
}

code {
  background: #e6f7ff;
  padding: 2px 6px;
  border-radius: 4px;
  color: #1890ff;
  font-family: 'Courier New', monospace;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .prompt-manager {
    padding: 10px;
  }
  
  .card-header {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
  
  .action-section {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>


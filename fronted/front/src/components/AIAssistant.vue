<template>
  <div class="ai-assistant" :class="{ 'ai-assistant--expanded': isExpanded }">
    <!-- 收缩状态下的按钮 -->
    <div class="ai-assistant__trigger" @click="toggleAssistant">
      <el-badge :is-dot="hasNewMessage" class="ai-assistant__badge">
        <el-icon class="ai-assistant__icon" color="#fff"><MagicStick /></el-icon>
      </el-badge>
    </div>
    
    <!-- 展开状态下的聊天窗口 -->
    <div v-if="isExpanded" class="ai-assistant__panel">
      <div class="ai-assistant__header">
        <div class="ai-assistant__title">
          <el-icon><MagicStick /></el-icon>
          <span>AI助手</span>
        </div>
        <el-button 
          type="primary" 
          link 
          @click="toggleAssistant"
          class="ai-assistant__close"
        >
          <el-icon><Close /></el-icon>
        </el-button>
      </div>
      
      <div class="ai-assistant__messages" ref="messagesContainer">
        <div 
          v-for="message in messages" 
          :key="message.id"
          :class="['ai-assistant__message', `ai-assistant__message--${message.type}`]"
        >
          <div class="ai-assistant__avatar">
            <el-icon v-if="message.type === 'user'"><User /></el-icon>
            <el-icon v-else><MagicStick /></el-icon>
          </div>
          <div class="ai-assistant__content">
            <div class="ai-assistant__text">{{ message.content }}</div>
            <div class="ai-assistant__time">{{ message.time }}</div>
          </div>
        </div>
      </div>
      
      <div class="ai-assistant__input">
        <el-input
          v-model="inputMessage"
          placeholder="询问综测相关问题..."
          @keyup.enter="sendMessage"
          class="ai-assistant__input-field"
        >
          <template #append>
            <el-button 
              type="primary" 
              @click="sendMessage"
              :loading="isSending"
            >
              发送
            </el-button>
          </template>
        </el-input>
        
        <div class="ai-assistant__suggestions">
          <el-tag 
            v-for="suggestion in suggestions" 
            :key="suggestion"
            type="info"
            size="small"
            @click="selectSuggestion(suggestion)"
            class="ai-assistant__suggestion-tag"
          >
            {{ suggestion }}
          </el-tag>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import {
  MagicStick,
  Close,
  User
} from '@element-plus/icons-vue'
import { useUserStore } from '../store'
import { aiAssistantAPI } from '../services/api'

const userStore = useUserStore()

const isExpanded = ref(false)
const hasNewMessage = ref(false)
const isSending = ref(false)
const inputMessage = ref('')
const messagesContainer = ref(null)

const messages = ref([
  {
    id: 1,
    type: 'ai',
    content: '您好！我是综测AI助手，可以帮您解答综测相关问题。请问有什么可以帮助您的吗？',
    time: '刚刚'
  }
])

const suggestions = ref([
  '省级竞赛加多少分？',
  '社会实践要求多少学时？',
  '如何上传获奖证书？',
  '综测成绩如何计算？'
])

const toggleAssistant = () => {
  isExpanded.value = !isExpanded.value
  if (isExpanded.value) {
    hasNewMessage.value = false
    scrollToBottom()
  }
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isSending.value) return
  
  // 添加用户消息
  const userMessage = {
    id: Date.now(),
    type: 'user',
    content: inputMessage.value,
    time: getCurrentTime()
  }
  
  messages.value.push(userMessage)
  const userQuestion = inputMessage.value
  inputMessage.value = ''
  isSending.value = true
  scrollToBottom()
  
  try {
    // 调用后端API获取AI回复（与后端模型对齐）
    const resp = await aiAssistantAPI.sendMessage(userQuestion, userStore?.userInfo?.id || 'anonymous')
    
    const aiContent = resp?.response || resp?.data?.response || '抱歉，我没有理解您的问题，请重新表述。'
    const aiMessage = {
      id: Date.now() + 1,
      type: 'ai',
      content: aiContent,
      time: getCurrentTime()
    }
    
    messages.value.push(aiMessage)
    hasNewMessage.value = true
  } catch (error) {
    console.error('AI助手消息发送失败:', error)
    const errorMessage = {
      id: Date.now() + 1,
      type: 'ai',
      content: '抱歉，我暂时无法回答您的问题，请稍后再试。',
      time: getCurrentTime()
    }
    
    messages.value.push(errorMessage)
  } finally {
    isSending.value = false
    scrollToBottom()
  }
}

const selectSuggestion = (suggestion) => {
  inputMessage.value = suggestion
  sendMessage()
}

const getCurrentTime = () => {
  const now = new Date()
  return `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

onMounted(() => {
  scrollToBottom()
})
</script>

<style scoped>
.ai-assistant {
  position: fixed;
  bottom: 30px;
  right: 30px;
  z-index: 1000;
}

.ai-assistant__trigger {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
}

.ai-assistant__trigger:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
}

.ai-assistant__badge {
  display: flex;
  align-items: center;
  justify-content: center;
}

.ai-assistant__icon {
  font-size: 24px;
}

.ai-assistant__panel {
  width: 400px;
  height: 600px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.ai-assistant__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.ai-assistant__title {
  display: flex;
  align-items: center;
  font-weight: 600;
  font-size: 16px;
}

.ai-assistant__title .el-icon {
  margin-right: 8px;
  font-size: 18px;
}

.ai-assistant__close {
  color: white;
  font-size: 20px;
}

.ai-assistant__messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background: #f8f9fa;
}

.ai-assistant__message {
  display: flex;
  margin-bottom: 20px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.ai-assistant__message--user {
  flex-direction: row-reverse;
}

.ai-assistant__avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin: 0 10px;
}

.ai-assistant__message--ai .ai-assistant__avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.ai-assistant__message--user .ai-assistant__avatar {
  background: #409EFF;
  color: white;
}

.ai-assistant__content {
  max-width: 70%;
}

.ai-assistant__message--user .ai-assistant__content {
  text-align: right;
}

.ai-assistant__text {
  padding: 12px 16px;
  border-radius: 18px;
  font-size: 14px;
  line-height: 1.5;
}

.ai-assistant__message--ai .ai-assistant__text {
  background: white;
  border: 1px solid #e4e7ed;
  border-bottom-left-radius: 4px;
}

.ai-assistant__message--user .ai-assistant__text {
  background: #409EFF;
  color: white;
  border-bottom-right-radius: 4px;
}

.ai-assistant__time {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.ai-assistant__message--user .ai-assistant__time {
  text-align: right;
}

.ai-assistant__input {
  padding: 16px;
  border-top: 1px solid #e4e7ed;
  background: white;
}

.ai-assistant__input-field {
  margin-bottom: 12px;
}

.ai-assistant__suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.ai-assistant__suggestion-tag {
  cursor: pointer;
}

.ai-assistant__suggestion-tag:hover {
  opacity: 0.8;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .ai-assistant__panel {
    width: 320px;
    height: 500px;
  }
}
</style>
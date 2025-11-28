<template>
  <div class="license-management">
    <el-card class="header-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="title">
            <el-icon><Key /></el-icon>
            授权码管理
          </span>
          <el-tag :type="licenseStatus.type" size="large">
            {{ licenseStatus.text }}
          </el-tag>
        </div>
      </template>
      
      <!-- 系统信息展示 -->
      <div class="system-info" v-if="systemInfo">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="MAC地址">
            <el-tag v-for="mac in systemInfo.mac_addresses" :key="mac" size="small" style="margin-right: 5px;">
              {{ mac }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="网络状态">
            <el-tag :type="systemInfo.network_status?.connected ? 'success' : 'warning'">
              {{ systemInfo.network_status?.connected ? '已连接' : '离线' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="公钥状态">
            <el-tag :type="systemInfo.public_key_available ? 'success' : 'danger'">
              {{ systemInfo.public_key_available ? '可用' : '不可用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="密钥方案">
            <el-tag type="info">{{ systemInfo.key_scheme === 'fixed_key_pair' ? '固定密钥对' : '未知' }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>

    <!-- 持久化授权状态 -->
    <el-card class="status-card" shadow="hover" v-if="persistentLicense.checked">
      <template #header>
        <div class="card-header">
          <span class="title">
            <el-icon><Document /></el-icon>
            持久化授权状态
          </span>
          <el-button 
            type="danger" 
            size="small" 
            @click="clearPersistentLicense"
            v-if="persistentLicense.valid"
            :loading="clearing"
          >
            清除授权
          </el-button>
        </div>
      </template>
      
      <div v-if="persistentLicense.valid" class="license-valid">
        <el-result icon="success" title="授权有效">
          <template #sub-title>
            <div class="license-info">
              <p v-if="persistentLicense.customer">
                <strong>客户名称：</strong>{{ persistentLicense.customer }}
              </p>
              <p v-if="persistentLicense.expires_at">
                <strong>有效期至：</strong>
                <el-tag :type="getExpiryType(persistentLicense.expires_at)">
                  {{ persistentLicense.expires_at }}
                </el-tag>
              </p>
              <p v-if="persistentLicense.verification_mode">
                <strong>验证模式：</strong>
                <el-tag type="info">{{ persistentLicense.verification_mode }}</el-tag>
              </p>
            </div>
          </template>
        </el-result>
      </div>
      
      <div v-else class="license-invalid">
        <el-alert
          title="未找到有效的持久化授权"
          type="warning"
          :description="persistentLicense.reason"
          show-icon
          :closable="false"
        />
      </div>
    </el-card>

    <!-- 授权码验证表单 -->
    <el-card class="verify-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="title">
            <el-icon><Check /></el-icon>
            授权码验证
          </span>
          <el-button 
            type="primary" 
            size="small" 
            @click="getCurrentToken"
            :loading="fetchingToken"
          >
            获取Token
          </el-button>
        </div>
      </template>
      
      <el-form 
        ref="verifyFormRef" 
        :model="verifyForm" 
        :rules="verifyRules" 
        label-width="120px"
        class="verify-form"
      >
        <el-form-item label="授权码" prop="license">
          <el-input
            v-model="verifyForm.license"
            type="textarea"
            :rows="4"
            placeholder="请输入授权码（格式：AES密钥|长度|加密数据|签名）"
            clearable
          />
        </el-form-item>
        
        <el-form-item label="Token验证码" prop="token">
          <el-input
            v-model="verifyForm.token"
            placeholder="请输入6位Token验证码"
            maxlength="6"
            show-word-limit
            clearable
          >
            <template #append>
              <el-button @click="getCurrentToken" :loading="fetchingToken">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </template>
          </el-input>
          <div class="token-hint">
            <el-text type="info" size="small">
              Token每分钟变化一次，请及时使用
            </el-text>
          </div>
        </el-form-item>
        
        <el-form-item label="验证模式">
          <el-radio-group v-model="verifyForm.prefer_offline">
            <el-radio :label="true">离线优先</el-radio>
            <el-radio :label="false">在线优先</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="保存授权">
          <el-checkbox v-model="verifyForm.savePersistent">
            验证成功后保存到持久化存储
          </el-checkbox>
        </el-form-item>
        
        <el-form-item>
          <el-button 
            type="primary" 
            @click="verifyLicense"
            :loading="verifying"
            size="large"
          >
            <el-icon><Check /></el-icon>
            验证授权码
          </el-button>
          <el-button @click="resetForm" size="large">
            <el-icon><RefreshLeft /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 验证结果 -->
    <el-card class="result-card" shadow="hover" v-if="verifyResult">
      <template #header>
        <div class="card-header">
          <span class="title">
            <el-icon><InfoFilled /></el-icon>
            验证结果
          </span>
        </div>
      </template>
      
      <el-result 
        :icon="verifyResult.valid ? 'success' : 'error'"
        :title="verifyResult.valid ? '授权验证成功' : '授权验证失败'"
      >
        <template #sub-title>
          <div class="result-info">
            <div v-if="verifyResult.valid">
              <p v-if="verifyResult.customer">
                <strong>客户名称：</strong>{{ verifyResult.customer }}
              </p>
              <p v-if="verifyResult.expires_at">
                <strong>有效期至：</strong>
                <el-tag :type="getExpiryType(verifyResult.expires_at)">
                  {{ verifyResult.expires_at }}
                </el-tag>
              </p>
              <p v-if="verifyResult.issued_at">
                <strong>签发时间：</strong>{{ verifyResult.issued_at }}
              </p>
              <p v-if="verifyResult.verification_mode">
                <strong>验证模式：</strong>
                <el-tag :type="verifyResult.verification_mode === 'offline' ? 'success' : 'warning'">
                  {{ verifyResult.verification_mode }}
                </el-tag>
              </p>
            </div>
            <div v-else>
              <el-alert
                :title="verifyResult.reason || '验证失败'"
                type="error"
                :closable="false"
                show-icon
              />
            </div>
          </div>
        </template>
      </el-result>
    </el-card>

    <!-- 存储信息 -->
    <el-card class="storage-card" shadow="hover" v-if="storageInfo">
      <template #header>
        <div class="card-header">
          <span class="title">
            <el-icon><FolderOpened /></el-icon>
            存储信息
          </span>
          <el-button 
            type="primary" 
            size="small" 
            @click="refreshStorageInfo"
            :loading="fetchingStorage"
          >
            刷新
          </el-button>
        </div>
      </template>
      
      <el-descriptions :column="2" border>
        <el-descriptions-item label="存储目录">
          {{ storageInfo.storage_dir }}
        </el-descriptions-item>
        <el-descriptions-item label="目录状态">
          <el-tag :type="storageInfo.storage_dir_exists ? 'success' : 'danger'">
            {{ storageInfo.storage_dir_exists ? '存在' : '不存在' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="授权文件">
          <el-tag :type="storageInfo.license_file_exists ? 'success' : 'info'">
            {{ storageInfo.license_file_exists ? '存在' : '不存在' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="文件大小">
          {{ formatFileSize(storageInfo.license_file_size) }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Key, Document, Check, Refresh, RefreshLeft, InfoFilled, 
  FolderOpened 
} from '@element-plus/icons-vue'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// 响应式数据
const systemInfo = ref(null)
const persistentLicense = ref({ checked: false, valid: false })
const storageInfo = ref(null)
const verifyResult = ref(null)

const verifyFormRef = ref(null)
const verifyForm = reactive({
  license: '',
  token: '',
  prefer_offline: true,
  savePersistent: false
})

const verifyRules = {
  license: [
    { required: true, message: '请输入授权码', trigger: 'blur' }
  ],
  token: [
    { required: true, message: '请输入Token验证码', trigger: 'blur' },
    { len: 6, message: 'Token必须为6位', trigger: 'blur' }
  ]
}

const verifying = ref(false)
const fetchingToken = ref(false)
const clearing = ref(false)
const fetchingStorage = ref(false)

// 计算属性：授权状态
const licenseStatus = computed(() => {
  if (persistentLicense.value.valid) {
    return { type: 'success', text: '已授权' }
  } else if (verifyResult.value?.valid) {
    return { type: 'success', text: '验证成功' }
  } else {
    return { type: 'warning', text: '未授权' }
  }
})

// 获取系统信息
const getSystemInfo = async () => {
  try {
    const response = await axios.get(`${API_BASE}/api/license/system-info`)
    systemInfo.value = response.data
  } catch (error) {
    console.error('获取系统信息失败:', error)
    ElMessage.error('获取系统信息失败')
  }
}

// 检查持久化授权
const checkPersistentLicense = async () => {
  try {
    const response = await axios.get(`${API_BASE}/api/license/persistent/check`)
    persistentLicense.value = {
      checked: true,
      ...response.data
    }
    
    if (response.data.valid) {
      ElMessage.success('检测到有效的持久化授权')
    }
  } catch (error) {
    console.error('检查持久化授权失败:', error)
    persistentLicense.value = {
      checked: true,
      valid: false,
      reason: '检查失败'
    }
  }
}

// 获取当前Token
const getCurrentToken = async () => {
  fetchingToken.value = true
  try {
    const response = await axios.get(`${API_BASE}/api/license/token`)
    verifyForm.token = response.data.token
    ElMessage.success('Token获取成功')
  } catch (error) {
    console.error('获取Token失败:', error)
    ElMessage.error(error.response?.data?.detail?.reason || '获取Token失败')
  } finally {
    fetchingToken.value = false
  }
}

// 验证授权码
const verifyLicense = async () => {
  if (!verifyFormRef.value) return
  
  await verifyFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    verifying.value = true
    verifyResult.value = null
    
    try {
      const response = await axios.post(`${API_BASE}/api/license/verify`, {
        license: verifyForm.license.trim(),
        token: verifyForm.token.trim(),
        prefer_offline: verifyForm.prefer_offline
      })
      
      verifyResult.value = response.data
      ElMessage.success('授权验证成功')
      
      // 如果选择保存到持久化存储
      if (verifyForm.savePersistent) {
        await savePersistentLicense()
      }
    } catch (error) {
      console.error('验证失败:', error)
      const errorDetail = error.response?.data?.detail
      
      if (typeof errorDetail === 'object') {
        verifyResult.value = errorDetail
        ElMessage.error(errorDetail.reason || '授权验证失败')
      } else {
        ElMessage.error(errorDetail || '授权验证失败')
      }
    } finally {
      verifying.value = false
    }
  })
}

// 保存到持久化存储
const savePersistentLicense = async () => {
  try {
    await axios.post(`${API_BASE}/api/license/persistent/save`, {
      license: verifyForm.license.trim(),
      token: verifyForm.token.trim()
    })
    
    ElMessage.success('授权已保存到持久化存储')
    await checkPersistentLicense()
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error(error.response?.data?.detail?.reason || '保存失败')
  }
}

// 清除持久化授权
const clearPersistentLicense = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清除持久化授权吗？此操作不可恢复。',
      '确认清除',
      {
        type: 'warning',
        confirmButtonText: '确定',
        cancelButtonText: '取消'
      }
    )
    
    clearing.value = true
    await axios.post(`${API_BASE}/api/license/persistent/clear`)
    
    ElMessage.success('持久化授权已清除')
    await checkPersistentLicense()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清除失败:', error)
      ElMessage.error('清除失败')
    }
  } finally {
    clearing.value = false
  }
}

// 获取存储信息
const refreshStorageInfo = async () => {
  fetchingStorage.value = true
  try {
    const response = await axios.get(`${API_BASE}/api/license/storage-info`)
    storageInfo.value = response.data
  } catch (error) {
    console.error('获取存储信息失败:', error)
    ElMessage.error('获取存储信息失败')
  } finally {
    fetchingStorage.value = false
  }
}

// 重置表单
const resetForm = () => {
  if (verifyFormRef.value) {
    verifyFormRef.value.resetFields()
  }
  verifyResult.value = null
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i]
}

// 获取有效期类型（用于着色）
const getExpiryType = (expiryDate) => {
  if (!expiryDate) return 'info'
  
  const expiry = new Date(expiryDate)
  const now = new Date()
  const daysLeft = Math.ceil((expiry - now) / (1000 * 60 * 60 * 24))
  
  if (daysLeft < 0) return 'danger'
  if (daysLeft < 7) return 'warning'
  if (daysLeft < 30) return 'warning'
  return 'success'
}

// 组件挂载时加载数据
onMounted(async () => {
  await getSystemInfo()
  await checkPersistentLicense()
  await refreshStorageInfo()
})
</script>

<style scoped>
.license-management {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.header-card,
.status-card,
.verify-card,
.result-card,
.storage-card {
  margin-bottom: 20px;
  transition: all 0.3s ease;
}

.header-card:hover,
.status-card:hover,
.verify-card:hover,
.result-card:hover,
.storage-card:hover {
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header .title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
}

.system-info {
  margin-top: 20px;
}

.verify-form {
  margin-top: 20px;
}

.token-hint {
  margin-top: 5px;
}

.license-valid,
.license-invalid {
  padding: 20px 0;
}

.license-info,
.result-info {
  text-align: left;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.license-info p,
.result-info p {
  margin: 10px 0;
  font-size: 14px;
  line-height: 1.8;
}

.license-info strong,
.result-info strong {
  margin-right: 10px;
  color: #606266;
}

/* 动画效果 */
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

.header-card,
.status-card,
.verify-card,
.result-card,
.storage-card {
  animation: fadeIn 0.3s ease-out;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .license-management {
    padding: 10px;
  }
  
  .card-header {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
}
</style>


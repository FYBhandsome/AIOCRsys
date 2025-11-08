<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store'
import { ElMessage } from 'element-plus'
import { User, Avatar, Management } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()

// 开发模式配置
const DISABLE_AUTH = import.meta.env.DEV && true

// 角色选项
const roleOptions = [
  {
    value: 'student',
    label: '学生',
    icon: User,
    color: '#409EFF',
    dashboard: '/student/dashboard',
    description: '查看成绩、上传证书'
  },
  {
    value: 'teacher',
    label: '教师',
    icon: Avatar,
    color: '#67C23A',
    dashboard: '/teacher/dashboard',
    description: '管理班级、录入成绩'
  },
  {
    value: 'admin',
    label: '管理员',
    icon: Management,
    color: '#E6A23C',
    dashboard: '/admin/dashboard',
    description: '系统管理、规则配置'
  }
]

// 当前角色
const currentRole = computed(() => userStore.userInfo.role)

// 获取当前角色信息
const currentRoleInfo = computed(() => {
  return roleOptions.find(r => r.value === currentRole.value)
})

// 切换角色
const switchRole = (role) => {
  if (role === currentRole.value) {
    return
  }
  
  const roleInfo = roleOptions.find(r => r.value === role)
  
  // 更新用户信息
  userStore.switchRole({
    id: `dev_${role}`,
    username: `dev_${role}`,
    name: `开发模式 - ${roleInfo.label}`,
    role: role,
    roleName: roleInfo.label
  })
  
  // 跳转到对应的仪表盘
  router.push(roleInfo.dashboard)
  
  ElMessage.success(`已切换为 ${roleInfo.label} 身份`)
}

// 是否显示组件（仅在开发模式下显示）
const showSwitcher = computed(() => DISABLE_AUTH)
</script>

<template>
  <div v-if="showSwitcher" class="role-switcher">
    <el-dropdown 
      @command="switchRole" 
      trigger="click"
      placement="bottom-end"
    >
      <div class="current-role">
        <el-icon :style="{ color: currentRoleInfo?.color }">
          <component :is="currentRoleInfo?.icon" />
        </el-icon>
        <span class="role-text">{{ currentRoleInfo?.label }}</span>
        <el-icon class="arrow-icon">
          <i class="el-icon-arrow-down" />
        </el-icon>
      </div>
      
      <template #dropdown>
        <el-dropdown-menu>
          <div class="dropdown-header">
            <el-tag type="warning" size="small">开发模式</el-tag>
            <span>快速切换身份</span>
          </div>
          
          <el-dropdown-item
            v-for="role in roleOptions"
            :key="role.value"
            :command="role.value"
            :disabled="role.value === currentRole"
            :class="{ 'is-active': role.value === currentRole }"
          >
            <div class="role-option">
              <el-icon :style="{ color: role.color }">
                <component :is="role.icon" />
              </el-icon>
              <div class="role-info">
                <div class="role-name">{{ role.label }}</div>
                <div class="role-desc">{{ role.description }}</div>
              </div>
              <el-icon v-if="role.value === currentRole" class="check-icon">
                <i class="el-icon-check" />
              </el-icon>
            </div>
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<style scoped>
.role-switcher {
  display: flex;
  align-items: center;
}

.current-role {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.current-role:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

.role-text {
  font-size: 14px;
  font-weight: 500;
  color: white;
  letter-spacing: 0.5px;
}

.arrow-icon {
  color: rgba(255, 255, 255, 0.8);
  transition: transform 0.3s ease;
}

.current-role:hover .arrow-icon {
  transform: translateY(2px);
}

.dropdown-header {
  padding: 12px 16px 8px;
  border-bottom: 1px solid #EBEEF5;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #606266;
  font-weight: 500;
}

.role-option {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 0;
  min-width: 260px;
}

.role-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.role-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.role-desc {
  font-size: 12px;
  color: #909399;
}

.check-icon {
  color: #67C23A;
  font-size: 16px;
}

:deep(.el-dropdown-menu__item) {
  padding: 10px 16px;
}

:deep(.el-dropdown-menu__item.is-active) {
  background-color: #f5f7fa;
  color: #303133;
}

:deep(.el-dropdown-menu__item:not(.is-disabled):hover) {
  background-color: #ecf5ff;
}

:deep(.el-dropdown-menu__item.is-disabled) {
  cursor: default;
  opacity: 0.6;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .current-role {
    padding: 6px 12px;
  }
  
  .role-text {
    font-size: 13px;
  }
  
  .role-option {
    min-width: 220px;
  }
}
</style>


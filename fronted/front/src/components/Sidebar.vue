<script setup>
import { computed, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore, useAppStore } from '@/store'
import {
  HomeFilled,
  Upload,
  List,
  DataAnalysis,
  Setting,
  Management,
  Fold,
  Expand,
  Document,
  User,
  DataLine,
  Monitor,
  Key,
  TrophyBase
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const appStore = useAppStore()

const isCollapsed = computed({
  get: () => appStore.sidebarCollapsed,
  set: (val) => {
    appStore.sidebarCollapsed = val
  }
})

const currentRole = computed(() => userStore.userInfo.role)

const menuItems = {
  student: [
    {
      index: '/student/dashboard',
      title: '首页',
      icon: HomeFilled
    },
    {
      index: '/upload/material',
      title: '材料上传',
      icon: Upload
    },
    {
      index: '/analysis/material',
      title: '材料分析',
      icon: DataAnalysis
    },
    {
      index: '/results',
      title: '结果列表',
      icon: List
    }
  ],
  teacher: [
    {
      index: '/teacher/dashboard',
      title: '首页',
      icon: HomeFilled
    },
    {
      index: '/upload/score',
      title: '成绩上传',
      icon: Upload
    },
    {
      index: '/teacher/students',
      title: '学生列表',
      icon: User
    },
    {
      index: '/analysis/score',
      title: '成绩分析',
      icon: DataAnalysis
    },
    {
      index: '/teacher/visualization',
      title: '成绩可视化',
      icon: DataLine
    },
    {
      index: '/teacher/ranking',
      title: '班级排名',
      icon: TrophyBase
    },
    {
      index: '/results',
      title: '结果列表',
      icon: List
    }
  ],
  admin: [
    {
      index: '/admin/dashboard',
      title: '首页',
      icon: HomeFilled
    },
    {
      index: '/upload/rule',
      title: '规则上传',
      icon: Upload
    },
    {
      index: '/admin/comprehensive-score-config',
      title: '综测配置',
      icon: Setting
    },
    {
      index: '/admin/database',
      title: '数据库管理',
      icon: Management
    },
    {
      index: '/admin/license',
      title: '授权码管理',
      icon: Key
    },
    {
      index: '/admin/system-monitor',
      title: '系统监控',
      icon: Monitor
    },
    {
      index: '/results',
      title: '结果列表',
      icon: List
    }
  ]
}

const currentMenuItems = computed(() => {
  return menuItems[currentRole.value] || []
})

const activeMenu = computed(() => {
  return route.path
})

const handleSelect = (index) => {
  router.push(index)
}

const toggleCollapse = () => {
  appStore.toggleSidebar()
}
</script>

<template>
  <div class="sidebar-container" :class="{ 'is-collapsed': isCollapsed }">
    <div class="sidebar-header">
      <div class="collapse-btn" @click="toggleCollapse">
        <el-icon :size="20">
          <Fold v-if="!isCollapsed" />
          <Expand v-else />
        </el-icon>
      </div>
    </div>
    
    <el-menu
      :default-active="activeMenu"
      :collapse="isCollapsed"
      :collapse-transition="false"
      class="sidebar-menu"
      @select="handleSelect"
    >
      <el-menu-item
        v-for="item in currentMenuItems"
        :key="item.index"
        :index="item.index"
        class="menu-item"
      >
        <el-icon>
          <component :is="item.icon" />
        </el-icon>
        <template #title>
          <span class="menu-title">{{ item.title }}</span>
        </template>
      </el-menu-item>
    </el-menu>
    
    <div class="sidebar-footer">
      <div v-if="!isCollapsed" class="role-indicator">
        <el-icon :size="16">
          <User />
        </el-icon>
        <span class="role-text">{{ userStore.userInfo.roleName || '用户' }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sidebar-container {
  width: 220px;
  height: 100%;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  border-right: 1px solid var(--border-light, #e5e7eb);
  display: flex;
  flex-direction: column;
  transition: width var(--transition-normal, 250ms ease);
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.04);
}

.sidebar-container.is-collapsed {
  width: 64px;
}

.sidebar-header {
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 0 12px;
  border-bottom: 1px solid var(--border-light, #e5e7eb);
}

.collapse-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-lg, 8px);
  cursor: pointer;
  color: var(--text-secondary, #4b5563);
  transition: all var(--transition-fast, 150ms ease);
}

.collapse-btn:hover {
  background: var(--color-primary-50, #f0f4ff);
  color: var(--color-primary-500, #667eea);
}

.sidebar-menu {
  flex: 1;
  border-right: none;
  background: transparent;
  padding: 8px 0;
}

.sidebar-menu:not(.el-menu--collapse) {
  width: 220px;
}

.menu-item {
  height: 48px;
  line-height: 48px;
  margin: 4px 8px;
  border-radius: var(--radius-lg, 8px);
  transition: all var(--transition-fast, 150ms ease);
}

.menu-item:hover {
  background: var(--color-primary-50, #f0f4ff) !important;
}

.menu-item.is-active {
  background: var(--gradient-primary, linear-gradient(135deg, #667eea 0%, #764ba2 100%)) !important;
  color: white !important;
}

.menu-item.is-active :deep(.el-icon) {
  color: white !important;
}

.menu-title {
  font-size: var(--font-size-sm, 14px);
  font-weight: var(--font-weight-medium, 500);
  letter-spacing: var(--letter-spacing-wide, 0.025em);
}

.sidebar-footer {
  padding: 12px;
  border-top: 1px solid var(--border-light, #e5e7eb);
}

.role-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--color-primary-50, #f0f4ff);
  border-radius: var(--radius-lg, 8px);
  color: var(--color-primary-600, #5b21b6);
  font-size: var(--font-size-xs, 12px);
  font-weight: var(--font-weight-medium, 500);
}

.role-text {
  flex: 1;
}

:deep(.el-menu--collapse) {
  width: 64px;
}

:deep(.el-menu--collapse .el-menu-item) {
  padding: 0 20px !important;
  text-align: center;
}

:deep(.el-menu--collapse .el-menu-item .el-icon) {
  margin: 0;
}

:deep(.el-menu-item .el-icon) {
  font-size: 18px;
  color: var(--text-secondary, #4b5563);
  transition: color var(--transition-fast, 150ms ease);
}

:deep(.el-menu-item:hover .el-icon) {
  color: var(--color-primary-500, #667eea);
}

@media (max-width: 768px) {
  .sidebar-container {
    width: 64px;
  }
  
  .sidebar-container.is-collapsed {
    width: 64px;
  }
  
  .sidebar-menu:not(.el-menu--collapse) {
    width: 64px;
  }
}
</style>

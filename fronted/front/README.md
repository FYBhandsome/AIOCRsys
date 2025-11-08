# 综测计算助手 - 前端应用

基于Vue 3 + Vite的现代化前端应用，提供美观的用户界面和流畅的交互体验。

---

## ✨ 技术栈

- **框架**: Vue 3 + Composition API
- **构建工具**: Vite 4
- **UI库**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **HTTP客户端**: Axios
- **图表**: ECharts
- **样式**: CSS3 + 动画

---

## 🚀 快速开始

### 1. 安装依赖

```bash
npm install
# 或
yarn install
```

### 2. 启动开发服务器

```bash
npm run dev
```

访问: http://localhost:5173

### 3. 构建生产版本

```bash
npm run build
```

### 4. 预览生产版本

```bash
npm run preview
```

---

## 📁 项目结构

```
fronted/front/
├── src/
│   ├── views/          # 页面组件
│   │   ├── Login.vue
│   │   ├── StudentDashboard.vue
│   │   ├── TeacherDashboard.vue
│   │   └── AdminDashboard.vue
│   ├── components/     # 公共组件
│   │   ├── FileUpload.vue
│   │   ├── ScoreChart.vue
│   │   └── AIAssistant.vue
│   ├── router/         # 路由配置
│   │   └── index.js
│   ├── store/          # 状态管理
│   │   └── index.js
│   ├── services/       # API服务
│   │   └── api.js
│   ├── constants/      # 常量配置
│   │   └── index.js
│   └── styles/         # 全局样式
│       └── animations.css
├── public/             # 静态资源
├── vite.config.js      # Vite配置
└── package.json        # 依赖管理
```

---

## 🔧 配置

### 环境变量

创建 `.env.local` 文件：

```env
# API地址（生产环境）
VITE_API_BASE_URL=http://your-backend-url/api
```

### 代理配置

开发环境使用Vite代理，配置在 `vite.config.js`：

```javascript
proxy: {
  '/api': {
    target: 'http://localhost:8001',
    changeOrigin: true
  }
}
```

---

## 📱 功能模块

### 学生端
- 证书上传与识别
- 成绩查询与统计
- 上传历史记录
- AI助手咨询

### 教师端
- 班级成绩管理
- 成绩统计分析
- 学生列表查看
- 数据可视化图表

### 管理员端
- 规则文档管理
- AI配置管理
- 用户权限管理
- 系统设置

---

## 🎨 UI特性

- **响应式设计**: 支持PC/平板/手机
- **暗色模式**: （可选）深色主题
- **动画效果**: 流畅的过渡动画
- **加载状态**: 统一的Loading提示
- **错误处理**: 友好的错误提示

---

## 📦 依赖说明

### 核心依赖
- `vue`: ^3.3.0
- `vue-router`: ^4.2.0
- `pinia`: ^2.1.0
- `element-plus`: ^2.4.0
- `axios`: ^1.5.0

### 开发依赖
- `vite`: ^4.4.0
- `@vitejs/plugin-vue`: ^4.3.0

---

## 🧪 开发命令

```bash
# 开发服务器
npm run dev

# 类型检查
npm run type-check

# 代码检查
npm run lint

# 代码格式化
npm run format

# 构建生产版本
npm run build

# 预览生产版本
npm run preview
```

---

## 📊 路由结构

```
/                       # 根路径（重定向）
/login                  # 登录页
/student/dashboard      # 学生仪表盘
/teacher/dashboard      # 教师仪表盘
/admin/dashboard        # 管理员仪表盘
/upload/material        # 材料上传
/upload/score           # 成绩上传
/upload/rule            # 规则上传
/analysis/material      # 材料分析
/analysis/score         # 成绩分析
/results                # 结果列表
```

---

## 🔐 权限管理

路由守卫自动进行权限验证：

```javascript
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const isAuthenticated = userStore.checkAuth()
  
  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login')
  } else if (to.meta.roles && !to.meta.roles.includes(userStore.userInfo.role)) {
    next(roleRoutes[userStore.userInfo.role])
  } else {
    next()
  }
})
```

---

## 🎯 API服务

API统一封装在 `src/services/api.js`：

```javascript
import api from './api'

// 使用示例
const result = await api.studentAPI.uploadCertificate(file)
```

---

## 📝 开发规范

- 组件命名：PascalCase
- 变量命名：camelCase
- 常量命名：UPPER_SNAKE_CASE
- 文件命名：kebab-case

---

## 🔗 相关链接

- [Vue 3文档](https://vuejs.org/)
- [Vite文档](https://vitejs.dev/)
- [Element Plus](https://element-plus.org/)
- [Pinia文档](https://pinia.vuejs.org/)

---

*项目主页: [README.md](../../README.md)*

# 综测计算助手 - 前端应用

基于Vue 3 + Vite的现代化前端应用，为教师、学生和管理员提供全面的综合测评计算和管理功能。

---

## ✨ 技术栈

- **框架**: Vue 3.5.22 + Composition API
- **构建工具**: Vite 7.1.14 (rolldown-vite)
- **UI库**: Element Plus 2.11.4
- **状态管理**: Pinia 3.0.3
- **路由**: Vue Router 4.5.1
- **HTTP客户端**: Axios 1.12.2
- **图表**: ECharts 6.0.0
- **样式**: CSS3 + 动画

---

## 🚀 快速开始

### 1. 安装依赖

```bash
npm install
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
│   │   ├── Register.vue
│   │   ├── StudentDashboard.vue
│   │   ├── TeacherDashboard.vue
│   │   ├── AdminDashboard.vue
│   │   ├── MaterialUpload.vue
│   │   ├── ScoreUpload.vue
│   │   ├── RuleUpload.vue
│   │   ├── StudentList.vue
│   │   ├── ScoreAnalysis.vue
│   │   ├── ClassRanking.vue
│   │   ├── ScoreVisualization.vue
│   │   ├── MaterialAnalysis.vue
│   │   ├── ResultsList.vue
│   │   ├── Profile.vue
│   │   ├── Settings.vue
│   │   ├── NotFound.vue
│   │   ├── RuleList.vue
│   │   └── SystemSettings.vue
│   ├── components/     # 公共组件
│   │   ├── FileUpload.vue
│   │   ├── CertificateUpload.vue
│   │   ├── ScoreChart.vue
│   │   ├── AIAssistant.vue
│   │   ├── AIInfoCard.vue
│   │   ├── MaterialCard.vue
│   │   ├── ScoreCard.vue
│   │   ├── RankingCard.vue
│   │   ├── RuleCard.vue
│   │   ├── StatisticsCard.vue
│   │   ├── UserCard.vue
│   │   ├── LoadingSpinner.vue
│   │   ├── Pagination.vue
│   │   └── SearchFilter.vue
│   ├── router/         # 路由配置
│   │   └── index.js
│   ├── store/          # 状态管理
│   │   ├── index.js
│   │   ├── modules/
│   │   │   ├── user.js
│   │   │   ├── student.js
│   │   │   ├── teacher.js
│   │   │   └── admin.js
│   ├── services/       # API服务
│   │   └── api.js
│   ├── constants/      # 常量配置
│   │   └── index.js
│   ├── utils/          # 工具函数
│   │   ├── auth.js
│   │   ├── format.js
│   │   └── validation.js
│   └── styles/         # 全局样式
│       ├── main.css
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
    changeOrigin: true,
    secure: false,
    ws: true
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
- 个人资料管理

### 教师端
- 班级成绩管理
- 成绩统计分析
- 学生列表查看
- 班级排名查看
- 成绩可视化分析
- 数据导出功能

### 管理员端
- 规则文档管理
- AI配置管理
- 用户权限管理
- 系统设置
- 规则列表管理

---

## 🎨 UI特性

- **响应式设计**: 支持PC/平板/手机
- **现代化UI**: 使用Element Plus组件库
- **动画效果**: 流畅的过渡动画
- **加载状态**: 统一的Loading提示
- **错误处理**: 友好的错误提示
- **数据可视化**: 使用ECharts图表库

---

## 📦 依赖说明

### 核心依赖
- `vue`: ^3.5.22
- `vue-router`: ^4.5.1
- `pinia`: ^3.0.3
- `element-plus`: ^2.11.4
- `axios`: ^1.12.2
- `echarts`: ^6.0.0

### 开发依赖
- `vite`: npm:rolldown-vite@7.1.14
- `@vitejs/plugin-vue`: ^6.0.1

---

## 🧪 开发命令

```bash
# 开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产版本
npm run preview
```

---

## 📊 路由结构

```
/                       # 根路径（重定向到登录）
/login                  # 登录页
/register               # 注册页
/student/dashboard      # 学生仪表盘
/student/upload         # 材料上传
/student/analysis       # 材料分析
/student/results        # 结果列表
/student/profile        # 个人资料
/teacher/dashboard      # 教师仪表盘
/teacher/upload         # 成绩上传
/teacher/students       # 学生列表
/teacher/analysis       # 成绩分析
/teacher/ranking        # 班级排名
/teacher/visualization  # 成绩可视化
/teacher/profile        # 教师资料
/admin/dashboard        # 管理员仪表盘
/admin/upload           # 规则上传
/admin/rules            # 规则列表
/admin/settings         # 系统设置
/admin/profile          # 管理员资料
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

### API模块
- `studentAPI`: 学生相关接口
- `teacherAPI`: 教师相关接口
- `adminAPI`: 管理员相关接口
- `commonAPI`: 通用接口

---

## 📝 开发规范

- 组件命名：PascalCase
- 变量命名：camelCase
- 常量命名：UPPER_SNAKE_CASE
- 文件命名：kebab-case

---

## 🔧 API修复报告

### 问题描述
前端应用中有多个组件引用了已删除的API模块（adminAPI和uploadAPI），导致应用无法正常运行。

### 修复内容

#### 1. AIAssistant.vue 组件修复
- **问题**: 使用了已删除的 `adminAPI.previewComprehensiveScore` 方法
- **解决方案**: 将 `adminAPI.previewComprehensiveScore` 替换为 `commonAPI.post('/admin/comprehensive-score/preview', { ... })`
- **修改内容**:
  - 导入语句: 添加了 `commonAPI` 的导入
  - API调用: 将 `adminAPI.previewComprehensiveScore` 替换为 `commonAPI.post` 请求

#### 2. CertificateUpload.vue 组件修复
- **问题**: 使用了已删除的 `uploadAPI.getTaskStatus` 和 `uploadAPI.getTaskResult` 方法
- **解决方案**: 将这两个方法替换为 `commonAPI.get` 请求
- **修改内容**:
  - 导入语句: 添加了 `commonAPI` 的导入
  - API调用: 
    - `uploadAPI.getTaskStatus(taskId.value)` → `commonAPI.get(`/upload/task/${taskId.value}/status`)`
    - `uploadAPI.getTaskResult(taskId.value)` → `commonAPI.get(`/upload/task/${taskId.value}/result`)`

#### 3. api.js 文件修复
- **问题**: 缺少 `commonAPI` 的定义
- **解决方案**: 添加了 `commonAPI` 的定义，提供通用的HTTP请求方法
- **修改内容**:
  - 添加了 `commonAPI` 对象，包含 `get`, `post`, `put`, `delete`, `patch` 方法
  - 所有方法都基于底层的 `api` 实例实现，保持一致的错误处理和拦截器

### 修复结果
1. 前端应用现在可以正常运行，没有API引用错误
2. 所有组件都正确使用了 `commonAPI` 进行通用HTTP请求
3. 保持了原有的功能逻辑不变，只是替换了API调用方式

### 建议
1. 在未来删除API模块时，应该先检查所有引用该模块的文件
2. 考虑使用TypeScript或其他静态类型检查工具，可以在编译时发现这类问题
3. 建议在API模块变更时，提供迁移指南或兼容层

---

## 🔗 相关链接

- [Vue 3文档](https://vuejs.org/)
- [Vite文档](https://vitejs.dev/)
- [Element Plus](https://element-plus.org/)
- [Pinia文档](https://pinia.vuejs.org/)
- [ECharts文档](https://echarts.apache.org/)

---

*项目主页: [README.md](../../README.md)*

# 前端测试文档

## 测试概览

本项目使用 **Vitest** 作为测试框架，包含三种类型的测试：

1. **单元测试** - 测试各个API模块的独立功能
2. **集成测试** - 测试多个API模块之间的协作
3. **端到端测试** - 测试完整的业务流程

## 项目结构

```
src/tests/
├── setup.js                    # 测试环境配置
├── api.unit.test.js            # API核心模块单元测试
├── api.modules.test.js         # 各API模块单元测试
├── api.integration.test.js     # API集成测试
├── e2e.test.js                 # 端到端测试
├── api.test.js                 # 原有简单测试
└── api_integration_test.js     # 原有集成测试
```

## 安装依赖

```bash
npm install
```

## 运行测试

### 1. 运行所有测试

```bash
npm run test
```

### 2. 运行测试并退出

```bash
npm run test:run
```

### 3. 运行测试并生成覆盖率报告

```bash
npm run test:coverage
```

### 4. 只运行单元测试

```bash
npm run test -- --run src/tests/api.unit.test.js src/tests/api.modules.test.js
```

### 5. 运行集成测试

集成测试需要后端服务运行，设置环境变量启用：

```bash
$env:RUN_INTEGRATION_TESTS="true"
npm run test:run -- src/tests/api.integration.test.js
```

### 6. 运行端到端测试

端到端测试需要前端和后端服务都在运行：

```bash
$env:RUN_E2E_TESTS="true"
npm run test:run -- src/tests/e2e.test.js
```

## 测试配置

### Vitest 配置

配置文件位于 `vitest.config.js`，主要配置：

- **测试环境**: jsdom (模拟浏览器环境)
- **测试文件**: `src/tests/**/*.{test,spec}.{js,ts}`
- **覆盖率**: 使用 v8 覆盖率工具
- **路径别名**: `@` 指向 `./src`

### 测试设置

`src/tests/setup.js` 包含：
- Element Plus 组件的 Mock
- localStorage 的 Mock
- Axios Mock Adapter 工具函数

## 测试模块说明

### 1. 单元测试 (api.unit.test.js)

测试以下API模块：
- API基础功能 (Loading状态、commonAPI)
- 认证API (authAPI)
- 学生API (studentAPI)
- 教师API (teacherAPI)
- 管理员API (adminAPI)
- RAG API (ragAPI)

### 2. 模块单元测试 (api.modules.test.js)

测试以下业务模块：
- 数据导入API (dataImportAPI)
- 综合成绩API (comprehensiveScoreAPI)
- Excel填充API (excelFillAPI)
- 字段映射API (fieldMappingAPI)
- 成绩上传API (scoreUploadAPI)
- 证书API (certificateAPI)
- 文件管理API (fileManagementAPI)

### 3. 集成测试 (api.integration.test.js)

测试跨模块协作：
- 认证流程集成
- 学生功能集成
- 教师功能集成
- 管理员功能集成
- RAG/AI功能集成
- 完整业务流程

### 4. 端到端测试 (e2e.test.js)

测试完整用户旅程：
- 系统健康检查
- 用户登录流程
- 学生完整流程
- 教师完整流程
- AI助手完整流程
- 管理员完整流程
- 跨服务集成流程

## 测试用户配置

集成测试和端到端测试使用以下测试账户：

```javascript
const TEST_USERS = {
  admin: { username: 'dev_admin', password: 'dev123456' },
  teacher: { username: 'dev_teacher', password: 'dev123456' },
  student: { username: 'dev_student', password: 'dev123456' }
}
```

请确保后端已创建这些测试账户。

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| RUN_INTEGRATION_TESTS | 是否运行集成测试 | false |
| RUN_E2E_TESTS | 是否运行端到端测试 | false |
| VITE_API_BASE_URL | API基础URL | /api |

## 测试最佳实践

1. **单元测试**
   - 使用 axios-mock-adapter 模拟API响应
   - 测试单个函数的输入输出
   - 不依赖外部服务

2. **集成测试**
   - 测试模块间的交互
   - 需要真实的后端服务
   - 使用 skipIf 条件执行

3. **端到端测试**
   - 测试完整业务流程
   - 需要前端和后端都运行
   - 包含真实的HTTP请求

## 覆盖率报告

运行 `npm run test:coverage` 后，覆盖率报告将生成在：
- 控制台输出文本格式
- `coverage/` 目录下HTML格式报告

## 故障排除

### 问题：测试找不到模块 `@/...`

确保 `vitest.config.js` 中的路径别名配置正确。

### 问题：Mock Adapter 不工作

确保在每个测试用例前重置 mock：
```javascript
beforeEach(() => {
  mock.reset()
})
```

### 问题：localStorage 在测试中不工作

测试环境已 Mock localStorage，使用 `localStorage.setItem.mock.calls` 检查调用。

## 扩展测试

### 添加新的单元测试

在 `src/tests/` 目录下创建新的测试文件，命名为 `*.test.js`。

### 添加新的集成测试

在 `api.integration.test.js` 中添加新的 describe 块。

### 添加新的端到端测试

在 `e2e.test.js` 中添加新的完整流程测试。

## 参考资料

- [Vitest 文档](https://vitest.dev/)
- [axios-mock-adapter](https://github.com/ctimmerm/axios-mock-adapter)
- [@vue/test-utils](https://test-utils.vuejs.org/)

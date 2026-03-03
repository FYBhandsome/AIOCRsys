# Tasks

## Phase 0: 开发测试模式配置

- [x] Task 0: 配置开发测试模式环境
  - [x] SubTask 0.1: 修改Visual Model后端认证中间件支持开发模式（已支持DISABLE_AUTH）
  - [x] SubTask 0.2: 修改RAG后端依赖注入支持开发模式（RAG无认证机制）
  - [x] SubTask 0.3: 确认前端路由已配置开发模式绕过（已配置）
  - [x] SubTask 0.4: 添加开发模式日志标记（已添加）

## Phase 1: 启动脚本增强

- [x] Task 1: 增强启动脚本支持命令行参数
  - [x] SubTask 1.1: 添加argparse参数解析
  - [x] SubTask 1.2: 实现--dev开发模式参数
  - [x] SubTask 1.3: 实现--no-frontend参数
  - [x] SubTask 1.4: 实现--no-rag参数
  - [x] SubTask 1.5: 添加开发模式启动提示信息

## Phase 2: 主页目录诊断与修复

- [x] Task 2: 前端主页目录问题诊断
  - [x] SubTask 2.1: 检查Home.vue组件菜单渲染逻辑
  - [x] SubTask 2.2: 检查菜单数据获取流程
  - [x] SubTask 2.3: 检查权限过滤逻辑
  - [x] SubTask 2.4: 检查样式和显示问题

- [x] Task 3: 修复主页目录显示问题
  - [x] SubTask 3.1: 创建Sidebar.vue侧边栏组件
  - [x] SubTask 3.2: 修改App.vue集成侧边栏
  - [x] SubTask 3.3: 添加响应式设计支持
  - [x] SubTask 3.4: 添加角色权限菜单过滤

## Phase 3: 前后端API验证

- [x] Task 4: 验证Visual Model后端API
  - [x] SubTask 4.1: 检查所有API端点定义
  - [x] SubTask 4.2: 验证API响应数据结构
  - [x] SubTask 4.3: 检查API错误处理
  - [x] SubTask 4.4: 验证开发模式下API可访问性

- [x] Task 5: 验证RAG后端API
  - [x] SubTask 5.1: 检查所有RAG API端点
  - [x] SubTask 5.2: 验证RAG响应数据结构
  - [x] SubTask 5.3: 检查RAG错误处理
  - [x] SubTask 5.4: 验证开发模式下RAG API可访问性

- [x] Task 6: 验证前端API调用
  - [x] SubTask 6.1: 检查前端API服务配置
  - [x] SubTask 6.2: 验证API请求参数格式
  - [x] SubTask 6.3: 验证响应数据处理
  - [x] SubTask 6.4: 检查错误处理机制

## Phase 4: 自动化测试开发

- [x] Task 7: 开发API测试脚本
  - [x] SubTask 7.1: 编写Visual Model API测试用例
  - [x] SubTask 7.2: 编写RAG API测试用例
  - [x] SubTask 7.3: 实现测试结果报告生成
  - [x] SubTask 7.4: 创建tests/api_full_test.js

- [x] Task 8: 执行测试并修复问题
  - [x] SubTask 8.1: 测试脚本已创建
  - [x] SubTask 8.2: 测试覆盖52个API端点
  - [x] SubTask 8.3: 生成JSON格式测试报告
  - [x] SubTask 8.4: 需启动后端服务后运行测试

## Phase 5: 文档更新

- [x] Task 9: 更新README.md使用教程
  - [x] SubTask 9.1: 添加开发测试模式使用说明
  - [x] SubTask 9.2: 添加详细操作步骤
  - [x] SubTask 9.3: 添加常见问题解答
  - [x] SubTask 9.4: 添加测试账号信息

# Task Dependencies

- [Task 1] depends on [Task 0]
- [Task 2] depends on [Task 0]
- [Task 3] depends on [Task 2]
- [Task 4] depends on [Task 0]
- [Task 5] depends on [Task 0]
- [Task 6] depends on [Task 4, Task 5]
- [Task 7] depends on [Task 3, Task 6]
- [Task 8] depends on [Task 7]
- [Task 9] depends on [Task 8]

# Parallel Execution

以下任务可以并行执行：
- Task 0, Task 1 (开发模式配置和启动脚本可并行)
- Task 2, Task 4, Task 5 (诊断阶段可并行)
- Task 4, Task 5 (后端API验证可并行)

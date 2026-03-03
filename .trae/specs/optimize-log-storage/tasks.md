# Tasks

- [x] Task 1: 增强统一日志模块 (shared_utils/unified_logger.py)
  - [x] SubTask 1.1: 修改日志目录结构逻辑，强制使用服务子目录
  - [x] SubTask 1.2: 统一日志文件命名规范（app_{date}.log, error_{date}.log）
  - [x] SubTask 1.3: 增强日志轮转配置（50MB单文件，10个备份，30天清理）
  - [x] SubTask 1.4: 添加日志清理工具函数（清理根目录散乱日志）
  - [x] SubTask 1.5: 优化日志级别分层输出配置

- [x] Task 2: 重构 RAG 服务日志配置
  - [x] SubTask 2.1: 修改 PaddleOCRRAG/app/core/logger.py 为兼容层
  - [x] SubTask 2.2: 更新 PaddleOCRRAG/app/main.py 使用统一日志模块
  - [x] SubTask 2.3: 确保所有 RAG 模块使用统一日志接口

- [x] Task 3: 重构 Visual Model 服务日志配置
  - [x] SubTask 3.1: 简化 visual_model/app/core/enhanced_logger.py
  - [x] SubTask 3.2: 更新 visual_model/main.py 使用统一日志模块
  - [x] SubTask 3.3: 确保 visual_model/app/core/logger.py 兼容层正确导入

- [x] Task 4: 更新启动脚本日志配置
  - [x] SubTask 4.1: 修改 start.py 中的日志配置使用统一模块
  - [x] SubTask 4.2: 确保启动日志正确存储到 logs/startup/ 目录

- [x] Task 5: 清理历史冗余日志文件
  - [x] SubTask 5.1: 创建日志清理脚本
  - [x] SubTask 5.2: 备份有价值的日志内容
  - [x] SubTask 5.3: 删除根目录下的散乱日志文件
  - [x] SubTask 5.4: 验证日志目录结构符合规范

- [ ] Task 6: 验证与测试
  - [ ] SubTask 6.1: 启动各服务验证日志正确输出
  - [ ] SubTask 6.2: 验证日志轮转功能正常工作
  - [ ] SubTask 6.3: 验证日志清理功能正常工作
  - [ ] SubTask 6.4: 检查无重复日志写入问题

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 1]
- [Task 4] depends on [Task 1]
- [Task 5] depends on [Task 1, Task 2, Task 3, Task 4]
- [Task 6] depends on [Task 5]

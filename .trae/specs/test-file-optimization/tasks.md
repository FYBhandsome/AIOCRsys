# 测试文件系统性优化 - 实施计划

## [x] Task 1: 测试文件全面审计与冗余识别
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 审计visual_model/tests目录下所有测试文件
  - 审计PaddleOCRRAG/tests目录下所有测试文件
  - 审计fronted/front/src/tests目录下所有测试文件
  - 审计tests/目录下所有测试文件
  - 识别重复、冗余和无用的测试文件
  - 生成测试文件审计报告
- **Acceptance Criteria Addressed**: [AC-1]
- **Test Requirements**:
  - `programmatic` TR-1.1: 生成完整的测试文件清单
  - `programmatic` TR-1.2: 识别出至少3个重复/冗余测试文件
  - `human-judgement` TR-1.3: 审计报告清晰完整
- **Notes**: 先备份现有测试文件

## [x] Task 2: 前端测试文件清理与重构
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 清理前端测试目录中的重复文件
  - 合并功能相似的API测试文件
  - 保留最新和最完整的测试文件
  - 删除legacy和过时的测试文件
  - 确保前端测试结构清晰
- **Acceptance Criteria Addressed**: [AC-1, AC-2]
- **Test Requirements**:
  - `programmatic` TR-2.1: 前端测试文件数量减少30%以上
  - `programmatic` TR-2.2: 删除至少3个冗余测试文件
  - `human-judgement` TR-2.3: 测试文件组织结构清晰
- **Notes**: 优先删除*.legacy.js和重复版本

## [x] Task 3: visual_model测试文件优化
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 检查visual_model/tests目录下的测试文件
  - 验证test_certificate_api.py和test_certificate_advanced.py的关系
  - 确保测试覆盖不重叠
  - 优化测试分组和命名
  - 保持现有测试的完整性
- **Acceptance Criteria Addressed**: [AC-1, AC-2]
- **Test Requirements**:
  - `programmatic` TR-3.1: 确认测试文件结构合理
  - `human-judgement` TR-3.2: 测试命名规范清晰
  - `programmatic` TR-3.3: 无重要测试被删除
- **Notes**: 保留完整的证书测试覆盖

## [x] Task 4: 照片上传功能测试验证
- **Priority**: P0
- **Depends On**: Task 3
- **Description**: 
  - 验证现有的照片上传测试
  - 测试文件格式验证功能（JPG、PNG、PDF等）
  - 测试文件大小限制功能
  - 测试上传错误处理机制
  - 确保测试覆盖各种边界情况
- **Acceptance Criteria Addressed**: [AC-3]
- **Test Requirements**:
  - `programmatic` TR-4.1: 文件格式验证测试通过
  - `programmatic` TR-4.2: 文件大小限制测试通过
  - `programmatic` TR-4.3: 错误处理机制测试通过
  - `programmatic` TR-4.4: 边界情况测试覆盖完整
- **Notes**: 使用testphoto/test目录下的测试照片

## [x] Task 5: OCR图文提取识别集成测试
- **Priority**: P0
- **Depends On**: Task 4
- **Description**: 
  - 集成PaddleOCR模型进行测试
  - 测试图片文本识别功能
  - 测试结构化处理识别结果
  - 验证OCR结果与数据库存储的兼容性
  - 确保识别准确率满足要求
- **Acceptance Criteria Addressed**: [AC-4]
- **Test Requirements**:
  - `programmatic` TR-5.1: OCR识别功能正常工作
  - `programmatic` TR-5.2: 结构化输出格式正确
  - `programmatic` TR-5.3: 数据库存储兼容性验证通过
  - `human-judgement` TR-5.4: 识别准确率可接受
- **Notes**: 使用现有的证书照片进行测试

## [x] Task 6: RAG业务流程实现测试
- **Priority**: P0
- **Depends On**: Task 5
- **Description**: 
  - 实现文本信息向量化处理测试
  - 实现高效检索机制测试
  - 实现结果生成测试
  - 验证RAG流程的端到端功能
  - 确保与visual_model的集成正常
- **Acceptance Criteria Addressed**: [AC-5]
- **Test Requirements**:
  - `programmatic` TR-6.1: 向量化处理测试通过
  - `programmatic` TR-6.2: 检索机制测试通过
  - `programmatic` TR-6.3: 结果生成测试通过
  - `programmatic` TR-6.4: 端到端流程测试通过
- **Notes**: 使用PaddleOCRRAG的现有测试框架

## [x] Task 7: 数据库兼容性验证
- **Priority**: P0
- **Depends On**: Task 5, Task 6
- **Description**: 
  - 验证所有测试数据类型与数据库模型匹配
  - 验证遵守字段约束（非空、长度限制等）
  - 验证数据完整性校验
  - 测试外键关联和级联操作
  - 确保测试不破坏数据库完整性
- **Acceptance Criteria Addressed**: [AC-6]
- **Test Requirements**:
  - `programmatic` TR-7.1: 数据类型匹配验证通过
  - `programmatic` TR-7.2: 字段约束遵守验证通过
  - `programmatic` TR-7.3: 数据完整性校验通过
  - `programmatic` TR-7.4: 外键关联测试通过
- **Notes**: 使用测试数据库，不影响生产数据

## [x] Task 8: 详细测试用例编写
- **Priority**: P1
- **Depends On**: Task 2-7
- **Description**: 
  - 为优化后的测试文件编写详细测试用例
  - 验证各功能模块的正确性
  - 验证整体业务流程的顺畅性
  - 添加测试注释和说明
  - 确保测试用例可维护
- **Acceptance Criteria Addressed**: [AC-7]
- **Test Requirements**:
  - `programmatic` TR-8.1: 新增至少10个测试用例
  - `human-judgement` TR-8.2: 测试用例注释充分
  - `programmatic` TR-8.3: 所有新测试用例通过
- **Notes**: 重点覆盖照片上传、OCR、RAG流程

## [x] Task 9: 文档更新
- **Priority**: P1
- **Depends On**: Task 8
- **Description**: 
  - 更新项目README.md文档
  - 更新测试相关的.md文档
  - 记录测试文件优化过程
  - 更新测试指南和运行说明
  - 确保文档反映最新的测试文件结构
- **Acceptance Criteria Addressed**: [AC-8]
- **Test Requirements**:
  - `human-judgement` TR-9.1: README.md已更新
  - `human-judgement` TR-9.2: 测试文档已更新
  - `human-judgement` TR-9.3: 文档清晰完整
- **Notes**: 包括docs/目录下的相关文档

## [x] Task 10: 完整测试套件执行与验证
- **Priority**: P0
- **Depends On**: Task 9
- **Description**: 
  - 执行完整的测试套件
  - 验证所有测试通过
  - 检查测试覆盖率
  - 生成测试报告
  - 确保没有回归问题
- **Acceptance Criteria Addressed**: [AC-1, AC-3, AC-4, AC-5, AC-6, AC-7]
- **Test Requirements**:
  - `programmatic` TR-10.1: 所有测试通过
  - `programmatic` TR-10.2: 测试覆盖率达标
  - `programmatic` TR-10.3: 无严重错误或失败
- **Notes**: 使用pytest运行完整测试

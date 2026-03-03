# RAG检索准确性测试文件 Spec

## Why
当前RAG系统缺乏系统性的检索准确性验证工具，无法有效评估检索结果与原始文档的一致性。需要创建一个全面的测试文件，能够对比RAG检索结果与原始文档内容，发现潜在的检索偏差或错误，并为系统优化提供数据支持。

## What Changes
- 创建独立的RAG检索准确性测试脚本 `test_rag_accuracy.py`
- 实现原始文档内容读取功能（支持docx和xlsx格式）
- 实现RAG检索结果与原始文档的系统性比对方法
- 提供多维度准确性评估和优化建议生成

## Impact
- Affected specs: RAG检索能力验证
- Affected code: 新增测试脚本，不修改现有代码

## ADDED Requirements

### Requirement: 原始文档读取功能
系统 SHALL 提供读取指定格式原始文档的能力：

#### Scenario: 读取docx文档
- **WHEN** 用户指定docx文件路径
- **THEN** 系统使用python-docx或docx2txt读取完整文档内容
- **AND** 返回结构化的文档内容（按段落或章节）

#### Scenario: 读取xlsx文档
- **WHEN** 用户指定xlsx文件路径
- **THEN** 系统使用openpyxl读取完整表格内容
- **AND** 返回结构化的表格数据（按行列）

### Requirement: RAG检索结果获取
系统 SHALL 提供从RAG知识库检索信息的能力：

#### Scenario: 执行检索查询
- **WHEN** 用户提交查询请求
- **THEN** 系统调用RAG向量数据库执行检索
- **AND** 返回完整的检索结果（文档、元数据、相似度分数）

#### Scenario: 打印完整检索输出
- **WHEN** 检索完成
- **THEN** 系统格式化打印完整的检索结果
- **AND** 包含检索耗时、返回文档数、相似度分数等详细信息

### Requirement: 系统性比对方法
系统 SHALL 提供多维度比对方法验证检索准确性：

#### Scenario: 关键信息匹配验证
- **WHEN** 执行比对操作
- **THEN** 系统提取原始文档中的关键信息点
- **AND** 验证RAG检索结果是否包含这些关键信息

#### Scenario: 竞赛类别匹配验证
- **WHEN** 查询特定竞赛信息
- **THEN** 系统验证返回的竞赛类别是否与Excel列表一致
- **AND** 验证竞赛级别是否正确

#### Scenario: 分数规则验证
- **WHEN** 查询加分规则
- **THEN** 系统验证返回的分数是否与原始文档一致
- **AND** 记录任何不一致之处

### Requirement: 优化建议生成
系统 SHALL 根据比对结果生成优化建议：

#### Scenario: 发现检索不准确
- **WHEN** 比对发现检索结果与原文不一致
- **THEN** 系统分析可能的原因
- **AND** 提供具体的优化建议

#### Scenario: 生成测试报告
- **WHEN** 所有测试完成
- **THEN** 系统生成详细的测试报告
- **AND** 包含准确性统计、问题列表、优化建议

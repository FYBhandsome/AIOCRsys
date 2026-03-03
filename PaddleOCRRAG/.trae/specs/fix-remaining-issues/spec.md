# RAG系统问题全面修复规范

## Why

根据测试报告，RAG系统仍存在以下问题需要修复：
1. **学习成绩占比规则未找到**（严重程度：高）- 综合测评规则覆盖率仅87.5%
2. **源文档对比匹配率0%**（严重程度：中）- 检索结果与源文档内容不匹配
3. **AI与RAG集成问题** - 需要确保AI模型能正确使用RAG检索信息

## What Changes

- 修复学习成绩占比规则的检索问题
- 优化源文档对比验证逻辑
- 增强AI与RAG的集成能力
- 完善端到端测试验证

## Impact

- Affected specs: RAG检索模块、AI服务模块
- Affected code: 
  - `app/services/chat_service.py`
  - `app/rag/vector_db/vector_db.py`
  - `tests/test_rag_accuracy.py`

## ADDED Requirements

### Requirement: 学习成绩占比规则检索

系统 SHALL 能够正确检索学习成绩占比相关规则。

#### Scenario: 学习成绩占比查询
- **WHEN** 用户查询"学习成绩占比"或"学习成绩分计算"
- **THEN** 系统应返回包含"M=20%*A+70%*B+10%*C"公式的规则
- **AND** 返回结果应包含学习成绩分计算办法

### Requirement: 源文档对比验证

系统 SHALL 能够正确对比检索结果与源文档内容。

#### Scenario: 源文档对比
- **WHEN** 执行源文档对比验证时
- **THEN** 检索结果应与源文档内容高度匹配
- **AND** 相似度应达到50%以上

### Requirement: AI与RAG集成

系统 SHALL 确保AI模型能正确使用RAG检索信息生成响应。

#### Scenario: AI对话集成
- **WHEN** 用户通过AI对话查询规则信息
- **THEN** AI应基于RAG检索结果生成响应
- **AND** 响应内容应准确反映规则信息

## MODIFIED Requirements

### Requirement: 综合测评规则覆盖率

综合测评规则覆盖率应从87.5%提升到100%。

**修改前**: 覆盖率87.5%（7/8规则可检索）
**修改后**: 覆盖率100%（8/8规则可检索）

### Requirement: 测试通过率

测试通过率应从85.7%提升到100%。

**修改前**: 通过率85.7%（6/7通过）
**修改后**: 通过率100%（7/7通过）

## REMOVED Requirements

无移除的需求。

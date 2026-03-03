# RAG向量知识库切片策略优化规范

## Why

当前RAG系统的文档切片策略存在以下问题：
1. **切片尺寸过小**（500字符），导致关键信息被分割，检索时只能获取孤立关键词而丢失上下文
2. **切片重叠不足**（50字符），规则边界信息容易丢失
3. **分数规则验证准确率低**（27.1%），关键词覆盖不完整
4. 需要验证RAG核心流程是否正确实现检索增强生成

## What Changes

- **增大切片尺寸**: 从500字符增加到1000字符
- **增大切片重叠**: 从50字符增加到150字符
- **优化切片边界策略**: 确保规则完整性
- **验证RAG核心流程**: 确认向量化存储、检索增强、AI生成是否正确实现
- **更新README.md**: 完善项目文档，详细阐述设计逻辑和业务流程
- **更新测试文件**: 验证优化效果，确保准确度达到100%

## Impact

- Affected specs: RAG检索模块、文档加载模块
- Affected code: 
  - `app/rag/loaders/enhanced_loader.py`
  - `app/rag/loaders/loader.py`
  - `app/core/config_manager.py`
  - `tests/test_rag_accuracy.py`
  - `README.md`

## ADDED Requirements

### Requirement: 文档切片策略优化

系统 SHALL 采用优化的文档切片策略，确保检索信息的完整性和上下文连贯性。

#### Scenario: 切片尺寸优化
- **WHEN** 文档被加载和向量化时
- **THEN** 每个切片应包含至少1000字符（而非500字符）
- **AND** 切片间重叠应至少150字符（而非50字符）
- **AND** 切片边界应优先在段落边界处分割

#### Scenario: 规则完整性保证
- **WHEN** 规则文档被切片时
- **THEN** 每个切片应包含完整的规则描述
- **AND** 不应出现规则被截断导致语义不完整的情况
- **AND** 分数信息应与对应规则在同一切片中

### Requirement: RAG核心流程验证

系统 SHALL 正确实现RAG的核心流程：向量化存储、检索增强、AI生成。

#### Scenario: 向量化存储验证
- **WHEN** 文档上传到系统时
- **THEN** 文档内容应被正确提取并转换为向量
- **AND** 向量应存储在ChromaDB中
- **AND** 元数据应正确关联

#### Scenario: 检索增强验证
- **WHEN** 用户提交查询时
- **THEN** 系统应从向量库检索相关信息
- **AND** 检索结果应与用户提示词有效结合
- **AND** 组合信息应传递给AI模型

#### Scenario: AI生成验证
- **WHEN** AI模型接收到增强后的提示词
- **THEN** 模型应基于检索上下文生成响应
- **AND** 响应应准确反映规则内容

### Requirement: 测试准确度达标

系统 SHALL 通过所有RAG测试，准确度达到100%。

#### Scenario: 竞赛类别验证
- **WHEN** 执行竞赛类别匹配测试时
- **THEN** 所有测试用例应正确匹配
- **AND** 准确率应达到100%

#### Scenario: 分数规则验证
- **WHEN** 执行分数规则检索测试时
- **THEN** 关键词覆盖率应达到100%
- **AND** 分数信息应完整准确

## MODIFIED Requirements

### Requirement: 配置参数调整

当前配置参数需要更新以支持优化的切片策略。

**修改前**:
```python
chunk_size: int = 500
chunk_overlap: int = 50
```

**修改后**:
```python
chunk_size: int = 1000
chunk_overlap: int = 150
```

### Requirement: 切片分隔符优先级

切片分隔符优先级需要调整以更好地处理中文规则文档。

**修改前**:
```python
separators: List[str] = ["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
```

**修改后**:
```python
separators: List[str] = ["\n\n", "。\n", "。\r\n", "\n", "。", "！", "？", "；", "，", " ", ""]
```

## REMOVED Requirements

无移除的需求。

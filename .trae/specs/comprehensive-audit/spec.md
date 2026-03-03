# 全面业务逻辑与技术实现审查 Spec

## Why
当前项目需要进行全面的业务逻辑完整性检查、表格映射关系验证、功能实现细节审查、测试脚本开发以及代码优化，以确保系统稳定性、功能完整性和代码质量。

## What Changes
- 修复前端API与后端接口的不匹配问题
- 完善Excel表格字段映射关系，确保与需求描述一致
- 补充缺失的前端API接口定义
- 优化RAG提示词确保返回标准JSON格式
- 创建JavaScript测试文件进行功能验证
- 清理冗余代码和优化项目结构
- **BREAKING** 修正列索引映射，可能影响现有Excel填充功能

## Impact
- Affected specs: 业务逻辑完整性、数据映射准确性、API接口一致性
- Affected code: 
  - `visual_model/app/services/excel_fill_service.py` - Excel填充服务
  - `visual_model/app/services/field_mapping_service.py` - 字段映射服务
  - `fronted/front/src/services/api.js` - 前端API服务
  - `visual_model/app/core/comprehensive_prompts.py` - RAG提示词
  - `PaddleOCRRAG/app/rag/vector_db/vector_db.py` - 向量数据库

## ADDED Requirements

### Requirement: 前端API接口补充
系统 SHALL 在前端API服务中补充以下缺失的接口定义：

```javascript
// studentAPI 中需补充
uploadMaterial: (formData) => api.post('/v1/student/material/upload', formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
  timeout: 120000
}),
getMaterials: () => api.get('/v1/student/materials'),
```

#### Scenario: 材料上传功能
- **WHEN** 学生上传材料时
- **THEN** 前端应能正确调用后端接口
- **AND** 返回上传结果

### Requirement: Excel列映射修正
系统 SHALL 按照需求描述修正Excel列映射关系：

| 列标 | 字段名 | 代码列索引 |
|------|--------|-----------|
| A | 总排名 | 1 |
| B | 专业 | 2 |
| C | 班级 | 3 |
| D | 姓名 | 4 |
| E | 学号 | 5 |
| F | A1—基础分 | 6 |
| G | A2—附加分 | 7 |
| H | A3—扣分项 | 8 |
| I | 思想道德素质(A)总分 | 9 |
| J | 思想道德素质(A)总分% | 10 |
| K | 学习成绩 | 11 |
| L | 学习成绩% | 12 |
| M | 学习成绩70% | 13 |
| N | C1—科技竞赛项目 | 14 |
| O | C2—体育竞技项目 | 15 |
| P | C3—文化类竞赛项目 | 16 |
| Q | C4—创新创业实践项目 | 17 |
| R | 素质拓展(C)总分 | 18 |
| S | 素质拓展(C)总分10% | 19 |
| T | 综合测评总成绩 | 20 |
| U | 学生签字 | 21 |

#### Scenario: Excel填充列映射
- **WHEN** 系统填充Excel数据时
- **THEN** 应使用正确的列索引
- **AND** 数据应填充到正确的列位置

### Requirement: RAG响应JSON格式保证
系统 SHALL 确保RAG服务返回标准JSON格式数据：

1. 在提示词中明确要求返回纯JSON
2. 添加JSON解析失败的重试机制
3. 提供默认值兜底方案

#### Scenario: JSON解析失败处理
- **WHEN** RAG返回非标准JSON时
- **THEN** 系统应尝试多种解析方式
- **AND** 解析失败时返回默认配置

### Requirement: JavaScript测试文件创建
系统 SHALL 创建完整的JavaScript测试文件：

1. 测试前端API接口调用
2. 测试数据上传和下载流程
3. 测试AI对话功能
4. 测试综测计算流程

#### Scenario: API接口测试
- **WHEN** 执行测试脚本时
- **THEN** 应验证所有API接口可访问性
- **AND** 记录测试结果和覆盖率

### Requirement: 冗余代码清理
系统 SHALL 清理以下冗余代码：

1. 重复的日志配置模块（保留统一模块）
2. 未使用的测试文件
3. 废弃的API路由
4. 重复的工具函数

#### Scenario: 代码清理验证
- **WHEN** 清理完成后
- **THEN** 项目应能正常运行
- **AND** 所有测试用例通过

### Requirement: RAG向量切片优化
系统 SHALL 优化RAG向量切片策略：

1. 调整chunk_size为500字符
2. 设置chunk_overlap为50字符
3. 按段落和句子边界切分
4. 添加元数据标签

#### Scenario: 向量检索优化
- **WHEN** 用户查询综测规则时
- **THEN** 系统应返回最相关的规则片段
- **AND** 响应时间小于2秒

## MODIFIED Requirements

### Requirement: Excel填充服务列映射修正
原 `visual_model/app/services/excel_fill_service.py` 中的 `_fill_student_row` 方法 SHALL 修正列映射：

**修改前：**
```python
col_map = {
    'A1—基础分': 6,
    'A2—附加分': 7,
    'A3—扣罚分': 8,
    ...
    '综合测评总成绩': 19  # 错误：应为20
}
```

**修改后：**
```python
col_map = {
    'A1—基础分': 6,
    'A2—附加分': 7,
    'A3—扣分项': 8,  # 修正名称
    '思想道德素质(A)总分': 9,
    '思想道德素质(A)总分%': 10,  # 新增
    '学习成绩': 11,
    '学习成绩%': 12,  # 新增
    '学习成绩70%': 13,
    'C1—科技竞赛项目': 14,
    'C2—体育竞技项目': 15,
    'C3—文化类竞赛项目': 16,
    'C4—创新创业实践项目': 17,
    '素质拓展(C)总分': 18,
    '素质拓展(C)总分10%': 19,
    '综合测评总成绩': 20  # 修正
}
```

### Requirement: 字段映射服务完善
原 `visual_model/app/services/field_mapping_service.py` SHALL 完善字段映射：

1. 添加成绩百分比列的计算
2. 修正加减分说明表的填充逻辑
3. 添加数据验证机制

## REMOVED Requirements

### Requirement: 废弃重复的日志配置
**Reason**: 已有统一的 `shared_utils/unified_logger.py` 模块
**Migration**: 
- 保留 `enhanced_logger.py` 作为兼容层
- 删除其他重复的日志配置代码

### Requirement: 废弃未使用的API端点
**Reason**: 部分API端点已废弃或合并
**Migration**: 
- 清理 `visual_model/app/api/` 中未使用的路由
- 更新API文档

## 问题清单与优先级

### P0 - 严重问题（立即修复）
1. 前端 `studentAPI.uploadMaterial` 和 `studentAPI.getMaterials` 未定义
2. Excel填充服务列映射与需求描述不一致
3. RAG响应JSON解析可能失败导致系统崩溃

### P1 - 高优先级（本周修复）
1. 字段映射服务缺少百分比列计算
2. 加减分说明表填充逻辑不完整
3. 缺少JavaScript测试文件

### P2 - 中优先级（两周内修复）
1. RAG向量切片策略优化
2. 代码冗余清理
3. API接口文档更新

### P3 - 低优先级（后续迭代）
1. 性能优化
2. 日志格式统一
3. 错误处理增强

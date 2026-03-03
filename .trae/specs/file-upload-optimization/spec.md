# 文件上传逻辑全面优化 Spec

## Why
当前文件上传功能存在以下问题：
1. Excel文件解析使用固定列索引，与实际数据源表格结构不匹配
2. 前端上传组件未实际调用后端API，仅模拟上传
3. 缺少文件格式验证、结构完整性检查和数据校验逻辑
4. 错误处理机制不完善，无法给用户提供明确的错误反馈
5. 部分API接口与前端对接不完整

## What Changes
- 重构Excel解析服务，支持动态列映射和结构验证
- 完善前端上传组件，实现实际API调用
- 添加文件格式验证、结构完整性检查
- 实现数据校验逻辑和错误处理机制
- 完善前后端API对接逻辑
- 添加综测计算表格上传和解析功能

## Impact
- Affected specs: 文件上传、成绩导入、综测计算
- Affected code: 
  - `visual_model/app/services/score_service.py`
  - `visual_model/app/api/teacher.py`
  - `visual_model/app/api/student.py`
  - `fronted/front/src/views/ScoreUpload.vue`
  - `fronted/front/src/components/FileUpload.vue`
  - `fronted/front/src/services/api.js`

## ADDED Requirements

### Requirement: Excel文件结构验证
系统 SHALL 在解析Excel文件前验证文件结构是否符合预期格式。

#### Scenario: 验证学生成绩单结构
- **WHEN** 教师上传学生成绩单Excel文件
- **THEN** 系统验证文件包含必需的列（学号、姓名、班级等）
- **AND** 系统返回结构验证结果，包括缺失列和多余列

#### Scenario: 验证综测计算表格结构
- **WHEN** 教师上传综测计算表格Excel文件
- **THEN** 系统验证文件包含所有必需的评分列（A1-A3, B, C1-C4等）
- **AND** 系统返回结构验证结果

### Requirement: 动态列映射
系统 SHALL 支持动态识别Excel列标题并映射到对应字段。

#### Scenario: 自动识别列标题
- **WHEN** Excel文件的列顺序与预期不同
- **THEN** 系统通过列标题自动识别并映射到正确字段
- **AND** 解析结果正确对应各字段

#### Scenario: 处理列标题变体
- **WHEN** Excel文件使用不同的列标题命名（如"学号"或"学生学号"）
- **THEN** 系统识别常见变体并正确映射

### Requirement: 数据校验逻辑
系统 SHALL 对导入的数据进行完整性和有效性校验。

#### Scenario: 学号格式校验
- **WHEN** 导入的学号格式不正确
- **THEN** 系统记录错误并跳过该行
- **AND** 返回详细的错误信息

#### Scenario: 数值范围校验
- **WHEN** 成绩数值超出合理范围
- **THEN** 系统标记异常数据
- **AND** 提供修正建议

### Requirement: 前端上传组件完善
前端上传组件 SHALL 实际调用后端API并处理响应。

#### Scenario: 成绩单上传成功
- **WHEN** 教师选择正确的Excel文件并点击上传
- **THEN** 组件调用后端API上传文件
- **AND** 显示上传进度和结果

#### Scenario: 上传失败处理
- **WHEN** 上传过程中发生错误
- **THEN** 组件显示具体错误信息
- **AND** 提供重试选项

### Requirement: 综测计算表格上传
系统 SHALL 支持综测计算表格的上传和解析。

#### Scenario: 上传综测计算表格
- **WHEN** 教师上传综测计算表格Excel文件
- **THEN** 系统解析表格中的综测数据
- **AND** 更新学生的综测成绩记录

### Requirement: 错误处理机制
系统 SHALL 提供完善的错误处理和用户反馈机制。

#### Scenario: 文件格式错误
- **WHEN** 上传的文件格式不支持
- **THEN** 返回明确的错误提示，说明支持的格式

#### Scenario: 数据解析错误
- **WHEN** Excel文件数据解析失败
- **THEN** 返回具体错误位置和原因
- **AND** 提供修正建议

## MODIFIED Requirements

### Requirement: 成绩导入服务
原有成绩导入服务 SHALL 增强为支持多种Excel格式的通用解析服务。

#### 新增功能
- 动态列标题识别
- 结构验证
- 数据校验
- 详细错误报告

## REMOVED Requirements
无移除的需求。

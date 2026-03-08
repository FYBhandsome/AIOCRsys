# API 接口文档

## 目录
- [基础配置](#基础配置)
- [认证接口](#认证接口)
- [学生接口](#学生接口)
- [教师接口](#教师接口)
- [管理员接口](#管理员接口)
- [RAG 接口](#rag-接口)
- [数据导入接口](#数据导入接口)
- [综合成绩接口](#综合成绩接口)
- [Excel 填充接口](#excel-填充接口)
- [字段映射接口](#字段映射接口)
- [成绩上传接口](#成绩上传接口)
- [证书接口](#证书接口)
- [文件管理接口](#文件管理接口)
- [通用接口](#通用接口)

---

## 基础配置

### API 配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| BASE_URL | 主后端服务代理路径 | /api |
| RAG_BASE_URL | RAG 服务代理路径 | /rag-api |
| TIMEOUT | 请求超时时间 | 30000ms |
| RETRY_TIMES | 重试次数 | 3 |

### 上传配置

| 配置项 | 说明 | 值 |
|--------|------|-----|
| MAX_SIZE | 最大文件大小 | 10MB |
| ALLOWED_TYPES | 允许的文件类型 | image/jpeg, image/png, image/gif, application/pdf |
| ALLOWED_EXTENSIONS | 允许的文件扩展名 | .jpg, .jpeg, .png, .gif, .pdf |

### 任务状态

| 状态 | 说明 |
|------|------|
| pending | 等待处理 |
| processing | 处理中 |
| completed | 已完成 |
| failed | 处理失败 |

---

## 认证接口

### 登录
- **接口路径**: `/v1/auth/login`
- **请求方法**: POST
- **请求参数**:
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **响应格式**: JSON

### 注册
- **接口路径**: `/v1/auth/register`
- **请求方法**: POST
- **请求参数**: 用户数据对象
- **响应格式**: JSON

### 获取用户信息
- **接口路径**: `/v1/auth/me`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

### 登出
- **接口路径**: `/v1/auth/logout`
- **请求方法**: POST
- **请求参数**: 无
- **响应格式**: JSON

### 请求重置密码
- **接口路径**: `/v1/auth/password/reset-request`
- **请求方法**: POST
- **请求参数**:
  ```json
  {
    "email": "string"
  }
  ```
- **响应格式**: JSON

### 确认重置密码
- **接口路径**: `/v1/auth/password/reset-confirm`
- **请求方法**: POST
- **请求参数**:
  ```json
  {
    "email": "string",
    "verification_code": "string",
    "new_password": "string"
  }
  ```
- **响应格式**: JSON

---

## 学生接口

### 上传证书
- **接口路径**: `/v1/student/certificate/upload`
- **请求方法**: POST
- **请求参数**: FormData
  - `file`: 文件
- **响应格式**: JSON
- **超时时间**: 60000ms

### 获取成绩摘要
- **接口路径**: `/v1/student/scores/summary`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

### 获取成绩详情
- **接口路径**: `/v1/student/scores/detail`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

### 获取上传历史
- **接口路径**: `/v1/student/uploads`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

### 获取综合分析
- **接口路径**: `/v1/student/comprehensive/analysis`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

### 获取成绩趋势
- **接口路径**: `/v1/student/scores/trend`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

### 上传材料
- **接口路径**: `/v1/student/material/upload`
- **请求方法**: POST
- **请求参数**: FormData
- **响应格式**: JSON
- **超时时间**: 120000ms

### 获取材料列表
- **接口路径**: `/v1/student/materials`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

---

## 教师接口

### 上传成绩
- **接口路径**: `/v1/teacher/scores/upload`
- **请求方法**: POST
- **请求参数**: FormData
  - `file`: 文件
  - `class_id`: 班级ID (可选)
  - `academic_year`: 学年 (可选)
  - `semester`: 学期 (可选)
- **响应格式**: JSON
- **超时时间**: 120000ms

### 预览成绩
- **接口路径**: `/v1/teacher/scores/preview`
- **请求方法**: POST
- **请求参数**: FormData
  - `file`: 文件
  - `rows`: 行数 (默认10)
- **响应格式**: JSON
- **超时时间**: 60000ms

### 获取学生列表
- **接口路径**: `/v1/teacher/students`
- **请求方法**: GET
- **请求参数**:
  - `class_id`: 班级ID (可选)
- **响应格式**: JSON

### 获取学生详情
- **接口路径**: `/v1/teacher/students/{studentId}`
- **请求方法**: GET
- **路径参数**: `studentId` - 学生ID
- **响应格式**: JSON

### 创建学生
- **接口路径**: `/v1/teacher/students`
- **请求方法**: POST
- **请求参数**: 学生数据对象
- **响应格式**: JSON

### 更新学生
- **接口路径**: `/v1/teacher/students/{studentId}`
- **请求方法**: PUT
- **路径参数**: `studentId` - 学生ID
- **请求参数**: 学生数据对象
- **响应格式**: JSON

### 删除学生
- **接口路径**: `/v1/teacher/students/{studentId}`
- **请求方法**: DELETE
- **路径参数**: `studentId` - 学生ID
- **响应格式**: JSON

### 重置学生密码
- **接口路径**: `/v1/teacher/students/{studentId}/reset-password`
- **请求方法**: POST
- **路径参数**: `studentId` - 学生ID
- **响应格式**: JSON

### 更新学生状态
- **接口路径**: `/v1/teacher/students/{studentId}/status`
- **请求方法**: PATCH
- **路径参数**: `studentId` - 学生ID
- **请求参数**:
  ```json
  {
    "status": "string"
  }
  ```
- **响应格式**: JSON

### 导入学生
- **接口路径**: `/v1/teacher/students/import`
- **请求方法**: POST
- **请求参数**: FormData
- **响应格式**: JSON

### 导出学生
- **接口路径**: `/v1/teacher/students/export`
- **请求方法**: GET
- **请求参数**: 查询参数
- **响应格式**: Blob

### 获取学生成绩
- **接口路径**: `/v1/teacher/students/{studentId}/scores`
- **请求方法**: GET
- **路径参数**: `studentId` - 学生ID
- **响应格式**: JSON

### 获取学生成绩详情
- **接口路径**: `/v1/teacher/students/{studentId}/score-detail`
- **请求方法**: GET
- **路径参数**: `studentId` - 学生ID
- **响应格式**: JSON

### 获取班级列表
- **接口路径**: `/v1/teacher/classes`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

### 获取班级统计
- **接口路径**: `/v1/teacher/classes/stats`
- **请求方法**: GET
- **请求参数**:
  - `class_id`: 班级ID
- **响应格式**: JSON

### 获取班级排名
- **接口路径**: `/v1/teacher/classes/ranking`
- **请求方法**: GET
- **请求参数**:
  - `class_id`: 班级ID
- **响应格式**: JSON

### 获取班级学生排名
- **接口路径**: `/v1/teacher/classes/{classId}/student-ranking`
- **请求方法**: GET
- **路径参数**: `classId` - 班级ID
- **响应格式**: JSON

### 导出班级排名
- **接口路径**: `/v1/teacher/classes/ranking/export`
- **请求方法**: GET
- **请求参数**: 查询参数
- **响应格式**: Blob

### 上传综合成绩
- **接口路径**: `/v1/teacher/comprehensive/upload`
- **请求方法**: POST
- **请求参数**: FormData
  - `file`: 文件
  - `academic_year`: 学年 (可选)
  - `semester`: 学期 (可选)
- **响应格式**: JSON
- **超时时间**: 180100ms

### 获取综合成绩列表
- **接口路径**: `/v1/teacher/comprehensive/list`
- **请求方法**: GET
- **请求参数**: 查询参数
- **响应格式**: JSON

### 获取成绩分布
- **接口路径**: `/v1/teacher/analysis/distribution`
- **请求方法**: GET
- **请求参数**: 查询参数
- **响应格式**: JSON

### 获取科目对比
- **接口路径**: `/v1/teacher/analysis/subject-comparison`
- **请求方法**: GET
- **请求参数**: 查询参数
- **响应格式**: JSON

### 获取成绩趋势
- **接口路径**: `/v1/teacher/analysis/trend`
- **请求方法**: GET
- **请求参数**: 查询参数
- **响应格式**: JSON

### 获取班级对比
- **接口路径**: `/v1/teacher/analysis/class-comparison`
- **请求方法**: GET
- **请求参数**: 查询参数
- **响应格式**: JSON

### 获取成绩相关性
- **接口路径**: `/v1/teacher/analysis/correlation`
- **请求方法**: GET
- **请求参数**: 查询参数
- **响应格式**: JSON

### 导出分析数据
- **接口路径**: `/v1/teacher/analysis/export`
- **请求方法**: GET
- **请求参数**: 查询参数
- **响应格式**: Blob

---

## 管理员接口

### 上传规则文档
- **接口路径**: `/v1/admin/rules/upload`
- **请求方法**: POST
- **请求参数**: FormData
  - `file`: 文件
  - `description`: 描述 (可选)
- **响应格式**: JSON
- **超时时间**: 60000ms

### 获取规则文档列表
- **接口路径**: `/v1/admin/rules/list`
- **请求方法**: GET
- **请求参数**:
  - `enabled_only`: 仅启用 (可选，默认false)
- **响应格式**: JSON

### 更新规则状态
- **接口路径**: `/v1/admin/rules/{docId}/status`
- **请求方法**: PATCH
- **路径参数**: `docId` - 文档ID
- **请求参数**:
  ```json
  {
    "enabled": "boolean"
  }
  ```
- **响应格式**: JSON

### 删除规则文档
- **接口路径**: `/v1/admin/rules/{docId}`
- **请求方法**: DELETE
- **路径参数**: `docId` - 文档ID
- **请求参数**:
  - `delete_file`: 删除文件 (可选)
- **响应格式**: JSON

### 更新规则
- **接口路径**: `/v1/admin/rules/{ruleId}`
- **请求方法**: PATCH
- **路径参数**: `ruleId` - 规则ID
- **请求参数**: 规则数据对象
- **响应格式**: JSON

### 删除规则
- **接口路径**: `/v1/admin/rules/{ruleId}`
- **请求方法**: DELETE
- **路径参数**: `ruleId` - 规则ID
- **响应格式**: JSON

### 获取 AI 配置
- **接口路径**: `/v1/admin/ai/config`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

### 更新 AI 配置
- **接口路径**: `/v1/admin/ai/config`
- **请求方法**: PUT
- **请求参数**: 配置数据对象
- **响应格式**: JSON

### 测试 AI 连接
- **接口路径**: `/v1/admin/ai/config/test`
- **请求方法**: POST
- **请求参数**: 无
- **响应格式**: JSON

### 重置 AI 配置
- **接口路径**: `/v1/admin/ai/config/reset`
- **请求方法**: POST
- **请求参数**: 无
- **响应格式**: JSON

### 验证 AI 配置
- **接口路径**: `/v1/admin/ai/config/validate`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

### 获取系统设置
- **接口路径**: `/v1/admin/settings`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

### 更新系统设置
- **接口路径**: `/v1/admin/settings`
- **请求方法**: PUT
- **请求参数**: 设置数据对象
- **响应格式**: JSON

### 获取用户列表
- **接口路径**: `/v1/admin/users`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

### 创建用户
- **接口路径**: `/v1/admin/users`
- **请求方法**: POST
- **请求参数**: 用户数据对象
- **响应格式**: JSON

### 更新用户
- **接口路径**: `/v1/admin/users/{userId}`
- **请求方法**: PUT
- **路径参数**: `userId` - 用户ID
- **请求参数**: 用户数据对象
- **响应格式**: JSON

### 删除用户
- **接口路径**: `/v1/admin/users/{userId}`
- **请求方法**: DELETE
- **路径参数**: `userId` - 用户ID
- **响应格式**: JSON

### 获取提示词
- **接口路径**: `/v1/admin/prompts`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

### 更新提示词
- **接口路径**: `/v1/admin/prompts`
- **请求方法**: PUT
- **请求参数**: 提示词数据对象
- **响应格式**: JSON

### 重置提示词
- **接口路径**: `/v1/admin/prompts/reset`
- **请求方法**: POST
- **请求参数**: 无
- **响应格式**: JSON

### 获取向量数据库统计
- **接口路径**: `/v1/admin/vector-db/stats`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

### 清空向量数据库
- **接口路径**: `/v1/admin/vector-db/clear`
- **请求方法**: POST
- **请求参数**: 无
- **响应格式**: JSON

### 重置向量数据库
- **接口路径**: `/v1/admin/vector-db/reset`
- **请求方法**: POST
- **请求参数**:
  - `backup`: 是否备份 (可选，默认true)
- **响应格式**: JSON

### 重建向量数据库索引
- **接口路径**: `/v1/admin/vector-db/reindex`
- **请求方法**: POST
- **请求参数**: 无
- **响应格式**: JSON

### 获取向量数据库集合
- **接口路径**: `/v1/admin/vector-db/collections`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

### 获取向量数据库健康状态
- **接口路径**: `/v1/admin/vector-db/health`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

### 获取 RAG 统计
- **接口路径**: `/v1/admin/rag/stats`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

### RAG 健康检查
- **接口路径**: `/v1/admin/rag/health`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

---

## RAG 接口

### 聊天
- **接口路径**: `/chat`
- **请求方法**: POST
- **请求参数**:
  ```json
  {
    "message": "string",
    "chat_history": "array",
    "use_rag": "boolean"
  }
  ```
- **响应格式**: JSON

### 流式聊天
- **接口路径**: `/chat/stream`
- **请求方法**: POST
- **请求参数**:
  ```json
  {
    "message": "string",
    "chat_history": "array"
  }
  ```
- **响应格式**: SSE (Server-Sent Events)

### 异步聊天
- **接口路径**: `/chat/async`
- **请求方法**: POST
- **请求参数**:
  ```json
  {
    "message": "string",
    "chat_history": "array"
  }
  ```
- **响应格式**: JSON

### 获取文档列表
- **接口路径**: `/documents`
- **请求方法**: GET
- **请求参数**:
  - `category`: 分类 (可选)
  - `tags`: 标签 (可选)
- **响应格式**: JSON

### 获取文档详情
- **接口路径**: `/documents/{docId}`
- **请求方法**: GET
- **路径参数**: `docId` - 文档ID
- **响应格式**: JSON

### 删除文档
- **接口路径**: `/documents/{docId}`
- **请求方法**: DELETE
- **路径参数**: `docId` - 文档ID
- **响应格式**: JSON

### 获取系统信息
- **接口路径**: `/system/info`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

### 获取系统健康状态
- **接口路径**: `/system/health`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

### 获取 LLM 配置
- **接口路径**: `/system/llm/config`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

### 更新 LLM 配置
- **接口路径**: `/system/llm/config`
- **请求方法**: PUT
- **请求参数**: 配置数据对象
- **响应格式**: JSON

### 测试 LLM 连接
- **接口路径**: `/system/llm/test`
- **请求方法**: POST
- **请求参数**: 无
- **响应格式**: JSON

### 获取向量数据库统计
- **接口路径**: `/vector-db/stats`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

### 获取提示词
- **接口路径**: `/prompts`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

### 更新提示词
- **接口路径**: `/prompts`
- **请求方法**: PUT
- **请求参数**: 提示词数据对象
- **响应格式**: JSON

### 重置提示词
- **接口路径**: `/prompts/reset`
- **请求方法**: POST
- **请求参数**: 无
- **响应格式**: JSON

### 获取缓存统计
- **接口路径**: `/chat/cache/stats`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

### 清空缓存
- **接口路径**: `/chat/cache`
- **请求方法**: DELETE
- **请求参数**: 无
- **响应格式**: JSON

### 获取聊天历史
- **接口路径**: `/ai/history`
- **请求方法**: GET
- **请求参数**:
  - `limit`: 限制数量 (默认20)
  - `session_id`: 会话ID (可选)
- **响应格式**: JSON

### 清空聊天历史
- **接口路径**: `/ai/history`
- **请求方法**: DELETE
- **请求参数**:
  - `session_id`: 会话ID (可选)
- **响应格式**: JSON

---

## 数据导入接口

### 导入 Excel
- **接口路径**: `/v1/data-import/excel`
- **请求方法**: POST
- **请求参数**: FormData
  - `file`: 文件
  - `academic_year`: 学年 (可选)
  - `semester`: 学期 (可选)
  - `class_id`: 班级ID (可选)
- **响应格式**: JSON
- **超时时间**: 120000ms

### 获取模板
- **接口路径**: `/v1/data-import/template`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

### 预览 Excel
- **接口路径**: `/v1/data-import/preview`
- **请求方法**: POST
- **请求参数**: FormData
  - `file`: 文件
  - `rows`: 行数 (默认10)
- **响应格式**: JSON

---

## 综合成绩接口

### 计算学生综合成绩
- **接口路径**: `/v1/comprehensive-score/calculate/student/{studentId}`
- **请求方法**: POST
- **路径参数**: `studentId` - 学生ID
- **请求参数**:
  - `academic_year`: 学年
  - `semester`: 学期
  - `config_id`: 配置ID (可选)
- **响应格式**: JSON

### 计算班级综合成绩
- **接口路径**: `/v1/comprehensive-score/calculate/class/{classId}`
- **请求方法**: POST
- **路径参数**: `classId` - 班级ID
- **请求参数**:
  - `academic_year`: 学年
  - `semester`: 学期
  - `config_id`: 配置ID (可选)
- **响应格式**: JSON

### 获取学生综合成绩
- **接口路径**: `/v1/comprehensive-score/student/{studentId}`
- **请求方法**: GET
- **路径参数**: `studentId` - 学生ID
- **请求参数**:
  - `academic_year`: 学年
  - `semester`: 学期
- **响应格式**: JSON

### 获取班级排名
- **接口路径**: `/v1/comprehensive-score/class/{classId}/ranking`
- **请求方法**: GET
- **路径参数**: `classId` - 班级ID
- **请求参数**:
  - `academic_year`: 学年
  - `semester`: 学期
- **响应格式**: JSON

### 添加成绩详情
- **接口路径**: `/v1/comprehensive-score/detail`
- **请求方法**: POST
- **请求参数**: 成绩详情数据对象
- **响应格式**: JSON

### 删除成绩详情
- **接口路径**: `/v1/comprehensive-score/detail/{detailId}`
- **请求方法**: DELETE
- **路径参数**: `detailId` - 详情ID
- **响应格式**: JSON

### 获取配置列表
- **接口路径**: `/v1/comprehensive-score/config/list`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

### 创建配置
- **接口路径**: `/v1/comprehensive-score/config`
- **请求方法**: POST
- **请求参数**: 配置数据对象
- **响应格式**: JSON

### 更新配置
- **接口路径**: `/v1/comprehensive-score/config/{configId}`
- **请求方法**: PUT
- **路径参数**: `configId` - 配置ID
- **请求参数**: 配置数据对象
- **响应格式**: JSON

### 获取班级列表
- **接口路径**: `/v1/comprehensive-score/classes`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

### 获取班级统计
- **接口路径**: `/v1/comprehensive-score/class/{classId}/stats`
- **请求方法**: GET
- **路径参数**: `classId` - 班级ID
- **请求参数**:
  - `academic_year`: 学年
  - `semester`: 学期
- **响应格式**: JSON

---

## Excel 填充接口

### 从模板填充
- **接口路径**: `/v1/excel-fill/from-template`
- **请求方法**: POST
- **请求参数**: FormData
  - `template_file`: 模板文件
  - `raw_data_file`: 原始数据文件
  - `academic_year`: 学年 (可选)
  - `semester`: 学期 (可选)
  - `class_id`: 班级ID (可选)
- **响应格式**: Blob
- **超时时间**: 180100ms

### 处理 OCR
- **接口路径**: `/v1/excel-fill/process-ocr`
- **请求方法**: POST
- **请求参数**: OCR 数据对象
- **响应格式**: JSON

### 批量处理
- **接口路径**: `/v1/excel-fill/batch-process`
- **请求方法**: POST
- **请求参数**: 批量处理数据对象
- **响应格式**: JSON

### 获取权重配置
- **接口路径**: `/v1/excel-fill/weight-config`
- **请求方法**: GET
- **请求参数**:
  - `academic_year`: 学年
  - `semester`: 学期
- **响应格式**: JSON

### 分析证书
- **接口路径**: `/v1/excel-fill/analyze-certificate`
- **请求方法**: POST
- **请求参数**: FormData
  - `certificate_text`: 证书文本
  - `student_id`: 学生ID (可选)
  - `student_name`: 学生姓名 (可选)
- **响应格式**: JSON

### 检索规则
- **接口路径**: `/v1/excel-fill/retrieve-rules`
- **请求方法**: POST
- **请求参数**: FormData
  - `query`: 查询
- **响应格式**: JSON

### 计算成绩
- **接口路径**: `/v1/excel-fill/calculate-score`
- **请求方法**: POST
- **请求参数**: FormData
  - `student_id`: 学生ID
  - `student_name`: 学生姓名
  - `class_name`: 班级名称
  - `academic_info`: 学业信息 (JSON)
  - `certificate_info`: 证书信息 (JSON)
  - `score_details`: 成绩详情 (JSON)
- **响应格式**: JSON

### 获取模板列
- **接口路径**: `/v1/excel-fill/template-columns`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

---

## 字段映射接口

### 处理并填充
- **接口路径**: `/v1/field-mapping/process`
- **请求方法**: POST
- **请求参数**: FormData
  - `source_file`: 源文件
  - `template_file`: 模板文件
  - `academic_year`: 学年 (可选)
  - `semester`: 学期 (可选)
  - `output_dir`: 输出目录 (可选)
- **响应格式**: JSON
- **超时时间**: 180100ms

### 处理并下载
- **接口路径**: `/v1/field-mapping/download`
- **请求方法**: POST
- **请求参数**: FormData
  - `source_file`: 源文件
  - `template_file`: 模板文件
  - `academic_year`: 学年 (可选)
  - `semester`: 学期 (可选)
- **响应格式**: Blob
- **超时时间**: 180100ms

### 获取源字段
- **接口路径**: `/v1/field-mapping/source-fields`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

### 获取目标字段
- **接口路径**: `/v1/field-mapping/target-fields`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

### 预览源文件
- **接口路径**: `/v1/field-mapping/preview-source`
- **请求方法**: POST
- **请求参数**: FormData
  - `file`: 文件
  - `rows`: 行数 (默认10)
- **响应格式**: JSON

---

## 成绩上传接口

### 上传成绩
- **接口路径**: `/v1/score-upload/upload`
- **请求方法**: POST
- **请求参数**: FormData
  - `file`: 文件
  - `academic_year`: 学年
  - `semester`: 学期
  - `uploaded_by`: 上传人
  - `upload_role`: 上传角色 (可选)
- **响应格式**: JSON
- **超时时间**: 120000ms

### 获取历史记录
- **接口路径**: `/v1/score-upload/history/{studentId}`
- **请求方法**: GET
- **路径参数**: `studentId` - 学生ID
- **请求参数**:
  - `academic_year`: 学年 (可选)
  - `semester`: 学期 (可选)
- **响应格式**: JSON

### 获取上传记录
- **接口路径**: `/v1/score-upload/upload-records`
- **请求方法**: GET
- **请求参数**:
  - `upload_by`: 上传人 (可选)
  - `status`: 状态 (可选)
  - `limit`: 限制数量 (默认20)
- **响应格式**: JSON

### 获取字段映射
- **接口路径**: `/v1/score-upload/field-mapping`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

### 预览
- **接口路径**: `/v1/score-upload/preview`
- **请求方法**: POST
- **请求参数**: FormData
  - `file`: 文件
  - `rows`: 行数 (默认10)
- **响应格式**: JSON

---

## 证书接口

### 上传证书
- **接口路径**: `/v1/certificate/upload`
- **请求方法**: POST
- **请求参数**: FormData
  - `files`: 文件数组
  - `student_id`: 学生ID
  - `title`: 标题 (可选)
  - `certificate_type`: 证书类型 (可选)
  - `level`: 级别 (可选)
  - `issuer`: 颁发机构 (可选)
  - `issue_date`: 颁发日期 (可选)
  - `category`: 分类 (可选)
  - `sub_category`: 子分类 (可选)
  - `score`: 分数 (可选)
- **响应格式**: JSON
- **超时时间**: 120000ms

### 获取学生证书
- **接口路径**: `/v1/certificate/student/{studentId}`
- **请求方法**: GET
- **路径参数**: `studentId` - 学生ID
- **请求参数**:
  - `status`: 状态 (可选)
  - `category`: 分类 (可选)
- **响应格式**: JSON

### 获取证书详情
- **接口路径**: `/v1/certificate/{certificateId}`
- **请求方法**: GET
- **路径参数**: `certificateId` - 证书ID
- **响应格式**: JSON

### 删除证书
- **接口路径**: `/v1/certificate/{certificateId}`
- **请求方法**: DELETE
- **路径参数**: `certificateId` - 证书ID
- **请求参数**:
  - `deleted_by`: 删除人 (可选)
- **响应格式**: JSON

### 更新证书
- **接口路径**: `/v1/certificate/{certificateId}`
- **请求方法**: PUT
- **路径参数**: `certificateId` - 证书ID
- **请求参数**: FormData
- **响应格式**: JSON

### 获取统计信息
- **接口路径**: `/v1/certificate/statistics/{studentId}`
- **请求方法**: GET
- **路径参数**: `studentId` - 学生ID
- **响应格式**: JSON

### 批量更新状态
- **接口路径**: `/v1/certificate/batch-status`
- **请求方法**: POST
- **请求参数**:
  ```json
  {
    "certificate_ids": "array",
    "status": "string",
    "reviewed_by": "string (可选)",
    "review_comment": "string (可选)"
  }
  ```
- **响应格式**: JSON

---

## 文件管理接口

### 上传文件
- **接口路径**: `/v1/file/upload`
- **请求方法**: POST
- **请求参数**: FormData
  - `file`: 文件
  - `file_type`: 文件类型
  - `owner_id`: 所有者ID
  - `owner_type`: 所有者类型 (可选)
  - `is_public`: 是否公开 (可选)
  - `metadata`: 元数据 (可选，JSON)
- **响应格式**: JSON
- **超时时间**: 120000ms

### 批量上传文件
- **接口路径**: `/v1/file/upload-multiple`
- **请求方法**: POST
- **请求参数**: FormData
  - `files`: 文件数组
  - `file_type`: 文件类型
  - `owner_id`: 所有者ID
  - `owner_type`: 所有者类型 (可选)
- **响应格式**: JSON
- **超时时间**: 180100ms

### 初始化分片上传
- **接口路径**: `/v1/file/chunk/init`
- **请求方法**: POST
- **请求参数**:
  - `filename`: 文件名
  - `file_size`: 文件大小
  - `file_type`: 文件类型
  - `owner_id`: 所有者ID
  - `chunk_size`: 分片大小 (可选)
- **响应格式**: JSON

### 上传分片
- **接口路径**: `/v1/file/chunk/{fileId}/{chunkIndex}`
- **请求方法**: POST
- **路径参数**:
  - `fileId`: 文件ID
  - `chunkIndex`: 分片索引
- **请求参数**: FormData
  - `chunk`: 分片
  - `upload_ip`: 上传IP (可选)
- **响应格式**: JSON
- **超时时间**: 60000ms

### 完成分片上传
- **接口路径**: `/v1/file/chunk/{fileId}/complete`
- **请求方法**: POST
- **路径参数**: `fileId` - 文件ID
- **响应格式**: JSON

### 获取上传进度
- **接口路径**: `/v1/file/chunk/{fileId}/progress`
- **请求方法**: GET
- **路径参数**: `fileId` - 文件ID
- **响应格式**: JSON

### 下载文件
- **接口路径**: `/v1/file/download/{fileId}`
- **请求方法**: GET
- **路径参数**: `fileId` - 文件ID
- **请求参数**:
  - `user_id`: 用户ID (可选)
  - `user_type`: 用户类型 (可选，默认student)
- **响应格式**: Blob

### 下载结果
- **接口路径**: `/v1/file/download-result/{fileId}`
- **请求方法**: GET
- **路径参数**: `fileId` - 文件ID
- **请求参数**:
  - `user_id`: 用户ID (可选)
  - `user_type`: 用户类型 (可选，默认student)
- **响应格式**: Blob

### 获取文件信息
- **接口路径**: `/v1/file/info/{fileId}`
- **请求方法**: GET
- **路径参数**: `fileId` - 文件ID
- **响应格式**: JSON

### 列出文件
- **接口路径**: `/v1/file/list`
- **请求方法**: GET
- **请求参数**:
  - `owner_id`: 所有者ID (可选)
  - `file_type`: 文件类型 (可选)
  - `status`: 状态 (可选)
  - `limit`: 限制数量 (可选，默认20)
  - `offset`: 偏移量 (可选，默认0)
- **响应格式**: JSON

### 删除文件
- **接口路径**: `/v1/file/{fileId}`
- **请求方法**: DELETE
- **路径参数**: `fileId` - 文件ID
- **请求参数**:
  - `user_id`: 用户ID (可选)
  - `user_type`: 用户类型 (可选，默认student)
  - `backup`: 是否备份 (可选，默认true)
- **响应格式**: JSON

### 获取下载历史
- **接口路径**: `/v1/file/download-history`
- **请求方法**: GET
- **请求参数**:
  - `file_id`: 文件ID (可选)
  - `downloader_id`: 下载人ID (可选)
  - `limit`: 限制数量 (可选，默认50)
- **响应格式**: JSON

### 获取分类
- **接口路径**: `/v1/file/categories`
- **请求方法**: GET
- **请求参数**: 无
- **响应格式**: JSON

---

## 通用接口

### GET 请求
- **请求方法**: GET
- **用途**: 发送通用 GET 请求

### POST 请求
- **请求方法**: POST
- **用途**: 发送通用 POST 请求

### PUT 请求
- **请求方法**: PUT
- **用途**: 发送通用 PUT 请求

### DELETE 请求
- **请求方法**: DELETE
- **用途**: 发送通用 DELETE 请求

### PATCH 请求
- **请求方法**: PATCH
- **用途**: 发送通用 PATCH 请求

---

## 错误码说明

| 错误码 | 说明 |
|--------|------|
| NETWORK_ERROR | 网络错误 |
| TIMEOUT | 请求超时 |
| UNAUTHORIZED | 未授权 |
| FORBIDDEN | 禁止访问 |
| NOT_FOUND | 资源不存在 |
| VALIDATION_ERROR | 验证错误 |
| SERVER_ERROR | 服务器错误 |
| UNKNOWN | 未知错误 |

## HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 204 | 无内容 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 422 | 验证失败 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |
| 502 | 网关错误 |
| 503 | 服务不可用 |

---

*文档生成时间: 2026-03-06*

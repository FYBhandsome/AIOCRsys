# API接口清单文档

## 文档概述

本文档梳理了Visual Model后端系统的所有API接口，包括请求方法、路径、参数、响应格式等信息，用于后续的API测试和开发参考。

**生成日期**: 2026-03-06  
**系统版本**: 1.0.0  
**文档版本**: v1.0

---

## 目录

1. [认证模块 (auth.py)](#1-认证模块-authpy)
2. [学生模块 (student.py)](#2-学生模块-studentpy)
3. [教师模块 (teacher.py)](#3-教师模块-teacherpy)
4. [管理员模块 (admin.py)](#4-管理员模块-adminpy)
5. [成绩上传模块 (score_upload.py)](#5-成绩上传模块-score_uploadpy)
6. [证书上传模块 (certificate_upload.py)](#6-证书上传模块-certificate_uploadpy)
7. [班级管理模块 (class_.py)](#7-班级管理模块-class_py)
8. [综测成绩模块 (comprehensive_score.py)](#8-综测成绩模块-comprehensive_scorepy)
9. [AI助手模块 (ai.py)](#9-ai助手模块-aipy)
10. [文件管理模块 (file_management.py)](#10-文件管理模块-file_managementpy)
11. [数据导入模块 (data_import.py)](#11-数据导入模块-data_importpy)
12. [系统模块 (system_routes.py)](#12-系统模块-system_routespy)
13. [关键业务流程API](#13-关键业务流程api)

---

## 1. 认证模块 (auth.py)

### 路由前缀: `/auth`

| 序号 | 请求方法 | 请求路径 | 功能描述 | 必要参数 | 认证要求 | 响应格式 |
|-----|---------|---------|---------|---------|---------|---------|
| 1 | POST | `/register` | 用户注册 | `UserCreate` (username, password, role等) | 否 | `{message, username, user_id}` |
| 2 | POST | `/login` | 用户登录 | `UserLogin` (username, password) | 否 | `{access_token, expires_in}` |
| 3 | GET | `/me` | 获取当前用户信息 | 无 | 是 (Token) | `{id, username, email, role, ...}` |
| 4 | POST | `/password/reset-request` | 请求密码重置 | `PasswordResetRequest` (email) | 否 | `{message, expires_in}` |
| 5 | POST | `/password/reset-confirm` | 确认密码重置 | `PasswordResetConfirm` (email, verification_code, new_password) | 否 | `{message}` |
| 6 | POST | `/password/change` | 修改密码 | `PasswordChange` (old_password, new_password) | 是 (Token) | `{message}` |
| 7 | POST | `/logout` | 用户登出 | 无 | 是 (Token) | `{message}` |

**备注**:
- 注册时用户名、邮箱、学号均需唯一
- 登录失败返回401错误
- 密码重置验证码有效期2分钟

---

## 2. 学生模块 (student.py)

### 路由前缀: `/student`

| 序号 | 请求方法 | 请求路径 | 功能描述 | 必要参数 | 认证要求 | 响应格式 |
|-----|---------|---------|---------|---------|---------|---------|
| 1 | POST | `/certificate/upload` | 上传单张证书 | `file` (图片文件) | 是 (学生用户) | `OCRResult` |
| 2 | POST | `/certificate/upload/batch` | 批量上传证书 | `files` (图片文件列表，最多20张) | 是 (学生用户) | `{success, message, results, summary}` |
| 3 | GET | `/scores/summary` | 获取综合成绩摘要 | 无 | 是 (学生用户) | `{a_score, b_score, c_score, total_score, certificates, ...}` |
| 4 | GET | `/scores/detail` | 获取详细成绩 | 无 | 是 (学生用户) | `{student_id, academic_scores, moral_activities, certificates}` |
| 5 | GET | `/uploads` | 获取上传历史 | 无 | 是 (学生用户) | `[{id, filename, type, status, upload_time, ...}]` |
| 6 | GET | `/certificates` | 查看证书列表 | 无 | 是 (学生用户) | `{total, certificates, summary}` |
| 7 | GET | `/comprehensive/analysis` | 获取综合分析 | 无 | 是 (学生用户) | `{student_id, academic_performance, certificate_performance, ...}` |
| 8 | GET | `/scores/trend` | 获取成绩趋势 | 无 | 是 (学生用户) | `{trend_data, summary}` |
| 9 | POST | `/material/upload` | 上传材料文件 | `file`, `material_type` | 是 (学生用户) | `{success, file_id, filename, message}` |
| 10 | GET | `/materials` | 获取材料列表 | `material_type` (可选) | 是 (学生用户) | `{student_id, materials, total}` |

**备注**:
- 证书上传后自动进行OCR识别、分类和加分计算
- 批量上传最多20张证书
- 材料文件支持: jpeg, png, gif, pdf

---

## 3. 教师模块 (teacher.py)

### 路由前缀: `/teacher`

| 序号 | 请求方法 | 请求路径 | 功能描述 | 必要参数 | 认证要求 | 响应格式 |
|-----|---------|---------|---------|---------|---------|---------|
| 1 | GET | `/classes` | 获取班级列表 | 无 | 是 (教师用户) | `[{id, name, grade, major, student_count, ...}]` |
| 2 | POST | `/scores/upload` | 上传成绩单 | `file` (Excel), `semester`, `academic_year`, `sheet_name` (可选) | 是 (教师用户) | `{message, data: {total, imported, failed, errors}}` |
| 3 | GET | `/scores/analysis` | 成绩分析 | `class_name`, `semester`, `academic_year` (均可选) | 是 (教师用户) | `{class_name, total_students, statistics, distribution, top_10}` |
| 4 | GET | `/students` | 查看学生列表 | `class_name`, `grade`, `limit`, `offset` (均可选) | 是 (教师/管理员) | `{total, students}` |
| 5 | GET | `/students/{student_id}/scores` | 查看学生成绩 | `student_id`, `semester`, `academic_year` (可选) | 是 (教师用户) | `{student_id, student_name, total_records, scores}` |
| 6 | PUT | `/students/{student_id}/scores` | 修改学生成绩 | `student_id`, `score_data` | 是 (教师用户) | `{message}` |
| 7 | GET | `/classes/stats` | 获取班级统计 | `class_name`, `semester`, `academic_year` (均可选) | 是 (教师/管理员) | `{class_name, total_students, statistics, distribution}` |
| 8 | GET | `/classes/ranking` | 获取班级排名 | `class_name`, `semester`, `academic_year`, `limit`, `offset` (均可选) | 是 (教师/管理员) | `{class_name, total_students, rankings}` |
| 9 | GET | `/classes/ranking/export` | 导出班级排名 | `class_name`, `semester`, `academic_year` (均可选) | 是 (教师/管理员) | Excel文件下载 |
| 10 | GET | `/analysis/distribution` | 获取成绩分布 | `class_name`, `semester`, `academic_year` (均可选) | 是 (教师/管理员) | `{class_name, total_students, distribution, average}` |
| 11 | GET | `/analysis/subject-comparison` | 科目成绩对比 | `class_name`, `semester`, `academic_year` (均可选) | 是 (教师/管理员) | `{class_name, subjects}` |
| 12 | GET | `/analysis/trend` | 成绩趋势 | `class_name`, `student_id` (均可选) | 是 (教师/管理员) | `{class_name, student_id, trend, total_records}` |
| 13 | GET | `/analysis/class-comparison` | 班级对比 | `semester`, `academic_year` (均可选) | 是 (教师/管理员) | `{semester, academic_year, classes}` |
| 14 | GET | `/analysis/correlation` | 成绩相关性分析 | `class_name`, `semester`, `academic_year` (均可选) | 是 (教师/管理员) | `{class_name, sample_size, correlation}` |
| 15 | GET | `/analysis/export` | 导出分析数据 | `class_name`, `semester`, `academic_year` (均可选) | 是 (教师/管理员) | Excel文件下载 |
| 16 | POST | `/comprehensive/upload` | 上传综测表格 | `file` (Excel), `academic_year`, `semester` | 是 (教师用户) | `{message, data: {...}}` |

**备注**:
- 成绩单支持Excel格式 (.xlsx, .xls)
- 最大文件大小10MB
- 自动创建不存在的学生记录

---

## 4. 管理员模块 (admin.py)

### 路由前缀: `/admin`

#### 4.1 综测规则管理

| 序号 | 请求方法 | 请求路径 | 功能描述 | 必要参数 | 认证要求 | 响应格式 |
|-----|---------|---------|---------|---------|---------|---------|
| 1 | POST | `/rules/upload` | 上传规则文档 | `file`, `description` | 是 (管理员) | RAG上传结果 |
| 2 | GET | `/rules/list` | 获取规则文档列表 | `enabled_only` (可选) | 是 (管理员) | `{success, documents, message}` |
| 3 | PATCH | `/rules/{doc_id}/status` | 更新规则状态 | `doc_id`, `enabled` | 是 (管理员) | 更新结果 |
| 4 | DELETE | `/rules/{doc_id}` | 删除规则文档 | `doc_id`, `delete_file` (可选) | 是 (管理员) | 删除结果 |

#### 4.2 AI大模型配置管理

| 序号 | 请求方法 | 请求路径 | 功能描述 | 必要参数 | 认证要求 | 响应格式 |
|-----|---------|---------|---------|---------|---------|---------|
| 5 | GET | `/ai/config` | 获取AI配置 | 无 | 是 (管理员) | 配置信息 |
| 6 | PUT | `/ai/config` | 更新AI配置 | `config` (JSON) | 是 (管理员) | 更新结果 |
| 7 | POST | `/ai/config/test` | 测试AI连接 | 无 | 是 (管理员) | 测试结果 |
| 8 | POST | `/ai/config/reset` | 重置AI配置 | 无 | 是 (管理员) | 重置结果 |
| 9 | GET | `/ai/config/validate` | 验证AI配置 | 无 | 是 (管理员) | 验证结果 |

#### 4.3 Prompt管理

| 序号 | 请求方法 | 请求路径 | 功能描述 | 必要参数 | 认证要求 | 响应格式 |
|-----|---------|---------|---------|---------|---------|---------|
| 10 | GET | `/prompts` | 获取Prompt配置 | 无 | 是 (管理员) | Prompt配置 |
| 11 | PUT | `/prompts` | 更新Prompt配置 | `prompts` (JSON) | 是 (管理员) | 更新结果 |
| 12 | POST | `/prompts/reset` | 重置Prompt配置 | 无 | 是 (管理员) | 重置结果 |

#### 4.4 向量数据库管理

| 序号 | 请求方法 | 请求路径 | 功能描述 | 必要参数 | 认证要求 | 响应格式 |
|-----|---------|---------|---------|---------|---------|---------|
| 13 | GET | `/vector-db/stats` | 获取向量数据库统计 | 无 | 是 (管理员) | 统计信息 |
| 14 | POST | `/vector-db/reset` | 重置向量数据库 | `confirm`, `rebuild` (均可选) | 是 (管理员) | 重置结果 |
| 15 | POST | `/vector-db/rebuild` | 重建向量数据库 | 无 | 是 (管理员) | 重建结果 |

#### 4.5 RAG系统信息

| 序号 | 请求方法 | 请求路径 | 功能描述 | 必要参数 | 认证要求 | 响应格式 |
|-----|---------|---------|---------|---------|---------|---------|
| 16 | GET | `/rag/stats` | 获取RAG系统统计 | 无 | 是 (管理员) | 统计信息 |
| 17 | GET | `/rag/health` | RAG健康检查 | 无 | 是 (管理员) | 健康状态 |

#### 4.6 系统设置

| 序号 | 请求方法 | 请求路径 | 功能描述 | 必要参数 | 认证要求 | 响应格式 |
|-----|---------|---------|---------|---------|---------|---------|
| 18 | GET | `/settings` | 获取系统设置 | 无 | 是 (管理员) | `{ocr, rag, jwt}` |
| 19 | PUT | `/settings` | 更新系统设置 | `settings_data` (JSON) | 是 (管理员) | `{message, updated_keys, errors}` |

#### 4.7 用户管理

| 序号 | 请求方法 | 请求路径 | 功能描述 | 必要参数 | 认证要求 | 响应格式 |
|-----|---------|---------|---------|---------|---------|---------|
| 20 | GET | `/users` | 获取用户列表 | 无 | 是 (管理员) | `{total, users}` |
| 21 | POST | `/users` | 创建新用户 | `user_data` (JSON) | 是 (管理员) | 创建结果 |
| 22 | DELETE | `/users/{user_id}` | 删除用户 | `user_id` | 是 (管理员) | 删除结果 |

#### 4.8 综测配置管理

| 序号 | 请求方法 | 请求路径 | 功能描述 | 必要参数 | 认证要求 | 响应格式 |
|-----|---------|---------|---------|---------|---------|---------|
| 23 | GET | `/comprehensive-score-config/fields` | 获取学业成绩字段列表 | 无 | 是 (管理员) | `{fields: [...]}` |
| 24 | POST | `/comprehensive-score-config` | 创建综测配置 | `config_data` | 是 (管理员) | 配置详情 |
| 25 | GET | `/comprehensive-score-config` | 获取配置列表 | `is_active`, `limit`, `offset` (均可选) | 是 (管理员) | `{total, configs}` |
| 26 | GET | `/comprehensive-score-config/{config_id}` | 获取单个配置 | `config_id` | 是 (管理员) | 配置详情 |
| 27 | GET | `/comprehensive-score-config/default` | 获取默认配置 | 无 | 是 (管理员) | 默认配置 |
| 28 | PUT | `/comprehensive-score-config/{config_id}` | 更新配置 | `config_id`, `config_data` | 是 (管理员) | `{message, config}` |
| 29 | DELETE | `/comprehensive-score-config/{config_id}` | 删除配置 | `config_id` | 是 (管理员) | `{message}` |
| 30 | POST | `/comprehensive-score/calculate` | 批量计算综测成绩 | `config_id`, `semester`, `academic_year`, `class_name` (可选) | 是 (管理员) | `{message, config, processed, updated, failed, errors}` |
| 31 | POST | `/comprehensive-score/preview` | 预览计算结果 | `config_id`, `student_id`, `semester`, `academic_year` | 是 (管理员) | 详细计算过程 |

**备注**:
- 综测配置权重总和必须为100%
- 批量计算会保留手动修改的分数

---

## 5. 成绩上传模块 (score_upload.py)

### 路由前缀: `/score-upload`

| 序号 | 请求方法 | 请求路径 | 功能描述 | 必要参数 | 认证要求 | 响应格式 |
|-----|---------|---------|---------|---------|---------|---------|
| 1 | POST | `/upload` | 上传成绩单 | `file`, `academic_year`, `semester`, `uploaded_by`, `upload_role` | 是 | `{success, message, file_id, upload_id, processed, failed}` |
| 2 | GET | `/history/{student_id}` | 获取学生成绩历史 | `student_id`, `academic_year` (可选), `semester` (可选) | 否 | `{success, student_id, history, total}` |
| 3 | GET | `/upload-records` | 获取上传记录 | `upload_by` (可选), `status` (可选), `limit` (可选) | 否 | `{success, records, total}` |
| 4 | GET | `/field-mapping` | 获取字段映射 | 无 | 否 | `{mapping, description}` |
| 5 | POST | `/preview` | 预览成绩单 | `file`, `rows` (可选) | 否 | `{success, columns, row_count, data}` |

**备注**:
- 只支持Excel文件格式 (.xlsx, .xls)

---

## 6. 证书上传模块 (certificate_upload.py)

### 路由前缀: `/certificate`

| 序号 | 请求方法 | 请求路径 | 功能描述 | 必要参数 | 认证要求 | 响应格式 |
|-----|---------|---------|---------|---------|---------|---------|
| 1 | POST | `/upload` | 上传证书 | `files`, `student_id`, `title` (可选), ... | 是 | `{success, message, certificate_id, batch_id, images}` |
| 2 | GET | `/student/{student_id}` | 获取学生证书 | `student_id`, `status` (可选), `category` (可选) | 否 | `{success, student_id, total, certificates}` |
| 3 | GET | `/{certificate_id}` | 获取证书详情 | `certificate_id` | 否 | 证书详情 |
| 4 | DELETE | `/{certificate_id}` | 删除证书 | `certificate_id`, `deleted_by` (可选) | 是 | 删除结果 |
| 5 | PUT | `/{certificate_id}` | 更新证书信息 | `certificate_id`, 各种可选字段 | 是 | 更新结果 |
| 6 | GET | `/statistics/{student_id}` | 获取证书统计 | `student_id` | 否 | 统计信息 |
| 7 | POST | `/batch-status` | 批量更新状态 | `certificate_ids`, `status`, `reviewed_by` (可选), `review_comment` (可选) | 是 | `{success, updated_count, message}` |

**备注**:
- 状态值: pending, approved, rejected, cancelled

---

## 7. 班级管理模块 (class_.py)

### 路由前缀: `/classes`

| 序号 | 请求方法 | 请求路径 | 功能描述 | 必要参数 | 认证要求 | 响应格式 |
|-----|---------|---------|---------|---------|---------|---------|
| 1 | POST | `/` | 创建班级 | `ClassCreate` | 是 | `ClassResponse` |
| 2 | GET | `/{class_id}` | 获取班级详情 | `class_id` | 是 | `ClassResponse` |
| 3 | PUT | `/{class_id}` | 更新班级 | `class_id`, `ClassUpdate` | 是 | `ClassResponse` |
| 4 | DELETE | `/{class_id}` | 删除班级 | `class_id` | 是 | `{message}` |
| 5 | GET | `/` | 获取班级列表 | `skip`, `limit` (均可选) | 是 | `List[ClassResponse]` |
| 6 | GET | `/{class_id}/students` | 获取班级学生 | `class_id`, `skip`, `limit`, `name_filter` (均可选) | 是 | `{class_id, class_name, students, total, skip, limit}` |
| 7 | POST | `/{class_id}/students/{student_id}` | 添加学生 | `class_id`, `student_id` | 是 | `{message}` |
| 8 | DELETE | `/{class_id}/students/{student_id}` | 移除学生 | `class_id`, `student_id` | 是 | `{message}` |
| 9 | GET | `/{class_id}/stats` | 获取班级统计 | `class_id` | 是 | `{class_id, class_name, student_count, average_score, ...}` |

**备注**:
- 班级统计包含平均成绩、尖子生、科目平均等信息

---

## 8. 综测成绩模块 (comprehensive_score.py)

### 路由前缀: `/comprehensive-score`

| 序号 | 请求方法 | 请求路径 | 功能描述 | 必要参数 | 认证要求 | 响应格式 |
|-----|---------|---------|---------|---------|---------|---------|
| 1 | POST | `/calculate/student/{student_id}` | 计算单个学生综测 | `student_id`, `academic_year`, `semester`, `config_id` (可选) | 是 | 计算结果 |
| 2 | POST | `/calculate/class/{class_id}` | 计算班级综测 | `class_id`, `academic_year`, `semester`, `config_id` (可选) | 是 | 计算结果 |
| 3 | GET | `/student/{student_id}` | 获取学生综测成绩 | `student_id`, `academic_year`, `semester` | 是 | 成绩详情 |
| 4 | GET | `/class/{class_id}/ranking` | 获取班级排名 | `class_id`, `academic_year`, `semester` | 是 | `{class_id, total_count, rankings}` |
| 5 | POST | `/detail` | 添加加减分明细 | `ScoreDetailCreate` | 是 | `{success, id, message}` |
| 6 | DELETE | `/detail/{detail_id}` | 删除加减分明细 | `detail_id` | 是 | `{success, message}` |
| 7 | GET | `/config/list` | 获取配置列表 | 无 | 是 | `{configs: [...]}` |
| 8 | POST | `/config` | 创建配置 | `ConfigCreate` | 是 | `{success, id, message}` |
| 9 | PUT | `/config/{config_id}` | 更新配置 | `config_id`, `ConfigCreate` | 是 | `{success, message}` |
| 10 | GET | `/classes` | 获取班级列表 | 无 | 是 | `{classes: [...]}` |
| 11 | GET | `/class/{class_id}/stats` | 获取班级统计 | `class_id`, `academic_year`, `semester` | 是 | `{class_id, total_students, stats}` |

**备注**:
- 类别类型: A1, A2, A3, C1, C2, C3, C4
- 配置权重总和必须为100%

---

## 9. AI助手模块 (ai.py)

### 路由前缀: `/ai`

| 序号 | 请求方法 | 请求路径 | 功能描述 | 必要参数 | 认证要求 | 响应格式 |
|-----|---------|---------|---------|---------|---------|---------|
| 1 | POST | `/chat` | AI对话 | `ChatRequest` | 是 (Token) | `ChatResponse` |
| 2 | POST | `/chat/stream` | 流式AI对话 | `ChatRequest` | 是 (Token) | SSE流式响应 |
| 3 | POST | `/assistant/message` | AI助手消息 | `AssistantMessageRequest` | 是 (Token) | `AssistantMessageResponse` |
| 4 | GET | `/suggestions` | 获取推荐问题 | 无 | 是 (Token) | `{suggestions: [...]}` |
| 5 | GET | `/history` | 获取对话历史 | `limit` (可选), `session_id` (可选) | 是 (Token) | `{history, total, session_id}` |
| 6 | DELETE | `/history` | 清空对话历史 | `session_id` (可选) | 是 (Token) | `{message, deleted_count}` |

**备注**:
- 需要启用RAG系统才能使用AI功能
- 对话历史会自动保存到数据库

---

## 10. 文件管理模块 (file_management.py)

### 路由前缀: `/file`

| 序号 | 请求方法 | 请求路径 | 功能描述 | 必要参数 | 认证要求 | 响应格式 |
|-----|---------|---------|---------|---------|---------|---------|
| 1 | POST | `/upload` | 上传单个文件 | `file`, `file_type`, `owner_id`, `owner_type` (可选), `is_public` (可选), `metadata` (可选) | 是 | 上传结果 |
| 2 | POST | `/upload-multiple` | 批量上传文件 | `files`, `file_type`, `owner_id`, `owner_type` (可选) | 是 | 批量上传结果 |
| 3 | POST | `/chunk/init` | 初始化分片上传 | `filename`, `file_size`, `file_type`, `owner_id`, `chunk_size` (可选) | 是 | 初始化结果 |
| 4 | POST | `/chunk/{file_id}/{chunk_index}` | 上传分片 | `file_id`, `chunk_index`, `chunk` | 是 | 上传结果 |
| 5 | POST | `/chunk/{file_id}/complete` | 完成分片上传 | `file_id` | 是 | 合并结果 |
| 6 | GET | `/chunk/{file_id}/progress` | 获取上传进度 | `file_id` | 是 | 进度信息 |
| 7 | GET | `/download/{file_id}` | 下载文件 | `file_id`, `user_id`, `user_type` (可选) | 是 | 文件下载 |
| 8 | GET | `/download/result/{file_id}` | 下载结果文件 | `file_id`, `user_id`, `user_type` (可选) | 是 | Excel文件下载 |
| 9 | GET | `/info/{file_id}` | 获取文件信息 | `file_id` | 是 | 文件信息 |
| 10 | GET | `/list` | 列出文件 | `owner_id` (可选), `file_type` (可选), `status` (可选), `limit` (可选), `offset` (可选) | 是 | 文件列表 |
| 11 | DELETE | `/{file_id}` | 删除文件 | `file_id`, `user_id`, `user_type` (可选), `backup` (可选) | 是 | 删除结果 |
| 12 | GET | `/download-history` | 获取下载历史 | `file_id` (可选), `downloader_id` (可选), `limit` (可选) | 是 | 下载历史 |
| 13 | GET | `/categories` | 获取文件分类 | 无 | 是 | `{categories, allowed_extensions, max_file_size, chunk_size}` |

**备注**:
- 文件类型: transcript, photo, certificate, template, result
- 分片上传适合大文件

---

## 11. 数据导入模块 (data_import.py)

### 路由前缀: `/data-import`

| 序号 | 请求方法 | 请求路径 | 功能描述 | 必要参数 | 认证要求 | 响应格式 |
|-----|---------|---------|---------|---------|---------|---------|
| 1 | POST | `/excel` | 导入Excel数据 | `file`, `academic_year` (可选), `semester` (可选), `class_id` (可选) | 是 | 导入结果统计 |
| 2 | GET | `/template` | 获取导入模板 | 无 | 是 | 模板信息 |
| 3 | POST | `/preview` | 预览Excel数据 | `file`, `rows` (可选) | 是 | `{sheets, data}` |

**备注**:
- 只支持Excel文件格式 (.xlsx, .xls)

---

## 12. 系统模块 (system_routes.py)

### 路由前缀: `/system` 和 `/`

| 序号 | 请求方法 | 请求路径 | 功能描述 | 必要参数 | 认证要求 | 响应格式 |
|-----|---------|---------|---------|---------|---------|---------|
| 1 | GET | `/system/health` | 系统健康检查 | 无 | 否 | `{status, service, version, timestamp, ...}` |
| 2 | GET | `/system/info` | 获取系统信息 | 无 | 否 | `{service, version, platform, cpu_count, memory_total, ...}` |
| 3 | GET | `/system/stats` | 获取系统统计 | 无 | 否 | `{cpu_percent, memory_percent, disk_percent, timestamp}` |
| 4 | GET | `/health` | API健康检查 | 无 | 否 | `{status, service, version, timestamp, ...}` |

**备注**:
- 无需认证的公共接口，用于监控和负载均衡

---

## 13. 关键业务流程API

### 13.1 学生证书上传流程

**主要API**:
1. `POST /student/certificate/upload` - 上传单张证书
2. `POST /student/certificate/upload/batch` - 批量上传证书
3. `GET /student/certificates` - 查看证书列表
4. `GET /student/scores/summary` - 查看成绩摘要

**测试要点**:
- 文件格式验证
- OCR识别准确性
- 证书分类正确性
- 加分计算准确性

### 13.2 教师成绩导入流程

**主要API**:
1. `POST /teacher/scores/upload` - 上传成绩单
2. `GET /teacher/students` - 查看学生列表
3. `GET /teacher/scores/analysis` - 成绩分析
4. `GET /teacher/classes/ranking` - 班级排名

**测试要点**:
- Excel解析
- 数据验证
- 自动创建学生
- 成绩统计计算

### 13.3 综测成绩计算流程

**主要API**:
1. `POST /admin/comprehensive-score-config` - 创建综测配置
2. `POST /admin/comprehensive-score/preview` - 预览计算
3. `POST /admin/comprehensive-score/calculate` - 批量计算
4. `GET /comprehensive-score/class/{class_id}/ranking` - 查看排名

**测试要点**:
- 权重配置验证
- 计算逻辑正确性
- 批量处理性能
- 结果持久化

### 13.4 AI助手对话流程

**主要API**:
1. `POST /ai/chat` - 普通对话
2. `POST /ai/chat/stream` - 流式对话
3. `GET /ai/history` - 获取历史
4. `GET /ai/suggestions` - 推荐问题

**测试要点**:
- RAG检索准确性
- 对话上下文保持
- 流式响应稳定性
- 历史记录保存

### 13.5 用户认证流程

**主要API**:
1. `POST /auth/register` - 用户注册
2. `POST /auth/login` - 用户登录
3. `GET /auth/me` - 获取用户信息
4. `POST /auth/password/change` - 修改密码

**测试要点**:
- 用户名/邮箱唯一性
- 密码加密存储
- Token过期处理
- 权限控制

---

## 附录

### A. 认证说明

系统使用JWT (JSON Web Token) 进行身份认证：

1. 调用 `POST /auth/login` 获取 access_token
2. 在后续请求的 Header 中添加: `Authorization: Bearer {access_token}`
3. Token有效期由配置决定（默认小时）

### B. 错误响应格式

标准错误响应:
```json
{
  "detail": "错误描述信息"
}
```

或使用自定义错误格式:
```json
{
  "success": false,
  "error_code": "ERROR_CODE",
  "message": "错误信息",
  "details": [...]
}
```

### C. 分页参数说明

通用分页参数:
- `limit`: 返回记录数量（默认值因接口而异）
- `offset`: 偏移量（从0开始）
- `skip`: 同offset

### D. 文件大小限制

- 普通文件上传: 根据配置
- 成绩单/综测表格: 10MB
- 证书图片: 根据配置
- 分片上传: 支持大文件

---

## 文档修订记录

| 版本 | 日期 | 修改人 | 修改内容 |
|-----|-----|-------|---------|
| v1.0 | 2026-03-06 | API分析工具 | 初始版本，梳理所有API接口 |

---

**文档结束**

# API接口对比文档

## 1. 概述

本文档对比了 `visual_model` 项目和 `PaddleOCRRAG` 项目的API接口，重点关注综测成绩计算、证书管理、数据分析等核心功能。

## 2. 项目架构对比

| 特性 | visual_model | PaddleOCRRAG |
|------|--------------|-------------|
| 框架 | FastAPI + Tortoise ORM | FastAPI |
| 数据库 | SQLite/PostgreSQL | 无（主要使用RAG） |
| 主要功能 | 完整的综测管理系统 | RAG检索+证书分析 |
| 重点模块 | 数据存储、综测计算、API接口 | 规则检索、证书分析、对话 |

## 3. visual_model 项目API接口

### 3.1 综测成绩API (comprehensive_score.py)

#### 3.1.1 计算学生综测成绩

**接口：** `POST /comprehensive-score/calculate/student/{student_id}`

**参数：**
- `student_id`: 学生学号（路径参数）
- `academic_year`: 学年（Query参数）
- `semester`: 学期（Query参数）
- `config_id`: 配置ID（可选，Query参数）

**响应示例：**
```json
{
  "success": true,
  "data": {
    "student_id": "230521001",
    "student_name": "张三",
    "a_total_score": 95.0,
    "a_weighted_score": 19.0,
    "b_raw_score": 88.5,
    "b_weighted_score": 61.95,
    "c_total_score": 12.0,
    "c_weighted_score": 1.2,
    "total_score": 82.15,
    "ranking": 5
  }
}
```

#### 3.1.2 计算班级综测成绩

**接口：** `POST /comprehensive-score/calculate/class/{class_id}`

**参数：**
- `class_id`: 班级ID（路径参数）
- `academic_year`: 学年（Query参数）
- `semester`: 学期（Query参数）
- `config_id`: 配置ID（可选，Query参数）

**响应示例：**
```json
{
  "success": true,
  "class_id": "230521",
  "total_students": 45,
  "calculated_count": 45,
  "average_score": 78.5
}
```

#### 3.1.3 获取学生综测成绩详情

**接口：** `GET /comprehensive-score/student/{student_id}`

**参数：**
- `student_id`: 学生学号（路径参数）
- `academic_year`: 学年（Query参数）
- `semester`: 学期（Query参数）

**响应示例：**
```json
{
  "success": true,
  "data": {
    "student_id": "230521001",
    "student_name": "张三",
    "class_name": "230521班",
    "major": "计算机科学",
    "a1_score": 80.0,
    "a2_score": 15.0,
    "a3_score": 0.0,
    "a_total_score": 95.0,
    "a_weighted_score": 19.0,
    "b_raw_score": 88.5,
    "b_weighted_score": 61.95,
    "c1_score": 5.0,
    "c2_score": 3.0,
    "c3_score": 2.0,
    "c4_score": 2.0,
    "c_total_score": 12.0,
    "c_weighted_score": 1.2,
    "total_score": 82.15,
    "ranking": 5,
    "semester": "1",
    "academic_year": "2024-2025",
    "score_details": [
      {
        "id": 1,
        "category_type": "C1",
        "item_name": "数学建模竞赛",
        "score": 5.0,
        "certificate_id": 10
      }
    ]
  }
}
```

#### 3.1.4 获取班级排名

**接口：** `GET /comprehensive-score/class/{class_id}/ranking`

**参数：**
- `class_id`: 班级ID（路径参数）
- `academic_year`: 学年（Query参数）
- `semester`: 学期（Query参数）

**响应示例：**
```json
{
  "class_id": "230521",
  "academic_year": "2024-2025",
  "semester": "1",
  "total_count": 45,
  "rankings": [
    {
      "rank": 1,
      "student_id": "230521001",
      "student_name": "张三",
      "a_total_score": 95.0,
      "b_total_score": 88.5,
      "c_total_score": 12.0,
      "total_score": 82.15
    }
  ]
}
```

#### 3.1.5 添加加减分明细

**接口：** `POST /comprehensive-score/detail`

**请求体：**
```json
{
  "student_id": "230521001",
  "academic_year": "2024-2025",
  "semester": "1",
  "category_type": "C1",
  "item_name": "数学建模竞赛",
  "score": 5.0,
  "description": "全国大学生数学建模竞赛一等奖",
  "certificate_id": 10
}
```

**响应示例：**
```json
{
  "success": true,
  "id": 1,
  "message": "添加成功"
}
```

#### 3.1.6 获取综测配置列表

**接口：** `GET /comprehensive-score/config/list`

**响应示例：**
```json
{
  "configs": [
    {
      "id": 1,
      "name": "默认配置",
      "description": "计算机学院2025年综测配置",
      "a_weight": 20.0,
      "b_weight": 70.0,
      "c_weight": 10.0,
      "academic_score_field": "weighted_average",
      "academic_score_scale": 1.0,
      "is_default": true
    }
  ]
}
```

#### 3.1.7 创建/更新综测配置

**接口：** `POST /comprehensive-score/config`（创建）
**接口：** `PUT /comprehensive-score/config/{config_id}`（更新）

**请求体：**
```json
{
  "name": "2025级配置",
  "description": "2025级综测配置",
  "a_weight": 20.0,
  "b_weight": 70.0,
  "c_weight": 10.0,
  "academic_score_field": "weighted_average",
  "academic_score_scale": 1.0,
  "is_default": false
}
```

#### 3.1.8 获取班级统计信息

**接口：** `GET /comprehensive-score/class/{class_id}/stats`

**参数：**
- `class_id`: 班级ID（路径参数）
- `academic_year`: 学年（Query参数）
- `semester`: 学期（Query参数）

**响应示例：**
```json
{
  "class_id": "230521",
  "academic_year": "2024-2025",
  "semester": "1",
  "total_students": 45,
  "stats": {
    "average": 78.5,
    "max": 92.3,
    "min": 65.2,
    "a_average": 90.5,
    "b_average": 82.3,
    "c_average": 8.5
  }
}
```

### 3.2 其他核心API模块

#### 3.2.1 学生管理API (student.py)
- `GET /student/{student_id}` - 获取学生信息
- `POST /student` - 创建学生
- `PUT /student/{student_id}` - 更新学生信息
- `GET /student/{student_id}/scores` - 获取学生成绩

#### 3.2.2 证书管理API (certificate_upload.py)
- `POST /certificate/upload` - 上传证书
- `GET /certificate/{certificate_id}` - 获取证书详情
- `PUT /certificate/{certificate_id}/review` - 审核证书
- `GET /student/{student_id}/certificates` - 获取学生证书列表

#### 3.2.3 数据导入API (data_import.py)
- `POST /import/academic-score` - 导入学业成绩
- `POST /import/comprehensive-score` - 导入综测成绩
- `POST /import/students` - 导入学生信息

#### 3.2.4 Excel填充API (excel_fill.py)
- `POST /excel/fill` - 填充Excel模板
- `POST /excel/fill-from-rag` - 使用RAG填充Excel
- `GET /excel/template` - 下载Excel模板

## 4. PaddleOCRRAG 项目API接口

### 4.1 证书管理API (certificate_routes.py)

#### 4.1.1 证书加分计算

**接口：** `POST /certificate/calculate`

**请求体：**
```json
{
  "certificate_text": "全国大学生数学建模竞赛一等奖",
  "student_info": {
    "grade": "2024",
    "major": "计算机科学"
  }
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "证书加分计算成功",
  "data": {
    "category": "C1",
    "score": 5.0,
    "rules": "根据《计算机学院综合测评实施细则》第5.2条，科技竞赛国家级一等奖加5分",
    "confidence": 0.95,
    "explanation": "该证书属于科技竞赛类别，级别为国家级，获得一等奖，根据规定可加5分"
  }
}
```

#### 4.1.2 证书分析

**接口：** `POST /certificate/analyze`

**请求体：**
```json
{
  "certificate_text": "全国大学生数学建模竞赛一等奖",
  "student_info": {
    "grade": "2024",
    "major": "计算机科学"
  }
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "证书分析成功",
  "data": {
    "certificate_type": "竞赛",
    "certificate_level": "国家级",
    "certificate_name": "全国大学生数学建模竞赛",
    "category": "C",
    "sub_category": "C1",
    "score": 5.0,
    "rules_matched": [
      "科技竞赛加分规则",
      "国家级竞赛加分标准"
    ]
  }
}
```

### 4.2 对话交流API (chat_routes.py)

#### 4.2.1 普通对话

**接口：** `POST /chat`

**请求体：**
```json
{
  "message": "科技竞赛怎么加分？",
  "chat_history": [],
  "use_rag": true,
  "student_info": {
    "grade": "2024",
    "major": "计算机科学"
  }
}
```

**响应示例：**
```json
{
  "reply": "根据《计算机学院综合测评实施细则》，科技竞赛（C1类）的加分标准如下：...",
  "retrieved_rules": [
    "科技竞赛加分规则第1条",
    "科技竞赛加分规则第2条"
  ],
  "confidence": 0.98,
  "context_used": true
}
```

#### 4.2.2 流式对话

**接口：** `POST /chat/stream`

### 4.3 文档管理API (document_routes.py)

#### 4.3.1 上传文档

**接口：** `POST /document/upload`

#### 4.3.2 获取文档列表

**接口：** `GET /document/list`

#### 4.3.3 启用/禁用文档

**接口：** `PUT /document/{document_id}/status`

### 4.4 向量数据库API (vector_db_routes.py)

#### 4.4.1 获取向量库统计

**接口：** `GET /vector-db/stats`

#### 4.4.2 重置向量库

**接口：** `POST /vector-db/reset`

### 4.5 系统管理API (system_routes.py)

#### 4.5.1 获取系统状态

**接口：** `GET /system/status`

#### 4.5.2 获取/更新Prompt配置

**接口：** `GET /prompt/config`
**接口：** `PUT /prompt/config`

#### 4.5.3 获取/更新LLM配置

**接口：** `GET /llm/config`
**接口：** `PUT /llm/config`
**接口：** `POST /llm/test`

## 5. API功能对比表

| 功能模块 | visual_model | PaddleOCRRAG | 说明 |
|---------|--------------|-------------|------|
| 综测成绩计算 | ✅ 完整实现 | ❌ 无 | visual_model有完整的综测计算引擎 |
| 证书管理 | ✅ 完整实现 | ✅ 基础分析 | visual_model有证书存储和审核，PaddleOCRRAG有RAG分析 |
| 学生信息管理 | ✅ 完整实现 | ❌ 无 | visual_model有完整的学生CRUD |
| 班级管理 | ✅ 完整实现 | ❌ 无 | visual_model有班级管理功能 |
| 数据导入导出 | ✅ 完整实现 | ❌ 无 | visual_model支持Excel导入导出 |
| RAG规则检索 | ⚠️ 部分集成 | ✅ 核心功能 | PaddleOCRRAG是专业的RAG系统 |
| 证书OCR识别 | ✅ 集成PaddleOCR | ✅ 集成PaddleOCR | 两者都有OCR功能 |
| 对话咨询 | ✅ 集成RAG | ✅ 完整实现 | PaddleOCRRAG对话功能更完善 |
| 数据持久化 | ✅ 完整数据库 | ❌ 无 | visual_model有完整的数据库设计 |
| 历史记录 | ✅ 版本控制 | ❌ 无 | visual_model有数据历史记录 |

## 6. 统一响应格式对比

### 6.1 visual_model 响应格式

```json
{
  "success": true,
  "message": "操作成功",
  "data": {},
  "timestamp": "2024-03-08T10:00:00Z"
}
```

### 6.2 PaddleOCRRAG 响应格式

```json
{
  "success": true,
  "message": "操作成功",
  "data": {},
  "timestamp": "2024-03-08T10:00:00Z"
}
```

**说明：** 两个项目的响应格式基本一致，都使用统一的响应包装器。

## 7. 集成建议

### 7.1 推荐架构

建议将两个项目整合为一个完整的综测管理系统：

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Vue.js)                    │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              visual_model API Gateway                    │
│  - 学生管理、班级管理、综测计算、数据存储               │
│  - 集成 PaddleOCRRAG 的 RAG 和对话功能                 │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   Database    │  │  PaddleOCR    │  │  PaddleOCRRAG │
│  (Tortoise)   │  │     OCR       │  │  RAG Service  │
└───────────────┘  └───────────────┘  └───────────────┘
```

### 7.2 关键集成点

1. **证书分析流程**：
   - visual_model 接收证书上传
   - 调用 PaddleOCR 进行 OCR
   - 调用 PaddleOCRRAG 进行 RAG 分析和加分计算
   - visual_model 存储结果并更新综测成绩

2. **综测计算流程**：
   - visual_model 从数据库获取学生信息、学业成绩、证书信息
   - 调用 PaddleOCRRAG 获取规则和计算逻辑
   - visual_model 执行综测计算
   - 结果存入数据库

3. **智能对话流程**：
   - Frontend 发送用户问题
   - visual_model 转发给 PaddleOCRRAG
   - PaddleOCRRAG 进行 RAG 检索和回答
   - 返回给 Frontend

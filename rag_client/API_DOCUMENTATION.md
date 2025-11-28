# PaddleOCRRAG API 完整使用指南

## 目录

1. [简介](#简介)
2. [快速开始](#快速开始)
3. [API概述](#api概述)
4. [认证与安全](#认证与安全)
5. [API详细说明](#api详细说明)
6. [错误处理](#错误处理)
7. [最佳实践](#最佳实践)
8. [常见问题](#常见问题)
9. [更新日志](#更新日志)

## 简介

PaddleOCRRAG API是一个基于大语言模型和向量数据库的智能问答系统，专为教育场景设计，提供证书分析、智能问答和文档检索等功能。

### 主要特性

- 🎯 **智能证书分析**：自动分析各类证书并计算加分值
- 💬 **自然语言交互**：支持自然语言问答，提供精准回答
- 📚 **文档检索**：基于向量数据库的高效文档检索
- 🔍 **多模态支持**：支持文本、图像等多种输入格式
- ⚡ **高性能**：优化的API响应速度和并发处理能力

## 快速开始

### 1. 启动服务

```bash
# 克隆项目
git clone https://github.com/your-repo/PaddleOCRRAG.git
cd PaddleOCRRAG

# 安装依赖
pip install -r requirements.txt

# 启动服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 验证服务

```bash
# 健康检查
curl http://localhost:8000/api/v1/system/health
```

### 3. 第一个API调用

```bash
# 测试LLM连接
curl -X POST http://localhost:8000/api/v1/llm/test
```

## API概述

### 基础信息

- **基础URL**: `http://localhost:8000/api/v1`
- **协议**: HTTP/HTTPS
- **数据格式**: JSON
- **字符编码**: UTF-8

### API列表

| 分类 | 端点 | 方法 | 描述 |
|------|------|------|------|
| 系统 | `/system/health` | GET | 系统健康检查 |
| LLM | `/llm/test` | POST | LLM连接测试 |
| 证书 | `/certificate/calculate` | POST | 证书加分计算 |
| 证书 | `/certificate/analyze` | POST | 证书分析 |
| 对话 | `/chat` | POST | AI对话交流 |
| 文档 | `/documents` | GET | 文档列表 |

## 认证与安全

### API密钥

目前API不需要认证，但在生产环境中建议使用API密钥：

```http
Authorization: Bearer YOUR_API_KEY
```

### 安全建议

1. 使用HTTPS协议传输敏感数据
2. 定期轮换API密钥
3. 限制API调用频率
4. 验证输入数据，防止注入攻击

## API详细说明

### 1. 系统健康检查

检查系统运行状态和各组件健康状况。

**端点**: `GET /api/v1/system/health`

**请求示例**:
```bash
curl -X GET http://localhost:8000/api/v1/system/health
```

**响应示例**:
```json
{
  "success": true,
  "message": "系统健康",
  "data": {
    "status": "healthy",
    "timestamp": "2023-11-15T12:00:00.000Z",
    "components": {
      "database": "healthy",
      "llm": "healthy",
      "vector_db": "healthy"
    }
  }
}
```

### 2. LLM连接测试

测试大语言模型连接是否正常。

**端点**: `POST /api/v1/llm/test`

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/llm/test \
  -H "Content-Type: application/json"
```

**响应示例**:
```json
{
  "success": true,
  "message": "LLM连接测试成功",
  "data": {
    "response": "测试响应内容",
    "timestamp": "2023-11-15T12:00:00.000Z",
    "model": "gpt-3.5-turbo",
    "response_time": 1.23
  }
}
```

### 3. 证书加分计算

根据证书信息计算加分值。

**端点**: `POST /api/v1/certificate/calculate`

**请求参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| student_id | string | 是 | 学生ID |
| certificate_type | string | 是 | 证书类型 |
| certificate_level | string | 是 | 证书级别 |
| certificate_name | string | 是 | 证书名称 |
| score | number | 否 | 证书分数 |
| issue_date | string | 否 | 颁发日期 (YYYY-MM-DD) |

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/certificate/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "20230001",
    "certificate_type": "语言证书",
    "certificate_level": "CET-4",
    "certificate_name": "英语四级证书",
    "score": 500,
    "issue_date": "2023-06-15"
  }'
```

**响应示例**:
```json
{
  "success": true,
  "message": "证书加分计算成功",
  "data": {
    "points": 3,
    "certificate_type": "语言证书",
    "certificate_level": "CET-4",
    "calculation_details": {
      "base_points": 2,
      "score_bonus": 1,
      "total_points": 3
    }
  }
}
```

### 4. 证书分析

分析证书信息并提供详细反馈。

**端点**: `POST /api/v1/certificate/analyze`

**请求参数**: 与证书加分计算API相同

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/certificate/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "20230001",
    "certificate_type": "语言证书",
    "certificate_level": "CET-4",
    "certificate_name": "英语四级证书",
    "score": 500,
    "issue_date": "2023-06-15"
  }'
```

**响应示例**:
```json
{
  "success": true,
  "message": "证书分析成功",
  "data": {
    "analysis": "该证书为英语四级证书，分数500分，属于中等水平。根据学校综合测评规定，CET-4证书可获得3分加分。",
    "points": 3,
    "certificate_type": "语言证书",
    "certificate_level": "CET-4",
    "recommendations": [
      "建议考取更高等级的英语证书以获得更多加分",
      "可以考虑参加英语口语考试提升综合能力"
    ]
  }
}
```

### 5. AI对话交流

与AI进行自然语言对话交流。

**端点**: `POST /api/v1/chat`

**请求参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| question | string | 是 | 问题内容 |
| context | string | 否 | 对话上下文 |
| student_id | string | 否 | 学生ID（用于个性化回答） |

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "你好，我想了解英语四级证书的加分规则",
    "student_id": "20230001"
  }'
```

**响应示例**:
```json
{
  "success": true,
  "message": "对话处理成功",
  "data": {
    "response": "根据学校综合测评规定，英语四级证书(CET-4)可以获得3分加分。如果分数达到425分以上，属于有效证书。具体加分规则可能会根据学院政策有所调整，建议查看最新的综合测评实施细则。",
    "timestamp": "2023-11-15T12:00:00.000Z",
    "sources": [
      {
        "title": "计算机学院综合测评实施细则（2025）",
        "relevance": 0.95
      }
    ]
  }
}
```

### 6. 文档列表

获取系统中可用的文档列表。

**端点**: `GET /api/v1/documents`

**查询参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | number | 否 | 页码（默认1） |
| size | number | 否 | 每页数量（默认10） |
| type | string | 否 | 文档类型过滤 |

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/documents?page=1&size=10"
```

**响应示例**:
```json
{
  "success": true,
  "message": "获取文档列表成功",
  "data": {
    "total": 25,
    "page": 1,
    "size": 10,
    "documents": [
      {
        "id": "doc_001",
        "title": "计算机学院综合测评实施细则（2025）",
        "type": "rule",
        "upload_date": "2023-09-01T00:00:00.000Z",
        "size": "2.3MB"
      }
    ]
  }
}
```

## 错误处理

### 错误响应格式

所有API错误都遵循统一的响应格式：

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": "详细错误信息"
  },
  "timestamp": "2023-11-15T12:00:00.000Z"
}
```

### 常见错误码

| 错误码 | HTTP状态码 | 描述 |
|--------|------------|------|
| INVALID_REQUEST | 400 | 请求参数无效 |
| UNAUTHORIZED | 401 | 未授权访问 |
| FORBIDDEN | 403 | 禁止访问 |
| NOT_FOUND | 404 | 资源不存在 |
| RATE_LIMIT_EXCEEDED | 429 | 请求频率超限 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |
| SERVICE_UNAVAILABLE | 503 | 服务不可用 |

### 错误处理示例

```javascript
// JavaScript错误处理示例
fetch('http://localhost:8000/api/v1/certificate/calculate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    student_id: "20230001",
    certificate_type: "语言证书",
    certificate_level: "CET-4",
    certificate_name: "英语四级证书",
    score: 500,
    issue_date: "2023-06-15"
  })
})
.then(response => {
  if (!response.ok) {
    return response.json().then(error => {
      throw new Error(`API错误: ${error.error.code} - ${error.error.message}`);
    });
  }
  return response.json();
})
.then(data => {
  console.log('加分值:', data.data.points);
})
.catch(error => {
  console.error('请求失败:', error.message);
});
```

## 最佳实践

### 1. 请求优化

- 使用适当的HTTP方法（GET用于查询，POST用于创建/更新）
- 合理设置请求超时时间
- 压缩大型请求体
- 使用连接池提高性能

### 2. 错误处理

- 始终检查响应状态码
- 实现指数退避重试机制
- 记录详细的错误日志
- 提供用户友好的错误提示

### 3. 安全实践

- 验证所有输入数据
- 使用HTTPS传输敏感数据
- 实现API访问频率限制
- 定期更新依赖库

### 4. 性能优化

- 使用缓存减少重复请求
- 批量处理多个操作
- 异步处理长时间任务
- 监控API性能指标

## 常见问题

### Q: 如何获取API访问密钥？

A: 目前API不需要访问密钥，但在生产环境中，请联系管理员获取API密钥。

### Q: API调用频率限制是多少？

A: 目前没有明确的频率限制，但建议合理控制调用频率，避免对服务器造成过大压力。

### Q: 如何处理大文件上传？

A: 对于大文件，建议使用分块上传方式，或者先上传文件获取ID，再通过ID引用文件。

### Q: API响应时间是多少？

A: 大多数API响应时间在1-3秒内，复杂查询可能需要更长时间。

### Q: 如何获取实时API状态？

A: 可以通过健康检查端点 `/api/v1/system/health` 获取系统实时状态。

## 更新日志

### v1.0.0 (2023-11-15)
- 初始版本发布
- 实现基础API功能
- 支持证书分析和计算
- 实现AI对话交流功能

### v1.1.0 (计划中)
- 添加批量操作API
- 增强错误处理机制
- 优化API响应性能
- 添加更多文档类型支持

---

## 联系我们

如有任何问题或建议，请通过以下方式联系我们：

- 邮箱：support@paddleocrrag.com
- 官网：https://paddleocrrag.com
- GitHub：https://github.com/your-repo/PaddleOCRRAG

## 许可证

本项目采用 MIT 许可证，详情请参阅 [LICENSE](LICENSE) 文件。
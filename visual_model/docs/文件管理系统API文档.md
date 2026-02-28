# 文件上传与管理系统 - API文档

## 1. 概述

本系统提供完整的文件上传、下载和管理功能，支持成绩单、照片、证书等各类文件的规范化存储和管理。

## 2. 目录结构设计

```
D:/PaddleOCR/visual_model/
├── uploads/                    # 文件上传根目录
│   ├── transcripts/            # 成绩单目录
│   ├── photos/                 # 照片目录
│   ├── certificates/            # 证书目录
│   ├── templates/               # 模板目录
│   ├── results/                 # 结果目录
│   ├── chunks/                  # 分片临时目录
│   └── temp/                    # 临时文件目录
├── results/                     # 综测计算结果目录
└── backups/                     # 文件备份目录
```

## 3. 文件命名规则

**唯一标识格式**: `{学号/工号}_{时间戳}_{文件说明}`

**时间戳格式**: `YYYYMMDDHHMMSSmmm` (精确到毫秒)

**示例**: `202300502120_20260228234256789_成绩单`

## 4. API接口

### 4.1 文件上传

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/v1/file/upload` | 上传单个文件 |
| POST | `/v1/file/upload-multiple` | 批量上传文件 |
| POST | `/v1/file/chunk/init` | 初始化分片上传 |
| POST | `/v1/file/chunk/{file_id}/{chunk_index}` | 上传分片 |
| POST | `/v1/file/chunk/{file_id}/complete` | 完成分片上传 |
| GET | `/v1/file/chunk/{file_id}/progress` | 获取上传进度 |

### 4.2 文件下载

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/v1/file/download/{file_id}` | 下载文件 |
| GET | `/v1/file/download-result/{file_id}` | 下载综测结果文件 |
| GET | `/v1/file/info/{file_id}` | 获取文件信息 |
| GET | `/v1/file/list` | 列出文件 |
| DELETE | `/v1/file/{file_id}` | 删除文件 |
| GET | `/v1/file/download-history` | 获取下载历史 |

### 4.3 文件管理
| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/v1/file/categories` | 获取文件分类信息 |

## 5. 分片上传流程

```
1. 初始化分片上传
   POST /v1/file/chunk/init
   ↓
2. 上传分片 (循环)
   POST /v1/file/chunk/{file_id}/{index}
   ↓
3. 完成上传
   POST /v1/file/chunk/{file_id}/complete
   ↓
4. 文件合并完成
```

## 6. 权限控制

- 文件所有者自动获得全部权限
- 支持公开/私有文件设置
- 支持基于角色的权限控制
- 管理员拥有全部权限

## 7. 前端使用示例

```javascript
import { fileManagementAPI } from '@/services/api'

// 上传单个文件
const result = await fileManagementAPI.upload(file, {
  file_type: 'transcript',
  owner_id: '202300502120'
})

// 分片上传大文件
const init = await fileManagementAPI.initChunkUpload(
  'large_file.xlsx',
  150 * 1024 * 1024,
  'transcript',
  '202300502120'
)

for (let i = 0; i < init.chunk_count; i++) {
  const chunk = getChunk(i)  // 需要实现分片获取
  await fileManagementAPI.uploadChunk(init.file_id, i, chunk)
}

await fileManagementAPI.completeChunkUpload(init.file_id)

// 下载文件
const blob = await fileManagementAPI.download(fileId, {
  user_id: '202300502120',
  user_type: 'student'
})
```

## 8. 数据库表结构

### 8.1 file_metadata (文件元数据表)

| 字段 | 类型 | 说明 |
|------|------|------|
| file_id | VARCHAR(100) | 唯一标识 |
| original_filename | VARCHAR(255) | 原始文件名 |
| stored_filename | VARCHAR(255) | 存储文件名 |
| file_type | VARCHAR(50) | 文件类型 |
| file_size | INTEGER | 文件大小 |
| file_hash | VARCHAR(64) | MD5哈希 |
| storage_path | VARCHAR(500) | 存储路径 |
| owner_id | VARCHAR(50) | 所有者ID |
| status | VARCHAR(20) | 状态 |

### 8.2 file_chunks (文件分片表)

| 字段 | 类型 | 说明 |
|------|------|------|
| file_id | VARCHAR(100) | 关联文件ID |
| chunk_index | INTEGER | 分片序号 |
| chunk_hash | VARCHAR(64) | 分片哈希 |
| status | VARCHAR(20) | 状态 |

### 8.3 download_logs (下载日志表)

| 字段 | 类型 | 说明 |
|------|------|------|
| file_id | VARCHAR(100) | 文件ID |
| downloader_id | VARCHAR(50) | 下载者ID |
| download_status | VARCHAR(20) | 下载状态 |

## 9. 性能指标

- 支持至少100个并发文件上传请求
- 大文件(>100MB)支持分片上传
- 文件检索响应时间 < 500ms

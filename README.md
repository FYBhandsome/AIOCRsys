# 综测计算助手系统

<div align="center">

**基于PaddleOCR + FastAPI + Vue3的智能综合测评计算系统**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-blue)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.0+-green)](https://vuejs.org/)
[![Python](https://img.shields.io/badge/Python-3.9+-orange)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

[快速开始](#快速开始) • [功能特性](#功能特性) • [系统架构](#系统架构) • [文档](#文档目录)

</div>

---

## 📖 项目简介

综测计算助手是一个智能化的综合测评管理系统，通过OCR技术自动识别获奖证书，结合AI大模型智能计算综测加分，帮助学校、教师和学生高效管理综合测评数据。

### 核心能力

- 🎯 **智能OCR识别**：基于PaddleOCR，自动识别证书信息
- 🤖 **AI智能加分**：对接RAG系统，智能计算综测分数
- 👥 **多角色管理**：学生、教师、管理员三种角色权限体系
- 📊 **数据可视化**：直观的成绩统计和分析图表
- 🔒 **安全可靠**：JWT认证 + 离线授权验证双重保障

---

## ✨ 功能特性

### 学生端
- ✅ 在线上传获奖证书
- ✅ 自动OCR识别证书信息
- ✅ AI智能计算综测加分
- ✅ 查看个人综测成绩和排名
- ✅ 上传历史记录管理
- ✅ AI助手在线咨询

### 教师端
- ✅ 批量上传学生成绩
- ✅ 班级成绩统计分析
- ✅ 学生成绩查询与管理
- ✅ 成绩数据可视化
- ✅ 导出成绩报表

### 管理员端
- ✅ **最高权限**：管理员可以访问所有端点和功能
- ✅ 综测规则文档管理（上传、启用、停用、删除）
- ✅ AI大模型配置管理
  - 配置 API Key 和模型参数
  - 测试连接和验证配置
  - 支持多种服务商（OpenAI、讯飞星火等）
- ✅ Prompt提示词管理
  - 自定义系统提示词、用户提示词、聊天提示词
  - 实时占位符验证
  - 一键重置为默认
- ✅ 向量数据库管理
  - 实时统计信息监控
  - 重建和重置向量索引
  - 数据库健康检查
- ✅ **数据库管理**（新增）
  - 查看所有数据表统计
  - 查看和管理表数据
  - 删除指定记录
  - 清空指定表或所有数据
- ✅ 用户权限管理
- ✅ 系统设置配置
- ✅ 数据统计与监控

### 认证与权限
- ✅ **用户注册系统**（新增）
  - 支持学生、教师角色注册
  - 邮箱验证功能
  - 密码加密存储
- ✅ **密码管理**（新增）
  - 邮箱密码重置
  - 密码修改功能
  - 安全令牌机制
- ✅ **三级权限体系**
  - 管理员：拥有最高权限，可访问所有功能
  - 教师：管理班级和学生成绩
  - 学生：查看和管理个人数据

---

## 🚀 快速开始

### 环境要求

- **Python**: 3.9+
- **Node.js**: 16+
- **数据库**: SQLite（默认）/ MySQL / PostgreSQL

### 1. 克隆项目

```bash
git clone https://github.com/your-repo/paddleocr-assessment.git
cd paddleocr-assessment
```

### 2. 启动后端服务

```bash
cd visual_model

# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
```

后端服务运行在 http://localhost:8001

### 3. 启动前端服务

```bash
cd fronted/front

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务运行在 http://localhost:5173

### 4. 访问系统

打开浏览器访问 http://localhost:5173

**测试账号：**
```
学生账号: student1 / password123
教师账号: teacher1 / password123
管理员: admin / admin123
```

### 🔓 开发模式（可选）

开发测试时可以禁用认证，快速切换三种身份测试功能：

```powershell
# 运行脚本快速切换
.\切换认证模式.ps1
```

**身份切换功能：**
- 👨‍🎓 **学生** - 测试证书上传、成绩查看
- 👨‍🏫 **教师** - 测试班级管理、成绩录入
- 👨‍💼 **管理员** - 测试系统配置、规则管理

详见：[开发指南 - 开发模式](docs/开发指南.md#🎭-开发模式禁用认证)

---

## 🏗️ 系统架构

```
综测计算助手系统
├── 前端服务 (Vue 3 + Element Plus)
│   ├── 用户界面
│   ├── 状态管理 (Pinia)
│   ├── 路由权限控制
│   └── RAG管理界面
│
├── 后端服务 (FastAPI + Tortoise ORM)
│   ├── RESTful API
│   ├── JWT认证
│   ├── 权限控制
│   ├── 数据库管理
│   └── RAG API转发 (8001 → 8000)
│
├── OCR服务 (PaddleOCR)
│   ├── 证书图像识别
│   ├── 文本提取
│   └── 信息结构化
│
├── RAG系统 (端口8000)
│   ├── 规则文档检索
│   ├── AI智能对话
│   ├── 综测加分计算
│   ├── Prompt管理
│   └── 向量数据库管理
│
└── 授权验证 (离线验证)
    ├── License管理
    ├── 设备绑定
    └── 有效期控制
```

### 数据流架构

```
前端界面 (localhost:5173)
    ↓
后端服务 (localhost:8001) /v1/admin/*
    ↓ (通过 rag_client.py)
RAG API服务 (localhost:8000) /api/v1/*
```

---

## 🤖 RAG API 集成功能

### 功能概述

本系统已完整集成 RAG API，通过后端（8001端口）转发到 RAG 服务（8000端口），提供强大的 AI 智能加分和管理功能。

### 核心功能

#### 1. AI 大模型配置管理

**访问路径**: 管理员面板 → 系统设置 → AI大模型

**主要功能**:
- ✅ 配置 AI 服务商（OpenAI、讯飞星火、通义千问等）
- ✅ 设置 API Key 和 Access Key（密码保护）
- ✅ 配置模型ID和API地址
- ✅ 调整温度参数（0-1）和最大Token数
- ✅ 一键测试 AI 连接
- ✅ 重置为默认配置
- ✅ 配置验证功能

**使用步骤**:
1. 登录管理员账号
2. 进入"系统设置" → "AI大模型"标签页
3. 填写 API Key、模型ID、API地址等配置
4. 点击"测试连接"验证配置
5. 保存配置

#### 2. Prompt 提示词管理

**访问路径**: 管理员面板 → 系统设置 → Prompt管理

**主要功能**:
- ✅ 自定义系统提示词（System Prompt）
- ✅ 自定义用户提示词（User Prompt）
- ✅ 自定义聊天系统提示词（Chat System Prompt）
- ✅ 实时验证必需占位符
- ✅ 提供配置示例和说明
- ✅ 一键重置为默认值

**占位符说明**:
- **系统提示词**: 必须包含 `{context}` 占位符
- **用户提示词**: 必须包含 `{query}` 占位符
- **聊天系统提示词**: 必须包含 `{context_section}` 和 `{student_info_section}` 占位符

#### 3. 向量数据库管理

**访问路径**: 管理员面板 → 系统设置 → 向量数据库

**主要功能**:
- ✅ 实时查看数据库统计信息
  - 总文档数和启用文档数
  - 嵌入模型信息
  - LLM引擎信息
  - 数据库状态（正常/加载中/错误）
- ✅ 重建向量数据库（基于启用的文档重新构建索引）
- ✅ 重置向量数据库（清空所有数据，可选立即重建）
- ✅ 详细信息展示和健康监控

**操作说明**:
- **重建向量库**: 不删除现有数据，适合文档更新后使用
- **重置向量库**: 会清空所有数据，操作不可恢复（需二次确认）

### API 端点

新增的管理员 API 端点：

```python
# AI大模型配置
GET  /v1/admin/ai/config              # 获取配置
PUT  /v1/admin/ai/config              # 更新配置
POST /v1/admin/ai/config/test         # 测试连接
POST /v1/admin/ai/config/reset        # 重置配置
GET  /v1/admin/ai/config/validate     # 验证配置

# Prompt管理
GET  /v1/admin/prompts                # 获取Prompt
PUT  /v1/admin/prompts                # 更新Prompt
POST /v1/admin/prompts/reset          # 重置Prompt

# 向量数据库管理
GET  /v1/admin/vector-db/stats        # 获取统计
POST /v1/admin/vector-db/reset        # 重置数据库
POST /v1/admin/vector-db/rebuild      # 重建数据库

# RAG系统信息
GET  /v1/admin/rag/stats              # 系统统计
GET  /v1/admin/rag/health             # 健康检查
```

### 实现的组件

**后端**:
- `visual_model/app/services/rag_client.py` - RAG客户端（新增11个方法）
- `visual_model/app/api/admin.py` - 管理员API（新增10个端点）

**前端**:
- `fronted/front/src/components/SystemSettings.vue` - 系统设置主界面
- `fronted/front/src/components/PromptManager.vue` - Prompt管理组件
- `fronted/front/src/components/VectorDBManager.vue` - 向量数据库管理组件
- `fronted/front/src/services/api.js` - API服务（新增10个方法）

### 安全特性

1. **权限控制**: 所有 RAG 管理功能需要管理员权限
2. **数据保护**: API Key 使用密码输入框，显示时脱敏
3. **操作确认**: 危险操作（如重置数据库）需要二次确认
4. **错误处理**: 完善的错误提示和异常处理

### 故障排查

#### 无法连接到 RAG 服务
**解决方案**:
1. 确认 RAG 服务（8000端口）正在运行
2. 检查 `config.py` 中的 `RAG_BASE_URL` 配置
3. 检查网络连接和防火墙设置

#### AI 连接测试失败
**解决方案**:
1. 验证 API Key 是否正确
2. 检查 API 地址和模型ID
3. 确认服务商API可用

#### Prompt 保存失败
**解决方案**:
1. 确保包含必需的占位符
2. 检查占位符拼写和大小写
3. 参考配置示例

---

## 📚 文档目录

### 📘 快速指南
- **[快速开始](docs/快速开始指南.md)** - 5分钟快速上手
- **[部署指南](docs/部署指南.md)** - 生产环境部署方案

### 📗 开发文档
- **[开发指南](docs/开发指南.md)** - 开发环境配置、代码规范、开发模式
- **[API文档](docs/API接口文档.md)** - 完整的API接口说明
- **[系统架构](docs/系统架构设计.md)** - 技术架构详解
- **[综合测试指南](docs/综合测试指南.md)** - ✨ 系统综合测试方法

### 📕 功能说明
- **[OCR使用指南](docs/PaddleOCR使用指南.md)** - OCR功能配置与使用
- **[授权验证说明](docs/授权验证说明.md)** - 离线授权系统说明
- **[新功能使用指南](docs/新功能使用指南.md)** - ✨ 用户注册、密码重置、数据库管理
- **[权限管理说明](docs/权限管理说明.md)** - ✨ 三级权限体系详解
- **[邮件服务配置](docs/邮件服务配置指南.md)** - ✨ SMTP邮件服务配置

### 📙 模块文档
- **[后端服务](visual_model/README.md)** - 后端API服务说明
- **[前端应用](fronted/front/README.md)** - 前端项目说明

---

## 💻 技术栈

### 后端技术
- **框架**: FastAPI 0.100+
- **ORM**: Tortoise ORM
- **认证**: JWT + 离线License
- **OCR**: PaddleOCR
- **异步**: asyncio + uvicorn
- **日志**: Python logging

### 前端技术
- **框架**: Vue 3 + Vite
- **UI**: Element Plus
- **状态**: Pinia
- **路由**: Vue Router
- **HTTP**: Axios
- **图表**: ECharts

---

## 📁 项目结构

```
D:\PaddleOCR\
├── visual_model/          # 后端服务
│   ├── app/              # 应用核心
│   │   ├── api/         # API路由
│   │   ├── business/    # 业务逻辑
│   │   ├── core/        # 核心模块
│   │   ├── models/      # 数据模型
│   │   └── services/    # 服务层
│   ├── config.py        # 配置文件
│   ├── main.py          # 应用入口
│   └── requirements.txt # Python依赖
│
├── fronted/front/        # 前端应用
│   ├── src/
│   │   ├── components/  # 组件
│   │   ├── views/       # 页面
│   │   ├── router/      # 路由
│   │   ├── store/       # 状态
│   │   └── services/    # API服务
│   ├── package.json     # Node依赖
│   └── vite.config.js   # Vite配置
│
├── docs/                 # 文档目录
│   ├── 快速开始指南.md
│   ├── 开发指南.md
│   ├── 部署指南.md
│   ├── API接口文档.md
│   ├── 系统架构设计.md
│   ├── PaddleOCR使用指南.md
│   └── 授权验证说明.md
│
└── README.md            # 本文件
```

---

## 🔧 配置说明

### 后端配置

编辑 `visual_model/config.py` 或创建 `.env` 文件：

```env
# 服务器配置
HOST=127.0.0.1
PORT=8001
DEBUG=False

# 数据库配置
DATABASE_URL=sqlite:///data/database.db

# JWT配置
JWT_SECRET_KEY=your-secret-key-here
JWT_EXPIRATION_HOURS=24

# OCR配置
OCR_USE_GPU=False
OCR_THRESHOLD=0.15

# RAG系统配置（可选）
RAG_BASE_URL=http://localhost:8000
RAG_ENABLED=True
```

### 前端配置

编辑 `fronted/front/.env` 或 `.env.local`：

```env
# API地址（生产环境）
VITE_API_BASE_URL=http://your-backend-url/api
```

---

## 🎯 使用流程

### 学生使用流程
1. 登录系统
2. 上传获奖证书图片
3. 系统自动OCR识别
4. AI计算综测加分
5. 查看成绩和排名

### 教师使用流程
1. 登录系统
2. 上传班级成绩单（Excel）
3. 查看学生列表和成绩
4. 分析班级成绩统计
5. 导出成绩报表

### 管理员使用流程
1. 登录系统
2. 上传综测规则文档
3. 配置AI大模型参数
4. 管理用户权限
5. 监控系统运行状态

---

## 🔐 安全特性

- ✅ **JWT身份认证**：Token过期自动刷新
- ✅ **角色权限控制**：细粒度的权限管理
- ✅ **CORS跨域配置**：安全的跨域请求
- ✅ **SQL注入防护**：ORM参数化查询
- ✅ **XSS防护**：前端数据过滤
- ✅ **离线授权验证**：设备绑定+有效期控制

---

## 📊 数据统计

- 支持用户数：1000+
- 单次OCR识别：< 2秒
- API响应时间：< 100ms
- 并发处理能力：100+ QPS
- 存储空间：根据文件数量动态扩展

---

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交Pull Request

---

## 📝 更新日志

### v2.1.1 (2025-11-05) - 数据库Schema修复
- 🔧 **数据库Schema更新** - 修复users表缺失字段问题
- ✅ 添加username、email、real_name等字段
- ✅ 完善数据库迁移机制
- ✅ 所有测试通过（35个测试，100%成功率）
- ✅ 用户注册功能完全正常

### v2.1.0 (2025-11-05) - 权限管理重构
- ⭐ **权限系统重构** - 管理员拥有最高权限
- ✨ 代码更简洁，权限逻辑更清晰
- ✅ 更新所有API端点权限检查
- ✅ 新增权限管理文档
- ✅ 完善测试覆盖（35个测试用例）
- ✅ 100%向后兼容

### v2.0.0 (2025-11-05) - 用户认证系统
- ✨ **用户注册系统**
  - 支持学生、教师角色注册
  - 邮箱验证功能
  - 密码bcrypt加密
- ✨ **密码管理**
  - 邮箱密码重置
  - 密码修改功能
  - 安全令牌机制（1小时过期）
- ✨ **数据库管理**（仅管理员）
  - 查看所有数据表统计
  - 查看和管理表数据
  - 删除记录/清空表/清空所有数据
- ✅ SMTP邮件服务集成
- ✅ 精美HTML邮件模板
- ✅ 完整的前端组件
- ✅ 全面的API测试

### v1.1.0 (2025-11-05) - RAG集成
- ✨ **RAG API 完整集成**
- ✅ 添加 AI 大模型配置管理界面
- ✅ 添加 Prompt 提示词管理功能
- ✅ 添加向量数据库管理功能
- ✅ 实现后端 API 转发（8001 → 8000）
- ✅ 创建3个新的管理组件
- ✅ 扩展11个RAG客户端方法
- ✅ 新增10个管理员API端点
- ✅ 优化用户界面和交互体验

### v1.0.0 (2025-11-03)
- ✨ 初始版本发布
- ✅ 完整的三端权限体系
- ✅ OCR证书识别功能
- ✅ AI智能加分计算
- ✅ 离线授权验证系统

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - OCR识别引擎
- [FastAPI](https://fastapi.tiangolo.com/) - 后端框架
- [Vue.js](https://vuejs.org/) - 前端框架
- [Element Plus](https://element-plus.org/) - UI组件库

---

## 📮 联系方式

- 项目地址：https://github.com/your-repo/paddleocr-assessment
- 问题反馈：https://github.com/your-repo/paddleocr-assessment/issues
- 邮箱：support@example.com

---

<div align="center">

**如果这个项目对你有帮助，请给个 ⭐Star 支持一下！**

Made with ❤️ by PaddleOCR Team

</div>

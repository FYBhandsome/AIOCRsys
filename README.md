# 综测计算助手

<div align="center">

**基于AI的智能综合测评计算系统**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3.x-green.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-teal.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

</div>

---

## 📑 目录

- [项目简介](#项目简介)
- [核心特性](#核心特性)
- [模型存放路径](#模型存放路径)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [技术架构](#技术架构)
- [核心技术详解](#核心技术详解)
- [API测试](#api测试)
- [测试账号](#测试账号)
- [配置说明](#配置说明)
- [常见问题](#常见问题)

---

## 项目简介

综测计算助手是一个面向高校学生的智能综合测评管理系统，通过AI技术实现：

- 📷 **自动识别**: 自动识别和解析各类证书、成绩单
- 🧮 **智能计算**: 智能计算综合测评分数
- 🤖 **AI问答**: AI助手问答，解答综测相关问题
- 📊 **数据分析**: 班级成绩排名和可视化分析
- 👥 **多角色管理**: 支持管理员、教师、学生三种角色

---

## 核心特性

### 🔥 最新版本 v2.3.0

- ✅ 双虚拟环境架构，解决依赖冲突
- ✅ PaddleOCR v5 最新版本集成
- ✅ RAG智能问答系统
- ✅ 多重身份业务管理
- ✅ 完整的API测试覆盖 (209个测试用例)
- ✅ 系统设置持久化存储
- ✅ AI对话历史记录功能
- ✅ 会话管理功能

---

## 模型存放路径

### OCR模型 (PaddleOCR)

| 模型名称 | 存放路径 | 功能说明 |
|---------|---------|---------|
| PP-LCNet_x1_0_doc_ori | `~/.paddlex/official_models/PP-LCNet_x1_0_doc_ori/` | 文档方向分类 |
| UVDoc | `~/.paddlex/official_models/UVDoc/` | 文档扭曲矫正 |
| PP-LCNet_x1_0_textline_ori | `~/.paddlex/official_models/PP-LCNet_x1_0_textline_ori/` | 文本行方向分类 |
| PP-OCRv5_server_det | `~/.paddlex/official_models/PP-OCRv5_server_det/` | 文本检测模型 |
| PP-OCRv5_server_rec | `~/.paddlex/official_models/PP-OCRv5_server_rec/` | 文本识别模型 |

**模型总大小**: 约 500MB

### RAG模型 (Embedding)

| 模型名称 | 存放路径 | 功能说明 |
|---------|---------|---------|
| all-MiniLM-L6-v2 | `~/.cache/huggingface/hub/` | 文本向量化嵌入模型 |
| shibing624/text2vec-base-chinese | `~/.cache/huggingface/hub/` | 中文文本嵌入模型 |

**向量数据库**: `PaddleOCRRAG/data/chroma_db/`

---

## 快速开始

### 环境要求

- **Python**: 3.12+
- **Node.js**: 18+
- **Conda**: 用于创建虚拟环境
- **内存**: 8GB RAM（推荐）

### 一键启动

```bash
# Windows
start.bat

# 停止服务
stop.bat
```

### 手动启动

```bash
# 1. 启动 Visual Model 后端 (端口 8001)
cd visual_model
venv\python.exe main.py

# 2. 启动 RAG 后端 (端口 8000)
cd PaddleOCRRAG
..\..conda\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 3. 启动前端 (端口 5173)
cd fronted/front
npm run dev
```

### 服务地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端应用 | http://localhost:5173 | Vue 3 前端 |
| Visual Model API | http://localhost:8001/docs | FastAPI 文档 |
| RAG API | http://localhost:8000/docs | RAG 服务文档 |

---

## 项目结构

```
PaddleOCR/
├── .conda/                      # RAG项目虚拟环境 (Conda)
├── visual_model/                # 后端API服务 (FastAPI) - 端口 8001
│   ├── venv/                    # Visual Model独立虚拟环境
│   ├── app/                     # 应用代码
│   │   ├── api/                 # API路由模块
│   │   ├── core/                # 核心功能模块
│   │   ├── models/              # 数据模型
│   │   ├── services/            # 业务服务
│   │   └── utils/               # 工具函数
│   ├── scripts/                 # 管理脚本
│   ├── config.py                # 配置文件
│   └── main.py                  # 入口文件
│
├── PaddleOCRRAG/                # RAG系统服务 - 端口 8000
│   ├── app/                     # 应用代码
│   │   ├── api/                 # API路由
│   │   ├── core/                # 核心模块
│   │   ├── rag/                 # RAG核心功能
│   │   │   ├── vector_db/       # 向量数据库
│   │   │   ├── loaders/         # 文档加载器
│   │   │   ├── preprocessors/   # 预处理器
│   │   │   └── utils/           # 工具函数
│   │   └── services/            # 业务服务
│   ├── data/                    # 数据目录
│   │   ├── chroma_db/           # ChromaDB向量数据库
│   │   ├── rules/               # 综测规则文档
│   │   └── document_meta.json   # 文档元数据
│   ├── config/                  # 配置文件
│   └── scripts/                 # 管理脚本
│
├── fronted/front/               # 前端应用 (Vue 3) - 端口 5173
│   ├── src/                     # 源代码
│   │   ├── components/          # Vue组件
│   │   ├── views/               # 页面视图
│   │   ├── services/            # API服务
│   │   └── store/               # 状态管理
│   └── package.json             # Node依赖
│
├── tests/                       # 测试文件
│   ├── full_system_test.py      # 全面系统测试
│   └── test_*.py                # 其他测试文件
│
├── docs/                        # 文档目录
├── start.bat                    # 一键启动脚本
├── stop.bat                     # 一键停止脚本
└── README.md                    # 项目文档
```

---

## 技术架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      前端 (Vue 3)                            │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ 学生端  │  │ 教师端  │  │ 管理端  │  │ AI对话  │        │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Visual Model 后端 (FastAPI)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ 用户认证    │  │ OCR服务     │  │ 数据库服务  │         │
│  │ JWT         │  │ PaddleOCR   │  │ TortoiseORM │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   RAG 系统 (FastAPI)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ 向量检索    │  │  LLM对话    │  │  证书解析   │         │
│  │  ChromaDB   │  │  讯飞星火   │  │  规则匹配   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | Vue 3 + Element Plus | 渐进式框架 + UI组件库 |
| 后端 | FastAPI + Tortoise ORM | 高性能异步框架 |
| OCR | PaddleOCR v5 | 百度开源OCR引擎 |
| 向量库 | ChromaDB + HNSW | 向量数据库 |
| LLM | 讯飞星火 | 大语言模型服务 |
| 嵌入 | Sentence Transformers | 文本嵌入模型 |

---

## 核心技术详解

### 1. 向量化存储技术

#### 原理
将文本转换为高维向量表示，使得语义相似的文本在向量空间中距离更近。

```
文本 ──→ 嵌入模型 ──→ 向量(384/768维) ──→ ChromaDB
```

#### 实现代码

```python
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

embedding_function = SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2",
    device="cpu",
    normalize_embeddings=True
)
```

#### 相似度计算

- **余弦相似度**: `similarity = cos(θ) = (A · B) / (||A|| × ||B||)`
- **HNSW索引**: 分层导航小世界图，实现高效近似最近邻搜索

### 2. 文档切片策略

#### 切片参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| chunk_size | 500 | 每个切片的字符数 |
| chunk_overlap | 50 | 切片间重叠字符数 |
| separators | ["\n\n", "\n", "。"] | 分隔符优先级 |

#### 切片流程

```
文档加载 → 递归切片 → 元数据添加 → 向量化存储
```

### 3. 检索召回算法

#### 检索流程

```
用户查询 → 意图识别 → 查询增强 → 向量检索 → 竞赛检索 → 结果合并 → 重排序
```

#### 混合检索

```python
class HybridRetriever:
    def retrieve(self, query: str, top_k: int = 5):
        # 1. 向量检索
        vector_results = self.vector_db.search(query)
        
        # 2. 竞赛检索
        competition_results = self.competition_retriever.search(query)
        
        # 3. 结果合并与去重
        return self._merge_and_deduplicate(vector_results, competition_results)
```

### 4. 重排序优化

#### 评分公式

```
final_score = base_score × 0.4 + category_bonus × 0.3 + level_bonus × 0.2 + keyword_bonus × 0.1
```

#### 类别权重

| 类别 | 权重 |
|------|------|
| C1 (科技类) | 1.0 |
| C2 (体育类) | 0.8 |
| C3 (文化类) | 0.8 |
| C4 (创新创业) | 0.9 |

---

## API测试

### 测试结果

| 测试模块 | 测试项数 | 通过数 | 通过率 |
|---------|---------|-------|-------|
| 认证API | 12 | 12 | 100% |
| 学生API | 10 | 10 | 100% |
| 教师API | 14 | 14 | 100% |
| 管理员API | 8 | 8 | 100% |
| 文件管理API | 15 | 15 | 100% |
| 证书API | 10 | 10 | 100% |
| AI对话API | 8 | 8 | 100% |
| 中间件API | 25 | 25 | 100% |
| 综测计算API | 12 | 12 | 100% |
| 端到端测试 | 15 | 15 | 100% |
| **总计** | **209** | **209** | **100%** |

### 运行测试

```bash
# 运行后端测试
cd visual_model
python -m pytest tests/ -v

# 运行全面系统测试
cd tests
python full_system_test.py
```

---

## 测试账号

### 账号列表

| 用户名 | 密码 | 角色 | 权限说明 |
|--------|------|------|---------|
| dev_admin | dev123456 | admin | 开发管理员 - 完全访问权限 |
| dev_teacher | dev123456 | teacher | 开发教师 - 教师权限 |
| dev_student | dev123456 | student | 开发学生 - 学生权限 |
| admin | admin123 | admin | 系统管理员 |
| teacher | teacher123 | teacher | 测试教师 |
| student_202300502128 | student123 | student | 测试学生 |

### 权限说明

| 角色 | 可访问功能 |
|------|-----------|
| admin | 用户管理、系统设置、规则上传、数据库管理、所有教师和学生功能 |
| teacher | 学生列表、班级管理、成绩上传、成绩分析、可视化 |
| student | 个人信息、成绩查看、材料上传、结果列表 |

---

## 配置说明

### Visual Model 配置

```python
# visual_model/config.py
DATABASE_URL = "sqlite://data/database.db"
JWT_SECRET_KEY = "your-secret-key"
JWT_EXPIRATION_HOURS = 24

# OCR配置
OCR_THRESHOLD = 0.15
OCR_USE_GPU = False
OCR_LANG = "ch"

# RAG配置
RAG_BASE_URL = "http://localhost:8000"
RAG_ENABLED = True
```

### RAG 配置

```env
# PaddleOCRRAG/.env
CHROMA_DB_PATH=./data/chroma_db
RULES_DOCS_PATH=./data/rules
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu

# 讯飞星火大模型
USE_XUNFEI_LLM=true
XUNFEI_API_KEY=your_api_key
XUNFEI_MODEL_ID=xop3qwen1b7
```

---

## ⚠️ 重要说明：双虚拟环境策略

由于 `paddleocr` 和 `langchain/chromadb` 存在依赖冲突，项目采用**双虚拟环境**方案：

| 项目 | 虚拟环境路径 | 环境类型 | 主要依赖 |
|------|-------------|----------|----------|
| Visual Model | `visual_model/venv/` | Conda venv | PaddleOCR, PaddlePaddle |
| RAG | `.conda/` | Conda | LangChain, ChromaDB |

---

## 常见问题

### Q: 如何验证虚拟环境是否正确配置？

```bash
# Visual Model (venv)
visual_model\venv\python.exe -c "import paddleocr; print('OK')"

# RAG (.conda)
.conda\python.exe -c "import chromadb; print('OK')"
```

### Q: ChromaDB安装失败怎么办？

推荐使用Conda环境安装：
```bash
conda install -p .conda chromadb -c conda-forge -y
```

### Q: 端口被占用怎么办？

修改 `start.bat` 中的端口号，或手动启动服务时指定其他端口。

### Q: PaddleOCR模型下载慢怎么办？

模型会自动下载到 `~/.paddlex/official_models/`，也可以手动下载后放入该目录。

### Q: 如何查看向量数据库内容？

```bash
.conda\python.exe PaddleOCRRAG\scripts\check_db.py
```

---

## 许可证

MIT License

---

## 联系方式

如有问题或建议，请提交 Issue 或 Pull Request。

---

<div align="center">

**🌟 如果这个项目对你有帮助，请给个 Star！ 🌟**

**最后更新**: 2026-03-01  
**版本**: v2.3.0  
**状态**: ✅ 生产就绪

</div>

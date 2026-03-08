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
- [文档中心](#文档中心)
- [模型存放路径](#模型存放路径)
- [快速开始](#快速开始)
  - [详细操作步骤](#详细操作步骤)
  - [命令行参数说明](#命令行参数说明)
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

### 🔥 最新版本 v2.5.0

- ✅ 双虚拟环境架构，解决依赖冲突
- ✅ PaddleOCR v5 最新版本集成
- ✅ RAG智能问答系统
- ✅ 多重身份业务管理
- ✅ 完整的API测试覆盖 (209个测试用例)
- ✅ 系统设置持久化存储
- ✅ AI对话历史记录功能
- ✅ 会话管理功能
- ✅ Excel模板字段映射修正
- ✅ RAG JSON解析增强（重试机制+兜底方案）
- ✅ 向量切片策略优化（chunk_size=500, overlap=50）
- ✅ 前端API接口补充（uploadMaterial, getMaterials）
- ✅ **三者格式兼容性验证**（Excel、数据库、JSON）
- ✅ **统一文档体系**（docs/系统架构与数据规范.md）

---

## 文档中心

### 📚 核心文档

| 文档名称 | 路径 | 说明 |
|---------|------|------|
| 系统架构与数据规范 | [docs/系统架构与数据规范.md](docs/系统架构与数据规范.md) | 完整的系统架构、数据结构、API接口、Excel模板和三者格式映射关系 |
| RAG端到端业务系统PRD | [.trae/specs/rag-end-to-end-business-system/spec.md](.trae/specs/rag-end-to-end-business-system/spec.md) | 产品需求文档，包含功能需求和验收标准 |
| RAG端到端业务系统实施计划 | [.trae/specs/rag-end-to-end-business-system/tasks.md](.trae/specs/rag-end-to-end-business-system/tasks.md) | 实施计划，包含任务分解和优先级 |
| RAG端到端业务系统验证清单 | [.trae/specs/rag-end-to-end-business-system/checklist.md](.trae/specs/rag-end-to-end-business-system/checklist.md) | 验证清单，包含检查点和验收标准 |

### 📋 测试报告

| 文档名称 | 路径 | 说明 |
|---------|------|------|
| 三者格式兼容性测试 | [visual_model/tests/test_format_compatibility.py](visual_model/tests/test_format_compatibility.py) | Excel、数据库、JSON三者格式兼容性测试（14个测试用例） |
| RAG集成测试 | [visual_model/tests/test_rag_integration.py](visual_model/tests/test_rag_integration.py) | RAG系统集成测试（18个测试用例） |
| 综评成绩API测试 | [visual_model/tests/test_comprehensive_score_api.py](visual_model/tests/test_comprehensive_score_api.py) | 综评成绩API测试（21个测试用例） |

### 📊 历史文档（已归档）

以下文档已被整合到[系统架构与数据规范.md](docs/系统架构与数据规范.md)中，保留用于历史参考：

- [01_数据库结构文档.md](01_数据库结构文档.md)
- [02_Excel模板结构文档.md](02_Excel模板结构文档.md)
- [03_API接口对比文档.md](03_API接口对比文档.md)
- [04_三者字段映射关系表.md](04_三者字段映射关系表.md)

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

### 详细操作步骤

#### 1. 环境准备

```bash
# 克隆项目后，首先创建虚拟环境
python manage.py venv

# 安装前端依赖
cd fronted/front
npm install
```

#### 2. 启动服务

**正常模式（推荐生产环境）**

```bash
# Windows 一键启动
start.bat

# 或使用 Python 脚本
python start.py

# 停止服务
stop.bat
```

**开发测试模式（仅用于开发测试）**

```bash
# 使用 --dev 参数启动开发模式
python start.py --dev

# 开发模式特点：
# - 所有认证已禁用（无需登录即可访问所有API）
# - 自动设置 DEV_MODE=true 和 DISABLE_AUTH=true
# - 便于前端开发和API测试
# - ⚠️ 请勿用于生产环境！
```

**选择性启动服务**

```bash
# 不启动前端（仅后端服务）
python start.py --no-frontend

# 不启动RAG服务
python start.py --no-rag

# 组合使用
python start.py --dev --no-rag
```

#### 3. 访问前端应用

启动成功后，打开浏览器访问：

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端应用 | http://localhost:5173 | Vue 3 前端 |
| Visual Model API | http://localhost:8001/docs | FastAPI 文档 |
| RAG API | http://localhost:8010/docs | RAG 服务文档 |

#### 4. 测试账号信息

| 用户名 | 密码 | 角色 | 权限说明 |
|--------|------|------|---------|
| dev_admin | dev123456 | admin | 开发管理员 - 完全访问权限 |
| dev_teacher | dev123456 | teacher | 开发教师 - 教师权限 |
| dev_student | dev123456 | student | 开发学生 - 学生权限 |

> 💡 **提示**: 开发模式下无需登录，可直接访问所有功能。

### 命令行参数说明

| 参数 | 说明 |
|------|------|
| `--dev` | 开发测试模式，禁用所有认证，设置环境变量 `DEV_MODE=true` 和 `DISABLE_AUTH=true` |
| `--no-frontend` | 不启动前端服务，仅启动后端API |
| `--no-rag` | 不启动RAG服务，适用于不需要AI问答功能的场景 |
| `--help` | 显示帮助信息 |

**使用示例：**

```bash
python start.py                  # 正常启动所有服务
python start.py --dev            # 开发测试模式（禁用认证）
python start.py --no-frontend    # 不启动前端
python start.py --no-rag         # 不启动RAG服务
python start.py --dev --no-rag   # 开发模式且不启动RAG
```

### 手动启动

```bash
# 1. 启动 Visual Model 后端 (端口 8001)
cd visual_model
venv\python.exe main.py

# 2. 启动 RAG 后端 (端口 8010)
cd PaddleOCRRAG
..\..conda\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8010

# 3. 启动前端 (端口 5173)
cd fronted/front
npm run dev
```

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
├── PaddleOCRRAG/                # RAG系统服务 - 端口 8010
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
│   ├── test_api_integration.py  # API集成测试
│   ├── test_rag.py              # RAG系统测试
│   └── utils/                   # 测试工具
│
├── docs/                        # 文档目录
├── .trae/                       # 规划文档目录
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
| **三者格式兼容性** | **14** | **14** | **100%** |
| **RAG集成测试** | **18** | **18** | **100%** |
| **综评成绩API测试** | **21** | **21** | **100%** |
| **总计** | **277** | **277** | **100%** |

### 运行测试

```bash
# 运行RAG系统测试
cd PaddleOCRRAG
python -m pytest tests/ -v

# 运行Visual Model测试
cd visual_model
python -m pytest tests/ -v

# 运行API集成测试
cd tests
python -m pytest test_api_integration.py -v

# 运行三者格式兼容性测试
cd visual_model
python -m pytest tests/test_format_compatibility.py -v

# 运行RAG集成测试
cd visual_model
python -m pytest tests/test_rag_integration.py -v

# 运行综评成绩API测试
cd visual_model
python -m pytest tests/test_comprehensive_score_api.py -v
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

### 数据源表格结构

#### 综合测评计算表（主表）

| 列标 | 字段名 | 数据类型 | 说明 |
|------|--------|---------|------|
| A | 总排名 | Integer | 班级排名 |
| B | 专业 | String | 专业名称 |
| C | 班级 | String | 班级名称 |
| D | 姓名 | String | 学生姓名 |
| E | 学号 | String | 学生学号（主键） |
| F | A1—基础分 | Float | 思想道德基础分 |
| G | A2—附加分 | Float | 思想道德附加分 |
| H | A3—扣分项 | Float | 思想道德扣分 |
| I | 思想道德素质(A)总分 | Float | A类总分 |
| J | 思想道德素质(A)总分% | Float | A类加权分(20%) |
| K | 学习成绩 | Float | 学业成绩原始分 |
| L | 学习成绩% | Float | 学业成绩百分比 |
| M | 学习成绩70% | Float | B类加权分(70%) |
| N | C1—科技竞赛项目 | Float | 科技竞赛加分 |
| O | C2—体育竞技项目 | Float | 体育竞技加分 |
| P | C3—文化类竞赛项目 | Float | 文化竞赛加分 |
| Q | C4—创新创业实践项目 | Float | 创新创业加分 |
| R | 素质拓展(C)总分 | Float | C类总分 |
| S | 素质拓展(C)总分10% | Float | C类加权分(10%) |
| T | 综合测评总成绩8% | Float | 最终综测成绩 |
| U | 学生签字 | String | 学生签字确认 |

#### 加减分说明表（辅助表）

| 列标 | 字段名 | 说明 |
|------|--------|------|
| A | 专业 | 学生专业 |
| B | 班级 | 学生班级 |
| C | 姓名 | 学生姓名 |
| D | A1—基础分 | 基础分明细 |
| E | A2—附加分 | 附加分明细（含备注） |
| F | A3—扣分项 | 扣分项明细（含备注） |
| G | C1—科技竞赛项目 | 科技竞赛明细 |
| H | C2—体育竞技项目 | 体育竞技明细 |
| I | C3—文化类竞赛项目 | 文化竞赛明细 |
| J | C4—创新创业实践项目 | 创新创业明细 |

#### 学生成绩单（数据源）

| 列标 | 字段名 | 数据类型 | 映射到数据库 |
|------|--------|---------|-------------|
| A | 学号 | String | Student.id |
| B | 姓名 | String | Student.name |
| C | 班级 | String | Student.class_name |
| D | 专业名称 | String | Student.major |
| E | 年级 | String | Student.grade |
| F | 总分 | Float | AcademicScore.total_score |
| G | 门数 | Integer | AcademicScore.course_count |
| H | 总学分 | Float | AcademicScore.total_credits |
| I | 获得学分 | Float | AcademicScore.earned_credits |
| J | 算术平均分 | Float | AcademicScore.arithmetic_average |
| K | 算术平均分排名 | Integer | AcademicScore.arithmetic_average_rank |
| L | 学分加权平均分 | Float | AcademicScore.weighted_average |
| M | 学分加权平均分排名 | Integer | AcademicScore.weighted_average_rank |
| N | 平均学分绩点 | Float | AcademicScore.average_credit_gpa |
| O | 平均学分绩点排名 | Integer | AcademicScore.average_credit_gpa_rank |
| P | 不及格门次 | Integer | AcademicScore.failed_course_count |

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
RAG_BASE_URL = "http://localhost:8010"
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

**方法一：使用启动脚本自动处理**

启动脚本会自动检测端口冲突并切换到备用端口：
```bash
python start.py
```

**方法二：手动查找并关闭占用进程**

```bash
# Windows 查找占用端口的进程
netstat -ano | findstr ":8001"

# 关闭进程 (PID 为上一步查到的进程ID)
taskkill /F /PID <进程ID>
```

**方法三：选择性启动服务**

```bash
# 如果前端端口被占用，可以只启动后端
python start.py --no-frontend
```

### Q: 如何验证服务是否正常？

**方法一：访问健康检查接口**

```bash
# Visual Model 健康检查
curl http://localhost:8001/api/v1/health

# RAG 服务健康检查
curl http://localhost:8010/health
```

**方法二：访问 API 文档**

- Visual Model API: http://localhost:8001/docs
- RAG API: http://localhost:8010/docs

**方法三：查看启动日志**

```bash
# 日志文件位置
type logs\startup\startup.log
```

### Q: 如何运行测试？

```bash
# 运行RAG系统测试
cd PaddleOCRRAG
python -m pytest tests/ -v

# 运行Visual Model测试
cd visual_model
python -m pytest tests/ -v

# 运行API集成测试
cd tests
python -m pytest test_api_integration.py -v

# 运行三者格式兼容性测试
cd visual_model
python -m pytest tests/test_format_compatibility.py -v

# 运行RAG集成测试
cd visual_model
python -m pytest tests/test_rag_integration.py -v

# 运行综评成绩API测试
cd visual_model
python -m pytest tests/test_comprehensive_score_api.py -v
```

### Q: PaddleOCR模型下载慢怎么办？

模型会自动下载到 `~/.paddlex/official_models/`，也可以手动下载后放入该目录。

### Q: 如何查看向量数据库内容？

```bash
.conda\python.exe PaddleOCRRAG\scripts\check_db.py
```

### Q: 开发模式下认证是否真的被禁用？

是的，使用 `python start.py --dev` 启动时：
- 环境变量 `DEV_MODE=true`
- 环境变量 `DISABLE_AUTH=true`
- 后端服务会跳过所有认证中间件

⚠️ **警告**: 开发模式仅用于本地开发和测试，请勿在生产环境中使用！

### Q: 三者格式兼容性如何保证？

系统通过以下机制保证Excel、数据库、JSON三者格式兼容：

1. **字段映射类** (`FieldMapping`): 定义了JSON到数据库、JSON到Excel的字段映射关系
2. **数据验证类** (`DataValidator`): 实现了数据验证、类型转换、格式转换功能
3. **测试覆盖**: 14个测试用例验证三者格式兼容性
4. **统一文档**: [docs/系统架构与数据规范.md](docs/系统架构与数据规范.md) 详细说明了三者映射关系

---

## 许可证

MIT License

---

## 联系方式

如有问题或建议，请提交 Issue 或 Pull Request。

---

<div align="center">

**🌟 如果这个项目对你有帮助，请给个 Star！ 🌟**

**最后更新**: 2026-03-08  
**版本**: v2.5.0  
**状态**: ✅ 生产就绪

</div>

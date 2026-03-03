# 综测加分规则 RAG 系统

<div align="center">

**基于RAG的智能综测加分查询系统**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

</div>

---

## 📑 目录

- [项目概述](#项目概述)
- [设计逻辑](#设计逻辑)
- [核心技术架构](#核心技术架构)
- [完整的业务处理流程](#完整的业务处理流程)
- [切片策略说明](#切片策略说明)
- [性能指标](#性能指标)
- [使用说明](#使用说明)
- [API接口](#api接口)
- [配置说明](#配置说明)
- [项目结构](#项目结构)

---

## 项目概述

### 项目名称

**综测加分规则 RAG 系统** - 基于检索增强生成技术的智能综测加分查询API服务

### 项目简介

本系统是一个面向高校综合测评场景的智能问答系统，通过RAG（Retrieval-Augmented Generation，检索增强生成）技术，实现对综测加分规则的智能检索和精准问答。系统能够自动解析规则文档，构建向量索引，并根据用户查询智能匹配相关规则，返回准确的加分信息。

### 主要功能特性

| 功能模块 | 描述 |
|---------|------|
| 📄 **自动解析** | 上传规则文档（docx/xlsx/pdf/txt），自动解析并向量化存储 |
| 🤖 **智能计算** | 根据证书信息自动匹配加分规则和分值 |
| 💬 **AI对话** | 自然语言问答，支持多轮对话上下文 |
| 🎛️ **灵活配置** | 自定义Prompt提示词，个性化计算规则 |
| 📊 **完整管理** | 文档管理、向量库管理、统计分析 |
| 🏷️ **类别感知** | 自动识别查询意图，精准定位规则类别 |

---

## 设计逻辑

### RAG核心原理

RAG（Retrieval-Augmented Generation）是一种结合检索和生成的AI架构，其核心思想是：

```
用户查询 → 检索相关文档 → 构建增强上下文 → LLM生成回答
```

**核心优势**：
- **知识可更新**：无需重新训练模型，只需更新文档库
- **答案可追溯**：每个回答都有明确的文档来源
- **减少幻觉**：基于真实文档生成，降低模型编造风险
- **领域适配**：轻松适配特定领域的知识库

### 系统设计思路

本系统采用**类别感知的RAG架构**，针对综测加分规则的特点进行深度优化：

```
┌─────────────────────────────────────────────────────────────┐
│                    系统设计核心思路                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 文档预处理层                                            │
│     ├─ 智能切片：保持规则完整性，避免规则与分数分离          │
│     ├─ 类别标注：自动识别C1/C2/C3/C4子类别                  │
│     └─ 元数据增强：添加竞赛类型、级别、分数等信息            │
│                                                             │
│  2. 检索增强层                                              │
│     ├─ 意图识别：分析用户查询，预测类别和级别                │
│     ├─ 查询增强：添加类别标签，提升检索精度                  │
│     └─ 混合检索：向量检索 + 元数据过滤                       │
│                                                             │
│  3. 重排序层                                                │
│     ├─ 类别匹配：优先返回类别一致的结果                      │
│     ├─ 关键词匹配：重要术语加权                              │
│     └─ 来源权威性：官方细则优先                              │
│                                                             │
│  4. 生成层                                                  │
│     ├─ 上下文组装：整合检索结果                              │
│     ├─ Prompt工程：结构化提示词                              │
│     └─ LLM生成：讯飞星火大模型                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心技术架构

### 架构总览

```
┌─────────────────────────────────────────────────────────────────────┐
│                         核心技术架构                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐           │
│  │ 向量数据库    │   │ 嵌入模型      │   │ 意图识别器    │           │
│  │ (ChromaDB)   │   │ (Sentence-   │   │ (IntentRe-   │           │
│  │              │   │ Transformers)│   │ cognizer)    │           │
│  └──────────────┘   └──────────────┘   └──────────────┘           │
│         │                  │                  │                     │
│         ▼                  ▼                  ▼                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐           │
│  │ 竞赛映射器    │   │ 查询增强器    │   │ 重排器        │           │
│  │ (Competition │   │ (QueryEn-    │   │ (CategoryRe- │           │
│  │ Mapper)      │   │ hancer)      │   │ ranker)      │           │
│  └──────────────┘   └──────────────┘   └──────────────┘           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1. 向量数据库（ChromaDB）

**功能**：存储文档向量，支持高效相似度检索

**技术特点**：
- 使用HNSW（Hierarchical Navigable Small World）索引算法
- 支持余弦相似度、欧氏距离、点积等多种距离度量
- 持久化存储，支持元数据过滤

**核心配置**：
```python
collection = client.get_or_create_collection(
    name="zongce_rules",
    embedding_function=embedding_function,
    metadata={"hnsw:space": "cosine"}  # 使用余弦相似度
)
```

### 2. 嵌入模型（Sentence-Transformers）

**功能**：将文本转换为高维向量表示

**模型选择**：

| 模型名称 | 向量维度 | 速度 | 质量 | 适用场景 |
|---------|---------|------|------|---------|
| all-MiniLM-L6-v2 | 384 | 快 | 中 | 实时查询（默认） |
| all-mpnet-base-v2 | 768 | 中 | 高 | 精确检索 |
| paraphrase-multilingual | 768 | 中 | 高 | 多语言支持 |

**相似度计算**：
```
余弦相似度: similarity = cos(θ) = (A · B) / (||A|| × ||B||)
```

### 3. 意图识别器

**功能**：分析用户查询，预测主/子类别、竞赛类型、级别等

**识别维度**：
- **主类别**：C（素质拓展）
- **子类别**：C1（科技）、C2（体育）、C3（文化）、C4（创新创业）
- **竞赛类型**：A类、B类、非AB类
- **级别**：国家级、省部级、校级
- **获奖等级**：一等奖、二等奖、三等奖

**核心实现**：
```python
class IntentRecognizer:
    def recognize(self, query: str) -> IntentResult:
        # 1. 竞赛名称提取与匹配
        competition_name, comp_info, match_score = self._extract_competition(query)
        
        # 2. 子类别预测（基于关键词）
        sub_category, matched_kw = self._predict_sub_category(query)
        
        # 3. 级别和获奖等级提取
        level = self._extract_level(query)
        award_level = self._extract_award_level(query)
        
        return IntentResult(
            sub_category=sub_category,
            competition_type=comp_info.competition_type,
            level=level,
            award_level=award_level,
            confidence=match_score / 100.0
        )
```

### 4. 竞赛映射器

**功能**：标准化竞赛名称，支持模糊匹配

**核心能力**：
- 加载Excel竞赛列表，构建名称映射表
- 支持别名匹配（如"蓝桥杯" → "蓝桥杯全国软件和信息技术专业人才大赛"）
- 使用rapidfuzz进行模糊匹配，相似度阈值70%

**映射示例**：
```python
competition_aliases = {
    "蓝桥杯": ["蓝桥杯全国软件和信息技术专业人才大赛", "蓝桥杯大赛"],
    "互联网+": ["中国国际互联网+大学生创新创业大赛"],
    "数学建模": ["全国大学生数学建模竞赛", "高教社杯数学建模"],
}
```

### 5. 查询增强器

**功能**：为查询添加类别标签，提升检索精度

**增强策略**：
```python
# 原始查询
query = "蓝桥杯省赛一等奖加多少分"

# 增强后查询
enhanced_query = "【主类:C｜子类:C1｜竞赛类型:B｜级别:省部级｜获奖等级:一等奖】蓝桥杯省赛一等奖加多少分"
```

**元数据过滤器构建**：
```python
def build_metadata_filter(self, intent: IntentResult) -> Dict[str, Any]:
    filters = []
    if intent.sub_category:
        filters.append({"sub_category": intent.sub_category})
    if intent.competition_type:
        filters.append({"competition_type": intent.competition_type})
    return {"$and": filters} if len(filters) > 1 else filters[0]
```

### 6. 重排器

**功能**：对检索结果进行二次排序，提升类别匹配度

**评分权重**：

| 评分维度 | 权重 | 说明 |
|---------|------|------|
| 相似度分数 | 35% | 向量相似度 |
| 类别匹配 | 35% | 主类、子类、类型、级别匹配 |
| 关键词匹配 | 20% | 重要术语匹配 |
| 来源权威性 | 10% | 官方细则优先 |

**类别匹配加分**：
```python
CATEGORY_BONUS = {
    "main_match": 0.20,      # 主类别匹配
    "sub_match": 0.20,       # 子类别匹配
    "type_match": 0.15,      # 竞赛类型匹配
    "level_match": 0.15,     # 级别匹配
    "category_match": 0.10   # A/B类匹配
}
```

---

## 完整的业务处理流程

### 1. 文档加载与向量化流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                    文档加载与向量化流程                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐     │
│  │ 文档上传  │ →  │ 格式解析  │ →  │ 智能切片  │ →  │ 类别标注  │     │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘     │
│       │              │              │              │               │
│       │         docx/xlsx      chunk_size     C1/C2/C3/C4         │
│       │         pdf/txt        =1000          自动识别             │
│       │                                                        │
│       ▼              ▼              ▼              ▼               │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐     │
│  │ 元数据增强 │ →  │ 向量嵌入  │ →  │ 存储入库  │ →  │ 索引构建  │     │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘     │
│                       │                                            │
│                  Sentence-                                     │
│                  Transformers                                  │
│                  (384维向量)                                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**详细步骤**：

1. **文档上传**：支持docx、xlsx、pdf、txt格式
2. **格式解析**：提取文本内容，保留表格结构
3. **智能切片**：按段落边界切分，保护规则完整性
4. **类别标注**：根据章节标题自动识别子类别
5. **元数据增强**：添加竞赛类型、级别、分数等信息
6. **向量嵌入**：使用Sentence-Transformers生成向量
7. **存储入库**：存入ChromaDB向量数据库
8. **索引构建**：HNSW索引自动构建

### 2. 用户查询处理流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                    用户查询处理流程                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐                                                      │
│  │ 用户输入  │  "蓝桥杯省赛一等奖加多少分"                          │
│  └──────────┘                                                      │
│       │                                                             │
│       ▼                                                             │
│  ┌──────────┐                                                      │
│  │ 意图识别  │  子类:C1, 类型:B, 级别:省部级, 获奖:一等奖           │
│  └──────────┘                                                      │
│       │                                                             │
│       ▼                                                             │
│  ┌──────────┐                                                      │
│  │ 查询增强  │  添加类别标签【主类:C｜子类:C1｜...】                │
│  └──────────┘                                                      │
│       │                                                             │
│       ▼                                                             │
│  ┌──────────┐                                                      │
│  │ 向量检索  │  ChromaDB相似度搜索，Top-K=10                        │
│  └──────────┘                                                      │
│       │                                                             │
│       ▼                                                             │
│  ┌──────────┐                                                      │
│  │ 相似度过滤 │  阈值=0.7，过滤低相关结果                           │
│  └──────────┘                                                      │
│       │                                                             │
│       ▼                                                             │
│  ┌──────────┐                                                      │
│  │ 重排序    │  类别匹配 + 关键词匹配 + 来源权威性                   │
│  └──────────┘                                                      │
│       │                                                             │
│       ▼                                                             │
│  ┌──────────┐                                                      │
│  │ Top-K结果 │  返回最相关的5条规则                                  │
│  └──────────┘                                                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3. 检索增强生成流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                    检索增强生成流程                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐     │
│  │ 检索结果  │ →  │ 上下文组装 │ →  │ Prompt构建 │ →  │ LLM生成   │     │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘     │
│                       │              │              │               │
│                  整合Top-K结果    结构化提示词    讯飞星火大模型    │
│                  构建上下文窗口   注入规则信息    生成自然语言回答  │
│                                                                     │
│       ┌──────────────────────────────────────────────────┐         │
│       │                 Prompt模板示例                    │         │
│       ├──────────────────────────────────────────────────┤         │
│       │ 你是一个综测加分规则助手。                        │         │
│       │                                                  │         │
│       │ 参考规则：                                        │         │
│       │ {context}                                        │         │
│       │                                                  │         │
│       │ 用户问题：{query}                                │         │
│       │                                                  │         │
│       │ 请根据以上规则，回答用户的问题。                  │         │
│       │ 如果规则中没有相关信息，请明确说明。              │         │
│       └──────────────────────────────────────────────────┘         │
│                                                                     │
│       ┌──────────────────────────────────────────────────┐         │
│       │                 输出示例                          │         │
│       ├──────────────────────────────────────────────────┤         │
│       │ 根据规则，蓝桥杯属于B类竞赛。                     │         │
│       │ 省级（省部级）一等奖加分为：15分。                │         │
│       │                                                  │         │
│       │ 规则来源：计算机学院综合测评实施细则              │         │
│       └──────────────────────────────────────────────────┘         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 切片策略说明

### 当前切片参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `chunk_size` | 1000 | 每个切片的最大字符数 |
| `chunk_overlap` | 150 | 切片之间的重叠字符数 |
| `similarity_threshold` | 0.7 | 相似度阈值，低于此值的结果将被过滤 |

### 分隔符优先级

系统按以下优先级进行文本切分：

```python
separators = [
    "\n\n",      # 优先级1：段落边界
    "。\n",      # 优先级2：句末换行
    "。\r\n",    # 优先级3：句末换行（Windows）
    "\n",        # 优先级4：换行符
    "。",        # 优先级5：句号
    "！",        # 优先级6：感叹号
    "？",        # 优先级7：问号
    "；",        # 优先级8：分号
    "，",        # 优先级9：逗号
    " ",         # 优先级10：空格
    ""           # 优先级11：字符级切分
]
```

### 规则边界检测

系统采用**智能规则完整性保护**策略，确保规则与分数在同一切片：

**检测模式**：
```python
RULE_SCORE_PATTERN = re.compile(
    r'([AB]类[^国省市]*[国省市]级[^奖]*[一二三]等奖[^0-9]*(\d+)[分])|'
    r'(国家级[^奖]*[一二三]等奖[^0-9]*(\d+)[分])|'
    r'(省部级[^奖]*[一二三]等奖[^0-9]*(\d+)[分])'
)
```

**示例**：
```
原始文本：
"A类国家级一等奖20分，A类国家级二等奖15分，B类省部级一等奖10分"

切分结果：
切片1: "A类国家级一等奖20分"
切片2: "A类国家级二等奖15分"
切片3: "B类省部级一等奖10分"
```

### 特殊内容处理

| 内容类型 | 处理策略 |
|---------|---------|
| **表格** | 按行切分，保持行完整性 |
| **列表项** | 按列表项边界切分 |
| **规则条款** | 保护规则与分数的完整性 |

---

## 性能指标

### 检索准确率

| 指标 | 数值 | 说明 |
|------|------|------|
| **竞赛类别匹配准确率** | 100% | A类/B类/非AB类识别准确率 |
| **分数规则检索准确率** | 93.8% | 正确返回加分规则的比例 |
| **综合测评规则覆盖率** | 87.5% | 规则文档覆盖的完整性 |
| **测试通过率** | 85.7% | 7项测试中6项通过 |

### 响应性能

| 操作 | 平均耗时 | 说明 |
|------|---------|------|
| 文档加载（docx） | 139ms | 91个段落 |
| 文档加载（xlsx） | 622ms | 172条记录 |
| RAG系统初始化 | 2.7s | 包含模型加载 |
| 向量检索 | 257ms | 单次查询 |
| 类别感知检索 | 244ms | 含意图识别+重排 |

### 系统资源

| 指标 | 数值 | 说明 |
|------|------|------|
| 启动时间 | < 5s | 服务启动到可接受请求 |
| 内存占用 | < 500MB | 稳定运行时 |
| 向量维度 | 384 | all-MiniLM-L6-v2模型 |

---

## 使用说明

### 环境要求

- **Python**: 3.8+
- **内存**: 8GB RAM（推荐）
- **系统**: Windows 10+ / Linux / macOS

### 安装依赖

```bash
pip install -r requirements.txt
```

### 环境配置

创建 `.env` 文件：

```env
# 向量数据库配置
CHROMA_DB_PATH=./data/chroma_db
RULES_DOCS_PATH=./data/rules

# RAG配置
TOP_K=2                      # 检索返回的相关文档数量
MAX_CONTEXT_LENGTH=1024      # 上下文长度限制

# 嵌入模型配置
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu
HF_ENDPOINT=https://hf-mirror.com

# 讯飞星火大模型配置
USE_XUNFEI_LLM=true
XUNFEI_API_KEY=your_api_key
XUNFEI_MODEL_ID=your_model_id
XUNFEI_BASE_URL=http://maas-api.cn-huabei-1.xf-yun.com/v1
XUNFEI_TEMPERATURE=0.1
XUNFEI_MAX_TOKENS=1024
```

### 缓存目录说明

系统在运行时会在用户目录下创建缓存文件，Windows系统默认缓存目录为：

```
C:\Users\<用户名>\.cache\
├── chroma/                          # Chroma向量数据库缓存
│   └── (向量索引和元数据缓存)
│
└── huggingface/                     # Hugging Face模型缓存
    └── hub/
        └── models--sentence-transformers--all-MiniLM-L6-v2/
            # 嵌入模型文件（约90MB）
            # 首次运行时自动下载
```

**说明**：
- `chroma`：存储Chroma向量数据库的缓存数据
- `huggingface`：存储Hugging Face模型，包括`all-MiniLM-L6-v2`嵌入模型
- 首次运行时，系统会自动下载嵌入模型到`huggingface/hub`目录
- 如需更改缓存位置，可设置环境变量`HF_HOME`和`CHROMA_CACHE_DIR`

### 测试账号

系统提供以下测试账号供开发者登录测试使用：

| 角色 | 用户名 | 密码 | 说明 |
|------|--------|------|------|
| **管理员** | `admin` | `admin123` | 系统管理员账号，拥有全部权限 |
| **管理员** | `dev_admin` | `dev123` | 开发管理员账号（推荐使用） |
| **教师** | `teacher` | `teacher123` | 测试教师账号 |
| **教师** | `dev_teacher` | `dev123` | 开发教师账号 |
| **学生** | `student_202300502128` | `student123` | 测试学生账号 |
| **学生** | `dev_student` | `dev123` | 开发学生账号 |

**推荐开发者使用**：`dev_admin` / `dev123`（管理员权限）

### 启动服务

```bash
# 开发模式
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# 生产模式
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 访问服务

- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **交互式测试**: http://localhost:8000/static/api_test.html
- **文档分析页面**: http://localhost:8000/static/document_analysis.html

---

## API接口

### 1. 文档管理

| API端点 | 方法 | 功能 |
|---------|------|------|
| `/api/v1/documents/upload` | POST | 上传单个文档 |
| `/api/v1/documents/batch-upload` | POST | 批量上传文档 |
| `/api/v1/documents` | GET | 获取文档列表 |
| `/api/v1/documents/{doc_id}` | DELETE | 删除文档 |

### 2. 加分计算

| API端点 | 方法 | 功能 |
|---------|------|------|
| `/api/v1/chat` | POST | AI对话交流 |
| `/api/v1/calculate-score` | POST | 计算综测加分 |

### 3. 向量库管理

| API端点 | 方法 | 功能 |
|---------|------|------|
| `/api/v1/vector-db/stats` | GET | 获取向量库统计 |
| `/api/v1/vector-db/clear` | DELETE | 清空向量库 |

### 使用示例

```python
import requests

# AI对话
url = "http://localhost:8000/api/v1/chat"
data = {
    "message": "蓝桥杯省赛一等奖加多少分",
    "chat_history": []
}
response = requests.post(url, json=data)
result = response.json()
print(f"回复: {result['data']['response']}")

# 计算加分
url = "http://localhost:8000/api/v1/calculate-score"
data = {
    "competition_name": "蓝桥杯",
    "award_level": "一等奖",
    "level": "省部级"
}
response = requests.post(url, json=data)
result = response.json()
print(f"加分: {result['data']['score']}")
```

---

## 配置说明

### 环境变量配置

```env
# 向量数据库配置
CHROMA_DB_PATH=./data/chroma_db      # 向量数据库存储路径
RULES_DOCS_PATH=./data/rules          # 规则文档目录

# RAG配置
TOP_K=2                               # 检索返回数量
MAX_CONTEXT_LENGTH=1024               # 上下文最大长度

# 嵌入模型配置
EMBEDDING_MODEL=all-MiniLM-L6-v2      # 嵌入模型名称
EMBEDDING_DEVICE=cpu                  # 计算设备（cpu/cuda）
HF_ENDPOINT=https://hf-mirror.com     # HuggingFace镜像

# 讯飞星火大模型配置
USE_XUNFEI_LLM=true                   # 是否使用讯飞星火
XUNFEI_API_KEY=your_api_key           # API密钥
XUNFEI_MODEL_ID=your_model_id         # 模型ID
XUNFEI_BASE_URL=http://maas-api.cn-huabei-1.xf-yun.com/v1
XUNFEI_TEMPERATURE=0.1                # 生成温度
XUNFEI_MAX_TOKENS=1024                # 最大生成长度
```

---

## 项目结构

```
PaddleOCRRAG/
├── app/
│   ├── main.py                     # FastAPI 应用入口
│   ├── models.py                   # 数据模型定义
│   ├── core/
│   │   ├── config_manager.py       # 配置管理
│   │   ├── llm_manager.py          # LLM管理器
│   │   ├── prompt_manager.py       # Prompt管理器
│   │   ├── document_manager.py     # 文档管理器
│   │   ├── cache.py                # 缓存管理
│   │   ├── dependencies.py         # 依赖注入
│   │   ├── exceptions.py           # 异常定义
│   │   └── logger.py               # 统一日志系统
│   ├── api/
│   │   ├── routes.py               # API 路由注册
│   │   ├── chat_routes.py          # 聊天路由
│   │   ├── document_routes.py      # 文档路由
│   │   ├── certificate_routes.py   # 证书路由
│   │   ├── vector_db_routes.py     # 向量库路由
│   │   ├── prompt_routes.py        # Prompt路由
│   │   ├── system_routes.py        # 系统路由
│   │   ├── cache_routes.py         # 缓存路由
│   │   └── log_routes.py           # 日志路由
│   ├── rag/
│   │   ├── vector_db/
│   │   │   ├── base_vector_db.py   # 向量数据库基类
│   │   │   ├── vector_db.py        # 向量数据库实现
│   │   │   └── reranker.py         # 重排序器
│   │   ├── loaders/
│   │   │   ├── loader.py           # 文档加载器
│   │   │   └── enhanced_loader.py  # 增强加载器
│   │   ├── preprocessors/
│   │   │   ├── intent_recognizer.py    # 意图识别器
│   │   │   ├── query_enhancer.py       # 查询增强器
│   │   │   └── competition_mapper.py   # 竞赛映射器
│   │   └── utils/
│   │       └── category_keywords.py    # 类别关键词
│   ├── services/
│   │   ├── chat_service.py         # 聊天服务
│   │   ├── document_service.py     # 文档服务
│   │   ├── certificate_service.py  # 证书服务
│   │   └── system_service.py       # 系统服务
│   └── models/
│       └── schemas.py              # Pydantic模型
├── config/
│   ├── app_config.json             # 应用配置
│   └── prompts.json                # Prompt模板
├── data/
│   ├── rules/                      # 规则文档目录
│   │   ├── 计算机学院综合测评实施细则.docx
│   │   └── 学科竞赛名称列表.xlsx
│   ├── chroma_db/                  # 向量数据库
│   └── document_meta.json          # 文档元数据
├── scripts/
│   ├── vectorize_documents.py      # 文档向量化脚本
│   ├── verify_vector_db.py         # 向量库验证脚本
│   └── diagnose_rag.py             # RAG诊断脚本
├── static/
│   ├── api_test.html               # API测试页面
│   └── interactive_api_docs.html   # 交互式文档
├── tests/
│   ├── test_rag_accuracy.py        # RAG准确率测试
│   ├── test_api.py                 # API测试
│   └── conftest.py                 # 测试配置
├── rag_client/
│   └── paddle_ocrrag_client.py     # Python客户端
├── requirements.txt                # 项目依赖
├── pytest.ini                      # Pytest配置
└── README.md                       # 本文档
```

---

## 📚 学习资源

- **[FastAPI 官方文档](https://fastapi.tiangolo.com/)**
- **[LangChain 文档](https://python.langchain.com/)**
- **[ChromaDB 文档](https://docs.trychroma.com/)**
- **[Sentence-Transformers 文档](https://www.sbert.net/)**
- **[讯飞星火 API 文档](https://www.xfyun.cn/doc/spark/API.html)**

---

## 📄 许可证

本项目仅供学习和研究使用。

---

<div align="center">

**🌟 如果这个项目对你有帮助，请给个 Star！ 🌟**

**最后更新**: 2026-03-03  
**版本**: v2.4.0  
**状态**: ✅ 生产就绪

</div>

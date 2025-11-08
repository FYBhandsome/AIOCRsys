# 综测计算助手 - 后端服务

基于FastAPI的高性能后端API服务，提供OCR识别、综测计算、用户管理等核心功能。

---

## 📋 功能特性

- ✅ **RESTful API**: 完整的REST风格API接口
- ✅ **JWT认证**: 基于Token的用户认证
- ✅ **角色权限**: 学生/教师/管理员三级权限
- ✅ **OCR识别**: PaddleOCR证书文字识别
- ✅ **AI集成**: RAG系统智能加分计算
- ✅ **异步处理**: 高并发异步请求处理
- ✅ **数据持久化**: Tortoise ORM数据库管理
- ✅ **离线授权**: 完整的License验证系统

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境

```bash
# 复制配置文件
cp .env.example .env

# 编辑配置
nano .env
```

### 3. 启动服务

```bash
# 开发环境
python main.py

# 生产环境
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001
```

### 4. 访问文档

- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

---

## 📁 项目结构

```
visual_model/
├── app/                    # 应用核心
│   ├── api/               # API路由
│   ├── core/              # 核心功能
│   ├── models/            # 数据模型
│   ├── services/          # 业务服务
│   └── business/          # 业务逻辑
├── config.py              # 配置文件
├── main.py                # 应用入口
├── requirements.txt       # 依赖包
├── data/                  # 数据目录
├── uploads/               # 上传文件
└── logs/                  # 日志文件
```

---

## 🔧 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| DEBUG | False | 调试模式 |
| HOST | 127.0.0.1 | 服务器地址 |
| PORT | 8001 | 服务器端口 |
| DATABASE_URL | sqlite:///data/database.db | 数据库URL |
| JWT_SECRET_KEY | 随机生成 | JWT密钥 |
| OCR_USE_GPU | False | GPU加速 |
| RAG_ENABLED | True | 启用RAG |

---

## 📡 API概览

### 认证接口
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/auth/me` - 获取当前用户信息
- `POST /api/v1/auth/password/reset-request` - 请求密码重置
- `POST /api/v1/auth/password/reset-confirm` - 确认密码重置
- `POST /api/v1/auth/password/change` - 修改密码

### 学生接口
- `POST /api/v1/student/certificate/upload` - 上传证书
- `GET /api/v1/student/scores/summary` - 成绩摘要
- `GET /api/v1/student/uploads` - 上传历史

### 教师接口
- `GET /api/v1/teacher/classes` - 班级列表
- `POST /api/v1/teacher/scores/upload` - 上传成绩
- `GET /api/v1/teacher/scores/analysis` - 成绩分析

### 管理员接口
- `POST /api/v1/admin/rules/upload` - 上传规则
- `GET /api/v1/admin/ai/config` - AI配置
- `GET /api/v1/admin/users` - 用户管理
- `GET /api/v1/admin/database/tables` - 数据库表列表
- `GET /api/v1/admin/database/tables/{table}/data` - 获取表数据
- `DELETE /api/v1/admin/database/tables/{table}/records/{id}` - 删除记录

---

## 🗄️ 数据库

使用Tortoise ORM，支持多种数据库：

- SQLite（默认）
- MySQL
- PostgreSQL

### 初始化数据库

```bash
# 自动创建表（首次启动）
python main.py

# 手动迁移（推荐）
python scripts/manage_db.py migrate

# 检查数据库表状态
python scripts/manage_db.py check

# 重置数据库（⚠️ 会删除所有数据）
python scripts/manage_db.py reset
```

### 数据库Schema管理

系统使用Tortoise ORM自动管理数据库schema。如果遇到schema不匹配问题：

1. **运行迁移**：
   ```bash
   python scripts/manage_db.py migrate
   ```

2. **检查表状态**：
   ```bash
   python scripts/manage_db.py check
   ```

3. **创建示例数据**（开发测试用）：
   ```bash
   python scripts/manage_db.py sample
   ```

**注意：** 生产环境请谨慎使用重置命令，建议先备份数据库。

---

## 🧪 测试

```bash
# 运行完整系统测试（推荐）
python test_system.py

# 快速测试（核心功能）
python test_system.py --quick

# 详细输出
python test_system.py --verbose

# 使用pytest（单元测试）
pytest
pytest --cov=app
```

**测试覆盖：**
- ✅ 35个综合测试用例
- ✅ 认证、权限、安全测试
- ✅ API功能测试
- ✅ 数据库管理测试
- ✅ RAG集成测试

---

## 📝 开发规范

- 遵循PEP 8代码风格
- 使用类型注解
- 添加文档字符串
- 编写单元测试

---

## 🔗 相关链接

- [FastAPI文档](https://fastapi.tiangolo.com/)
- [Tortoise ORM](https://tortoise-orm.readthedocs.io/)
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)

---

*项目主页: [README.md](../README.md)*

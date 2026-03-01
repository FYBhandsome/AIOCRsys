# 开发环境配置指南

## 环境概览

本项目包含两个后端服务，每个服务使用独立的虚拟环境：

| 项目 | 路径 | 虚拟环境 | Python解释器 |
|------|------|----------|--------------|
| PaddleOCRRAG (RAG服务) | `d:\PaddleOCR\PaddleOCRRAG` | `.conda` | `d:\PaddleOCR\.conda\python.exe` |
| visual_model (主应用) | `d:\PaddleOCR\visual_model` | `venv` 或系统Python | `D:\Anaconda3\python.exe` |

## 环境配置详情

### 1. PaddleOCRRAG 项目 (RAG服务)

**虚拟环境路径**: `d:\PaddleOCR\.conda`

**激活方式**:
```powershell
# PowerShell
d:\PaddleOCR\.conda\Scripts\Activate.ps1

# CMD
d:\PaddleOCR\.conda\Scripts\activate.bat
```

**依赖安装**:
```powershell
cd d:\PaddleOCR\PaddleOCRRAG
pip install -r requirements.txt
```

**启动服务**:
```powershell
cd d:\PaddleOCR\PaddleOCRRAG
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**运行测试**:
```powershell
cd d:\PaddleOCR\PaddleOCRRAG
python -m pytest tests/ -v
```

### 2. visual_model 项目 (主应用)

**虚拟环境路径**: `d:\PaddleOCR\visual_model\venv` 或使用系统Python (`D:\Anaconda3\python.exe`)

**激活方式**:
```powershell
# PowerShell - 使用venv
d:\PaddleOCR\visual_model\venv\Scripts\Activate.ps1

# 或使用系统Python (推荐)
# 无需激活，直接使用 D:\Anaconda3\python.exe
```

**依赖安装**:
```powershell
cd d:\PaddleOCR\visual_model
pip install -r requirements.txt
```

**启动服务**:
```powershell
cd d:\PaddleOCR\visual_model
python main.py
# 或
python -m uvicorn app.api_entry:app --host 0.0.0.0 --port 8080
```

**运行测试**:
```powershell
cd d:\PaddleOCR\visual_model
D:\Anaconda3\python.exe -m pytest tests/ -v
```

## 常用命令速查

### RAG项目 (PaddleOCRRAG)

| 操作 | 命令 |
|------|------|
| 激活环境 | `d:\PaddleOCR\.conda\Scripts\Activate.ps1` |
| 安装依赖 | `pip install -r requirements.txt` |
| 启动服务 | `python -m uvicorn app.main:app --port 8000` |
| 运行测试 | `python -m pytest tests/ -v` |
| 检查依赖 | `pip list` |

### 主应用项目 (visual_model)

| 操作 | 命令 |
|------|------|
| 使用系统Python | `D:\Anaconda3\python.exe` |
| 安装依赖 | `pip install -r requirements.txt` |
| 启动服务 | `python main.py` |
| 运行测试 | `D:\Anaconda3\python.exe -m pytest tests/ -v` |
| 检查依赖 | `pip list` |

## 环境验证脚本

### 验证RAG环境
```powershell
cd d:\PaddleOCR\PaddleOCRRAG
d:\PaddleOCR\.conda\python.exe -c "import fastapi; import chromadb; print('RAG环境验证成功')"
```

### 验证主应用环境
```powershell
cd d:\PaddleOCR\visual_model
D:\Anaconda3\python.exe -c "import fastapi; import tortoise; print('主应用环境验证成功')"
```

## 服务依赖关系

```
visual_model (主应用:8080)
    │
    └──> PaddleOCRRAG (RAG服务:8000)
              │
              └──> 向量数据库 (ChromaDB)
              └──> LLM服务 (智谱AI/本地模型)
```

## 注意事项

1. **端口配置**:
   - RAG服务默认运行在 `8000` 端口
   - 主应用默认运行在 `8080` 端口

2. **数据库**:
   - 主应用使用 SQLite (开发) / MySQL (生产)
   - RAG服务使用 ChromaDB 向量数据库

3. **环境隔离**:
   - 两个项目使用独立的虚拟环境
   - 避免依赖冲突

4. **测试运行**:
   - 测试前确保数据库已初始化
   - 可使用 `scripts/init_test_data.py` 初始化测试数据

## 故障排除

### 问题: 模块找不到
```powershell
# 确保在正确的目录下运行
cd d:\PaddleOCR\visual_model
# 或
cd d:\PaddleOCR\PaddleOCRRAG

# 重新安装依赖
pip install -r requirements.txt
```

### 问题: 端口被占用
```powershell
# 查看端口占用
netstat -ano | findstr :8000
netstat -ano | findstr :8080

# 结束占用进程 (替换PID)
taskkill /PID <进程ID> /F
```

### 问题: 虚拟环境激活失败
```powershell
# 允许脚本执行
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

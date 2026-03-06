# 端口配置说明文档

## 概述
本文档记录了综测计算助手项目各服务的端口配置分配，确保系统各组件能够正常启动并通信。

## 端口分配表

| 服务名称 | 默认端口 | 备用端口 | 虚拟环境 | 配置文件 | 说明
|---|---|---|---|---|---|
| Visual Model 后端 | 8001 | 8002, 8003, 8004, 8005, 8006 | venv | visual_model/config.py | 主后端API服务，提供OCR识别、用户认证、数据管理等功能
| RAG 服务 | 8000 | 8010, 8011, 8012, 8013, 8014 | .conda | start.py / PaddleOCRRAG/app/main.py | RAG智能问答服务，提供文档检索和AI对话功能
| 前端应用 | 5173 | 5174, 5175, 5176, 5177, 5178 | Node.js | fronted/front/.env | Vue.js前端应用，提供用户界面

## 配置文件位置

### Visual Model 服务
- 配置文件：`visual_model/config.py`
- 环境变量：`visual_model/.env`
- 端口配置：`PORT: int = Field(default=8001)`
- RAG服务调用地址：`RAG_BASE_URL: str = Field(default="http://localhost:8000")`

### RAG 服务
- 启动脚本：`start.py`
- 配置文件：`PaddleOCRRAG/app/main.py`
- 独立启动脚本：`PaddleOCRRAG/run.bat`
- 端口配置：`port=8000`

### 前端应用
- 配置文件：`fronted/front/.env`
- API地址配置：`VITE_API_BASE_URL=http://localhost:8001/api`

## 端口冲突解决历史

### 问题日期：2026-03-06
**问题描述**：RAG服务的备用端口列表包含8001，与Visual Model服务的默认端口冲突。
**影响范围**：系统启动时，RAG服务在8000被占用时会尝试使用8001，导致Visual Model服务无法启动。

**修复方案**：
1. 修改`start.py`中RAG服务的备用端口配置
2. 将RAG服务的备用端口从`[8001, 8010, 8011, 8012, 8013]`改为`[8010, 8011, 8012, 8013, 8014]`
3. 确保两个服务的端口范围完全隔离

**修改文件**：`d:\PaddleOCR\start.py` 第124行

## 服务间通信架构

```
前端 (5173)
    |
    └─> Visual Model (8001)
          |
          └─> RAG 服务 (8000)
```

## 启动方式

### 统一启动（推荐）
```bash
# 在项目根目录执行
start.bat
# 或
python start.py
```

### 独立启动
```bash
# Visual Model 服务
cd visual_model
venv\Scripts\activate
python main.py

# RAG 服务
cd PaddleOCRRAG
..\.conda\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
# 或使用
run.bat

# 前端应用
cd fronted\front
npm run dev
```

## 端口检查命令

### Windows 系统
```cmd
# 检查端口占用
netstat -ano | findstr ":8000"
netstat -ano | findstr ":8001"

# 关闭占用端口的进程
taskkill /F /PID <进程ID>
```

## 注意事项

1. **虚拟环境区分**：
   - Visual Model 使用 venv 虚拟环境：`visual_model/venv/
   - PaddleOCRRAG 使用 .conda 虚拟环境：.conda/

2. **端口隔离**：确保各服务端口范围完全隔离，避免冲突

3. **跨服务调用**：
   - 前端调用 Visual Model: http://localhost:8001/api
   - Visual Model 调用 RAG: http://localhost:8000

4. **健康检查端点**：
   - Visual Model: /api/v1/health
   - RAG服务: /health

## 更新日志

- 2026-03-06
  - 初始创建文档
  - 修复RAG服务备用端口冲突问题

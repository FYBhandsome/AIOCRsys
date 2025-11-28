# PaddleOCRRAG API 使用指南

本指南提供了PaddleOCRRAG API的详细使用示例和最佳实践，帮助开发者快速集成和使用API功能。

## 目录

- [快速开始](#快速开始)
- [认证与安全](#认证与安全)
- [API使用示例](#api使用示例)
  - [系统管理API](#系统管理api)
  - [文档管理API](#文档管理api)
  - [证书加分计算API](#证书加分计算api)
  - [AI对话API](#ai对话api)
  - [配置管理API](#配置管理api)
- [错误处理](#错误处理)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)
- [更新日志](#更新日志)

## 快速开始

### 1. 启动服务

```bash
# 启动PaddleOCRRAG服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 验证服务

```bash
# 检查服务健康状态
curl -X GET "http://localhost:8000/api/v1/health"
```

### 3. 基本API调用

```python
import requests

# API基础URL
BASE_URL = "http://localhost:8000"

# 健康检查
response = requests.get(f"{BASE_URL}/api/v1/health")
print(response.json())
```

## 认证与安全

### 当前认证方式

目前API不需要认证，但建议在生产环境中添加适当的认证机制：

```python
# 示例：添加API密钥认证
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_API_KEY"
}

response = requests.get(f"{BASE_URL}/api/v1/health", headers=headers)
```

### 安全建议

1. **HTTPS**: 在生产环境中使用HTTPS
2. **API密钥**: 实施API密钥认证
3. **速率限制**: 添加适当的速率限制
4. **输入验证**: 对用户输入进行验证和清理
5. **日志记录**: 记录API访问日志

## API使用示例

### 系统管理API

#### 健康检查

```python
import requests

def check_health():
    """检查系统健康状态"""
    response = requests.get("http://localhost:8000/api/v1/health")
    
    if response.status_code == 200:
        data = response.json()
        print(f"系统状态: {data['status']}")
        print(f"服务版本: {data['version']}")
        print(f"运行时间: {data['uptime']}")
        return True
    else:
        print(f"健康检查失败: {response.status_code}")
        return False

# 使用示例
check_health()
```

#### LLM连接测试

```python
import requests

def test_llm_connection():
    """测试LLM连接"""
    response = requests.post(
        "http://localhost:8000/api/v1/llm/test",
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            print("LLM连接成功")
            print(f"响应时间: {data['data'].get('response_time', 'N/A')}ms")
            return True
        else:
            print(f"LLM连接失败: {data.get('error', {}).get('message', '未知错误')}")
            return False
    else:
        print(f"请求失败: {response.status_code}")
        return False

# 使用示例
test_llm_connection()
```

### 文档管理API

#### 上传文档

```python
import requests
import os

def upload_document(file_path, description=""):
    """上传单个文档"""
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return None
    
    url = "http://localhost:8000/api/v1/documents/upload"
    
    with open(file_path, 'rb') as f:
        files = {'file': (os.path.basename(file_path), f)}
        data = {'description': description}
        
        response = requests.post(url, files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                doc_info = result["data"]
                print(f"文档上传成功")
                print(f"文档ID: {doc_info['id']}")
                print(f"文件名: {doc_info['filename']}")
                print(f"状态: {doc_info['status']}")
                return doc_info
            else:
                print(f"上传失败: {result.get('error', {}).get('message', '未知错误')}")
                return None
        else:
            print(f"请求失败: {response.status_code}")
            return None

# 使用示例
doc_info = upload_document("规则文档.docx", "2025年综测规则")
```

#### 获取文档列表

```python
import requests

def get_documents_list(skip=0, limit=100, status=None):
    """获取文档列表"""
    url = "http://localhost:8000/api/v1/documents"
    params = {"skip": skip, "limit": limit}
    
    if status:
        params["status"] = status
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            documents = result["data"]["items"]
            total = result["data"]["total"]
            
            print(f"共找到 {total} 个文档:")
            for doc in documents:
                print(f"- ID: {doc['id']}, 文件名: {doc['filename']}, 状态: {doc['status']}")
            
            return documents
        else:
            print(f"获取失败: {result.get('error', {}).get('message', '未知错误')}")
            return None
    else:
        print(f"请求失败: {response.status_code}")
        return None

# 使用示例
documents = get_documents_list()
```

#### 更新文档状态

```python
import requests

def update_document_status(doc_id, status):
    """更新文档状态"""
    url = f"http://localhost:8000/api/v1/documents/{doc_id}/status"
    data = {"status": status}
    
    response = requests.patch(url, json=data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print(f"文档状态更新成功: {status}")
            return True
        else:
            print(f"更新失败: {result.get('error', {}).get('message', '未知错误')}")
            return False
    else:
        print(f"请求失败: {response.status_code}")
        return False

# 使用示例
update_document_status("doc_id_here", "enabled")
```

### 证书加分计算API

#### 计算证书加分

```python
import requests

def calculate_certificate_score(certificate_text, student_info=None):
    """计算证书加分"""
    url = "http://localhost:8000/api/v1/calculate-score"
    
    data = {"certificate_text": certificate_text}
    if student_info:
        data["student_info"] = student_info
    
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            score_data = result["data"]
            print(f"证书分析成功")
            print(f"类别: {score_data.get('category', 'N/A')}")
            print(f"加分: {score_data.get('score', 'N/A')}")
            print(f"置信度: {score_data.get('confidence', 'N/A')}")
            
            if "reasoning" in score_data:
                print(f"推理过程: {score_data['reasoning']}")
            
            return score_data
        else:
            print(f"计算失败: {result.get('error', {}).get('message', '未知错误')}")
            return None
    else:
        print(f"请求失败: {response.status_code}")
        return None

# 使用示例
certificate_text = "张三同学在2023年全国大学生数学建模竞赛中获得一等奖"
student_info = {"年级": "大三", "专业": "计算机科学"}

score_data = calculate_certificate_score(certificate_text, student_info)
```

#### 批量计算证书加分

```python
import requests
import json

def batch_calculate_scores(certificates_list):
    """批量计算证书加分"""
    url = "http://localhost:8000/api/v1/calculate-score/batch"
    
    data = {"certificates": certificates_list}
    
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            results = result["data"]["results"]
            print(f"批量计算完成，共处理 {len(results)} 个证书")
            
            for i, score_data in enumerate(results):
                print(f"\n证书 {i+1}:")
                print(f"  类别: {score_data.get('category', 'N/A')}")
                print(f"  加分: {score_data.get('score', 'N/A')}")
                print(f"  置信度: {score_data.get('confidence', 'N/A')}")
            
            return results
        else:
            print(f"批量计算失败: {result.get('error', {}).get('message', '未知错误')}")
            return None
    else:
        print(f"请求失败: {response.status_code}")
        return None

# 使用示例
certificates = [
    {"certificate_text": "获得2023年全国大学生数学建模竞赛一等奖"},
    {"certificate_text": "通过大学英语六级考试，分数550分"},
    {"certificate_text": "发表SCI论文一篇，影响因子3.5"}
]

batch_results = batch_calculate_scores(certificates)
```

### AI对话API

#### 智能问答

```python
import requests

def chat_with_ai(question, use_rag=True, conversation_history=None):
    """与AI进行对话"""
    url = "http://localhost:8000/api/v1/chat"
    
    data = {
        "question": question,
        "use_rag": use_rag
    }
    
    if conversation_history:
        data["conversation_history"] = conversation_history
    
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            chat_data = result["data"]
            reply = chat_data.get("reply", "")
            
            print(f"AI回复: {reply}")
            
            # 如果使用了RAG，显示相关文档信息
            if use_rag and "sources" in chat_data:
                sources = chat_data["sources"]
                if sources:
                    print("\n相关文档:")
                    for source in sources:
                        print(f"- {source.get('title', 'N/A')} (相似度: {source.get('similarity', 'N/A')})")
            
            return reply
        else:
            print(f"对话失败: {result.get('error', {}).get('message', '未知错误')}")
            return None
    else:
        print(f"请求失败: {response.status_code}")
        return None

# 使用示例
question = "获得国家级奖学金可以加多少分？"
reply = chat_with_ai(question)
```

#### 多轮对话

```python
import requests

def multi_turn_chat():
    """多轮对话示例"""
    url = "http://localhost:8000/api/v1/chat"
    conversation_history = []
    
    print("开始多轮对话 (输入'quit'退出)")
    
    while True:
        user_input = input("\n您: ")
        
        if user_input.lower() == 'quit':
            break
        
        data = {
            "question": user_input,
            "use_rag": True,
            "conversation_history": conversation_history
        }
        
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                chat_data = result["data"]
                reply = chat_data.get("reply", "")
                
                print(f"\nAI: {reply}")
                
                # 更新对话历史
                conversation_history.append({"role": "user", "content": user_input})
                conversation_history.append({"role": "assistant", "content": reply})
            else:
                print(f"对话失败: {result.get('error', {}).get('message', '未知错误')}")
        else:
            print(f"请求失败: {response.status_code}")

# 使用示例
# multi_turn_chat()
```

### 配置管理API

#### 获取LLM配置

```python
import requests

def get_llm_config():
    """获取LLM配置"""
    response = requests.get("http://localhost:8000/api/v1/llm-config")
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            config = result["data"]
            print("当前LLM配置:")
            print(f"  启用状态: {config.get('enabled', False)}")
            print(f"  API密钥: {'已设置' if config.get('api_key') else '未设置'}")
            print(f"  模型ID: {config.get('model_id', 'N/A')}")
            print(f"  API基础URL: {config.get('api_base_url', 'N/A')}")
            print(f"  温度: {config.get('temperature', 'N/A')}")
            print(f"  最大令牌数: {config.get('max_tokens', 'N/A')}")
            
            return config
        else:
            print(f"获取配置失败: {result.get('error', {}).get('message', '未知错误')}")
            return None
    else:
        print(f"请求失败: {response.status_code}")
        return None

# 使用示例
config = get_llm_config()
```

#### 更新LLM配置

```python
import requests

def update_llm_config(config_data):
    """更新LLM配置"""
    url = "http://localhost:8000/api/v1/llm-config"
    
    response = requests.put(url, json=config_data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print("LLM配置更新成功")
            return True
        else:
            print(f"更新失败: {result.get('error', {}).get('message', '未知错误')}")
            return False
    else:
        print(f"请求失败: {response.status_code}")
        return False

# 使用示例
new_config = {
    "enabled": True,
    "api_key": "your-api-key-here",
    "api_base_url": "http://maas-api.cn-huabei-1.xf-yun.com/v1",
    "model_id": "qwen3-1.7b",
    "temperature": 0.2,
    "max_tokens": 2048
}

success = update_llm_config(new_config)
```

## 错误处理

### 统一错误格式

所有API返回统一的错误格式：

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": "详细错误信息"
  }
}
```

### 常见错误代码

| 错误代码 | HTTP状态码 | 描述 |
|---------|-----------|------|
| `VALIDATION_ERROR` | 400 | 请求参数验证失败 |
| `DOCUMENT_NOT_FOUND` | 404 | 文档不存在 |
| `LLM_CONNECTION_ERROR` | 503 | LLM连接失败 |
| `PROCESSING_ERROR` | 500 | 内部处理错误 |
| `RATE_LIMIT_EXCEEDED` | 429 | 请求频率超限 |

### 错误处理示例

```python
import requests

def handle_api_response(response):
    """处理API响应"""
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            return result.get("data")
        else:
            error = result.get("error", {})
            print(f"API错误: {error.get('code', 'UNKNOWN')} - {error.get('message', '未知错误')}")
            return None
    else:
        print(f"HTTP错误: {response.status_code}")
        try:
            error_data = response.json()
            error = error_data.get("error", {})
            print(f"详细信息: {error.get('message', '无详细信息')}")
        except:
            print("无法解析错误响应")
        return None

# 使用示例
response = requests.get("http://localhost:8000/api/v1/health")
data = handle_api_response(response)
```

## 最佳实践

### 1. 请求重试

```python
import requests
import time

def api_request_with_retry(url, method="GET", data=None, max_retries=3, retry_delay=1):
    """带重试的API请求"""
    for attempt in range(max_retries):
        try:
            if method == "GET":
                response = requests.get(url)
            elif method == "POST":
                response = requests.post(url, json=data)
            elif method == "PUT":
                response = requests.put(url, json=data)
            elif method == "PATCH":
                response = requests.patch(url, json=data)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            # 如果请求成功，返回响应
            if response.status_code == 200:
                return response
            
            # 如果是客户端错误，不重试
            if 400 <= response.status_code < 500:
                return response
            
            # 如果是服务器错误，等待后重试
            print(f"请求失败 (尝试 {attempt + 1}/{max_retries}): {response.status_code}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                
        except requests.exceptions.RequestException as e:
            print(f"请求异常 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    
    return None  # 所有重试都失败

# 使用示例
response = api_request_with_retry("http://localhost:8000/api/v1/health")
```

### 2. 异步请求

```python
import asyncio
import aiohttp
import json

async def async_api_request(session, url, method="GET", data=None):
    """异步API请求"""
    try:
        if method == "GET":
            async with session.get(url) as response:
                return await response.json()
        elif method == "POST":
            async with session.post(url, json=data) as response:
                return await response.json()
        elif method == "PUT":
            async with session.put(url, json=data) as response:
                return await response.json()
        elif method == "PATCH":
            async with session.patch(url, json=data) as response:
                return await response.json()
        else:
            raise ValueError(f"不支持的HTTP方法: {method}")
    except Exception as e:
        print(f"异步请求失败: {str(e)}")
        return None

async def batch_calculate_scores_async(certificates):
    """异步批量计算证书加分"""
    base_url = "http://localhost:8000"
    url = f"{base_url}/api/v1/calculate-score"
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for cert in certificates:
            task = async_api_request(session, url, "POST", cert)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return results

# 使用示例
# certificates = [
#     {"certificate_text": "获得2023年全国大学生数学建模竞赛一等奖"},
#     {"certificate_text": "通过大学英语六级考试，分数550分"}
# ]
# 
# results = asyncio.run(batch_calculate_scores_async(certificates))
```

### 3. 请求缓存

```python
import requests
import hashlib
import json
import time
from functools import wraps

# 简单的内存缓存
_cache = {}

def cache_response(ttl=300):  # 默认缓存5分钟
    """响应缓存装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = hashlib.md5(
                json.dumps([args, kwargs], sort_keys=True).encode()
            ).hexdigest()
            
            # 检查缓存
            if cache_key in _cache:
                cached_data, timestamp = _cache[cache_key]
                if time.time() - timestamp < ttl:
                    print("使用缓存数据")
                    return cached_data
            
            # 调用原始函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            _cache[cache_key] = (result, time.time())
            
            return result
        return wrapper
    return decorator

@cache_response(ttl=600)  # 缓存10分钟
def get_documents_list_cached(skip=0, limit=100):
    """带缓存的获取文档列表"""
    url = "http://localhost:8000/api/v1/documents"
    params = {"skip": skip, "limit": limit}
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            return result["data"]
    
    return None

# 使用示例
# 第一次调用会发送请求
docs1 = get_documents_list_cached()

# 第二次调用会使用缓存
docs2 = get_documents_list_cached()
```

### 4. 请求限流

```python
import time
from functools import wraps

def rate_limit(calls_per_second=1):
    """请求限流装饰器"""
    def decorator(func):
        last_called = [0]  # 使用列表以便在内部函数中修改
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 计算距离上次调用的时间
            elapsed = time.time() - last_called[0]
            min_interval = 1.0 / calls_per_second
            
            if elapsed < min_interval:
                # 等待剩余时间
                time.sleep(min_interval - elapsed)
            
            # 调用原始函数
            result = func(*args, **kwargs)
            
            # 更新最后调用时间
            last_called[0] = time.time()
            
            return result
        return wrapper
    return decorator

@rate_limit(calls_per_second=2)  # 限制每秒最多2次调用
def calculate_certificate_score_limited(certificate_text):
    """带限流的证书加分计算"""
    url = "http://localhost:8000/api/v1/calculate-score"
    data = {"certificate_text": certificate_text}
    
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            return result["data"]
    
    return None

# 使用示例
# 即使快速调用多次，也会被限流
# for i in range(5):
#     score = calculate_certificate_score_limited(f"证书文本 {i}")
#     print(f"结果 {i}: {score}")
```

## 常见问题

### Q: 如何处理大文件上传？

A: 对于大文件上传，建议使用分块上传或流式上传：

```python
import requests

def upload_large_file(file_path, chunk_size=1024*1024):  # 1MB chunks
    """分块上传大文件"""
    url = "http://localhost:8000/api/v1/documents/upload"
    
    with open(file_path, 'rb') as f:
        # 使用流式上传
        files = {'file': (os.path.basename(file_path), f)}
        data = {'description': '大文件上传'}
        
        response = requests.post(url, files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                return result["data"]
        
        return None
```

### Q: 如何处理长时间运行的任务？

A: 使用后台任务API：

```python
import requests
import time

def submit_background_task(task_type, data):
    """提交后台任务"""
    url = f"http://localhost:8000/api/v1/tasks/{task_type}"
    
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            task_id = result["data"]["task_id"]
            print(f"任务已提交，ID: {task_id}")
            return task_id
    
    return None

def check_task_status(task_id):
    """检查任务状态"""
    url = f"http://localhost:8000/api/v1/tasks/{task_id}"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            return result["data"]
    
    return None

def wait_for_task_completion(task_id, poll_interval=5, timeout=300):
    """等待任务完成"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        status = check_task_status(task_id)
        
        if not status:
            print("无法获取任务状态")
            return None
        
        task_status = status.get("status")
        
        if task_status == "completed":
            print("任务完成")
            return status.get("result")
        elif task_status == "failed":
            print(f"任务失败: {status.get('error', '未知错误')}")
            return None
        elif task_status == "running":
            progress = status.get("progress", 0)
            print(f"任务运行中，进度: {progress}%")
        
        time.sleep(poll_interval)
    
    print("任务超时")
    return None

# 使用示例
# task_data = {"certificates": [{"certificate_text": "证书1"}, {"certificate_text": "证书2"}]}
# task_id = submit_background_task("calculate-score-batch", task_data)
# result = wait_for_task_completion(task_id)
```

### Q: 如何优化API性能？

A: 以下是一些性能优化建议：

1. **使用缓存**: 对频繁访问的数据使用缓存
2. **批量操作**: 尽可能使用批量API而不是多次单个API调用
3. **异步请求**: 对于并发请求，使用异步HTTP客户端
4. **压缩数据**: 对于大数据传输，启用压缩
5. **选择合适的数据格式**: 使用JSON而不是XML等更重的格式

```python
# 启用压缩的请求示例
import requests
import json

def compressed_request(url, data):
    """发送压缩的请求"""
    headers = {
        "Content-Type": "application/json",
        "Accept-Encoding": "gzip, deflate",
        "Content-Encoding": "gzip"
    }
    
    # 这里简化了压缩过程，实际应用中需要使用gzip库压缩数据
    json_data = json.dumps(data)
    
    response = requests.post(url, data=json_data, headers=headers)
    return response
```

## 更新日志

### v2.0.0 (2025-01-01)
- 新增LLM配置管理API
- 修复证书加分计算API
- 优化AI对话API
- 添加交互式API文档

### v1.0.0 (2024-01-01)
- 初始版本发布
- 基础文档管理API
- 证书加分计算API
- AI对话API

---

如有其他问题，请参考[完整API文档](./API_DOCUMENTATION.md)或联系开发团队。
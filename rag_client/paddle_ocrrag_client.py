"""
PaddleOCRRAG API 客户端SDK

这个SDK提供了与PaddleOCRRAG API交互的简单接口，包括文档管理、
证书加分计算、AI对话等功能。

使用示例:
    from paddle_ocrrag_client import PaddleOCRRAGClient
    
    client = PaddleOCRRAGClient(base_url="http://localhost:8000")
    
    # 健康检查
    health = client.health.check()
    
    # 上传文档
    doc = client.documents.upload("规则文档.docx", "2025年综测规则")
    
    # 计算证书加分
    score = client.certificates.calculate_score("获得2023年全国大学生数学建模竞赛一等奖")
    
    # AI对话
    reply = client.chat.ask("获得国家级奖学金可以加多少分？")
"""

import json
import time
import requests
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import hashlib


class PaddleOCRRAGClient:
    """PaddleOCRRAG API客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None, timeout: int = 30):
        """
        初始化客户端
        
        Args:
            base_url: API基础URL
            api_key: API密钥（可选）
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        
        # 设置默认请求头
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        
        # 如果提供了API密钥，添加到请求头
        if api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {api_key}"
            })
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                params: Optional[Dict] = None, files: Optional[Dict] = None) -> Dict:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法 (GET, POST, PUT, PATCH, DELETE)
            endpoint: API端点
            data: 请求数据
            params: URL参数
            files: 上传文件
            
        Returns:
            API响应数据
            
        Raises:
            APIError: API请求失败
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params, timeout=self.timeout)
            elif method.upper() == "POST":
                if files:
                    response = self.session.post(url, data=data, files=files, timeout=self.timeout)
                else:
                    response = self.session.post(url, json=data, params=params, timeout=self.timeout)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, params=params, timeout=self.timeout)
            elif method.upper() == "PATCH":
                response = self.session.patch(url, json=data, params=params, timeout=self.timeout)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, params=params, timeout=self.timeout)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            # 解析响应
            try:
                response_data = response.json()
            except ValueError:
                response_data = {"success": False, "error": {"message": f"无法解析响应: {response.text}"}}
            
            # 检查API是否返回成功
            if response.status_code == 200 and response_data.get("success"):
                return response_data.get("data", {})
            else:
                error_msg = "未知错误"
                if response_data.get("error"):
                    error_msg = response_data["error"].get("message", "未知错误")
                elif "detail" in response_data:
                    error_msg = response_data["detail"]
                
                raise APIError(f"API请求失败 ({response.status_code}): {error_msg}")
                
        except requests.exceptions.RequestException as e:
            raise APIError(f"网络请求失败: {str(e)}")
    
    def health_check(self) -> Dict:
        """检查系统健康状态"""
        return self._request("GET", "/api/v1/health")
    
    @property
    def health(self):
        """健康检查API"""
        return HealthAPI(self)
    
    @property
    def documents(self):
        """文档管理API"""
        return DocumentsAPI(self)
    
    @property
    def certificates(self):
        """证书加分计算API"""
        return CertificatesAPI(self)
    
    @property
    def chat(self):
        """AI对话API"""
        return ChatAPI(self)
    
    @property
    def llm_config(self):
        """LLM配置API"""
        return LLMConfigAPI(self)
    
    @property
    def prompts(self):
        """Prompt配置API"""
        return PromptsAPI(self)


class APIError(Exception):
    """API错误异常"""
    pass


class HealthAPI:
    """健康检查API"""
    
    def __init__(self, client: PaddleOCRRAGClient):
        self.client = client
    
    def check(self) -> Dict:
        """检查系统健康状态"""
        return self.client._request("GET", "/api/v1/health")
    
    def test_llm(self) -> Dict:
        """测试LLM连接"""
        return self.client._request("POST", "/api/v1/llm/test")


class DocumentsAPI:
    """文档管理API"""
    
    def __init__(self, client: PaddleOCRRAGClient):
        self.client = client
    
    def upload(self, file_path: str, description: str = "") -> Dict:
        """
        上传单个文档
        
        Args:
            file_path: 文件路径
            description: 文档描述
            
        Returns:
            上传的文档信息
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f)}
            data = {'description': description}
            
            return self.client._request("POST", "/api/v1/documents/upload", data=data, files=files)
    
    def batch_upload(self, file_paths: List[str], descriptions: Optional[List[str]] = None) -> Dict:
        """
        批量上传文档
        
        Args:
            file_paths: 文件路径列表
            descriptions: 文档描述列表（可选）
            
        Returns:
            上传结果
        """
        if descriptions and len(descriptions) != len(file_paths):
            raise ValueError("描述列表长度必须与文件路径列表长度相同")
        
        files = []
        data = {}
        
        for i, file_path in enumerate(file_paths):
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            files.append(('files', (file_path.name, open(file_path, 'rb'))))
            
            if descriptions:
                data[f'description_{i}'] = descriptions[i]
        
        try:
            result = self.client._request("POST", "/api/v1/documents/batch-upload", data=data, files=files)
            return result
        finally:
            # 关闭所有打开的文件
            for _, (_, f) in files:
                f.close()
    
    def list(self, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> Dict:
        """
        获取文档列表
        
        Args:
            skip: 跳过的文档数量
            limit: 返回的最大文档数量
            status: 文档状态过滤 (enabled, disabled)
            
        Returns:
            文档列表和总数
        """
        params = {"skip": skip, "limit": limit}
        if status:
            params["status"] = status
        
        return self.client._request("GET", "/api/v1/documents", params=params)
    
    def get(self, doc_id: str) -> Dict:
        """
        获取文档信息
        
        Args:
            doc_id: 文档ID
            
        Returns:
            文档详细信息
        """
        return self.client._request("GET", f"/api/v1/documents/{doc_id}")
    
    def update_status(self, doc_id: str, status: str) -> Dict:
        """
        更新文档状态
        
        Args:
            doc_id: 文档ID
            status: 新状态 (enabled, disabled)
            
        Returns:
            更新结果
        """
        data = {"status": status}
        return self.client._request("PATCH", f"/api/v1/documents/{doc_id}/status", data=data)
    
    def delete(self, doc_id: str) -> Dict:
        """
        删除文档
        
        Args:
            doc_id: 文档ID
            
        Returns:
            删除结果
        """
        return self.client._request("DELETE", f"/api/v1/documents/{doc_id}")


class CertificatesAPI:
    """证书加分计算API"""
    
    def __init__(self, client: PaddleOCRRAGClient):
        self.client = client
    
    def calculate_score(self, certificate_text: str, student_info: Optional[Dict] = None) -> Dict:
        """
        计算证书加分
        
        Args:
            certificate_text: 证书文本内容
            student_info: 学生信息（可选）
            
        Returns:
            加分计算结果
        """
        data = {"certificate_text": certificate_text}
        if student_info:
            data["student_info"] = student_info
        
        return self.client._request("POST", "/api/v1/calculate-score", data=data)
    
    def batch_calculate(self, certificates: List[Dict]) -> Dict:
        """
        批量计算证书加分
        
        Args:
            certificates: 证书列表，每个元素包含certificate_text和可选的student_info
            
        Returns:
            批量计算结果
        """
        data = {"certificates": certificates}
        return self.client._request("POST", "/api/v1/calculate-score/batch", data=data)
    
    def calculate_score_cached(self, certificate_text: str, student_info: Optional[Dict] = None, 
                             cache_key: Optional[str] = None) -> Dict:
        """
        带缓存的证书加分计算
        
        Args:
            certificate_text: 证书文本内容
            student_info: 学生信息（可选）
            cache_key: 缓存键（可选，如果不提供将自动生成）
            
        Returns:
            加分计算结果
        """
        data = {"certificate_text": certificate_text}
        if student_info:
            data["student_info"] = student_info
        if cache_key:
            data["cache_key"] = cache_key
        
        return self.client._request("POST", "/api/v1/calculate-score/cached", data=data)
    
    def calculate_score_background(self, certificate_text: str, student_info: Optional[Dict] = None) -> Dict:
        """
        后台任务证书加分计算
        
        Args:
            certificate_text: 证书文本内容
            student_info: 学生信息（可选）
            
        Returns:
            任务ID
        """
        data = {"certificate_text": certificate_text}
        if student_info:
            data["student_info"] = student_info
        
        return self.client._request("POST", "/api/v1/calculate-score/background", data=data)


class ChatAPI:
    """AI对话API"""
    
    def __init__(self, client: PaddleOCRRAGClient):
        self.client = client
    
    def ask(self, question: str, use_rag: bool = True, conversation_history: Optional[List[Dict]] = None) -> Dict:
        """
        AI对话
        
        Args:
            question: 问题
            use_rag: 是否使用RAG检索
            conversation_history: 对话历史（可选）
            
        Returns:
            AI回复
        """
        data = {
            "question": question,
            "use_rag": use_rag
        }
        
        if conversation_history:
            data["conversation_history"] = conversation_history
        
        return self.client._request("POST", "/api/v1/chat", data=data)
    
    def ask_cached(self, question: str, use_rag: bool = True, conversation_history: Optional[List[Dict]] = None,
                  cache_key: Optional[str] = None) -> Dict:
        """
        带缓存的AI对话
        
        Args:
            question: 问题
            use_rag: 是否使用RAG检索
            conversation_history: 对话历史（可选）
            cache_key: 缓存键（可选，如果不提供将自动生成）
            
        Returns:
            AI回复
        """
        data = {
            "question": question,
            "use_rag": use_rag
        }
        
        if conversation_history:
            data["conversation_history"] = conversation_history
        if cache_key:
            data["cache_key"] = cache_key
        
        return self.client._request("POST", "/api/v1/chat/cached", data=data)
    
    def ask_background(self, question: str, use_rag: bool = True, conversation_history: Optional[List[Dict]] = None) -> Dict:
        """
        后台任务AI对话
        
        Args:
            question: 问题
            use_rag: 是否使用RAG检索
            conversation_history: 对话历史（可选）
            
        Returns:
            任务ID
        """
        data = {
            "question": question,
            "use_rag": use_rag
        }
        
        if conversation_history:
            data["conversation_history"] = conversation_history
        
        return self.client._request("POST", "/api/v1/chat/background", data=data)


class LLMConfigAPI:
    """LLM配置API"""
    
    def __init__(self, client: PaddleOCRRAGClient):
        self.client = client
    
    def get(self) -> Dict:
        """获取LLM配置"""
        return self.client._request("GET", "/api/v1/llm-config")
    
    def update(self, config: Dict) -> Dict:
        """
        更新LLM配置
        
        Args:
            config: 配置数据
            
        Returns:
            更新结果
        """
        return self.client._request("PUT", "/api/v1/llm-config", data=config)
    
    def reset(self) -> Dict:
        """重置LLM配置为默认值"""
        return self.client._request("POST", "/api/v1/llm-config/reset")
    
    def validate(self) -> Dict:
        """验证LLM配置"""
        return self.client._request("GET", "/api/v1/llm-config/validate")
    
    def test(self) -> Dict:
        """测试LLM连接"""
        return self.client._request("POST", "/api/v1/llm-config/test")


class PromptsAPI:
    """Prompt配置API"""
    
    def __init__(self, client: PaddleOCRRAGClient):
        self.client = client
    
    def get(self) -> Dict:
        """获取Prompt配置"""
        return self.client._request("GET", "/api/v1/prompts")
    
    def update(self, prompts: Dict) -> Dict:
        """
        更新Prompt配置
        
        Args:
            prompts: Prompt配置数据
            
        Returns:
            更新结果
        """
        return self.client._request("PUT", "/api/v1/prompts", data=prompts)
    
    def reset(self) -> Dict:
        """重置Prompt配置为默认值"""
        return self.client._request("POST", "/api/v1/prompts/reset")


# 辅助函数

def generate_cache_key(*args) -> str:
    """
    生成缓存键
    
    Args:
        *args: 用于生成缓存键的参数
        
    Returns:
        缓存键字符串
    """
    cache_string = json.dumps(args, sort_keys=True)
    return hashlib.md5(cache_string.encode()).hexdigest()


# 示例用法

if __name__ == "__main__":
    # 创建客户端
    client = PaddleOCRRAGClient(base_url="http://localhost:8000")
    
    try:
        # 健康检查
        print("健康检查:")
        health = client.health.check()
        print(f"  状态: {health.get('status')}")
        print(f"  版本: {health.get('version')}")
        
        # 上传文档
        print("\n上传文档:")
        doc = client.documents.upload("规则文档.docx", "2025年综测规则")
        print(f"  文档ID: {doc.get('id')}")
        print(f"  文件名: {doc.get('filename')}")
        
        # 计算证书加分
        print("\n计算证书加分:")
        score = client.certificates.calculate_score(
            "张三同学在2023年全国大学生数学建模竞赛中获得一等奖",
            {"年级": "大三", "专业": "计算机科学"}
        )
        print(f"  类别: {score.get('category')}")
        print(f"  加分: {score.get('score')}")
        print(f"  置信度: {score.get('confidence')}")
        
        # AI对话
        print("\nAI对话:")
        reply = client.chat.ask("获得国家级奖学金可以加多少分？")
        print(f"  回复: {reply.get('reply')}")
        
        # 获取LLM配置
        print("\nLLM配置:")
        llm_config = client.llm_config.get()
        print(f"  启用状态: {llm_config.get('enabled')}")
        print(f"  模型ID: {llm_config.get('model_id')}")
        
    except APIError as e:
        print(f"API错误: {str(e)}")
    except Exception as e:
        print(f"错误: {str(e)}")
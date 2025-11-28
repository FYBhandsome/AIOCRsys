from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import json


# ==================== 通用响应模型 ====================

class ApiResponse(BaseModel):
    """统一的API响应模型"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[Any] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# ==================== 证书加分计算相关 ====================

class CertificateRequest(BaseModel):
    """证书信息请求模型"""
    certificate_text: str = Field(..., description="证书文本内容")
    student_info: Optional[Dict[str, Any]] = Field(None, description="学生信息（如年级、专业等）")


class ScoreResponse(BaseModel):
    """加分结果响应模型"""
    category: str = Field(..., description="加分类别")
    score: float = Field(..., description="加分分值")
    rules: str = Field(..., description="匹配的规则条文")
    confidence: float = Field(..., description="匹配置信度 (0-1)")
    explanation: Optional[str] = Field(None, description="加分说明")


# ==================== 对话交流相关 ====================

class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: str = Field(..., description="消息角色: user/assistant")
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    """对话请求模型"""
    message: str = Field(..., description="用户当前的消息")
    chat_history: Optional[List[ChatMessage]] = Field(None, description="对话历史")
    use_rag: bool = Field(True, description="是否使用RAG检索相关规则")
    student_info: Optional[Dict[str, Any]] = Field(None, description="学生信息")


class ChatResponse(BaseModel):
    """对话响应模型"""
    reply: str = Field(..., description="AI回复内容")
    retrieved_rules: Optional[List[str]] = Field(None, description="检索到的相关规则")
    confidence: Optional[float] = Field(None, description="回复置信度")
    context_used: bool = Field(False, description="是否使用了RAG上下文")


class ChatStreamResponse(BaseModel):
    """流式聊天响应模型"""
    type: str = Field(..., description="响应类型: content/end/error")
    content: Optional[str] = Field(None, description="内容片段")
    retrieved_rules: Optional[List[str]] = Field(None, description="检索到的相关规则（仅在type=end时提供）")
    confidence: Optional[float] = Field(None, description="回复置信度（仅在type=end时提供）")
    context_used: Optional[bool] = Field(None, description="是否使用了RAG上下文（仅在type=end时提供）")
    error: Optional[str] = Field(None, description="错误信息（仅在type=error时提供）")
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.dict(), ensure_ascii=False)


# ==================== 文档管理相关 ====================

class DocumentInfo(BaseModel):
    """文档信息模型"""
    id: str = Field(..., description="文档ID")
    original_name: str = Field(..., description="原始文件名")
    file_path: str = Field(..., description="文件存储路径")
    file_size: int = Field(..., description="文件大小（字节）")
    file_type: str = Field(..., description="文件类型")
    description: str = Field("", description="文档描述")
    enabled: bool = Field(True, description="是否启用")
    chunk_count: int = Field(0, description="向量块数量")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")


class DocumentUploadResponse(BaseModel):
    """文档上传响应模型"""
    document_id: str = Field(..., description="文档ID")
    original_name: str = Field(..., description="原始文件名")
    file_size: int = Field(..., description="文件大小")
    chunk_count: int = Field(..., description="向量块数量")
    message: str = Field(..., description="处理消息")


class DocumentStatusUpdate(BaseModel):
    """文档状态更新请求模型"""
    enabled: bool = Field(..., description="是否启用")


class DocumentListResponse(BaseModel):
    """文档列表响应模型"""
    documents: List[DocumentInfo] = Field(..., description="文档列表")
    total: int = Field(..., description="文档总数")
    enabled_count: int = Field(..., description="启用的文档数量")


# ==================== Prompt管理相关 ====================

class PromptConfig(BaseModel):
    """Prompt配置模型"""
    system_prompt: str = Field(..., description="系统提示词（用于计算加分）")
    user_prompt: str = Field(..., description="用户提示词模板")
    chat_system_prompt: str = Field(..., description="聊天系统提示词")
    updated_at: str = Field(..., description="更新时间")
    version: str = Field(..., description="配置版本")


class PromptUpdateRequest(BaseModel):
    """Prompt更新请求模型"""
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    user_prompt: Optional[str] = Field(None, description="用户提示词模板")
    chat_system_prompt: Optional[str] = Field(None, description="聊天系统提示词")


# ==================== 向量库管理相关 ====================

class VectorDBStats(BaseModel):
    """向量数据库统计信息模型"""
    total_documents: int = Field(..., description="文档片段总数")
    enabled_documents: int = Field(..., description="启用的文档数")
    embedding_model: str = Field(..., description="嵌入模型名称")
    llm_engine: str = Field(..., description="LLM引擎")
    status: str = Field(..., description="数据库状态")


class VectorDBResetRequest(BaseModel):
    """重置向量数据库请求模型"""
    confirm: bool = Field(..., description="确认重置操作")
    rebuild: bool = Field(True, description="是否立即重建")


class BatchUploadResult(BaseModel):
    """批量上传结果模型"""
    total: int = Field(..., description="总文件数")
    success: int = Field(..., description="成功数量")
    failed: int = Field(..., description="失败数量")
    results: List[Dict[str, Any]] = Field(..., description="详细结果列表")


# ==================== LLM配置管理相关 ====================

class LLMConfig(BaseModel):
    """LLM配置模型"""
    enabled: bool = Field(..., description="是否启用LLM")
    provider: str = Field(..., description="LLM提供商（如xunfei）")
    api_key: str = Field(..., description="API密钥（脱敏显示）")
    access_key: str = Field("", description="访问密钥（可选，脱敏显示）")
    api_base_url: str = Field(..., description="API基础URL")
    model_id: str = Field(..., description="模型ID")
    temperature: float = Field(..., description="温度参数（0.0-1.0）")
    max_tokens: int = Field(..., description="最大生成token数")
    updated_at: str = Field(..., description="更新时间")
    version: str = Field(..., description="配置版本")


class LLMConfigUpdateRequest(BaseModel):
    """LLM配置更新请求模型"""
    enabled: Optional[bool] = Field(None, description="是否启用LLM")
    provider: Optional[str] = Field(None, description="LLM提供商")
    api_key: Optional[str] = Field(None, description="API密钥")
    access_key: Optional[str] = Field(None, description="访问密钥（可选）")
    api_base_url: Optional[str] = Field(None, description="API基础URL")
    model_id: Optional[str] = Field(None, description="模型ID")
    temperature: Optional[float] = Field(None, ge=0.0, le=1.0, description="温度参数（0.0-1.0）")
    max_tokens: Optional[int] = Field(None, gt=0, description="最大生成token数")


class LLMConfigValidation(BaseModel):
    """LLM配置验证结果模型"""
    valid: bool = Field(..., description="配置是否有效")
    errors: List[str] = Field(..., description="错误列表")
    warnings: List[str] = Field(..., description="警告列表")


class LLMConnectionTest(BaseModel):
    """LLM连接测试结果模型"""
    success: bool = Field(..., description="连接是否成功")
    message: str = Field(..., description="结果消息")
    response: Optional[str] = Field(None, description="测试响应内容")

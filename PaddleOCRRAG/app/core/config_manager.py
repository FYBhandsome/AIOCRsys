"""
统一的配置管理模块
整合了app/config.py、app/llm_config_manager.py和app/prompt_manager.py的配置管理功能
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


# 配置模型
class LLMConfig(BaseModel):
    """LLM配置模型"""
    enabled: bool = True
    provider: str = "xunfei"
    api_key: str = ""
    api_secret: str = ""
    app_id: str = ""
    api_base_url: str = ""
    model_id: str = ""
    temperature: float = 0.7
    max_tokens: int = 2000
    
    @validator('temperature')
    def validate_temperature(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('temperature必须在0.0到1.0之间')
        return v
    
    @validator('max_tokens')
    def validate_max_tokens(cls, v):
        if v <= 0:
            raise ValueError('max_tokens必须大于0')
        return v


class VectorDBConfig(BaseModel):
    """向量数据库配置模型"""
    chroma_db_path: str = "./data/chroma_db"
    rules_docs_path: str = "./data/rules"
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_device: str = "cpu"
    hf_endpoint: str = "https://hf-mirror.com"
    chunk_size: int = 500
    chunk_overlap: int = 50


class RAGConfig(BaseModel):
    """RAG配置模型"""
    top_k: int = 5
    similarity_threshold: float = 0.7
    chain_type: str = "stuff"


class PromptConfig(BaseModel):
    """提示词配置模型"""
    system_prompt: str = ""
    user_prompt: str = ""
    chat_system_prompt: str = ""
    custom_prompts: Dict[str, str] = {}


class AppConfig(BaseModel):
    """应用配置模型"""
    llm: LLMConfig = LLMConfig()
    vector_db: VectorDBConfig = VectorDBConfig()
    rag: RAGConfig = RAGConfig()
    prompt: PromptConfig = PromptConfig()


class ConfigManager:
    """统一的配置管理器"""
    
    _instance = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化配置管理器"""
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.config_dir = Path("./config")
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "app_config.json"
        
        # 加载配置
        self.config = self._load_config()
    
    def _load_config(self) -> AppConfig:
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                return AppConfig(**config_data)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                return AppConfig()
        else:
            # 创建默认配置
            default_config = self._create_default_config()
            self._save_config(default_config)
            return default_config
    
    def _create_default_config(self) -> AppConfig:
        """创建默认配置"""
        api_key = os.getenv("XUNFEI_API_KEY", "")
        api_secret = ""
        if ":" in api_key:
            api_key, api_secret = api_key.split(":", 1)
        
        model_id = os.getenv("XUNFEI_MODEL_ID", "")
        app_id = os.getenv("XUNFEI_APP_ID", model_id)
        
        return AppConfig(
            llm=LLMConfig(
                enabled=os.getenv("USE_XUNFEI_LLM", "false").lower() == "true",
                provider="xunfei",
                api_key=api_key,
                api_secret=api_secret or os.getenv("XUNFEI_API_SECRET", ""),
                app_id=app_id,
                api_base_url=os.getenv("XUNFEI_BASE_URL", "https://maas-api.cn-huabei-1.xf-yun.com/v2"),
                model_id=model_id,
                temperature=float(os.getenv("XUNFEI_TEMPERATURE", "0.1")),
                max_tokens=int(os.getenv("XUNFEI_MAX_TOKENS", "1024"))
            ),
            vector_db=VectorDBConfig(
                chroma_db_path=os.getenv("CHROMA_DB_PATH", "./data/chroma_db"),
                rules_docs_path=os.getenv("RULES_DOCS_PATH", "./data/rules"),
                embedding_model=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
                embedding_device=os.getenv("EMBEDDING_DEVICE", "cpu"),
                hf_endpoint=os.getenv("HF_ENDPOINT", "https://hf-mirror.com"),
                chunk_size=500,
                chunk_overlap=50
            ),
            rag=RAGConfig(
                top_k=int(os.getenv("TOP_K", "2")),
                similarity_threshold=0.7,
                chain_type="stuff"
            ),
            prompt=PromptConfig(
                system_prompt="你是一个专业的证书审核助手，专门帮助用户分析各类证书的加分情况。",
                user_prompt="请帮我分析以下证书的加分情况：",
                chat_system_prompt="你是一个专业的证书审核助手，可以回答用户关于证书审核、加分标准等问题。",
                custom_prompts={}
            )
        )
    
    def _save_config(self, config: AppConfig) -> bool:
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config.dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        return self.config.dict()
    
    def get_llm_config(self) -> Dict[str, Any]:
        """获取LLM配置"""
        return self.config.llm.dict()
    
    def get_vector_db_config(self) -> Dict[str, Any]:
        """获取向量数据库配置"""
        return self.config.vector_db.dict()
    
    def get_rag_config(self) -> Dict[str, Any]:
        """获取RAG配置"""
        return self.config.rag.dict()
    
    def get_prompt_config(self) -> Dict[str, Any]:
        """获取提示词配置"""
        return self.config.prompt.dict()
    
    def update_llm_config(self, **kwargs) -> Dict[str, Any]:
        """更新LLM配置"""
        for key, value in kwargs.items():
            if hasattr(self.config.llm, key):
                setattr(self.config.llm, key, value)
        
        self._save_config(self.config)
        return self.config.llm.dict()
    
    def update_vector_db_config(self, **kwargs) -> Dict[str, Any]:
        """更新向量数据库配置"""
        for key, value in kwargs.items():
            if hasattr(self.config.vector_db, key):
                setattr(self.config.vector_db, key, value)
        
        self._save_config(self.config)
        return self.config.vector_db.dict()
    
    def update_rag_config(self, **kwargs) -> Dict[str, Any]:
        """更新RAG配置"""
        for key, value in kwargs.items():
            if hasattr(self.config.rag, key):
                setattr(self.config.rag, key, value)
        
        self._save_config(self.config)
        return self.config.rag.dict()
    
    def update_prompt_config(self, **kwargs) -> Dict[str, Any]:
        """更新提示词配置"""
        for key, value in kwargs.items():
            if hasattr(self.config.prompt, key):
                setattr(self.config.prompt, key, value)
        
        self._save_config(self.config)
        return self.config.prompt.dict()
    
    def reset_config(self) -> Dict[str, Any]:
        """重置配置为默认值"""
        self.config = self._create_default_config()
        return self.config.dict()
    
    def validate_llm_config(self) -> Dict[str, Any]:
        """验证LLM配置"""
        errors = []
        warnings = []
        
        if not self.config.llm.api_key:
            errors.append("API密钥不能为空")
        
        if not self.config.llm.app_id:
            errors.append("应用ID不能为空")
        
        if not self.config.llm.api_base_url:
            errors.append("API基础URL不能为空")
        
        if not self.config.llm.model_id:
            errors.append("模型ID不能为空")
        
        if self.config.llm.temperature < 0.0 or self.config.llm.temperature > 1.0:
            errors.append("温度参数必须在0.0到1.0之间")
        
        if self.config.llm.max_tokens <= 0:
            errors.append("最大token数必须大于0")
        
        if self.config.llm.provider == "xunfei" and not self.config.llm.api_secret:
            errors.append("讯飞星火大模型需要API密钥")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def test_llm_connection(self) -> Dict[str, Any]:
        """测试LLM连接"""
        try:
            # 使用延迟导入避免循环依赖
            import importlib
            llm_manager_module = importlib.import_module('app.core.llm_manager')
            llm_manager = llm_manager_module.llm_manager
            
            # 获取提供商状态
            status = llm_manager.get_provider_status()
            
            # 如果没有启用的提供商，返回失败
            if not status.get('default'):
                return {
                    "success": False,
                    "message": "没有可用的LLM提供商",
                    "status": status
                }
            
            # 尝试生成测试文本
            test_prompt = "你好，请回复'连接成功'"
            response = llm_manager.generate(test_prompt)
            
            if response and "连接成功" in response:
                return {
                    "success": True,
                    "message": "LLM连接测试成功",
                    "response": response,
                    "status": status
                }
            else:
                return {
                    "success": False,
                    "message": "LLM响应异常",
                    "response": response,
                    "status": status
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"测试LLM连接失败: {str(e)}",
                "status": None
            }
    
    # 便捷属性访问方法（兼容旧的settings方式）
    @property
    def CHROMA_DB_PATH(self) -> str:
        return self.config.vector_db.chroma_db_path
    
    @property
    def RULES_DOCS_PATH(self) -> str:
        return self.config.vector_db.rules_docs_path
    
    @property
    def EMBEDDING_MODEL(self) -> str:
        return self.config.vector_db.embedding_model
    
    @property
    def EMBEDDING_DEVICE(self) -> str:
        return self.config.vector_db.embedding_device
    
    @property
    def HF_ENDPOINT(self) -> str:
        return self.config.vector_db.hf_endpoint
    
    @property
    def TOP_K(self) -> int:
        return self.config.rag.top_k
    
    @property
    def USE_XUNFEI_LLM(self) -> bool:
        return self.config.llm.enabled
    
    @property
    def XUNFEI_API_KEY(self) -> str:
        return self.config.llm.api_key
    
    @property
    def XUNFEI_API_SECRET(self) -> str:
        return self.config.llm.api_secret
    
    @property
    def XUNFEI_APP_ID(self) -> str:
        return self.config.llm.app_id
    
    @property
    def XUNFEI_API_URL(self) -> str:
        return self.config.llm.api_base_url
    
    @property
    def XUNFEI_MODEL_ID(self) -> str:
        return self.config.llm.model_id
    
    @property
    def XUNFEI_TEMPERATURE(self) -> float:
        return self.config.llm.temperature
    
    @property
    def XUNFEI_MAX_TOKENS(self) -> int:
        return self.config.llm.max_tokens


# 创建全局实例
config_manager = ConfigManager()

# 导出settings别名以保持向后兼容
settings = config_manager
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用配置模块
使用 Pydantic Settings 进行配置管理和验证
"""

from pathlib import Path
from typing import List, Set
from pydantic import Field, field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
UNIFIED_LOG_DIR = PROJECT_ROOT / "logs" / "visual_model"


class Settings(BaseSettings):
    """应用配置类 - 使用 Pydantic 进行验证"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # API v1 路径前缀
    API_V1_STR: str = Field(default="/api/v1", description="API v1 路径前缀")
    
    # 基础配置
    PROJECT_NAME: str = Field(default="综测计算助手", description="项目名称")
    PROJECT_VERSION: str = Field(default="1.0.0", description="项目版本")
    PROJECT_DESCRIPTION: str = Field(
        default="综合测评计算助手后端 API 服务",
        description="项目描述"
    )
    DEBUG: bool = Field(default=False, description="调试模式")
    
    # 开发测试配置
    DISABLE_AUTH: bool = Field(default=False, description="禁用认证（仅开发测试）")
    DISABLE_MODEL_SOURCE_CHECK: bool = Field(default=False, description="禁用模型源检查（加速启动）")
    
    # 服务器配置
    HOST: str = Field(default="127.0.0.1", description="服务器主机地址")
    PORT: int = Field(default=8001, ge=1, le=65535, description="服务器端口")
    WORKERS: int = Field(default=1, ge=1, le=32, description="工作进程数")
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        description="允许的主机列表"
    )
    
    # 数据库配置
    DATABASE_URL: str = Field(
        default=f"sqlite:///{BASE_DIR / 'data' / 'database.db'}",
        description="数据库连接URL"
    )
    
    @computed_field
    @property
    def TORTOISE_ORM(self) -> dict:
        """Tortoise ORM 配置"""
        return {
            "connections": {
                "default": self.DATABASE_URL
            },
            "apps": {
                "models": {
                    "models": ["app.models.tortoise_models", "aerich.models"],
                    "default_connection": "default",
                },
            },
        }
    
    # 文件上传配置
    UPLOAD_FOLDER: Path = Field(
        default=BASE_DIR / "uploads",
        description="文件上传目录"
    )
    UPLOAD_DIR: str = Field(
        default=str(BASE_DIR / "uploads"),
        description="文件上传目录路径"
    )
    TEMP_DIR: str = Field(
        default=str(BASE_DIR / "temp"),
        description="临时文件目录路径"
    )
    RESULT_DIR: str = Field(
        default=str(BASE_DIR / "results"),
        description="结果文件目录路径"
    )
    DATABASE_PATH: str = Field(
        default=str(BASE_DIR / "data" / "database.db"),
        description="数据库文件路径"
    )
    MAX_CONTENT_LENGTH: int = Field(
        default=50 * 1024 * 1024,  # 50MB
        description="最大上传文件大小（字节）"
    )
    ALLOWED_EXTENSIONS: Set[str] = Field(
        default={"png", "jpg", "jpeg", "gif", "bmp", "pdf", "docx", "doc"},
        description="允许的文件扩展名"
    )
    
    # 注意：本项目已配置为使用PaddleOCR自动下载的默认模型
    # 模型将自动下载到 C:\Users\[用户名]\.paddlex\official_models\ 目录
    # 如需使用本地模型，请设置以下环境变量：
    # - OCR_DET_MODEL_DIR: 检测模型路径
    # - OCR_REC_MODEL_DIR: 识别模型路径
    # - OCR_CLS_MODEL_DIR: 方向分类器模型路径
    OCR_THRESHOLD: float = Field(
        default=0.15,
        ge=0.0,
        le=1.0,
        description="OCR识别阈值（降低以识别更多文本）"
    )
    OCR_USE_GPU: bool = Field(default=False, description="是否使用GPU加速")
    OCR_USE_ANGLE_CLS: bool = Field(
        default=True,
        description="是否使用方向分类器"
    )
    OCR_LANG: str = Field(default="ch", description="OCR识别语言")
    
    OCR_MAX_IMAGE_SIZE: int = Field(
        default=1600,
        ge=100,
        le=4096,
        description="OCR最大图像尺寸"
    )
    OCR_DET_DB_THRESH: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="检测阈值"
    )
    OCR_DET_DB_BOX_THRESH: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="检测框阈值"
    )
    OCR_REC_BATCH_NUM: int = Field(
        default=4,
        ge=1,
        le=32,
        description="识别批次大小（优化后减少内存占用）"
    )
    
    OCR_ENABLE_MKLDNN: bool = Field(
        default=False,
        description="是否启用MKL-DNN加速（CPU优化）- 注意: 新版PaddleOCR可能不支持此参数"
    )
    
    OCR_CPU_THREADS: int = Field(
        default=4,
        ge=1,
        le=16,
        description="CPU推理线程数"
    )
    
    OCR_DET_LIMIT_SIDE_LEN: int = Field(
        default=960,
        ge=480,
        le=1920,
        description="检测边长限制（减少内存占用）"
    )
    
    OCR_MODEL_POOL_SIZE: int = Field(
        default=1,
        ge=1,
        le=4,
        description="OCR模型池大小"
    )
    
    OCR_RESOURCE_MONITOR_INTERVAL: float = Field(
        default=5.0,
        ge=1.0,
        le=60.0,
        description="资源监控间隔（秒）"
    )
    
    OCR_MEMORY_ALERT_THRESHOLD: float = Field(
        default=80.0,
        ge=50.0,
        le=100.0,
        description="内存使用告警阈值（百分比）"
    )
    
    OCR_CPU_ALERT_THRESHOLD: float = Field(
        default=90.0,
        ge=50.0,
        le=100.0,
        description="CPU使用告警阈值（百分比）"
    )
    
    OCR_THREAD_ALERT_THRESHOLD: int = Field(
        default=50,
        ge=10,
        le=200,
        description="线程数量告警阈值"
    )
    
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:5173",
            "http://localhost:8080"
        ],
        description="允许的跨域来源"
    )
    ALLOWED_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:5173",
            "http://localhost:8080"
        ],
        description="允许的跨域来源"
    )
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        """解析CORS来源（支持逗号分隔的字符串）"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    RATE_LIMIT_CALLS: int = Field(
        default=100,
        ge=1,
        description="限流调用次数"
    )
    RATE_LIMIT_PERIOD: int = Field(
        default=60,
        ge=1,
        description="限流时间窗口（秒）"
    )
    
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式"
    )
    LOG_FILE: Path = Field(
        default=UNIFIED_LOG_DIR / "app.log",
        description="日志文件路径"
    )
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """验证日志级别"""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"日志级别必须是 {allowed} 之一")
        return v_upper
    
    JWT_SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT密钥"
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="JWT算法"
    )
    JWT_EXPIRATION_HOURS: int = Field(
        default=24,
        ge=1,
        le=720,
        description="JWT过期时间（小时）"
    )
    
    RAG_BASE_URL: str = Field(
        default="http://localhost:8000",
        description="RAG系统基础URL"
    )
    RAG_ENABLED: bool = Field(
        default=True,
        description="是否启用RAG系统集成"
    )
    
    SMTP_SERVER: str = Field(
        default="smtp.qq.com",
        description="SMTP服务器地址"
    )
    SMTP_PORT: int = Field(
        default=587,
        ge=1,
        le=65535,
        description="SMTP端口"
    )
    SMTP_USERNAME: str = Field(
        default="",
        description="SMTP用户名（邮箱地址）"
    )
    SMTP_PASSWORD: str = Field(
        default="",
        description="SMTP密码（授权码）"
    )
    FROM_EMAIL: str = Field(
        default="",
        description="发件人邮箱地址"
    )
    EMAIL_ENABLED: bool = Field(
        default=False,
        description="是否启用邮件服务"
    )
    
    FRONTEND_URL: str = Field(
        default="http://localhost:5173",
        description="前端应用URL"
    )
    
    def __init__(self, **kwargs):
        """初始化配置，确保必要的目录存在"""
        super().__init__(**kwargs)
        self.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        self.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        (BASE_DIR / "data").mkdir(parents=True, exist_ok=True)
        Path(self.TEMP_DIR).mkdir(parents=True, exist_ok=True)
        Path(self.RESULT_DIR).mkdir(parents=True, exist_ok=True)

    @property
    def DATABASE_DIR(self) -> str:
        """数据库目录路径"""
        return str(BASE_DIR / "data")

    @property
    def LOGS_DIR(self) -> str:
        """日志目录路径"""
        return str(UNIFIED_LOG_DIR)


TORTOISE_ORM = {
    "connections": {
        "default": f"sqlite:///{BASE_DIR / 'data' / 'database.db'}"
    },
    "apps": {
        "models": {
            "models": ["app.models.tortoise_models", "aerich.models"],
            "default_connection": "default",
        },
    },
}


settings = Settings()

DATABASE_URL = settings.DATABASE_URL

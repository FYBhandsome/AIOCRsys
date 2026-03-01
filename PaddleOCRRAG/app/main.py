"""
RAG系统主入口模块
提供FastAPI应用实例和启动配置
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import traceback
from pathlib import Path
from datetime import datetime
import threading

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared_utils.unified_logger import setup_logging, get_logger

setup_logging(
    service_name="rag",
    log_level="INFO",
    enable_file=True,
    enable_async=True,
    use_subdir=True
)
logger = get_logger(__name__)

_vector_db_ready = False

def log_startup_info():
    """记录启动信息"""
    logger.info("=" * 60)
    logger.info("综测加分规则RAG系统启动中...")
    logger.info(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Python版本: {sys.version}")
    logger.info(f"工作目录: {os.getcwd()}")
    logger.info(f"进程ID: {os.getpid()}")
    logger.info("=" * 60)

def init_vector_db_async():
    """异步初始化向量数据库"""
    global _vector_db_ready
    try:
        logger.info("[后台任务] 开始加载向量数据库...")
        from app.rag.vector_db.vector_db import get_vector_db
        vdb = get_vector_db()
        if vdb is not None:
            doc_count = vdb.count()
            logger.info(f"[后台任务] 向量数据库加载完成，文档数: {doc_count}")
        _vector_db_ready = True
    except Exception as e:
        logger.warning(f"[后台任务] 向量数据库加载失败: {e}")
        logger.warning("[后台任务] 服务将以无向量数据库模式运行")

def init_application():
    """初始化应用程序"""
    try:
        log_startup_info()
        logger.info("[1/3] 开始初始化应用程序...")
        
        logger.info("[2/3] 加载配置...")
        try:
            from app.core.config_manager import config_manager, settings
            logger.info(f"  - 配置文件路径: {config_manager.config_file}")
            logger.info(f"  - LLM启用状态: {settings.USE_XUNFEI_LLM}")
            logger.info(f"  - 向量数据库路径: {settings.CHROMA_DB_PATH}")
            logger.info(f"  - 规则文档路径: {settings.RULES_DOCS_PATH}")
            logger.info("  [OK] 配置加载完成")
        except Exception as e:
            logger.error(f"  [FAIL] 配置加载失败: {e}")
            logger.error(traceback.format_exc())
            raise
        
        logger.info("[3/3] 初始化LLM管理器...")
        try:
            from app.core.llm_manager import LLMManager
            llm_manager = LLMManager()
            providers = llm_manager.list_providers()
            logger.info(f"  - 可用LLM提供商: {providers}")
            if "xunfei" in providers:
                logger.info("  [OK] 讯飞星火大模型已启用")
            else:
                logger.warning("  [WARN] 讯飞星火大模型未启用，请检查配置")
            logger.info("  [OK] LLM管理器初始化完成")
        except Exception as e:
            logger.error(f"  [FAIL] LLM管理器初始化失败: {e}")
            logger.error(traceback.format_exc())
            raise
        
        logger.info("向量数据库将在后台异步加载...")
        db_thread = threading.Thread(target=init_vector_db_async, daemon=True)
        db_thread.start()
        
        logger.info("=" * 60)
        logger.info("应用程序初始化完成，服务已就绪")
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"应用程序初始化失败: {e}")
        logger.error(traceback.format_exc())
        logger.error("=" * 60)
        return False

init_result = init_application()

app = FastAPI(
    title="综测加分规则RAG系统API",
    description="根据证书信息查询综测加分规则，支持文档上传、向量检索、智能问答等功能",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

try:
    from app.core.exceptions import register_exception_handlers
    register_exception_handlers(app)
    logger.info("异常处理器注册完成")
except Exception as e:
    logger.warning(f"异常处理器注册失败: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8001",
        "http://127.0.0.1:8002",
        "http://127.0.0.1:8003",
        "http://127.0.0.1:8004",
        "http://127.0.0.1:8005",
        "http://127.0.0.1:8006",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://127.0.0.1:5177",
        "http://127.0.0.1:5178",
        "http://localhost:8000",
        "http://localhost:8001",
        "http://localhost:8002",
        "http://localhost:8003",
        "http://localhost:8010",
        "http://localhost:8011",
        "http://localhost:8012",
        "http://localhost:8013",
        "http://localhost:8014",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
        "http://localhost:5178",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    logger.info("加载API路由...")
    from app.api.routes import get_api_router
    api_router = get_api_router()
    app.include_router(api_router, prefix="/api/v1")
    logger.info(f"API路由加载完成，路由数量: {len(api_router.routes)}")
except Exception as e:
    logger.error(f"API路由加载失败: {e}")
    logger.error(traceback.format_exc())
    print(f"\n[FATAL] API路由加载失败: {e}", file=sys.stderr)
    print(traceback.format_exc(), file=sys.stderr)
    raise

static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    try:
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
        logger.info(f"静态文件目录挂载完成: {static_dir}")
    except Exception as e:
        logger.warning(f"静态文件目录挂载失败: {e}")

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "综测加分规则RAG系统API服务",
        "docs_url": "/docs",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "RAG系统",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/test")
async def test_page():
    """返回流式聊天测试页面"""
    test_page_path = os.path.join(static_dir, "test_stream_chat.html")
    if os.path.exists(test_page_path):
        return FileResponse(test_page_path)
    return {"error": "测试页面不存在"}

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("=" * 60)
    logger.info("FastAPI应用启动完成")
    logger.info(f"服务地址: http://127.0.0.1:8000")
    logger.info(f"API文档: http://127.0.0.1:8000/docs")
    logger.info("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("=" * 60)
    logger.info("FastAPI应用正在关闭...")
    logger.info("=" * 60)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )

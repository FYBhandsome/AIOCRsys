from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.routes import get_api_router, init_optimized_components
from fastapi.middleware.cors import CORSMiddleware
import os
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_application():
    """初始化应用程序"""
    try:
        logger.info("正在初始化应用程序...")
        
        # 初始化优化组件
        logger.info("正在初始化优化组件...")
        if init_optimized_components():
            logger.info("优化组件初始化完成")
        else:
            logger.warning("优化组件初始化失败，但应用程序将继续运行")
            
        logger.info("应用程序初始化完成")
        return True
    except Exception as e:
        logger.error(f"应用程序初始化失败: {str(e)}")
        return False

# 初始化应用程序
init_application()

app = FastAPI(
    title="综测加分规则RAG系统API",
    description="根据证书信息查询综测加分规则的API服务",
    version="1.0.0"
)


origins = [
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8001",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:8002",
    "http://127.0.0.1:8003",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 获取并注册路由
api_router = get_api_router()
app.include_router(api_router, prefix="/api/v1")

# 挂载静态文件目录
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    return {
        "message": "综测加分规则RAG系统API服务",
        "docs_url": "/docs",
        "version": "1.0.0"
    }

@app.get("/test")
async def test_page():
    """返回流式聊天测试页面"""
    test_page_path = os.path.join(static_dir, "test_stream_chat.html")
    if os.path.exists(test_page_path):
        return FileResponse(test_page_path)
    return {"error": "测试页面不存在"}


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综测计算助手 - 主应用入口
"""

import uvicorn

from app.core.app_factory import create_app
from config import settings


# 创建 FastAPI 应用实例
app = create_app()


if __name__ == "__main__":
    """启动应用服务器"""
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower()
    )
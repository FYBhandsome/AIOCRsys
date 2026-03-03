#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综测计算助手 - 主应用入口
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

if os.environ.get('DISABLE_MODEL_SOURCE_CHECK', '').lower() not in ('true', '1'):
    os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'

from shared_utils.unified_logger import setup_logging, get_logger

setup_logging(
    service_name="visual_model",
    log_level="INFO",
    enable_file=True,
    enable_async=True,
    use_subdir=True
)

import uvicorn

from app.core.app_factory import create_app
from config import settings

logger = get_logger(__name__)
logger.info("Visual Model 服务启动中...")

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
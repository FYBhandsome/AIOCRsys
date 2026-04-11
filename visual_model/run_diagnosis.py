#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.logger import setup_logging, get_logger

# 设置日志
setup_logging(
    service_name="db_diagnosis",
    log_level="INFO",
    enable_file=False,
    enable_async=False
)

logger = get_logger(__name__)

from diagnose_and_fix_db import diagnose_database

if __name__ == "__main__":
    exit_code = asyncio.run(diagnose_database())
    sys.exit(exit_code)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
前端日志接收API
用于接收和存储前端应用发送的日志
"""
from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import json
import threading
import sys

try:
    from shared_utils.unified_logger import get_logger, PROJECT_ROOT
except ImportError:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
    sys.path.insert(0, str(PROJECT_ROOT))
    from shared_utils.unified_logger import get_logger, PROJECT_ROOT

FRONTEND_LOG_DIR = PROJECT_ROOT / "logs" / "frontend"

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/logs", tags=["日志"])

_log_lock = threading.Lock()


class FrontendLogEntry(BaseModel):
    """前端日志条目"""
    timestamp: str
    level: str
    service: str
    message: str
    data: Optional[Dict[str, Any]] = None
    userId: Optional[str] = None
    sessionId: Optional[str] = None
    requestId: Optional[str] = None
    url: Optional[str] = None
    userAgent: Optional[str] = None


class FrontendLogsRequest(BaseModel):
    """前端日志请求"""
    logs: List[FrontendLogEntry]


def write_frontend_logs(logs: List[FrontendLogEntry]):
    """写入前端日志到文件"""
    try:
        FRONTEND_LOG_DIR.mkdir(parents=True, exist_ok=True)
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = FRONTEND_LOG_DIR / f"frontend_{today}.log"
        
        with _log_lock:
            with open(log_file, 'a', encoding='utf-8') as f:
                for log in logs:
                    log_dict = log.model_dump()
                    log_dict['received_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    f.write(json.dumps(log_dict, ensure_ascii=False) + '\n')
        
        logger.debug(f"写入 {len(logs)} 条前端日志")
    except Exception as e:
        logger.error(f"写入前端日志失败: {e}")


@router.post("")
async def receive_logs(request: Request, logs_data: FrontendLogsRequest):
    """
    接收前端日志
    
    将前端应用发送的日志写入统一的日志文件
    """
    try:
        logs = logs_data.logs
        
        if not logs:
            return {"status": "ok", "count": 0}
        
        for log in logs:
            level = log.level.upper()
            msg = f"[前端] {log.message}"
            
            if log.userId:
                msg = f"[用户:{log.userId}] {msg}"
            
            extra_data = {
                'source': 'frontend',
                'sessionId': log.sessionId,
                'url': log.url,
                'userAgent': log.userAgent,
                'data': log.data
            }
            
            if level == 'DEBUG':
                logger.debug(msg, extra=extra_data)
            elif level == 'INFO':
                logger.info(msg, extra=extra_data)
            elif level == 'WARN':
                logger.warning(msg, extra=extra_data)
            elif level in ('ERROR', 'FATAL'):
                logger.error(msg, extra=extra_data)
        
        write_frontend_logs(logs)
        
        return {"status": "ok", "count": len(logs)}
        
    except Exception as e:
        logger.error(f"处理前端日志失败: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/health")
async def logs_health():
    """日志服务健康检查"""
    return {
        "status": "healthy",
        "log_dir": str(FRONTEND_LOG_DIR),
        "timestamp": datetime.now().isoformat()
    }

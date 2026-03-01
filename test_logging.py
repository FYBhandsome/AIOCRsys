#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志系统测试脚本
验证所有服务的日志是否正确输出到统一目录
"""
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

def test_visual_model_logger():
    """测试 Visual Model 日志"""
    print("\n[测试] Visual Model 日志配置...")
    
    from visual_model.config import UNIFIED_LOG_DIR
    print(f"  日志目录: {UNIFIED_LOG_DIR}")
    
    from visual_model.app.core.enhanced_logger import get_logger, setup_logger
    
    logger = get_logger("test_visual_model")
    logger.info("Visual Model 日志测试 - INFO 级别")
    logger.warning("Visual Model 日志测试 - WARNING 级别")
    logger.error("Visual Model 日志测试 - ERROR 级别")
    
    print(f"  ✓ Visual Model 日志测试完成")
    return UNIFIED_LOG_DIR

def test_rag_logger():
    """测试 RAG 服务日志"""
    print("\n[测试] RAG 服务日志配置...")
    
    sys.path.insert(0, str(PROJECT_ROOT / "PaddleOCRRAG"))
    from app.core.logger import UNIFIED_LOG_DIR, get_logger, setup_logging
    
    print(f"  日志目录: {UNIFIED_LOG_DIR}")
    
    setup_logging(log_level="DEBUG")
    logger = get_logger("test_rag")
    
    logger.info("RAG 服务日志测试 - INFO 级别")
    logger.warning("RAG 服务日志测试 - WARNING 级别")
    logger.error("RAG 服务日志测试 - ERROR 级别")
    
    print(f"  ✓ RAG 服务日志测试完成")
    return UNIFIED_LOG_DIR

def test_unified_logger():
    """测试统一日志模块"""
    print("\n[测试] 统一日志模块...")
    
    from shared_utils.unified_logger import setup_logging, get_logger, PROJECT_ROOT as UTIL_PROJECT_ROOT
    
    print(f"  项目根目录: {UTIL_PROJECT_ROOT}")
    
    setup_logging(
        service_name="test_unified",
        log_level="DEBUG",
        enable_file=True,
        enable_async=False
    )
    
    logger = get_logger("test_unified")
    logger.info("统一日志模块测试 - INFO 级别")
    logger.warning("统一日志模块测试 - WARNING 级别")
    logger.error("统一日志模块测试 - ERROR 级别")
    
    print(f"  ✓ 统一日志模块测试完成")

def verify_log_structure():
    """验证日志目录结构"""
    print("\n[验证] 日志目录结构...")
    
    logs_dir = PROJECT_ROOT / "logs"
    
    expected_dirs = ["visual_model", "rag", "frontend"]
    
    for dir_name in expected_dirs:
        dir_path = logs_dir / dir_name
        if dir_path.exists():
            print(f"  ✓ {dir_name}/ 目录存在")
        else:
            print(f"  ✗ {dir_name}/ 目录不存在")
    
    print("\n[验证] 日志文件列表:")
    for log_file in logs_dir.rglob("*.log"):
        size = log_file.stat().st_size
        mtime = datetime.fromtimestamp(log_file.stat().st_mtime).strftime("%H:%M:%S")
        print(f"  - {log_file.relative_to(logs_dir)} ({size} bytes, {mtime})")

def main():
    """主测试函数"""
    print("=" * 60)
    print("日志系统测试")
    print("=" * 60)
    
    try:
        test_visual_model_logger()
    except Exception as e:
        print(f"  ✗ Visual Model 日志测试失败: {e}")
    
    try:
        test_rag_logger()
    except Exception as e:
        print(f"  ✗ RAG 服务日志测试失败: {e}")
    
    try:
        test_unified_logger()
    except Exception as e:
        print(f"  ✗ 统一日志模块测试失败: {e}")
    
    verify_log_structure()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()

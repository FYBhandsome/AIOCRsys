#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公共测试工具模块
提供测试脚本共用的工具函数和类
"""

import os
import sys
import json
import time
import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple


def print_separator(title: str = ""):
    """打印分隔线
    
    Args:
        title: 标题文本
    """
    print("\n" + "=" * 80)
    if title:
        print(f"  {title}")
        print("=" * 80)


def print_sub_separator(title: str = ""):
    """打印子分隔线
    
    Args:
        title: 标题文本
    """
    print("\n" + "-" * 60)
    if title:
        print(f"  {title}")
        print("-" * 60)


def format_size(size_bytes: int) -> str:
    """格式化文件大小
    
    Args:
        size_bytes: 字节数
        
    Returns:
        格式化后的大小字符串
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def get_file_hash(file_path: Path) -> str:
    """计算文件MD5哈希
    
    Args:
        file_path: 文件路径
        
    Returns:
        MD5哈希值（前16位）
    """
    try:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()[:16]
    except Exception:
        return "N/A"


def format_datetime(timestamp: float) -> str:
    """格式化时间戳
    
    Args:
        timestamp: Unix时间戳
        
    Returns:
        格式化后的时间字符串
    """
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


def get_directory_stats(directory: Path) -> Dict[str, Any]:
    """获取目录统计信息
    
    Args:
        directory: 目录路径
        
    Returns:
        统计信息字典
    """
    if not directory.exists():
        return {
            "exists": False,
            "file_count": 0,
            "total_size": 0,
            "files": []
        }
    
    total_size = 0
    file_count = 0
    files = []
    
    for item in directory.rglob('*'):
        if item.is_file():
            file_count += 1
            size = item.stat().st_size
            total_size += size
            files.append({
                "path": str(item.relative_to(directory)),
                "size": size,
                "size_formatted": format_size(size),
                "modified": format_datetime(item.stat().st_mtime)
            })
    
    return {
        "exists": True,
        "file_count": file_count,
        "total_size": total_size,
        "total_size_formatted": format_size(total_size),
        "files": files
    }


def save_test_report(report: Dict[str, Any], output_path: Path) -> None:
    """保存测试报告
    
    Args:
        report: 测试报告数据
        output_path: 输出文件路径
    """
    report["generated_at"] = datetime.now().isoformat()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n测试报告已保存: {output_path}")


class TestLogger:
    """测试日志记录器"""
    
    def __init__(self, name: str):
        self.name = name
        self.results = []
        self.start_time = time.time()
    
    def log(self, test_name: str, success: bool, message: str = "", duration: float = 0):
        """记录测试结果
        
        Args:
            test_name: 测试名称
            success: 是否成功
            message: 消息
            duration: 耗时（秒）
        """
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "duration_ms": round(duration * 1000, 2),
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        
        status = "✓" if success else "✗"
        print(f"  {status} {test_name}: {message}")
    
    def summary(self) -> Dict[str, Any]:
        """生成测试摘要
        
        Returns:
            摘要信息字典
        """
        total = len(self.results)
        passed = sum(1 for r in self.results if r["success"])
        failed = total - passed
        duration = time.time() - self.start_time
        
        return {
            "name": self.name,
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": f"{passed/total*100:.1f}%" if total > 0 else "0%",
            "duration_seconds": round(duration, 2),
            "results": self.results
        }


class ChromaDBHelper:
    """ChromaDB数据库助手类"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.sqlite_path = self.db_path / "chroma.sqlite3"
    
    def get_connection(self) -> Optional[sqlite3.Connection]:
        """获取数据库连接
        
        Returns:
            SQLite连接对象
        """
        if not self.sqlite_path.exists():
            return None
        
        return sqlite3.connect(str(self.sqlite_path))
    
    def get_collections(self) -> List[Tuple[str, str]]:
        """获取所有集合
        
        Returns:
            集合列表 [(id, name), ...]
        """
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM collections;")
            return cursor.fetchall()
        finally:
            conn.close()
    
    def get_document_count(self, collection_name: str = None) -> int:
        """获取文档数量
        
        Args:
            collection_name: 集合名称（可选）
            
        Returns:
            文档数量
        """
        conn = self.get_connection()
        if not conn:
            return 0
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM embedding_fulltext_search;")
            return cursor.fetchone()[0]
        except Exception:
            return 0
        finally:
            conn.close()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            "db_path": str(self.db_path),
            "exists": self.db_path.exists(),
            "sqlite_exists": self.sqlite_path.exists(),
            "collections": [],
            "total_documents": 0,
            "db_size_bytes": 0,
            "db_size_formatted": "0 B"
        }
        
        if self.sqlite_path.exists():
            stats["db_size_bytes"] = self.sqlite_path.stat().st_size
            stats["db_size_formatted"] = format_size(stats["db_size_bytes"])
            stats["collections"] = self.get_collections()
            stats["total_documents"] = self.get_document_count()
        
        return stats
    
    def clear_all_data(self) -> bool:
        """清空所有向量数据
        
        Returns:
            是否成功
        """
        import shutil
        
        try:
            if self.db_path.exists():
                for item in self.db_path.iterdir():
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                return True
            return False
        except Exception as e:
            print(f"清空数据失败: {e}")
            return False

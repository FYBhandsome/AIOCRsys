#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档向量化处理脚本
将综测规则文档转换为向量并存储到向量数据库
"""
import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.rag.vector_db import get_vector_db
from app.core.logger import get_logger

logger = get_logger(__name__)


class DocumentVectorizer:
    """文档向量化处理器"""
    
    def __init__(self, collection_name: str = "zongce_rules"):
        """初始化向量化处理器
        
        Args:
            collection_name: 向量数据库集合名称
        """
        self.collection_name = collection_name
        self.vector_db = get_vector_db(collection_name)
        from app.rag import get_enhanced_rule_loader
        EnhancedRuleLoader, _ = get_enhanced_rule_loader()
        self.loader = EnhancedRuleLoader()
        self.stats = {
            "total_files": 0,
            "processed_files": 0,
            "total_chunks": 0,
            "failed_files": 0,
            "errors": []
        }
    
    def process_directory(
        self,
        directory: str,
        file_extensions: List[str] = None,
        clear_existing: bool = False,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """处理目录中的所有文档
        
        Args:
            directory: 文档目录路径
            file_extensions: 要处理的文件扩展名列表
            clear_existing: 是否清空现有数据
            batch_size: 批处理大小
            
        Returns:
            处理统计信息
        """
        start_time = time.time()
        logger.info(f"开始处理目录: {directory}")
        
        if clear_existing:
            logger.info("清空现有向量数据...")
            self.vector_db.clear_all_documents()
        
        directory_path = Path(directory)
        if not directory_path.exists():
            logger.error(f"目录不存在: {directory}")
            return {"error": f"目录不存在: {directory}"}
        
        try:
            logger.info("加载并处理所有文档...")
            self.loader.load_all_documents(str(directory_path))
            
            chunks = self.loader.get_chunks_as_dicts()
            loader_stats = self.loader.get_stats()
            
            self.stats["total_files"] = loader_stats.get("total_files", 0)
            self.stats["processed_files"] = loader_stats.get("processed_files", 0)
            self.stats["total_chunks"] = len(chunks)
            
            if chunks:
                logger.info(f"开始批量添加 {len(chunks)} 个文档块到向量数据库...")
                self._add_documents_in_batches(chunks, batch_size)
            
            logger.info(f"文档处理统计: {loader_stats}")
            
        except Exception as e:
            self.stats["failed_files"] = self.stats.get("total_files", 0)
            error_msg = f"处理目录失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.stats["errors"].append(error_msg)
        
        duration = time.time() - start_time
        self.stats["duration_seconds"] = round(duration, 2)
        
        logger.info(f"文档向量化处理完成: {json.dumps(self.stats, ensure_ascii=False, indent=2)}")
        
        return self.stats
    
    def _process_single_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """处理单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            文档块列表
        """
        try:
            self.loader.load_all_documents(str(file_path.parent))
            chunks = self.loader.get_chunks_as_dicts()
            return chunks
        except Exception as e:
            logger.error(f"加载文件失败 {file_path}: {e}", exc_info=True)
            raise
    
    def _add_documents_in_batches(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int
    ):
        """批量添加文档到向量数据库
        
        Args:
            documents: 文档列表
            batch_size: 批处理大小
        """
        total = len(documents)
        for i in range(0, total, batch_size):
            batch = documents[i:i + batch_size]
            logger.info(f"添加批次 {i//batch_size + 1}/{(total + batch_size - 1)//batch_size}: {len(batch)} 个文档")
            
            try:
                self.vector_db.add_documents(batch)
            except Exception as e:
                logger.error(f"添加批次失败: {e}", exc_info=True)
                self.stats["errors"].append(f"批次 {i//batch_size + 1} 添加失败: {str(e)}")
    
    def process_single_document(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """处理单个文档
        
        Args:
            file_path: 文件路径
            metadata: 额外的元数据
            
        Returns:
            处理结果
        """
        logger.info(f"处理单个文档: {file_path}")
        
        try:
            documents = self.loader.load(file_path)
            
            if metadata:
                for doc in documents:
                    if "metadata" in doc:
                        doc["metadata"].update(metadata)
                    else:
                        doc["metadata"] = metadata
            
            if documents:
                self.vector_db.add_documents(documents)
                logger.info(f"文档处理完成: {len(documents)} 个文档块")
                return {
                    "success": True,
                    "file_path": file_path,
                    "chunk_count": len(documents)
                }
            else:
                return {
                    "success": False,
                    "file_path": file_path,
                    "error": "未生成任何文档块"
                }
                
        except Exception as e:
            logger.error(f"处理文档失败: {e}", exc_info=True)
            return {
                "success": False,
                "file_path": file_path,
                "error": str(e)
            }
    
    def verify_vectorization(self) -> Dict[str, Any]:
        """验证向量化结果
        
        Returns:
            验证结果
        """
        logger.info("开始验证向量化结果...")
        
        try:
            stats = self.vector_db.get_category_stats()
            
            test_queries = [
                "省级竞赛一等奖加多少分",
                "英语四级可以加多少分",
                "社会实践要求多少学时",
                "综测成绩如何计算"
            ]
            
            test_results = []
            for query in test_queries:
                results = self.vector_db.search_relevant(query, top_k=3)
                test_results.append({
                    "query": query,
                    "result_count": len(results.get("documents", [[]])[0]) if results else 0
                })
            
            verification = {
                "success": True,
                "database_stats": stats,
                "test_queries": test_results,
                "verified_at": datetime.now().isoformat()
            }
            
            logger.info(f"验证完成: {json.dumps(verification, ensure_ascii=False, indent=2)}")
            return verification
            
        except Exception as e:
            logger.error(f"验证失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_database_info(self) -> Dict[str, Any]:
        """获取数据库信息
        
        Returns:
            数据库信息
        """
        try:
            stats = self.vector_db.get_category_stats()
            return {
                "collection_name": self.collection_name,
                "total_documents": stats.get("total", 0),
                "by_type": stats.get("by_type", {}),
                "by_category": stats.get("by_main_category", {}),
                "by_sub_category": stats.get("by_sub_category", {})
            }
        except Exception as e:
            return {"error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="文档向量化处理工具")
    parser.add_argument(
        "--directory", "-d",
        default=str(PROJECT_ROOT / "data" / "rules"),
        help="要处理的文档目录"
    )
    parser.add_argument(
        "--file", "-f",
        help="处理单个文件"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="处理前清空现有数据"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="处理后验证结果"
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="显示数据库信息"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="批处理大小"
    )
    parser.add_argument(
        "--extensions",
        nargs="+",
        default=[".docx", ".doc", ".pdf", ".txt", ".xlsx", ".xls"],
        help="要处理的文件扩展名"
    )
    
    args = parser.parse_args()
    
    vectorizer = DocumentVectorizer()
    
    if args.info:
        info = vectorizer.get_database_info()
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return
    
    if args.file:
        result = vectorizer.process_single_document(args.file)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    if not os.path.exists(args.directory):
        print(f"错误: 目录不存在 - {args.directory}")
        sys.exit(1)
    
    stats = vectorizer.process_directory(
        directory=args.directory,
        file_extensions=args.extensions,
        clear_existing=args.clear,
        batch_size=args.batch_size
    )
    
    print("\n处理统计:")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    
    if args.verify:
        print("\n验证结果:")
        verification = vectorizer.verify_vectorization()
        print(json.dumps(verification, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

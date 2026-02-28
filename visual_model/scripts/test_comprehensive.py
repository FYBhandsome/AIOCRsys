#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面测试脚本 - PaddleOCR和RAG功能测试
包含详细的日志输出、模型信息、向量知识库信息
"""

import os
import sys
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def print_separator(title: str = ""):
    """打印分隔线"""
    print("\n" + "=" * 80)
    if title:
        print(f"  {title}")
        print("=" * 80)


def print_sub_separator(title: str = ""):
    """打印子分隔线"""
    print("\n" + "-" * 60)
    if title:
        print(f"  {title}")
        print("-" * 60)


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def get_file_hash(file_path: Path) -> str:
    """计算文件MD5哈希"""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()[:16]
    except:
        return "N/A"


def test_paddleocr_models_detailed():
    """测试PaddleOCR模型信息 - 详细版本"""
    print_separator("PaddleOCR 模型详细信息测试")
    
    paddleocr_model_dir = Path.home() / ".paddlex" / "official_models"
    
    print(f"\n【模型存放位置】")
    print(f"  完整路径: {paddleocr_model_dir}")
    print(f"  用户目录: {Path.home()}")
    
    if paddleocr_model_dir.exists():
        print(f"\n【模型目录状态】: 存在 ✓")
        
        print_sub_separator("已下载模型详细列表")
        
        total_size = 0
        model_count = 0
        models_info = []
        
        for model_dir in sorted(paddleocr_model_dir.iterdir()):
            if model_dir.is_dir():
                model_count += 1
                
                model_files = list(model_dir.rglob('*'))
                model_files = [f for f in model_files if f.is_file()]
                model_size = sum(f.stat().st_size for f in model_files)
                total_size += model_size
                
                mod_time = datetime.fromtimestamp(model_dir.stat().st_mtime)
                create_time = datetime.fromtimestamp(model_dir.stat().st_ctime)
                
                model_info = {
                    "name": model_dir.name,
                    "path": str(model_dir),
                    "size_bytes": model_size,
                    "size_formatted": format_size(model_size),
                    "file_count": len(model_files),
                    "modified_time": mod_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "created_time": create_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "files": []
                }
                
                print(f"\n模型 #{model_count}: {model_dir.name}")
                print(f"  ├─ 路径: {model_dir}")
                print(f"  ├─ 大小: {format_size(model_size)}")
                print(f"  ├─ 文件数: {len(model_files)}")
                print(f"  ├─ 创建时间: {create_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"  └─ 修改时间: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                if model_files:
                    print(f"\n  文件列表:")
                    for i, f in enumerate(sorted(model_files)[:10]):
                        file_size = f.stat().st_size
                        file_hash = get_file_hash(f) if file_size < 10 * 1024 * 1024 else "N/A"
                        rel_path = f.relative_to(model_dir)
                        print(f"    [{i+1}] {rel_path}")
                        print(f"        大小: {format_size(file_size)}, MD5: {file_hash}")
                        model_info["files"].append({
                            "name": str(rel_path),
                            "size": format_size(file_size)
                        })
                    if len(model_files) > 10:
                        print(f"    ... 共 {len(model_files)} 个文件")
                
                models_info.append(model_info)
        
        print_sub_separator("模型统计汇总")
        print(f"\n  模型总数: {model_count}")
        print(f"  总占用空间: {format_size(total_size)}")
        print(f"  平均模型大小: {format_size(total_size // model_count) if model_count > 0 else 'N/A'}")
        
        result = {
            "success": True,
            "model_directory": str(paddleocr_model_dir),
            "model_count": model_count,
            "total_size_bytes": total_size,
            "total_size_formatted": format_size(total_size),
            "models": models_info
        }
        
    else:
        print(f"\n【模型目录状态】: 不存在")
        print(f"  模型将在首次使用时自动下载到该目录")
        print(f"  下载源: PaddlePaddle官方模型仓库")
        
        result = {
            "success": True,
            "model_directory": str(paddleocr_model_dir),
            "model_count": 0,
            "total_size_bytes": 0,
            "models": [],
            "note": "模型将在首次使用时自动下载"
        }
    
    return result


def test_ocr_service_detailed():
    """测试OCR服务功能 - 详细版本"""
    print_separator("OCR 服务功能详细测试")
    
    try:
        from app.services.ocr_service import get_ocr_service, OCRService
        from config import settings
        
        print("\n【OCR 配置信息】")
        print(f"  ├─ 使用GPU: {settings.OCR_USE_GPU}")
        print(f"  ├─ 识别语言: {settings.OCR_LANG}")
        print(f"  ├─ 置信度阈值: {settings.OCR_THRESHOLD}")
        print(f"  ├─ 使用方向分类器: {settings.OCR_USE_ANGLE_CLS}")
        print(f"  ├─ 最大图像尺寸: {settings.OCR_MAX_IMAGE_SIZE}")
        print(f"  ├─ 检测阈值: {settings.OCR_DET_DB_THRESH}")
        print(f"  ├─ 检测框阈值: {settings.OCR_DET_DB_BOX_THRESH}")
        print(f"  └─ 识别批次大小: {settings.OCR_REC_BATCH_NUM}")
        
        print_sub_separator("初始化OCR服务")
        print("\n正在初始化OCR服务...")
        start_time = time.time()
        
        ocr_service = get_ocr_service()
        
        init_duration = time.time() - start_time
        print(f"OCR服务实例创建完成 (耗时: {init_duration:.2f}秒)")
        
        print_sub_separator("预热OCR引擎")
        print("\n正在预热OCR引擎（加载模型）...")
        warm_start = time.time()
        
        ocr_service.warm_up()
        
        warm_duration = time.time() - warm_start
        print(f"OCR引擎预热完成 (耗时: {warm_duration:.2f}秒)")
        
        print_sub_separator("OCR服务状态")
        print(f"\n  ├─ 服务状态: 已初始化 ✓")
        print(f"  ├─ OCR引擎: {type(ocr_service.ocr).__name__ if ocr_service.ocr else '未加载'}")
        print(f"  ├─ 使用GPU: {ocr_service.use_gpu}")
        print(f"  └─ 语言: {ocr_service.lang}")
        
        return {
            "success": True,
            "config": {
                "use_gpu": settings.OCR_USE_GPU,
                "lang": settings.OCR_LANG,
                "threshold": settings.OCR_THRESHOLD,
                "use_angle_cls": settings.OCR_USE_ANGLE_CLS,
                "max_image_size": settings.OCR_MAX_IMAGE_SIZE
            },
            "init_duration_seconds": round(init_duration, 2),
            "warm_up_duration_seconds": round(warm_duration, 2)
        }
        
    except ImportError as e:
        print(f"\n✗ PaddleOCR导入失败: {e}")
        print("  请确保已安装PaddleOCR: pip install paddleocr")
        return {"success": False, "error": f"导入失败: {e}"}
    except Exception as e:
        print(f"\n✗ OCR服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def test_rag_vector_db_detailed():
    """测试RAG向量知识库 - 详细版本"""
    print_separator("RAG 向量知识库详细测试")
    
    try:
        rag_project_root = project_root.parent / "PaddleOCRRAG"
        vector_db_path = rag_project_root / "data" / "chroma_db"
        
        print(f"\n【向量数据库位置】")
        print(f"  ├─ 项目根目录: {rag_project_root}")
        print(f"  └─ 数据库路径: {vector_db_path}")
        
        if vector_db_path.exists():
            print(f"\n【数据库目录状态】: 存在 ✓")
            
            print_sub_separator("向量数据库文件详情")
            
            total_size = 0
            file_count = 0
            db_files = []
            
            for item in sorted(vector_db_path.rglob('*')):
                if item.is_file():
                    file_count += 1
                    size = item.stat().st_size
                    total_size += size
                    mod_time = datetime.fromtimestamp(item.stat().st_mtime)
                    rel_path = item.relative_to(vector_db_path)
                    
                    file_info = {
                        "path": str(rel_path),
                        "size_bytes": size,
                        "size_formatted": format_size(size),
                        "modified": mod_time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    db_files.append(file_info)
                    
                    print(f"\n  文件: {rel_path}")
                    print(f"    ├─ 大小: {format_size(size)}")
                    print(f"    └─ 修改时间: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            print_sub_separator("向量数据库统计")
            print(f"\n  ├─ 文件总数: {file_count}")
            print(f"  ├─ 总大小: {format_size(total_size)}")
            print(f"  └─ 数据库类型: ChromaDB (持久化)")
            
            result = {
                "success": True,
                "db_path": str(vector_db_path),
                "exists": True,
                "file_count": file_count,
                "total_size_bytes": total_size,
                "total_size_formatted": format_size(total_size),
                "files": db_files
            }
        else:
            print(f"\n【数据库目录状态】: 不存在")
            print("  需要先运行向量化脚本创建向量数据库")
            
            result = {
                "success": True,
                "db_path": str(vector_db_path),
                "exists": False,
                "file_count": 0,
                "total_size_bytes": 0,
                "note": "需要运行向量化脚本"
            }
        
        return result
        
    except Exception as e:
        print(f"\n✗ RAG向量知识库测试失败: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def test_rag_service_detailed():
    """测试RAG服务功能 - 详细版本"""
    print_separator("RAG 服务功能详细测试")
    
    try:
        rag_project_root = project_root.parent / "PaddleOCRRAG"
        sys.path.insert(0, str(rag_project_root))
        
        from app.rag.vector_db.vector_db import get_vector_db, RuleVectorDB
        from app.core.config_manager import settings
        
        print("\n【RAG 配置信息】")
        print(f"  ├─ 向量数据库路径: {settings.CHROMA_DB_PATH}")
        print(f"  ├─ 规则文档路径: {settings.RULES_DOCS_PATH}")
        print(f"  ├─ 嵌入模型: {settings.EMBEDDING_MODEL}")
        print(f"  ├─ 嵌入设备: {settings.EMBEDDING_DEVICE}")
        print(f"  ├─ HuggingFace镜像: {settings.HF_ENDPOINT}")
        print(f"  └─ Top-K检索数: {settings.TOP_K}")
        
        print_sub_separator("初始化向量数据库")
        print("\n正在初始化向量数据库...")
        start_time = time.time()
        
        vector_db = get_vector_db()
        
        init_duration = time.time() - start_time
        print(f"向量数据库初始化完成 (耗时: {init_duration:.2f}秒)")
        
        print_sub_separator("获取向量数据库统计信息")
        
        stats = vector_db.get_category_stats()
        
        print("\n【向量数据库统计】")
        print(f"  ├─ 总文档数: {stats.get('total', 0)}")
        
        if 'by_type' in stats:
            print(f"\n  按类型分布:")
            for doc_type, count in stats['by_type'].items():
                print(f"    ├─ {doc_type}: {count}")
        
        if 'by_main_category' in stats:
            print(f"\n  按主类别分布:")
            for cat, count in stats['by_main_category'].items():
                print(f"    ├─ {cat}: {count}")
        
        if 'by_sub_category' in stats:
            print(f"\n  按子类别分布:")
            for cat, count in stats['by_sub_category'].items():
                print(f"    ├─ {cat}: {count}")
        
        if 'by_competition_type' in stats:
            print(f"\n  按竞赛类型分布:")
            for comp_type, count in stats['by_competition_type'].items():
                print(f"    ├─ {comp_type}: {count}")
        
        print(f"\n  需人工审核数: {stats.get('manual_review_count', 0)}")
        
        print_sub_separator("向量索引信息")
        print(f"\n  ├─ 集合名称: {vector_db.collection_name}")
        print(f"  ├─ 索引类型: HNSW (Hierarchical Navigable Small World)")
        print(f"  ├─ 相似度度量: Cosine (余弦相似度)")
        print(f"  └─ 嵌入维度: 384 (all-MiniLM-L6-v2) 或 768 (bge-small-zh)")
        
        return {
            "success": True,
            "config": {
                "chroma_db_path": settings.CHROMA_DB_PATH,
                "embedding_model": settings.EMBEDDING_MODEL,
                "top_k": settings.TOP_K
            },
            "stats": stats,
            "init_duration_seconds": round(init_duration, 2)
        }
        
    except ImportError as e:
        print(f"\n⚠ RAG服务导入失败（可能ChromaDB未安装）: {e}")
        return {"success": False, "error": f"导入失败: {e}", "requires_chromadb": True}
    except Exception as e:
        print(f"\n✗ RAG服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def test_rag_documents_detailed():
    """测试RAG文档向量化 - 详细版本"""
    print_separator("RAG 文档向量化详细测试")
    
    try:
        rag_project_root = project_root.parent / "PaddleOCRRAG"
        rules_dir = rag_project_root / "data" / "rules"
        
        print(f"\n【规则文档目录】")
        print(f"  路径: {rules_dir}")
        
        if rules_dir.exists():
            print(f"\n【目录状态】: 存在 ✓")
            
            print_sub_separator("规则文档详情")
            
            total_size = 0
            doc_count = 0
            documents = []
            
            for doc in sorted(rules_dir.iterdir()):
                if doc.is_file() and not doc.name.startswith('.'):
                    doc_count += 1
                    size = doc.stat().st_size
                    total_size += size
                    mod_time = datetime.fromtimestamp(doc.stat().st_mtime)
                    create_time = datetime.fromtimestamp(doc.stat().st_ctime)
                    
                    doc_info = {
                        "name": doc.name,
                        "extension": doc.suffix,
                        "size_bytes": size,
                        "size_formatted": format_size(size),
                        "modified": mod_time.strftime('%Y-%m-%d %H:%M:%S'),
                        "created": create_time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    documents.append(doc_info)
                    
                    print(f"\n  文档 #{doc_count}: {doc.name}")
                    print(f"    ├─ 类型: {doc.suffix.upper()}")
                    print(f"    ├─ 大小: {format_size(size)}")
                    print(f"    ├─ 创建时间: {create_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"    └─ 修改时间: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            print_sub_separator("文档统计汇总")
            print(f"\n  ├─ 文档总数: {doc_count}")
            print(f"  └─ 总大小: {format_size(total_size)}")
            
            result = {
                "success": True,
                "rules_directory": str(rules_dir),
                "document_count": doc_count,
                "total_size_bytes": total_size,
                "total_size_formatted": format_size(total_size),
                "documents": documents
            }
        else:
            print(f"\n【目录状态】: 不存在")
            print("  请将综测规则文档放入该目录")
            
            result = {
                "success": True,
                "rules_directory": str(rules_dir),
                "document_count": 0,
                "note": "目录不存在，请创建并放入规则文档"
            }
        
        return result
        
    except Exception as e:
        print(f"\n✗ RAG文档测试失败: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def test_rag_retrieval():
    """测试RAG检索功能"""
    print_separator("RAG 检索功能测试")
    
    try:
        rag_project_root = project_root.parent / "PaddleOCRRAG"
        sys.path.insert(0, str(rag_project_root))
        
        from app.rag.vector_db.vector_db import get_vector_db
        
        vector_db = get_vector_db()
        
        test_queries = [
            "综测计算细则",
            "省级竞赛一等奖加多少分",
            "英语四级可以加多少分",
            "社会实践要求多少学时",
            "创新创业加分规则"
        ]
        
        print("\n【检索测试】")
        
        results = []
        for query in test_queries:
            print_sub_separator(f"查询: {query}")
            
            start_time = time.time()
            search_result = vector_db.search_relevant(query, top_k=3)
            duration = time.time() - start_time
            
            documents = search_result.get("documents", [])
            metadatas = search_result.get("metadatas", [])
            distances = search_result.get("distances", [])
            
            if documents and len(documents) > 0:
                print(f"\n  找到 {len(documents)} 条相关结果 (耗时: {duration*1000:.2f}ms)")
                
                for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
                    print(f"\n  结果 #{i+1}:")
                    print(f"    ├─ 相似度距离: {dist:.4f}")
                    print(f"    ├─ 类型: {meta.get('type', 'N/A')}")
                    print(f"    ├─ 主类别: {meta.get('main_category', 'N/A')}")
                    print(f"    ├─ 子类别: {meta.get('sub_category', 'N/A')}")
                    print(f"    └─ 内容摘要: {doc[:100]}...")
            else:
                print(f"\n  未找到相关结果")
            
            results.append({
                "query": query,
                "result_count": len(documents) if documents else 0,
                "duration_ms": round(duration * 1000, 2)
            })
        
        return {
            "success": True,
            "test_queries": results
        }
        
    except ImportError as e:
        print(f"\n⚠ RAG检索测试跳过（ChromaDB未安装）: {e}")
        return {"success": False, "error": f"导入失败: {e}"}
    except Exception as e:
        print(f"\n✗ RAG检索测试失败: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def test_api_endpoints_detailed():
    """测试API端点 - 详细版本"""
    print_separator("API 端点详细测试")
    
    try:
        import requests
    except ImportError:
        print("requests库未安装，跳过API测试")
        return {"success": False, "error": "requests库未安装"}
    
    base_url = "http://localhost:8001"
    rag_url = "http://localhost:8000"
    
    print("\n【Visual Model API 测试】")
    print(f"  基础URL: {base_url}")
    
    visual_endpoints = [
        ("/health", "健康检查", "GET"),
        ("/api/v1/system/info", "系统信息", "GET"),
    ]
    
    visual_results = []
    for endpoint, name, method in visual_endpoints:
        url = f"{base_url}{endpoint}"
        print(f"\n  测试: {name}")
        print(f"    URL: {url}")
        print(f"    方法: {method}")
        
        try:
            start_time = time.time()
            if method == "GET":
                response = requests.get(url, timeout=5)
            duration = time.time() - start_time
            
            status = "✓ 成功" if response.status_code == 200 else "✗ 失败"
            print(f"    状态: {status} (HTTP {response.status_code})")
            print(f"    耗时: {duration*1000:.2f}ms")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"    响应: {json.dumps(data, ensure_ascii=False)[:100]}...")
                except:
                    print(f"    响应: {response.text[:100]}...")
            
            visual_results.append({
                "endpoint": endpoint,
                "name": name,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "success": response.status_code == 200
            })
        except requests.exceptions.RequestException as e:
            print(f"    状态: ✗ 连接失败")
            print(f"    错误: {str(e)[:50]}")
            visual_results.append({
                "endpoint": endpoint,
                "name": name,
                "success": False,
                "error": str(e)
            })
    
    print("\n【RAG API 测试】")
    print(f"  基础URL: {rag_url}")
    
    rag_endpoints = [
        ("/health", "健康检查", "GET"),
        ("/api/v1/system/status", "系统状态", "GET"),
    ]
    
    rag_results = []
    for endpoint, name, method in rag_endpoints:
        url = f"{rag_url}{endpoint}"
        print(f"\n  测试: {name}")
        print(f"    URL: {url}")
        print(f"    方法: {method}")
        
        try:
            start_time = time.time()
            if method == "GET":
                response = requests.get(url, timeout=5)
            duration = time.time() - start_time
            
            status = "✓ 成功" if response.status_code == 200 else "✗ 失败"
            print(f"    状态: {status} (HTTP {response.status_code})")
            print(f"    耗时: {duration*1000:.2f}ms")
            
            rag_results.append({
                "endpoint": endpoint,
                "name": name,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "success": response.status_code == 200
            })
        except requests.exceptions.RequestException as e:
            print(f"    状态: ✗ 连接失败")
            print(f"    错误: {str(e)[:50]}")
            rag_results.append({
                "endpoint": endpoint,
                "name": name,
                "success": False,
                "error": str(e)
            })
    
    return {
        "success": True,
        "visual_model_api": visual_results,
        "rag_api": rag_results
    }


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print("  综测计算助手 - 全面功能测试")
    print(f"  测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    results = {}
    
    results["paddleocr_models"] = test_paddleocr_models_detailed()
    results["ocr_service"] = test_ocr_service_detailed()
    results["rag_vector_db"] = test_rag_vector_db_detailed()
    results["rag_documents"] = test_rag_documents_detailed()
    results["rag_service"] = test_rag_service_detailed()
    results["rag_retrieval"] = test_rag_retrieval()
    results["api_endpoints"] = test_api_endpoints_detailed()
    
    print_separator("测试结果汇总")
    
    test_names = {
        "paddleocr_models": "PaddleOCR模型信息",
        "ocr_service": "OCR服务功能",
        "rag_vector_db": "RAG向量知识库",
        "rag_documents": "RAG文档向量化",
        "rag_service": "RAG服务功能",
        "rag_retrieval": "RAG检索功能",
        "api_endpoints": "API端点测试"
    }
    
    passed = 0
    total = len(results)
    
    for key, result in results.items():
        success = result.get("success", False) if isinstance(result, dict) else result
        status = "✓ 通过" if success else "✗ 失败"
        print(f"  {status}: {test_names.get(key, key)}")
        if success:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 测试通过")
    print(f"通过率: {passed/total*100:.1f}%")
    
    print_separator("测试报告保存")
    
    report = {
        "test_time": datetime.now().isoformat(),
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": f"{passed/total*100:.1f}%"
        },
        "results": results
    }
    
    report_path = project_root / "test_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n测试报告已保存: {report_path}")
    
    return results


if __name__ == "__main__":
    run_all_tests()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入规则文档到向量数据库
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import chromadb
from chromadb.config import Settings

def import_rules():
    """导入规则文档"""
    
    db_path = Path(r'd:\AIOCR\PaddleOCRRAG\data\chroma_db')
    rules_dir = Path(r'd:\AIOCR\PaddleOCRRAG\data\rules')
    
    print("=" * 60)
    print("导入规则文档到向量数据库")
    print("=" * 60)
    
    # 连接数据库
    client = chromadb.PersistentClient(
        path=str(db_path),
        settings=Settings(anonymized_telemetry=False)
    )
    
    collection = client.get_or_create_collection(
        name="zongce_rules",
        metadata={"hnsw:space": "cosine"}
    )
    
    print(f"\n当前文档数: {collection.count()}")
    
    # 读取规则文档
    documents = []
    metadatas = []
    
    # 读取 docx 文件
    docx_file = rules_dir / "03、计算机学院综合测评实施细则（2025）.docx"
    if docx_file.exists():
        print(f"\n正在读取: {docx_file.name}")
        try:
            import docx2txt
            text = docx2txt.process(str(docx_file))
            
            # 分段
            chunks = text.split('\n\n')
            for i, chunk in enumerate(chunks):
                if len(chunk.strip()) > 50:  # 只保留有意义的段落
                    documents.append(chunk.strip())
                    metadatas.append({
                        "source": docx_file.name,
                        "chunk_id": i,
                        "type": "rules"
                    })
            print(f"  提取了 {len(documents)} 个文档块")
        except Exception as e:
            print(f"  读取失败: {e}")
    
    # 读取 Excel 文件
    excel_file = rules_dir / "05、学科竞赛名称列表.xlsx"
    if excel_file.exists():
        print(f"\n正在读取: {excel_file.name}")
        try:
            import pandas as pd
            df = pd.read_excel(excel_file)
            
            for idx, row in df.iterrows():
                text = ' '.join([str(v) for v in row.values if pd.notna(v)])
                if len(text.strip()) > 20:
                    documents.append(text.strip())
                    metadatas.append({
                        "source": excel_file.name,
                        "row_id": idx,
                        "type": "competition_list"
                    })
            print(f"  提取了 {len(documents) - len(metadatas) + len(documents)} 个文档块")
        except Exception as e:
            print(f"  读取失败: {e}")
    
    if not documents:
        print("\n没有文档可导入")
        return
    
    # 添加到向量数据库
    print(f"\n正在导入 {len(documents)} 个文档块...")
    
    ids = [f"doc_{i}" for i in range(len(documents))]
    
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"导入完成!")
    print(f"当前文档数: {collection.count()}")
    
    # 验证
    print("\n验证查询...")
    results = collection.query(
        query_texts=["学科竞赛"],
        n_results=3
    )
    
    print(f"查询结果: {len(results['documents'][0])} 个文档")
    for i, doc in enumerate(results['documents'][0]):
        print(f"  {i+1}. {doc[:100]}...")
    
    print("\n" + "=" * 60)
    print("[SUCCESS] 导入完成!")
    print("=" * 60)

if __name__ == "__main__":
    import_rules()

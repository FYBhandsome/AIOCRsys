import os
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader, PDFPlumberLoader, Docx2txtLoader
)
from app.core.config_manager import settings


class RuleDocumentLoader:
    """综测规则文档加载器"""
    
    def __init__(self):
        self.documents = []
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", "。", "，", " ", ""]
        )
    
    def load_all_documents(self):
        """加载所有规则文档"""
        if not os.path.exists(settings.RULES_DOCS_PATH):
            os.makedirs(settings.RULES_DOCS_PATH, exist_ok=True)
            print(f"规则文档目录不存在，已创建: {settings.RULES_DOCS_PATH}")
            return self
        
        loaded_count = 0
        for filename in os.listdir(settings.RULES_DOCS_PATH):
            file_path = os.path.join(settings.RULES_DOCS_PATH, filename)
            
            # 跳过隐藏文件和目录
            if filename.startswith('.'):
                continue
            
            # 根据文件类型选择不同的加载器
            try:
                if filename.endswith(".txt"):
                    loader = TextLoader(file_path, encoding="utf-8")
                elif filename.endswith(".pdf"):
                    loader = PDFPlumberLoader(file_path)
                elif filename.endswith(".docx"):
                    loader = Docx2txtLoader(file_path)
                else:
                    continue  # 跳过不支持的文件类型
                
                docs = loader.load()
                self.documents.extend(docs)
                loaded_count += 1
                print(f"已加载文档: {filename} ({len(docs)} 页)")
            except Exception as e:
                print(f"加载文档 {filename} 时出错: {str(e)}")
                continue
        
        print(f"共加载 {loaded_count} 个文档")
        return self
    
    def split_documents(self):
        """分割文档为小块"""
        if not self.documents:
            return []
        return self.text_splitter.split_documents(self.documents)




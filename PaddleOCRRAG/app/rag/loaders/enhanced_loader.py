"""
增强文档加载器
支持按章节切分、类别标签嵌入、竞赛数据关联
"""
import os
import re
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import Docx2txtLoader, TextLoader, PDFPlumberLoader

from app.core.config_manager import settings
from app.rag.preprocessors.competition_mapper import get_competition_mapper
from app.rag.utils.category_keywords import SCORE_LIMITS, COMPETITION_TYPE_KEYWORDS
from app.core.logger import get_logger, LogContext, rag_logger, track_performance

logger = get_logger(__name__)


@dataclass
class EnhancedChunk:
    """增强的文档块"""
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "metadata": self.metadata
        }
    
    def to_langchain_format(self) -> Dict[str, Any]:
        """转换为LangChain Document格式"""
        from langchain_core.documents import Document
        return Document(page_content=self.text, metadata=self.metadata)


@dataclass
class RuleSection:
    """规则章节"""
    section_id: str
    title: str
    content: str
    main_category: str = "C"
    sub_category: Optional[str] = None
    source: str = ""


class EnhancedRuleLoader:
    """增强规则文档加载器"""
    
    SECTION_PATTERNS = {
        "C1": [
            r"第十二条[^\n]*科技[^\n]*",
            r"C1[：:][^\n]*",
            r"科技类[^\n]*奖励[^\n]*",
        ],
        "C2": [
            r"第十三条[^\n]*体育[^\n]*",
            r"C2[：:][^\n]*",
            r"体育类[^\n]*奖励[^\n]*",
        ],
        "C3": [
            r"第十四条[^\n]*文化[^\n]*",
            r"C3[：:][^\n]*",
            r"文化类[^\n]*奖励[^\n]*",
        ],
        "C4": [
            r"第十五条[^\n]*创新创业[^\n]*",
            r"C4[：:][^\n]*",
            r"创新创业[^\n]*奖励[^\n]*",
        ]
    }
    
    SCORE_PATTERNS = [
        (r"A类[^国]*国家级[^奖]*一等奖[^0-9]*(\d+)[分]", "A", "国家级", "一等奖"),
        (r"A类[^国]*国家级[^奖]*二等奖[^0-9]*(\d+)[分]", "A", "国家级", "二等奖"),
        (r"A类[^省]*省部级[^奖]*一等奖[^0-9]*(\d+)[分]", "A", "省部级", "一等奖"),
        (r"B类[^国]*国家级[^奖]*一等奖[^0-9]*(\d+)[分]", "B", "国家级", "一等奖"),
        (r"B类[^国]*国家级[^奖]*二等奖[^0-9]*(\d+)[分]", "B", "国家级", "二等奖"),
        (r"B类[^省]*省部级[^奖]*一等奖[^0-9]*(\d+)[分]", "B", "省部级", "一等奖"),
        (r"国家级[^奖]*一等奖[^0-9]*(\d+)[分]", None, "国家级", "一等奖"),
        (r"国家级[^奖]*二等奖[^0-9]*(\d+)[分]", None, "国家级", "二等奖"),
        (r"省部级[^奖]*一等奖[^0-9]*(\d+)[分]", None, "省部级", "一等奖"),
        (r"英语四级[^0-9]*(\d+)[分]", None, None, "CET4"),
        (r"英语六级[^0-9]*(\d+)[分]", None, None, "CET6"),
        (r"计算机二级[^0-9]*(\d+)[分]", None, None, "NCRE2"),
    ]
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """初始化增强加载器
        
        Args:
            chunk_size: 块大小
            chunk_overlap: 块重叠
        """
        self.logger = get_logger(__name__)
        self.chunks: List[EnhancedChunk] = []
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", "。", "，", " ", ""]
        )
        self.competition_mapper = None
    
    def _get_competition_mapper(self):
        """延迟加载竞赛映射器"""
        if self.competition_mapper is None:
            try:
                self.competition_mapper = get_competition_mapper()
                self.logger.debug("竞赛映射器加载成功")
            except Exception as e:
                self.logger.warning(f"加载竞赛映射器失败: {e}")
        return self.competition_mapper
    
    @track_performance("load_all_documents")
    def load_all_documents(self, docs_path: str = None) -> 'EnhancedRuleLoader':
        """加载所有规则文档
        
        Args:
            docs_path: 文档目录路径
            
        Returns:
            self，支持链式调用
        """
        start_time = time.time()
        
        if docs_path is None:
            docs_path = settings.RULES_DOCS_PATH
            
        if not os.path.exists(docs_path):
            os.makedirs(docs_path, exist_ok=True)
            self.logger.warning(f"规则文档目录不存在，已创建: {docs_path}")
            return self
        
        self.logger.info(f"开始加载文档目录: {docs_path}")
        
        loaded_count = 0
        error_count = 0
        for filename in os.listdir(docs_path):
            file_path = os.path.join(docs_path, filename)
            
            if filename.startswith('.'):
                continue
            
            try:
                if filename.endswith(".docx"):
                    self._load_docx(file_path, filename)
                    loaded_count += 1
                elif filename.endswith(".xlsx"):
                    self._load_excel(file_path, filename)
                    loaded_count += 1
                elif filename.endswith(".txt"):
                    self._load_txt(file_path, filename)
                    loaded_count += 1
                elif filename.endswith(".pdf"):
                    self._load_pdf(file_path, filename)
                    loaded_count += 1
                    
            except Exception as e:
                error_count += 1
                self.logger.error(f"加载文档 {filename} 时出错: {str(e)}", exc_info=True)
                continue
        
        duration_ms = int((time.time() - start_time) * 1000)
        self.logger.info(
            f"文档加载完成: 成功{loaded_count}个, 失败{error_count}个, 生成{len(self.chunks)}个chunk",
            extra={
                'duration_ms': duration_ms,
                'params': {
                    'loaded_count': loaded_count,
                    'error_count': error_count,
                    'chunk_count': len(self.chunks)
                }
            }
        )
        
        rag_logger.log_document_load(docs_path, loaded_count, len(self.chunks), duration_ms)
        
        return self
    
    def _load_docx(self, file_path: str, filename: str):
        """加载Word文档
        
        Args:
            file_path: 文件路径
            filename: 文件名
        """
        self.logger.info(f"加载Word文档: {filename}")
        
        loader = Docx2txtLoader(file_path)
        docs = loader.load()
        
        if docs:
            full_text = "\n".join([doc.page_content for doc in docs])
            sections = self._extract_sections(full_text, filename)
            
            for section in sections:
                self._process_section(section)
    
    def _load_excel(self, file_path: str, filename: str):
        """加载Excel竞赛列表
        
        Args:
            file_path: 文件路径
            filename: 文件名
        """
        self.logger.info(f"加载Excel竞赛列表: {filename}")
        
        mapper = self._get_competition_mapper()
        if mapper:
            competitions = mapper.get_all_competitions()
            
            for comp in competitions:
                chunk = self._create_competition_chunk(comp)
                self.chunks.append(chunk)
    
    def _load_txt(self, file_path: str, filename: str):
        """加载文本文件
        
        Args:
            file_path: 文件路径
            filename: 文件名
        """
        self.logger.info(f"加载文本文件: {filename}")
        
        loader = TextLoader(file_path, encoding="utf-8")
        docs = loader.load()
        
        if docs:
            full_text = "\n".join([doc.page_content for doc in docs])
            sections = self._extract_sections(full_text, filename)
            
            for section in sections:
                self._process_section(section)
    
    def _load_pdf(self, file_path: str, filename: str):
        """加载PDF文件
        
        Args:
            file_path: 文件路径
            filename: 文件名
        """
        self.logger.info(f"加载PDF文件: {filename}")
        
        loader = PDFPlumberLoader(file_path)
        docs = loader.load()
        
        if docs:
            full_text = "\n".join([doc.page_content for doc in docs])
            sections = self._extract_sections(full_text, filename)
            
            for section in sections:
                self._process_section(section)
    
    def _extract_sections(self, text: str, source: str) -> List[RuleSection]:
        """从文本中提取章节
        
        Args:
            text: 文档文本
            source: 来源文件名
            
        Returns:
            章节列表
        """
        sections = []
        
        article_pattern = r'(第[一二三四五六七八九十百]+条[^\n]*)'
        parts = re.split(article_pattern, text)
        
        current_section = None
        for i, part in enumerate(parts):
            if re.match(r'第[一二三四五六七八九十百]+条', part):
                if current_section:
                    sections.append(current_section)
                
                sub_category = self._detect_sub_category(part)
                current_section = RuleSection(
                    section_id=f"section_{len(sections)}",
                    title=part.strip(),
                    content="",
                    main_category="C",
                    sub_category=sub_category,
                    source=source
                )
            elif current_section:
                current_section.content += part
        
        if current_section:
            sections.append(current_section)
        
        return sections
    
    def _detect_sub_category(self, text: str) -> Optional[str]:
        """检测子类别
        
        Args:
            text: 文本内容
            
        Returns:
            子类别代码
        """
        for sub_cat, patterns in self.SECTION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return sub_cat
        return None
    
    def _process_section(self, section: RuleSection):
        """处理章节，生成chunk
        
        Args:
            section: 章节对象
        """
        if not section.content.strip():
            return
        
        sub_chunks = self.text_splitter.split_text(section.content)
        
        for i, chunk_text in enumerate(sub_chunks):
            enhanced_text = self._enhance_text(chunk_text, section)
            metadata = self._build_metadata(section, i, len(sub_chunks))
            
            score_info = self._extract_score_info(chunk_text)
            if score_info:
                metadata.update(score_info)
            
            chunk = EnhancedChunk(text=enhanced_text, metadata=metadata)
            self.chunks.append(chunk)
    
    def _enhance_text(self, text: str, section: RuleSection) -> str:
        """增强文本，添加类别标签
        
        Args:
            text: 原始文本
            section: 章节信息
            
        Returns:
            增强后的文本
        """
        tags = [f"主类:{section.main_category}"]
        
        if section.sub_category:
            tags.append(f"子类:{section.sub_category}")
        
        tag_str = "｜".join(tags)
        return f"【{tag_str}】{text}"
    
    def _build_metadata(self, section: RuleSection, chunk_index: int, total_chunks: int) -> Dict[str, Any]:
        """构建元数据
        
        Args:
            section: 章节信息
            chunk_index: 块索引
            total_chunks: 总块数
            
        Returns:
            元数据字典
        """
        metadata = {
            "type": "rule",
            "main_category": section.main_category,
            "sub_category": section.sub_category,
            "source": section.source,
            "section_title": section.title,
            "chunk_index": chunk_index,
            "total_chunks": total_chunks
        }
        
        if section.sub_category and section.sub_category in SCORE_LIMITS:
            metadata["max_score"] = SCORE_LIMITS[section.sub_category]["max"]
        
        return metadata
    
    def _extract_score_info(self, text: str) -> Optional[Dict[str, Any]]:
        """从文本中提取分数信息
        
        Args:
            text: 文本内容
            
        Returns:
            分数信息字典
        """
        for pattern, comp_type, level, award in self.SCORE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                score = int(match.group(1))
                info = {"score": score}
                if comp_type:
                    info["competition_type"] = comp_type
                if level:
                    info["level"] = level
                if award:
                    info["award_level"] = award
                return info
        return None
    
    def _create_competition_chunk(self, comp_info: Any) -> EnhancedChunk:
        """创建竞赛信息chunk
        
        Args:
            comp_info: 竞赛信息对象
            
        Returns:
            EnhancedChunk对象
        """
        comp_type = comp_info.competition_type
        level = comp_info.level
        name = comp_info.standard_name
        
        score = self._get_competition_score(comp_type, level)
        
        text = f"【主类:C｜子类:C1｜竞赛类型:{comp_type}｜级别:{level}】{name}"
        if score:
            text += f" 一等奖加{score}分"
        
        if comp_info.requires_manual_review:
            text += "（需人工审核）"
        
        metadata = {
            "type": "competition",
            "main_category": "C",
            "sub_category": "C1",
            "competition_type": comp_type,
            "level": level,
            "competition_name": name,
            "requires_manual_review": comp_info.requires_manual_review,
            "source": "学科竞赛名称列表"
        }
        
        if score:
            metadata["score"] = score
        
        return EnhancedChunk(text=text, metadata=metadata)
    
    def _get_competition_score(self, comp_type: str, level: str) -> Optional[int]:
        """获取竞赛加分
        
        Args:
            comp_type: 竞赛类型
            level: 竞赛级别
            
        Returns:
            加分值
        """
        if comp_type == "非AB":
            return None
        
        if comp_type in COMPETITION_TYPE_KEYWORDS:
            score_map = COMPETITION_TYPE_KEYWORDS[comp_type].get("score_map", {})
            key = f"{level}一等奖"
            return score_map.get(key)
        
        return None
    
    def get_chunks(self) -> List[EnhancedChunk]:
        """获取所有chunk
        
        Returns:
            chunk列表
        """
        return self.chunks
    
    def get_chunks_as_dicts(self) -> List[Dict[str, Any]]:
        """获取所有chunk（字典格式）
        
        Returns:
            chunk字典列表
        """
        return [chunk.to_dict() for chunk in self.chunks]
    
    def get_chunks_as_langchain(self) -> List[Any]:
        """获取所有chunk（LangChain格式）
        
        Returns:
            LangChain Document列表
        """
        return [chunk.to_langchain_format() for chunk in self.chunks]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            "total_chunks": len(self.chunks),
            "by_type": {},
            "by_sub_category": {},
            "by_competition_type": {}
        }
        
        for chunk in self.chunks:
            meta = chunk.metadata
            
            doc_type = meta.get("type", "unknown")
            stats["by_type"][doc_type] = stats["by_type"].get(doc_type, 0) + 1
            
            sub_cat = meta.get("sub_category", "unknown")
            stats["by_sub_category"][sub_cat] = stats["by_sub_category"].get(sub_cat, 0) + 1
            
            comp_type = meta.get("competition_type")
            if comp_type:
                stats["by_competition_type"][comp_type] = stats["by_competition_type"].get(comp_type, 0) + 1
        
        return stats


def get_enhanced_loader(chunk_size: int = 500, chunk_overlap: int = 50) -> EnhancedRuleLoader:
    """获取增强加载器实例
    
    Args:
        chunk_size: 块大小
        chunk_overlap: 块重叠
        
    Returns:
        EnhancedRuleLoader实例
    """
    return EnhancedRuleLoader(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

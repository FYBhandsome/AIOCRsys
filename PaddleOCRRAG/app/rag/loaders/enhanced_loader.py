"""
增强文档加载器
支持按章节切分、类别标签嵌入、竞赛数据关联
优化切片策略：按段落边界优先切分
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


DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 150


@dataclass
class ChunkConfig:
    """切片配置"""
    chunk_size: int = DEFAULT_CHUNK_SIZE
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
    separators: List[str] = field(default_factory=lambda: [
        "\n\n",
        "。\n",
        "。\r\n",
        "\n",
        "。",
        "！",
        "？",
        "；",
        "，",
        " ",
        ""
    ])
    
    list_item_pattern: str = r'(?:^\s*(?:\d+\.|[-•●○]\s)|(?:\n\s*(?:\d+\.|[-•●○]\s)))'
    table_separator: str = " | "
    rule_boundary_patterns: List[str] = field(default_factory=lambda: [
        r'[AB]类[^国省]*[国省]级[^奖]*[一二]等奖[^0-9]*\d+分',
        r'[AB]类.*?\d+分',
        r'国家级.*?一等奖.*?\d+分',
        r'省部级.*?一等奖.*?\d+分',
    ])


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


class SmartTextSplitter:
    """智能文本切分器 - 按段落边界优先切分，支持规则完整性保护"""
    
    RULE_SCORE_PATTERN = re.compile(
        r'([AB]类[^国省市]*[国省市]级[^奖]*[一二三]等奖[^0-9]*(\d+)[分])|'
        r'(国家级[^奖]*[一二三]等奖[^0-9]*(\d+)[分])|'
        r'(省部级[^奖]*[一二三]等奖[^0-9]*(\d+)[分])'
    )
    
    TABLE_ROW_PATTERN = re.compile(r'\|[^\n]+\|')
    
    def __init__(self, config: ChunkConfig = None):
        self.config = config or ChunkConfig()
        self._base_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            separators=self.config.separators
        )
    
    def split_text(self, text: str) -> List[str]:
        """智能切分文本
        
        优先按以下边界切分：
        1. 段落边界（\\n\\n）
        2. 句子边界（。！？）
        3. 列表项边界（1. 2. 3. 或 - •）
        4. 规则完整性保护（A类/B类规则与分数在同一切片）
        """
        if not text or not text.strip():
            return []
        
        paragraphs = self._split_by_paragraph(text)
        
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if self._is_list_item_start(para):
                if current_chunk:
                    chunks.extend(self._finalize_chunk(current_chunk))
                    current_chunk = ""
                
                list_chunks = self._split_list_items(para)
                chunks.extend(list_chunks)
            elif self._contains_table(para):
                if current_chunk:
                    chunks.extend(self._finalize_chunk(current_chunk))
                    current_chunk = ""
                table_chunks = self._split_table_content(para)
                chunks.extend(table_chunks)
            elif self._contains_rule_with_score(para):
                rule_chunks = self._split_rule_content(para, current_chunk)
                if rule_chunks:
                    chunks.extend(rule_chunks)
                    current_chunk = ""
            elif len(current_chunk) + len(para) + 2 <= self.config.chunk_size:
                current_chunk = current_chunk + "\n\n" + para if current_chunk else para
            else:
                if current_chunk:
                    chunks.extend(self._finalize_chunk(current_chunk))
                
                if len(para) > self.config.chunk_size:
                    sub_chunks = self._base_splitter.split_text(para)
                    chunks.extend(sub_chunks)
                else:
                    current_chunk = para
        
        if current_chunk:
            chunks.extend(self._finalize_chunk(current_chunk))
        
        return [c for c in chunks if c.strip()]
    
    def _contains_table(self, text: str) -> bool:
        """检测文本是否包含表格内容"""
        return self.config.table_separator in text or bool(self.TABLE_ROW_PATTERN.search(text))
    
    def _split_table_content(self, text: str) -> List[str]:
        """分割表格内容，保持行完整性"""
        lines = text.split('\n')
        table_rows = []
        current_row = ""
        
        for line in lines:
            if self.config.table_separator in line or self.TABLE_ROW_PATTERN.search(line):
                if current_row:
                    table_rows.append(current_row.strip())
                current_row = line
            else:
                current_row += "\n" + line if current_row else line
        
        if current_row:
            table_rows.append(current_row.strip())
        
        chunks = []
        current_chunk = ""
        
        for row in table_rows:
            if len(current_chunk) + len(row) + 2 <= self.config.chunk_size:
                current_chunk = current_chunk + "\n" + row if current_chunk else row
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = row
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _contains_rule_with_score(self, text: str) -> bool:
        """检测文本是否包含带分数的规则"""
        return bool(self.RULE_SCORE_PATTERN.search(text))
    
    def _split_rule_content(self, text: str, current_chunk: str) -> List[str]:
        """分割规则内容，确保规则与分数在同一切片"""
        chunks = []
        
        rule_matches = list(self.RULE_SCORE_PATTERN.finditer(text))
        
        if not rule_matches:
            return None
        
        last_end = 0
        for match in rule_matches:
            rule_start = match.start()
            rule_end = match.end()
            
            if rule_start > last_end:
                prefix = text[last_end:rule_start].strip()
                if prefix:
                    chunks.append(prefix)
            
            rule_text = text[rule_start:rule_end]
            chunks.append(rule_text)
            last_end = rule_end
        
        if last_end < len(text):
            suffix = text[last_end:].strip()
            if suffix:
                if chunks and len(chunks[-1]) + len(suffix) + 2 <= self.config.chunk_size:
                    chunks[-1] = chunks[-1] + " " + suffix
                else:
                    chunks.append(suffix)
        
        return chunks
    
    def _split_by_paragraph(self, text: str) -> List[str]:
        """按段落分割"""
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _is_list_item_start(self, text: str) -> bool:
        """检测是否为列表项开头"""
        lines = text.strip().split('\n')
        if not lines:
            return False
        
        first_line = lines[0].strip()
        list_patterns = [
            r'^\d+\.',
            r'^[-•●○]\s',
            r'^\([一二三四五六七八九十]+\)',
            r'^[一二三四五六七八九十]+[、.]',
        ]
        
        for pattern in list_patterns:
            if re.match(pattern, first_line):
                return True
        return False
    
    def _split_list_items(self, text: str) -> List[str]:
        """分割列表项"""
        lines = text.split('\n')
        items = []
        current_item = ""
        
        list_start_pattern = r'^\s*(?:\d+\.|[-•●○]\s|\([一二三四五六七八九十]+\)|[一二三四五六七八九十]+[、.])'
        
        for line in lines:
            if re.match(list_start_pattern, line.strip()):
                if current_item:
                    items.append(current_item.strip())
                current_item = line
            else:
                current_item += "\n" + line
        
        if current_item:
            items.append(current_item.strip())
        
        chunks = []
        current_chunk = ""
        
        for item in items:
            if len(current_chunk) + len(item) + 2 <= self.config.chunk_size:
                current_chunk = current_chunk + "\n" + item if current_chunk else item
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = item
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _finalize_chunk(self, text: str) -> List[str]:
        """最终处理chunk"""
        if len(text) <= self.config.chunk_size:
            return [text]
        
        return self._base_splitter.split_text(text)


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
    
    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        chunk_config: ChunkConfig = None
    ):
        """初始化增强加载器
        
        Args:
            chunk_size: 块大小（默认500字符）
            chunk_overlap: 块重叠（默认50字符）
            chunk_config: 切片配置对象（优先级高于单独参数）
        """
        self.logger = get_logger(__name__)
        self.chunks: List[EnhancedChunk] = []
        
        if chunk_config:
            self.chunk_config = chunk_config
        else:
            self.chunk_config = ChunkConfig(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
        
        self.text_splitter = SmartTextSplitter(self.chunk_config)
        self.competition_mapper = None
        self._chunk_counter = 0
    
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
        
        try:
            from docx import Document
            doc = Document(file_path)
            
            full_text_parts = []
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    full_text_parts.append(text)
            
            for table_idx, table in enumerate(doc.tables):
                table_text = self._extract_table_text(table, table_idx)
                if table_text:
                    full_text_parts.append(table_text)
            
            full_text = "\n\n".join(full_text_parts)
            self.logger.info(f"文档提取完成: {len(full_text)}字符, {len(doc.tables)}个表格")
            
            sections = self._extract_sections(full_text, filename)
            
            for section in sections:
                self._process_section(section)
                
        except ImportError:
            self.logger.warning("python-docx未安装，使用docx2txt备用方案")
            loader = Docx2txtLoader(file_path)
            docs = loader.load()
            
            if docs:
                full_text = "\n".join([doc.page_content for doc in docs])
                sections = self._extract_sections(full_text, filename)
                
                for section in sections:
                    self._process_section(section)
    
    def _extract_table_text(self, table, table_idx: int) -> str:
        """提取表格内容为结构化文本
        
        Args:
            table: 表格对象
            table_idx: 表格索引
            
        Returns:
            结构化的表格文本
        """
        if not table.rows:
            return ""
        
        rows_data = []
        for row in table.rows:
            cells = [cell.text.strip().replace('\n', ' ') for cell in row.cells]
            rows_data.append(cells)
        
        if not rows_data:
            return ""
        
        headers = rows_data[0] if rows_data else []
        
        result_lines = [f"【表格{table_idx + 1}】"]
        
        if len(rows_data) > 1 and len(headers) >= 2:
            for row in rows_data[1:]:
                if len(row) >= 2:
                    row_text = " | ".join([f"{h}: {v}" for h, v in zip(headers, row) if h and v])
                    if row_text:
                        result_lines.append(row_text)
        else:
            for row in rows_data:
                row_text = " | ".join([v for v in row if v])
                if row_text:
                    result_lines.append(row_text)
        
        return "\n".join(result_lines)
    
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
    
    def _process_section(self, section: RuleSection, page_number: int = None):
        """处理章节，生成chunk
        
        Args:
            section: 章节对象
            page_number: 页码（如果适用）
        """
        if not section.content.strip():
            return
        
        sub_chunks = self.text_splitter.split_text(section.content)
        
        for i, chunk_text in enumerate(sub_chunks):
            enhanced_text = self._enhance_text(chunk_text, section)
            metadata = self._build_metadata(
                section=section,
                chunk_index=i,
                total_chunks=len(sub_chunks),
                page_number=page_number
            )
            
            score_info = self._extract_score_info(chunk_text)
            if score_info:
                metadata.update(score_info)
            
            chunk = EnhancedChunk(text=enhanced_text, metadata=metadata)
            self.chunks.append(chunk)
            self._chunk_counter += 1
    
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
    
    def _build_metadata(
        self,
        section: RuleSection,
        chunk_index: int,
        total_chunks: int,
        page_number: int = None
    ) -> Dict[str, Any]:
        """构建元数据
        
        Args:
            section: 章节信息
            chunk_index: 块索引
            total_chunks: 总块数
            page_number: 页码（如果适用）
            
        Returns:
            元数据字典
        """
        category = self._determine_category(section)
        
        metadata = {
            "source_file": section.source,
            "chunk_index": self._chunk_counter,
            "local_chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "category": category,
            "type": "rule",
            "main_category": section.main_category,
            "sub_category": section.sub_category,
            "section_title": section.title,
        }
        
        if page_number is not None:
            metadata["page_number"] = page_number
        
        if section.sub_category and section.sub_category in SCORE_LIMITS:
            metadata["max_score"] = SCORE_LIMITS[section.sub_category]["max"]
        
        return metadata
    
    def _determine_category(self, section: RuleSection) -> str:
        """确定内容类别（A类/B类/C类）
        
        Args:
            section: 章节信息
            
        Returns:
            类别字符串
        """
        content = section.content.lower()
        title = section.title.lower() if section.title else ""
        
        if "a类" in content or "a类" in title:
            return "A类"
        elif "b类" in content or "b类" in title:
            return "B类"
        else:
            return "C类"
    
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
        
        category = "A类" if comp_type == "A" else ("B类" if comp_type == "B" else "C类")
        
        text = f"【主类:C｜子类:C1｜竞赛类型:{comp_type}｜级别:{level}】{name}"
        if score:
            text += f" 一等奖加{score}分"
        
        if comp_info.requires_manual_review:
            text += "（需人工审核）"
        
        metadata = {
            "source_file": "学科竞赛名称列表",
            "chunk_index": self._chunk_counter,
            "category": category,
            "type": "competition",
            "main_category": "C",
            "sub_category": "C1",
            "competition_type": comp_type,
            "level": level,
            "competition_name": name,
            "requires_manual_review": comp_info.requires_manual_review,
        }
        
        if score:
            metadata["score"] = score
        
        self._chunk_counter += 1
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
            "chunk_config": {
                "chunk_size": self.chunk_config.chunk_size,
                "chunk_overlap": self.chunk_config.chunk_overlap
            },
            "by_type": {},
            "by_category": {},
            "by_sub_category": {},
            "by_competition_type": {}
        }
        
        for chunk in self.chunks:
            meta = chunk.metadata
            
            doc_type = meta.get("type", "unknown")
            stats["by_type"][doc_type] = stats["by_type"].get(doc_type, 0) + 1
            
            category = meta.get("category", "unknown")
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
            
            sub_cat = meta.get("sub_category", "unknown")
            stats["by_sub_category"][sub_cat] = stats["by_sub_category"].get(sub_cat, 0) + 1
            
            comp_type = meta.get("competition_type")
            if comp_type:
                stats["by_competition_type"][comp_type] = stats["by_competition_type"].get(comp_type, 0) + 1
        
        return stats


def get_enhanced_loader(
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    chunk_config: ChunkConfig = None
) -> EnhancedRuleLoader:
    """获取增强加载器实例
    
    Args:
        chunk_size: 块大小（默认500字符）
        chunk_overlap: 块重叠（默认50字符）
        chunk_config: 切片配置对象（优先级高于单独参数）
        
    Returns:
        EnhancedRuleLoader实例
    """
    return EnhancedRuleLoader(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        chunk_config=chunk_config
    )

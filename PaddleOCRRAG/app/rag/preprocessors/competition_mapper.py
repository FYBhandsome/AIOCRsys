"""
竞赛名称映射器
负责加载Excel竞赛列表，构建映射表，支持模糊匹配
"""
import os
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict

from app.core.logger import get_logger, LogContext, rag_logger, mask_dict

logger = get_logger(__name__)


@dataclass
class CompetitionInfo:
    """竞赛信息数据类"""
    standard_name: str
    competition_type: str
    level: str
    aliases: List[str] = None
    requires_manual_review: bool = False
    
    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CompetitionMapper:
    """竞赛名称映射器"""
    
    _instance = None
    
    def __new__(cls, excel_path: str = None):
        logger.debug(f"[CompetitionMapper.__new__] 创建实例, excel_path={excel_path}")
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, excel_path: str = None):
        logger.debug(f"[CompetitionMapper.__init__] 初始化, _initialized={self._initialized}")
        if self._initialized:
            logger.debug("[CompetitionMapper] 已初始化，跳过")
            return
            
        self.logger = get_logger(__name__)
        self.competition_map: Dict[str, CompetitionInfo] = {}
        self.name_list: List[str] = []
        self.alias_map: Dict[str, str] = {}
        
        try:
            if excel_path:
                self.load_from_excel(excel_path)
                logger.debug(f"[CompetitionMapper] 加载Excel文件: {excel_path}")
        except Exception as e:
                logger.error(f"[CompetitionMapper] 加载Excel文件失败: {e}")
                logger.error(f"[CompetitionMapper] 请检查Excel文件格式是否正确")
        
        self._initialized = True
        logger.info(f"[CompetitionMapper] 初始化完成, 已加载 {len(self.competition_map)} 条竞赛记录")
    
    def load_from_excel(self, excel_path: str) -> bool:
        """从Excel文件加载竞赛列表
        
        Args:
            excel_path: Excel文件路径
            
        Returns:
            是否加载成功
        """
        start_time = time.time()
        logger.info(f"[load_from_excel] 开始加载Excel文件: {excel_path}")
        
        try:
            if not os.path.exists(excel_path):
                logger.error(f"[load_from_excel] Excel文件不存在: {excel_path}")
                return False
            
            import pandas as pd
            df = pd.read_excel(excel_path, sheet_name=0)
            logger.debug(f"[load_from_excel] Excel原始行数: {len(df)}")
            
            header_row = None
            for idx, row in df.iterrows():
                if '序号' in str(row.iloc[0]) or '竞赛名称' in str(row.iloc[1] if len(row) > 1 else ''):
                    header_row = idx
                    logger.debug(f"[load_from_excel] 找到表头行: {idx}")
                    break
            
            if header_row is not None:
                df = pd.read_excel(excel_path, sheet_name=0, header=header_row)
            
            df.columns = ['序号', '竞赛名称', '竞赛类别', '获奖竞赛级别'] + list(df.columns[4:])
            
            success_count = 0
            error_count = 0
            
            for idx, row in df.iterrows():
                try:
                    name = str(row['竞赛名称']).strip() if pd.notna(row['竞赛名称']) else None
                    comp_type = str(row['竞赛类别']).strip() if pd.notna(row['竞赛类别']) else None
                    level = str(row['获奖竞赛级别']).strip() if pd.notna(row['获奖竞赛级别']) else None
                    
                    if not name or name == 'nan':
                        continue
                    
                    requires_manual_review = (comp_type == "非AB")
                    
                    info = CompetitionInfo(
                        standard_name=name,
                        competition_type=comp_type or "未知",
                        level=level or "未知",
                        aliases=self._generate_aliases(name),
                        requires_manual_review=requires_manual_review
                    )
                    
                    self.competition_map[name] = info
                    self.name_list.append(name)
                    
                    for alias in info.aliases:
                        self.alias_map[alias.lower()] = name
                    
                    success_count += 1
                    
                    if requires_manual_review:
                        logger.debug(f"[load_from_excel] 非AB类竞赛: {name}")
                        
                except Exception as e:
                    error_count += 1
                    logger.warning(f"[load_from_excel] 处理第{idx}行数据失败: {e}")
                    continue
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            type_stats = {}
            for info in self.competition_map.values():
                t = info.competition_type
                type_stats[t] = type_stats.get(t, 0) + 1
            
            logger.info(
                f"[load_from_excel] 加载完成: 成功{success_count}条, 失败{error_count}条",
                extra={
                    'duration_ms': duration_ms,
                    'success_count': success_count,
                    'error_count': error_count,
                    'type_stats': type_stats
                }
            )
            
            rag_logger.log_document_load(excel_path, 1, success_count, duration_ms)
            
            return True
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"[load_from_excel] 加载失败: {e}",
                extra={'duration_ms': duration_ms},
                exc_info=True
            )
            return False
    
    def _generate_aliases(self, name: str) -> List[str]:
        """生成竞赛名称的别名列表
        
        Args:
            name: 标准竞赛名称
            
        Returns:
            别名列表
        """
        aliases = [name]
        
        name_clean = name.replace("（", "(").replace("）", ")")
        aliases.append(name_clean)
        
        match = re.search(r'[（(](.+?)[）)]', name)
        if match:
            suffix = match.group(1)
            name_without_suffix = name[:match.start()].strip()
            aliases.append(name_without_suffix)
            aliases.append(f"{name_without_suffix}({suffix})")
            
            if suffix in ['国赛', '国赛)', '国家级']:
                aliases.append(f"{name_without_suffix}国赛")
                aliases.append(f"{name_without_suffix}国家级")
            elif suffix in ['省赛', '省赛)', '省部级']:
                aliases.append(f"{name_without_suffix}省赛")
                aliases.append(f"{name_without_suffix}省部级")
        
        short_names = {
            "全国大学生电子设计竞赛": ["电赛", "电子设计大赛", "电子设计竞赛", "电子设计"],
            "全国大学生数学建模竞赛": ["数模", "数学建模", "建模大赛", "数学建模竞赛"],
            "全国大学生智能汽车竞赛": ["智能车", "智能车竞赛"],
            "全国大学生机械创新设计大赛": ["机械创新", "机械设计"],
            "中国国际互联网+大学生创新创业大赛": ["互联网+", "互联网+大赛"],
            "挑战杯大学生科技作品竞赛": ["挑战杯", "挑战杯竞赛"],
            "蓝桥杯全国软件和信息技术专业人才大赛": ["蓝桥杯", "蓝桥", "蓝桥杯大赛"],
            "外研社国才杯英语演讲比赛": ["外研社", "英语演讲"],
            "全国高校数字艺术设计大赛": ["数字艺术", "艺术设计大赛"],
            "中国机器人及人工智能大赛": ["机器人", "机器人竞赛", "人工智能大赛"],
            "全国大学生英语竞赛": ["英语竞赛", "NECCS"],
            "全国大学生计算机设计大赛": ["计算机设计", "计设"],
            "全国大学生创新创业年会": ["创新创业年会", "双创年会"],
            "全国周培源大学生力学竞赛": ["周培源力学", "力学竞赛", "培源力学"],
        }
        
        name_clean_quotes = name.replace('"', '').replace('"', '').replace('"', '')
        
        for full_name, short_list in short_names.items():
            if full_name in name or full_name in name_clean_quotes:
                aliases.extend(short_list)
                for short in short_list:
                    if '国赛' in name or '国家级' in name:
                        aliases.append(f"{short}国赛")
                    if '省赛' in name or '省部级' in name:
                        aliases.append(f"{short}省赛")
                logger.debug(f"[_generate_aliases] 为 '{name}' 添加别名: {short_list}")
                break
        
        if '蓝桥杯' in name:
            aliases.extend(['蓝桥杯', '蓝桥', '蓝桥杯大赛'])
            if '国赛' in name or '国家级' in name:
                aliases.extend(['蓝桥杯国赛', '蓝桥国赛'])
            if '省赛' in name or '省部级' in name:
                aliases.extend(['蓝桥杯省赛', '蓝桥省赛'])
        
        return list(set(aliases))
    
    def normalize_name(self, user_input: str, threshold: int = 70) -> Tuple[Optional[str], Optional[CompetitionInfo], int]:
        """标准化竞赛名称（模糊匹配）
        
        Args:
            user_input: 用户输入的竞赛名称
            threshold: 相似度阈值（0-100）
            
        Returns:
            (标准名称, 竞赛信息, 相似度分数)
        """
        start_time = time.time()
        logger.debug(f"[normalize_name] 开始匹配: '{user_input}', 阈值={threshold}")
        
        if not user_input:
            logger.warning("[normalize_name] 输入为空")
            return None, None, 0
        
        user_input = user_input.strip()
        
        if user_input in self.competition_map:
            info = self.competition_map[user_input]
            duration_ms = int((time.time() - start_time) * 1000)
            logger.debug(f"[normalize_name] 精确匹配: '{user_input}' -> '{user_input}'")
            rag_logger.log_competition_match(user_input, user_input, 100, info.competition_type)
            return user_input, info, 100
        
        user_lower = user_input.lower()
        if user_lower in self.alias_map:
            std_name = self.alias_map[user_lower]
            info = self.competition_map[std_name]
            duration_ms = int((time.time() - start_time) * 1000)
            logger.debug(f"[normalize_name] 别名匹配: '{user_input}' -> '{std_name}'")
            rag_logger.log_competition_match(user_input, std_name, 95, info.competition_type)
            return std_name, info, 95
        
        best_match = None
        best_score = 0
        best_name = None
        
        try:
            from rapidfuzz import process, fuzz
            result = process.extractOne(
                user_input, 
                self.name_list,
                scorer=fuzz.WRatio
            )
            if result:
                best_name, best_score, _ = result
                logger.debug(f"[normalize_name] rapidfuzz匹配: '{user_input}' -> '{best_name}' (分数: {best_score})")
        except ImportError:
            import difflib
            matches = difflib.get_close_matches(user_input, self.name_list, n=1, cutoff=0.6)
            if matches:
                best_name = matches[0]
                best_score = int(difflib.SequenceMatcher(None, user_input, best_name).ratio() * 100)
                logger.debug(f"[normalize_name] difflib匹配: '{user_input}' -> '{best_name}' (分数: {best_score})")
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        if best_score >= threshold and best_name:
            info = self.competition_map[best_name]
            rag_logger.log_competition_match(user_input, best_name, best_score, info.competition_type)
            rag_logger.log_performance("normalize_name", duration_ms, {"method": "fuzzy", "score": best_score})
            return best_name, info, best_score
        
        logger.debug(f"[normalize_name] 未找到匹配: '{user_input}' (最高分数: {best_score} < {threshold})")
        rag_logger.log_performance("normalize_name", duration_ms, {"method": "failed", "best_score": best_score})
        return None, None, best_score
    
    def get_competition_info(self, name: str) -> Optional[CompetitionInfo]:
        """获取竞赛信息
        
        Args:
            name: 竞赛名称
            
        Returns:
            竞赛信息
        """
        logger.debug(f"[get_competition_info] 查询: '{name}'")
        return self.competition_map.get(name)
    
    def get_all_competitions(self) -> List[CompetitionInfo]:
        """获取所有竞赛信息
        
        Returns:
            竞赛信息列表
        """
        logger.debug(f"[get_all_competitions] 返回 {len(self.competition_map)} 条记录")
        return list(self.competition_map.values())
    
    def get_competitions_by_type(self, comp_type: str) -> List[CompetitionInfo]:
        """按类别获取竞赛
        
        Args:
            comp_type: 竞赛类别（A/B/非AB）
            
        Returns:
            竞赛信息列表
        """
        logger.debug(f"[get_competitions_by_type] 查询类别: {comp_type}")
        result = [
            info for info in self.competition_map.values()
            if info.competition_type == comp_type
        ]
        logger.debug(f"[get_competitions_by_type] 找到 {len(result)} 条记录")
        return result
    
    def get_competitions_by_level(self, level: str) -> List[CompetitionInfo]:
        """按级别获取竞赛
        
        Args:
            level: 竞赛级别（国家级/省部级）
            
        Returns:
            竞赛信息列表
        """
        logger.debug(f"[get_competitions_by_level] 查询级别: {level}")
        result = [
            info for info in self.competition_map.values()
            if info.level == level
        ]
        logger.debug(f"[get_competitions_by_level] 找到 {len(result)} 条记录")
        return result
    
    def is_non_ab_competition(self, name: str) -> bool:
        """判断是否为非AB类竞赛
        
        Args:
            name: 竞赛名称
            
        Returns:
            是否为非AB类
        """
        info = self.competition_map.get(name)
        result = info.requires_manual_review if info else False
        logger.debug(f"[is_non_ab_competition] '{name}' -> {result}")
        return result
    
    def to_json(self) -> str:
        """导出为JSON
        
        Returns:
            JSON字符串
        """
        logger.debug("[to_json] 导出竞赛映射表为JSON")
        data = {
            name: info.to_dict() 
            for name, info in self.competition_map.items()
        }
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def save_to_json(self, output_path: str) -> bool:
        """保存到JSON文件
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            是否保存成功
        """
        logger.info(f"[save_to_json] 保存到: {output_path}")
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(self.to_json())
            logger.info(f"[save_to_json] 保存成功")
            return True
        except Exception as e:
            logger.error(f"[save_to_json] 保存失败: {e}", exc_info=True)
            return False


competition_mapper: Optional[CompetitionMapper] = None


def get_competition_mapper(excel_path: str = None) -> CompetitionMapper:
    """获取竞赛映射器单例
    
    Args:
        excel_path: Excel文件路径
        
    Returns:
        CompetitionMapper实例
    """
    global competition_mapper
    
    logger.debug(f"[get_competition_mapper] 获取实例, excel_path={excel_path}")
    
    if competition_mapper is None:
        if excel_path is None:
            from app.core.config_manager import settings
            rules_path = settings.RULES_DOCS_PATH
            excel_path = os.path.join(rules_path, "05、学科竞赛名称列表.xlsx")
            logger.debug(f"[get_competition_mapper] 使用默认路径: {excel_path}")
        
        competition_mapper = CompetitionMapper(excel_path)
    
    return competition_mapper

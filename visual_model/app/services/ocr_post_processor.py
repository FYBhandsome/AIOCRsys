#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR后处理模块 - 文字补全和修复
================================

功能：
1. 补全被截断的证书关键词（一等奖/二等奖/三等奖等）
2. 修复常见的OCR识别错误
3. 基于上下文推断缺失字符
4. 提取并标准化奖项等级信息
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class OCRPostProcessor:
    """OCR结果后处理器"""

    # 常见的证书关键词及其可能的截断形式
    AWARD_LEVEL_PATTERNS = {
        # 完整模式 -> 标准化名称
        r'特等奖': '特等奖',
        r'一等奖': '一等奖',
        r'二等奖': '二等奖',
        r'三等奖': '三等奖',
        r'优秀奖': '优秀奖',
        r'优胜奖': '优胜奖',
        r'金奖': '金奖',
        r'银奖': '银奖',
        r'铜奖': '铜奖',

        # 截断模式（缺少前缀数字）-> 推断补全
        r'(?<![一二三特优])等奖': '_PENDING_',  # 待推断的"等奖"
        r'(?<![一二三特优])等奖': '_PENDING_',
    }

    # 竞赛级别关键词
    LEVEL_KEYWORDS = [
        ('国家级', ['国家', '全国', '国际', '世界']),
        ('省部级', ['省级', '省赛', '赛区', '河北', '北京', '上海']),  # 常见省份
        ('市级', ['市级']),
        ('校级', ['校级', '院级', '校内']),
        ('院级', ['院级']),
    ]

    # 需要补全的前缀映射（基于上下文）
    PREFIX_INFERENCE_RULES = [
        # (上下文特征, 可能的前缀列表, 权重)
        (r'(蓝桥杯|ACM|数学建模|挑战杯|互联网\+|创新创业)', ['一', '二', '三'], 0.6),
        (r'(优秀|先进|积极分子)', ['优'], 0.8),
        (r'(第一名|冠军|金牌)', ['一'], 0.9),
        (r'(第二名|亚军|银牌)', ['二'], 0.9),
        (r'(第三名|季军|铜牌)', ['三'], 0.9),
    ]

    def __init__(self):
        self.stats = {
            'total_processed': 0,
            'fixes_applied': 0,
            'inferences_made': 0,
        }

    def process(self, ocr_text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        处理OCR文本，进行文字补全和修复

        Args:
            ocr_text: OCR原始文本
            context: 可选的上下文信息（如图像路径、证书类型等）

        Returns:
            处理结果字典，包含：
            - processed_text: 处理后的文本
            - raw_text: 原始文本
            - fixes: 应用的修复列表
            - award_info: 提取的奖项信息
            - confidence: 处理置信度
        """
        self.stats['total_processed'] += 1

        original_text = ocr_text
        fixes_applied = []

        # 步骤1：基础清理
        text = self._basic_cleanup(ocr_text)
        if text != ocr_text:
            fixes_applied.append({'type': 'cleanup', 'detail': '基础文本清理'})

        # 步骤2：补全被截断的奖项等级
        text, level_fixes = self._fix_truncated_award_levels(text)
        fixes_applied.extend(level_fixes)

        # 步骤3：修复常见OCR错误
        text, error_fixes = self._fix_common_ocr_errors(text)
        fixes_applied.extend(error_fixes)

        # 步骤4：提取结构化奖项信息
        award_info = self._extract_award_info(text, original_text)

        # 计算处理置信度
        confidence = self._calculate_confidence(original_text, text, fixes_applied)

        self.stats['fixes_applied'] += len(fixes_applied)

        result = {
            'processed_text': text,
            'raw_text': original_text,
            'fixes': fixes_applied,
            'award_info': award_info,
            'confidence': confidence,
        }

        if fixes_applied:
            logger.info(f"[OCR后处理] 应用{len(fixes_applied)}个修复: {[f['type'] for f in fixes_applied]}")

        return result

    def _basic_cleanup(self, text: str) -> str:
        """基础文本清理"""
        # 移除多余空格（保留单个空格）
        text = re.sub(r'\s+', ' ', text)
        # 移除特殊字符但保留中文标点和常用符号
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s，。、；：""''！（）《》\-\/\\\@\#\$\%\^\&\*\+\=\[\]\{\}\|\`\~\_\.\,\:\;\!\?\(\)]', '', text)
        return text.strip()

    def _fix_truncated_award_levels(self, text: str) -> Tuple[str, List[Dict]]:
        """补全被截断的奖项等级"""
        fixes = []
        modified_text = text

        # 检测所有"等奖"模式（可能是截断的）
        pending_matches = list(re.finditer(r'(?<![一二三特优金银铜])(等奖)', modified_text))

        if not pending_matches:
            return modified_text, fixes

        for match in reversed(pending_matches):  # 从后往前替换，避免位置偏移
            start, end = match.span()
            context_before = modified_text[max(0, start-50):start]
            context_after = modified_text[end:end+20]

            # 尝试推断正确的前缀
            inferred_prefix = self._infer_prefix(context_before + context_after, modified_text)

            if inferred_prefix:
                replacement = f'{inferred_prefix}等奖'
                modified_text = modified_text[:start] + replacement + modified_text[end:]
                fixes.append({
                    'type': 'award_level_completion',
                    'original': '等奖',
                    'replacement': replacement,
                    'confidence': 0.7 if inferred_prefix in ['一', '二', '三'] else 0.5,
                    'context': f'...{context_before[-30:]}[等奖]{context_after[:20]}...'
                })
                self.stats['inferences_made'] += 1
                logger.debug(f"[OCR后处理] 补全奖项等级: '等奖' -> '{replacement}'")

        return modified_text, fixes

    def _infer_prefix(self, context: str, full_text: str) -> Optional[str]:
        """
        基于上下文推断"等奖"的正确前缀

        Args:
            context: "等奖"周围的上下文
            full_text: 完整文本

        Returns:
            推断的前缀字符（如"一"、"二"、"三"），如果无法推断则返回None
        """

        # 规则1：检查是否在完整文本的其他位置出现过完整的奖项等级
        full_patterns = [r'(一|二|三|特|优)等奖', r'(第[一二三四五六七八九十]+名)']
        for pattern in full_patterns:
            matches = re.findall(pattern, full_text)
            if matches:
                # 找到其他位置的完整奖项，使用最常见的一个
                prefix = matches[0]
                if isinstance(prefix, tuple):
                    prefix = prefix[0]
                if prefix in ['一', '二', '三']:
                    logger.debug(f"[OCR后处理] 从其他位置找到完整奖项: {prefix}等奖")
                    return prefix

        # 规则2：基于竞赛类型推断（蓝桥杯等通常是高等级奖项）
        competition_keywords = {
            '蓝桥杯': '一',
            'ACM': '一',
            '数学建模': '一',
            '挑战杯': '一',
            '互联网+': '一',
            '创新创业': '一',
        }

        for keyword, likely_prefix in competition_keywords.items():
            if keyword in full_text:
                logger.debug(f"[OCR后处理] 基于竞赛类型'{keyword}'推断为{likely_prefix}等奖")
                return likely_prefix

        # 规则3：查找"第X届/届"后面的内容，通常会有完整描述
        session_match = re.search(r'第[一二三四五六七八九十\d]+届[^，。]*?(一|二|三)?等奖?', full_text)
        if session_match:
            matched_text = session_match.group()
            level_match = re.search(r'(一|二|三|特|优)等奖', matched_text)
            if level_match:
                prefix = level_match.group(1)
                logger.debug(f"[OCR后处理] 从届数描述中找到: {prefix}等奖")
                return prefix

            # 如果这届描述中有"等奖"但没有前缀，且是知名竞赛，默认为一等
            if any(kw in matched_text for kw in competition_keywords.keys()):
                logger.debug(f"[OCR后处理] 知名竞赛+届数描述，默认推断为一等奖")
                return '一'

        # 规则4：检查是否有"荣获"、"获得"等动词后的描述
        award_verb_pattern = re.search(r'(?:荣获|获得|取得)[^，。]{0,30}等奖', full_text)
        if award_verb_pattern:
            verb_context = award_verb_pattern.group()
            # 荣获的通常是一等奖或更高
            if '荣获' in verb_context or '获得' in verb_context:
                logger.debug(f"[OCR后处理] 基于'{verb_context[:10]}'默认推断为一等奖")
                return '一'

        # 无法推断
        logger.debug("[OCR后处理] 无法推断奖项等级前缀")
        return None

    def _fix_common_ocr_errors(self, text: str) -> Tuple[str, List[Dict]]:
        """修复常见的OCR错误"""
        fixes = []
        modified_text = text

        # 常见错误修正规则：(错误模式, 正确模式, 描述)
        error_rules = [
            # 数字/单位错误
            (r'(\d)届(\s*)奖', r'\1届\2', '多余的"奖"字'),
            (r'(\d+)分$', r'\1分', '末尾分数格式'),

            # 常见混淆字
            (r'己知', '已知', '"己"->"已"'),
            (r'巳知', '已知', '"巳"->"已"'),
            (r'由其', '尤其', '"由其"->"尤其"'),

            # 证书特有错误
            (r'荣茯', '荣获', '"茯"->"获"'),
            (r'荣獲', '荣获', '繁体"獲"->"获"'),
            (r'软作', '软件', '"作"->"件"'),
            (r'信自技术', '信息技术', '"自"->"息"'),
        ]

        for pattern, replacement, description in error_rules:
            matches = list(re.finditer(pattern, modified_text))
            if matches:
                count = len(matches)
                modified_text = re.sub(pattern, replacement, modified_text)
                fixes.append({
                    'type': 'ocr_error_fix',
                    'pattern': pattern,
                    'description': description,
                    'count': count,
                })

        return modified_text, fixes

    def _extract_award_info(self, processed_text: str, raw_text: str) -> Dict[str, Any]:
        """从处理后的文本中提取结构化奖项信息"""

        info = {
            'competition_name': None,
            'award_level': None,
            'competition_level': None,  # 国家级/省部级/校级
            'session': None,  # 第几届
            'issuer': None,
            'date': None,
            'recipient': None,
        }

        # 提取竞赛名称（在"荣获"或"获得"之后，到"等奖"之前的长文本）
        name_match = re.search(
            r'(?:荣获|获得)[^，。]{2,40}?(?:一|二|三|特|优)?等奖?',
            processed_text
        )
        if name_match:
            info['competition_name'] = name_match.group().strip()

        # 提取奖项等级
        level_match = re.search(
            r'(特等|一等|二等|三等|优秀|优胜|金|银|铜)奖',
            processed_text
        )
        if level_match:
            info['award_level'] = level_match.group() + '奖'

        # 提取竞赛级别（国家级/省部级等）
        for level_name, keywords in self.LEVEL_KEYWORDS:
            if any(kw in processed_text for kw in keywords):
                info['competition_level'] = level_name
                break

        # 特别处理：河北赛区等明确表示省部级
        if not info['competition_level']:
            province_patterns = ['赛区', '河北', '北京', '上海', '广东', '江苏', '浙江']
            if any(p in processed_text for p in province_patterns):
                info['competition_level'] = '省部级'

        # 提取届数
        session_match = re.search(r'第([一二三四五六七八九十\d]+)届', processed_text)
        if session_match:
            info['session'] = session_match.group()

        # 提取颁发单位
        issuer_patterns = [
            r'([^，。]{2,20})(?:组织委员会|委员会|协会|学会)',
            r'(?:主办|颁发|授予)[^，。]{0,5}([^，。]{2,20})',
        ]
        for pattern in issuer_patterns:
            match = re.search(pattern, processed_text)
            if match:
                groups = match.groups()
                info['issuer'] = groups[-1] if groups else None
                break

        # 提取日期
        date_match = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)', processed_text)
        if date_match:
            info['date'] = date_match.group(1)

        # 提取获奖人
        recipient_patterns = [
            r'姓名[：:]\s*([^\s\n，,。.]+)',
            r'获奖者[：:]\s*([^\s\n，,。.]+)',
            r'学生[：:]\s*([^\s\n，,。.]+)',
        ]
        for pattern in recipient_patterns:
            match = re.search(pattern, processed_text)
            if match:
                info['recipient'] = match.group(1)
                break

        # 如果processed_text没提取到，尝试raw_text
        if not all(info.values()) and raw_text:
            raw_info = self._extract_award_info(raw_text, None)
            for key, value in raw_info.items():
                if not info[key] and value:
                    info[key] = value

        return info

    def _calculate_confidence(self, original: str, processed: str, fixes: List[Dict]) -> float:
        """计算处理后文本的置信度"""
        base_confidence = 0.95  # 基础置信度

        # 根据修复类型调整置信度
        for fix in fixes:
            fix_type = fix.get('type', '')

            if fix_type == 'cleanup':
                base_confidence -= 0.01  # 清理操作影响很小
            elif fix_type == 'ocr_error_fix':
                base_confidence -= 0.02  # 错误修正略降
            elif fix_type == 'award_level_completion':
                # 奖项补全根据置信度调整
                fix_confidence = fix.get('confidence', 0.5)
                base_confidence *= (0.8 + 0.2 * fix_confidence)

        return max(0.5, min(1.0, base_confidence))  # 限制在0.5-1.0范围

    def get_stats(self) -> Dict[str, int]:
        """获取处理统计信息"""
        return self.stats.copy()


# 全局单例实例
_post_processor_instance = None


def get_ocr_post_processor() -> OCRPostProcessor:
    """获取OCR后处理器单例"""
    global _post_processor_instance
    if _post_processor_instance is None:
        _post_processor_instance = OCRPostProcessor()
    return _post_processor_instance


def process_ocr_text(ocr_text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """
    便捷函数：处理OCR文本

    Args:
        ocr_text: OCR原始文本
        context: 可选上下文

    Returns:
        处理结果字典
    """
    processor = get_ocr_post_processor()
    return processor.process(ocr_text, context)


if __name__ == "__main__":
    import sys

    test_cases = [
        ("荣获第十六届蓝桥杯全国软件和信息技术专业人才大赛河北赛区C/C++程序设计大学B组一等奖", "完整文本"),
        ("荣获第十六届蓝桥杯全国软件和信息技术专业人才大赛河北赛区C/C++程序设计大学B组等奖", "截断的一等奖"),
        ("荣获第十六届蓝桥杯全国软件和信息技术 专业人才大赛 河北 等奖。", "严重截断"),
        ("获得2023年数学建模竞赛国家级优秀奖", "优秀奖测试"),
    ]

    processor = OCRPostProcessor()

    print("=" * 70)
    print("OCR后处理模块测试")
    print("=" * 70)

    for i, (text, desc) in enumerate(test_cases, 1):
        print(f"\n[测试{i}] {desc}")
        print(f"原始文本: {text}")

        result = processor.process(text)

        print(f"处理后:   {result['processed_text']}")
        print(f"修复数:   {len(result['fixes'])}")
        if result['fixes']:
            for fix in result['fixes']:
                print(f"  - {fix['type']}: {fix.get('description', fix.get('original', ''))}")
        print(f"奖项信息: {result['award_info']}")
        print(f"置信度:   {result['confidence']:.2f}")

    print("\n" + "=" * 70)
    print(f"统计: {processor.get_stats()}")

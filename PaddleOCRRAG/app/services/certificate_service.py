"""
证书服务层
处理证书加分计算和分析的业务逻辑
"""
import json
import re
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from app.core.llm_manager import LLMManager

logger = logging.getLogger(__name__)


class CertificateService:
    """证书服务类"""
    
    def __init__(self):
        """初始化证书服务"""
        self._llm_manager = None
        self._vector_db = None
    
    @property
    def llm_manager(self):
        """延迟加载LLM管理器"""
        if self._llm_manager is None:
            self._llm_manager = LLMManager()
        return self._llm_manager
    
    @property
    def vector_db(self):
        """延迟加载向量数据库"""
        if self._vector_db is None:
            from app.rag.vector_db.vector_db import get_vector_db
            self._vector_db = get_vector_db()
        return self._vector_db
    
    def _retrieve_rules(self, query: str, top_k: int = 3) -> str:
        """检索相关规则
        
        Args:
            query: 查询文本
            top_k: 检索结果数量
            
        Returns:
            格式化的规则文本
        """
        try:
            results = self.vector_db.search_relevant(
                query=query,
                top_k=top_k,
                similarity_threshold=0.65
            )
            
            documents = results.get("documents", [])
            metadatas = results.get("metadatas", [])
            
            if not documents:
                logger.warning(f"未找到相关规则: {query[:50]}")
                return ""
            
            rules_parts = []
            for i, (doc, meta) in enumerate(zip(documents, metadatas), 1):
                category = meta.get("category", "未知类别") if meta else "未知类别"
                rules_parts.append(f"[规则{i}] 类别: {category}\n{doc}")
            
            rules = "\n\n".join(rules_parts)
            logger.info(f"检索到{len(documents)}条相关规则")
            return rules
            
        except Exception as e:
            logger.error(f"检索规则失败: {str(e)}")
            return ""
    
    def calculate_score(self, certificate_text: str, student_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """计算证书加分（新接口）
        
        Args:
            certificate_text: 证书文本内容
            student_info: 学生信息（可选）
            
        Returns:
            计算结果字典
        """
        try:
            rules = self._retrieve_rules(certificate_text)
            
            if rules:
                calculation_prompt = f"""
请根据以下证书信息和相关规则计算加分：

证书内容: {certificate_text}
学生信息: {student_info or '无'}

相关规则：
{rules}

请提供以下信息，并以JSON格式返回：
{{
    "category": "证书类别",
    "score": 证书加分值 (0-10分),
    "rules": "匹配的规则条文",
    "confidence": 匹配置信度 (0.0-1.0),
    "explanation": "加分说明"
}}
"""
                logger.info(f"证书加分计算使用RAG增强，检索到{len(rules)}字符规则")
            else:
                calculation_prompt = f"""
请根据以下证书信息计算加分：

证书内容: {certificate_text}
学生信息: {student_info or '无'}

请提供以下信息，并以JSON格式返回：
{{
    "category": "证书类别",
    "score": 证书加分值 (0-10分),
    "rules": "匹配的规则条文",
    "confidence": 匹配置信度 (0.0-1.0),
    "explanation": "加分说明"
}}
"""
                logger.warning("证书加分计算未使用RAG，直接计算")
            
            response = self.llm_manager.generate(calculation_prompt)
            
            category = "其他"
            score = 5.0
            rules_matched = "根据证书内容进行评估"
            confidence = 0.8
            explanation = response
            
            try:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    result_data = json.loads(json_match.group())
                    category = result_data.get("category", category)
                    score = float(result_data.get("score", score))
                    rules_matched = result_data.get("rules", rules_matched)
                    confidence = float(result_data.get("confidence", confidence))
                    explanation = result_data.get("explanation", explanation)
            except Exception as e:
                logger.warning(f"解析LLM响应失败: {e}")
            
            return {
                "category": category,
                "score": score,
                "rules": rules_matched,
                "confidence": confidence,
                "explanation": explanation,
                "certificate_text": certificate_text,
                "calculated_at": datetime.now().isoformat(),
                "used_rag": bool(rules)
            }
            
        except Exception as e:
            logger.error(f"证书加分计算失败: {str(e)}")
            raise
    
    def calculate_points(self, student_id: str, certificate_type: str, 
                        certificate_level: str, certificate_name: str, 
                        issue_date: str, certificate_file: Optional[str] = None) -> Dict[str, Any]:
        """计算证书加分
        
        Args:
            student_id: 学生ID
            certificate_type: 证书类型
            certificate_level: 证书级别
            certificate_name: 证书名称
            issue_date: 颁发日期
            certificate_file: 证书文件（可选）
            
        Returns:
            计算结果字典
        """
        try:
            query = f"{certificate_name} {certificate_type} {certificate_level}"
            rules = self._retrieve_rules(query)
            
            if rules:
                calculation_prompt = f"""
请根据以下证书信息和相关规则计算加分：

证书名称: {certificate_name}
证书类型: {certificate_type}
证书级别: {certificate_level}
颁发日期: {issue_date}

相关规则：
{rules}

请提供以下信息，并以JSON格式返回：
{{
    "points": 证书加分值 (0-10分),
    "reason": "加分理由",
    "rarity": "证书稀有度评估",
    "recognition": "行业认可度评估",
    "job_help": "对求职的帮助程度"
}}
"""
                logger.info(f"证书加分计算使用RAG增强，检索到{len(rules)}字符规则")
            else:
                calculation_prompt = f"""
请根据以下证书信息计算加分：

证书名称: {certificate_name}
证书类型: {certificate_type}
证书级别: {certificate_level}
颁发日期: {issue_date}

请提供以下信息，并以JSON格式返回：
{{
    "points": 证书加分值 (0-10分),
    "reason": "加分理由",
    "rarity": "证书稀有度评估",
    "recognition": "行业认可度评估",
    "job_help": "对求职的帮助程度"
}}
"""
                logger.warning("证书加分计算未使用RAG，直接计算")
            
            response = self.llm_manager.generate(calculation_prompt)
            
            points = 5
            try:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    result_data = json.loads(json_match.group())
                    points = result_data.get("points", 5)
            except Exception as e:
                logger.warning(f"解析LLM响应失败: {e}")
            
            return {
                "student_id": student_id,
                "certificate_type": certificate_type,
                "certificate_level": certificate_level,
                "certificate_name": certificate_name,
                "issue_date": issue_date,
                "points": points,
                "analysis": response,
                "calculated_at": datetime.now().isoformat(),
                "used_rag": bool(rules)
            }
            
        except Exception as e:
            logger.error(f"证书加分计算失败: {str(e)}")
            raise
    
    def analyze_certificate(self, certificate_type: str, certificate_level: str,
                           certificate_name: str, issue_date: str) -> Dict[str, Any]:
        """分析证书
        
        Args:
            certificate_type: 证书类型
            certificate_level: 证书级别
            certificate_name: 证书名称
            issue_date: 颁发日期
            
        Returns:
            分析结果字典
        """
        try:
            query = f"{certificate_name} {certificate_type} {certificate_level}"
            rules = self._retrieve_rules(query)
            
            if rules:
                analysis_prompt = f"""
请分析以下证书信息：

证书名称: {certificate_name}
证书类型: {certificate_type}
证书级别: {certificate_level}
颁发日期: {issue_date}

相关规则：
{rules}

请提供以下分析：
1. 证书价值评估
2. 适用行业和岗位
3. 获取难度
4. 职业发展帮助
5. 建议和备注
"""
                logger.info(f"证书分析使用RAG增强，检索到{len(rules)}字符规则")
            else:
                analysis_prompt = f"""
请分析以下证书信息：

证书名称: {certificate_name}
证书类型: {certificate_type}
证书级别: {certificate_level}
颁发日期: {issue_date}

请提供以下分析：
1. 证书价值评估
2. 适用行业和岗位
3. 获取难度
4. 职业发展帮助
5. 建议和备注
"""
                logger.warning("证书分析未使用RAG，直接分析")
            
            response = self.llm_manager.generate(analysis_prompt)
            
            return {
                "certificate_name": certificate_name,
                "certificate_type": certificate_type,
                "certificate_level": certificate_level,
                "analysis": response,
                "timestamp": datetime.now().isoformat(),
                "used_rag": bool(rules)
            }
            
        except Exception as e:
            logger.error(f"证书分析失败: {str(e)}")
            raise

"""
综测计算RAG检索服务
负责调用RAG进行规则检索并解析JSON结果
"""
import json
import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx

from app.core.logger import get_logger
from app.core.comprehensive_prompts import comprehensive_score_prompts

logger = get_logger(__name__)


class RAGComprehensiveService:
    """综测计算RAG检索服务"""
    
    def __init__(self, rag_base_url: str = "http://localhost:8000"):
        """初始化服务
        
        Args:
            rag_base_url: RAG服务基础URL
        """
        self.rag_base_url = rag_base_url
        self.client = httpx.AsyncClient(timeout=120.0)
        logger.info(f"RAG综测服务初始化完成, URL: {rag_base_url}")
    
    async def close(self):
        """关闭连接"""
        await self.client.aclose()
    
    def _log_data_trace(self, step: str, data: Any, level: str = "info"):
        """数据追踪日志
        
        Args:
            step: 处理步骤名称
            data: 数据内容
            level: 日志级别
        """
        log_msg = f"[数据追踪] {step}"
        
        if isinstance(data, (dict, list)):
            try:
                data_str = json.dumps(data, ensure_ascii=False, indent=2)
                if len(data_str) > 500:
                    data_str = data_str[:500] + "..."
            except Exception:
                data_str = str(data)[:500]
        else:
            data_str = str(data)[:500]
        
        if level == "debug":
            logger.debug(f"{log_msg}\n数据: {data_str}")
        elif level == "warning":
            logger.warning(f"{log_msg}\n数据: {data_str}")
        elif level == "error":
            logger.error(f"{log_msg}\n数据: {data_str}")
        else:
            logger.info(f"{log_msg}\n数据: {data_str}")
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """解析AI返回的JSON响应
        
        Args:
            response_text: AI返回的文本
            
        Returns:
            解析后的字典
        """
        self._log_data_trace("JSON解析-原始响应", response_text[:500])
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                self._log_data_trace("JSON解析-成功", result)
                return result
        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析失败: {e}")
        
        try:
            code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
            if code_block_match:
                json_str = code_block_match.group(1)
                result = json.loads(json_str)
                self._log_data_trace("JSON解析-代码块提取成功", result)
                return result
        except json.JSONDecodeError as e:
            logger.warning(f"代码块JSON解析失败: {e}")
        
        logger.error("无法解析JSON响应")
        return {
            "success": False,
            "error": "无法解析JSON响应",
            "raw_response": response_text[:500]
        }
    
    async def retrieve_rules(self, query: str) -> Dict[str, Any]:
        """检索综测规则
        
        Args:
            query: 查询问题
            
        Returns:
            检索结果
        """
        self._log_data_trace("规则检索-开始", {"query": query})
        
        try:
            prompt = comprehensive_score_prompts.get_rule_retrieval_prompt(query)
            
            response = await self.client.post(
                f"{self.rag_base_url}/api/v1/chat",
                json={
                    "message": prompt,
                    "chat_history": [],
                    "use_rag": True
                }
            )
            
            if response.status_code != 200:
                logger.error(f"RAG请求失败: {response.status_code}")
                return {"success": False, "error": f"RAG请求失败: {response.status_code}"}
            
            result = response.json()
            self._log_data_trace("规则检索-RAG响应", result)
            
            answer = result.get("answer", result.get("response", ""))
            parsed = self._parse_json_response(answer)
            
            return {
                "success": True,
                "rules": parsed.get("rules", []),
                "query": query,
                "retrieved_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"规则检索失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def analyze_certificate(
        self, 
        certificate_text: str, 
        student_info: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """分析证书并计算加分
        
        Args:
            certificate_text: 证书OCR文本
            student_info: 学生信息
            
        Returns:
            分析结果
        """
        self._log_data_trace("证书分析-开始", {
            "certificate_text": certificate_text[:200],
            "student_info": student_info
        })
        
        try:
            prompt = comprehensive_score_prompts.get_certificate_analysis_prompt(
                certificate_text, student_info
            )
            
            response = await self.client.post(
                f"{self.rag_base_url}/api/v1/chat",
                json={
                    "message": prompt,
                    "chat_history": [],
                    "use_rag": True
                }
            )
            
            if response.status_code != 200:
                logger.error(f"RAG请求失败: {response.status_code}")
                return {"success": False, "error": f"RAG请求失败: {response.status_code}"}
            
            result = response.json()
            self._log_data_trace("证书分析-RAG响应", result)
            
            answer = result.get("answer", result.get("response", ""))
            parsed = self._parse_json_response(answer)
            
            if parsed.get("success"):
                return {
                    "success": True,
                    "category": parsed.get("category", "C"),
                    "sub_category": parsed.get("sub_category", "C1"),
                    "score": float(parsed.get("score", 0)),
                    "level": parsed.get("level", ""),
                    "certificate_type": parsed.get("certificate_type", ""),
                    "certificate_name": parsed.get("certificate_name", ""),
                    "rules_matched": parsed.get("rules_matched", []),
                    "confidence": float(parsed.get("confidence", 0.8)),
                    "explanation": parsed.get("explanation", ""),
                    "analyzed_at": datetime.now().isoformat()
                }
            
            return parsed
            
        except Exception as e:
            logger.error(f"证书分析失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def calculate_student_score(
        self,
        student_id: str,
        student_name: str,
        class_name: str,
        academic_info: Dict[str, Any],
        certificate_info: List[Dict],
        score_details: List[Dict]
    ) -> Dict[str, Any]:
        """计算学生综测成绩
        
        Args:
            student_id: 学号
            student_name: 姓名
            class_name: 班级
            academic_info: 学业成绩信息
            certificate_info: 证书信息列表
            score_details: 加减分明细
            
        Returns:
            计算结果
        """
        self._log_data_trace("综测计算-开始", {
            "student_id": student_id,
            "student_name": student_name,
            "academic_info": academic_info,
            "certificate_count": len(certificate_info),
            "detail_count": len(score_details)
        })
        
        try:
            prompt = comprehensive_score_prompts.get_batch_calculation_prompt(
                student_id, student_name, class_name,
                academic_info, certificate_info, score_details
            )
            
            response = await self.client.post(
                f"{self.rag_base_url}/api/v1/chat",
                json={
                    "message": prompt,
                    "chat_history": [],
                    "use_rag": True
                }
            )
            
            if response.status_code != 200:
                logger.error(f"RAG请求失败: {response.status_code}")
                return {"success": False, "error": f"RAG请求失败: {response.status_code}"}
            
            result = response.json()
            self._log_data_trace("综测计算-RAG响应", result)
            
            answer = result.get("answer", result.get("response", ""))
            parsed = self._parse_json_response(answer)
            
            if parsed.get("success"):
                scores = parsed.get("scores", {})
                self._log_data_trace("综测计算-分数详情", scores)
                
                return {
                    "success": True,
                    "student_id": student_id,
                    "student_name": student_name,
                    "scores": scores,
                    "total_score": scores.get("total_score", 0),
                    "rank_info": parsed.get("rank_info", {}),
                    "details": parsed.get("details", []),
                    "calculated_at": datetime.now().isoformat()
                }
            
            return parsed
            
        except Exception as e:
            logger.error(f"综测计算失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def get_weight_config(
        self, 
        academic_year: str, 
        semester: str
    ) -> Dict[str, Any]:
        """获取权重配置
        
        Args:
            academic_year: 学年
            semester: 学期
            
        Returns:
            配置信息
        """
        self._log_data_trace("获取权重配置-开始", {
            "academic_year": academic_year,
            "semester": semester
        })
        
        try:
            prompt = comprehensive_score_prompts.get_weight_config_prompt(
                academic_year, semester
            )
            
            response = await self.client.post(
                f"{self.rag_base_url}/api/v1/chat",
                json={
                    "message": prompt,
                    "chat_history": [],
                    "use_rag": True
                }
            )
            
            if response.status_code != 200:
                logger.error(f"RAG请求失败: {response.status_code}")
                return self._get_default_config()
            
            result = response.json()
            answer = result.get("answer", result.get("response", ""))
            parsed = self._parse_json_response(answer)
            
            if parsed.get("success"):
                config = parsed.get("config", {})
                self._log_data_trace("权重配置-获取成功", config)
                return {
                    "success": True,
                    "config": config,
                    "source": parsed.get("source", "RAG")
                }
            
            return self._get_default_config()
            
        except Exception as e:
            logger.error(f"获取权重配置失败: {e}", exc_info=True)
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        default_config = {
            "name": "默认配置",
            "a_weight": 20.0,
            "b_weight": 70.0,
            "c_weight": 10.0,
            "academic_score_field": "weighted_average",
            "academic_score_scale": 1.0,
            "rules": {
                "a_max_score": 100,
                "c_max_score_per_item": 12,
                "level_scores": {
                    "国家级": 12,
                    "省级": 8,
                    "校级": 5,
                    "院级": 3
                }
            }
        }
        self._log_data_trace("使用默认配置", default_config)
        return {
            "success": True,
            "config": default_config,
            "source": "默认配置"
        }
    
    async def generate_excel_fill_data(
        self,
        raw_data: str,
        student_list: List[Dict]
    ) -> Dict[str, Any]:
        """生成Excel填充数据
        
        Args:
            raw_data: 原始数据（OCR识别或成绩单）
            student_list: 学生列表
            
        Returns:
            填充数据
        """
        self._log_data_trace("生成Excel填充数据-开始", {
            "raw_data_length": len(raw_data),
            "student_count": len(student_list)
        })
        
        try:
            prompt = comprehensive_score_prompts.get_excel_fill_prompt(
                raw_data, student_list
            )
            
            response = await self.client.post(
                f"{self.rag_base_url}/api/v1/chat",
                json={
                    "message": prompt,
                    "chat_history": [],
                    "use_rag": True
                }
            )
            
            if response.status_code != 200:
                logger.error(f"RAG请求失败: {response.status_code}")
                return {"success": False, "error": f"RAG请求失败: {response.status_code}"}
            
            result = response.json()
            self._log_data_trace("Excel填充-RAG响应", result)
            
            answer = result.get("answer", result.get("response", ""))
            parsed = self._parse_json_response(answer)
            
            if parsed.get("success"):
                fill_data = parsed.get("fill_data", [])
                self._log_data_trace("Excel填充数据-生成成功", {
                    "fill_count": len(fill_data)
                })
                
                return {
                    "success": True,
                    "fill_data": fill_data,
                    "summary": parsed.get("summary", {}),
                    "generated_at": datetime.now().isoformat()
                }
            
            return parsed
            
        except Exception as e:
            logger.error(f"生成Excel填充数据失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}


rag_comprehensive_service = RAGComprehensiveService()


def get_rag_comprehensive_service() -> RAGComprehensiveService:
    """获取RAG综测服务实例"""
    return rag_comprehensive_service

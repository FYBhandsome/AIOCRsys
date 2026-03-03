"""
综测计算RAG检索服务
负责调用RAG进行规则检索并解析JSON结果
"""
import json
import re
import logging
import time
import asyncio
import traceback
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx

from app.core.logger import get_logger, sanitize_for_logging, APILogMiddleware, log_function_call, create_context_logger
from app.core.comprehensive_prompts import comprehensive_score_prompts

logger = get_logger(__name__)
api_logger = APILogMiddleware("RAGService")


class RAGComprehensiveService:
    """综测计算RAG检索服务"""
    
    def __init__(self, rag_base_url: str = "http://localhost:8000"):
        """初始化服务
        
        Args:
            rag_base_url: RAG服务基础URL
        """
        self.rag_base_url = rag_base_url
        self.client = httpx.AsyncClient(timeout=120.0)
        logger.info(f"[服务初始化] RAG综测服务初始化完成, URL: {rag_base_url}")
    
    async def close(self):
        """关闭连接"""
        await self.client.aclose()
        logger.info("[服务关闭] RAG客户端连接已关闭")
    
    def _log_data_trace(self, step: str, data: Any, level: str = "info"):
        """数据追踪日志
        
        Args:
            step: 处理步骤名称
            data: 数据内容
            level: 日志级别
        """
        log_msg = f"[数据追踪] {step}"
        data_str = sanitize_for_logging(data, max_length=500)
        
        if level == "debug":
            logger.debug(f"{log_msg} | 数据: {data_str}")
        elif level == "warning":
            logger.warning(f"{log_msg} | 数据: {data_str}")
        elif level == "error":
            logger.error(f"{log_msg} | 数据: {data_str}")
        else:
            logger.info(f"{log_msg} | 数据: {data_str}")
    
    def _log_branch_decision(self, branch_name: str, condition: bool, context: str = ""):
        """记录分支判断"""
        logger.info(f"[分支判断] {context} | 分支: {branch_name} | 结果: {condition}")
    
    def _log_variable(self, var_name: str, var_value: Any, context: str = ""):
        """记录变量值"""
        logger.debug(f"[变量记录] {context} | 变量: {var_name} | 值: {sanitize_for_logging(var_value)}")
    
    def _clean_json_string(self, json_str: str) -> str:
        """清理JSON字符串中的常见问题
        
        Args:
            json_str: 原始JSON字符串
            
        Returns:
            清理后的JSON字符串
        """
        json_str = json_str.strip()
        json_str = re.sub(r'^```json\s*', '', json_str)
        json_str = re.sub(r'^```\s*', '', json_str)
        json_str = re.sub(r'\s*```$', '', json_str)
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_str)
        
        return json_str
    
    def _extract_json_multiple_methods(self, response_text: str) -> tuple:
        """使用多种方法尝试提取JSON
        
        Args:
            response_text: AI返回的文本
            
        Returns:
            (json_str, method_name) 或 (None, None)
        """
        method1 = re.search(r'^\s*\{[\s\S]*\}\s*$', response_text.strip())
        if method1:
            return method1.group().strip(), "纯JSON直接匹配"
        
        method2 = re.search(r'\{[\s\S]*\}', response_text)
        if method2:
            return method2.group(), "正则提取首个JSON对象"
        
        method3 = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
        if method3:
            return method3.group(1).strip(), "Markdown代码块提取"
        
        lines = response_text.strip().split('\n')
        json_lines = []
        in_json = False
        brace_count = 0
        
        for line in lines:
            if '{' in line:
                in_json = True
            if in_json:
                json_lines.append(line)
                brace_count += line.count('{') - line.count('}')
                if brace_count == 0:
                    break
        
        if json_lines:
            return '\n'.join(json_lines), "逐行解析提取"
        
        return None, None
    
    def _parse_json_response(self, response_text: str, default_value: Dict[str, Any] = None) -> Dict[str, Any]:
        """解析AI返回的JSON响应（增强版）
        
        Args:
            response_text: AI返回的文本
            default_value: 解析失败时的默认返回值
            
        Returns:
            解析后的字典
        """
        self._log_data_trace("JSON解析-原始响应", response_text[:500] if response_text else "空响应")
        
        if not response_text:
            logger.warning("[JSON解析] 响应为空")
            return default_value or {"success": False, "error": "响应为空"}
        
        json_str, method = self._extract_json_multiple_methods(response_text)
        
        if not json_str:
            logger.error("[JSON解析] 无法提取JSON内容")
            return default_value or {
                "success": False,
                "error": "无法提取JSON内容",
                "raw_response": response_text[:500]
            }
        
        self._log_data_trace(f"JSON解析-提取方法: {method}", json_str[:300])
        
        json_str = self._clean_json_string(json_str)
        
        try:
            result = json.loads(json_str)
            self._log_branch_decision(f"JSON解析成功({method})", True, "JSON解析")
            self._log_data_trace("JSON解析-成功", result)
            return result
        except json.JSONDecodeError as e:
            self._log_branch_decision(f"JSON解析失败({method})", False, "JSON解析")
            logger.warning(f"[JSON解析] 解析失败: {e}, 尝试修复...")
            
            try:
                fixed_str = self._repair_json(json_str)
                result = json.loads(fixed_str)
                self._log_branch_decision("JSON修复后解析", True, "JSON解析")
                logger.info("[JSON解析] 修复后解析成功")
                return result
            except Exception as repair_error:
                logger.error(f"[JSON解析] 修复后仍失败: {repair_error}")
        
        logger.error("[JSON解析] 所有解析方法均失败")
        return default_value or {
            "success": False,
            "error": "JSON解析失败",
            "raw_response": response_text[:500]
        }
    
    def _repair_json(self, json_str: str) -> str:
        """尝试修复常见的JSON格式问题
        
        Args:
            json_str: 有问题的JSON字符串
            
        Returns:
            修复后的JSON字符串
        """
        json_str = re.sub(r'(?<!\\)"([^"]*)"(\s*:)', r'"\1"\2', json_str)
        json_str = re.sub(r':\s*"([^"]*)"(\s*[,}\]])', r': "\1"\2', json_str)
        json_str = re.sub(r':\s*([^"{\[\d][^,}\]]*)(\s*[,}\]])', r': "\1"\2', json_str)
        json_str = re.sub(r'\\(?!["\\/bfnrt])', r'\\\\', json_str)
        json_str = re.sub(r'"([^"]*)"([^":,}\]\s])', r'"\1"\2', json_str)
        
        return json_str
    
    async def _call_rag_with_retry(
        self, 
        prompt: str, 
        max_retries: int = 3,
        retry_delay: float = 1.0,
        default_response: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """带重试机制的RAG调用
        
        Args:
            prompt: 提示词
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            default_response: 最终失败时的默认响应
            
        Returns:
            RAG响应结果
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                self._log_data_trace(f"RAG调用-尝试 {attempt + 1}/{max_retries}", {"prompt_length": len(prompt)})
                
                response = await self.client.post(
                    f"{self.rag_base_url}/api/v1/chat",
                    json={
                        "message": prompt,
                        "chat_history": [],
                        "use_rag": True
                    }
                )
                
                if response.status_code != 200:
                    error_msg = f"RAG请求失败: HTTP {response.status_code}"
                    logger.warning(f"[RAG重试] {error_msg}, 尝试 {attempt + 1}/{max_retries}")
                    last_error = error_msg
                    
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                        continue
                    break
                
                result = response.json()
                answer = result.get("answer", result.get("response", ""))
                
                parsed = self._parse_json_response(answer, default_response)
                
                if parsed.get("success"):
                    self._log_data_trace(f"RAG调用成功-第{attempt + 1}次尝试", parsed)
                    return parsed
                else:
                    last_error = parsed.get("error", "未知错误")
                    logger.warning(f"[RAG重试] JSON解析失败: {last_error}, 尝试 {attempt + 1}/{max_retries}")
                    
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                        continue
                        
            except Exception as e:
                last_error = str(e)
                logger.error(f"[RAG重试] 异常: {e}, 尝试 {attempt + 1}/{max_retries}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
        
        logger.error(f"[RAG重试] 所有重试均失败: {last_error}")
        return default_response or {"success": False, "error": f"重试失败: {last_error}"}
    
    async def retrieve_rules(self, query: str) -> Dict[str, Any]:
        """检索综测规则
        
        Args:
            query: 查询问题
            
        Returns:
            检索结果
        """
        func_name = "retrieve_rules"
        logger.info(f"[函数进入] {func_name} | 参数: query={sanitize_for_logging(query)}")
        start_time = time.time()
        
        self._log_data_trace("规则检索-开始", {"query": query})
        
        try:
            prompt = comprehensive_score_prompts.get_rule_retrieval_prompt(query)
            self._log_variable("prompt", prompt[:200], func_name)
            
            api_logger.log_business_operation(
                "RAG规则检索",
                {"query": query, "endpoint": f"{self.rag_base_url}/api/v1/chat"}
            )
            
            response = await self.client.post(
                f"{self.rag_base_url}/api/v1/chat",
                json={
                    "message": prompt,
                    "chat_history": [],
                    "use_rag": True
                }
            )
            
            self._log_variable("response_status", response.status_code, func_name)
            
            if response.status_code != 200:
                error_msg = f"RAG请求失败: {response.status_code}"
                logger.error(f"[{func_name}] {error_msg}")
                api_logger.log_error("POST", f"{self.rag_base_url}/api/v1/chat", 
                                    Exception(error_msg), {"query": query})
                return {"success": False, "error": error_msg}
            
            result = response.json()
            self._log_data_trace("规则检索-RAG响应", result)
            
            answer = result.get("answer", result.get("response", ""))
            parsed = self._parse_json_response(answer)
            
            elapsed = (time.time() - start_time) * 1000
            logger.info(f"[函数退出] {func_name} | 耗时: {elapsed:.2f}ms | 结果: success={parsed.get('success', False)}")
            
            return {
                "success": True,
                "rules": parsed.get("rules", []),
                "query": query,
                "retrieved_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            logger.error(f"[函数异常] {func_name} | 耗时: {elapsed:.2f}ms | 异常: {type(e).__name__}: {str(e)}\n{traceback.format_exc()}")
            api_logger.log_error("POST", f"{self.rag_base_url}/api/v1/chat", e, {"query": query})
            return {"success": False, "error": str(e)}
    
    async def analyze_certificate(
        self, 
        certificate_text: str, 
        student_info: Dict[str, Any] = None,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """分析证书并计算加分
        
        Args:
            certificate_text: 证书OCR文本
            student_info: 学生信息
            max_retries: 最大重试次数
            
        Returns:
            分析结果
        """
        self._log_data_trace("证书分析-开始", {
            "certificate_text": certificate_text[:200],
            "student_info": student_info
        })
        
        default_response = {
            "success": False,
            "category": "C",
            "sub_category": "C1",
            "score": 0,
            "level": "",
            "certificate_type": "",
            "certificate_name": "",
            "rules_matched": [],
            "confidence": 0.0,
            "explanation": "分析失败，使用默认值"
        }
        
        try:
            prompt = comprehensive_score_prompts.get_certificate_analysis_prompt(
                certificate_text, student_info
            )
            
            parsed = await self._call_rag_with_retry(
                prompt=prompt,
                max_retries=max_retries,
                default_response=default_response
            )
            
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
            return {**default_response, "error": str(e)}
    
    async def calculate_student_score(
        self,
        student_id: str,
        student_name: str,
        class_name: str,
        academic_info: Dict[str, Any],
        certificate_info: List[Dict],
        score_details: List[Dict],
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """计算学生综测成绩
        
        Args:
            student_id: 学号
            student_name: 姓名
            class_name: 班级
            academic_info: 学业成绩信息
            certificate_info: 证书信息列表
            score_details: 加减分明细
            max_retries: 最大重试次数
            
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
        
        default_response = {
            "success": False,
            "student_id": student_id,
            "student_name": student_name,
            "scores": {
                "a_score": {"a1_score": 0, "a2_score": 0, "a3_score": 0, "a_total": 0, "a_weighted": 0},
                "b_score": {"raw_score": 0, "field_used": "", "b_weighted": 0},
                "c_score": {"c1_score": 0, "c2_score": 0, "c3_score": 0, "c4_score": 0, "c_total": 0, "c_weighted": 0},
                "total_score": 0
            },
            "total_score": 0,
            "rank_info": {},
            "details": [],
            "error": "计算失败，使用默认值"
        }
        
        try:
            prompt = comprehensive_score_prompts.get_batch_calculation_prompt(
                student_id, student_name, class_name,
                academic_info, certificate_info, score_details
            )
            
            parsed = await self._call_rag_with_retry(
                prompt=prompt,
                max_retries=max_retries,
                default_response=default_response
            )
            
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
            return {**default_response, "error": str(e)}
    
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
        student_list: List[Dict],
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """生成Excel填充数据
        
        Args:
            raw_data: 原始数据（OCR识别或成绩单）
            student_list: 学生列表
            max_retries: 最大重试次数
            
        Returns:
            填充数据
        """
        self._log_data_trace("生成Excel填充数据-开始", {
            "raw_data_length": len(raw_data),
            "student_count": len(student_list)
        })
        
        default_response = {
            "success": False,
            "fill_data": [],
            "summary": {
                "total_students": len(student_list),
                "processed": 0,
                "failed": len(student_list)
            },
            "error": "生成失败，使用默认值"
        }
        
        try:
            prompt = comprehensive_score_prompts.get_excel_fill_prompt(
                raw_data, student_list
            )
            
            parsed = await self._call_rag_with_retry(
                prompt=prompt,
                max_retries=max_retries,
                default_response=default_response
            )
            
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
            return {**default_response, "error": str(e)}


rag_comprehensive_service = RAGComprehensiveService()


def get_rag_comprehensive_service() -> RAGComprehensiveService:
    """获取RAG综测服务实例"""
    return rag_comprehensive_service

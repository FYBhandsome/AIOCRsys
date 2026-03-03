"""
字段映射服务
负责学生成绩单与综测计算表之间的字段映射
"""
import json
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import pandas as pd
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
import shutil

from app.core.logger import get_logger
from app.services.rag_comprehensive_service import get_rag_comprehensive_service

logger = get_logger(__name__)


class FieldMappingService:
    """字段映射服务"""
    
    SOURCE_FIELDS = {
        '学号': 'student_id',
        '姓名': 'student_name',
        '班级': 'class_name',
        '专业名称': 'major',
        '年级': 'grade',
        '总分': 'total_score',
        '门数': 'course_count',
        '总学分': 'total_credits',
        '获得学分': 'earned_credits',
        '算术平均分': 'arithmetic_average',
        '算术平均分排名': 'arithmetic_average_rank',
        '学分加权平均分': 'weighted_average',
        '学分加权平均分排名': 'weighted_average_rank',
        '平均学分绩点': 'average_gpa',
        '平均学分绩点排名': 'average_gpa_rank',
        '不及格门次': 'failed_count'
    }
    
    TARGET_FIELDS = {
        'A': '总排名',
        'B': '专业',
        'C': '班级',
        'D': '姓名',
        'E': '学号',
        'F': 'A1—基础分',
        'G': 'A2—附加分',
        'H': 'A3—扣分项',
        'I': '思想道德素质(A)总分',
        'J': '思想道德素质(A)总分%',
        'K': '学习成绩',
        'L': '学习成绩%',
        'M': '学习成绩70%',
        'N': 'C1—科技竞赛项目',
        'O': 'C2—体育竞技项目',
        'P': 'C3—文化类竞赛项目',
        'Q': 'C4—创新创业实践项目',
        'R': '素质拓展(C)总分',
        'S': '素质拓展(C)总分10%',
        'T': '综合测评总成绩8%',
        'U': '学生签字'
    }
    
    FIELD_MAPPING = {
        'student_id': 'E',
        'student_name': 'D',
        'class_name': 'C',
        'major': 'B',
        'weighted_average': 'K',
        'arithmetic_average': 'K',
        'average_gpa': 'K'
    }
    
    HEADER_ROW = 3
    DATA_START_ROW = 4
    
    def __init__(self):
        """初始化服务"""
        self.rag_service = get_rag_comprehensive_service()
        logger.info("字段映射服务初始化完成")
    
    def _log_data_trace(self, step: str, data: Any, level: str = "info"):
        """数据追踪日志"""
        log_msg = f"[字段映射-{step}]"
        
        if isinstance(data, (dict, list)):
            try:
                data_str = json.dumps(data, ensure_ascii=False, indent=2)
                if len(data_str) > 1000:
                    data_str = data_str[:1000] + "..."
            except Exception:
                data_str = str(data)[:1000]
        else:
            data_str = str(data)[:1000]
        
        if level == "error":
            logger.error(f"{log_msg}\n{data_str}")
        elif level == "warning":
            logger.warning(f"{log_msg}\n{data_str}")
        else:
            logger.info(f"{log_msg}\n{data_str}")
    
    def read_source_data(self, file_path: str) -> List[Dict[str, Any]]:
        """读取源数据（学生成绩单）
        
        Args:
            file_path: 成绩单文件路径
            
        Returns:
            学生数据列表
        """
        self._log_data_trace("读取源数据", {"file": file_path})
        
        try:
            df = pd.read_excel(file_path, sheet_name=0, header=0)
            
            df.columns = [str(col).strip() for col in df.columns]
            
            self._log_data_trace("源数据列名", list(df.columns))
            
            students = []
            for idx, row in df.iterrows():
                student = {}
                for cn_name, en_name in self.SOURCE_FIELDS.items():
                    if cn_name in df.columns:
                        value = row[cn_name]
                        if pd.notna(value):
                            if '学号' in cn_name or '班级' in cn_name:
                                student[en_name] = str(value).replace('.0', '')
                            elif isinstance(value, float):
                                student[en_name] = round(value, 2)
                            else:
                                student[en_name] = value
                        else:
                            student[en_name] = None
                
                if student.get('student_id'):
                    students.append(student)
                    self._log_data_trace(f"读取学生", student, "debug")
            
            self._log_data_trace("源数据读取完成", {"count": len(students)})
            return students
            
        except Exception as e:
            logger.error(f"读取源数据失败: {e}", exc_info=True)
            raise
    
    def map_fields(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """字段映射
        
        Args:
            source_data: 源数据字典
            
        Returns:
            映射后的数据字典
        """
        self._log_data_trace("字段映射-输入", source_data)
        
        mapped = {
            'student_id': source_data.get('student_id'),
            'student_name': source_data.get('student_name'),
            'class_name': source_data.get('class_name'),
            'major': source_data.get('major'),
            'grade': source_data.get('grade'),
            'academic_info': {
                'total_score': source_data.get('total_score'),
                'course_count': source_data.get('course_count'),
                'total_credits': source_data.get('total_credits'),
                'earned_credits': source_data.get('earned_credits'),
                'arithmetic_average': source_data.get('arithmetic_average'),
                'arithmetic_average_rank': source_data.get('arithmetic_average_rank'),
                'weighted_average': source_data.get('weighted_average'),
                'weighted_average_rank': source_data.get('weighted_average_rank'),
                'average_gpa': source_data.get('average_gpa'),
                'average_gpa_rank': source_data.get('average_gpa_rank'),
                'failed_count': source_data.get('failed_count')
            },
            'b_score': source_data.get('weighted_average') or source_data.get('arithmetic_average') or 0
        }
        
        self._log_data_trace("字段映射-输出", mapped)
        return mapped
    
    async def process_and_fill(
        self,
        source_file: str,
        template_file: str,
        output_dir: str,
        academic_year: str = None,
        semester: str = None,
        certificate_data: List[Dict] = None
    ) -> Dict[str, Any]:
        """处理数据并填充模板
        
        Args:
            source_file: 源数据文件（学生成绩单）
            template_file: 模板文件
            output_dir: 输出目录
            academic_year: 学年
            semester: 学期
            certificate_data: 证书数据列表
            
        Returns:
            处理结果
        """
        self._log_data_trace("开始处理", {
            "source": source_file,
            "template": template_file,
            "output": output_dir
        })
        
        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = Path(output_dir) / f"综测成绩_{academic_year or '未知'}_{timestamp}.xlsx"
            
            shutil.copy(template_file, output_file)
            
            source_students = self.read_source_data(source_file)
            self._log_data_trace("源学生数据", {"count": len(source_students)})
            
            weight_config = await self.rag_service.get_weight_config(
                academic_year or "2024-2025",
                semester or "1"
            )
            self._log_data_trace("权重配置", weight_config)
            
            wb = load_workbook(output_file)
            ws_main = wb['综合测评计算表']
            ws_detail = wb['加减分说明']
            
            processed = 0
            failed = 0
            results = []
            
            for student in source_students:
                try:
                    mapped_data = self.map_fields(student)
                    
                    row_idx = self._find_student_row(ws_main, mapped_data['student_id'])
                    
                    if not row_idx:
                        row_idx = self._get_next_empty_row(ws_main)
                    
                    cert_info = []
                    if certificate_data:
                        cert_info = [c for c in certificate_data 
                                   if c.get('student_id') == mapped_data['student_id']]
                    
                    calc_result = await self.rag_service.calculate_student_score(
                        student_id=mapped_data['student_id'],
                        student_name=mapped_data['student_name'],
                        class_name=mapped_data['class_name'] or '',
                        academic_info=mapped_data['academic_info'],
                        certificate_info=cert_info,
                        score_details=[]
                    )
                    
                    self._log_data_trace(f"计算结果-{mapped_data['student_id']}", calc_result)
                    
                    if calc_result.get('success'):
                        self._fill_student_data(ws_main, ws_detail, row_idx, mapped_data, calc_result, weight_config)
                        processed += 1
                        results.append({
                            'student_id': mapped_data['student_id'],
                            'student_name': mapped_data['student_name'],
                            'success': True,
                            'total_score': calc_result.get('total_score', 0)
                        })
                    else:
                        self._fill_basic_data(ws_main, row_idx, mapped_data, weight_config)
                        processed += 1
                        results.append({
                            'student_id': mapped_data['student_id'],
                            'student_name': mapped_data['student_name'],
                            'success': True,
                            'total_score': mapped_data['b_score']
                        })
                        
                except Exception as e:
                    failed += 1
                    logger.error(f"处理学生 {student.get('student_id')} 失败: {e}")
                    results.append({
                        'student_id': student.get('student_id'),
                        'success': False,
                        'error': str(e)
                    })
            
            self._calculate_rankings(ws_main)
            
            wb.save(output_file)
            wb.close()
            
            self._log_data_trace("处理完成", {
                "processed": processed,
                "failed": failed,
                "output": str(output_file)
            })
            
            return {
                'success': True,
                'output_file': str(output_file),
                'processed': processed,
                'failed': failed,
                'results': results,
                'weight_config': weight_config
            }
            
        except Exception as e:
            logger.error(f"处理填充失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _find_student_row(self, ws, student_id: str) -> Optional[int]:
        """查找学生所在行"""
        if not student_id:
            return None
        
        for row in range(self.DATA_START_ROW, ws.max_row + 1):
            cell_value = ws.cell(row=row, column=5).value
            if cell_value:
                cell_id = str(cell_value).replace('.0', '')
                if cell_id == student_id:
                    return row
        return None
    
    def _get_next_empty_row(self, ws) -> int:
        """获取下一个空行"""
        for row in range(self.DATA_START_ROW, ws.max_row + 100):
            if not ws.cell(row=row, column=5).value:
                return row
        return ws.max_row + 1
    
    def _fill_student_data(
        self, 
        ws_main, 
        ws_detail, 
        row: int, 
        mapped_data: Dict, 
        calc_result: Dict,
        weight_config: Dict
    ):
        """填充学生数据"""
        scores = calc_result.get('scores', {})
        a_score = scores.get('a_score', {})
        b_score = scores.get('b_score', {})
        c_score = scores.get('c_score', {})
        
        config = weight_config.get('config', {})
        a_weight = config.get('a_weight', 20.0) / 100
        b_weight = config.get('b_weight', 70.0) / 100
        c_weight = config.get('c_weight', 10.0) / 100
        
        ws_main.cell(row=row, column=1).value = row - self.DATA_START_ROW + 1
        ws_main.cell(row=row, column=2).value = mapped_data.get('major', '')
        ws_main.cell(row=row, column=3).value = mapped_data.get('class_name', '')
        ws_main.cell(row=row, column=4).value = mapped_data.get('student_name', '')
        ws_main.cell(row=row, column=5).value = mapped_data.get('student_id', '')
        
        ws_main.cell(row=row, column=6).value = a_score.get('a1_score', 0)
        ws_main.cell(row=row, column=7).value = a_score.get('a2_score', 0)
        ws_main.cell(row=row, column=8).value = a_score.get('a3_score', 0)
        
        a_total = a_score.get('a_total', 0)
        ws_main.cell(row=row, column=9).value = a_total
        ws_main.cell(row=row, column=10).value = round(a_total * a_weight, 2)
        
        b_raw = b_score.get('raw_score', mapped_data.get('b_score', 0))
        ws_main.cell(row=row, column=11).value = b_raw
        ws_main.cell(row=row, column=12).value = round(b_raw * b_weight / 70, 2) if b_raw else 0
        ws_main.cell(row=row, column=13).value = round(b_raw * b_weight, 2)
        
        ws_main.cell(row=row, column=14).value = c_score.get('c1_score', 0)
        ws_main.cell(row=row, column=15).value = c_score.get('c2_score', 0)
        ws_main.cell(row=row, column=16).value = c_score.get('c3_score', 0)
        ws_main.cell(row=row, column=17).value = c_score.get('c4_score', 0)
        
        c_total = c_score.get('c_total', 0)
        ws_main.cell(row=row, column=18).value = c_total
        ws_main.cell(row=row, column=19).value = round(c_total * c_weight, 2)
        
        total_score = calc_result.get('total_score', 0)
        ws_main.cell(row=row, column=20).value = round(total_score, 2)
        
        ws_main.cell(row=row, column=21).value = ''
        
        details = calc_result.get('details', [])
        for detail in details:
            self._add_detail_row(ws_detail, mapped_data, detail)
        
        self._log_data_trace(f"填充学生数据-{row}", {
            'student_id': mapped_data.get('student_id'),
            'a_total': a_total,
            'b_raw': b_raw,
            'c_total': c_total,
            'total': total_score
        })
    
    def _fill_basic_data(
        self, 
        ws_main, 
        row: int, 
        mapped_data: Dict,
        weight_config: Dict
    ):
        """填充基础数据（无RAG计算结果时）"""
        config = weight_config.get('config', {})
        b_weight = config.get('b_weight', 70.0) / 100
        
        ws_main.cell(row=row, column=1).value = row - self.DATA_START_ROW + 1
        ws_main.cell(row=row, column=2).value = mapped_data.get('major', '')
        ws_main.cell(row=row, column=3).value = mapped_data.get('class_name', '')
        ws_main.cell(row=row, column=4).value = mapped_data.get('student_name', '')
        ws_main.cell(row=row, column=5).value = mapped_data.get('student_id', '')
        
        b_raw = mapped_data.get('b_score', 0)
        ws_main.cell(row=row, column=11).value = b_raw
        ws_main.cell(row=row, column=12).value = round(b_raw * b_weight / 70, 2) if b_raw else 0
        ws_main.cell(row=row, column=13).value = round(b_raw * b_weight, 2)
        
        ws_main.cell(row=row, column=6).value = 100
        ws_main.cell(row=row, column=9).value = 100
        ws_main.cell(row=row, column=10).value = 20
        
        total = 20 + round(b_raw * b_weight, 2)
        ws_main.cell(row=row, column=20).value = round(total, 2)
        
        ws_main.cell(row=row, column=21).value = ''
        
        self._log_data_trace(f"填充基础数据-{row}", {
            'student_id': mapped_data.get('student_id'),
            'b_score': b_raw
        })
    
    def _add_detail_row(self, ws_detail, mapped_data: Dict, detail: Dict):
        """添加明细行"""
        row = ws_detail.max_row + 1
        
        ws_detail.cell(row=row, column=1).value = mapped_data.get('major', '')
        ws_detail.cell(row=row, column=2).value = mapped_data.get('class_name', '')
        ws_detail.cell(row=row, column=3).value = mapped_data.get('student_name', '')
        
        category = detail.get('category', '')
        item_name = detail.get('item', detail.get('item_name', ''))
        score = detail.get('score', 0)
        
        if 'A1' in category:
            ws_detail.cell(row=row, column=4).value = f"{item_name}: {score}分"
        elif 'A2' in category:
            ws_detail.cell(row=row, column=5).value = f"{item_name}: {score}分"
        elif 'A3' in category:
            ws_detail.cell(row=row, column=6).value = f"{item_name}: {score}分"
        elif 'C1' in category:
            ws_detail.cell(row=row, column=7).value = f"{item_name}: {score}分"
        elif 'C2' in category:
            ws_detail.cell(row=row, column=8).value = f"{item_name}: {score}分"
        elif 'C3' in category:
            ws_detail.cell(row=row, column=9).value = f"{item_name}: {score}分"
        elif 'C4' in category:
            ws_detail.cell(row=row, column=10).value = f"{item_name}: {score}分"
    
    def _calculate_rankings(self, ws):
        """计算排名"""
        scores = []
        
        for row in range(self.DATA_START_ROW, ws.max_row + 1):
            total = ws.cell(row=row, column=20).value
            if total is not None:
                try:
                    scores.append((row, float(total)))
                except (ValueError, TypeError):
                    pass
        
        scores.sort(key=lambda x: x[1], reverse=True)
        
        for rank, (row, score) in enumerate(scores, 1):
            ws.cell(row=row, column=1).value = rank


field_mapping_service = FieldMappingService()


def get_field_mapping_service() -> FieldMappingService:
    """获取字段映射服务实例"""
    return field_mapping_service

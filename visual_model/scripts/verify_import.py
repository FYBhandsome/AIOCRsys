#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证数据导入结果

用于查询数据库中的数据，并与Excel中的数据进行比较，验证导入结果的完整性和准确性。
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from tortoise import Tortoise, run_async
from app.models.tortoise_models import Student, AcademicScore, ComprehensiveScore
from config import settings
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ImportVerifier:
    """数据导入验证器"""
    
    def __init__(self, excel_path):
        """初始化验证器
        
        Args:
            excel_path: Excel文件路径
        """
        self.excel_path = excel_path
        self.excel_data = None
        self.db_data = {
            "students": [],
            "academic_scores": [],
            "comprehensive_scores": []
        }
        self.verification_results = {
            "total_excel_records": 0,
            "total_db_records": 0,
            "matched_records": 0,
            "mismatched_records": [],
            "missing_records": []
        }
    
    def read_excel(self):
        """读取Excel文件"""
        try:
            logger.info(f"开始读取Excel文件: {self.excel_path}")
            
            # 读取Excel文件，跳过前2行标题
            df = pd.read_excel(self.excel_path, sheet_name="综合测评计算表", skiprows=2)
            
            # 只保留前20列数据
            df = df.iloc[:, :20]
            
            # 重命名列名，使其更清晰
            df.columns = [
                "总排名", "专业", "班级", "姓名", "学号",
                "A1—基础分", "A2—附加分", "A3—扣罚分", "思想道德素质(A)总分", "思想道德素质(A)总分20%",
                "学习成绩", "学习成绩70%",
                "C1—科技类竞赛项目", "C2—体育竞技项目", "C3—文化类竞赛项目", "C4—创新创业实践项目", "素质拓展（C）总分", "素质拓展（C）总分10%",
                "综合测评总成绩", "学生签字"
            ]
            
            # 过滤掉空行
            df = df.dropna(subset=["学号"]).reset_index(drop=True)
            
            self.excel_data = df
            self.verification_results["total_excel_records"] = len(df)
            
            logger.info(f"成功读取Excel文件，共 {len(df)} 条记录")
            return True
            
        except Exception as e:
            logger.error(f"读取Excel文件失败: {e}")
            return False
    
    async def init_db(self):
        """初始化数据库连接"""
        try:
            logger.info("开始初始化数据库连接")
            
            # 配置Tortoise ORM
            await Tortoise.init(
                db_url=settings.DATABASE_URL,
                modules={'models': ['app.models.tortoise_models']}
            )
            
            logger.info("数据库连接初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"数据库连接初始化失败: {e}")
            return False
    
    async def fetch_db_data(self):
        """从数据库中获取数据"""
        try:
            logger.info("开始从数据库中获取数据")
            
            # 获取学生数据
            students = await Student.all()
            self.db_data["students"] = students
            
            # 获取学业成绩数据
            academic_scores = await AcademicScore.all()
            self.db_data["academic_scores"] = academic_scores
            
            # 获取综测成绩数据
            comprehensive_scores = await ComprehensiveScore.all()
            self.db_data["comprehensive_scores"] = comprehensive_scores
            
            self.verification_results["total_db_records"] = len(students)
            
            logger.info(f"成功从数据库中获取数据: 学生 {len(students)} 条, 学业成绩 {len(academic_scores)} 条, 综测成绩 {len(comprehensive_scores)} 条")
            return True
            
        except Exception as e:
            logger.error(f"从数据库中获取数据失败: {e}")
            return False
    
    def verify_data(self):
        """验证数据完整性和准确性"""
        try:
            logger.info("开始验证数据完整性和准确性")
            
            # 创建学号到数据库记录的映射
            student_map = {student.id: student for student in self.db_data["students"]}
            academic_score_map = {score.student_id: score for score in self.db_data["academic_scores"]}
            comprehensive_score_map = {score.student_id: score for score in self.db_data["comprehensive_scores"]}
            
            # 遍历Excel数据，验证每条记录
            for index, row in self.excel_data.iterrows():
                # 将学号转换为字符串，去除小数点
                excel_student_id = str(int(row['学号'])) if pd.notna(row['学号']) else str(row['学号'])
                
                if excel_student_id in student_map:
                    # 记录存在，验证数据准确性
                    self._verify_record(row, excel_student_id, student_map, academic_score_map, comprehensive_score_map)
                else:
                    # 记录不存在
                    self.verification_results["missing_records"].append({
                        "index": index + 1,
                        "student_id": excel_student_id,
                        "name": row['姓名'],
                        "reason": "数据库中不存在该记录"
                    })
            
            logger.info(f"数据验证完成: 匹配 {self.verification_results['matched_records']} 条, 不匹配 {len(self.verification_results['mismatched_records'])} 条, 缺失 {len(self.verification_results['missing_records'])} 条")
            return True
            
        except Exception as e:
            logger.error(f"数据验证失败: {e}")
            return False
    
    def _verify_record(self, row, student_id, student_map, academic_score_map, comprehensive_score_map):
        """验证单条记录
        
        Args:
            row: Excel数据行
            student_id: 学号
            student_map: 学生记录映射
            academic_score_map: 学业成绩记录映射
            comprehensive_score_map: 综测成绩记录映射
        """
        try:
            # 验证学生信息
            student = student_map[student_id]
            
            # 验证学业成绩
            academic_score = academic_score_map.get(student_id)
            
            # 验证综测成绩
            comprehensive_score = comprehensive_score_map.get(student_id)
            
            # 检查综合测评总成绩是否匹配（允许小数点后2位误差）
            excel_total_score = row['综合测评总成绩']
            db_total_score = student.total_score
            
            if abs(excel_total_score - db_total_score) > 0.01:
                self.verification_results["mismatched_records"].append({
                    "student_id": student_id,
                    "name": row['姓名'],
                    "field": "综合测评总成绩",
                    "excel_value": excel_total_score,
                    "db_value": db_total_score,
                    "difference": abs(excel_total_score - db_total_score)
                })
            else:
                self.verification_results["matched_records"] += 1
            
        except Exception as e:
            logger.error(f"验证记录失败 {student_id}: {e}")
            self.verification_results["mismatched_records"].append({
                "student_id": student_id,
                "name": row['姓名'],
                "reason": f"验证过程中发生错误: {str(e)}"
            })
    
    def generate_verification_report(self):
        """生成验证报告"""
        logger.info("=" * 50)
        logger.info("数据导入验证报告")
        logger.info("=" * 50)
        logger.info(f"Excel总记录数: {self.verification_results['total_excel_records']}")
        logger.info(f"数据库总记录数: {self.verification_results['total_db_records']}")
        logger.info(f"匹配记录数: {self.verification_results['matched_records']}")
        logger.info(f"不匹配记录数: {len(self.verification_results['mismatched_records'])}")
        logger.info(f"缺失记录数: {len(self.verification_results['missing_records'])}")
        
        if self.verification_results['mismatched_records']:
            logger.info("\n不匹配记录详情:")
            for i, record in enumerate(self.verification_results['mismatched_records'], 1):
                logger.info(f"  {i}. 学号: {record['student_id']}, 姓名: {record['name']}")
                if "field" in record:
                    logger.info(f"     字段: {record['field']}, Excel值: {record['excel_value']}, 数据库值: {record['db_value']}, 差异: {record['difference']:.4f}")
                else:
                    logger.info(f"     原因: {record['reason']}")
        
        if self.verification_results['missing_records']:
            logger.info("\n缺失记录详情:")
            for i, record in enumerate(self.verification_results['missing_records'], 1):
                logger.info(f"  {i}. 索引: {record['index']}, 学号: {record['student_id']}, 姓名: {record['name']}")
                logger.info(f"     原因: {record['reason']}")
        
        logger.info("\n" + "=" * 50)
        
        # 计算验证通过率
        if self.verification_results['total_excel_records'] > 0:
            pass_rate = (self.verification_results['matched_records'] / self.verification_results['total_excel_records']) * 100
            logger.info(f"验证通过率: {pass_rate:.2f}%")
            
            if pass_rate == 100:
                logger.info("✅ 数据导入完全成功，所有记录都匹配！")
            elif pass_rate >= 90:
                logger.info("✅ 数据导入基本成功，通过率较高！")
            else:
                logger.info("⚠️  数据导入存在较多问题，需要进一步检查！")
        
        logger.info("=" * 50)
    
    async def close_db(self):
        """关闭数据库连接"""
        try:
            await Tortoise.close_connections()
            logger.info("数据库连接已关闭")
        except Exception as e:
            logger.error(f"关闭数据库连接失败: {e}")


async def main():
    """主函数"""
    # Excel文件路径
    excel_path = r"d:\PaddleOCR\visual_model\data\230521班综合测评计算表格.xlsx"
    
    # 创建验证器
    verifier = ImportVerifier(excel_path)
    
    # 读取Excel文件
    if not verifier.read_excel():
        logger.error("读取Excel文件失败，验证终止")
        return
    
    # 初始化数据库连接
    if not await verifier.init_db():
        logger.error("初始化数据库连接失败，验证终止")
        return
    
    try:
        # 从数据库中获取数据
        if not await verifier.fetch_db_data():
            logger.error("从数据库中获取数据失败，验证终止")
            return
        
        # 验证数据
        if not verifier.verify_data():
            logger.error("数据验证失败")
            return
        
        # 生成验证报告
        verifier.generate_verification_report()
        
    finally:
        # 关闭数据库连接
        await verifier.close_db()


if __name__ == "__main__":
    # 运行异步主函数
    run_async(main())
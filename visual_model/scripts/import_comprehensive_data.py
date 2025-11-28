#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合测评数据导入脚本

将Excel文件中的综合测评数据导入到数据库中
"""

import os
import sys
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from tortoise import Tortoise, run_async
from app.models.tortoise_models import Student, AcademicScore, ComprehensiveScore
from config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('import_comprehensive_data.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ComprehensiveDataImporter:
    """综合测评数据导入器"""
    
    def __init__(self, excel_path: str):
        """初始化导入器
        
        Args:
            excel_path: Excel文件路径
        """
        self.excel_path = excel_path
        self.data = None
        self.import_stats = {
            "total": 0,
            "students": 0,
            "academic_scores": 0,
            "comprehensive_scores": 0,
            "errors": []
        }
    
    def read_excel(self) -> bool:
        """读取Excel文件
        
        Returns:
            bool: 是否读取成功
        """
        try:
            logger.info(f"开始读取Excel文件: {self.excel_path}")
            
            # 读取Excel文件，跳过前2行标题
            df = pd.read_excel(self.excel_path, sheet_name="综合测评计算表", skiprows=2)
            
            # 打印实际列数和列名，用于调试
            logger.info(f"Excel文件实际列数: {len(df.columns)}")
            logger.info(f"Excel文件实际列名: {list(df.columns)}")
            
            # 只保留前20列数据（根据错误信息，Excel文件只有20列）
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
            
            self.data = df
            self.import_stats["total"] = len(df)
            
            logger.info(f"成功读取Excel文件，共 {len(df)} 条记录")
            return True
            
        except Exception as e:
            logger.error(f"读取Excel文件失败: {e}")
            self.import_stats["errors"].append(f"读取Excel文件失败: {str(e)}")
            return False
    
    async def init_db(self) -> bool:
        """初始化数据库连接
        
        Returns:
            bool: 是否初始化成功
        """
        try:
            logger.info("开始初始化数据库连接")
            
            # 配置Tortoise ORM
            await Tortoise.init(
                db_url=settings.DATABASE_URL,
                modules={'models': ['app.models.tortoise_models']}
            )
            
            # 创建表（如果不存在）
            await Tortoise.generate_schemas(safe=True)
            
            logger.info("数据库连接初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"数据库连接初始化失败: {e}")
            self.import_stats["errors"].append(f"数据库连接初始化失败: {str(e)}")
            return False
    
    async def import_data(self) -> bool:
        """导入数据到数据库
        
        Returns:
            bool: 是否导入成功
        """
        if self.data is None:
            logger.error("没有读取到数据，无法导入")
            return False
        
        try:
            logger.info("开始导入数据到数据库")
            
            for index, row in self.data.iterrows():
                try:
                    logger.info(f"正在导入第 {index + 1}/{len(self.data)} 条记录: {row['姓名']}({row['学号']})")
                    
                    # 导入学生信息
                    await self._import_student(row)
                    
                    # 导入学业成绩
                    await self._import_academic_score(row)
                    
                    # 导入综测成绩
                    await self._import_comprehensive_score(row)
                    
                except Exception as e:
                    error_msg = f"导入第 {index + 1} 条记录失败: {str(e)}"
                    logger.error(error_msg)
                    self.import_stats["errors"].append(error_msg)
            
            logger.info("数据导入完成")
            return True
            
        except Exception as e:
            logger.error(f"数据导入失败: {e}")
            self.import_stats["errors"].append(f"数据导入失败: {str(e)}")
            return False
    
    async def _import_student(self, row: pd.Series) -> None:
        """导入学生信息
        
        Args:
            row: 数据行
        """
        try:
            # 将学号转换为字符串，去除小数点
            student_id = str(int(row['学号'])) if pd.notna(row['学号']) else str(row['学号'])
            
            # 将班级转换为字符串
            class_name = str(row['班级']) if pd.notna(row['班级']) else ''
            
            # 从班级中提取年级，如230521 -> 2023
            grade = class_name[:4] if len(class_name) >= 4 else ''
            
            # 检查学生是否已存在
            student = await Student.filter(id=student_id).first()
            
            if not student:
                # 创建学生记录
                student = await Student.create(
                    id=student_id,
                    name=row['姓名'],
                    college="计算机学院",  # 从Excel中无法直接获取，暂时硬编码
                    major=row['专业'],
                    class_name=class_name,
                    grade=grade,
                    total_score=row['综合测评总成绩']
                )
                logger.info(f"创建学生记录: {row['姓名']}({student_id})")
                self.import_stats["students"] += 1
            else:
                # 更新学生记录
                await student.update_from_dict({
                    "name": row['姓名'],
                    "major": row['专业'],
                    "class_name": class_name,
                    "grade": grade,
                    "total_score": row['综合测评总成绩']
                })
                await student.save()
                logger.info(f"更新学生记录: {row['姓名']}({student_id})")
                self.import_stats["students"] += 1
                
        except Exception as e:
            student_id = str(row['学号']) if pd.notna(row['学号']) else '未知'
            logger.error(f"导入学生信息失败 {student_id}: {e}")
            raise
    
    async def _import_academic_score(self, row: pd.Series) -> None:
        """导入学业成绩
        
        Args:
            row: 数据行
        """
        try:
            # 将学号转换为字符串，去除小数点
            student_id = str(int(row['学号'])) if pd.notna(row['学号']) else str(row['学号'])
            
            # 将班级转换为字符串
            class_name = str(row['班级']) if pd.notna(row['班级']) else ''
            
            # 从班级中提取年级
            grade = class_name[:4] if len(class_name) >= 4 else ''
            
            # 检查学业成绩是否已存在
            academic_score = await AcademicScore.filter(
                student_id=student_id,
                semester="2024-1",  # 暂时使用固定学期，需要根据实际情况调整
                academic_year="2023-2024"  # 暂时使用固定学年，需要根据实际情况调整
            ).first()
            
            if not academic_score:
                # 创建学业成绩记录
                academic_score = await AcademicScore.create(
                    student_id=student_id,
                    student_name=row['姓名'],
                    college="计算机学院",
                    grade=grade,
                    major=row['专业'],
                    class_name=class_name,
                    total_score=row['学习成绩'],
                    arithmetic_average=row['学习成绩'],
                    weighted_average=row['学习成绩'],
                    semester="2024-1",
                    academic_year="2023-2024"
                )
                logger.info(f"创建学业成绩记录: {row['姓名']}({student_id})")
                self.import_stats["academic_scores"] += 1
            else:
                # 更新学业成绩记录
                await academic_score.update_from_dict({
                    "student_name": row['姓名'],
                    "college": "计算机学院",
                    "grade": grade,
                    "major": row['专业'],
                    "class_name": class_name,
                    "total_score": row['学习成绩'],
                    "arithmetic_average": row['学习成绩'],
                    "weighted_average": row['学习成绩']
                })
                await academic_score.save()
                logger.info(f"更新学业成绩记录: {row['姓名']}({student_id})")
                self.import_stats["academic_scores"] += 1
                
        except Exception as e:
            student_id = str(row['学号']) if pd.notna(row['学号']) else '未知'
            logger.error(f"导入学业成绩失败 {student_id}: {e}")
            raise
    
    async def _import_comprehensive_score(self, row: pd.Series) -> None:
        """导入综测成绩
        
        Args:
            row: 数据行
        """
        try:
            # 将学号转换为字符串，去除小数点
            student_id = str(int(row['学号'])) if pd.notna(row['学号']) else str(row['学号'])
            
            # 检查综测成绩是否已存在
            comprehensive_score = await ComprehensiveScore.filter(
                student_id=student_id,
                semester="2024-1",
                academic_year="2023-2024"
            ).first()
            
            # 计算A类、B类、C类成绩
            a_total_score = row['思想道德素质(A)总分']
            b_total_score = row['学习成绩']
            c_total_score = row['素质拓展（C）总分']
            
            if not comprehensive_score:
                # 创建综测成绩记录
                comprehensive_score = await ComprehensiveScore.create(
                    student_id=student_id,
                    a_total_score=a_total_score,
                    a1_score=row['A1—基础分'],
                    a2_score=row['A2—附加分'],
                    a3_score=row['A3—扣罚分'] if pd.notna(row['A3—扣罚分']) else 0,
                    b_total_score=b_total_score,
                    c_total_score=c_total_score,
                    c1_score=row['C1—科技类竞赛项目'] if pd.notna(row['C1—科技类竞赛项目']) else 0,
                    c2_score=row['C2—体育竞技项目'] if pd.notna(row['C2—体育竞技项目']) else 0,
                    c3_score=row['C3—文化类竞赛项目'] if pd.notna(row['C3—文化类竞赛项目']) else 0,
                    c4_score=row['C4—创新创业实践项目'] if pd.notna(row['C4—创新创业实践项目']) else 0,
                    total_score=row['综合测评总成绩'],
                    semester="2024-1",
                    academic_year="2023-2024"
                )
                logger.info(f"创建综测成绩记录: {row['姓名']}({student_id})")
                self.import_stats["comprehensive_scores"] += 1
            else:
                # 更新综测成绩记录
                await comprehensive_score.update_from_dict({
                    "a_total_score": a_total_score,
                    "a1_score": row['A1—基础分'],
                    "a2_score": row['A2—附加分'],
                    "a3_score": row['A3—扣罚分'] if pd.notna(row['A3—扣罚分']) else 0,
                    "b_total_score": b_total_score,
                    "c_total_score": c_total_score,
                    "c1_score": row['C1—科技类竞赛项目'] if pd.notna(row['C1—科技类竞赛项目']) else 0,
                    "c2_score": row['C2—体育竞技项目'] if pd.notna(row['C2—体育竞技项目']) else 0,
                    "c3_score": row['C3—文化类竞赛项目'] if pd.notna(row['C3—文化类竞赛项目']) else 0,
                    "c4_score": row['C4—创新创业实践项目'] if pd.notna(row['C4—创新创业实践项目']) else 0,
                    "total_score": row['综合测评总成绩']
                })
                await comprehensive_score.save()
                logger.info(f"更新综测成绩记录: {row['姓名']}({student_id})")
                self.import_stats["comprehensive_scores"] += 1
                
        except Exception as e:
            student_id = str(row['学号']) if pd.notna(row['学号']) else '未知'
            logger.error(f"导入综测成绩失败 {student_id}: {e}")
            raise
    
    async def close_db(self) -> None:
        """关闭数据库连接"""
        try:
            await Tortoise.close_connections()
            logger.info("数据库连接已关闭")
        except Exception as e:
            logger.error(f"关闭数据库连接失败: {e}")
    
    def generate_report(self) -> None:
        """生成导入报告"""
        logger.info("=" * 50)
        logger.info("综合测评数据导入报告")
        logger.info("=" * 50)
        logger.info(f"总记录数: {self.import_stats['total']}")
        logger.info(f"成功导入学生数: {self.import_stats['students']}")
        logger.info(f"成功导入学业成绩数: {self.import_stats['academic_scores']}")
        logger.info(f"成功导入综测成绩数: {self.import_stats['comprehensive_scores']}")
        logger.info(f"错误数: {len(self.import_stats['errors'])}")
        
        if self.import_stats['errors']:
            logger.info("错误详情:")
            for i, error in enumerate(self.import_stats['errors'], 1):
                logger.info(f"  {i}. {error}")
        
        logger.info("=" * 50)


async def main():
    """主函数"""
    # Excel文件路径
    excel_path = "d:\\PaddleOCR\\visual_model\\data\\230521班综合测评计算表格.xlsx"
    
    # 创建导入器
    importer = ComprehensiveDataImporter(excel_path)
    
    # 读取Excel文件
    if not importer.read_excel():
        logger.error("读取Excel文件失败，导入终止")
        return
    
    # 初始化数据库连接
    if not await importer.init_db():
        logger.error("初始化数据库连接失败，导入终止")
        return
    
    try:
        # 导入数据
        if not await importer.import_data():
            logger.error("数据导入失败")
        else:
            logger.info("数据导入成功")
    finally:
        # 关闭数据库连接
        await importer.close_db()
        
        # 生成导入报告
        importer.generate_report()


if __name__ == "__main__":
    # 运行异步主函数
    run_async(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据初始化脚本
准备完整的测试数据用于综测系统功能测试
"""
import os
import sys
import json
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = Path("D:/PaddleOCR/visual_model/data/database.db")
TEST_DATA_DIR = Path("D:/PaddleOCR/visual_model/data")
TEST_PHOTO_DIR = Path("D:/PaddleOCR/visual_model/testphoto")


def init_test_photos():
    """初始化测试图片目录"""
    TEST_PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    
    # 创建测试图片说明文件
    readme_content = """# 测试图片目录

此目录用于存放测试用的证书图片。

## 测试用例

1. 正常证书图片：
   - test_certificate_1.jpg - 科技竞赛证书
   - test_certificate_2.jpg - 英语等级证书
   - test_certificate_3.jpg - 体育竞赛证书

2. 边界情况：
   - large_file.jpg - 大于10MB的图片（测试文件大小限制）
   - invalid_format.txt - 非图片文件（测试格式验证）

3. 异常情况：
   - corrupted.jpg - 损坏的图片文件
   - empty.jpg - 空文件

## 图片要求

- 格式：JPG, PNG, PDF
- 大小：不超过10MB
- 内容：清晰的证书照片
"""
    
    readme_path = TEST_PHOTO_DIR / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"测试图片目录已创建: {TEST_PHOTO_DIR}")


def init_test_database():
    """初始化测试数据库数据"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("初始化测试数据...")
    
    # 插入测试班级
    test_classes = [
        ("230521", "230521班", "2023", "计算机科学与技术", "计算机学院"),
        ("230522", "230522班", "2023", "软件工程", "计算机学院"),
        ("test_class_001", "测试班级2023级1班", "2023", "计算机科学与技术", "计算机学院"),
    ]
    
    for cls in test_classes:
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO classes (id, name, grade, major, college)
                VALUES (?, ?, ?, ?, ?)
            """, cls)
        except Exception as e:
            print(f"插入班级失败: {e}")
    
    print(f"  - 插入 {len(test_classes)} 个测试班级")
    
    # 插入测试学生
    test_students = [
        ("202300502120", "张三", "男", "计算机学院", "计算机科学与技术", "230521", "2023"),
        ("202300502121", "李四", "女", "计算机学院", "计算机科学与技术", "230521", "2023"),
        ("202300502122", "王五", "男", "计算机学院", "计算机科学与技术", "230521", "2023"),
        ("202300502123", "赵六", "女", "计算机学院", "计算机科学与技术", "230521", "2023"),
        ("202300502124", "钱七", "男", "计算机学院", "计算机科学与技术", "230521", "2023"),
    ]
    
    for student in test_students:
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO students (id, name, gender, college, major, class_name, grade)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, student)
        except Exception as e:
            print(f"插入学生失败: {e}")
    
    print(f"  - 插入 {len(test_students)} 个测试学生")
    
    # 插入测试用户
    test_users = [
        ("admin", "admin123", "admin", "admin@test.com", "系统管理员"),
        ("teacher001", "teacher123", "teacher", "teacher@test.com", "测试教师"),
        ("202300502120", "student123", "student", "student@test.com", "张三"),
    ]
    
    for user in test_users:
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO users (username, password_hash, role, email, phone)
                VALUES (?, ?, ?, ?, ?)
            """, user)
        except Exception as e:
            print(f"插入用户失败: {e}")
    
    print(f"  - 插入 {len(test_users)} 个测试用户")
    
    # 插入学业成绩
    test_scores = [
        (1, "202300502120", "张三", 85.5, 12, 32.0, 32.0, 85.5, 5, 86.2, 4, 3.45, 4, 0, "1", "2024-2025", "学生成绩单.xlsx"),
        (2, "202300502121", "李四", 88.0, 12, 32.0, 32.0, 88.0, 3, 88.5, 3, 3.55, 3, 0, "1", "2024-2025", "学生成绩单.xlsx"),
        (3, "202300502122", "王五", 82.3, 12, 32.0, 32.0, 82.3, 8, 83.0, 7, 3.30, 7, 1, "1", "2024-2025", "学生成绩单.xlsx"),
        (4, "202300502123", "赵六", 90.2, 12, 32.0, 32.0, 90.2, 1, 90.8, 1, 3.65, 1, 0, "1", "2024-2025", "学生成绩单.xlsx"),
        (5, "202300502124", "钱七", 78.5, 12, 32.0, 30.0, 78.5, 15, 79.0, 14, 3.10, 15, 2, "1", "2024-2025", "学生成绩单.xlsx"),
    ]
    
    for score in test_scores:
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO academic_scores 
                (id, student_id, student_name, total_score, course_count, total_credits, earned_credits,
                 arithmetic_average, arithmetic_average_rank, weighted_average, weighted_average_rank,
                 average_gpa, average_gpa_rank, failed_course_count, semester, academic_year, source_file)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, score)
        except Exception as e:
            print(f"插入成绩失败: {e}")
    
    print(f"  - 插入 {len(test_scores)} 条学业成绩")
    
    # 插入综测成绩
    test_comprehensive = [
        (1, "202300502120", "张三", "230521", "计算机科学与技术", 100, 5, 0, 105, 21.0, 86.2, 60.34, 8, 0, 0, 0, 8, 0.8, 82.14, 4, "1", "2024-2025"),
        (2, "202300502121", "李四", "230521", "计算机科学与技术", 100, 8, 0, 108, 21.6, 88.5, 61.95, 12, 0, 0, 0, 12, 1.2, 84.75, 2, "1", "2024-2025"),
        (3, "202300502122", "王五", "230521", "计算机科学与技术", 100, 0, -2, 98, 19.6, 83.0, 58.10, 5, 0, 0, 0, 5, 0.5, 78.20, 7, "1", "2024-2025"),
        (4, "202300502123", "赵六", "230521", "计算机科学与技术", 100, 10, 0, 110, 22.0, 90.8, 63.56, 15, 0, 0, 0, 15, 1.5, 87.06, 1, "1", "2024-2025"),
        (5, "202300502124", "钱七", "230521", "计算机科学与技术", 100, 0, 0, 100, 20.0, 79.0, 55.30, 3, 0, 0, 0, 3, 0.3, 75.60, 5, "1", "2024-2025"),
    ]
    
    for comp in test_comprehensive:
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO comprehensive_scores 
                (id, student_id, student_name, class_name, major,
                 a1_score, a2_score, a3_score, a_total_score, a_weighted_score,
                 b_raw_score, b_weighted_score,
                 c1_score, c2_score, c3_score, c4_score, c_total_score, c_weighted_score,
                 total_score, ranking, semester, academic_year)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, comp)
        except Exception as e:
            print(f"插入综测成绩失败: {e}")
    
    print(f"  - 插入 {len(test_comprehensive)} 条综测成绩")
    
    conn.commit()
    conn.close()
    
    print("测试数据初始化完成！")


def verify_test_data():
    """验证测试数据"""
    print("\n验证测试数据...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 验证各表数据量
    tables = ["students", "classes", "users", "academic_scores", "comprehensive_scores"]
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} 条记录")
    
    conn.close()


def main():
    """主函数"""
    print("=" * 60)
    print("综测系统测试数据初始化")
    print("=" * 60)
    
    # 初始化测试图片目录
    init_test_photos()
    
    # 初始化测试数据库
    init_test_database()
    
    # 验证测试数据
    verify_test_data()
    
    print("\n" + "=" * 60)
    print("测试数据准备完成！")
    print("=" * 60)
    print("\n可以运行以下命令执行测试：")
    print("  pytest tests/test_comprehensive_flow.py -v --asyncio-mode=auto")


if __name__ == "__main__":
    main()

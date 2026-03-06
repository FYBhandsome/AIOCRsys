#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整测试数据生成脚本
生成包含班级、学生、成绩、证书等完整的测试数据
"""

import os
import sys
from pathlib import Path
import random
from datetime import datetime
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATA_DIR = Path("D:/PaddleOCR/visual_model/data")
DOCS_DIR = Path("D:/PaddleOCR/visual_model/docs")

DATA_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

# 测试数据配置
CLASSES = [
    {"id": "230521", "name": "230521班", "grade": "2023", "major": "网络工程", "college": "计算机学院"},
    {"id": "230522", "name": "230522班", "grade": "2023", "major": "软件工程", "college": "计算机学院"},
    {"id": "230523", "name": "230523班", "grade": "2023", "major": "计算机科学与技术", "college": "计算机学院"},
]

FIRST_NAMES = ["张", "李", "王", "刘", "陈", "杨", "黄", "赵", "周", "吴", "徐", "孙", "胡", "朱", "高", "林"]
LAST_NAMES = ["伟", "芳", "娜", "秀英", "敏", "静", "丽", "强", "磊", "军", "洋", "勇", "艳", "杰", "涛", "明", "超", "秀兰", "霞", "平", "刚", "桂英", "文", "华", "玲", "辉", "鑫", "斌", "波", "宇", "浩", "凯", "健", "俊", "帆", "鹏", "博", "婷", "雪", "倩", "琳", "欣", "颖", "佳", "蕾", "璐", "晶", "瑶", "茜"]

SUBJECTS = ["高等数学", "大学英语", "程序设计基础", "数据结构", "计算机网络", "操作系统", "数据库原理", "软件工程", "计算机组成原理", "离散数学"]

SEMESTERS = [
    {"semester": "1", "academic_year": "2024-2025"},
    {"semester": "2", "academic_year": "2024-2025"}
]

CERTIFICATE_TYPES = [
    {"title": "全国大学生数学建模竞赛", "category": "C", "sub_category": "C1", "levels": ["国家级一等奖", "国家级二等奖", "省级一等奖", "省级二等奖", "校级一等奖"]},
    {"title": "蓝桥杯全国软件和信息技术专业人才大赛", "category": "C", "sub_category": "C1", "levels": ["国家级一等奖", "国家级二等奖", "省级一等奖", "省级二等奖", "校级一等奖"]},
    {"title": "全国大学生英语竞赛", "category": "C", "sub_category": "C3", "levels": ["国家级特等奖", "国家级一等奖", "国家级二等奖", "省级一等奖", "校级一等奖"]},
    {"title": "软件著作权登记证书", "category": "C", "sub_category": "C4", "levels": ["国家级"]},
    {"title": "计算机软件技术资格考试", "category": "C", "sub_category": "C4", "levels": ["初级", "中级", "高级"]},
    {"title": "优秀学生干部", "category": "A", "sub_category": "A1", "levels": ["校级", "院级"]},
    {"title": "三好学生", "category": "A", "sub_category": "A1", "levels": ["国家级", "省级", "校级", "院级"]},
    {"title": "校运动会", "category": "C", "sub_category": "C2", "levels": ["第一名", "第二名", "第三名", "优秀奖"]},
]


def generate_students():
    """生成学生数据"""
    students = []
    student_id_base = 202300502100
    
    for cls in CLASSES:
        # 每个班级生成4-5名学生
        num_students = random.randint(4, 5)
        for i in range(num_students):
            student_id = str(student_id_base + i + len(students) * 10)
            name = random.choice(FIRST_NAMES) + random.choice(LAST_NAMES)
            dormitory = f"{random.randint(1, 6)}#{random.randint(101, 699)}"
            
            student = {
                "id": student_id,
                "name": name,
                "class_id": cls["id"],
                "class_name": cls["name"],
                "grade": cls["grade"],
                "major": cls["major"],
                "college": cls["college"],
                "dormitory_number": dormitory,
                "dormitory_score": round(random.uniform(80, 100), 1),
                "physical_test_score": round(random.uniform(60, 95), 1),
            }
            students.append(student)
    
    return students


def generate_academic_scores(students):
    """生成学业成绩数据"""
    all_scores = []
    
    for sem in SEMESTERS:
        for student in students:
            # 生成课程数（8-12门）
            course_count = random.randint(8, 12)
            total_credits = course_count * 2.5 + random.randint(-2, 2)
            
            # 生成课程成绩
            course_scores = []
            total_score = 0
            weighted_total = 0
            total_weight = 0
            failed_count = 0
            earned_credits = total_credits
            
            for _ in range(course_count):
                # 生成随机分数，包含边界情况
                rand_val = random.random()
                if rand_val < 0.05:
                    score = 0  # 零分
                elif rand_val < 0.10:
                    score = 100  # 满分
                elif rand_val < 0.15:
                    score = 60  # 刚好及格
                elif rand_val < 0.20:
                    score = random.randint(0, 59)  # 不及格
                else:
                    score = random.randint(60, 99)  # 正常分数
                
                credit = round(random.uniform(2, 4), 1)
                course_scores.append({
                    "subject": random.choice(SUBJECTS),
                    "score": score,
                    "credit": credit
                })
                
                total_score += score
                weighted_total += score * credit
                total_weight += credit
                
                if score < 60:
                    failed_count += 1
                    earned_credits -= credit
            
            arithmetic_average = round(total_score / course_count, 2)
            weighted_average = round(weighted_total / total_weight, 2)
            
            # 计算绩点 (简化版)
            gpa_map = {
                (90, 100): 4.0,
                (85, 89): 3.7,
                (82, 84): 3.3,
                (78, 81): 3.0,
                (75, 77): 2.7,
                (72, 74): 2.3,
                (68, 71): 2.0,
                (64, 67): 1.5,
                (60, 63): 1.0,
                (0, 59): 0.0,
            }
            
            avg_gpa = 0
            for cs in course_scores:
                for (low, high), gpa in gpa_map.items():
                    if low <= cs["score"] <= high:
                        avg_gpa += gpa * cs["credit"]
                        break
            avg_gpa = round(avg_gpa / total_weight, 2)
            
            score_entry = {
                "学号": student["id"],
                "姓名": student["name"],
                "班级": student["class_name"],
                "专业名称": student["major"],
                "年级": student["grade"],
                "总分": total_score,
                "门数": course_count,
                "总学分": round(total_credits, 1),
                "获得学分": round(earned_credits, 1),
                "算术平均分": arithmetic_average,
                "算术平均分排名": None,
                "学分加权平均分": weighted_average,
                "学分加权平均分排名": None,
                "平均学分绩点": avg_gpa,
                "平均学分绩点排名": None,
                "不及格门次": failed_count,
                "semester": sem["semester"],
                "academic_year": sem["academic_year"],
                "course_scores": course_scores,
            }
            all_scores.append(score_entry)
    
    # 计算排名
    for sem in SEMESTERS:
        for cls in CLASSES:
            sem_cls_scores = [s for s in all_scores 
                              if s["semester"] == sem["semester"] 
                              and s["academic_year"] == sem["academic_year"]
                              and s["班级"] == cls["name"]]
            
            # 按加权平均分排序
            sem_cls_scores.sort(key=lambda x: -x["学分加权平均分"])
            for idx, s in enumerate(sem_cls_scores, 1):
                s["算术平均分排名"] = idx
                s["学分加权平均分排名"] = idx
                s["平均学分绩点排名"] = idx
    
    return all_scores


def generate_certificates(students):
    """生成证书数据"""
    certificates = []
    cert_id = 1
    
    # 选择部分学生生成证书
    selected_students = random.sample(students, min(6, len(students)))
    
    for student in selected_students:
        # 每个学生生成1-3个证书
        num_certs = random.randint(1, 3)
        for _ in range(num_certs):
            cert_type = random.choice(CERTIFICATE_TYPES)
            level = random.choice(cert_type["levels"])
            
            # 根据证书类型计算加分
            score_map = {
                "国家级一等奖": 5,
                "国家级二等奖": 4,
                "国家级三等奖": 3,
                "国家级": 3,
                "国家级特等奖": 6,
                "省级一等奖": 3,
                "省级二等奖": 2,
                "初级": 1,
                "中级": 2,
                "高级": 4,
                "校级": 1,
                "校级一等奖": 2,
                "院级": 0.5,
                "第一名": 3,
                "第二名": 2,
                "第三名": 1,
                "优秀奖": 0.5,
            }
            
            score = score_map.get(level, 1)
            
            cert = {
                "证书编号": f"CERT{cert_id:04d}",
                "学号": student["id"],
                "学生姓名": student["name"],
                "班级": student["class_name"],
                "证书标题": cert_type["title"],
                "级别": level,
                "颁发机构": "测试机构",
                "颁发日期": f"{random.randint(2023, 2025)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                "类别": cert_type["category"],
                "子类别": cert_type["sub_category"],
                "加分": score,
                "状态": "approved" if random.random() > 0.2 else "pending",
            }
            certificates.append(cert)
            cert_id += 1
    
    return certificates


def export_to_excel(academic_scores, certificates):
    """导出数据到Excel"""
    # 按学期分组导出成绩
    for sem in SEMESTERS:
        sem_scores = [s for s in academic_scores 
                     if s["semester"] == sem["semester"] 
                     and s["academic_year"] == sem["academic_year"]]
        
        df_scores = pd.DataFrame(sem_scores)
        # 移除辅助列
        columns_to_drop = ["semester", "academic_year", "course_scores"]
        existing_columns = [col for col in columns_to_drop if col in df_scores.columns]
        if existing_columns:
            df_scores = df_scores.drop(existing_columns, axis=1)
        
        # 确保列顺序与原始文件一致
        column_order = [
            "学号", "姓名", "班级", "专业名称", "年级", 
            "总分", "门数", "总学分", "获得学分", 
            "算术平均分", "算术平均分排名", 
            "学分加权平均分", "学分加权平均分排名", 
            "平均学分绩点", "平均学分绩点排名", "不及格门次"
        ]
        df_scores = df_scores[column_order]
        
        filename = f"学生成绩单_{sem['academic_year']}_第{sem['semester']}学期.xlsx"
        filepath = DATA_DIR / filename
        df_scores.to_excel(filepath, index=False)
        print(f"已生成: {filepath}")
    
    # 导出证书数据
    df_certs = pd.DataFrame(certificates)
    cert_filepath = DATA_DIR / "证书数据.xlsx"
    df_certs.to_excel(cert_filepath, index=False)
    print(f"已生成: {cert_filepath}")


def generate_summary_document(students, academic_scores, certificates):
    """生成测试数据总结文档"""
    summary = f"""# 测试数据总结报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 数据概览

### 1. 班级数据
共生成 **{len(CLASSES)}** 个班级:

| 班级编号 | 班级名称 | 年级 | 专业 | 学院 |
|---------|---------|------|------|------|
"""

    for cls in CLASSES:
        summary += f"| {cls['id']} | {cls['name']} | {cls['grade']} | {cls['major']} | {cls['college']} |\n"

    summary += f"""
### 2. 学生数据
共生成 **{len(students)}** 名学生:

| 班级 | 学生人数 | 学号范围 |
|------|---------|---------|
"""

    for cls in CLASSES:
        cls_students = [s for s in students if s["class_id"] == cls["id"]]
        if cls_students:
            ids = [int(s["id"]) for s in cls_students]
            summary += f"| {cls['name']} | {len(cls_students)} | {min(ids)} - {max(ids)} |\n"

    summary += f"""
### 3. 学业成绩数据
共生成 **{len(academic_scores)}** 条成绩记录:

| 学年学期 | 记录数 | 覆盖学生数 |
|---------|--------|-----------|
"""

    for sem in SEMESTERS:
        sem_count = len([s for s in academic_scores 
                        if s["semester"] == sem["semester"] 
                        and s["academic_year"] == sem["academic_year"]])
        summary += f"| {sem['academic_year']} 第{sem['semester']}学期 | {sem_count} | {len(students)} |\n"

    summary += f"""
#### 成绩分布统计
"""

    all_weighted_scores = [s["学分加权平均分"] for s in academic_scores]
    summary += f"""
- 学分加权平均分范围: {min(all_weighted_scores):.2f} - {max(all_weighted_scores):.2f}
- 平均分: {np.mean(all_weighted_scores):.2f}
- 包含边界情况:
  - 满分(100分): {len([s for s in academic_scores if any(cs["score"] == 100 for cs in s.get("course_scores", []))])} 人次
  - 零分(0分): {len([s for s in academic_scores if any(cs["score"] == 0 for cs in s.get("course_scores", []))])} 人次
  - 及格线(60分): {len([s for s in academic_scores if any(cs["score"] == 60 for cs in s.get("course_scores", []))])} 人次

### 4. 证书数据
共生成 **{len(certificates)}** 个证书:

| 类别 | 数量 |
|------|------|
| A类(思想道德) | {len([c for c in certificates if c['类别'] == 'A'])} |
| C类(素质拓展) | {len([c for c in certificates if c['类别'] == 'C'])} |

| 子类别 | 数量 |
|--------|------|
"""

    sub_categories = {
        "A1": "思想表现",
        "A2": "道德品质",
        "A3": "集体活动",
        "C1": "科技竞赛",
        "C2": "体育竞技",
        "C3": "文化竞赛",
        "C4": "创新创业",
    }

    for sub_cat, desc in sub_categories.items():
        count = len([c for c in certificates if c.get("子类别") == sub_cat])
        if count > 0:
            summary += f"| {sub_cat}({desc}) | {count} |\n"

    summary += f"""
## 文件清单

生成的Excel文件:

1. {DATA_DIR / '学生成绩单_2024-2025_第1学期.xlsx'}
   - 2024-2025学年第一学期成绩
   - {len([s for s in academic_scores if s['semester'] == '1'])} 条记录

2. {DATA_DIR / '学生成绩单_2024-2025_第2学期.xlsx'}
   - 2024-2025学年第二学期成绩
   - {len([s for s in academic_scores if s['semester'] == '2'])} 条记录

3. {DATA_DIR / '证书数据.xlsx'}
   - 获奖证书数据
   - {len(certificates)} 条记录

## 数据特点

- ✅ 包含3个班级、{len(students)}名学生的完整信息
- ✅ 覆盖2个学期的学业成绩
- ✅ 包含多种科目和分数段
- ✅ 包含边界情况(满分、零分、刚好及格)
- ✅ 包含{len(certificates)}个获奖证书，覆盖A/C类不同级别
- ✅ 数据符合数据库结构要求
- ✅ Excel格式正确，可直接用于上传测试
"""

    doc_path = DOCS_DIR / "测试数据总结.md"
    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write(summary)
    print(f"已生成: {doc_path}")


def main():
    """主函数"""
    print("=" * 60)
    print("完整测试数据生成")
    print("=" * 60)
    
    # 生成数据
    print("\n1. 生成学生数据...")
    students = generate_students()
    print(f"   生成了 {len(students)} 名学生")
    
    print("\n2. 生成学业成绩数据...")
    academic_scores = generate_academic_scores(students)
    print(f"   生成了 {len(academic_scores)} 条成绩记录")
    
    print("\n3. 生成证书数据...")
    certificates = generate_certificates(students)
    print(f"   生成了 {len(certificates)} 个证书")
    
    # 导出Excel
    print("\n4. 导出Excel文件...")
    export_to_excel(academic_scores, certificates)
    
    # 生成总结文档
    print("\n5. 生成总结文档...")
    generate_summary_document(students, academic_scores, certificates)
    
    print("\n" + "=" * 60)
    print("测试数据生成完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

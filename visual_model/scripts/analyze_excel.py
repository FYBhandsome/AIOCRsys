#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel字段分析脚本
"""
import pandas as pd
import os

# 分析学生成绩单
score_file = 'D:/PaddleOCR/visual_model/data/学生成绩单.xlsx'
if os.path.exists(score_file):
    print('=== 学生成绩单.xlsx 字段 ===')
    df = pd.read_excel(score_file, sheet_name=0, header=0)
    for col in df.columns:
        print(f'  - {col}')
    print(f'\n总列数: {len(df.columns)}')
    print(f'总行数: {len(df)}')
    print('\n前3行数据预览:')
    print(df.head(3).to_string())
else:
    print(f'文件不存在: {score_file}')

print('\n' + '='*50 + '\n')

# 分析综测计算表模板
template_file = 'D:/PaddleOCR/visual_model/data/230521班综合测评计算表格模板.xlsx'
if os.path.exists(template_file):
    print('=== 综测计算表模板.xlsx 工作表 ===')
    xl = pd.ExcelFile(template_file)
    for sheet in xl.sheet_names:
        print(f'\n--- 工作表: {sheet} ---')
        df = pd.read_excel(template_file, sheet_name=sheet, header=2)
        for col in df.columns:
            print(f'  - {col}')
else:
    print(f'文件不存在: {template_file}')

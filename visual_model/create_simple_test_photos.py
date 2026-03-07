#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成带文字的测试图片
用于OCR测试
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_test_image(text, output_path, width=800, height=600):
    """创建带文字的测试图片"""
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except:
        try:
            font = ImageFont.truetype("simhei.ttf", 36)
        except:
            font = ImageFont.load_default()
    
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    draw.text((x, y), text, fill='black', font=font)
    img.save(output_path, 'JPEG', quality=95)
    print(f"已创建测试图片: {output_path}")

def main():
    test_dir = r"d:\PaddleOCR\visual_model\testphoto\test"
    
    test_texts = [
        "获奖证书",
        "姓名: 张三 学号: 202300502101",
        "竞赛一等奖",
        "颁发单位: XX大学",
        "日期: 2024年05月01日"
    ]
    
    for i, text in enumerate(test_texts):
        output_path = os.path.join(test_dir, f"test_cert_{i+1}.jpg")
        create_test_image(text, output_path)
    
    print(f"\n完成！共生成 {len(test_texts)} 张测试照片")
    print(f"保存位置: {test_dir}")

if __name__ == "__main__":
    main()

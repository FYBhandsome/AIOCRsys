#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PaddleOCR v4 模型下载脚本
自动下载并配置 PP-OCRv4 模型
"""

import os
import sys
import urllib.request
import tarfile
from pathlib import Path

# 模型下载链接
MODELS = {
    "det": {
        "name": "检测模型 (DET)",
        "url": "https://paddleocr.bj.bcebos.com/PP-OCRv4/chinese/ch_PP-OCRv4_det_infer.tar",
        "filename": "ch_PP-OCRv4_det_infer.tar",
        "extract_dir": "ch_PP-OCRv4_det_infer"
    },
    "rec": {
        "name": "识别模型 (REC)",
        "url": "https://paddleocr.bj.bcebos.com/PP-OCRv4/chinese/ch_PP-OCRv4_rec_infer.tar",
        "filename": "ch_PP-OCRv4_rec_infer.tar",
        "extract_dir": "ch_PP-OCRv4_rec_infer"
    },
    "cls": {
        "name": "方向分类器 (CLS)",
        "url": "https://paddleocr.bj.bcebos.com/dygraph_v2.0/ch/ch_ppocr_mobile_v2.0_cls_infer.tar",
        "filename": "ch_ppocr_mobile_v2.0_cls_infer.tar",
        "extract_dir": "ch_ppocr_mobile_v2.0_cls_infer"
    }
}

def download_file(url, filepath):
    """下载文件并显示进度"""
    def reporthook(count, block_size, total_size):
        percent = int(count * block_size * 100 / total_size)
        sys.stdout.write(f"\r进度: {percent}% ({count * block_size / (1024*1024):.1f}MB / {total_size / (1024*1024):.1f}MB)")
        sys.stdout.flush()
    
    urllib.request.urlretrieve(url, filepath, reporthook)
    print()  # 换行

def extract_tar(tar_path, extract_dir):
    """解压 tar 文件"""
    print(f"正在解压到: {extract_dir}")
    with tarfile.open(tar_path, 'r') as tar:
        tar.extractall(extract_dir)
    print("解压完成")

def main():
    """主函数"""
    print("=" * 60)
    print("PaddleOCR v4 模型下载工具")
    print("=" * 60)
    print()
    print("注意：本项目已配置为使用PaddleOCR自动下载的默认模型")
    print("模型将自动下载到 C:\\Users\\[用户名]\\.paddlex\\official_models\\ 目录")
    print("本脚本仅用于手动下载特定版本的模型到本地")
    print()
    
    # 获取项目根目录
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    models_dir = project_root / "models" / "paddleocr_v4"
    
    # 创建模型目录
    models_dir.mkdir(parents=True, exist_ok=True)
    print(f"手动下载模型目录: {models_dir}")
    print()
    
    # 下载每个模型
    for model_key, model_info in MODELS.items():
        print(f"开始下载: {model_info['name']}")
        print(f"   URL: {model_info['url']}")
        
        # 下载路径
        tar_path = models_dir / model_info['filename']
        extract_dir = models_dir / model_info['extract_dir']
        
        # 检查是否已存在
        if extract_dir.exists():
            print(f"模型已存在，跳过: {extract_dir}")
            print()
            continue
        
        try:
            # 下载文件
            if not tar_path.exists():
                print(f"下载中...")
                download_file(model_info['url'], tar_path)
                print(f"下载完成: {tar_path}")
            else:
                print(f"文件已存在，跳过下载: {tar_path}")
            
            # 解压文件
            extract_tar(tar_path, models_dir)
            
            # 删除压缩包以节省空间
            if tar_path.exists():
                tar_path.unlink()
                print(f"已删除压缩包: {tar_path}")
            
            print(f"{model_info['name']} 安装完成")
            print()
            
        except Exception as e:
            print(f"下载失败: {e}")
            print(f"   请手动下载: {model_info['url']}")
            print()
            continue
    
    # 生成配置提示
    print("=" * 60)
    print("所有模型下载完成！")
    print("=" * 60)
    print()
    print("如需使用手动下载的模型，请在 .env 文件中添加以下配置：")
    print("否则，系统将继续使用自动下载的默认模型")
    print()
    print(f"OCR_DET_MODEL_DIR={models_dir / MODELS['det']['extract_dir']}")
    print(f"OCR_REC_MODEL_DIR={models_dir / MODELS['rec']['extract_dir']}")
    print(f"OCR_CLS_MODEL_DIR={models_dir / MODELS['cls']['extract_dir']}")
    print()
    print("现在可以启动服务了: python visual_model/main.py 或使用 uvicorn 启动")

if __name__ == "__main__":
    main()


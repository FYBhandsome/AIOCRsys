
import os
from PIL import Image

def verify_photos():
    test_dir = r"d:\PaddleOCR\visual_model\testphoto\test"
    
    if not os.path.exists(test_dir):
        print(f"目录不存在: {test_dir}")
        return
    
    files = [f for f in os.listdir(test_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    total = len(files)
    success = 0
    failed = []
    
    print(f"开始验证 {total} 张测试照片...\n")
    
    for filename in files:
        filepath = os.path.join(test_dir, filename)
        try:
            with Image.open(filepath) as img:
                img.verify()
                # 重新打开图片确认
                with Image.open(filepath) as img2:
                    # 获取图片信息
                    width, height = img2.size
                    format_name = img2.format
            success += 1
            print(f"✓ {filename} - {format_name} - {width}x{height}")
        except Exception as e:
            failed.append((filename, str(e)))
            print(f"✗ {filename} - 验证失败: {e}")
    
    print(f"\n{'='*60}")
    print(f"验证结果:")
    print(f"总计: {total}")
    print(f"成功: {success}")
    print(f"失败: {len(failed)}")
    
    if failed:
        print(f"\n失败的文件:")
        for filename, error in failed:
            print(f"  - {filename}: {error}")
    
    print(f"{'='*60}")
    return success == total

if __name__ == "__main__":
    verify_photos()

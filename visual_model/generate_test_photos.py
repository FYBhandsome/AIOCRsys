
import os
from PIL import Image, ImageEnhance, ImageFilter
import shutil

def adjust_brightness(image, factor):
    """调整图片亮度"""
    enhancer = ImageEnhance.Brightness(image)
    return enhancer.enhance(factor)

def apply_blur(image):
    """轻微模糊"""
    return image.filter(ImageFilter.GaussianBlur(radius=1))

def resize_image(image, width, height):
    """调整图片尺寸"""
    return image.resize((width, height), Image.LANCZOS)

def save_image(image, output_path, quality=95):
    """保存图片，确保可以被PIL打开"""
    image.save(output_path, quality=quality)
    # 验证图片可以正常打开
    try:
        with Image.open(output_path) as img:
            img.verify()
        return True
    except Exception as e:
        print(f"警告: 图片 {output_path} 可能有问题: {e}")
        return False

def main():
    input_dir = r"d:\PaddleOCR\visual_model\testphoto"
    output_dir = r"d:\PaddleOCR\visual_model\testphoto\test"
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 支持的图片格式
    supported_formats = ['.jpg', '.jpeg', '.png']
    
    # 分辨率设置
    resolutions = [
        ('low', 640, 480),
        ('medium', 1280, 960),
        ('high', 2560, 1920)
    ]
    
    # 质量变体
    quality_variants = [
        ('normal', lambda x: x),
        ('dark', lambda x: adjust_brightness(x, 0.6)),
        ('bright', lambda x: adjust_brightness(x, 1.4)),
        ('blur', apply_blur)
    ]
    
    # 输出格式
    output_formats = ['jpg', 'png']
    
    count = 0
    
    # 处理每张原始照片
    for filename in os.listdir(input_dir):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in supported_formats:
            continue
            
        original_name = os.path.splitext(filename)[0]
        original_path = os.path.join(input_dir, filename)
        
        try:
            # 打开原始图片
            with Image.open(original_path) as img:
                img = img.convert('RGB')
                
                # 为每种分辨率生成变体
                for res_name, width, height in resolutions:
                    resized_img = resize_image(img, width, height)
                    
                    # 为每种质量变体生成
                    for qual_name, qual_func in quality_variants:
                        processed_img = qual_func(resized_img.copy())
                        
                        # 保存为JPG和PNG格式
                        for out_format in output_formats:
                            # 生成文件名
                            safe_name = original_name.replace(' ', '_').replace('"', '')
                            output_filename = f"{safe_name}_{out_format}_{res_name}_{qual_name}.{out_format}"
                            output_path = os.path.join(output_dir, output_filename)
                            
                            # 保存图片
                            if out_format == 'jpg':
                                save_image(processed_img, output_path, quality=90)
                            else:
                                # PNG不使用quality参数
                                processed_img.save(output_path)
                                # 验证
                                try:
                                    with Image.open(output_path) as test_img:
                                        test_img.verify()
                                except Exception as e:
                                    print(f"警告: PNG图片 {output_path} 验证失败: {e}")
                            
                            count += 1
                            print(f"已生成: {output_filename}")
                            
        except Exception as e:
            print(f"处理 {filename} 时出错: {e}")
    
    print(f"\n完成！共生成 {count} 张测试照片")
    print(f"保存位置: {output_dir}")

if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
图片拼接工具 - 通用版本
可以将任意前缀的截图按顺序纵向拼接为一张
使用方法: python stitch_all.py
"""

from PIL import Image
import os
import sys

# 设置输出编码为UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 配置
input_dir = r"C:\Users\maobcjl\.codebuddy\skills\tax-compliance-planning"

# 定义需要拼接的截图组
screenshot_groups = [
    {
        "prefix": "screenshot_03_vat",
        "count": 3,
        "output": "screenshot_03_vat_complete.png"
    }
]

def stitch_images(prefix, count, output_file):
    """纵向拼接指定数量的图片"""
    images = []
    
    # 按顺序加载图片
    for i in range(1, count + 1):
        filepath = os.path.join(input_dir, f"{prefix}-{i}.png")
        if os.path.exists(filepath):
            try:
                img = Image.open(filepath)
                images.append(img)
                print(f"  [OK] 已加载: {os.path.basename(filepath)}")
            except Exception as e:
                print(f"  [FAIL] 加载失败: {os.path.basename(filepath)} - {e}")
        else:
            print(f"  [WARN] 文件不存在: {os.path.basename(filepath)}")
    
    if not images:
        print(f"  [FAIL] 未找到任何图片: {prefix}")
        return False
    
    # 计算拼接后的尺寸
    max_width = max(img.width for img in images)
    total_height = sum(img.height for img in images)
    
    print(f"  [INFO] 拼接信息: {len(images)}张图片, {max_width}x{total_height}px")
    
    # 创建新图片
    combined = Image.new('RGB', (max_width, total_height), color='white')
    
    # 拼接图片
    y_offset = 0
    for i, img in enumerate(images):
        x_offset = (max_width - img.width) // 2
        combined.paste(img, (x_offset, y_offset))
        y_offset += img.height
    
    # 保存
    try:
        output_path = os.path.join(input_dir, output_file)
        combined.save(output_path, 'PNG', quality=95)
        print(f"  [OK] 已保存: {output_file}")
        return True
    except Exception as e:
        print(f"  [FAIL] 保存失败: {e}")
        return False

def main():
    print("=" * 60)
    print("图片拼接工具 - 通用版本")
    print("=" * 60 + "\n")
    
    for group in screenshot_groups:
        prefix = group["prefix"]
        count = group["count"]
        output = group["output"]
        
        print(f"[INFO] 开始拼接: {prefix}")
        success = stitch_images(prefix, count, output)
        
        if success:
            print(f"[OK] {prefix} 拼接完成!\n")
        else:
            print(f"[FAIL] {prefix} 拼接失败!\n")
    
    print("=" * 60)
    print("[OK] 全部完成!")
    print("=" * 60)

if __name__ == "__main__":
    main()

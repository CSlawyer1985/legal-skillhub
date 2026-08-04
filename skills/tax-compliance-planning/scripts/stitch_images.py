# -*- coding: utf-8 -*-
"""
图片拼接工具 - 将多张截图按顺序纵向拼接为一张
使用方法: python stitch_images.py
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
prefix = "screenshot_02_planning"
output_file = r"C:\Users\maobcjl\.codebuddy\skills\tax-compliance-planning\screenshot_02_planning_complete.png"

def stitch_images_vertical():
    """纵向拼接图片"""
    images = []
    
    # 按顺序加载图片
    for i in range(1, 5):  # 1-4
        filepath = os.path.join(input_dir, f"{prefix}-{i}.png")
        if os.path.exists(filepath):
            try:
                img = Image.open(filepath)
                images.append(img)
                print(f"[OK] 已加载: {os.path.basename(filepath)}")
            except Exception as e:
                print(f"[FAIL] 加载失败: {os.path.basename(filepath)} - {e}")

    if not images:
        print("[FAIL] 未找到任何图片!")
        return False
    
    # 计算拼接后的尺寸
    max_width = max(img.width for img in images)
    total_height = sum(img.height for img in images)
    
    print(f"\n拼接信息:")
    print(f"  图片数量: {len(images)}")
    print(f"  最大宽度: {max_width} px")
    print(f"  总高度: {total_height} px")
    
    # 创建新图片
    combined = Image.new('RGB', (max_width, total_height), color='white')
    
    # 拼接图片
    y_offset = 0
    for i, img in enumerate(images):
        # 居中放置
        x_offset = (max_width - img.width) // 2
        combined.paste(img, (x_offset, y_offset))
        y_offset += img.height
        print(f"[OK] 已拼接第 {i+1} 张")
    
    # 保存
    try:
        combined.save(output_file, 'PNG', quality=95)
        print(f"\n[OK] 拼接完成! 已保存到:")
        print(f"  {output_file}")
        return True
    except Exception as e:
        print(f"\n[FAIL] 保存失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("图片拼接工具 - 税务筹划案例截图")
    print("=" * 50 + "\n")
    
    success = stitch_images_vertical()
    
    print("\n" + "=" * 50)
    if success:
        print("[OK] 任务完成!")
    else:
        print("[FAIL] 任务失败!")
    print("=" * 50)

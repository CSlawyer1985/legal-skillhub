#!/usr/bin/env python3
import os
import re
import sys
import shutil
import pdfplumber
import fitz  # PyMuPDF
import easyocr
import numpy as np

# 设置为True只显示计划，不实际重命名
DRY_RUN = False

# 公司简称映射（示例数据）
COMPANY_SHORT = {
    "示例物业服务有限公司": "示例公司",
    "示例物业管理有限公司": "示例永勤",
    "示例保安服务有限公司": "示例米格",
    "示例运营管理有限公司": "示例溪水",
    # 分公司也映射到同一简称
    "示例物业服务有限公司安徽分公司": "示例公司",
    "示例物业服务有限公司第一分公司": "示例公司",
    "示例物业服务有限公司嘉兴分公司": "示例公司",
    "示例物业服务有限公司金华分公司": "示例公司",
    "示例物业服务有限公司宁波分公司": "示例公司",
    "示例物业服务有限公司绍兴分公司": "示例公司",
    "示例物业服务有限公司申花路分公司": "示例公司",
    "示例物业服务有限公司台州分公司": "示例公司",
    "示例物业服务有限公司温州分公司": "示例公司",
}

# 初始化EasyOCR阅读器（全局，避免重复加载）
ocr_reader = None

def get_ocr_reader():
    global ocr_reader
    if ocr_reader is None:
        try:
            ocr_reader = easyocr.Reader(['ch_sim', 'en'])
        except Exception as e:
            print(f"警告: 初始化EasyOCR失败: {e}")
            return None
    return ocr_reader

def extract_date_from_text(text):
    """从文本中提取日期，返回YYYYMMDD格式"""
    patterns = [
        r'(\d{4})年(\d{1,2})月(\d{1,2})日',
        r'(\d{4})-(\d{1,2})-(\d{1,2})',
        r'(\d{4})/(\d{1,2})/(\d{1,2})',
        r'(\d{4})\.(\d{1,2})\.(\d{1,2})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            # 简单的日期验证
            if 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                return f"{year:04d}{month:02d}{day:02d}"
    return None

def extract_text_with_pdfplumber(pdf_path):
    """使用pdfplumber提取PDF文本"""
    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        print(f"  pdfplumber提取失败: {e}")
        return ""

def extract_date_with_ocr(pdf_path):
    """使用OCR从PDF图像中提取日期"""
    reader = get_ocr_reader()
    if reader is None:
        return None
    
    try:
        doc = fitz.open(pdf_path)
        all_text = ""
        
        # 只处理前3页
        for page_num in range(min(3, len(doc))):
            page = doc[page_num]
            pix = page.get_pixmap(dpi=200)
            img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
            if pix.n == 4:
                img_array = img_array[:, :, :3]
            
            result = reader.readtext(img_array, detail=0)
            page_text = " ".join(result)
            all_text += page_text + "\n"
        
        doc.close()
        
        # 从OCR文本中提取日期
        return extract_date_from_text(all_text)
        
    except Exception as e:
        print(f"  OCR处理失败: {e}")
        return None

def extract_date(pdf_path):
    """提取PDF日期，先尝试pdfplumber，再尝试OCR"""
    print(f"处理: {os.path.basename(pdf_path)}")
    
    # 先用pdfplumber提取文本
    text = extract_text_with_pdfplumber(pdf_path)
    if text and len(text) > 10:  # 有实际文本内容
        print(f"  文本长度: {len(text)} 字符")
        date = extract_date_from_text(text)
        if date:
            print(f"  找到日期: {date} (via pdfplumber)")
            return date
        else:
            print(f"  未找到日期格式，尝试OCR...")
    else:
        print(f"  无文本或文本过短，尝试OCR...")
    
    # 使用OCR
    date = extract_date_with_ocr(pdf_path)
    if date:
        print(f"  找到日期: {date} (via OCR)")
        return date
    
    print(f"  警告: 无法提取日期")
    return None

def get_company_short(name):
    """获取公司简称"""
    for full, short in COMPANY_SHORT.items():
        if full in name:
            return short
    # 如果未匹配，返回原名称的前4个字符
    return name[:4]

def generate_new_filename(old_filename, date, file_type):
    """生成新文件名"""
    # 移除可能的前缀（如20260409_）
    base = old_filename
    if base.startswith("20260409_"):
        base = base[9:]
    
    # 根据文件类型处理
    if "企业信用信息公示报告" in base:
        # 企业信用报告
        # 提取公司名称
        company = base.replace("企业信用信息公示报告.pdf", "")
        short = get_company_short(company)
        return f"{date}_{short}_企业信用信息公示报告.pdf"
    
    elif "至" in base and "函" in base:
        # 往来函件
        parts = base.split("至")
        if len(parts) == 2:
            sender = parts[0]
            rest = parts[1]
            receiver = rest.split("函")[0]
            suffix = "函" + rest.split("函")[1] if "函" in rest else ""
            
            sender_short = get_company_short(sender)
            receiver_short = get_company_short(receiver)
            
            # 判断是函还是回函
            if "回函" in base:
                return f"{date}_{receiver_short}至{sender_short}_回函.pdf"
            else:
                return f"{date}_{sender_short}至{receiver_short}_函.pdf"
    
    # 默认：日期_原文件名
    return f"{date}_{base}"

def main():
    if len(sys.argv) < 2:
        print("Usage: python rename_files_with_dates.py <folder>")
        sys.exit(1)
    
    folder = sys.argv[1]
    if not os.path.exists(folder):
        print(f"Folder not found: {folder}")
        sys.exit(1)
    
    pdf_files = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    
    print(f"找到 {len(pdf_files)} 个PDF文件")
    print("=" * 60)
    
    rename_plan = []
    no_date_files = []
    
    for pdf in pdf_files:
        old_name = os.path.basename(pdf)
        date = extract_date(pdf)
        
        if date:
            new_name = generate_new_filename(old_name, date, "")
            rename_plan.append((pdf, os.path.join(os.path.dirname(pdf), new_name)))
        else:
            no_date_files.append(pdf)
        
        print()
    
    print("=" * 60)
    print("重命名计划:")
    for old_path, new_path in rename_plan:
        old_name = os.path.basename(old_path)
        new_name = os.path.basename(new_path)
        print(f"  {old_name} -> {new_name}")
    
    if no_date_files:
        print("\n无法提取日期的文件:")
        for f in no_date_files:
            print(f"  {os.path.basename(f)}")
    
    print(f"\n总计: {len(rename_plan)} 个文件可重命名，{len(no_date_files)} 个文件无法提取日期")
    
    if DRY_RUN:
        print("\n当前为模拟模式 (DRY_RUN=True)，未执行实际重命名。")
        print("如需实际重命名，请将脚本中的 DRY_RUN 设置为 False。")
    else:
        print("\n执行重命名...")
        for old_path, new_path in rename_plan:
            try:
                shutil.move(old_path, new_path)
                print(f"重命名: {os.path.basename(old_path)} -> {os.path.basename(new_path)}")
            except Exception as e:
                print(f"重命名失败 {old_path}: {e}")
        
        print("\n重命名完成")
        print(f"注意: 请手动更新案件材料清单.md中的文件列表")

if __name__ == "__main__":
    main()
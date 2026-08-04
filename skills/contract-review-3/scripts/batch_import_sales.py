#!/usr/bin/env python3
"""
批量导入买卖合同模板到合同库
"""

import os
import subprocess
import json
from pathlib import Path

# 文件路径列表
SOURCE_FILES = [
    ("1.采购框架协议 Framework Purchase Agreement.docx", "采购框架协议（英文）"),
    ("1.产品试用买卖框架合同.docx", "产品试用买卖框架合同"),
    ("1.买卖框架合同.docx", "买卖框架合同"),
    ("1.设备买卖及安装合同.docx", "设备买卖及安装合同"),
    ("2.附件：采购订单的格式 Appendix_ Format of Purchase Order.docx", "采购订单格式（附件）"),
    ("2.知识产权协议.docx", "知识产权协议"),
    ("3.保密协议.docx", "保密协议"),
    ("4.反商业贿赂协议.docx", "反商业贿赂协议"),
    ("5.采购订单.docx", "采购订单"),
    ("采购框架协议 Framework Purchase Agreement 中英文版文本清单.docx", "采购框架协议文本清单"),
    ("订购单（订单）.docx", "订购单"),
    ("分销商协议-2.docx", "分销商协议"),
    ("国际货物买卖合同.docx", "国际货物买卖合同"),
    ("货物买卖合同.docx", "货物买卖合同"),
    ("货物买卖框架合同（详细版）文本清单.docx", "货物买卖框架合同（详细版）"),
    ("数据采购交易（转让）合同（一次交易）.docx", "数据采购交易合同"),
    ("物资采购合同.docx", "物资采购合同"),
    ("虚拟物品采购合同.docx", "虚拟物品采购合同"),
    ("一般商品买卖合同.docx", "一般商品买卖合同"),
    ("一般小型设备买卖及安装合同.docx", "一般小型设备买卖及安装合同"),
    ("OEM采购协议.docx", "OEM采购协议"),
]

BASE_DIR = Path("/Users/gaoshengjie/Library/Mobile Documents/com~apple~CloudDocs/大连知恒/合同模板库/1.买卖合同")
OUTPUT_DIR = Path("/Users/gaoshengjie/.workbuddy/skills/contract-review/references/template-library/买卖合同")
SCRIPT = Path("/Users/gaoshengjie/.workbuddy/skills/word-reader/scripts/read_word.py")

def convert_file(docx_path: Path, output_path: Path) -> bool:
    """转换单个文件"""
    try:
        result = subprocess.run(
            ["python3", str(SCRIPT), str(docx_path), "--format", "markdown"],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            content = result.stdout
            lines = content.split('\n')
            body_start = 0
            for i, line in enumerate(lines):
                if line.startswith('## 正文内容'):
                    body_start = i + 1
                    break
            body_content = '\n'.join(lines[body_start:]) if body_start > 0 else content
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(body_content)
            return True
        else:
            print(f"  错误: {result.stderr}")
            return False
    except Exception as e:
        print(f"  异常: {e}")
        return False

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    success_count = 0
    fail_count = 0
    print(f"开始导入买卖合同模板到: {OUTPUT_DIR}\n")
    for filename, display_name in SOURCE_FILES:
        source_path = BASE_DIR / filename
        output_filename = f"{display_name}.md"
        output_path = OUTPUT_DIR / output_filename
        print(f"处理: {display_name}...")
        if not source_path.exists():
            print(f"  ⚠️ 文件不存在")
            fail_count += 1
            continue
        if convert_file(source_path, output_path):
            print(f"  ✅ 已保存: {output_filename}")
            success_count += 1
        else:
            print(f"  ❌ 转换失败")
            fail_count += 1
    print(f"\n导入完成: 成功 {success_count}, 失败 {fail_count}")

if __name__ == '__main__':
    main()

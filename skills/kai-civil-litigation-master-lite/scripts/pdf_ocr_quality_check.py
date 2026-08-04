#!/usr/bin/env python3
"""
PDF OCR 质量检查脚本：验证 OCR 处理后的 PDF 质量
检查项：文件完整性、页数一致性、文本层质量、乱码检测、中文比例
"""

import sys
import json
import unicodedata
from pathlib import Path
from datetime import datetime
from collections import defaultdict

import fitz


# 常见 OCR 错误字符映射表
OCR_ERROR_PATTERNS = {
    # 形近字错误
    '囗': '口',  # 国字框 vs 口
    '〇': '零',  # 圆圈零
    '丨': 'l',   # 竖线
    '丿': '',    # 撇，通常应删除
    '丶': '、',  # 点号
    # 全角半角问题
    '０': '0', '１': '1', '２': '2', '３': '3', '４': '4',
    '５': '5', '６': '6', '７': '7', '８': '8', '９': '9',
    'ａ': 'a', 'ｂ': 'b', 'ｃ': 'c', 'ｄ': 'd', 'ｅ': 'e',
    'Ａ': 'A', 'Ｂ': 'B', 'Ｃ': 'C', 'Ｄ': 'D', 'Ｅ': 'E',
    # 中文标点问题
    '「': '"', '」': '"', '『': '"', '』': '"',
    '【': '[', '】': ']',
    '―': '-', '—': '-',
    '…': '...',
    # 常见错字
    '曰': '日',
    '巳': '已',
    '未': '末',
    '冃': '月',
    '亊': '事',
    '凊': '清',
    '徳': '德',
    # 其他 Unicode 可疑字符
    '\ufeff': '',  # BOM
    '\u200b': '',  # 零宽空格
    '\u200c': '',  # 零宽非连接符
    '\u200d': '',  # 零宽连接符
}

# 可疑字符类别（Unicode Category）
SUSPICIOUS_CATEGORIES = {
    'Co': '私用区字符',
    'Cs': '代理字符',
    'Cn': '未分配字符',
}

# 可能是乱码的字符范围
GARBAGE_CODEPOINT_RANGES = [
    (0xE000, 0xF8FF),    # 私用区
    (0xF900, 0xFAFF),    # CJK 兼容表意文字（可能是乱码）
    (0x1F600, 0x1F64F),  # Emoji（在正式文档中可疑）
]


def is_garbage_char(c: str) -> tuple[bool, str]:
    """
    判断字符是否为乱码或可疑字符
    
    Returns:
        (是否可疑, 原因)
    """
    cp = ord(c)
    cat = unicodedata.category(c)
    
    # 检查 Unicode 类别
    if cat in SUSPICIOUS_CATEGORIES:
        return True, f"{SUSPICIOUS_CATEGORIES[cat]}(U+{cp:04X})"
    
    # 检查控制字符（除了正常换行、制表符）
    if cat == 'Cc' and cp not in (0x09, 0x0A, 0x0D):
        return True, f"控制字符(U+{cp:04X})"
    
    # 检查私用区等可疑范围
    for start, end in GARBAGE_CODEPOINT_RANGES:
        if start <= cp <= end:
            return True, f"可疑字符范围(U+{cp:04X})"
    
    # 检查是否是 OCR 常见错误字符
    if c in OCR_ERROR_PATTERNS:
        return True, f"疑似OCR错误:'{c}'→'{OCR_ERROR_PATTERNS[c]}'"
    
    return False, ""


def detect_garbage_in_text(text: str, max_samples: int = 10) -> list:
    """
    检测文本中的乱码字符，返回位置信息
    
    Returns:
        [
            {
                "char": "字符",
                "position": 字符位置,
                "context": "上下文(前后10字符)",
                "reason": "原因"
            },
            ...
        ]
    """
    garbage_list = []
    
    for i, c in enumerate(text):
        is_garbage, reason = is_garbage_char(c)
        if is_garbage:
            # 获取上下文
            start = max(0, i - 10)
            end = min(len(text), i + 11)
            context = text[start:end]
            # 标记当前字符
            rel_pos = i - start
            marked_context = context[:rel_pos] + f"【{c}】" + context[rel_pos+1:]
            
            garbage_list.append({
                "char": c,
                "position": i,
                "context": marked_context,
                "reason": reason
            })
            
            if len(garbage_list) >= max_samples:
                break
    
    return garbage_list


def apply_ocr_correction(text: str) -> tuple[str, list]:
    """
    应用 OCR 纠错映射表
    
    Returns:
        (修正后的文本, 修改记录列表)
    """
    corrections = []
    result = []
    
    for c in text:
        if c in OCR_ERROR_PATTERNS:
            corrected = OCR_ERROR_PATTERNS[c]
            if corrected:  # 不为空才记录
                corrections.append(f"'{c}'→'{corrected}'")
            result.append(corrected)
        else:
            result.append(c)
    
    return ''.join(result), corrections


def analyze_text_quality(text: str) -> dict:
    """
    分析文本质量
    
    Returns:
        {
            "char_count": int,
            "line_count": int,
            "chinese_count": int,
            "chinese_ratio": float,
            "control_char_ratio": float,
            "suspicious_ratio": float,
            "garbage_chars": list,  # 乱码字符详情
            "needs_correction": bool,  # 是否需要纠错
            "issues": list
        }
    """
    result = {
        "char_count": len(text),
        "line_count": len([l for l in text.split('\n') if l.strip()]),
        "chinese_count": 0,
        "chinese_ratio": 0.0,
        "control_char_ratio": 0.0,
        "suspicious_ratio": 0.0,
        "garbage_chars": [],
        "needs_correction": False,
        "issues": []
    }
    
    if not text:
        result["issues"].append("无文本内容")
        return result
    
    # 统计中文字符
    result["chinese_count"] = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    result["chinese_ratio"] = result["chinese_count"] / len(text)
    
    # 统计控制字符（乱码指标）
    control_chars = sum(1 for c in text if unicodedata.category(c) in ('Cc', 'Cf'))
    result["control_char_ratio"] = control_chars / len(text)
    
    # 统计可疑字符
    suspicious = 0
    for c in text:
        cat = unicodedata.category(c)
        if cat not in ('Ll', 'Lu', 'Lo', 'Nd', 'Pc', 'Pd', 'Ps', 'Pe', 'Pi', 'Pf', 'Po', 
                       'Zs', 'Zl', 'Zp', 'Cc', 'Cf', 'Sk', 'Sm', 'Sc'):
            suspicious += 1
    result["suspicious_ratio"] = suspicious / len(text)
    
    # 检测乱码字符详情
    result["garbage_chars"] = detect_garbage_in_text(text)
    if result["garbage_chars"]:
        result["needs_correction"] = True
    
    # 质量判断
    if result["control_char_ratio"] > 0.05:
        result["issues"].append(f"控制字符比例过高 ({result['control_char_ratio']:.1%})")
    if result["suspicious_ratio"] > 0.10:
        result["issues"].append(f"可疑字符比例过高 ({result['suspicious_ratio']:.1%})")
    if result["garbage_chars"]:
        result["issues"].append(f"检测到 {len(result['garbage_chars'])} 处可疑乱码")
    if result["char_count"] < 20:
        result["issues"].append(f"文本内容过少 ({result['char_count']} 字符)")
    
    return result


def check_pdf_quality(pdf_path: Path, source_path: Path = None) -> dict:
    """
    检查单个 PDF 的质量
    
    Returns:
        {
            "file": str,
            "status": "ok"|"warning"|"error",
            "pages": int,
            "source_pages": int,
            "page_match": bool,
            "total_chars": int,
            "empty_pages": int,
            "low_text_pages": int,
            "issues": list,
            "details": list
        }
    """
    result = {
        "file": str(pdf_path),
        "status": "ok",
        "pages": 0,
        "source_pages": None,
        "page_match": True,
        "total_chars": 0,
        "empty_pages": 0,
        "low_text_pages": 0,
        "issues": [],
        "details": []
    }
    
    try:
        doc = fitz.open(pdf_path)
        result["pages"] = len(doc)
        
        # 如果提供了源文件，对比页数
        if source_path and source_path.exists():
            try:
                src_doc = fitz.open(source_path)
                result["source_pages"] = len(src_doc)
                result["page_match"] = (result["pages"] == result["source_pages"])
                src_doc.close()
                if not result["page_match"]:
                    result["issues"].append(f"页数不匹配 (输出:{result['pages']} vs 源:{result['source_pages']})")
            except Exception as e:
                result["issues"].append(f"无法读取源文件对比页数: {e}")
        
        # 逐页检查
        for page_num, page in enumerate(doc):
            text = page.get_text()
            quality = analyze_text_quality(text)
            quality["page"] = page_num + 1
            result["details"].append(quality)
            result["total_chars"] += quality["char_count"]
            
            if quality["char_count"] == 0:
                result["empty_pages"] += 1
            elif quality["char_count"] < 20:
                result["low_text_pages"] += 1
        
        doc.close()
        
        # 汇总判断
        if result["empty_pages"] > 0:
            result["issues"].append(f"存在 {result['empty_pages']} 个空文本页")
            result["status"] = "warning"
        if result["low_text_pages"] > result["pages"] * 0.5:
            result["issues"].append(f"过半页面文本内容过少 ({result['low_text_pages']}/{result['pages']})")
            result["status"] = "warning"
        if not result["page_match"]:
            result["status"] = "error"
        if result["total_chars"] == 0:
            result["status"] = "error"
            result["issues"].append("文档无文本内容")
            
    except Exception as e:
        result["status"] = "error"
        result["issues"].append(f"无法打开 PDF: {e}")
    
    return result


def check_directory_quality(src_dir: Path, dst_dir: Path) -> dict:
    """
    检查整个目录的 OCR 质量
    
    Returns:
        {
            "timestamp": str,
            "source": str,
            "destination": str,
            "summary": {...},
            "structure_check": {...},
            "files": list
        }
    """
    print(f"\n正在检查 OCR 质量...")
    print(f"源目录: {src_dir}")
    print(f"输出目录: {dst_dir}\n")
    
    src_pdfs = set(p.relative_to(src_dir) for p in src_dir.rglob("*.pdf"))
    dst_pdfs = set(p.relative_to(dst_dir) for p in dst_dir.rglob("*.pdf"))
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "source": str(src_dir),
        "destination": str(dst_dir),
        "summary": {
            "total_checked": 0,
            "ok": 0,
            "warning": 0,
            "error": 0
        },
        "structure_check": {
            "source_files": len(src_pdfs),
            "output_files": len(dst_pdfs),
            "missing_in_output": [str(p) for p in sorted(src_pdfs - dst_pdfs)],
            "extra_in_output": [str(p) for p in sorted(dst_pdfs - src_pdfs)]
        },
        "files": []
    }
    
    # 检查结构问题
    if report["structure_check"]["missing_in_output"]:
        print(f"⚠️  输出目录缺失 {len(report['structure_check']['missing_in_output'])} 个文件")
    if report["structure_check"]["extra_in_output"]:
        print(f"ℹ️  输出目录多出 {len(report['structure_check']['extra_in_output'])} 个文件")
    
    # 检查每个输出文件
    for rel_path in sorted(dst_pdfs):
        src_path = src_dir / rel_path
        dst_path = dst_dir / rel_path
        
        quality = check_pdf_quality(dst_path, src_path)
        report["files"].append(quality)
        report["summary"]["total_checked"] += 1
        
        if quality["status"] == "ok":
            report["summary"]["ok"] += 1
        elif quality["status"] == "warning":
            report["summary"]["warning"] += 1
        elif quality["status"] == "error":
            report["summary"]["error"] += 1
        
        # 实时显示问题
        status_icon = {"ok": "✓", "warning": "⚠️", "error": "✗"}[quality["status"]]
        if quality["issues"]:
            print(f"{status_icon} {rel_path}")
            for issue in quality["issues"]:
                print(f"    - {issue}")
    
    return report


def generate_markdown_report(report: dict, output_path: Path = None) -> str:
    """生成 Markdown 格式的质量报告"""
    lines = []
    lines.append("# PDF OCR 质量检查报告\n")
    lines.append(f"**检查时间:** {report['timestamp']}\n")
    lines.append(f"**源目录:** {report['source']}\n")
    lines.append(f"**输出目录:** {report['destination']}\n")
    
    lines.append("## 结构检查\n")
    sc = report["structure_check"]
    lines.append(f"- 源文件数: {sc['source_files']}")
    lines.append(f"- 输出文件数: {sc['output_files']}")
    if sc["missing_in_output"]:
        lines.append(f"- ⚠️ 缺失文件: {len(sc['missing_in_output'])} 个")
        for f in sc["missing_in_output"][:10]:
            lines.append(f"  - `{f}`")
        if len(sc["missing_in_output"]) > 10:
            lines.append(f"  - ... 共 {len(sc['missing_in_output'])} 个")
    else:
        lines.append("- ✓ 无缺失文件")
    
    lines.append("\n## 质量汇总\n")
    s = report["summary"]
    lines.append(f"| 状态 | 数量 |")
    lines.append(f"|------|------|")
    lines.append(f"| 正常 | {s['ok']} |")
    lines.append(f"| 警告 | {s['warning']} |")
    lines.append(f"| 错误 | {s['error']} |")
    lines.append(f"| **总计** | **{s['total_checked']}** |")
    
    # 问题文件详情
    problem_files = [f for f in report["files"] if f["status"] != "ok"]
    if problem_files:
        lines.append("\n## 问题文件详情\n")
        for f in problem_files:
            rel_path = Path(f["file"]).name
            lines.append(f"### {rel_path}")
            lines.append(f"- 状态: {f['status'].upper()}")
            lines.append(f"- 页数: {f['pages']}")
            if f['source_pages']:
                lines.append(f"- 源文件页数: {f['source_pages']}")
            lines.append(f"- 总字符: {f['total_chars']}")
            lines.append(f"- 空文本页: {f['empty_pages']}")
            lines.append("- 问题:")
            for issue in f["issues"]:
                lines.append(f"  - ⚠️ {issue}")
            lines.append("")
    else:
        lines.append("\n✓ 所有文件质量检查通过\n")
    
    md_content = "\n".join(lines)
    
    if output_path:
        output_path.write_text(md_content, encoding="utf-8")
    
    return md_content


def main():
    import argparse
    parser = argparse.ArgumentParser(description="PDF OCR 质量检查")
    parser.add_argument("src", help="源文件夹路径（用于对比）")
    parser.add_argument("dst", help="输出文件夹路径（待检查）")
    parser.add_argument("-o", "--output", help="报告输出目录（默认输出到 dst）")
    args = parser.parse_args()
    
    src_dir = Path(args.src)
    dst_dir = Path(args.dst)
    
    if not src_dir.exists():
        print(f"错误：源文件夹不存在: {src_dir}")
        sys.exit(1)
    if not dst_dir.exists():
        print(f"错误：输出文件夹不存在: {dst_dir}")
        sys.exit(1)
    
    report = check_directory_quality(src_dir, dst_dir)
    
    # 保存 JSON 报告
    output_dir = Path(args.output) if args.output else dst_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    json_path = output_dir / ".ocr_quality_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 生成 Markdown 报告
    md_path = output_dir / "OCR质量检查报告.md"
    generate_markdown_report(report, md_path)
    
    # 打印汇总
    print("\n" + "=" * 60)
    print("质量检查完成!")
    print("=" * 60)
    s = report["summary"]
    print(f"总计检查: {s['total_checked']} 个 PDF")
    print(f"  ✓ 正常: {s['ok']}")
    print(f"  ⚠️ 警告: {s['warning']}")
    print(f"  ✗ 错误: {s['error']}")
    print(f"\n报告文件:")
    print(f"  JSON: {json_path}")
    print(f"  Markdown: {md_path}")
    print("=" * 60)
    
    # 退出码
    if s['error'] > 0:
        sys.exit(2)
    elif s['warning'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

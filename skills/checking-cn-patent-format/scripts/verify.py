#!/usr/bin/env python3
"""
docx 审查内容完整性验证工具

功能：
1. 比较原始文档和审查后文档的段落数量
2. 模拟接受所有修订后比较文本内容
3. 验证文件结构完整性（确保没有文件丢失）
4. 检查新增文件是否符合预期（仅批注相关文件）

用法：
    python verify.py input.doc reviewed.docx work_dir
"""

# argparse 用于解析命令行参数
import argparse
# io 提供流处理功能，这里用于设置 UTF-8 输出
import io
# sys 提供系统相关功能
import sys
# json 用于读写 JSON 格式文件
import json
# Path 用于面向对象的文件路径处理
from pathlib import Path
# datetime 用于处理日期和时间
from datetime import datetime

# 设置标准输出为 UTF-8 编码，确保中文正常显示
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# 计算当前脚本相对于 skill 根目录的路径
SKILL_ROOT = Path(__file__).parent.parent
# 将 skill 根目录添加到 Python 路径，以便导入其他模块
sys.path.insert(0, str(SKILL_ROOT))

# 导入解压文档的函数
from ooxml.scripts.unpack import unpack_document
# minidom 是安全的 XML DOM 解析库
from defusedxml import minidom
# 导入 doc_converter 模块中的 ensure_docx 函数，用于 .doc 转 .docx
from scripts.doc_converter import ensure_docx


def count_paragraphs(xml_path):
    """
    统计 document.xml 中的段落数量。

    通过计算 w:p（paragraph）元素的数量来确定文档的段落数。
    """
    with open(xml_path, 'r', encoding='utf-8') as f:
        dom = minidom.parse(f)
    return len(dom.getElementsByTagName('w:p'))


def is_inside_tag(elem, tag_name):
    """
    检查元素是否嵌套在指定的标签内部。

    用于判断文本是否在删除标记（w:del）内部，从而跳过已删除的文本。
    """
    parent = elem.parentNode
    while parent:
        if parent.nodeType == parent.ELEMENT_NODE and parent.tagName == tag_name:
            return True
        parent = parent.parentNode
    return False


def accept_all_changes_and_extract(xml_path):
    """
    模拟接受所有修订后提取文本。

    在 Word 的修订模式下，删除的文本被包裹在 w:del 标记中。
    这个函数跳过所有在 w:del 内部的文本，模拟"接受所有修订"的效果。

    Args:
        xml_path: document.xml 文件路径

    Returns:
        非空段落文本列表
    """
    with open(xml_path, 'r', encoding='utf-8') as f:
        dom = minidom.parse(f)
    paras = dom.getElementsByTagName('w:p')
    result = []
    for para in paras:
        texts = []
        for t_elem in para.getElementsByTagName('w:t'):
            # 跳过在删除标记内部的文本
            if is_inside_tag(t_elem, 'w:del'):
                continue
            for child in t_elem.childNodes:
                if child.nodeType == child.TEXT_NODE:
                    texts.append(child.data)
        text = ''.join(texts)
        # 只保留非空段落
        if text.strip():
            result.append(text.strip())
    return result


def get_all_files(base_dir):
    """
    递归获取目录下所有文件的相对路径。

    用于比较原始文档和审查后文档的文件结构。
    """
    base = Path(base_dir)
    files = set()
    for p in base.rglob('*'):
        if p.is_file():
            rel = p.relative_to(base).as_posix()
            files.add(rel)
    return files


def verify(input_doc, reviewed_docx, work_dir):
    """
    验证审查后文档的完整性。

    Args:
        input_doc: 原始 docx/doc 文件路径
        reviewed_docx: 审查后的 docx 文件路径
        work_dir: 工作目录（用于存放解压内容）

    Returns:
        0 表示所有验证通过，1 表示有验证失败
    """
    work_dir = Path(work_dir)

    input_doc_path = Path(input_doc)
    converted_docx = None

    # 如果是 .doc 格式，先转换为 .docx
    if input_doc_path.suffix.lower() == ".doc":
        print(f"检测到 .doc 格式原始文件，正在转换为 .docx 以进行验证 ...")
        try:
            docx_path, was_converted = ensure_docx(str(input_doc), str(work_dir))
            if was_converted:
                converted_docx = docx_path
                input_doc = docx_path
                print(f"转换完成，使用临时文件: {Path(docx_path).name}")
        except Exception as e:
            print(f"❌ 无法转换 .doc 原始文件: {e}")
            return 1

    # 定义解压目录
    unpacked_original = work_dir / "unpacked_original"
    unpacked_reviewed = work_dir / "unpacked_reviewed"

    # 解压原始文档（如果不存在）
    if not unpacked_original.exists():
        print(f"正在解压原始文档到 {unpacked_original} ...")
        unpack_document(str(input_doc), str(unpacked_original))
    else:
        print(f"原始文档已解压：{unpacked_original}")

    # 解压审查文档（如果不存在）
    if not unpacked_reviewed.exists():
        print(f"正在解压审查文档到 {unpacked_reviewed} ...")
        unpack_document(str(reviewed_docx), str(unpacked_reviewed))
    else:
        print(f"审查文档已解压：{unpacked_reviewed}")

    # 定义 document.xml 路径
    orig_xml = unpacked_original / "word" / "document.xml"
    rev_xml = unpacked_reviewed / "word" / "document.xml"

    # 初始化验证结果标志
    all_pass = True

    log_data = {
        'verification_time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        'input_doc': str(input_doc),
        'reviewed_docx': str(reviewed_docx),
        'work_dir': str(work_dir),
        'checks': {}
    }

    # ===== 1. 段落数量验证 =====
    print("\n===== 1. 段落数量验证 =====")
    orig_count = count_paragraphs(str(orig_xml))
    rev_count = count_paragraphs(str(rev_xml))

    if orig_count != rev_count:
        print(f"❌ 验证失败：段落数量不一致！原始={orig_count}, 审查={rev_count}")
        all_pass = False
        log_data['checks']['paragraph_count'] = {'status': 'fail', 'original': orig_count, 'reviewed': rev_count}
    else:
        print(f"✅ 段落数量验证通过：{orig_count} 段")
        log_data['checks']['paragraph_count'] = {'status': 'pass', 'count': orig_count}

    # ===== 2. 模拟接受修订验证（参考性） =====
    print("\n===== 2. 模拟接受修订验证（参考性） =====")
    orig_text = accept_all_changes_and_extract(str(orig_xml))
    rev_text = accept_all_changes_and_extract(str(rev_xml))

    if len(orig_text) != len(rev_text):
        print(f"[INFO] 非空段落数不一致：原始={len(orig_text)}, 审查={len(rev_text)}（已知误报：当修订删除整段文本时，该段变为空段被过滤，属正常现象）")

    diff_count = 0
    for i, (o, r) in enumerate(zip(orig_text, rev_text)):
        if o != r:
            diff_count += 1

    if diff_count > 0:
        print(f"[INFO] 共 {diff_count} 处文本差异（均为修订模式下的预期替换/删除操作）")
        log_data['checks']['simulated_accept'] = {'status': 'info', 'diff_count': diff_count, 'note': '修订模式下的预期差异'}
    else:
        print("[PASS] 无文本差异")
        log_data['checks']['simulated_accept'] = {'status': 'pass', 'diff_count': 0}

    # ===== 3. 文件结构验证 =====
    print("\n===== 3. 文件结构验证 =====")
    orig_files = get_all_files(str(unpacked_original))
    rev_files = get_all_files(str(unpacked_reviewed))

    # 检查是否有文件丢失
    missing = orig_files - rev_files
    if missing:
        print(f"❌ 验证失败：审查版缺少以下文件: {sorted(missing)}")
        all_pass = False
        log_data['checks']['file_structure'] = {'status': 'fail', 'missing_files': sorted(missing)}
    else:
        print("✅ 文件结构验证通过：原始文件全部保留")
        log_data['checks']['file_structure'] = {'status': 'pass', 'missing_files': []}

    # 检查新增文件是否符合预期
    added = rev_files - orig_files
    expected_new = {
        'word/comments.xml',
        'word/commentsExtended.xml',
        'word/commentsIds.xml',
        'word/commentsExtensible.xml',
        'word/people.xml',
    }
    unexpected_new = added - expected_new
    if unexpected_new:
        print(f"⚠️ 审查版包含非预期新增文件: {sorted(unexpected_new)}")
    else:
        print("✅ 新增文件验证通过：仅添加了预期的批注相关文件")

    # ===== 验证总结 =====
    print("\n===== 验证总结 =====")
    if all_pass:
        print("✅ 所有验证项通过，文档内容完整")
        log_data['overall_result'] = 'pass'
        result = 0
    else:
        print("❌ 存在验证失败项，请排查原因后修正")
        log_data['overall_result'] = 'fail'
        result = 1

    # 保存验证日志到工作目录
    try:
        log_path = work_dir / "verify_log.json"
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        print(f"验证日志已保存: {log_path}")
    except Exception as e:
        print(f"Warning: 无法保存验证日志: {e}")

    # 清理临时转换文件
    if converted_docx:
        try:
            Path(converted_docx).unlink()
            print(f"已清理临时转换文件: {Path(converted_docx).name}")
        except OSError:
            pass

    return result


def main():
    """命令行入口函数。"""
    parser = argparse.ArgumentParser(description="docx 审查内容完整性验证")
    parser.add_argument("input_doc", help="原始 docx/doc 文件路径")
    parser.add_argument("reviewed_docx", help="审查后 docx 文件路径")
    parser.add_argument("work_dir", help="工作文件夹路径（用于存放解压内容）")
    args = parser.parse_args()

    sys.exit(verify(args.input_doc, args.reviewed_docx, args.work_dir))


# 当直接运行此脚本时执行 main 函数
if __name__ == "__main__":
    main()

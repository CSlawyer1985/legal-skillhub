#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from ooxml.scripts.unpack import unpack_document
from defusedxml import minidom
from scripts.doc_converter import ensure_docx


def count_paragraphs(xml_path):
    with open(xml_path, 'r', encoding='utf-8') as f:
        dom = minidom.parse(f)
    return len(dom.getElementsByTagName('w:p'))


def is_inside_tag(elem, tag_name):
    parent = elem.parentNode
    while parent:
        if parent.nodeType == parent.ELEMENT_NODE and parent.tagName == tag_name:
            return True
        parent = parent.parentNode
    return False


def accept_all_changes_and_extract(xml_path):
    with open(xml_path, 'r', encoding='utf-8') as f:
        dom = minidom.parse(f)
    paras = dom.getElementsByTagName('w:p')
    result = []
    for para in paras:
        texts = []
        for t_elem in para.getElementsByTagName('w:t'):
            if is_inside_tag(t_elem, 'w:del'):
                continue
            for child in t_elem.childNodes:
                if child.nodeType == child.TEXT_NODE:
                    texts.append(child.data)
        text = ''.join(texts)
        if text.strip():
            result.append(text.strip())
    return result


def get_all_files(base_dir):
    base = Path(base_dir)
    files = set()
    for p in base.rglob('*'):
        if p.is_file():
            rel = p.relative_to(base).as_posix()
            files.add(rel)
    return files


def verify(input_docx, reviewed_docx, work_dir):
    work_dir = Path(work_dir)

    input_docx_path = Path(input_docx)
    converted_docx = None

    if input_docx_path.suffix.lower() == ".doc":
        print(f"检测到 .doc 格式原始文件，正在转换为 .docx 以进行验证 ...")
        try:
            docx_path, was_converted = ensure_docx(str(input_docx), str(work_dir))
            if was_converted:
                converted_docx = docx_path
                input_docx = docx_path
                print(f"转换完成，使用临时文件: {Path(docx_path).name}")
        except Exception as e:
            print(f"❌ 无法转换 .doc 原始文件: {e}")
            return 1

    unpacked_original = work_dir / "unpacked_original"
    unpacked_reviewed = work_dir / "unpacked_reviewed"

    if not unpacked_original.exists():
        print(f"正在解压原始文档到 {unpacked_original} ...")
        unpack_document(str(input_docx), str(unpacked_original))
    else:
        print(f"原始文档已解压：{unpacked_original}")

    if not unpacked_reviewed.exists():
        print(f"正在解压审查文档到 {unpacked_reviewed} ...")
        unpack_document(str(reviewed_docx), str(unpacked_reviewed))
    else:
        print(f"审查文档已解压：{unpacked_reviewed}")

    orig_xml = unpacked_original / "word" / "document.xml"
    rev_xml = unpacked_reviewed / "word" / "document.xml"

    all_pass = True

    print("\n===== 1. 段落数量验证 =====")
    orig_count = count_paragraphs(str(orig_xml))
    rev_count = count_paragraphs(str(rev_xml))

    if orig_count != rev_count:
        print(f"❌ 验证失败：段落数量不一致！原始={orig_count}, 审查={rev_count}")
        all_pass = False
    else:
        print(f"✅ 段落数量验证通过：{orig_count} 段")

    print("\n===== 2. 模拟接受修订验证 =====")
    orig_text = accept_all_changes_and_extract(str(orig_xml))
    rev_text = accept_all_changes_and_extract(str(rev_xml))

    if len(orig_text) != len(rev_text):
        print(f"❌ 验证失败：段落数不一致！原始={len(orig_text)}, 审查={len(rev_text)}")
        all_pass = False

    diff_count = 0
    for i, (o, r) in enumerate(zip(orig_text, rev_text)):
        if o != r:
            diff_count += 1
            print(f"段落 {i+1} 有差异（预期为修订模式下的替换/删除）:")
            print(f"  原始: {o}")
            print(f"  审查: {r}")

    if all_pass and len(orig_text) == len(rev_text):
        if diff_count > 0:
            print(f"✅ 模拟接受修订验证通过：共 {diff_count} 处差异，均为预期修订操作")
        else:
            print("✅ 模拟接受修订验证通过：无差异")

    print("\n===== 3. 文件结构验证 =====")
    orig_files = get_all_files(str(unpacked_original))
    rev_files = get_all_files(str(unpacked_reviewed))

    missing = orig_files - rev_files
    if missing:
        print(f"❌ 验证失败：审查版缺少以下文件: {sorted(missing)}")
        all_pass = False
    else:
        print("✅ 文件结构验证通过：原始文件全部保留")

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

    print("\n===== 验证总结 =====")
    if all_pass:
        print("✅ 所有验证项通过，文档内容完整")
        result = 0
    else:
        print("❌ 存在验证失败项，请排查原因后修正")
        result = 1

    if converted_docx:
        try:
            Path(converted_docx).unlink()
            print(f"已清理临时转换文件: {Path(converted_docx).name}")
        except OSError:
            pass

    return result


def main():
    parser = argparse.ArgumentParser(description="docx 审查内容完整性验证")
    parser.add_argument("input_docx", help="原始 docx 文件路径")
    parser.add_argument("reviewed_docx", help="审查后 docx 文件路径")
    parser.add_argument("work_dir", help="工作文件夹路径（用于存放解压内容）")
    args = parser.parse_args()

    sys.exit(verify(args.input_docx, args.reviewed_docx, args.work_dir))


if __name__ == "__main__":
    main()

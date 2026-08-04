#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跳过批注重定位工具

功能：
1. 读取被跳过的审查意见（skipped_reviews_<timestamp>.json）
2. 读取去重后的审查意见（reviews_<timestamp>.json）
3. 识别每个被跳过条目所属的section章节
4. 在相应section章节结尾处插入"额外批注"锚定文本
5. 以"额外批注"为定位点，添加原被跳过的批注内容
6. 生成去重后批注数据文件（deduplicated_comments_<timestamp>.json）
7. 记录所有重定位操作到日志

用法：
    python skip_relocator.py --input-doc "<input_doc>" \
        --reviewed-docx "<input_dir>/<input_stem>_ReviewOut_<timestamp>.docx" \
        --work-dir "<work_dir>" --timestamp "<timestamp>" \
        --author "checking-cn-patent-format"
"""

import sys
import io
import json
import argparse
import tempfile
from pathlib import Path
from datetime import datetime, timezone

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
except (AttributeError, io.UnsupportedOperation):
    pass

SKILL_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from ooxml.scripts.unpack import unpack_document
from ooxml.scripts.pack import pack_document
from scripts.document import Document
from scripts.doc_converter import ensure_docx


ANCHOR_TEXT = "额外批注"

SECTION_ORDER = ["摘要", "权利要求书", "说明书", "说明书附图", "摘要附图", "全文"]


def _escape_xml(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _detect_section(para_text, para_index, total_paragraphs):
    stripped = para_text.strip()
    import re
    if re.search(r'说\s*明\s*书\s*摘\s*要', stripped):
        return "摘要"
    if re.search(r'摘\s*要\s*附\s*图', stripped):
        return "摘要附图"
    if re.search(r'权\s*利\s*要\s*求\s*书', stripped):
        return "权利要求书"
    if stripped in ('技术领域', '背景技术', '发明内容', '实用新型内容', '附图说明', '具体实施方式'):
        return "说明书"
    if re.search(r'说\s*明\s*书\s*附\s*图', stripped):
        return "说明书附图"
    if re.match(r'^1\s*[.、]\s*', stripped):
        return "权利要求书"
    return None


def _find_section_boundaries(paragraphs, known_sections=None):
    """
    查找文档中各章节的边界。

    遍历所有段落，根据章节标题特征确定每个章节的起始位置。
    返回章节名称到 (起始索引, 结束索引) 的映射。

    Args:
        paragraphs: 所有段落元素列表
        known_sections: 可选，从header_sections.json获取的已知章节元数据列表。
                       用于检测零段落章节（如摘要附图）。(BUG-006修复)

    【代码同步】此函数与 review_adder.py 中的同名函数保持逻辑一致。
                 同步版本: v2.1-BUG006-fix
                 修改任一文件时请同步更新另一文件。
    """
    import re
    section_starts = {}
    for i, para in enumerate(paragraphs):
        para_text = _get_para_text(para)
        section = _detect_section(para_text, i, len(paragraphs))
        if section and section not in section_starts:
            section_starts[section] = i

    # 【BUG-006修复】基于已知章节元数据补充零段落章节
    if known_sections and isinstance(known_sections, list):
        zero_para_sections = []
        for sec in known_sections:
            sec_name = sec.get('section_name', '')
            para_count = sec.get('paragraph_count', 0)
            if para_count == 0 and sec_name and sec_name not in section_starts:
                zero_para_sections.append((sec_name, known_sections.index(sec)))

        if zero_para_sections:
            ordered_detected = sorted(section_starts.items(), key=lambda x: x[1])
            for zsec_name, zsec_idx in zero_para_sections:
                inserted = False
                for i, (detected_name, detected_pos) in enumerate(ordered_detected):
                    det_sec = next((s for s in known_sections if s.get('section_name') == detected_name), None)
                    det_idx_in_known = known_sections.index(det_sec) if det_sec else len(known_sections)
                    if zsec_idx < det_idx_in_known:
                        if i > 0:
                            prev_end = ordered_detected[i - 1][1]
                            section_starts[zsec_name] = prev_end
                            inserted = True
                        elif i == 0:
                            section_starts[zsec_name] = 0
                            inserted = True
                        break
                if not inserted and zsec_name not in section_starts:
                    if ordered_detected:
                        last_pos = ordered_detected[-1][1]
                        section_starts[zsec_name] = last_pos
                    else:
                        section_starts[zsec_name] = 0

    ordered = sorted(section_starts.items(), key=lambda x: x[1])

    section_ranges = {}
    for idx, (name, start) in enumerate(ordered):
        if idx + 1 < len(ordered):
            end = ordered[idx + 1][1]
        else:
            end = len(paragraphs)
        section_ranges[name] = (start, end)

    if not section_ranges:
        section_ranges["全文"] = (0, len(paragraphs))
        return section_ranges

    first_section_start = ordered[0][1]
    if first_section_start > 0:
        if "摘要" not in section_ranges:
            section_ranges["摘要"] = (0, first_section_start)

    if "权利要求书" not in section_ranges and "摘要" in section_ranges:
        abstract_end = section_ranges["摘要"][1]
        for i in range(abstract_end, len(paragraphs)):
            para_text = _get_para_text(paragraphs[i]).strip()
            if re.match(r'^\d+\s*[.、]\s*', para_text):
                section_ranges["权利要求书"] = (i, section_ranges.get("说明书", (len(paragraphs),))[0])
                break

    if "摘要附图" not in section_ranges and "摘要" in section_ranges and "权利要求书" in section_ranges:
        abstract_end = section_ranges["摘要"][1]
        claims_start = section_ranges["权利要求书"][0]
        for i in range(abstract_end, claims_start):
            para_text = _get_para_text(paragraphs[i]).strip()
            if re.match(r'^图\s*\d', para_text) or re.search(r'摘\s*要\s*附\s*图', para_text):
                section_ranges["摘要附图"] = (i, claims_start)
                break

    if "说明书附图" not in section_ranges and "说明书" in section_ranges:
        description_end = section_ranges["说明书"][1]
        for i in range(description_end, len(paragraphs)):
            para_text = _get_para_text(paragraphs[i]).strip()
            if re.match(r'^图\s*\d', para_text) or re.search(r'说\s*明\s*书\s*附\s*图', para_text):
                section_ranges["说明书附图"] = (i, len(paragraphs))
                break

    return section_ranges


def _get_para_text(para_elem):
    texts = []
    for t_elem in para_elem.getElementsByTagName("w:t"):
        for child in t_elem.childNodes:
            if child.nodeType == child.TEXT_NODE and child.data:
                texts.append(child.data)
    return "".join(texts)


def _is_in_deletion(elem):
    parent = elem.parentNode
    visited = set()
    depth = 0
    while parent is not None:
        if depth >= 100:
            return False
        node_id = id(parent)
        if node_id in visited:
            return False
        visited.add(node_id)
        depth += 1
        if parent.nodeType == parent.ELEMENT_NODE and parent.tagName == "w:del":
            return True
        parent = parent.parentNode
    return False


def _insert_anchor_paragraph_at_section_end(doc, section_ranges, section_name, paragraphs):
    if section_name not in section_ranges:
        return None, None

    start_idx, end_idx = section_ranges[section_name]

    last_para = None
    for i in range(end_idx - 1, start_idx - 1, -1):
        if i < len(paragraphs) and not _is_in_deletion(paragraphs[i]):
            last_para = paragraphs[i]
            break

    if last_para is None:
        return None, None

    anchor_para_xml = f'''<w:p>
  <w:r>
    <w:t xml:space="preserve">{_escape_xml(ANCHOR_TEXT)}</w:t>
  </w:r>
</w:p>'''

    editor = doc["word/document.xml"]
    new_nodes = editor.insert_after(last_para, anchor_para_xml)

    anchor_para = None
    for node in new_nodes:
        if node.nodeType == node.ELEMENT_NODE and node.tagName == "w:p":
            anchor_para = node
            break

    return anchor_para, end_idx


def _add_comment_to_anchor(doc, anchor_para, comment_text):
    runs = anchor_para.getElementsByTagName("w:r")
    if not runs:
        return None

    first_run = runs[0]
    last_run = runs[-1]

    doc.add_comment(start=first_run, end=last_run, text=comment_text)
    return True


def _build_deduplicated_comments(reviews, skipped_reviews, relocation_log, work_dir, timestamp, input_doc):
    now_iso = datetime.now().astimezone().isoformat()

    reviews_path = work_dir / f"reviews_{timestamp}.json"
    skipped_path = work_dir / f"skipped_reviews_{timestamp}.json" if skipped_reviews else None
    dedup_log_path = work_dir / f"reviews_{timestamp}_dedup_log.json"

    metadata = {
        "source_file": str(reviews_path) if reviews_path.exists() else None,
        "skipped_file": str(skipped_path) if skipped_path and skipped_path.exists() else None,
        "dedup_log_file": str(dedup_log_path) if dedup_log_path.exists() else None,
        "processing_timestamp": now_iso,
        "input_doc": str(input_doc),
        "work_dir": str(work_dir),
        "timestamp": timestamp
    }

    total_before = len(reviews) + len(skipped_reviews) if skipped_reviews else len(reviews)
    total_after = len(reviews)

    dedup_summary = {
        "total_before_dedup": total_before,
        "total_after_dedup": total_after,
        "total_removed": total_before - total_after,
        "removal_rate": round((total_before - total_after) / total_before * 100, 2) if total_before > 0 else 0,
        "strategies_applied": [],
        "conflicts_resolved": 0,
        "skipped_count": len(skipped_reviews) if skipped_reviews else 0
    }

    if dedup_log_path.exists():
        try:
            with open(dedup_log_path, 'r', encoding='utf-8') as f:
                dedup_log_data = json.load(f)
            if 'summary' in dedup_log_data:
                summary = dedup_log_data['summary']
                dedup_summary['strategies_applied'] = summary.get('strategies_used', [])
            dedup_summary['total_before_dedup'] = dedup_log_data.get('summary', {}).get('total_reviews_before', total_before)
            dedup_summary['total_removed'] = dedup_log_data.get('summary', {}).get('total_removed', total_before - total_after)
            dedup_summary['removal_rate'] = dedup_log_data.get('summary', {}).get('removal_rate', dedup_summary['removal_rate'])
        except (json.JSONDecodeError, KeyError):
            pass

    comments = []

    for idx, review in enumerate(reviews):
        comment_entry = {
            "original_index": idx,
            "comment_id": None,
            "section": review.get("section", ""),
            "paragraph_index": review.get("paragraph_index"),
            "claim_number": review.get("claim_number"),
            "context": review.get("context", ""),
            "highlight_text": review.get("highlight_text"),
            "old_text": review.get("old_text"),
            "new_text": review.get("new_text"),
            "action_type": review.get("action_type", "comment"),
            "occurrence": review.get("occurrence"),
            "issue": review.get("issue", ""),
            "suggestion": review.get("suggestion", ""),
            "rule_id": review.get("rule_id"),
            "severity": review.get("severity"),
            "status": "added",
            "skip_reason": None,
            "relocation_info": None
        }
        comments.append(comment_entry)

    if skipped_reviews:
        for skip_review in skipped_reviews:
            skip_reason = skip_review.get("skip_reason", "other")
            section = skip_review.get("section", "")

            relocated = False
            for log_entry in relocation_log:
                if (log_entry.get("section") == section and
                    log_entry.get("issue") == skip_review.get("issue") and
                    log_entry.get("context") == skip_review.get("context")):
                    relocated = True
                    comment_entry = {
                        "original_index": None,
                        "comment_id": log_entry.get("new_comment_id"),
                        "section": section,
                        "paragraph_index": log_entry.get("new_paragraph_index"),
                        "claim_number": skip_review.get("claim_number"),
                        "context": skip_review.get("context", ""),
                        "highlight_text": ANCHOR_TEXT,
                        "old_text": skip_review.get("old_text"),
                        "new_text": skip_review.get("new_text"),
                        "action_type": "comment",
                        "occurrence": None,
                        "issue": skip_review.get("issue", ""),
                        "suggestion": skip_review.get("suggestion", ""),
                        "rule_id": skip_review.get("rule_id"),
                        "severity": skip_review.get("severity"),
                        "status": "relocated",
                        "skip_reason": None,
                        "relocation_info": {
                            "original_section": section,
                            "anchor_text": ANCHOR_TEXT,
                            "new_paragraph_index": log_entry.get("new_paragraph_index"),
                            "relocation_timestamp": log_entry.get("relocation_timestamp")
                        }
                    }
                    comments.append(comment_entry)
                    break

            if not relocated:
                comment_entry = {
                    "original_index": None,
                    "comment_id": None,
                    "section": section,
                    "paragraph_index": skip_review.get("paragraph_index"),
                    "claim_number": skip_review.get("claim_number"),
                    "context": skip_review.get("context", ""),
                    "highlight_text": skip_review.get("highlight_text"),
                    "old_text": skip_review.get("old_text"),
                    "new_text": skip_review.get("new_text"),
                    "action_type": skip_review.get("action_type", "comment"),
                    "occurrence": skip_review.get("occurrence"),
                    "issue": skip_review.get("issue", ""),
                    "suggestion": skip_review.get("suggestion", ""),
                    "rule_id": skip_review.get("rule_id"),
                    "severity": skip_review.get("severity"),
                    "status": "skipped",
                    "skip_reason": skip_reason,
                    "relocation_info": None
                }
                comments.append(comment_entry)

    result = {
        "metadata": metadata,
        "deduplication_summary": dedup_summary,
        "comments": comments
    }

    return result


def relocate_skipped_comments(input_doc, reviewed_docx, work_dir, timestamp, author="checking-cn-patent-format"):
    work_dir = Path(work_dir)
    input_doc_path = Path(input_doc)
    reviewed_docx_path = Path(reviewed_docx)

    skipped_file = work_dir / f"skipped_reviews_{timestamp}.json"
    reviews_file = work_dir / f"reviews_{timestamp}.json"

    if not skipped_file.exists():
        print(f"未找到跳过条目文件: {skipped_file}，无需重定位")
        reviews = []
        skipped_reviews = []
        relocation_log = []

        dedup_data = _build_deduplicated_comments(reviews, skipped_reviews, relocation_log, work_dir, timestamp, input_doc)
        dedup_output = work_dir / f"deduplicated_comments_{timestamp}.json"
        with open(dedup_output, 'w', encoding='utf-8') as f:
            json.dump(dedup_data, f, ensure_ascii=False, indent=2)
        print(f"去重批注数据已保存: {dedup_output}")

        return {
            "total_skipped": 0,
            "relocated_count": 0,
            "failed_count": 0,
            "dedup_output": str(dedup_output)
        }

    with open(skipped_file, 'r', encoding='utf-8') as f:
        skipped_reviews = json.load(f)

    with open(reviews_file, 'r', encoding='utf-8') as f:
        reviews = json.load(f)

    if not skipped_reviews:
        print("跳过条目为空，无需重定位")
        relocation_log = []
        dedup_data = _build_deduplicated_comments(reviews, skipped_reviews, relocation_log, work_dir, timestamp, input_doc)
        dedup_output = work_dir / f"deduplicated_comments_{timestamp}.json"
        with open(dedup_output, 'w', encoding='utf-8') as f:
            json.dump(dedup_data, f, ensure_ascii=False, indent=2)
        print(f"去重批注数据已保存: {dedup_output}")

        return {
            "total_skipped": 0,
            "relocated_count": 0,
            "failed_count": 0,
            "dedup_output": str(dedup_output)
        }

    print(f"发现 {len(skipped_reviews)} 条跳过条目，开始重定位处理...")

    converted_docx = None
    actual_input = reviewed_docx_path

    if reviewed_docx_path.suffix.lower() == ".doc":
        print(f"检测到 .doc 格式文件，正在转换为 .docx ...")
        try:
            docx_path, was_converted = ensure_docx(str(reviewed_docx_path), str(work_dir))
            if was_converted:
                converted_docx = docx_path
                actual_input = Path(docx_path)
                print(f"转换完成，使用临时文件: {actual_input.name}")
        except Exception as e:
            raise RuntimeError(f"无法转换 .doc 文件: {e}")

    relocation_log = []
    relocated_count = 0
    failed_count = 0

    with tempfile.TemporaryDirectory(prefix="skip_relocate_") as temp_dir:
        unpacked_dir = Path(temp_dir) / "unpacked"

        print(f"正在解压 {actual_input.name} ...")
        unpack_document(str(actual_input), str(unpacked_dir))

        print(f"正在初始化文档编辑器 ...")
        doc = Document(
            str(unpacked_dir),
            track_revisions=True,
            author=author,
            initials="MA"
        )

        dom = doc["word/document.xml"].dom
        paragraphs = list(dom.getElementsByTagName("w:p"))

        # 【BUG-006修复】尝试加载header_sections.json获取零段落章节元数据
        known_sections = None
        header_files = sorted(work_dir.glob("header_sections_*.json"))
        if header_files:
            try:
                with open(header_files[0], 'r', encoding='utf-8') as hf:
                    header_data = json.load(hf)
                known_sections = header_data.get('sections', [])
                if known_sections:
                    print(f"    [BUG-006修复] 已加载章节元数据 ({len(known_sections)} 个章节，含零段落章节)")
            except Exception:
                pass

        section_ranges = _find_section_boundaries(paragraphs, known_sections=known_sections)
        print(f"已识别章节范围: {[(k, v) for k, v in section_ranges.items()]}")

        section_skipped = {}
        for skip_review in skipped_reviews:
            section = skip_review.get("section", "")
            if section:
                section_skipped.setdefault(section, []).append(skip_review)

        anchor_inserted = {}

        for section_name, skipped_items in section_skipped.items():
            print(f"\n处理章节 [{section_name}]：{len(skipped_items)} 条跳过条目")

            if section_name not in section_ranges:
                print(f"  ⚠ 章节 '{section_name}' 未在文档中找到，跳过")
                for item in skipped_items:
                    relocation_log.append({
                        "section": section_name,
                        "issue": item.get("issue", ""),
                        "context": item.get("context", ""),
                        "original_paragraph_index": item.get("paragraph_index"),
                        "status": "failed",
                        "reason": f"章节 '{section_name}' 未在文档中找到",
                        "relocation_timestamp": datetime.now().astimezone().isoformat()
                    })
                    failed_count += 1
                continue

            anchor_para, para_idx = _insert_anchor_paragraph_at_section_end(
                doc, section_ranges, section_name, paragraphs
            )

            if anchor_para is None:
                print(f"  ⚠ 无法在章节 '{section_name}' 结尾插入锚定文本，跳过")
                for item in skipped_items:
                    relocation_log.append({
                        "section": section_name,
                        "issue": item.get("issue", ""),
                        "context": item.get("context", ""),
                        "original_paragraph_index": item.get("paragraph_index"),
                        "status": "failed",
                        "reason": "无法插入锚定文本",
                        "relocation_timestamp": datetime.now().astimezone().isoformat()
                    })
                    failed_count += 1
                continue

            anchor_inserted[section_name] = {
                "anchor_para": anchor_para,
                "paragraph_index": para_idx
            }
            print(f"  ✓ 已在章节 [{section_name}] 结尾插入锚定文本 '{ANCHOR_TEXT}'")

            for skip_item in skipped_items:
                issue = skip_item.get("issue", "")
                suggestion = skip_item.get("suggestion", "")
                section = skip_item.get("section", "")
                claim_number = skip_item.get("claim_number")

                comment_text = ""
                if section == "权利要求书" and claim_number is not None:
                    comment_text = f"权利要求{claim_number}: "
                comment_text += f"{issue}\n修改建议：{suggestion}"

                try:
                    result = _add_comment_to_anchor(doc, anchor_para, comment_text)
                    if result:
                        new_comment_id = doc.next_comment_id - 1
                        relocation_log.append({
                            "section": section_name,
                            "issue": issue,
                            "context": skip_item.get("context", ""),
                            "original_paragraph_index": skip_item.get("paragraph_index"),
                            "new_paragraph_index": para_idx,
                            "new_comment_id": new_comment_id,
                            "anchor_text": ANCHOR_TEXT,
                            "status": "relocated",
                            "relocation_timestamp": datetime.now().astimezone().isoformat()
                        })
                        relocated_count += 1
                        print(f"  ✓ 已重定位批注: {issue[:40]}...")
                    else:
                        relocation_log.append({
                            "section": section_name,
                            "issue": issue,
                            "context": skip_item.get("context", ""),
                            "original_paragraph_index": skip_item.get("paragraph_index"),
                            "status": "failed",
                            "reason": "批注添加失败",
                            "relocation_timestamp": datetime.now().astimezone().isoformat()
                        })
                        failed_count += 1
                        print(f"  ⚠ 批注添加失败: {issue[:40]}...")
                except Exception as e:
                    relocation_log.append({
                        "section": section_name,
                        "issue": issue,
                        "context": skip_item.get("context", ""),
                        "original_paragraph_index": skip_item.get("paragraph_index"),
                        "status": "failed",
                        "reason": str(e),
                        "relocation_timestamp": datetime.now().astimezone().isoformat()
                    })
                    failed_count += 1
                    print(f"  ❌ 批注添加异常: {type(e).__name__}: {str(e)}")

        print(f"\n正在保存修改 ...")
        doc.save()

        print(f"正在打包为 {reviewed_docx_path.name} ...")
        reviewed_docx_path.parent.mkdir(parents=True, exist_ok=True)
        pack_document(str(unpacked_dir), str(reviewed_docx_path), validate=False)

    if converted_docx:
        try:
            Path(converted_docx).unlink()
            print(f"已清理临时转换文件: {Path(converted_docx).name}")
        except OSError:
            pass

    log_output = work_dir / f"relocation_log_{timestamp}.json"
    log_data = {
        "processing_timestamp": datetime.now().astimezone().isoformat(),
        "input_doc": str(input_doc),
        "reviewed_docx": str(reviewed_docx),
        "total_skipped": len(skipped_reviews),
        "relocated_count": relocated_count,
        "failed_count": failed_count,
        "anchor_text": ANCHOR_TEXT,
        "relocations": relocation_log
    }
    with open(log_output, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    print(f"重定位日志已保存: {log_output}")

    dedup_data = _build_deduplicated_comments(reviews, skipped_reviews, relocation_log, work_dir, timestamp, input_doc)
    dedup_output = work_dir / f"deduplicated_comments_{timestamp}.json"
    with open(dedup_output, 'w', encoding='utf-8') as f:
        json.dump(dedup_data, f, ensure_ascii=False, indent=2)
    print(f"去重批注数据已保存: {dedup_output}")

    print(f"\n重定位处理完成：共 {len(skipped_reviews)} 条跳过条目，成功重定位 {relocated_count} 条，失败 {failed_count} 条")

    return {
        "total_skipped": len(skipped_reviews),
        "relocated_count": relocated_count,
        "failed_count": failed_count,
        "log_output": str(log_output),
        "dedup_output": str(dedup_output)
    }


def main():
    parser = argparse.ArgumentParser(description="跳过批注重定位工具")
    parser.add_argument("--input-doc", required=True, help="原始输入文档路径")
    parser.add_argument("--reviewed-docx", required=True, help="审查后的docx文件路径")
    parser.add_argument("--work-dir", required=True, help="工作目录路径")
    parser.add_argument("--timestamp", required=True, help="时间戳")
    parser.add_argument("--author", default="checking-cn-patent-format", help="批注作者名称")

    args = parser.parse_args()

    result = relocate_skipped_comments(
        input_doc=args.input_doc,
        reviewed_docx=args.reviewed_docx,
        work_dir=args.work_dir,
        timestamp=args.timestamp,
        author=args.author
    )

    if result["failed_count"] > 0 and result["relocated_count"] == 0:
        sys.exit(1)

    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
import argparse
import io
import json
import re
import sys
import tempfile
from pathlib import Path

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


def _is_in_deletion(elem):
    parent = elem.parentNode
    while parent:
        if parent.nodeType == parent.ELEMENT_NODE and parent.tagName == "w:del":
            return True
        parent = parent.parentNode
    return False


def _get_run_text(r_elem):
    text = ""
    for t_node in r_elem.getElementsByTagName("w:t"):
        for child in t_node.childNodes:
            if child.nodeType == child.TEXT_NODE:
                text += child.data
    return text


def _get_run_rpr(r_elem):
    rpr_nodes = r_elem.getElementsByTagName("w:rPr")
    if rpr_nodes:
        return rpr_nodes[0].toxml()
    return ""


def _collect_active_runs(paragraph_elem):
    runs = []
    full_text = ""

    for r_elem in paragraph_elem.getElementsByTagName("w:r"):
        parent = r_elem.parentNode
        inside_del = False
        while parent:
            if parent.nodeType == parent.ELEMENT_NODE and parent.tagName == "w:del":
                inside_del = True
                break
            parent = parent.parentNode

        if inside_del:
            continue

        if r_elem.getElementsByTagName("w:delText"):
            continue

        r_text = _get_run_text(r_elem)
        if not r_text:
            continue

        rpr = _get_run_rpr(r_elem)
        runs.append({
            'elem': r_elem,
            'text': r_text,
            'start': len(full_text),
            'rpr': rpr,
        })
        full_text += r_text

    return runs, full_text


def _normalize_whitespace(text):
    return re.sub(r'\s+', '', text)


def _find_text_in_full_text(full_text, target_text):
    idx = full_text.find(target_text)
    if idx != -1:
        return idx, target_text

    normalized_full = _normalize_whitespace(full_text)
    normalized_target = _normalize_whitespace(target_text)
    norm_idx = normalized_full.find(normalized_target)
    if norm_idx == -1:
        return -1, None

    char_count = 0
    orig_idx = 0
    for ci, ch in enumerate(full_text):
        if not ch.isspace():
            if char_count == norm_idx:
                orig_idx = ci
                break
            char_count += 1

    norm_target_len = len(normalized_target)
    end_orig_idx = orig_idx
    norm_chars_found = 0
    for ci in range(orig_idx, len(full_text)):
        if not full_text[ci].isspace():
            norm_chars_found += 1
            if norm_chars_found >= norm_target_len:
                end_orig_idx = ci + 1
                break

    actual_text = full_text[orig_idx:end_orig_idx]
    return orig_idx, actual_text


def _map_runs_for_range(runs, target_start, target_end):
    first_run_idx = None
    last_run_idx = None

    for i, run in enumerate(runs):
        run_start = run['start']
        run_end = run_start + len(run['text'])
        if run_start < target_end and run_end > target_start:
            if first_run_idx is None:
                first_run_idx = i
            last_run_idx = i

    return first_run_idx, last_run_idx


def _find_precise_in_paragraph(paragraph_elem, target_text, context=None, skip=0):
    runs, full_text = _collect_active_runs(paragraph_elem)

    if not full_text:
        return None

    remaining_skip = skip

    search_start = 0
    while True:
        idx, actual_text = _find_text_in_full_text(full_text[search_start:], target_text)
        if idx == -1:
            return None

        idx += search_start
        if actual_text is None:
            actual_text = target_text

        match_end = idx + len(actual_text)

        if context:
            if context not in full_text:
                search_start = match_end
                continue

        if remaining_skip > 0:
            remaining_skip -= 1
            search_start = match_end
            continue

        first_run_idx, last_run_idx = _map_runs_for_range(runs, idx, match_end)

        if first_run_idx is None or last_run_idx is None:
            return None

        return {
            'runs': runs,
            'first_run_idx': first_run_idx,
            'last_run_idx': last_run_idx,
            'target_start': idx,
            'target_end': match_end,
            'actual_text': actual_text,
            'paragraph_elem': paragraph_elem,
        }

    return None


def _detect_section(para_text, para_index, total_paragraphs):
    stripped = para_text.strip()

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


def _find_section_boundaries(paragraphs):
    section_starts = {}
    for i, para in enumerate(paragraphs):
        para_text = _get_para_text(para)
        section = _detect_section(para_text, i, len(paragraphs))
        if section and section not in section_starts:
            section_starts[section] = i

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

    return section_ranges


def _get_para_text(para_elem):
    texts = []
    for t_elem in para_elem.getElementsByTagName("w:t"):
        for child in t_elem.childNodes:
            if child.nodeType == child.TEXT_NODE and child.data:
                texts.append(child.data)
    return "".join(texts)


def _find_context_in_section(context, section_name, section_ranges, paragraphs, occurrence=None):
    if section_name in section_ranges:
        start_idx, end_idx = section_ranges[section_name]
        search_paragraphs = list(paragraphs[start_idx:end_idx])
    else:
        search_paragraphs = list(paragraphs)

    skip = (occurrence - 1) if occurrence and occurrence > 0 else 0

    for para in search_paragraphs:
        if _is_in_deletion(para):
            continue
        result = _find_precise_in_paragraph(para, context, skip=skip)
        if result is not None:
            return result
        if skip > 0:
            runs, full_text = _collect_active_runs(para)
            if context in full_text:
                skip -= 1

    return None


def _find_context_anywhere(context, paragraphs, occurrence=None):
    skip = (occurrence - 1) if occurrence and occurrence > 0 else 0

    for para in paragraphs:
        if _is_in_deletion(para):
            continue
        result = _find_precise_in_paragraph(para, context, skip=skip)
        if result is not None:
            return result
        if skip > 0:
            runs, full_text = _collect_active_runs(para)
            if context in full_text:
                skip -= 1

    return None


def _find_revision_range(nodes):
    first_rev = None
    last_rev = None
    for node in nodes:
        if node.nodeType == node.ELEMENT_NODE and node.tagName in ('w:del', 'w:ins'):
            if first_rev is None:
                first_rev = node
            last_rev = node
    return first_rev, last_rev


def _escape_xml(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _build_revision_parts(runs, first_run_idx, last_run_idx, target_start, target_end, insert_text=None):
    first_run = runs[first_run_idx]
    last_run = runs[last_run_idx]

    first_local_start = target_start - first_run['start']
    last_local_end = target_end - last_run['start']

    parts = []

    before_text = first_run['text'][:first_local_start]

    first_wrong_part = first_run['text'][first_local_start:] if first_run_idx != last_run_idx else first_run['text'][first_local_start:last_local_end]

    if before_text:
        parts.append(f'<w:r>{first_run["rpr"]}<w:t xml:space="preserve">{_escape_xml(before_text)}</w:t></w:r>')

    if first_run_idx == last_run_idx:
        wrong_part = first_run['text'][first_local_start:last_local_end]
        if wrong_part:
            parts.append(f'<w:del><w:r>{first_run["rpr"]}<w:delText>{_escape_xml(wrong_part)}</w:delText></w:r></w:del>')
    else:
        if first_wrong_part:
            parts.append(f'<w:del><w:r>{first_run["rpr"]}<w:delText>{_escape_xml(first_wrong_part)}</w:delText></w:r></w:del>')

        for run in runs[first_run_idx + 1:last_run_idx]:
            if run['text']:
                parts.append(f'<w:del><w:r>{run["rpr"]}<w:delText>{_escape_xml(run["text"])}</w:delText></w:r></w:del>')

        last_wrong_part = last_run['text'][:last_local_end]
        if last_wrong_part:
            parts.append(f'<w:del><w:r>{last_run["rpr"]}<w:delText>{_escape_xml(last_wrong_part)}</w:delText></w:r></w:del>')

    if insert_text is not None:
        parts.append(f'<w:ins><w:r>{first_run["rpr"]}<w:t>{_escape_xml(insert_text)}</w:t></w:r></w:ins>')

    after_text = last_run['text'][last_local_end:]
    if after_text:
        parts.append(f'<w:r>{last_run["rpr"]}<w:t xml:space="preserve">{_escape_xml(after_text)}</w:t></w:r>')

    return parts


def _apply_replace_in_paragraph(doc, para_info, new_text):
    runs = para_info['runs']
    first_run_idx = para_info['first_run_idx']
    last_run_idx = para_info['last_run_idx']
    target_start = para_info['target_start']
    target_end = para_info['target_end']

    first_run = runs[first_run_idx]
    last_run = runs[last_run_idx]

    common_parent = first_run['elem'].parentNode
    if not all(run['elem'].parentNode is common_parent for run in runs[first_run_idx:last_run_idx + 1]):
        return None

    parts = _build_revision_parts(runs, first_run_idx, last_run_idx, target_start, target_end, insert_text=new_text)
    replacement = "".join(parts)

    new_nodes = doc["word/document.xml"].replace_node(first_run['elem'], replacement)

    for run in runs[first_run_idx + 1:last_run_idx + 1]:
        run['elem'].parentNode.removeChild(run['elem'])

    return new_nodes


def _apply_delete_in_paragraph(doc, para_info):
    runs = para_info['runs']
    first_run_idx = para_info['first_run_idx']
    last_run_idx = para_info['last_run_idx']
    target_start = para_info['target_start']
    target_end = para_info['target_end']

    first_run = runs[first_run_idx]
    last_run = runs[last_run_idx]

    common_parent = first_run['elem'].parentNode
    if not all(run['elem'].parentNode is common_parent for run in runs[first_run_idx:last_run_idx + 1]):
        return None

    parts = _build_revision_parts(runs, first_run_idx, last_run_idx, target_start, target_end, insert_text=None)
    replacement = "".join(parts)

    new_nodes = doc["word/document.xml"].replace_node(first_run['elem'], replacement)

    for run in runs[first_run_idx + 1:last_run_idx + 1]:
        run['elem'].parentNode.removeChild(run['elem'])

    return new_nodes


def _apply_replace_in_revision_mode(doc, old_text, new_text, context=None, section=None, section_ranges=None, paragraphs=None, occurrence=None):
    dom = doc["word/document.xml"].dom
    all_paragraphs = list(dom.getElementsByTagName("w:p"))

    search_paragraphs = all_paragraphs
    if section and section_ranges and section in section_ranges:
        start_idx, end_idx = section_ranges[section]
        search_paragraphs = all_paragraphs[start_idx:end_idx]

    skip = (occurrence - 1) if occurrence and occurrence > 0 else 0

    for para in search_paragraphs:
        if _is_in_deletion(para):
            continue

        result = _find_precise_in_paragraph(para, old_text, context=context, skip=skip)
        if result is None:
            if skip > 0:
                runs, full_text = _collect_active_runs(para)
                _, actual = _find_text_in_full_text(full_text, old_text)
                if actual is not None:
                    skip -= 1
            continue

        return _apply_replace_in_paragraph(doc, result, new_text)

    return None


def _apply_delete_in_revision_mode(doc, old_text, context=None, section=None, section_ranges=None, paragraphs=None, occurrence=None):
    dom = doc["word/document.xml"].dom
    all_paragraphs = list(dom.getElementsByTagName("w:p"))

    search_paragraphs = all_paragraphs
    if section and section_ranges and section in section_ranges:
        start_idx, end_idx = section_ranges[section]
        search_paragraphs = all_paragraphs[start_idx:end_idx]

    skip = (occurrence - 1) if occurrence and occurrence > 0 else 0

    for para in search_paragraphs:
        if _is_in_deletion(para):
            continue

        result = _find_precise_in_paragraph(para, old_text, context=context, skip=skip)
        if result is None:
            if skip > 0:
                runs, full_text = _collect_active_runs(para)
                _, actual = _find_text_in_full_text(full_text, old_text)
                if actual is not None:
                    skip -= 1
            continue

        return _apply_delete_in_paragraph(doc, result)

    return None


def _add_comment_for_context(doc, context, section, section_ranges, paragraphs, comment_text, occurrence=None, highlight_text=None):
    para_info = _find_context_in_section(context, section, section_ranges, paragraphs, occurrence=occurrence)

    if para_info is None:
        para_info = _find_context_anywhere(context, paragraphs, occurrence=occurrence)

    if para_info is None:
        return False

    if highlight_text:
        paragraph_elem = para_info['paragraph_elem']
        highlight_info = _find_precise_in_paragraph(paragraph_elem, highlight_text)
        if highlight_info is not None:
            para_info = highlight_info

    runs = para_info['runs']
    first_run_idx = para_info['first_run_idx']
    last_run_idx = para_info['last_run_idx']
    target_start = para_info['target_start']
    target_end = para_info['target_end']

    first_run = runs[first_run_idx]
    last_run = runs[last_run_idx]

    first_local_start = target_start - first_run['start']
    last_local_end = target_end - last_run['start']

    if first_run_idx == last_run_idx and first_local_start == 0 and last_local_end == len(first_run['text']):
        doc.add_comment(start=first_run['elem'], end=first_run['elem'], text=comment_text)
        return True

    if first_run_idx == last_run_idx:
        before_text = first_run['text'][:first_local_start]
        target_part = first_run['text'][first_local_start:last_local_end]
        after_text = first_run['text'][last_local_end:]

        parts = []
        if before_text:
            parts.append(f'<w:r>{first_run["rpr"]}<w:t xml:space="preserve">{_escape_xml(before_text)}</w:t></w:r>')
        parts.append(f'<w:r>{first_run["rpr"]}<w:t xml:space="preserve">{_escape_xml(target_part)}</w:t></w:r>')
        if after_text:
            parts.append(f'<w:r>{first_run["rpr"]}<w:t xml:space="preserve">{_escape_xml(after_text)}</w:t></w:r>')

        replacement = "".join(parts)
        new_nodes = doc["word/document.xml"].replace_node(first_run['elem'], replacement)

        comment_node = new_nodes[1] if len(new_nodes) > 1 else new_nodes[0]
        doc.add_comment(start=new_nodes[0], end=new_nodes[-1], text=comment_text)
        return True

    first_parts = []
    before_text = first_run['text'][:first_local_start]
    first_target = first_run['text'][first_local_start:]
    if before_text:
        first_parts.append(f'<w:r>{first_run["rpr"]}<w:t xml:space="preserve">{_escape_xml(before_text)}</w:t></w:r>')
    first_parts.append(f'<w:r>{first_run["rpr"]}<w:t xml:space="preserve">{_escape_xml(first_target)}</w:t></w:r>')

    first_replacement = "".join(first_parts)
    first_new_nodes = doc["word/document.xml"].replace_node(first_run['elem'], first_replacement)

    last_parts = []
    last_target = last_run['text'][:last_local_end]
    after_text = last_run['text'][last_local_end:]
    last_parts.append(f'<w:r>{last_run["rpr"]}<w:t xml:space="preserve">{_escape_xml(last_target)}</w:t></w:r>')
    if after_text:
        last_parts.append(f'<w:r>{last_run["rpr"]}<w:t xml:space="preserve">{_escape_xml(after_text)}</w:t></w:r>')

    last_replacement = "".join(last_parts)
    last_new_nodes = doc["word/document.xml"].replace_node(last_run['elem'], last_replacement)

    doc.add_comment(start=first_new_nodes[-1], end=last_new_nodes[0], text=comment_text)
    return True


def add_reviews(input_path: str, output_path: str, reviews: list, author: str = "checking-patdocx-cn-single-agent"):
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(f"输入文件不存在: {input_path}")

    converted_docx = None
    actual_input = input_path

    if input_path.suffix.lower() == ".doc":
        print(f"检测到 .doc 格式文件，正在转换为 .docx ...")
        work_dir = output_path.parent
        try:
            docx_path, was_converted = ensure_docx(str(input_path), str(work_dir))
            if was_converted:
                converted_docx = docx_path
                actual_input = Path(docx_path)
                print(f"转换完成，使用临时文件: {actual_input.name}")
        except Exception as e:
            raise RuntimeError(f"无法转换 .doc 文件: {e}")
    elif input_path.suffix.lower() != ".docx":
        raise ValueError(f"不支持的文件格式: {input_path.suffix}，仅支持 .doc 和 .docx")

    try:
        with tempfile.TemporaryDirectory(prefix="review_add_") as temp_dir:
            unpacked_dir = Path(temp_dir) / "unpacked"

            print(f"正在解压 {actual_input.name} ...")
            unpack_document(str(actual_input), str(unpacked_dir))

            print(f"正在初始化文档编辑器 ...")
            doc = Document(
                str(unpacked_dir),
                track_revisions=True,
                author=author,
                initials="PC"
            )

            dom = doc["word/document.xml"].dom
            paragraphs = list(dom.getElementsByTagName("w:p"))
            section_ranges = _find_section_boundaries(paragraphs)
            print(f"已识别章节范围: {[(k, v) for k, v in section_ranges.items()]}")

            success_count = 0
            skip_count = 0

            for i, review in enumerate(reviews):
                section = review.get("section", "")
                claim_number = review.get("claim_number")
                issue = review.get("issue", "")
                context = review.get("context", "")
                suggestion = review.get("suggestion", "")
                action_type = review.get("action_type", "comment")
                old_text = review.get("old_text")
                new_text = review.get("new_text")
                occurrence = review.get("occurrence", None)
                highlight_text = review.get("highlight_text")

                if not context:
                    print(f"  跳过无效条目 #{i+1}: context 为空")
                    skip_count += 1
                    continue

                print(f'  处理 #{i+1}: [{section}] action_type={action_type} "{context}"', end="")
                if occurrence is not None:
                    print(f' occurrence={occurrence}', end="")
                if highlight_text:
                    print(f' highlight="{highlight_text}"', end="")
                print()

                comment_text = ""
                if section == "权利要求书" and claim_number is not None:
                    comment_text = f"权利要求{claim_number}: "
                comment_text += f"{issue}\n修改建议：{suggestion}"

                if action_type == "replace":
                    if not old_text or not new_text:
                        print(f"    ⚠ action_type=replace 但 old_text 或 new_text 为空，降级为仅添加批注")
                        if _add_comment_for_context(doc, context, section, section_ranges, paragraphs, comment_text, occurrence=occurrence, highlight_text=highlight_text):
                            success_count += 1
                            print(f"    ✓ 已添加批注（降级，精准定位）")
                        else:
                            print(f"    ⚠ 未找到文本: \"{context}\"")
                            skip_count += 1
                        continue

                    new_nodes = _apply_replace_in_revision_mode(
                        doc, old_text, new_text,
                        context=context, section=section,
                        section_ranges=section_ranges, paragraphs=paragraphs,
                        occurrence=occurrence
                    )
                    if new_nodes is None:
                        print(f"    ⚠ 未找到待替换文本: \"{old_text}\"，降级为仅添加批注")
                        if _add_comment_for_context(doc, context, section, section_ranges, paragraphs, comment_text, occurrence=occurrence, highlight_text=highlight_text):
                            success_count += 1
                            print(f"    ✓ 已添加批注（降级，精准定位）")
                        else:
                            print(f"    ⚠ 未找到上下文文本: \"{context}\"")
                            skip_count += 1
                        continue

                    first_rev, last_rev = _find_revision_range(new_nodes)
                    if first_rev is not None and last_rev is not None:
                        doc.add_comment(start=first_rev, end=last_rev, text=comment_text)
                    else:
                        doc.add_comment(start=new_nodes[0], end=new_nodes[-1], text=comment_text)
                    success_count += 1
                    print(f"    ✓ 已在修订模式下替换并添加批注（精准定位）")

                elif action_type == "delete":
                    if not old_text:
                        print(f"    ⚠ action_type=delete 但 old_text 为空，降级为仅添加批注")
                        if _add_comment_for_context(doc, context, section, section_ranges, paragraphs, comment_text, occurrence=occurrence, highlight_text=highlight_text):
                            success_count += 1
                            print(f"    ✓ 已添加批注（降级，精准定位）")
                        else:
                            print(f"    ⚠ 未找到文本: \"{context}\"")
                            skip_count += 1
                        continue

                    new_nodes = _apply_delete_in_revision_mode(
                        doc, old_text,
                        context=context, section=section,
                        section_ranges=section_ranges, paragraphs=paragraphs,
                        occurrence=occurrence
                    )
                    if new_nodes is None:
                        print(f"    ⚠ 未找到待删除文本: \"{old_text}\"，降级为仅添加批注")
                        if _add_comment_for_context(doc, context, section, section_ranges, paragraphs, comment_text, occurrence=occurrence, highlight_text=highlight_text):
                            success_count += 1
                            print(f"    ✓ 已添加批注（降级，精准定位）")
                        else:
                            print(f"    ⚠ 未找到上下文文本: \"{context}\"")
                            skip_count += 1
                        continue

                    first_rev, last_rev = _find_revision_range(new_nodes)
                    if first_rev is not None and last_rev is not None:
                        doc.add_comment(start=first_rev, end=last_rev, text=comment_text)
                    else:
                        doc.add_comment(start=new_nodes[0], end=new_nodes[-1], text=comment_text)
                    success_count += 1
                    print(f"    ✓ 已在修订模式下删除并添加批注（精准定位）")

                else:
                    if _add_comment_for_context(doc, context, section, section_ranges, paragraphs, comment_text, occurrence=occurrence, highlight_text=highlight_text):
                        success_count += 1
                        print(f"    ✓ 已添加批注（精准定位）")
                    else:
                        print(f"    ⚠ 未找到文本: \"{context}\"")
                        skip_count += 1

            print(f"正在保存修改 ...")
            doc.save()

            print(f"正在打包为 {output_path.name} ...")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            pack_document(str(unpacked_dir), str(output_path), validate=False)

        print(f"\n处理完成：共 {len(reviews)} 处，成功 {success_count} 处，跳过 {skip_count} 处")
        return {"total": len(reviews), "success": success_count, "skip": skip_count}
    finally:
        if converted_docx:
            try:
                Path(converted_docx).unlink()
                print(f"已清理临时转换文件: {Path(converted_docx).name}")
            except OSError:
                pass


def main():
    parser = argparse.ArgumentParser(description="审查意见批注添加工具")
    parser.add_argument("input", help="输入 docx 文件路径")
    parser.add_argument("output", help="输出 docx 文件路径")
    parser.add_argument("--reviews-file", required=True, help="审查意见 JSON 文件路径")
    parser.add_argument("--author", default="checking-patdocx-cn-single-agent", help="批注作者名称")

    args = parser.parse_args()

    reviews_path = Path(args.reviews_file)
    if not reviews_path.exists():
        print(f"错误：审查意见文件不存在: {reviews_path}")
        sys.exit(1)

    with open(reviews_path, "r", encoding="utf-8") as f:
        reviews = json.load(f)

    add_reviews(args.input, args.output, reviews, args.author)


if __name__ == "__main__":
    main()

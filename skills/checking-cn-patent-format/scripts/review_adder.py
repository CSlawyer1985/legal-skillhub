#!/usr/bin/env python3
"""
审查意见批注添加工具

功能：
1. 读取审查意见 JSON 文件
2. 在 Word 文档中定位对应文本位置
3. 根据 action_type 执行不同操作：
   - replace: 在修订模式下替换文本
   - delete: 在修订模式下删除文本
   - comment: 添加批注
4. 输出带有修订和批注的 docx 文件

用法：
    python review_adder.py input.docx output.docx --reviews-file reviews.json
"""

# argparse 用于解析命令行参数
import argparse
# io 提供流处理功能，这里用于设置 UTF-8 输出
import io
# json 用于读写 JSON 格式文件
import json
# re 提供正则表达式支持
import re
# sys 提供系统相关功能
import sys
# tempfile 用于创建临时目录
import tempfile
# Path 用于面向对象的文件路径处理
from pathlib import Path

# 设置标准输出为 UTF-8 编码，确保中文正常显示
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
except (AttributeError, io.UnsupportedOperation):
    pass

# 将父目录添加到 Python 路径，以便导入其他模块
SKILL_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_ROOT))

# 导入解压和打包文档的函数
from ooxml.scripts.unpack import unpack_document
from ooxml.scripts.pack import pack_document

# 导入 Document 类，用于操作 Word 文档的批注和修订
from scripts.document import Document

# 导入 doc_converter 模块中的 ensure_docx 函数，用于 .doc 转 .docx
from scripts.doc_converter import ensure_docx
from scripts.patent_analyzer import PatentAnalyzer
from scripts.error_handling import AnnotationBatchLogger

ABSTRACT_FIG_ANCHOR_TEXT = "摘要附图批注"

REVIEWER_BY_SEVERITY = {
    "格式": {"author": "格式问题", "initials": "GS"},
    "实质": {"author": "实质问题", "initials": "SZ"},
    "严重": {"author": "严重问题", "initials": "YZ"},
    "default": {"author": "checking-cn-patent-format", "initials": "MA"},
}


def _clean_control_chars(text: str) -> str:
    """
    清理文本中的XML非法控制字符（解决BUG #1：XML解析崩溃）。

    XML 1.0规范仅允许以下控制字符：
    - 0x09 (Tab)
    - 0x0A (Line Feed)
    - 0x0D (Carriage Return)

    其他控制字符（0x00-0x08, 0x0B, 0x0C, 0x0E-0x1F）均会导致XML解析失败。
    Agent输出的emoji标记（如🔴对应的\\u0019）属于此类非法字符。

    Args:
        text: 待清理的文本字符串

    Returns:
        清理后的安全文本字符串
    """
    if not text or not isinstance(text, str):
        return text

    # 定义XML允许的控制字符
    allowed_controls = {0x09, 0x0A, 0x0D}  # Tab, LF, CR

    # 过滤掉所有不允许的控制字符（0x00-0x1F范围，除允许的3个外）
    cleaned_chars = []
    for char in text:
        code = ord(char)
        if code < 0x20 and code not in allowed_controls:
            # 跳过非法控制字符，不添加到结果中
            continue
        cleaned_chars.append(char)

    return ''.join(cleaned_chars)


def _sanitize_review(review: dict) -> dict:
    """
    清理单条审查意见中所有文本字段的控制字符。

    对issue、suggestion、context、highlight_text、old_text、new_text等
    所有文本字段执行控制字符清理，防止XML解析失败。

    Args:
        review: 单条审查意见字典

    Returns:
        清理后的审查意见字典（原地修改）
    """
    text_fields = ['issue', 'suggestion', 'context', 'highlight_text',
                   'old_text', 'new_text']

    for field in text_fields:
        if field in review and review[field] is not None:
            original = review[field]
            cleaned = _clean_control_chars(original)
            if cleaned != original:
                print(f"    [清理] 字段 '{field}' 已移除 {len(original) - len(cleaned)} 个非法控制字符")
                review[field] = cleaned

    return review


def _is_in_deletion(elem):
    """
    检查元素是否在删除标记（w:del）内部。
    用于跳过已被标记为删除的文本。
    """
    parent = elem.parentNode
    visited = set()
    max_depth = 100
    depth = 0
    while parent is not None:
        if depth >= max_depth:
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


def _get_run_text(r_elem):
    """
    从文本运行（w:r）元素中提取所有文本内容。
    遍历所有 w:t 子元素，拼接其文本节点内容。
    """
    text = ""
    for t_node in r_elem.getElementsByTagName("w:t"):
        for child in t_node.childNodes:
            if child.nodeType == child.TEXT_NODE:
                text += child.data
    return text


def _get_run_rpr(r_elem):
    """
    获取文本运行的格式属性（w:rPr）XML 字符串。
    用于在替换文本时保持原有格式。
    """
    rpr_nodes = r_elem.getElementsByTagName("w:rPr")
    if rpr_nodes:
        return rpr_nodes[0].toxml()
    return ""


def _collect_active_runs(paragraph_elem):
    """
    收集段落中所有"有效"的文本运行。

    有效指的是：
    - 不在删除标记内部
    - 不包含删除文本（w:delText）
    - 包含非空文本

    返回：
        runs: 包含每个文本运行的详细信息的列表
        full_text: 拼接后的完整文本
    """
    runs = []
    full_text = ""

    for r_elem in paragraph_elem.getElementsByTagName("w:r"):
        # 检查是否在删除标记内部
        parent = r_elem.parentNode
        inside_del = False
        while parent:
            if parent.nodeType == parent.ELEMENT_NODE and parent.tagName == "w:del":
                inside_del = True
                break
            parent = parent.parentNode

        if inside_del:
            continue

        # 跳过包含删除文本的运行
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
    """去除文本中的所有空白字符，用于模糊匹配。"""
    return re.sub(r'\s+', '', text)


def _edit_distance(s1, s2):
    """
    计算两个字符串之间的Levenshtein编辑距离。

    用于模糊匹配降级：当精确匹配和空白忽略匹配都失败时，
    通过编辑距离判断context是否因Unicode编码差异或异体字
    而无法精确匹配。

    Args:
        s1: 第一个字符串
        s2: 第二个字符串

    Returns:
        编辑距离（整数）
    """
    if len(s1) < len(s2):
        return _edit_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    prev_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row

    return prev_row[-1]


def _fuzzy_match_context(full_text, target_text, threshold=0.85):
    """
    基于编辑距离的模糊匹配，作为精确匹配失败时的降级方案。

    当Agent输出的context因Unicode编码差异（如\\uXXXX转义、
    异体字差异）导致精确匹配失败时，通过编辑距离相似度
    判断是否为同一文本。

    Args:
        full_text: 文档中的完整文本
        target_text: 待查找的目标文本
        threshold: 相似度阈值（0-1），低于此值不视为匹配

    Returns:
        (start_index, actual_text) 如果找到匹配
        (-1, None) 如果未找到匹配
    """
    if not target_text or not full_text:
        return -1, None

    target_len = len(target_text)
    best_ratio = 0.0
    best_start = -1
    best_actual = None

    step = max(1, target_len // 10)

    for start in range(0, len(full_text) - target_len + 1, step):
        end = min(start + target_len + max(10, target_len // 5), len(full_text))
        candidate = full_text[start:end]

        dist = _edit_distance(target_text, candidate)
        max_len = max(len(target_text), len(candidate))
        ratio = 1.0 - dist / max_len if max_len > 0 else 0.0

        if ratio > best_ratio:
            best_ratio = ratio
            best_start = start
            best_actual = candidate

    if best_ratio >= threshold:
        refined_start = max(0, best_start - 5)
        refined_end = min(len(full_text), best_start + target_len + 10)

        for s in range(refined_start, min(refined_end, len(full_text) - target_len + 1)):
            e = min(s + target_len + max(5, target_len // 10), len(full_text))
            cand = full_text[s:e]
            dist = _edit_distance(target_text, cand)
            max_len = max(len(target_text), len(cand))
            ratio = 1.0 - dist / max_len if max_len > 0 else 0.0

            if ratio > best_ratio:
                best_ratio = ratio
                best_start = s
                best_actual = cand

        return best_start, best_actual

    return -1, None


def _find_text_in_full_text(full_text, target_text):
    """
    在完整文本中查找目标文本。

    先尝试精确匹配，如果失败则尝试忽略空白字符的匹配，
    最后尝试基于编辑距离的模糊匹配（降级方案）。
    返回匹配的起始位置和实际匹配的文本。
    """
    idx = full_text.find(target_text)
    if idx != -1:
        return idx, target_text

    # 精确匹配失败，尝试忽略空白字符的匹配
    normalized_full = _normalize_whitespace(full_text)
    normalized_target = _normalize_whitespace(target_text)
    norm_idx = normalized_full.find(normalized_target)
    if norm_idx == -1:
        # 空白忽略匹配也失败，尝试模糊匹配（降级方案）
        # 仅对较短文本启用模糊匹配（避免性能问题）
        if len(target_text) <= 300:
            fuzzy_idx, fuzzy_actual = _fuzzy_match_context(full_text, target_text, threshold=0.85)
            if fuzzy_idx != -1:
                print(f"    [模糊匹配] 精确匹配失败，通过编辑距离模糊匹配定位（相似度>=85%）")
                return fuzzy_idx, fuzzy_actual
        return -1, None

    # 将规范化后的索引映射回原始文本的索引
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
    """
    根据目标文本范围，确定涉及哪些文本运行。

    返回第一个和最后一个涉及的运行索引。
    """
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
    """
    在段落中精确定位目标文本。

    Args:
        paragraph_elem: 段落 XML 元素
        target_text: 要查找的目标文本
        context: 上下文文本（用于验证）
        skip: 跳过前几次匹配（用于处理重复文本）

    Returns:
        包含定位信息的字典，如果未找到则返回 None
    """
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

        # 如果指定了上下文，检查上下文是否存在于段落中
        if context:
            if context not in full_text:
                search_start = match_end
                continue

        # 处理 skip 逻辑
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
    """
    根据段落文本内容检测所属章节。

    使用正则表达式匹配章节标题特征。
    """
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

    # 权利要求通常以数字编号开头
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
                       用于检测零段落章节（如摘要附图），解决纯文本扫描无法发现
                       无文字内容章节的问题。(BUG-006修复)

    【代码同步】此函数与 skip_relocator.py 中的同名函数保持逻辑一致。
                 同步版本: v2.1-BUG006-fix
                 修改任一文件时请同步更新另一文件。
    """
    section_starts = {}
    for i, para in enumerate(paragraphs):
        para_text = _get_para_text(para)
        section = _detect_section(para_text, i, len(paragraphs))
        if section and section not in section_starts:
            section_starts[section] = i

    # 【BUG-006修复】基于已知章节元数据补充零段落章节
    if known_sections and isinstance(known_sections, list):
        known_names = set()
        for sec in known_sections:
            sec_name = sec.get('section_name', '')
            para_count = sec.get('paragraph_count', 0)
            known_names.add(sec_name)
            if para_count == 0 and sec_name and sec_name not in section_starts:
                pass  # 零段落章节稍后统一处理

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
                    if zsec_idx < known_sections.index(
                        next((s for s in known_sections if s.get('section_name') == detected_name), None)
                        if any(s.get('section_name') == detected_name for s in known_sections)
                        else len(known_sections)
                    ):
                        insert_pos = detected_pos
                        if i > 0:
                            prev_end = ordered_detected[i - 1][1]
                        else:
                            prev_end = 0
                        if zsec_name not in section_starts:
                            section_ranges_temp = dict(sorted(section_starts.items(), key=lambda x: x[1]))
                            for sn, (ss, se) in section_ranges_temp.items():
                                if ss >= insert_pos:
                                    continue
                                if ss <= insert_pos <= se or (se > insert_pos and i == 0):
                                    section_starts[zsec_name] = se
                                    inserted = True
                                    break
                        break
                if not inserted and zsec_name not in section_starts:
                    if ordered_detected:
                        last_pos = ordered_detected[-1][1]
                        section_starts[zsec_name] = last_pos
                    else:
                        section_starts[zsec_name] = 0

    # 按起始位置排序
    ordered = sorted(section_starts.items(), key=lambda x: x[1])

    section_ranges = {}
    for idx, (name, start) in enumerate(ordered):
        if idx + 1 < len(ordered):
            end = ordered[idx + 1][1]
        else:
            end = len(paragraphs)
        section_ranges[name] = (start, end)

    # 如果没有检测到任何章节，将整个文档作为一个章节
    if not section_ranges:
        section_ranges["全文"] = (0, len(paragraphs))
        return section_ranges

    # 处理文档开头到第一个章节之间的内容
    first_section_start = ordered[0][1]
    if first_section_start > 0:
        if "摘要" not in section_ranges:
            section_ranges["摘要"] = (0, first_section_start)

    # 如果未检测到权利要求书，尝试通过编号特征推断
    if "权利要求书" not in section_ranges and "摘要" in section_ranges:
        abstract_end = section_ranges["摘要"][1]
        for i in range(abstract_end, len(paragraphs)):
            para_text = _get_para_text(paragraphs[i]).strip()
            if re.match(r'^\d+\s*[.、]\s*', para_text):
                section_ranges["权利要求书"] = (i, section_ranges.get("说明书", (len(paragraphs),))[0])
                break

    # 如果未检测到摘要附图，尝试推断
    if "摘要附图" not in section_ranges and "摘要" in section_ranges and "权利要求书" in section_ranges:
        abstract_end = section_ranges["摘要"][1]
        claims_start = section_ranges["权利要求书"][0]
        for i in range(abstract_end, claims_start):
            para_text = _get_para_text(paragraphs[i]).strip()
            if re.match(r'^图\s*\d', para_text) or re.search(r'摘\s*要\s*附\s*图', para_text):
                section_ranges["摘要附图"] = (i, claims_start)
                break

    # 如果未检测到说明书附图，尝试推断
    if "说明书附图" not in section_ranges and "说明书" in section_ranges:
        description_end = section_ranges["说明书"][1]
        # 说明书附图通常在说明书之后，查找连续的图号段落
        for i in range(description_end, len(paragraphs)):
            para_text = _get_para_text(paragraphs[i]).strip()
            # 匹配"图N"格式或包含"说明书附图"关键词
            if re.match(r'^图\s*\d', para_text) or re.search(r'说\s*明\s*书\s*附\s*图', para_text):
                # 找到说明书附图的起始位置
                section_ranges["说明书附图"] = (i, len(paragraphs))
                break

    return section_ranges


def _get_para_text(para_elem):
    """从段落元素中提取所有文本内容。"""
    texts = []
    for t_elem in para_elem.getElementsByTagName("w:t"):
        for child in t_elem.childNodes:
            if child.nodeType == child.TEXT_NODE and child.data:
                texts.append(child.data)
    return "".join(texts)


def _find_context_in_section(context, section_name, section_ranges, paragraphs, occurrence=None):
    """
    在指定章节中查找上下文文本。

    Args:
        context: 要查找的上下文文本
        section_name: 章节名称
        section_ranges: 章节范围映射
        paragraphs: 所有段落元素列表
        occurrence: 指定第几次出现（从1开始）

    Returns:
        定位信息字典，未找到则返回 None
    """
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


def _find_context_by_paragraph_index(context, section_name, section_ranges, paragraphs, paragraph_index, highlight_text=None):
    """
    使用 paragraph_index 在指定章节的特定段落中查找文本。

    Args:
        context: 要查找的上下文文本
        section_name: 章节名称
        section_ranges: 章节范围映射
        paragraphs: 所有段落元素列表
        paragraph_index: 目标段落在章节内的索引（从0开始）
        highlight_text: 精准定位文本

    Returns:
        定位信息字典，未找到则返回 None
    """
    if section_name not in section_ranges:
        return None

    start_idx, end_idx = section_ranges[section_name]
    abs_para_idx = start_idx + paragraph_index

    if abs_para_idx < 0 or abs_para_idx >= len(paragraphs):
        return None

    para = paragraphs[abs_para_idx]
    if _is_in_deletion(para):
        return None

    search_text = highlight_text if highlight_text else context
    result = _find_precise_in_paragraph(para, search_text)
    if result is not None:
        return result

    return None


def _find_context_anywhere(context, paragraphs, occurrence=None):
    """
    在整个文档中查找上下文文本。

    与 _find_context_in_section 类似，但不限制章节范围。
    """
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
    """
    在节点列表中查找第一个和最后一个修订标记（w:del 或 w:ins）。

    用于确定批注应该附加在哪个范围上。
    """
    first_rev = None
    last_rev = None
    for node in nodes:
        if node.nodeType == node.ELEMENT_NODE and node.tagName in ('w:del', 'w:ins'):
            if first_rev is None:
                first_rev = node
            last_rev = node
    return first_rev, last_rev


def _escape_xml(s):
    """转义 XML 特殊字符，防止注入攻击。"""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _build_revision_parts(runs, first_run_idx, last_run_idx, target_start, target_end, insert_text=None):
    """
    构建修订追踪所需的 XML 片段。

    将目标文本范围内的内容标记为删除（w:del），
    并在其后插入新文本（w:ins，如果提供了 insert_text）。

    Args:
        runs: 文本运行列表
        first_run_idx: 第一个涉及的运行索引
        last_run_idx: 最后一个涉及的运行索引
        target_start: 目标文本起始位置
        target_end: 目标文本结束位置
        insert_text: 要插入的新文本（None 表示仅删除）

    Returns:
        XML 片段列表
    """
    first_run = runs[first_run_idx]
    last_run = runs[last_run_idx]

    first_local_start = target_start - first_run['start']
    last_local_end = target_end - last_run['start']

    parts = []

    before_text = first_run['text'][:first_local_start]

    if len(runs) - 1 == first_run_idx - first_run_idx + (last_run_idx - first_run_idx):
        pass

    first_wrong_part = first_run['text'][first_local_start:] if first_run_idx != last_run_idx else first_run['text'][first_local_start:last_local_end]

    # 添加目标文本之前的保留文本
    if before_text:
        parts.append(f'<w:r>{first_run["rpr"]}<w:t xml:space="preserve">{_escape_xml(before_text)}</w:t></w:r>')

    # 处理目标文本的删除标记
    if first_run_idx == last_run_idx:
        wrong_part = first_run['text'][first_local_start:last_local_end]
        if wrong_part:
            parts.append(f'<w:del><w:r>{first_run["rpr"]}<w:delText>{_escape_xml(wrong_part)}</w:delText></w:r></w:del>')
    else:
        if first_wrong_part:
            parts.append(f'<w:del><w:r>{first_run["rpr"]}<w:delText>{_escape_xml(first_wrong_part)}</w:delText></w:r></w:del>')

        # 处理中间完全包含的运行
        for run in runs[first_run_idx + 1:last_run_idx]:
            if run['text']:
                parts.append(f'<w:del><w:r>{run["rpr"]}<w:delText>{_escape_xml(run["text"])}</w:delText></w:r></w:del>')

        last_wrong_part = last_run['text'][:last_local_end]
        if last_wrong_part:
            parts.append(f'<w:del><w:r>{last_run["rpr"]}<w:delText>{_escape_xml(last_wrong_part)}</w:delText></w:r></w:del>')

    # 添加插入的新文本
    if insert_text is not None:
        parts.append(f'<w:ins><w:r>{first_run["rpr"]}<w:t>{_escape_xml(insert_text)}</w:t></w:r></w:ins>')

    # 添加目标文本之后的保留文本
    after_text = last_run['text'][last_local_end:]
    if after_text:
        parts.append(f'<w:r>{last_run["rpr"]}<w:t xml:space="preserve">{_escape_xml(after_text)}</w:t></w:r>')

    return parts


def _apply_replace_in_paragraph(doc, para_info, new_text):
    """
    在段落中应用替换操作。

    将目标文本标记为删除，并插入新文本。
    """
    runs = para_info['runs']
    first_run_idx = para_info['first_run_idx']
    last_run_idx = para_info['last_run_idx']
    target_start = para_info['target_start']
    target_end = para_info['target_end']

    first_run = runs[first_run_idx]
    last_run = runs[last_run_idx]

    # 检查所有涉及的运行是否有相同的父元素
    common_parent = first_run['elem'].parentNode
    if not all(run['elem'].parentNode is common_parent for run in runs[first_run_idx:last_run_idx + 1]):
        return None

    parts = _build_revision_parts(runs, first_run_idx, last_run_idx, target_start, target_end, insert_text=new_text)
    replacement = "".join(parts)

    # 替换第一个运行元素
    new_nodes = doc["word/document.xml"].replace_node(first_run['elem'], replacement)

    # 移除其他涉及的运行元素
    for run in runs[first_run_idx + 1:last_run_idx + 1]:
        run['elem'].parentNode.removeChild(run['elem'])

    return new_nodes


def _apply_delete_in_paragraph(doc, para_info):
    """
    在段落中应用删除操作。

    将目标文本标记为删除，不插入新文本。
    """
    runs = para_info['runs']
    first_run_idx = para_info['first_run_idx']
    last_run_idx = para_info['last_run_idx']
    target_start = para_info['target_start']
    target_end = para_info['target_end']

    first_run = runs[first_run_idx]
    last_run = runs[last_run_idx]

    # 检查所有涉及的运行是否有相同的父元素
    common_parent = first_run['elem'].parentNode
    if not all(run['elem'].parentNode is common_parent for run in runs[first_run_idx:last_run_idx + 1]):
        return None

    parts = _build_revision_parts(runs, first_run_idx, last_run_idx, target_start, target_end, insert_text=None)
    replacement = "".join(parts)

    # 替换第一个运行元素
    new_nodes = doc["word/document.xml"].replace_node(first_run['elem'], replacement)

    # 移除其他涉及的运行元素
    for run in runs[first_run_idx + 1:last_run_idx + 1]:
        run['elem'].parentNode.removeChild(run['elem'])

    return new_nodes


def _apply_replace_in_revision_mode(doc, old_text, new_text, context=None, section=None, section_ranges=None, paragraphs=None, occurrence=None):
    """
    在修订模式下应用替换操作。

    在指定章节或整个文档中查找 old_text，并将其替换为 new_text。
    """
    dom = doc["word/document.xml"].dom
    all_paragraphs = list(dom.getElementsByTagName("w:p"))

    # 如果指定了章节，限制搜索范围
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
    """
    在修订模式下应用删除操作。

    在指定章节或整个文档中查找 old_text，并将其标记为删除。
    """
    dom = doc["word/document.xml"].dom
    all_paragraphs = list(dom.getElementsByTagName("w:p"))

    # 如果指定了章节，限制搜索范围
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


def _add_comment_for_context(doc, context, section, section_ranges, paragraphs, comment_text, occurrence=None, highlight_text=None, paragraph_index=None):
    """
    为指定上下文添加批注。

    先尝试使用 paragraph_index 精确定位，再在指定章节中查找，如果失败则在全文档中查找。
    可以指定 highlight_text 来精确定位批注范围。
    """
    para_info = None

    if paragraph_index is not None and section and section_ranges:
        para_info = _find_context_by_paragraph_index(context, section, section_ranges, paragraphs, paragraph_index, highlight_text=highlight_text)

    if para_info is None:
        para_info = _find_context_in_section(context, section, section_ranges, paragraphs, occurrence=occurrence)
    if para_info is None:
        para_info = _find_context_anywhere(context, paragraphs, occurrence=occurrence)

    if para_info is None:
        return False

    # 如果指定了高亮文本，尝试更精确地定位
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

    # 如果整个运行就是要批注的范围，直接添加批注
    if first_run_idx == last_run_idx and first_local_start == 0 and last_local_end == len(first_run['text']):
        doc.add_comment(start=first_run['elem'], end=first_run['elem'], text=comment_text)
        return True

    # 如果目标文本在同一个运行内，需要拆分运行
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

    # 目标文本跨多个运行，需要分别处理首尾运行
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


def _find_text_in_headers(doc, target_text, highlight_text=None, occurrence=None):
    """
    在页眉XML文件中搜索目标文本。

    当正文搜索失败时，尝试在页眉文件中查找文本。

    适用于"说明书附图"等位于页眉中的章节标题文本。

    Args:
        doc: Document对象
        target_text: 要查找的目标文本
        highlight_text: 精准定位文本
        occurrence: 第几次出现（从1开始）

    Returns:
        包含header_path和定位信息的字典，未找到则返回None
    """
    unpacked_dir = doc.unpacked_path
    word_dir = unpacked_dir / "word"

    if not word_dir.exists():
        return None

    skip = (occurrence - 1) if occurrence and occurrence > 0 else 0
    search_text = highlight_text if highlight_text else target_text

    for header_file in sorted(word_dir.glob("header*.xml")):
        header_path = f"word/{header_file.name}"

        try:
            editor = doc[header_path]
        except ValueError:
            continue

        dom = editor.dom
        paragraphs = list(dom.getElementsByTagName("w:p"))

        for para in paragraphs:
            if _is_in_deletion(para):
                continue

            result = _find_precise_in_paragraph(para, search_text, skip=skip)
            if result is not None:
                result['header_path'] = header_path
                return result

            if skip > 0:
                runs, full_text = _collect_active_runs(para)
                if search_text in full_text:
                    skip -= 1

    return None


def _add_comment_for_header(doc, header_path, para_info, comment_text):
    """
    在页眉XML文件中为指定文本添加批注。

    与_add_comment_for_context类似，但批注添加到页眉文件中，
    使用add_comment_in_file方法确保批注范围标记插入到页眉XML中。

    Args:
        doc: Document对象
        header_path: 页眉XML文件路径（如"word/header1.xml"）
        para_info: 定位信息字典（来自_find_precise_in_paragraph）
        comment_text: 批注文本

    Returns:
        True表示成功，False表示失败
    """
    runs = para_info['runs']
    first_run_idx = para_info['first_run_idx']
    last_run_idx = para_info['last_run_idx']
    target_start = para_info['target_start']
    target_end = para_info['target_end']

    first_run = runs[first_run_idx]
    last_run = runs[last_run_idx]

    first_local_start = target_start - first_run['start']
    last_local_end = target_end - last_run['start']

    editor = doc[header_path]

    # 如果整个运行就是要批注的范围，直接添加批注
    if first_run_idx == last_run_idx and first_local_start == 0 and last_local_end == len(first_run['text']):
        doc.add_comment_in_file(header_path, start=first_run['elem'], end=first_run['elem'], text=comment_text)
        return True

    # 如果目标文本在同一个运行内，需要拆分运行
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
        new_nodes = editor.replace_node(first_run['elem'], replacement)

        doc.add_comment_in_file(header_path, start=new_nodes[0], end=new_nodes[-1], text=comment_text)
        return True

    # 目标文本跨多个运行，需要分别处理首尾运行
    first_parts = []
    before_text = first_run['text'][:first_local_start]
    first_target = first_run['text'][first_local_start:]
    if before_text:
        first_parts.append(f'<w:r>{first_run["rpr"]}<w:t xml:space="preserve">{_escape_xml(before_text)}</w:t></w:r>')
    first_parts.append(f'<w:r>{first_run["rpr"]}<w:t xml:space="preserve">{_escape_xml(first_target)}</w:t></w:r>')

    first_replacement = "".join(first_parts)
    first_new_nodes = editor.replace_node(first_run['elem'], first_replacement)

    last_parts = []
    last_target = last_run['text'][:last_local_end]
    after_text = last_run['text'][last_local_end:]
    last_parts.append(f'<w:r>{last_run["rpr"]}<w:t xml:space="preserve">{_escape_xml(last_target)}</w:t></w:r>')
    if after_text:
        last_parts.append(f'<w:r>{last_run["rpr"]}<w:t xml:space="preserve">{_escape_xml(after_text)}</w:t></w:r>')

    last_replacement = "".join(last_parts)
    last_new_nodes = editor.replace_node(last_run['elem'], last_replacement)

    doc.add_comment_in_file(header_path, start=first_new_nodes[-1], end=last_new_nodes[0], text=comment_text)
    return True


def _try_add_comment_with_header_fallback(doc, context, section, section_ranges, paragraphs, comment_text, occurrence=None, highlight_text=None, paragraph_index=None):
    """
    尝试在正文中添加批注，失败则在页眉中尝试。

    先调用_add_comment_for_context在正文(document.xml)中搜索并添加批注，
    如果正文搜索失败，则调用_find_text_in_headers在页眉XML文件中搜索，
    找到后使用_add_comment_for_header在页眉中添加批注。

    Args:
        doc: Document对象
        context: 上下文文本
        section: 章节名称
        section_ranges: 章节范围映射
        paragraphs: 所有段落元素列表
        comment_text: 批注文本
        occurrence: 第几次出现
        highlight_text: 精准定位文本
        paragraph_index: 段落索引

    Returns:
        "body" - 正文批注成功
        "header:<path>" - 页眉批注成功
        None - 均失败
    """
    if _add_comment_for_context(doc, context, section, section_ranges, paragraphs, comment_text, occurrence=occurrence, highlight_text=highlight_text, paragraph_index=paragraph_index):
        return "body"

    header_result = _find_text_in_headers(doc, context, highlight_text=highlight_text, occurrence=occurrence)
    if header_result is not None:
        header_path = header_result.pop('header_path')
        if _add_comment_for_header(doc, header_path, header_result, comment_text):
            return f"header:{header_path}"

    return None


def _insert_abstract_fig_anchor(doc, section_ranges, paragraphs):
    """
    在摘要附图章节结尾插入锚定文本段落。

    对于摘要附图section的批注，不再寻找锚定文字，
    而是新增"摘要附图批注"文字作为批注的锚定文字。

    Args:
        doc: Document对象
        section_ranges: 章节范围映射
        paragraphs: 所有段落元素列表

    Returns:
        锚定段落元素，如果插入失败则返回None
    """
    if "摘要附图" not in section_ranges:
        return None

    start_idx, end_idx = section_ranges["摘要附图"]

    last_para = None
    for i in range(end_idx - 1, start_idx - 1, -1):
        if i < len(paragraphs) and not _is_in_deletion(paragraphs[i]):
            last_para = paragraphs[i]
            break

    if last_para is None:
        return None

    anchor_para_xml = f'''<w:p>
  <w:r>
    <w:t xml:space="preserve">{_escape_xml(ABSTRACT_FIG_ANCHOR_TEXT)}</w:t>
  </w:r>
</w:p>'''

    editor = doc["word/document.xml"]
    new_nodes = editor.insert_after(last_para, anchor_para_xml)

    anchor_para = None
    for node in new_nodes:
        if node.nodeType == node.ELEMENT_NODE and node.tagName == "w:p":
            anchor_para = node
            break

    return anchor_para


def _add_comment_to_abstract_fig_anchor(doc, anchor_para, comment_text):
    """
    在摘要附图锚定段落上添加批注。

    Args:
        doc: Document对象
        anchor_para: 锚定段落元素
        comment_text: 批注文本

    Returns:
        True表示成功，False表示失败
    """
    runs = anchor_para.getElementsByTagName("w:r")
    if not runs:
        return False

    doc.add_comment(start=runs[0], end=runs[-1], text=comment_text)
    return True


def _strip_comment_labels(text, labels=None):
    """
    剥离文本中已有的批注结构化标签（如"【问题描述】"、"【修改建议】"）。

    防止 review_adder.py 在构建批注文本时重复添加标签，
    导致最终批注中出现"【问题描述】【问题描述】"的重复字词。

    Args:
        text: 待处理的文本字符串
        labels: 需要剥离的标签列表，默认为常见标签

    Returns:
        剥离标签后的文本字符串
    """
    if not text or not isinstance(text, str):
        return text
    if labels is None:
        labels = ['【问题描述】', '【修改建议】', '【问题】', '【建议】']
    for label in labels:
        text = text.replace(label, '')
    return text.strip()


def _classify_severity(review: dict) -> str:
    issue = (review.get('issue') or '').lower()
    action_type = review.get('action_type', 'comment')

    severe_keywords = ['公开不充分', '单一性', '保护范围', '缺少必要', '无法实现']
    substantive_keywords = ['所述', '引用', '主题', '不一致', '缺少', '错误', '重复', '用语']
    format_keywords = ['格式', '标点', '错别字', '编号', '字体', '空格', '缩进']

    for kw in severe_keywords:
        if kw in issue:
            return "严重"

    if action_type in ('replace', 'delete'):
        for kw in substantive_keywords:
            if kw in issue:
                return "实质"
        return "实质"

    for kw in format_keywords:
        if kw in issue:
            return "格式"

    for kw in substantive_keywords:
        if kw in issue:
            return "实质"

    return "格式"


def _get_reviewer_for_review(review: dict, default_author: str = "checking-cn-patent-format"):
    severity = _classify_severity(review)
    reviewer = REVIEWER_BY_SEVERITY.get(severity, REVIEWER_BY_SEVERITY["default"])
    return reviewer["author"], reviewer["initials"]


def add_reviews(input_path: str, output_path: str, reviews: list, author: str = "checking-cn-patent-format"):
    """
    主函数：将审查意见添加到 Word 文档中。

    Args:
        input_path: 输入 docx 文件路径
        output_path: 输出 docx 文件路径
        reviews: 审查意见列表
        author: 批注作者名称

    Returns:
        处理结果统计字典
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(f"输入文件不存在: {input_path}")

    converted_docx = None
    actual_input = input_path

    # 如果是 .doc 格式，先转换为 .docx
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

    # 使用临时目录处理文档
    with tempfile.TemporaryDirectory(prefix="review_add_") as temp_dir:
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
        work_dir_for_headers = output_path.parent
        if work_dir_for_headers:
            header_files = sorted(work_dir_for_headers.glob("header_sections_*.json"))
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

        success_count = 0
        skip_count = 0
        abstract_fig_anchor = None
        annotation_logger = AnnotationBatchLogger()

        patent_analyzer = PatentAnalyzer(str(actual_input))
        patent_analyzer.extract_text()

        # 逐条处理审查意见
        for i, review in enumerate(reviews):
            try:
                # 【BUG修复#1】清理所有文本字段中的XML非法控制字符（防止崩溃）
                _sanitize_review(review)

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
                paragraph_index = review.get("paragraph_index", None)

                # 跳过没有上下文的无效条目
                if not context:
                    print(f"  跳过无效条目 #{i+1}: context 为空")
                    skip_count += 1
                    continue

                # 【BUG修复#3】验证关键字段完整性，跳过不完整记录
                required_fields = ['section', 'issue', 'suggestion', 'action_type']
                missing_fields = [f for f in required_fields if not review.get(f)]
                if missing_fields:
                    print(f"  跳过不完整条目 #{i+1}: 缺少字段 {missing_fields}")
                    skip_count += 1
                    continue

                print(f'  处理 #{i+1}: [{section}] action_type={action_type} "{context}"', end="")
                if occurrence is not None:
                    print(f' occurrence={occurrence}', end="")
                if highlight_text:
                    print(f' highlight="{highlight_text}"', end="")
                print()

                severity = _classify_severity(review)
                reviewer_author, reviewer_initials = _get_reviewer_for_review(review, default_author=author)

                clean_issue = _strip_comment_labels(issue)
                clean_suggestion = _strip_comment_labels(suggestion)
                comment_text = ""
                if section == "权利要求书" and claim_number is not None:
                    comment_text = f"权利要求{claim_number}: "
                comment_text += f"【问题描述】{clean_issue}\n【修改建议】{clean_suggestion}"

                if section == "摘要附图":
                    if abstract_fig_anchor is None:
                        abstract_fig_anchor = _insert_abstract_fig_anchor(doc, section_ranges, paragraphs)
                        if abstract_fig_anchor is not None:
                            print(f"    ✓ 已在摘要附图章节结尾插入锚定文本 '{ABSTRACT_FIG_ANCHOR_TEXT}'")

                    if abstract_fig_anchor is not None:
                        result = _add_comment_to_abstract_fig_anchor(doc, abstract_fig_anchor, comment_text)
                        if result:
                            success_count += 1
                            print(f"    ✓ 已在摘要附图锚定文本上添加批注")
                        else:
                            skip_count += 1
                            print(f"    ⚠ 无法在摘要附图锚定文本上添加批注")
                    else:
                        print(f"    ⚠ 无法在摘要附图章节插入锚定文本")
                        skip_count += 1
                    continue

                # 根据 action_type 执行不同操作
                if action_type == "replace":
                    if not old_text or not new_text:
                        print(f"    ⚠ action_type=replace 但 old_text 或 new_text 为空，降级为仅添加批注")
                        result = _try_add_comment_with_header_fallback(doc, context, section, section_ranges, paragraphs, comment_text, occurrence=occurrence, highlight_text=highlight_text, paragraph_index=paragraph_index)
                        if result:
                            success_count += 1
                            if result.startswith("header:"):
                                print(f"    ✓ 已在页眉中添加批注（降级，{result}）")
                            else:
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
                        result = _try_add_comment_with_header_fallback(doc, context, section, section_ranges, paragraphs, comment_text, occurrence=occurrence, highlight_text=highlight_text, paragraph_index=paragraph_index)
                        if result:
                            success_count += 1
                            if result.startswith("header:"):
                                print(f"    ✓ 已在页眉中添加批注（降级，{result}）")
                            else:
                                print(f"    ✓ 已添加批注（降级，精准定位）")
                        else:
                            print(f"    ⚠ 未找到上下文文本: \"{context}\"")
                            skip_count += 1
                        continue

                    # 为替换操作添加批注
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
                        result = _try_add_comment_with_header_fallback(doc, context, section, section_ranges, paragraphs, comment_text, occurrence=occurrence, highlight_text=highlight_text, paragraph_index=paragraph_index)
                        if result:
                            success_count += 1
                            if result.startswith("header:"):
                                print(f"    ✓ 已在页眉中添加批注（降级，{result}）")
                            else:
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
                        result = _try_add_comment_with_header_fallback(doc, context, section, section_ranges, paragraphs, comment_text, occurrence=occurrence, highlight_text=highlight_text, paragraph_index=paragraph_index)
                        if result:
                            success_count += 1
                            if result.startswith("header:"):
                                print(f"    ✓ 已在页眉中添加批注（降级，{result}）")
                            else:
                                print(f"    ✓ 已添加批注（降级，精准定位）")
                        else:
                            print(f"    ⚠ 未找到上下文文本: \"{context}\"")
                            skip_count += 1
                        continue

                    # 为删除操作添加批注
                    first_rev, last_rev = _find_revision_range(new_nodes)
                    if first_rev is not None and last_rev is not None:
                        doc.add_comment(start=first_rev, end=last_rev, text=comment_text)
                    else:
                        doc.add_comment(start=new_nodes[0], end=new_nodes[-1], text=comment_text)
                    success_count += 1
                    print(f"    ✓ 已在修订模式下删除并添加批注（精准定位）")

                else:
                    # 默认操作：仅添加批注
                    result = _try_add_comment_with_header_fallback(doc, context, section, section_ranges, paragraphs, comment_text, occurrence=occurrence, highlight_text=highlight_text, paragraph_index=paragraph_index)
                    if result:
                        success_count += 1
                        if result.startswith("header:"):
                            print(f"    ✓ 已在页眉中添加批注（{result}）")
                        else:
                            print(f"    ✓ 已添加批注（精准定位）")
                    else:
                        print(f"    ⚠ 未找到文本: \"{context}\"")
                        skip_count += 1

            except Exception as e:
                # 【BUG修复#1增强】全局异常捕获：防止单条审查意见处理失败导致整个脚本崩溃
                print(f"  ❌ 处理 #{i+1} 时发生异常: {type(e).__name__}: {str(e)}")
                print(f"     该条目将被跳过，继续处理后续条目...")
                annotation_logger.log_failure(
                    section=review.get('section', ''),
                    context_preview=(review.get('context') or '')[:80],
                    error=e,
                    review_index=i
                )
                skip_count += 1
                import traceback
                traceback.print_exc()
                continue

        stats = annotation_logger.get_statistics()
        print(f"\n批注添加统计:")
        print(f"  成功: {stats['successful']} 个")
        print(f"  跳过: {stats['skipped']} 个")
        print(f"  失败: {stats['failed']} 个")
        if stats['total'] > 0:
            print(f"  成功率: {stats['success_rate']:.1f}%")

        print(f"正在保存修改 ...")
        doc.save()

        print(f"正在打包为 {output_path.name} ...")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pack_document(str(unpacked_dir), str(output_path), validate=False)

    if converted_docx:
        try:
            Path(converted_docx).unlink()
            print(f"已清理临时转换文件: {Path(converted_docx).name}")
        except OSError:
            pass

    print(f"\n处理完成：共 {len(reviews)} 处，成功 {success_count} 处，跳过 {skip_count} 处")
    return {"total": len(reviews), "success": success_count, "skip": skip_count, "annotation_stats": stats}


def main():
    """命令行入口函数。"""
    parser = argparse.ArgumentParser(description="审查意见批注添加工具")
    parser.add_argument("input", help="输入 docx 文件路径")
    parser.add_argument("output", help="输出 docx 文件路径")
    parser.add_argument("--reviews-file", required=True, help="审查意见 JSON 文件路径")
    parser.add_argument("--author", default="checking-cn-patent-format", help="批注作者名称")

    args = parser.parse_args()

    reviews_path = Path(args.reviews_file)
    if not reviews_path.exists():
        print(f"错误：审查意见文件不存在: {reviews_path}")
        sys.exit(1)

    with open(reviews_path, "r", encoding="utf-8") as f:
        reviews = json.load(f)

    add_reviews(args.input, args.output, reviews, args.author)


# 当直接运行此脚本时执行 main 函数
if __name__ == "__main__":
    main()

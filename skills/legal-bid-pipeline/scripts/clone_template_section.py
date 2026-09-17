#!/usr/bin/env python3
# Maintained by Lu Lingyan, Deheng (Wuxi) Law Firm.
"""
模板章节拷贝器 (Clone Template Section) — 四步拷贝法脚本化

把招标文件模板章节拷贝到投标文件，模拟 Word Ctrl+C/V 的内部行为，避免
"deepcopy 段落 XML 后编号全丢、字体全变"的经典问题。

四步（缺一不可，来源 references/docx_engineering.md 第五节）：
  ① 段落 deepcopy（内容层）
  ② numbering 定义拷贝：源文档用到的 abstractNum 拷进目标 numbering.xml，
     分配新 abstractNumId；num 指向它；段落 numId remap
  ③ 字体扁平化：每个 run 显式补齐 rFonts eastAsia/ascii/hAnsi + sz
  ④ 失效 pStyle 清理：目标文档不存在的样式直接删，重要属性拍平进 pPr

用法（CLI）:
    # 用章节特征句定位（推荐，最安全）
    python clone_template_section.py \\
        --source 招标文件.docx \\
        --target 投标文件.docx \\
        --feature-sentence "磋商申请及声明" \\
        --paragraph-count 30 \\
        --output 投标文件_v1.docx

    # 用段落索引范围定位（索引容易随模板版本变化，不推荐）
    python clone_template_section.py \\
        --source 招标文件.docx \\
        --target 投标文件.docx \\
        --start-index 0 --end-index 30 \\
        --output 投标文件_v1.docx

    # dry-run：只报告将要拷贝的内容和检测到的问题，不写文件
    python clone_template_section.py ... --dry-run

用法（Python API）:
    from clone_template_section import clone_section
    clone_section(
        source_path="招标文件.docx",
        target_path="投标文件.docx",
        feature_sentence="磋商申请及声明",
        paragraph_count=30,
        output_path="投标文件_v1.docx",
    )

重要约束：
- 拷贝前会全文搜索 feature_sentence，必须唯一命中（=1），否则拒绝执行
  （避免残留块导致"改了个寂寞"，对应 docx_engineering.md 五点六节）
- 不会"整体复制"源 numbering.xml——ID 冲突会把目标已有列表冲乱
- 拷贝后建议调用 setup_pagination.py 重新配置页码
"""

import argparse
import copy
import sys
from typing import Optional, Tuple, List

from docx import Document
from docx.oxml.ns import qn, nsmap
from docx.oxml import OxmlElement


# ────────────────────────────────────────────────────────────
# 工具函数
# ────────────────────────────────────────────────────────────

def _get_numbering_part(doc) -> Optional[object]:
    """获取文档的 numbering part（可能为 None）。"""
    try:
        return doc.part.numbering_part
    except KeyError:
        return None
    except AttributeError:
        return None


def _get_or_create_numbering_part(doc):
    """获取或创建 numbering part。"""
    try:
        return doc.part.numbering_part
    except KeyError:
        # 文档没有 numbering part，创建一个空的
        from docx.opc.part import Part
        from docx.opc.constants import RELATIONSHIP_TYPE as RT
        # 这种情况下简单返回 None，让上层处理
        return None
    except AttributeError:
        return None


def _find_paragraph_by_feature(doc, feature_sentence: str) -> Tuple[Optional[int], int]:
    """按特征句定位段落。返回 (首个匹配的段落索引, 总匹配数)。
    特征句越独特越好（避免重名）。
    """
    matches = 0
    first_idx = None
    for i, p in enumerate(doc.paragraphs):
        if feature_sentence in p.text:
            matches += 1
            if first_idx is None:
                first_idx = i
    return first_idx, matches


def _collect_paragraph_number_ids(paragraph_elements: List) -> set:
    """从段落 XML 元素列表中收集所有用到的 numId。"""
    num_ids = set()
    for p in paragraph_elements:
        # 查找段落中的 numPr/numId
        numPr_list = p.findall(qn('w:pPr') + '/' + qn('w:numPr'))
        for numPr in numPr_list:
            numId_el = numPr.find(qn('w:numId'))
            if numId_el is not None:
                val = numId_el.get(qn('w:val'))
                if val is not None:
                    num_ids.add(int(val))
    return num_ids


def _collect_paragraph_styles(paragraph_elements: List) -> set:
    """从段落 XML 元素列表中收集所有引用的 pStyle ID。"""
    style_ids = set()
    for p in paragraph_elements:
        pStyle_list = p.findall(qn('w:pPr') + '/' + qn('w:pStyle'))
        for s in pStyle_list:
            val = s.get(qn('w:val'))
            if val is not None:
                style_ids.add(val)
    return style_ids


def _get_existing_style_ids(doc) -> set:
    """获取目标文档已有的样式 ID 集合。"""
    existing = set()
    for style in doc.styles:
        try:
            existing.add(style.style_id)
        except AttributeError:
            pass
    return existing


def _get_numbering_definitions(numbering_part) -> Tuple[dict, dict]:
    """从 numbering part 提取 abstractNum 和 num 定义。
    返回 ({abstractNumId: element}, {numId: abstractNumId})
    """
    if numbering_part is None:
        return {}, {}
    numbering_el = numbering_part.element
    abstract_nums = {}
    nums_mapping = {}  # numId -> abstractNumId

    for ab in numbering_el.findall(qn('w:abstractNum')):
        ab_id = ab.get(qn('w:abstractNumId'))
        if ab_id is not None:
            abstract_nums[int(ab_id)] = ab

    for num in numbering_el.findall(qn('w:num')):
        num_id = num.get(qn('w:numId'))
        ab_ref = num.find(qn('w:abstractNumId'))
        if num_id is not None and ab_ref is not None:
            ab_id = ab_ref.get(qn('w:val'))
            if ab_id is not None:
                nums_mapping[int(num_id)] = int(ab_id)

    return abstract_nums, nums_mapping


def _get_max_ids(numbering_part) -> Tuple[int, int]:
    """获取当前最大的 abstractNumId 和 numId。返回 (max_ab, max_num)"""
    abstract_nums, nums_mapping = _get_numbering_definitions(numbering_part)
    max_ab = max(abstract_nums.keys()) if abstract_nums else -1
    max_num = max(nums_mapping.keys()) if nums_mapping else -1
    return max_ab, max_num


# ────────────────────────────────────────────────────────────
# 四步拷贝法核心
# ────────────────────────────────────────────────────────────

def clone_section(
    source_path: str,
    target_path: str,
    feature_sentence: Optional[str] = None,
    start_index: Optional[int] = None,
    paragraph_count: Optional[int] = None,
    end_index: Optional[int] = None,
    output_path: Optional[str] = None,
    dry_run: bool = False,
    verbose: bool = True,
) -> bool:
    """
    执行四步拷贝法，把源文档的指定章节拷贝到目标文档末尾。

    参数：
        source_path: 源文档（通常是招标文件模板章节所在的 docx）
        target_path: 目标文档（投标文件）
        feature_sentence: 章节定位特征句（推荐用法）
        start_index: 起始段落索引（与 feature_sentence 二选一）
        paragraph_count: 要拷贝的段落数
        end_index: 结束段落索引（与 paragraph_count 二选一）
        output_path: 输出路径（默认原地修改 target）
        dry_run: 只报告，不写文件
        verbose: 是否打印处理过程

    返回 True 表示成功（或 dry-run 检测无致命问题），False 表示失败。
    """
    def _log(msg):
        if verbose:
            print(msg)

    # ── 加载文档 ──
    _log(f"▶ 加载源文档：{source_path}")
    src_doc = Document(source_path)
    _log(f"▶ 加载目标文档：{target_path}")
    tgt_doc = Document(target_path)

    src_paras = src_doc.paragraphs
    tgt_paras = tgt_doc.paragraphs
    _log(f"  源文档共 {len(src_paras)} 段")
    _log(f"  目标文档共 {len(tgt_paras)} 段")

    # ── 步骤 0：定位要拷贝的段落范围 ──
    if feature_sentence:
        idx, matches = _find_paragraph_by_feature(src_doc, feature_sentence)
        if matches == 0:
            _log(f"✗ 特征句「{feature_sentence}」在源文档中未找到")
            return False
        if matches > 1:
            _log(f"✗ 特征句「{feature_sentence}」在源文档中命中 {matches} 次，"
                 "请提供更独特的特征句（参见 docx_engineering.md 五点六节）")
            return False
        start_idx = idx
        _log(f"  特征句定位：起始段 = {start_idx}")
    else:
        if start_index is None:
            _log("✗ 必须提供 feature_sentence 或 start_index")
            return False
        start_idx = start_index
        _log(f"  索引定位：起始段 = {start_idx}")

    if end_index is not None:
        end_idx = end_index
    elif paragraph_count is not None:
        end_idx = start_idx + paragraph_count
    else:
        _log("✗ 必须提供 paragraph_count 或 end_index")
        return False

    if end_idx > len(src_paras):
        end_idx = len(src_paras)
        _log(f"  ⚠ 结束索引超出范围，自动截到 {end_idx}")

    _log(f"  拷贝范围：[{start_idx}, {end_idx})，共 {end_idx - start_idx} 段")

    # 提取源段落的 XML 元素
    src_body = src_doc.element.body
    src_para_elements = [p for p in src_body.findall(qn('w:p'))]
    src_slice = src_para_elements[start_idx:end_idx]

    if not src_slice:
        _log("✗ 选定范围为空")
        return False

    # ── 四步法预处理：分析需要重映射的资源 ──
    _log("\n▶ 四步拷贝法预处理")

    # 第②步：numbering 重新映射
    src_num_part = _get_numbering_part(src_doc)
    tgt_num_part = _get_numbering_part(tgt_doc)

    src_num_ids_used = _collect_paragraph_number_ids(src_slice)
    _log(f"  步骤② 源段落使用的 numId：{src_num_ids_used if src_num_ids_used else '（无）'}")

    # 建立 numId 重映射表
    num_id_remap = {}  # 源 numId -> 目标 numId（新分配）
    if src_num_ids_used and src_num_part and tgt_num_part:
        src_abs_nums, src_num_map = _get_numbering_definitions(src_num_part)
        tgt_max_ab, tgt_max_num = _get_max_ids(tgt_num_part)
        tgt_abs_nums, _ = _get_numbering_definitions(tgt_num_part)

        next_ab = tgt_max_ab + 1
        next_num = tgt_max_num + 1
        # 按 abstractNumId 去重（多个 numId 可能指向同一个 abstractNum）
        ab_already_added = {}  # 源 abstractNumId -> 新 abstractNumId

        for src_num_id in src_num_ids_used:
            src_ab_id = src_num_map.get(src_num_id)
            if src_ab_id is None:
                continue
            if src_ab_id in ab_already_added:
                # 复用已分配的
                new_ab_id = ab_already_added[src_ab_id]
            else:
                new_ab_id = next_ab
                next_ab += 1
                ab_already_added[src_ab_id] = new_ab_id
                # 拷贝 abstractNum 元素并改 ID
                src_ab_el = src_abs_nums[src_ab_id]
                new_ab_el = copy.deepcopy(src_ab_el)
                new_ab_el.set(qn('w:abstractNumId'), str(new_ab_id))
                # 插入到目标 numbering 的 abstractNum 区段（必须在 num 区段之前）
                _insert_abstract_num(tgt_num_part.element, new_ab_el)

            # 创建新的 num 指向新 abstractNum
            new_num_el = OxmlElement('w:num')
            new_num_el.set(qn('w:numId'), str(next_num))
            ab_ref = OxmlElement('w:abstractNumId')
            ab_ref.set(qn('w:val'), str(new_ab_id))
            new_num_el.append(ab_ref)
            tgt_num_part.element.append(new_num_el)

            num_id_remap[src_num_id] = next_num
            next_num += 1

        _log(f"  步骤② numbering 重映射：{num_id_remap}")
    elif src_num_ids_used:
        _log(f"  步骤② ⚠ 源段落用到 numId {src_num_ids_used}，但源/目标 numbering part 缺失，编号可能丢失")

    # 第④步：pStyle 失效检查
    src_styles_used = _collect_paragraph_styles(src_slice)
    tgt_existing_styles = _get_existing_style_ids(tgt_doc)
    missing_styles = src_styles_used - tgt_existing_styles
    if missing_styles:
        _log(f"  步骤④ 目标文档缺失的 pStyle：{missing_styles}（拷贝时将清除这些样式引用）")
    else:
        _log(f"  步骤④ 目标文档已包含所有引用的样式（{src_styles_used or '无样式引用'}）")

    if dry_run:
        _log("\n▶ dry-run 完成，未写入文件")
        return True

    # ── 实际拷贝：执行四步 ──
    _log("\n▶ 开始拷贝段落（四步法）")
    tgt_body = tgt_doc.element.body

    for src_p in src_slice:
        # 第①步：deepcopy
        new_p = copy.deepcopy(src_p)

        # 第②步：numId remap
        if num_id_remap:
            _remap_num_ids_in_paragraph(new_p, num_id_remap)

        # 第③步：字体扁平化
        _flatten_fonts_in_paragraph(new_p)

        # 第④步：失效 pStyle 清理
        if missing_styles:
            _strip_invalid_pstyles(new_p, missing_styles)

        # 插入到目标 body 末尾（但在 sectPr 之前，如果有）
        _insert_paragraph_before_sectPr(tgt_body, new_p)

    _log(f"  ✓ 已拷贝 {len(src_slice)} 段到目标文档末尾")

    # ── 保存 ──
    out_path = output_path or target_path
    tgt_doc.save(out_path)
    _log(f"\n▶ 已保存到：{out_path}")
    _log("  建议后续：1) 用 Word 打开手动 F9 刷新所有域 2) 运行 setup_pagination.py 重新配置页码")
    return True


# ────────────────────────────────────────────────────────────
# 四步法各步的辅助函数
# ────────────────────────────────────────────────────────────

def _insert_abstract_num(numbering_el, new_ab_el):
    """把新的 abstractNum 元素插入到 numbering.xml 的合适位置。
    OOXML 要求所有 abstractNum 必须排在所有 num 之前。
    """
    # 找第一个 num 元素的位置，插到它前面；如果没 num，追加到末尾
    first_num = numbering_el.find(qn('w:num'))
    if first_num is not None:
        first_num.addprevious(new_ab_el)
    else:
        numbering_el.append(new_ab_el)


def _remap_num_ids_in_paragraph(p_el, remap: dict):
    """在段落 XML 中把所有 numId 按重映射表更新。"""
    for numPr in p_el.findall(qn('w:pPr') + '/' + qn('w:numPr')):
        numId_el = numPr.find(qn('w:numId'))
        if numId_el is not None:
            old_val = numId_el.get(qn('w:val'))
            if old_val is not None:
                old_int = int(old_val)
                if old_int in remap:
                    numId_el.set(qn('w:val'), str(remap[old_int]))


def _flatten_fonts_in_paragraph(p_el):
    """第③步：每个 run 显式补齐 rFonts eastAsia/ascii/hAnsi + sz。
    源 run 常只写 hAnsi，eastAsia 靠源 docDefaults 兜底，跨文档后兜底链断裂 → 中文回退默认字体。
    """
    DEFAULT_FONT = '宋体'
    DEFAULT_SIZE = '21'  # 10.5pt（小五 = 21 半磅）

    for r in p_el.findall(qn('w:r')):
        rPr = r.find(qn('w:rPr'))
        if rPr is None:
            rPr = OxmlElement('w:rPr')
            # rPr 必须是 r 的第一个子元素
            r.insert(0, rPr)

        # 字体补齐
        rFonts = rPr.find(qn('w:rFonts'))
        if rFonts is None:
            rFonts = OxmlElement('w:rFonts')
            rPr.insert(0, rFonts)
        for attr in ('w:eastAsia', 'w:ascii', 'w:hAnsi'):
            if rFonts.get(qn(attr)) is None:
                rFonts.set(qn(attr), DEFAULT_FONT)

        # 字号补齐
        sz = rPr.find(qn('w:sz'))
        if sz is None:
            sz = OxmlElement('w:sz')
            rPr.append(sz)
            sz.set(qn('w:val'), DEFAULT_SIZE)


def _strip_invalid_pstyles(p_el, invalid_style_ids: set):
    """第④步：删除目标文档不存在的 pStyle 引用。
    重要属性（如缩进）拍平进 pPr，防止样式失效后段落格式塌缩。
    """
    pPr = p_el.find(qn('w:pPr'))
    if pPr is None:
        return
    for pStyle in pPr.findall(qn('w:pStyle')):
        val = pStyle.get(qn('w:val'))
        if val in invalid_style_ids:
            pPr.remove(pStyle)
            # 拍平基础缩进属性（避免完全失格式）
            if pPr.find(qn('w:ind')) is None:
                ind = OxmlElement('w:ind')
                ind.set(qn('w:firstLineChars'), '200')  # 首行缩进 2 字符
                pPr.append(ind)


def _insert_paragraph_before_sectPr(body_el, new_p):
    """把新段落插入到 body 的 sectPr 之前（如果存在 sectPr），
    否则直接追加。OOXML 规定 sectPr 必须是 body 的最后一个子元素。
    """
    sectPr = body_el.find(qn('w:sectPr'))
    if sectPr is not None:
        sectPr.addprevious(new_p)
    else:
        body_el.append(new_p)


# ────────────────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────────────────

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="四步拷贝法：把招标模板章节拷贝到投标文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--source", required=True, help="源文档（如招标文件.docx）")
    parser.add_argument("--target", required=True, help="目标文档（如投标文件.docx）")
    parser.add_argument("--output", "-o", help="输出路径（默认原地修改 target）")
    loc = parser.add_mutually_exclusive_group(required=True)
    loc.add_argument("--feature-sentence", help="章节定位特征句（推荐，需唯一命中）")
    loc.add_argument("--start-index", type=int, help="起始段落索引（不推荐，易随模板版本变化）")
    parser.add_argument("--paragraph-count", type=int, help="要拷贝的段落数")
    parser.add_argument("--end-index", type=int, help="结束段落索引（与 paragraph_count 二选一）")
    parser.add_argument("--dry-run", action="store_true", help="只报告，不写文件")
    args = parser.parse_args(argv)

    if args.start_index is None and not args.feature_sentence:
        parser.error("必须提供 --feature-sentence 或 --start-index")
    if args.paragraph_count is None and args.end_index is None:
        parser.error("必须提供 --paragraph-count 或 --end-index")

    ok = clone_section(
        source_path=args.source,
        target_path=args.target,
        feature_sentence=args.feature_sentence,
        start_index=args.start_index,
        paragraph_count=args.paragraph_count,
        end_index=args.end_index,
        output_path=args.output,
        dry_run=args.dry_run,
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

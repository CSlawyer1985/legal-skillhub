# -*- coding: utf-8 -*-
"""
build_master.py — 母版化（阶段1 步骤④）/ 生成（阶段2）完整实现

将原始 DOCX 按「变量映射表」替换为通用母版；或将母版按「变量→真实值」替换为成品。
核心铁律：只替换文本、绝不改动格式（字体/字号/对齐/行距/表格边框均不可触碰）。

v5 替换策略（精确区间替换，根治 run 级格式损坏）:
  Pass 1  普通替换：单 <w:t> 节点内的直接字符串替换（公司名、固定长文本）
  Pass 2  长词优先：按 old 长度降序重排后再替换，防止短词先命中污染长词
  Pass 3  精确区间替换：段落内所有 <w:t> 拼接成完整文本 → 按映射规则 find 定位
          每个 old 的精确区间 → 区间起始节点写入 new、其余被覆盖节点清空
          （保留 run 结构含下划线）、区间外字符原样保留
          解决日期等被 Word 拆分的跨节点文本，且不丢下划线、不拆行
          注意：不用 difflib 模糊对齐（其会把新变量名与原文的公共字符误判为
          equal，导致替换文本被拆开、下划线归属错位）

映射 JSON 格式（old 必须是模板中的原文，new 是 {{变量}} 或真实值）:
  [
    {"old": "张伟", "new": "{{委托人姓名}}"},
    {"old": "民间借贷纠纷", "new": "{{案由}}"},
    {"old": "【2026】年【5】月【13】日", "new": "{{日期}}"}
  ]

映射铁律（踩坑史沉淀，2026-08 同事测试报告固化）:
  - 绝不使用短数字作 old（如 "10"、"50"），会误伤其他字段
  - 同一变量出现多次只映射一次，全文替换自动覆盖所有位置
  - old 优先取「填空位本体文本」（如 "张伟"），而非带上下文的整句
    （如 "受理 张伟 诉"）——上下文 old 会把新文本塞进无下划线前缀 run，导致下划线丢失
  - 避免 old 是其他 new 的子串（如 "原告" 会污染 "{{原告}}"）——用带空格上下文规避
  - 日期等被拆分的文本，old 写完整串，依赖 Pass 3 精确区间替换匹配
  - 全角/半角括号以模板中的实际字符为准

用法:
  python build_master.py <原.docx> <映射.json> <输出母版.docx> [--verify]
  python build_master.py <原.docx> <映射.json> --dry-run       # 预览替换效果，不写入文件
"""
import sys
import json
import re
import zipfile
import os
from pathlib import Path

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

# w:t 精确匹配：<w:t> 或 <w:t xml:space="preserve">，不用宽泛 <w:t[^>]*>（会把 <w:tab/> 误匹配）
WT_RE = r"<w:t(?:\s[^>]*)?>"


# ---------------------------------------------------------------------------
# 核心替换引擎
# ---------------------------------------------------------------------------

def split_t_nodes(xml_text):
    """把 document.xml 按 <w:p> 段落切分，返回 (段落列表, 前后缀)。"""
    parts = re.split(r"(<w:p[ >])", xml_text)
    return parts


def parse_style_underline_map(styles_xml):
    """解析 styles.xml，返回 {styleId: 是否含下划线（<w:u> 非 none）}。"""
    style_map = {}
    for m in re.finditer(r"<w:style\b[^>]*>.*?</w:style>", styles_xml, re.DOTALL):
        style = m.group(0)
        sid = re.search(r'w:styleId="([^"]+)"', style)
        if not sid:
            continue
        has_u = False
        for um in re.finditer(r"<w:u(?:\s[^>]*)?/?>", style):
            if 'w:val="none"' not in um.group(0):
                has_u = True
                break
        style_map[sid.group(1)] = has_u
    return style_map


def extract_t_texts(para_xml, style_map=None):
    """提取一个段落 XML 内所有 <w:t> 节点的 (起止位置, 文本, 是否下划线)。
    下划线三级检测：run 级 <w:u>（非 none）→ rStyle 字符样式 → 段落 pStyle。"""
    style_map = style_map or {}
    # 段落级样式是否含下划线
    p_underline = False
    pm = re.search(r'<w:pStyle[^>]*w:val="([^"]+)"', para_xml)
    if pm and style_map.get(pm.group(1)):
        p_underline = True

    # 先扫所有 run 的下划线状态（run 区间 -> 是否下划线）
    run_spans = []
    for m in re.finditer(r"<w:r[ >].*?</w:r>", para_xml, re.DOTALL):
        run = m.group(0)
        has_u = None  # None = 未显式定义
        for um in re.finditer(r"<w:u(?:\s[^>]*)?/?>", run):
            has_u = ('w:val="none"' not in um.group(0))
        if has_u is None:
            rs = re.search(r'<w:rStyle[^>]*w:val="([^"]+)"', run)
            has_u = bool(rs and style_map.get(rs.group(1))) or p_underline
        run_spans.append((m.start(), m.end(), has_u))

    nodes = []
    for m in re.finditer(WT_RE + r"(.*?)</w:t>", para_xml, re.DOTALL):
        t_start, t_end, text = m.start(1), m.end(1), m.group(1)
        has_u = False
        for rs, re_, flag in run_spans:
            if rs <= t_start < re_:
                has_u = flag
                break
        nodes.append((t_start, t_end, text, has_u))
    return nodes


def merge_replace_paragraph(para_xml, mapping_sorted, style_map=None):
    """
    Pass 3 核心（v5.2）：段落内所有 <w:t> 拼接成全文 → 按映射规则定位每个 old 的
    精确区间 → new 写入「区间内第一个带下划线节点」（无下划线则写起始节点），
    其余被覆盖节点清空（保留 run 结构含下划线）、区间外字符原样保留。
    v5.1 修复：new 继承「填空位（带下划线节点）」的下划线格式，而非「前缀（无下划线起始节点）」。
    v5.2 修复：下划线检测扩展到「样式继承」——run 级 <w:u>、rStyle 字符样式、段落 pStyle 三级。
    返回 (新段落XML, 命中次数)。
    """
    nodes = extract_t_texts(para_xml, style_map)
    if len(nodes) < 2:
        return para_xml, 0, [], []

    full_text = "".join(t for _, _, t, _u in nodes)

    # 定位所有 old 的替换区间（长词优先，标记已占用避免重叠）
    replacements = []
    hit_olds = []          # 命中的 old（用于 dry-run 命中判定与 build 命中比对）
    skipped_overlaps = []  # 因区间重叠被跳过的 old（v3.3.2：静默跳过 → 显式告警）
    used = [False] * len(full_text)
    for m in mapping_sorted:
        old = m["old"]
        if not old:
            continue
        start = 0
        while True:
            idx = full_text.find(old, start)
            if idx == -1:
                break
            if any(used[idx: idx + len(old)]):
                skipped_overlaps.append((old, m["new"]))
                start = idx + 1
                continue
            replacements.append((idx, idx + len(old), m["new"]))
            hit_olds.append(old)
            for k in range(idx, idx + len(old)):
                used[k] = True
            start = idx + len(old)

    if not replacements:
        return para_xml, 0, hit_olds, skipped_overlaps

    replacements.sort(key=lambda r: r[0])

    # 每个节点在 full_text 中的字符区间 [char_start, char_end) + 下划线标志
    ranges = []
    underline_flags = []
    pos = 0
    for _, _, t, u in nodes:
        ranges.append([pos, pos + len(t)])
        underline_flags.append(u)
        pos += len(t)

    # 确定每个替换区间的「写入节点」：区间内第一个带下划线节点，无则起始节点
    write_node = {}
    for ri, (rs, re_, _rnew) in enumerate(replacements):
        chosen = None
        for ni, (cs, ce) in enumerate(ranges):
            if cs < re_ and rs < ce and underline_flags[ni]:
                chosen = ni
                break
        if chosen is None:
            for ni, (cs, ce) in enumerate(ranges):
                if cs <= rs < ce:
                    chosen = ni
                    break
        write_node[ri] = chosen

    # 逐节点构建输出：区间外原样保留，写入节点写 new，其余覆盖节点清空
    result_texts = [""] * len(nodes)
    for ni, (cs, ce) in enumerate(ranges):
        cov = []
        for ri, (rs, re_, rnew) in enumerate(replacements):
            ov_s = max(rs, cs)
            ov_e = min(re_, ce)
            if ov_s < ov_e:
                cov.append((ov_s, ov_e, rnew, ri))
        cov.sort()
        cursor = cs
        parts = []
        for (ov_s, ov_e, rnew, ri) in cov:
            if cursor < ov_s:
                parts.append(full_text[cursor:ov_s])
            if write_node[ri] == ni:  # 本节点是该替换区间的写入节点 → 写入 new
                parts.append(rnew)
            cursor = ov_e
        if cursor < ce:
            parts.append(full_text[cursor:ce])
        result_texts[ni] = "".join(parts)

    # 重建段落 XML：每个 <w:t> 写入其 result_texts[ni]
    result = []
    last = 0
    for ni, (s, e, _t, _u) in enumerate(nodes):
        result.append(para_xml[last:s])
        result.append(result_texts[ni])
        last = e
    result.append(para_xml[last:])
    return "".join(result), len(replacements), hit_olds, skipped_overlaps


def check_mapping_conflicts(mapping):
    """构建前安全检查：拦截/告警映射陷阱（子串污染、替换顺序、跨节点、区间重叠）。返回 (阻断列表, 告警列表)。"""
    blockers = []
    warnings = []
    cross_node_olds = []  # v3.3.2 问题5：跨节点提醒合并降噪
    for m in mapping:
        old, new = m["old"], m["new"]
        # 1) old 是其他 new 的子串 → 会污染已生成的变量（真错误）
        for o in mapping:
            if o is not m and old in o["new"] and old != o["new"]:
                blockers.append(f"old '{old}' 是 new '{o['new']}' 的子串，会污染变量")
        # 2) old 是其他更长 old 的子串（提醒人工确认替换顺序，长词优先已缓解）
        for o in mapping:
            if o is not m and old in o["old"] and len(old) < len(o["old"]):
                warnings.append(f"old '{old}' 是 old '{o['old']}' 的子串，注意替换顺序")
        # 3) old 疑似跨节点（收集后合并为一行，v3.3.2 降噪）
        # 生成方向的 old 是 {{变量}}，为母版化时整体写入的单节点文本，不会跨节点——跳过
        if not old.startswith("{{") and any(c in old for c in "年月日时分【】、，"):
            cross_node_olds.append(old)

    # 问题5：跨节点提醒合并为一行汇总（不再逐条刷屏）
    if cross_node_olds:
        preview = cross_node_olds[:5]
        suffix = "…" if len(cross_node_olds) > 5 else ""
        warnings.append(
            f"{len(cross_node_olds)} 条 old 含年月日等字符、可能跨 <w:t> 节点"
            f"（Pass3 已自动处理跨节点匹配，仅实际未命中时需关注）：{preview}{suffix}"
        )

    # 4) v3.3.2 问题3：old 两两「边界重叠」检测（相邻填空位：A 尾部字符 == B 头部字符，
    #    文档中相邻时区间重叠会导致短规则被静默跳过）——静态预判，提示合并或调整边界
    def _norm(s):
        return re.sub(r"\s", "", s)

    for i in range(len(mapping)):
        for j in range(i + 1, len(mapping)):
            a, b = mapping[i]["old"], mapping[j]["old"]
            na, nb = _norm(a), _norm(b)
            if not na or not nb or na == nb:
                continue
            if na in nb or nb in na:
                continue  # 子串关系已由检查 2 覆盖
            overlap = False
            for L in range(min(len(na), len(nb)), 1, -1):
                if na.endswith(nb[:L]) or nb.endswith(na[:L]):
                    overlap = True
                    break
            if overlap:
                warnings.append(
                    f"old '{a}' 与 '{b}' 边界重叠（文档中相邻时区间冲突、短规则会被跳过），"
                    f"建议合并为整段替换或调整 old 边界"
                )

    return list(dict.fromkeys(blockers)), list(dict.fromkeys(warnings))


def replace_in_document_xml(xml_text, mapping, style_map=None):
    """
    对 document.xml 内容执行精确区间替换（v5.2）：Pass1 单节点直接替换 → Pass2 长词优先
    → Pass3 段落精确区间替换（跨节点文本合并后按映射区间定位替换，下划线继承）。
    返回 (新XML, 统计dict)。
    """
    # old 按长度降序（长词优先，防短词污染）
    mapping_sorted = sorted(mapping, key=lambda m: len(m["old"]), reverse=True)

    stats = {"pass1_hits": 0, "pass3_hits": 0, "unhit": [], "hit_olds": set(), "skipped_overlaps": []}

    # ---- Pass 1+2: 全局直接替换（长词优先），仅命中单节点内完整出现的 old ----
    pass1_found = set()  # 记录被 Pass1 命中的 old，防止 Pass3 对「old 是 new 前缀」的规则重复替换
    for m in mapping_sorted:
        cnt = xml_text.count(m["old"])
        if cnt:
            xml_text = xml_text.replace(m["old"], m["new"])
            stats["pass1_hits"] += cnt
            pass1_found.add(m["old"])
            stats["hit_olds"].add(m["old"])

    # Pass3 排除「Pass1 已命中且 old 是 new 子串」的规则——否则 Pass3 会在已替换文本里再次匹配 old，产生双重替换
    pass3_mapping = [
        m for m in mapping_sorted
        if not (m["old"] in pass1_found and m["old"] in m["new"])
    ]

    # ---- Pass 3: 段落精确区间替换（处理跨 <w:t> 拆分的 old）----
    parts = split_t_nodes(xml_text)
    out = []
    i = 0
    while i < len(parts):
        part = parts[i]
        if part in ("<w:p ", "<w:p>"):
            para_xml = part
            k = i + 1
            while k < len(parts) and parts[k] not in ("<w:p ", "<w:p>"):
                para_xml += parts[k]
                k += 1
            new_para, hits, hit_olds, skipped = merge_replace_paragraph(para_xml, pass3_mapping, style_map)
            stats["pass3_hits"] += hits
            stats["hit_olds"].update(hit_olds)
            stats["skipped_overlaps"].extend(skipped)
            out.append(new_para)
            i = k
        else:
            out.append(part)
            i += 1
    xml_text = "".join(out)

    # ---- 统计未命中的 old（基于真实命中集合 hit_olds，能区分「已替换」与「从未出现」，杜绝 dry-run 假阳性）----
    for m in mapping:
        if m["old"] not in stats["hit_olds"]:
            stats["unhit"].append(m["old"])

    return xml_text, stats


def replace_in_plain_xml(xml_text, mapping):
    """页眉/页脚等：仅做 Pass 1+2 直接替换（一般无拆分日期）。"""
    mapping_sorted = sorted(mapping, key=lambda m: len(m["old"]), reverse=True)
    hits = 0
    for m in mapping_sorted:
        if m["old"] in xml_text:
            xml_text = xml_text.replace(m["old"], m["new"])
            hits += 1
    return xml_text, hits


# ---------------------------------------------------------------------------
# DOCX 解包 / 重打包
# ---------------------------------------------------------------------------

HEADER_FOOTER = [
    "word/header1.xml", "word/header2.xml", "word/header3.xml",
    "word/footer1.xml", "word/footer2.xml", "word/footer3.xml",
]


def dry_run_preview(src_path, mapping):
    """预览模式：与实跑共用同一替换引擎，命中判定与 build 完全一致，杜绝假阳性。"""
    with zipfile.ZipFile(src_path) as zin:
        xml = zin.read("word/document.xml").decode("utf-8")
        style_map = {}
        if "word/styles.xml" in zin.namelist():
            style_map = parse_style_underline_map(zin.read("word/styles.xml").decode("utf-8"))
    mapping_sorted = sorted(mapping, key=lambda m: len(m["old"]), reverse=True)
    # 直接复用实跑引擎（Pass1 单节点替换 + Pass3 跨节点精确区间替换）
    _, stats = replace_in_document_xml(xml, mapping_sorted, style_map)

    print(f"===== DRY-RUN 预览（{src_path.name}）=====")
    print(f"映射规则 {len(mapping)} 条 | 单节点替换 {stats['pass1_hits']} 处 | 精确区间替换命中 {stats['pass3_hits']} 段")
    print()
    unhit_set = set(stats["unhit"])
    for m in mapping_sorted:
        if m["old"] in stats["hit_olds"]:
            print(f"  ✓ [{m['old']}] → [{m['new']}]  命中")
        else:
            print(f"  ✗ [{m['old']}] → [{m['new']}]  未命中（检查全角/半角、空格，或该文本被 Word 拆分方式特殊）")
    print()
    hit_count = len(stats["hit_olds"])
    print(f"命中: {hit_count}/{len(mapping)} 条规则")
    if stats["unhit"]:
        print(f"未命中 {len(stats['unhit'])} 条: {stats['unhit']}")
    if stats["skipped_overlaps"]:
        skipped = list(dict.fromkeys(stats["skipped_overlaps"]))
        print(f"[!] {len(skipped)} 条规则因区间重叠被跳过（建议合并为整段替换或调整 old 边界）:")
        for old, new in skipped:
            print(f"     - '{old}' → '{new}'")


def verify_run_binding(src_path, out_path, mapping):
    """
    run 级「文本-格式绑定校验」：校验每个 new 文本落在与对应 old 相同的 run 下划线状态中。
    补 T9（剥文本逐字节比对）的盲区——T9 查不出"下划线归属错位"。
    返回问题列表（空 = 通过）。
    """
    def parse_runs(path):
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8")
        runs = []
        for m in re.finditer(r"<w:r[ >].*?</w:r>", xml, re.DOTALL):
            r = m.group(0)
            t = "".join(re.findall(WT_RE + r"([^<]*)</w:t>", r))
            u = ("<w:u " in r) or ("<w:u/>" in r)
            runs.append((t, u))
        return runs

    src_runs = parse_runs(src_path)
    out_runs = parse_runs(out_path)

    old_underline = {}
    for t, u in src_runs:
        if t:
            old_underline.setdefault(t, u)

    problems = []
    for m in mapping:
        old, new = m["old"], m["new"]
        if old not in old_underline:
            continue
        expected_u = old_underline[old]
        found = any(new in t and u == expected_u for t, u in out_runs)
        if not found:
            problems.append(f"{old}→{new} 下划线状态不符（母版 u={'有' if expected_u else '无'}）")
    return problems


def build(src, mapping_path, out, verify=True):
    src_path, out_path = Path(src), Path(out)
    if not src_path.exists():
        print(f"[X] 输入文件不存在: {src}")
        sys.exit(1)

    with open(mapping_path, encoding="utf-8") as f:
        mapping = json.load(f)
    if not isinstance(mapping, list) or not all("old" in m and "new" in m for m in mapping):
        print('[X] 映射 JSON 格式错误，应为 [{"old": ..., "new": ...}, ...]')
        sys.exit(1)

    # 安全检查：拦截空 old（会死循环）与短数字 old（铁律）
    for m in mapping:
        if not m["old"].strip():
            print("[X] 危险映射：old 为空字符串，会匹配任意位置。请填写实际原文。")
            sys.exit(1)
        if re.fullmatch(r"\d{1,3}", m["old"].strip()):
            print(f"[X] 危险映射：old='{m['old']}' 是短数字，会误伤其他字段。请用完整串（如 '【2026】年【5】月'）。")
            sys.exit(1)

    # 映射冲突检测（子串污染阻断 / 替换顺序+跨节点告警）
    blockers, warnings = check_mapping_conflicts(mapping)
    if blockers:
        print("[X] 映射冲突（阻断）：")
        for b in blockers:
            print(f"     - {b}")
        print("     请用带空格上下文规避（如 '  原告  '）或调整 old 取值后重试。")
        sys.exit(1)
    if warnings:
        print("[!] 映射提醒（不阻断，请人工确认）：")
        for w in warnings:
            print(f"     - {w}")

    with zipfile.ZipFile(src_path) as zin:
        names = zin.namelist()
        data = {n: zin.read(n) for n in names}

    # 解析样式下划线映射（供 Pass3 下划线继承检测，覆盖 rStyle/pStyle 样式继承）
    style_map = {}
    if "word/styles.xml" in data:
        style_map = parse_style_underline_map(data["word/styles.xml"].decode("utf-8"))

    # 主文档
    doc_xml = data["word/document.xml"].decode("utf-8")
    doc_xml, stats = replace_in_document_xml(doc_xml, mapping, style_map)
    data["word/document.xml"] = doc_xml.encode("utf-8")

    # 页眉页脚
    hf_hits = 0
    for rel in HEADER_FOOTER:
        if rel in data:
            x = data[rel].decode("utf-8")
            x, h = replace_in_plain_xml(x, mapping)
            data[rel] = x.encode("utf-8")
            hf_hits += h

    # 原子写入：先写临时文件，成功后再 os.replace 替换，防中断残留半成品
    tmp_path = out_path.with_name(out_path.name + ".tmp")
    with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
        for n in names:
            zout.writestr(n, data[n])
    os.replace(tmp_path, out_path)

    print(f"[OK] 母版已生成: {out}")
    print(f"     映射规则 {len(mapping)} 条 | 正文替换 {stats['pass1_hits']} 处 | 精确区间替换命中 {stats['pass3_hits']} 段 | 页眉页脚 {hf_hits} 条规则生效")

    if stats["unhit"]:
        print(f"[!] {len(stats['unhit'])} 条规则未命中（检查全角/半角、或该文本被拆分方式特殊）:")
        for u in stats["unhit"]:
            print(f"     - {u}")
    if stats["skipped_overlaps"]:
        skipped = list(dict.fromkeys(stats["skipped_overlaps"]))
        print(f"[!] {len(skipped)} 条规则因区间重叠被跳过（长词优先占位后短规则区间与之重叠，建议合并为整段替换或调整 old 边界）:")
        for old, new in skipped:
            print(f"     - '{old}' → '{new}'")

    # ---- 验证：确认所有 new 变量均已出现在母版中 ----
    if verify:
        final_xml = data["word/document.xml"].decode("utf-8")
        missing_vars = [m["new"] for m in mapping if m["new"] not in final_xml]
        if missing_vars:
            print(f"[!] {len(missing_vars)} 个变量未出现在母版正文中:")
            for v in missing_vars:
                print(f"     - {v}")
        else:
            print("[OK] 验证通过：所有变量均已写入母版")

        # ---- T9 格式回归验证：剥除 <w:t> 文本后 XML 逐字节比对（w:t 精确正则）----
        with zipfile.ZipFile(src_path) as zorig:
            orig_xml = zorig.read("word/document.xml").decode("utf-8")
        stripped_orig = re.sub(WT_RE + r"[^<]*</w:t>", "", orig_xml)
        stripped_master = re.sub(WT_RE + r"[^<]*</w:t>", "", final_xml)
        if stripped_orig != stripped_master:
            print(f"[!] T9 格式回归验证失败：剥除文本后 XML 有差异（原文 {len(stripped_orig)} 字符 → 母版 {len(stripped_master)} 字符）")
            print(f"    请检查映射规则的 old 字段是否精确匹配模板原文，或映射是否正确。")
        else:
            print(f"[OK] T9 格式零改动验证通过（{len(stripped_orig)} 字符一致）")

        # ---- run 级文本-格式绑定校验（补 T9 盲区）----
        binding_problems = verify_run_binding(src_path, out_path, mapping)
        if binding_problems:
            print(f"[!] run 绑定校验发现 {len(binding_problems)} 处下划线状态异常：")
            for p in binding_problems:
                print(f"     - {p}")
        else:
            print("[OK] run 绑定校验通过（下划线归属与母版一致）")


if __name__ == "__main__":
    if "--dry-run" in sys.argv:
        if len(sys.argv) < 4:
            print("用法: python build_master.py <原.docx> <映射.json> --dry-run")
            sys.exit(1)
        src = Path(sys.argv[1])
        mapping_path = sys.argv[2]
        if not src.exists():
            print(f"[X] 输入文件不存在: {src}")
            sys.exit(1)
        with open(mapping_path, encoding="utf-8") as f:
            mapping = json.load(f)
        if not isinstance(mapping, list) or not all("old" in m and "new" in m for m in mapping):
            print('[X] 映射 JSON 格式错误，应为 [{"old": ..., "new": ...}, ...]')
            sys.exit(1)
        for m in mapping:
            if re.fullmatch(r"\d{1,3}", m["old"].strip()):
                print(f"[X] 危险映射：old='{m['old']}' 是短数字，会误伤其他字段。")
                sys.exit(1)
        dry_run_preview(src, mapping)
    elif len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    else:
        build(sys.argv[1], sys.argv[2], sys.argv[3])

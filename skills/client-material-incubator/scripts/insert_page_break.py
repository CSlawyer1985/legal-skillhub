# -*- coding: utf-8 -*-
"""insert_page_break.py — 两套文书之间安全插入分页符（v3.3.1 新增）

设计要点（对应 2026-08-18 修复的偏移错位 bug）：
1. 单次字符串替换：定位目标标题段落完整 XML → 段首插入 <w:r><w:br w:type="page"/></w:r>
   -> xml.replace(target, new_p, 1)。
   禁止逐段偏移替换（[xml[:m.start()] + p + xml[m.end():] 循环）——插入使文档长度变化后，
   后续段落的原始偏移会错位，导致段落被截断、Word 报文件损坏（18 段被截成 8 段的实测事故）。
2. 三重自检：段落数不变（<w:p> 数量 = 源文件）、XML 可解析、分页符增量恰为 1。
3. 原子写入：先写 .tmp 再 os.replace，防中断残留半成品。
4. 自动备份：原地覆盖（输出=输入）前先复制 .bak，防误操作。

用法:
    python insert_page_break.py <输入.docx> <标题关键词> [输出.docx]
    # 标题关键词建议带空格原文，如 "授 权 委 托 书"；输出缺省时原地覆盖（自动备份 .bak）
"""
import os
import re
import sys
import shutil
import zipfile
import xml.etree.ElementTree as ET

PAGE_BREAK_RUN = '<w:r><w:br w:type="page"/></w:r>'


def normalize(s: str) -> str:
    """去除所有空白字符（半角/全角空格、tab、换行等）后比对。"""
    return re.sub(r"\s", "", s)


def find_title_para(xml: str, keyword: str):
    """定位包含标题关键词的段落完整 XML。返回命中列表（应恰为 1 个）。"""
    pat = re.compile(r"<w:p\b.*?</w:p>", re.DOTALL)
    hits = []
    for m in pat.finditer(xml):
        texts = re.findall(r"<w:t[^>]*>([^<]*)</w:t>", m.group(0))
        if normalize("".join(texts)) == normalize(keyword):
            hits.append(m.group(0))
    return hits


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    src, keyword = sys.argv[1], sys.argv[2]
    out = sys.argv[3] if len(sys.argv) >= 4 else src
    if not os.path.exists(src):
        print(f"[X] 输入文件不存在: {src}")
        sys.exit(1)

    with zipfile.ZipFile(src) as z:
        names = z.namelist()
        data = {n: z.read(n) for n in names}
    xml = data["word/document.xml"].decode("utf-8")
    para_before = len(re.findall(r"<w:p\b.*?</w:p>", xml, re.DOTALL))

    hits = find_title_para(xml, keyword)
    if not hits:
        print(f"[X] 未找到标题段落: {keyword}")
        print(f"    （提示：标题关键词需为整段文本，可带空格原文，如「授 权 委 托 书」）")
        sys.exit(1)
    if len(hits) > 1:
        print(f"[X] 标题段落不唯一（命中 {len(hits)} 处），请提供更精确的关键词")
        sys.exit(1)

    target = hits[0]
    rp = re.search(r"<w:r\b", target)
    if rp is None:
        print("[X] 目标段落内未找到 run，无法插入分页符")
        sys.exit(1)
    new_p = target[: rp.start()] + PAGE_BREAK_RUN + target[rp.start():]
    new_xml = xml.replace(target, new_p, 1)

    # ---- 三重自检 ----
    para_after = len(re.findall(r"<w:p\b.*?</w:p>", new_xml, re.DOTALL))
    if para_after != para_before:
        print(f"[X] 自检失败：段落数 {para_before} -> {para_after}（必须不变）")
        sys.exit(1)
    try:
        ET.fromstring(new_xml)
    except ET.ParseError as e:
        print(f"[X] 自检失败：XML 解析异常 {e}")
        sys.exit(1)
    delta = new_xml.count('w:type="page"') - xml.count('w:type="page"')
    if delta != 1:
        print(f"[X] 自检失败：分页符增量 {delta}（应为 1）")
        sys.exit(1)

    data["word/document.xml"] = new_xml.encode("utf-8")

    # 原地覆盖前自动备份
    if out == src and not os.path.exists(src + ".bak"):
        shutil.copy2(src, src + ".bak")

    tmp = out + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zo:
        for n in names:
            zo.writestr(n, data[n])
    os.replace(tmp, out)
    print(f"[OK] 分页符已插入: {out}（段落数 {para_after} 不变，三重自检全部通过）")


if __name__ == "__main__":
    main()

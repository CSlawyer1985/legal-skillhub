#!/usr/bin/env python3
"""将 modify-plan.json 应用到 DOCX，生成含修订痕迹 + 页码的修订版。

复用 contract-copilot 的 docx 修订模块（scripts/docx/reviewer.ContractReviewer）。
修订作者署名取自 config/reviewer_profile.json。

action 字段对应杨司和《合同审查与修改实务》"增删改调"：
  delete=删, insert=增, replace=改, comment=调（落批注，不直接改文）。
view/quality_dim/module 等字段仅用于复核追溯，不影响修订落点。

用法：
    python3 apply_modify_plan.py --input <原合同.docx> --plan <modify-plan.json> \
        --output <修订版.docx> [--unpacked <解包临时目录>]
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

# 让脚本能 import 同目录下的 docx 模块
SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from docx.reviewer import ContractReviewer  # noqa: E402
from docx.pack import pack_document  # noqa: E402


def load_reviewer_profile() -> dict:
    """读取署名配置，但署名固定为 WPS / WP，不得改为其他名称。

    用户（龚家勇律师）强制要求：批注人、修订人的署名必须统一为 "WPS"，
    禁止使用任何其他名称（如真实审阅人姓名、Claude、合同审查助手等）。
    因此无论 config/reviewer_profile.json 内容如何，本函数始终返回 WPS/WP，
    仅从配置读取时做一致性校验与提示，不采用配置中的其他名称。
    """
    p = SKILL_ROOT / "config" / "reviewer_profile.json"
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            cfg_author = data.get("author", "WPS")
            cfg_initials = data.get("initials", "WP")
            if cfg_author != "WPS" or cfg_initials != "WP":
                # 配置中的署名非 WPS，按强制规则覆盖并提示
                print(
                    "[署名锁定] 检测到 config/reviewer_profile.json 署名非 WPS，"
                    "已按强制规则统一覆盖为 WPS / WP。"
                )
        except Exception:
            pass
    # 强制锁定：署名只允许为 WPS / WP
    return {"author": "WPS", "initials": "WP"}


def unpack_docx(input_docx: Path, unpacked_dir: Path) -> None:
    """解包 DOCX 为目录结构，保留原始 XML（不做美化，避免实体编码破坏中文）。"""
    import zipfile

    unpacked_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(input_docx) as zf:
        zf.extractall(unpacked_dir)


def inject_page_numbers(unpacked_dir: Path) -> None:
    """向文档注入页脚页码（PAGE 字段，居中）。

    通过修改 word/document.xml 的 w:sectPr，引用一个带 PAGE 字段的页脚，
    并新建 word/footer1.xml + 更新 [Content_Types].xml 与 document.xml.rels。
    """
    import defusedxml.ElementTree as ET
    import re

    document_xml = unpacked_dir / "word" / "document.xml"
    if not document_xml.exists():
        return
    text = document_xml.read_text(encoding="utf-8")
    if "w:sectPr" not in text:
        return

    # 在每个 w:sectPr 末尾加上 <w:footerReference w:type="default" r:id="rIdFooter1"/>
    # 注意：这里仅处理主 sectPr（最后一个），简化实现
    sectpr_close = "</w:sectPr>"
    footer_ref = '<w:footerReference w:type="default" r:id="rIdFooter1"/>'
    if footer_ref in text:
        return  # 已有页码，跳过

    idx = text.rfind(sectpr_close)
    if idx < 0:
        return
    # 在 </w:sectPr> 前插入 footerReference（位于 sectPr 内、最后一子元素前）
    insert_at = text.rfind(">", 0, idx) + 1
    new_text = text[:insert_at] + footer_ref + text[insert_at:]
    document_xml.write_text(new_text, encoding="utf-8")

    # 创建 footer1.xml
    footer_xml = unpacked_dir / "word" / "footer1.xml"
    footer_content = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
        '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
        '<w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>'
        '<w:r><w:fldChar w:fldCharType="end"/></w:r>'
        '</w:p></w:ftr>'
    )
    footer_xml.write_text(footer_content, encoding="utf-8")

    # 更新 document.xml.rels
    rels_xml = unpacked_dir / "word" / "_rels" / "document.xml.rels"
    if rels_xml.exists():
        rels = rels_xml.read_text(encoding="utf-8")
        if "rIdFooter1" not in rels:
            rels = rels.replace(
                "</Relationships>",
                '<Relationship Id="rIdFooter1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/></Relationships>',
            )
            rels_xml.write_text(rels, encoding="utf-8")

    # 更新 [Content_Types].xml
    ct_xml = unpacked_dir / "[Content_Types].xml"
    if ct_xml.exists():
        ct = ct_xml.read_text(encoding="utf-8")
        if "footer1.xml" not in ct:
            ct = ct.replace(
                "</Types>",
                '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/></Types>',
            )
            ct_xml.write_text(ct, encoding="utf-8")


def build_paragraph_index(reviewer: ContractReviewer):
    """构建段落文本 → 节点对象 的预索引（一次遍历，后续定位不再全文档扫描）。

    返回 list[(text, node)]，按文档顺序排列。仅用于加速 find_text 定位，
    不修改任何文档内容，不影响修订落点语义。
    """
    index = []
    for para in reviewer.get_paragraphs():
        text = reviewer._get_document_text(para)
        index.append((text, para))
    return index


def locate_node(reviewer: ContractReviewer, index, needle, start=0):
    """在段落预索引中从 start 位置向后查找包含 needle 的段落节点。

    采用"就近顺序定位"：优先匹配 start 之后最近的一段，避免重复扫描全文，
    且保证多条 finding 按文档顺序依次落点（与原 find_text 语义一致）。
    找不到时回退到全文查找，保证与原行为兼容。
    """
    if needle:
        for i in range(start, len(index)):
            if needle in index[i][0]:
                return index[i][1], i
    # 回退：全文任意位置（兼容锚文本跨段落或特殊情形）
    try:
        return reviewer.find_text(needle), start
    except Exception:
        return None, start


def apply_finding(reviewer: ContractReviewer, finding: dict, index=None, cursor=0):
    """将单条 finding 应用到文档，返回 (状态, 新游标)。

    index/cursor 为可选加速参数：传入后按"就近顺序定位"避免每条 finding 全文档扫描。
    不传 index 时退化为原 find_text 行为，保持向后兼容。
    """
    action = finding.get("action", "comment")
    anchor = finding.get("anchor_text", "")
    current = finding.get("current_text", "")
    proposed = finding.get("proposed_text", "")
    reason = finding.get("reason", "")

    try:
        if action == "delete":
            if index is not None:
                node, cursor = locate_node(reviewer, index, anchor or current, cursor)
                if node is None:
                    return f"failed: 未定位到删除目标", cursor
            else:
                node = reviewer.find_text(anchor or current)
            reviewer.suggest_deletion(node)
            return "applied", cursor
        if action == "insert":
            if anchor and index is not None:
                node, cursor = locate_node(reviewer, index, anchor, cursor)
                if node is None:
                    node = reviewer.doc["word/document.xml"].get_node(tag="w:body")
            elif anchor:
                node = reviewer.find_text(anchor)
            else:
                node = reviewer.doc["word/document.xml"].get_node(tag="w:body")
            reviewer.insert_text_after(node, proposed, as_paragraph=True)
            return "applied", cursor
        if action == "replace":
            # replace_text_via_paragraph 内部自带段落定位，无需索引加速；
            # 但传入 current 即原文，语义与原行为完全一致。
            reviewer.replace_text_via_paragraph(current, proposed, comment_text=reason or None)
            return "applied", cursor
        # 默认 comment
        if index is not None:
            node, cursor = locate_node(reviewer, index, anchor or current, cursor)
            if node is None:
                return f"failed: 未定位到批注目标", cursor
        else:
            node = reviewer.find_text(anchor or current)
        reviewer.add_comment(node, (reason + " | 建议：" + proposed) if proposed else reason)
        return "applied", cursor
    except Exception as e:  # noqa: BLE001
        return f"failed: {e}", cursor


def main() -> None:
    parser = argparse.ArgumentParser(description="应用合同修改计划，生成修订痕迹版")
    parser.add_argument("--input", required=True, help="原合同 DOCX 路径")
    parser.add_argument("--plan", required=True, help="modify-plan.json 路径")
    parser.add_argument("--output", required=True, help="输出修订版 DOCX 路径")
    parser.add_argument("--unpacked", default=None, help="解包临时目录（可选）")
    args = parser.parse_args()

    input_docx = Path(args.input)
    plan_path = Path(args.plan)
    output_docx = Path(args.output)

    profile = load_reviewer_profile()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    findings = plan.get("findings", [])

    tmp_dir = Path(args.unpacked) if args.unpacked else Path(tempfile.mkdtemp(prefix="cmod_"))
    unpacked_dir = tmp_dir / "unpacked"
    unpack_docx(input_docx, unpacked_dir)

    reviewer = ContractReviewer(unpacked_dir, author=profile["author"], initials=profile["initials"])

    # 构建段落预索引（一次遍历），加速后续定位，避免每条 finding 全文档扫描
    paragraph_index = build_paragraph_index(reviewer)
    cursor = 0

    results = []
    for f in findings:
        status, cursor = apply_finding(reviewer, f, index=paragraph_index, cursor=cursor)
        results.append({"id": f.get("id"), "action": f.get("action"), "status": status})
        print(f"[{f.get('id')}] {f.get('action')} -> {status}")

    # 先将修订落盘（内存 DOM -> 磁盘 XML）
    reviewer.save(validate=False)

    # 注入页码（直接改磁盘 XML，须在 save 之后）
    inject_page_numbers(unpacked_dir)

    # 打包
    ok = pack_document(unpacked_dir, output_docx, validate=True)
    if not ok:
        print("ERROR: 打包校验失败", file=sys.stderr)
        sys.exit(1)

    applied = sum(1 for r in results if r["status"] == "applied")
    print(f"\n完成：{applied}/{len(results)} 条已应用")
    print(f"修订版已生成：{output_docx}")

    # 清理临时目录（除非用户指定）
    if not args.unpacked and tmp_dir.exists():
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
extract_case.py — 变量核对清单生成（阶段2 步骤①→②）

职责边界（教学点）:
  - 语义抽取（人名/金额/案由识别）由 AI 在对话中完成；
  - 本脚本负责机械化部分：加载材料包 manifest 的变量字典 →
    合并 AI 抽取结果 → 输出「一次确认表」（已确认/待补/低置信度需复核）。

用法:
  # 1. 输出材料包所需全部变量的空白核对表
  python extract_case.py --manifest demo-manifest.json

  # 2. 注入 AI 抽取的事实（JSON），输出一次确认表
  python extract_case.py --manifest demo-manifest.json --facts facts.json

  # facts.json 格式:
  # [
  #   {"key": "{{委托人姓名}}", "value": "张伟", "confidence": 0.95, "source": "笔录"},
  #   {"key": "{{案由}}", "value": "民间借贷纠纷", "confidence": 0.6, "source": "录音@00:12:33"}
  # ]

置信度规则:
  >= 0.9  直接采信
  0.6~0.9 采信但标记（建议扫一眼）
  < 0.6   列入"需人工复核"，不进确认表正文
"""
import sys
import json
import re
import zipfile
import argparse
from pathlib import Path


def expand_doc_vars(manifest_path, manifest):
    """扫描 manifest 引用的母版 DOCX，收集实际出现的 {{变量}} 全集。"""
    base = Path(manifest_path).parent
    found = {}
    for doc in manifest.get("docs", []):
        rel = doc.get("file") or doc.get("path")
        if not rel or doc.get("no_master"):
            continue
        p = base / rel
        if not p.exists():
            continue
        with zipfile.ZipFile(p) as z:
            xml = z.read("word/document.xml").decode("utf-8")
        for v in set(re.findall(r"\{\{[^}]+\}\}", xml)):
            found.setdefault(v, []).append(doc.get("name", rel))
    return found


def load_variables(manifest_path):
    """从 manifest 提取变量字典，并用母版实际变量展开占位族（如 {{勾选_*}}）。"""
    with open(manifest_path, encoding="utf-8") as f:
        m = json.load(f)

    doc_vars = expand_doc_vars(manifest_path, m)

    variables = []
    vd = m.get("variable_dictionary") or m.get("variables") or {}
    groups = vd.items() if isinstance(vd, dict) else [("未分组", vd)]
    for group, items in groups:
        for it in items:
            it = {"name": it} if isinstance(it, str) else dict(it)
            it.setdefault("group", group)
            name = it["name"]
            if "*" in name or "/" in name:
                # 占位族：展开为母版中实际变量；/ 连接的说明性名称跳过（母版里是独立变量）
                if "*" in name:
                    prefix = name.split("*")[0]
                    for actual in sorted(v for v in doc_vars if v.startswith(prefix)):
                        e = dict(it)
                        e["name"] = actual
                        e["expanded_from"] = name
                        variables.append(e)
                continue
            variables.append(it)

    # 兜底：母版里出现但字典未列的变量补进来
    # 若字典中存在同前缀的 "/" 说明性条目（如 {{签订年份/月份/日期}}），继承其 required
    listed = {v["name"] for v in variables}
    slash_entries = []
    for group, items in (vd.items() if isinstance(vd, dict) else []):
        for it in items:
            nm = it if isinstance(it, str) else it.get("name", "")
            if "/" in nm:
                slash_entries.append(it if isinstance(it, dict) else {"name": nm})
    for actual, used_in in sorted(doc_vars.items()):
        if actual not in listed:
            required = True
            stem = actual.strip("{}")
            for se in slash_entries:
                parts = se["name"].strip("{}").split("/")
                # 例: "签订年份/月份/日期" → 前缀"签订"匹配 "签订月份"
                if parts and stem.startswith(parts[0][:-2]) is False:
                    pass
                if any(stem == parts[0] or (stem.startswith(parts[0][:2]) and p in stem) for p in parts):
                    required = se.get("required", True)
                    break
            variables.append({
                "name": actual, "group": "（字典未列）", "required": required,
                "note": f"出现于: {', '.join(used_in)}",
            })
    return variables


def render_checklist(variables, facts):
    """输出一次确认表（Markdown）。"""
    fact_map = {f["key"]: f for f in facts}

    confirmed, review, missing = [], [], []
    for v in variables:
        name = v["name"]
        f = fact_map.get(name)
        if not f or not f.get("value"):
            missing.append(v)
        elif f.get("confidence", 1) < 0.6:
            review.append((v, f))
        else:
            confirmed.append((v, f))

    lines = ["# 委托材料变量 · 一次确认表", ""]
    lines.append("请核对以下信息，**回复「确认」或指出需要修改的项**，整套材料一次生成。")
    lines.append("")

    if confirmed:
        lines.append("## ✅ 已识别信息（请核对）")
        lines.append("")
        lines.append("| 项目 | 值 | 来源 |")
        lines.append("|------|-----|------|")
        for v, f in confirmed:
            flag = " ⚠️低置信" if f.get("confidence", 1) < 0.9 else ""
            lines.append(f"| {v['name'].strip('{}')} | {f['value']}{flag} | {f.get('source','—')} |")
        lines.append("")

    if review:
        lines.append("## 🔍 需人工复核（置信度低，未采信）")
        lines.append("")
        for v, f in review:
            lines.append(f"- **{v['name'].strip('{}')}**：识别为「{f['value']}」（置信度 {f['confidence']}，来源 {f.get('source','—')}）——请确认或更正")
        lines.append("")

    if missing:
        lines.append("## ❓ 待补充信息")
        lines.append("")
        for v in missing:
            req = "（必填）" if v.get("required", True) else "（可留空）"
            lines.append(f"- {v['name'].strip('{}')}{req}")
        lines.append("")

    lines.append("---")
    lines.append(f"共 {len(variables)} 项变量：已识别 {len(confirmed)}，待复核 {len(review)}，待补充 {len(missing)}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="变量核对清单生成")
    ap.add_argument("--manifest", required=True, help="材料包 manifest.json")
    ap.add_argument("--facts", default=None, help="AI 抽取的事实 JSON（可选）")
    ap.add_argument("--out", default=None, help="输出到文件（默认打印）")
    args = ap.parse_args()

    variables = load_variables(args.manifest)
    facts = []
    if args.facts:
        with open(args.facts, encoding="utf-8") as f:
            facts = json.load(f)

    report = render_checklist(variables, facts)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"[OK] 确认表 -> {args.out}")
    else:
        print(report)


if __name__ == "__main__":
    main()

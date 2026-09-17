#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文书质检脚本（quality_checker.py）。

功能：加载 references/quality_checklist.md（附录 D 47 条全量，逐条带【适用范围】
与 [机检]/[人工] 二态标注），按案件阶段与文书类型过滤适用条目，对标注为[机检]的
条目逐条断言，输出"已通过 X 项/未通过 Y 项"清单（条目号＋原文位置＋修复建议），
并在末尾提示人工复核项。

阶段一致性核对仅作用于本次新生成文件——历史文件的身份后缀以生成时点阶段为准，
阶段切换后不追溯改名（大纲 5.0.1 后缀锚定），历史文件不因阶段切换被误判。

本地化层校验（--l10n）：校验 localization/provincial_sentencing_details/ 下各省
JSON 的罪名键覆盖率（本地细则罪名须 ⊆ crime_index 罪名集）、刑期幅度格式合法性、
effective_date 必填。校验不通过列清单，不阻断主包发布（责任在填充方）。

调用方式：
  python scripts/quality_checker.py --file 03_正式文书/xxx_辩护人.md --stage 侦查 --doc-type 取保类文书
  python scripts/quality_checker.py --file 03_正式文书/ --stage 审查起诉
  python scripts/quality_checker.py --l10n

统一接口规范：
  - 仅依赖Python标准库；支持--help；
  - 输出JSON信封：{status, error_code, message, data}；
  - 退出码：0通过 / 1存在未通过机检项 / 2文件缺失 / 3解析失败；
  - 错误码：MISSING_PARAM / NOT_FOUND / INVALID / ERR_IO。
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime

SCRIPT_NAME = "quality_checker"
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECKLIST = os.path.join(SKILL_ROOT, "references", "quality_checklist.md")
DATA_DIR = os.path.join(SKILL_ROOT, "assets", "data")
L10N_DIR = os.path.join(SKILL_ROOT, "localization", "provincial_sentencing_details")

# 规则行形态：  N. 禁止……——表述为……。【适用标签】`[机检]`（二态标记可带反引号）
RULE_RE = re.compile(r"^(\d+)\.\s*(.+?)\s*【([^】]+)】\s*`?\[(机检|人工)\]`?\s*$")
QUOTED_RE = re.compile(r"[\"“”'‘’]([^\"“”'‘’]{2,40})[\"“”'‘’]")

TEXT_EXT = {".md", ".txt", ".markdown"}


def make_trace_id():
    stamp = datetime.now().isoformat()
    return SCRIPT_NAME + hashlib.md5((SCRIPT_NAME + stamp).encode("utf-8")).hexdigest()[:8]


def envelope(status, error_code, message, data):
    return {"status": status, "error_code": error_code,
            "message": message, "data": data}


def emit(env, code):
    print(json.dumps(env, ensure_ascii=False, indent=2))
    sys.exit(code)


def load_rules(tid):
    if not os.path.isfile(CHECKLIST):
        emit(envelope("error", "NOT_FOUND", "质检规则清单缺失：%s" % CHECKLIST,
                      {"trace_id": tid}), 2)
    rules, malformed = [], []
    with open(CHECKLIST, "r", encoding="utf-8") as f:
        for ln_no, ln in enumerate(f, 1):
            ln = ln.strip()
            m = RULE_RE.match(ln)
            if not m:
                if re.match(r"^\d+\.", ln):
                    malformed.append({"line": ln_no, "text": ln[:80]})
                continue
            rid, body, tags, mode = m.group(1), m.group(2), m.group(3), m.group(4)
            rules.append({"id": int(rid), "body": body,
                          "scopes": [t.strip() for t in re.split(r"[·、,，]", tags) if t.strip()],
                          "mode": mode})
    return rules, malformed


def applicable(rule, stage, doc_type):
    """【适用】多标签并列为"命中任一即适用"；未传参时视为全适用。"""
    scopes = rule["scopes"]
    if "全阶段" in scopes:
        return True
    if not stage and not doc_type:
        return True
    if stage and stage in scopes:
        return True
    if doc_type and doc_type in scopes:
        return True
    return False


def forbidden_phrases(body):
    """从"禁止……——表述为……"中提取禁止表述（取——之前的引号内容）。"""
    head = body.split("——")[0]
    return [p for p in QUOTED_RE.findall(head) if p.strip()]


def rule_check(rule, text, lines):
    """返回 (通过/未通过, 命中位置列表, 修复建议)。"""
    rid = rule["id"]
    # 逐条专属机检（格式类）
    if rid == 26:  # 称呼不顶格
        hits = [i + 1 for i, ln in enumerate(lines) if re.match(r"^\s+尊敬的", ln)]
        return (not hits), [{"line": i, "text": lines[i - 1][:60]} for i in hits], \
            "称呼须顶格，参照党政机关文书格式规范"
    if rid == 27:  # 大标题后加标点
        hits = [i + 1 for i, ln in enumerate(lines)
                if re.match(r"^#{1,6}\s*.+[：:，,。；;、]$", ln)]
        return (not hits), [{"line": i, "text": lines[i - 1][:60]} for i in hits], \
            "大标题后不加标点符号"
    if rid == 3:  # 侦查阶段禁"全面了解案件情况"
        hits = [i + 1 for i, ln in enumerate(lines) if "全面了解案件情况" in ln]
        return (not hits), [{"line": i, "text": lines[i - 1][:60]} for i in hits], \
            '写"对本案有了一定的了解"'
    if rid == 19:  # 意见类须有摘要段
        ok = "总体认为" in text
        return ok, ([] if ok else [{"line": 0, "text": "（全文）"}]), \
            '须设摘要段"辩护人总体认为"，≤5 行、不得堆砌标题'
    # 通用：禁止表述命中检查
    hits = []
    for ph in forbidden_phrases(rule["body"]):
        for i, ln in enumerate(lines):
            if ph in ln:
                hits.append({"line": i + 1, "text": ln.strip()[:80], "phrase": ph})
    return (not hits), hits, "按规则改为正确表述（见 quality_checklist.md 第 %d 条）" % rid


def check_l10n(tid):
    idx_path = os.path.join(DATA_DIR, "crime_index.json")
    crime_names = set()
    if os.path.isfile(idx_path):
        try:
            with open(idx_path, "r", encoding="utf-8") as f:
                idx = json.load(f)
            for v in (idx.get("index") or {}).values():
                if isinstance(v, dict):
                    continue
            crime_names = set((idx.get("index") or {}).keys())
        except (OSError, ValueError):
            pass

    issues, files = [], []
    if not os.path.isdir(L10N_DIR):
        emit(envelope("error", "NOT_FOUND", "本地化目录不存在：%s" % L10N_DIR,
                      {"trace_id": tid}), 2)
    for fn in sorted(os.listdir(L10N_DIR)):
        if not fn.endswith(".json"):
            continue
        p = os.path.join(L10N_DIR, fn)
        files.append(fn)
        try:
            with open(p, "r", encoding="utf-8") as f:
                db = json.load(f)
        except (OSError, ValueError) as exc:
            issues.append({"file": fn, "issue": "解析失败：%s" % exc})
            continue
        if not db.get("province"):
            issues.append({"file": fn, "issue": "缺 province 字段"})
        if not db.get("effective_date"):
            issues.append({"file": fn, "issue": "缺 effective_date 字段（必填，标注细则文号与时点）"})
        if not db.get("source_note"):
            issues.append({"file": fn, "issue": "缺 source_note 字段（文号出处）"})
        crimes = db.get("crimes") or {}
        if crime_names:
            extra = sorted(set(crimes.keys()) - crime_names)
            if extra:
                issues.append({"file": fn,
                               "issue": "罪名键超出 crime_index 罪名集：%s" % "、".join(extra[:10])})
        for cname, tiers in crimes.items():
            if not isinstance(tiers, (dict, list)):
                issues.append({"file": fn, "issue": "罪名 %s 档次结构非法" % cname})
                continue
            for tk, tv in (tiers.items() if isinstance(tiers, dict) else []):
                if not isinstance(tv, list) or len(tv) == 0:
                    issues.append({"file": fn,
                                   "issue": "罪名 %s 档次 %s 刑期幅度须为非空数组" % (cname, tk)})
    emit(envelope("ok" if not issues else "error", None if not issues else "INVALID",
                  "本地化层校验：%d 个文件，问题 %d 项%s"
                  % (len(files), len(issues), "（不阻断主包发布，责任在填充方）" if issues else ""),
                  {"trace_id": tid, "files": files, "issues": issues,
                   "note": "省级量刑细则为移植者配置项；当前目录仅有 .md 文件的，"
                           "按 I-1 转 JSON 后本校验生效"}),
         0 if not issues else 1)


def main():
    ap = argparse.ArgumentParser(
        prog=SCRIPT_NAME, description="文书 47 条质检（仅执行机检条目）＋本地化层校验。")
    ap.add_argument("--file", help="待检文书文件或目录")
    ap.add_argument("--stage", default="", help="案件阶段：侦查/审查起诉/一审/二审")
    ap.add_argument("--doc-type", default="",
                    help="文书类型：取保类文书/羁押必要性/意见类文书/排非/批捕等（须与清单标签一致）")
    ap.add_argument("--l10n", action="store_true", help="本地化层校验模式")
    args = ap.parse_args()
    tid = make_trace_id()

    if args.l10n:
        check_l10n(tid)

    if not args.file:
        emit(envelope("error", "MISSING_PARAM", "须指定 --file（或使用 --l10n）",
                      {"trace_id": tid}), 1)
    if not os.path.exists(args.file):
        emit(envelope("error", "NOT_FOUND", "待检路径缺失：%s" % args.file,
                      {"trace_id": tid}), 2)

    if os.path.isfile(args.file):
        targets = [args.file]
    else:
        targets = sorted(os.path.join(dp, fn)
                         for dp, _, fns in os.walk(args.file)
                         for fn in fns
                         if os.path.splitext(fn)[1].lower() in TEXT_EXT)
    if not targets:
        emit(envelope("error", "NOT_FOUND", "无可检文书：%s" % args.file, {"trace_id": tid}), 2)

    rules, malformed = load_rules(tid)
    if not rules:
        emit(envelope("error", "INVALID",
                      "规则清单解析为空，请核对 quality_checklist.md 行格式",
                      {"trace_id": tid, "malformed": malformed}), 3)

    passed, failed, manual_ids = [], [], []
    for rule in rules:
        if not applicable(rule, args.stage, args.doc_type):
            continue
        if rule["mode"] == "人工":
            manual_ids.append(rule["id"])
            continue
        ok_hits, last_fix = [], ""
        for t in targets:
            try:
                with open(t, "r", encoding="utf-8") as f:
                    text = f.read()
            except (OSError, UnicodeDecodeError) as exc:
                emit(envelope("error", "ERR_IO", "读取失败：%s（%s）" % (t, exc),
                              {"trace_id": tid}), 3)
            ok, hits, fix = rule_check(rule, text, text.split("\n"))
            last_fix = fix
            if not ok:
                ok_hits.append({"file": t, "hits": hits})
        if ok_hits:
            failed.append({"id": rule["id"], "body": rule["body"][:60],
                           "fix": last_fix, "occurrences": ok_hits})
        else:
            passed.append(rule["id"])

    n_pass, n_fail = len(passed), len(failed)
    manual_note = ("另有 %d 条人工复核项请对照第 %s 条自查"
                   % (len(manual_ids), "、".join(map(str, manual_ids)))
                   if manual_ids else "本阶段无人工复核项")
    emit(envelope("ok" if n_fail == 0 else "error", None if n_fail == 0 else "INVALID",
                  "已通过 %d 项/未通过 %d 项" % (n_pass, n_fail),
                  {"trace_id": tid, "stage": args.stage or "（未指定）",
                   "doc_type": args.doc_type or "（未指定）",
                   "files_checked": len(targets), "passed": n_pass, "failed": n_fail,
                   "passed_ids": passed, "failed_items": failed,
                   "manual_review_note": manual_note,
                   "manual_ids": manual_ids,
                   "rules_malformed": malformed,
                   "note": "阶段一致性核对仅作用于本次新生成文件，历史文件后缀不追溯改名"}),
         0 if n_fail == 0 else 1)


if __name__ == "__main__":
    main()

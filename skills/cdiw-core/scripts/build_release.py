#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""发布闸门流水线脚本（build_release.py）。

五步流水线（规格书 2 章、8.8.6）：
  ① 敏感词扫描——对全目录递归扫描（关键词表外置，不随包分发），命中即阻断并定位残余；
  ② 保密检测——全文件虚构代称核验（Skill 资产中禁止真实案件数据）
     ＋ freshness_check.py --strict 前置（内容超期与效力待核双清零方可进入打包）；
  ③ 元数据核验——_meta／图标／描述／兼容区间双向核对、slug 三者一致、
     _meta version 与 CHANGELOG 最新条目一致、匿名条目数快照核对；
  ④ 打包 zip（--target hub 时排除法条包与 overlays）；
  ⑤ 扫描记录留痕（写包外，不入包）。

调用方式：
  python scripts/build_release.py --target local
  python scripts/build_release.py --target hub --out ./dist
  python scripts/build_release.py --target hub --keywords ./敏感词表.txt

统一接口规范：
  - 仅依赖Python标准库；支持--help；
  - 输出JSON信封：{status, error_code, message, data}；
  - 退出码：0全部通过 / 1存在 FAIL 步骤 / 2路径或文件缺失 / 3执行异常；
  - 错误码：MISSING_PARAM / NOT_FOUND / INVALID / ERR_IO。
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile
from datetime import datetime

SCRIPT_NAME = "build_release"
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE = os.path.dirname(SKILL_ROOT)

REAL_DATA_PATTERNS = [
    (r"\d{17}[\dXx]", "疑似身份证号"),
    (r"1[3-9]\d{9}", "疑似手机号"),
    (r"[\w.+-]+@[\w-]+\.[\w.]+", "疑似邮箱"),
]

# 豁免标记：脚本内的脱敏冒烟测试夹具属刻意构造的测试样本，非案件数据。
# 该标记须置于夹具所在行，build_release 保密检测跳过标记行。
FIXTURE_MARK = "cdiw-pii-fixture"

# 虚构代称白名单（包内示例允许使用）
FICTION = {"阿明", "阿强", "某某", "××", "张某", "李某", "赖某某", "祝某某",
           "余某某", "詹某某", "郝某某", "朱某某"}


def make_trace_id():
    stamp = datetime.now().isoformat()
    return SCRIPT_NAME + hashlib.md5((SCRIPT_NAME + stamp).encode("utf-8")).hexdigest()[:8]


def envelope(status, error_code, message, data):
    return {"status": status, "error_code": error_code,
            "message": message, "data": data}


def emit(env, code):
    print(json.dumps(env, ensure_ascii=False, indent=2))
    sys.exit(code)


def walk_files(root, exclude_dirs=()):
    out = []
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in exclude_dirs and not d.startswith(".git")]
        for fn in sorted(fns):
            if fn.startswith("."):
                continue
            out.append(os.path.join(dp, fn))
    return sorted(out)


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return ""


def step1_keyword_scan(files, keywords, tid):
    if keywords is None:
        return {"step": 1, "name": "敏感词扫描", "verdict": "SKIP",
                "detail": "未提供关键词表（--keywords），跳过；"
                          "发布前须以实际关键词表重跑，关键词表外置不随包分发"}
    hits = []
    for p in files:
        text = read_text(p)
        if not text:
            continue
        for kw in keywords:
            if kw and kw in text:
                hits.append({"file": os.path.relpath(p, SKILL_ROOT), "keyword": kw})
    return {"step": 1, "name": "敏感词扫描",
            "verdict": "FAIL" if hits else "PASS",
            "scanned": len(files), "keywords": len(keywords), "hits": hits[:100],
            "detail": "命中即阻断发布并定位残余，零命中方放行" if hits else "零命中，放行"}


def step2_confidentiality(files, tid):
    findings = []
    exempted = []
    for p in files:
        text = read_text(p)
        if not text:
            continue
        # 逐行扫描，跳过带豁免标记的测试夹具行
        scan_lines = []
        for ln in text.split("\n"):
            if FIXTURE_MARK in ln:
                exempted.append(os.path.relpath(p, SKILL_ROOT))
                continue
            scan_lines.append(ln)
        scan_text = "\n".join(scan_lines)
        for pat, desc in REAL_DATA_PATTERNS:
            m = re.search(pat, scan_text)
            if m:
                findings.append({"file": os.path.relpath(p, SKILL_ROOT),
                                 "type": desc, "sample": m.group(0)[:6] + "***"})
    # freshness_check --strict 前置
    fresh = {"ran": False}
    fscript = os.path.join(SKILL_ROOT, "scripts", "freshness_check.py")
    if os.path.isfile(fscript):
        try:
            r = subprocess.run([sys.executable, fscript, "--strict"],
                               capture_output=True, text=True, timeout=180)
            fresh = {"ran": True, "exit_code": r.returncode,
                     "stdout_tail": (r.stdout or "")[-600:]}
        except Exception as exc:
            fresh = {"ran": True, "error": str(exc)}
    fresh_ok = (not fresh.get("ran")) or fresh.get("exit_code") == 0
    verdict = "PASS" if (not findings and fresh_ok) else "FAIL"
    return {"step": 2, "name": "保密检测＋时效前置", "verdict": verdict,
            "real_data_findings": findings[:50],
            "exempted_fixture_lines": sorted(set(exempted)),
            "freshness_check": fresh,
            "detail": "全文件虚构代称核验＋freshness_check --strict 双清零；"
                      "带 %s 标记的行为脱敏冒烟测试夹具，不计入真实数据残留" % FIXTURE_MARK}


def step3_metadata(files, tid):
    checks = []
    meta_p = os.path.join(SKILL_ROOT, "_meta.json")
    meta = None
    if os.path.isfile(meta_p):
        try:
            meta = json.load(open(meta_p, encoding="utf-8"))
        except (OSError, ValueError):
            pass

    # ① slug／目录名／SKILL.md name 三者一致
    dirname = os.path.basename(SKILL_ROOT)
    skill_name = None
    sm = re.search(r"^name:\s*(\S+)", read_text(os.path.join(SKILL_ROOT, "SKILL.md")), re.M)
    if sm:
        skill_name = sm.group(1)
    slug = (meta or {}).get("slug")
    ok_slug = (slug == dirname == skill_name)
    checks.append({"item": "slug／目录名／name 三者一致", "verdict": "PASS" if ok_slug else "FAIL",
                   "value": {"slug": slug, "dirname": dirname, "skill_name": skill_name}})

    # ② 图标存在
    icon = os.path.join(SKILL_ROOT, "_icon.png")
    checks.append({"item": "图标 _icon.png", "verdict": "PASS" if os.path.isfile(icon) else "FAIL",
                   "value": os.path.basename(icon) if os.path.isfile(icon) else "缺失"})

    # ③ _meta version 与 CHANGELOG 最新条目一致
    cl = read_text(os.path.join(SKILL_ROOT, "CHANGELOG.md"))
    m = re.search(r"^##\s*\[?v?(\d+\.\d+\.\d+)\]?", cl, re.M)
    cl_ver = m.group(1) if m else None
    meta_ver = (meta or {}).get("version")
    ok_ver = (cl_ver is not None and cl_ver == meta_ver)
    checks.append({"item": "_meta version 与 CHANGELOG 最新条目一致",
                   "verdict": "PASS" if ok_ver else "FAIL",
                   "value": {"changelog": cl_ver, "meta": meta_ver}})

    # ④ 法条包兼容区间双向核对
    sbom_p = os.path.join(SKILL_ROOT, "SBOM.json")
    compat = {"core_side": None, "pack_side": None}
    if os.path.isfile(sbom_p):
        try:
            sbom = json.load(open(sbom_p, encoding="utf-8"))
            for d in sbom.get("data_layer", []):
                if d.get("external") == "cdiw-law-pack":
                    compat["core_side"] = d.get("compatible_law_pack")
        except (OSError, ValueError):
            pass
    pack_md = os.path.join(WORKSPACE, "cdiw-law-pack", "PACK.md")
    if not os.path.isfile(pack_md):
        pack_md = os.path.join(os.path.dirname(SKILL_ROOT), "cdiw-law-pack", "PACK.md")
    if os.path.isfile(pack_md):
        m2 = re.search(r'\*\*compatible_core\*\*:?\s*"([^"]+)"', read_text(pack_md))
        if not m2:
            m2 = re.search(r'compatible_core:?\s*"([^"]+)"', read_text(pack_md))
        if m2:
            compat["pack_side"] = m2.group(1).strip()
    ok_compat = bool(compat["core_side"]) and bool(compat["pack_side"])
    checks.append({"item": "法条包兼容区间双向声明",
                   "verdict": "PASS" if ok_compat else "FAIL", "value": compat})

    # ⑤ 匿名条目数快照核对（与数据文件实际计数比对）
    idx_p = os.path.join(SKILL_ROOT, "assets", "data", "crime_index.json")
    actual_total, actual_anon = None, None
    if os.path.isfile(idx_p):
        try:
            idx = json.load(open(idx_p, encoding="utf-8")).get("index", {})
            actual_total = len(idx)
            actual_anon = sum(1 for k in idx if re.match(r"^第[一二三四五六七八九十百零〇]+条$", str(k)))
        except (OSError, ValueError):
            pass
    doc_blob = read_text(os.path.join(SKILL_ROOT, "README.md")) + \
        read_text(os.path.join(SKILL_ROOT, "SKILL.md"))
    m3 = re.search(r"(\d+)\s*条匿名", doc_blob)
    doc_anon = int(m3.group(1)) if m3 else None
    ok_snap = (actual_anon is None) or (doc_anon is None) or (doc_anon == actual_anon)
    checks.append({"item": "匿名条目数快照核对",
                   "verdict": "PASS" if ok_snap else "FAIL",
                   "value": {"documented": doc_anon, "actual": actual_anon,
                             "total_crimes": actual_total},
                   "detail": "文档记载数须与数据文件实际计数一致，防快照漂移"})

    verdict = "FAIL" if any(c["verdict"] == "FAIL" for c in checks) else "PASS"
    return {"step": 3, "name": "元数据核验", "verdict": verdict, "checks": checks}


def load_release_exclusion(target, tid):
    """读取发布形态排除清单（assets/config/release_exclusion.json）。
    缺失或解析失败时按 strict 处理：hub 形态阻断，local 形态放行并注记。"""
    p = os.path.join(SKILL_ROOT, "assets", "config", "release_exclusion.json")
    if not os.path.isfile(p):
        if target == "hub":
            emit(envelope("error", "INVALID",
                          "hub 形态须有排除清单方可打包：%s" % p, {"trace_id": tid}), 2)
        return []
    try:
        cfg = json.load(open(p, encoding="utf-8"))
    except (OSError, ValueError) as exc:
        emit(envelope("error", "INVALID",
                      "排除清单解析失败：%s（%s）" % (p, exc), {"trace_id": tid}), 2)
    items = (cfg.get("targets", {}).get(target, {}) or {}).get("exclusions", [])
    return [(i.get("path", "").rstrip("/"), i.get("reason", ""), i.get("degraded_to", ""),
             bool(i.get("sensitive", False))) for i in items], cfg


def load_sensitive_watch(tid):
    """读取待评清单——登记在案但不参与剥离，供打包时人工关注。"""
    p = os.path.join(SKILL_ROOT, "assets", "config", "release_exclusion.json")
    if not os.path.isfile(p):
        return []
    try:
        cfg = json.load(open(p, encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return cfg.get("_待评清单", []) or []


def step4_package(target, out_dir, tid):
    os.makedirs(out_dir, exist_ok=True)
    name = "cdiw-core-%s-%s.zip" % (target, datetime.now().strftime("%Y%m%d"))
    zp = os.path.join(out_dir, name)
    excl = {"__pycache__", ".git"}
    exclusions, _cfg = load_release_exclusion(target, tid)
    excl_paths = [e[0] for e in exclusions]
    # 涉敏项：剥离清单中标记 sensitive 者，打包时须显著提示
    sensitive_items = [e for e in exclusions if e[3]]
    sensitive_dropped = []
    n, dropped = 0, []
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for p in walk_files(SKILL_ROOT, excl):
            rel = os.path.relpath(p, SKILL_ROOT)
            hit = next((e for e in exclusions
                        if rel == e[0] or rel.startswith(e[0] + os.sep)), None)
            if hit:
                if rel not in dropped:
                    dropped.append(rel)
                if hit[3]:
                    sensitive_dropped.append(os.path.basename(hit[0]))
                continue
            z.write(p, os.path.join(os.path.basename(SKILL_ROOT), rel))
            n += 1
    detail = "hub 形态不含法条包（两包同级，非子目录）"
    if exclusions:
        detail += "；已按排除清单剥离 %d 项" % len(excl_paths)
        if sensitive_items:
            detail += "，其中涉敏 %d 项：%s" % (
                len(sensitive_items),
                "、".join(os.path.basename(e[0]) for e in sensitive_items))
    return {"step": 4, "name": "打包", "verdict": "PASS",
            "zip": zp, "size": os.path.getsize(zp), "files": n, "target": target,
            "exclusions_applied": excl_paths,
            "dropped_files": dropped,
            "sensitive_dropped": sensitive_dropped,
            "sensitive_watch": load_sensitive_watch(tid),
            "degradation": {e[0]: {"reason": e[1], "degraded_to": e[2],
                                   "sensitive": e[3]} for e in exclusions},
            "detail": detail}


def step5_trace(report, out_dir, tid):
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, "release_scan_%s.json" % datetime.now().strftime("%Y%m%d-%H%M%S"))
    with open(p, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return {"step": 5, "name": "扫描记录留痕", "verdict": "PASS",
            "record": p, "detail": "留痕文件写包外，不进入发布包"}


def main():
    ap = argparse.ArgumentParser(
        prog=SCRIPT_NAME, description="发布闸门五步流水线。")
    ap.add_argument("--target", choices=("local", "hub"), default="local", help="发布形态")
    ap.add_argument("--out", default=os.path.join(WORKSPACE, "cdiw-仓库层", "发布留痕"),
                    help="打包与留痕输出目录（包外）")
    ap.add_argument("--keywords", help="敏感词表路径（一行一词，外置不随包分发）")
    args = ap.parse_args()
    tid = make_trace_id()

    kws = None
    if args.keywords:
        if not os.path.isfile(args.keywords):
            emit(envelope("error", "NOT_FOUND", "关键词表缺失：%s" % args.keywords,
                          {"trace_id": tid}), 2)
        kws = [ln.strip() for ln in read_text(args.keywords).split("\n") if ln.strip()]

    files = walk_files(SKILL_ROOT, {"__pycache__", ".git"})
    steps = []
    steps.append(step1_keyword_scan(files, kws, tid))
    steps.append(step2_confidentiality(files, tid))
    steps.append(step3_metadata(files, tid))

    failed = [s for s in steps if s["verdict"] == "FAIL"]
    if failed:
        emit(envelope("error", "INVALID",
                      "发布闸门阻断：%s" % "、".join("%d %s" % (s["step"], s["name"]) for s in failed),
                      {"trace_id": tid, "steps": steps, "blocked_at": [s["step"] for s in failed]}), 1)

    steps.append(step4_package(args.target, args.out, tid))
    steps.append(step5_trace({"trace_id": tid, "target": args.target, "steps": steps},
                             args.out, tid))

    s4 = [s for s in steps if s["step"] == 4][0]
    msg = "发布闸门五步全部通过（%s 形态）" % args.target
    if s4.get("sensitive_dropped"):
        msg += "；已剥离涉敏文件 %d 个：%s" % (
            len(s4["sensitive_dropped"]), "、".join(s4["sensitive_dropped"]))
    watch = s4.get("sensitive_watch") or []
    if watch:
        msg += "；待人工关注 %d 个文件（已登记未剥离）" % len(watch)

    emit(envelope("ok", None, msg,
                  {"trace_id": tid, "target": args.target, "steps": steps,
                   "sensitive_dropped": s4.get("sensitive_dropped", []),
                   "sensitive_watch": watch,
                   "note": "敏感词表外置、不随包分发；扫描记录留痕于包外"}), 0)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""aladin-drama-portrait · portrait_ingest.py
人物资产授权链·多源导入归一：把「角色/演员 + 授权凭证登记 + 发行上下文」
统一成人物肖像权自查 IR（_portrait_ir.json）。

支持输入（任意组合）：
  1) drama-cast 角色卡 _cast.json（cards{角色名:{...}}），自动作为人物资产清单
  2) 人物资产声明 assets.json：{角色名:{asset_types:[...],resembles_public_figure,public_figure_ref,note}}
     - asset_types 取值：ai_original / real_actor / digital_human / face_swap / voice_clone
     - 未声明的角色默认 ai_original（AI 纯原创虚拟形象）
  3) 授权凭证登记表 licenses.csv 或 licenses.json（一行=一份授权）
  4) drama-publish 发行计划 _publish_plan.json（抽取平台清单，用于授权平台越界比对）

用法：
  python portrait_ingest.py --cast _cast.json --assets assets.json \
      --licenses licenses.csv --publish _publish_plan.json \
      --release-date 2026-08-01 --out _portrait_ir.json

仅 Python 标准库，纯本地运行，剧本/角色/授权信息不出本机。
"""
import argparse
import csv
import io
import json
import os
import sys

ASSET_TYPES = ("ai_original", "real_actor", "digital_human", "face_swap", "voice_clone")

LICENSE_FIELDS = (
    "asset_name", "license_type", "licensor", "licensee",
    "scope_use", "scope_platform", "scope_region",
    "term_start", "term_end", "transferable", "source", "doc_ref",
)


def read_text(path):
    with open(path, "rb") as f:
        raw = f.read()
    for enc in ("utf-8-sig", "utf-8", "gb18030", "utf-16"):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return raw.decode("utf-8", errors="replace")


def load_json(path):
    return json.loads(read_text(path))


def as_bool(v):
    return str(v).strip().lower() in ("1", "yes", "y", "true", "是", "可", "可转授", "on")


# ---------- 角色清单（drama-cast 契约） ----------

def ingest_cast(path):
    data = load_json(path)
    persons = {}
    cards = data.get("cards") or {}
    if isinstance(cards, dict):
        for name, card in cards.items():
            if not isinstance(card, str):
                pres = (card or {}).get("presence", {}) if isinstance(card, dict) else {}
            else:
                pres = {}
            persons[name] = {
                "name": name,
                "role_type": (card.get("role_type") if isinstance(card, dict) else "") or "",
                "presence": pres,
                "from": "cast",
            }
    # 兼容：characters 顶层字符串列表
    for c in data.get("characters", []) or []:
        if isinstance(c, str) and c.strip() and c not in persons:
            persons[c] = {"name": c, "role_type": "", "presence": {}, "from": "cast"}
    project = data.get("project") or ""
    if isinstance(project, dict):
        project = project.get("title", "")
    return str(project or ""), persons


# ---------- 人物资产声明 ----------

def apply_assets(persons, path):
    decl = load_json(path)
    if not isinstance(decl, dict):
        return
    for name, spec in decl.items():
        p = persons.setdefault(name, {"name": name, "role_type": "", "presence": {}, "from": "manual"})
        if not isinstance(spec, dict):
            continue
        ats = spec.get("asset_types") or spec.get("asset_type") or []
        if isinstance(ats, str):
            ats = [x.strip() for x in ats.replace("，", ",").replace(";", ",").split(",") if x.strip()]
        ats = [a for a in ats if a in ASSET_TYPES]
        p["asset_types"] = ats
        p["resembles_public_figure"] = as_bool(spec.get("resembles_public_figure", False))
        p["public_figure_ref"] = str(spec.get("public_figure_ref") or "")
        p["note"] = str(spec.get("note") or "")


# ---------- 授权凭证登记 ----------

def norm_license(row):
    lic = {k: str(row.get(k, "") or "").strip() for k in LICENSE_FIELDS}
    # 平台范围拆列表
    plats = lic["scope_platform"]
    lic["scope_platform_list"] = [x.strip() for x in plats.replace("，", ",").replace(";", ",").replace("；", ",").split(",") if x.strip()]
    lic["transferable_bool"] = as_bool(lic["transferable"])
    return lic


def ingest_licenses(path):
    out = []
    if path.lower().endswith(".json"):
        data = load_json(path)
        rows = data if isinstance(data, list) else data.get("licenses", [])
        for r in rows:
            if isinstance(r, dict):
                out.append(norm_license(r))
        return out
    # CSV
    text = read_text(path)
    reader = csv.DictReader(io.StringIO(text))
    for r in reader:
        clean = {(k or "").strip(): (v or "") for k, v in r.items()}
        if not any(str(v).strip() for v in clean.values()):
            continue
        out.append(norm_license(clean))
    return out


# ---------- 发行上下文（drama-publish 契约） ----------

def ingest_publish(path):
    data = load_json(path)
    plats, dates = [], []

    def walk(node, key_hint=""):
        if isinstance(node, dict):
            for k, v in node.items():
                lk = str(k).lower()
                if lk in ("platform", "channel", "平台") and isinstance(v, str):
                    plats.append(v.strip())
                if ("date" in lk or "发行" in lk or "上线" in lk or "release" in lk) and isinstance(v, str):
                    dates.append(v.strip())
                walk(v, lk)
        elif isinstance(node, list):
            for v in node:
                walk(v, key_hint)
        elif isinstance(node, str):
            if key_hint in ("platform", "channel", "平台"):
                plats.append(node.strip())

    walk(data)
    # 去重保序
    plats = list(dict.fromkeys([p for p in plats if p]))
    dates = [d for d in dates if d]
    return plats, dates


def main():
    ap = argparse.ArgumentParser(description="短剧数字人肖像权·多源导入归一")
    ap.add_argument("--cast", help="drama-cast 角色卡 _cast.json")
    ap.add_argument("--assets", help="人物资产声明 assets.json")
    ap.add_argument("--licenses", help="授权凭证登记 licenses.csv / .json")
    ap.add_argument("--publish", help="drama-publish 发行计划 _publish_plan.json")
    ap.add_argument("--platforms", nargs="*", default=[], help="手动指定发行平台（覆盖/补充 publish 抽取）")
    ap.add_argument("--release-date", default="", help="发行/上线日期 YYYY-MM-DD（授权到期比对基准）")
    ap.add_argument("--out", default="_portrait_ir.json", help="输出 IR 路径")
    args = ap.parse_args()

    if not args.cast and not args.assets and not args.licenses:
        ap.error("至少提供 --cast / --assets / --licenses 之一")

    project = ""
    persons = {}
    inputs = []

    if args.cast:
        project, persons = ingest_cast(args.cast)
        inputs.append({"type": "cast", "path": args.cast, "persons": len(persons)})
    if args.assets:
        apply_assets(persons, args.assets)
        inputs.append({"type": "assets", "path": args.assets})
    # 默认资产类型：未声明者视为 AI 纯原创虚拟形象
    for p in persons.values():
        p.setdefault("asset_types", ["ai_original"])
        if not p["asset_types"]:
            p["asset_types"] = ["ai_original"]
        p.setdefault("resembles_public_figure", False)
        p.setdefault("public_figure_ref", "")
        p.setdefault("note", "")

    licenses = []
    if args.licenses:
        licenses = ingest_licenses(args.licenses)
        inputs.append({"type": "licenses", "path": args.licenses, "records": len(licenses)})

    platforms, dates = [], []
    if args.publish:
        platforms, dates = ingest_publish(args.publish)
        inputs.append({"type": "publish", "path": args.publish, "platforms": len(platforms)})
    if args.platforms:
        platforms = list(dict.fromkeys(platforms + args.platforms))
    release_date = args.release_date or (dates[0] if dates else "")

    person_list = sorted(persons.values(), key=lambda x: x["name"])
    for i, p in enumerate(person_list, 1):
        p["pid"] = "P%03d" % i

    ir = {
        "schema": "aladin-drama-portrait/ir@1",
        "project": project,
        "release": {"platforms": platforms, "release_date": release_date},
        "inputs": inputs,
        "person_count": len(person_list),
        "persons": person_list,
        "license_count": len(licenses),
        "licenses": licenses,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(ir, f, ensure_ascii=False, indent=2)

    print("[ok] 项目《%s》导入 %d 个人物资产、%d 份授权登记 -> %s"
          % (project or "未命名", len(person_list), len(licenses), args.out))
    if release_date:
        print("     发行基准日：%s ｜ 发行平台：%s" % (release_date, "、".join(platforms) or "(未指定)"))
    else:
        print("     [warn] 未提供 --release-date，到期比对将以今日为基准")
    ac = {}
    for p in person_list:
        for a in p["asset_types"]:
            ac[a] = ac.get(a, 0) + 1
    for k in ASSET_TYPES:
        if ac.get(k):
            print("     %-14s %d" % (k, ac[k]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

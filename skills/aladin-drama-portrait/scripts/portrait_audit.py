# -*- coding: utf-8 -*-
"""aladin-drama-portrait · portrait_audit.py
人物肖像权授权链自查：对每个人物资产做确定性检查——需授权类型是否缺证、
授权要素是否完整、是否过期/即将到期、平台/用途是否越界、AI形象是否撞脸公众人物、
声音克隆授权、转授瑕疵、平台 AI 人物报备缺失，输出 100 分制门禁评分与整改+回灌契约。

用法：
  python portrait_audit.py --ir _portrait_ir.json --platform 红果 \
      --filing-ai-persona yes --out _portrait.json

仅 Python 标准库，确定性可复算，同输入必同输出。
"""
import argparse
import datetime
import json
import sys

# 各人物资产类型所需的授权类型（license_type）
REQUIRED_LICENSE = {
    "real_actor": "portrait",       # 真人出演 → 肖像授权
    "digital_human": "digital_human",  # 第三方数字人 → 数字人许可
    "face_swap": "faceswap_source",    # 换脸 → 源肖像授权
    "voice_clone": "voice",            # 声音克隆 → 声音授权
    # ai_original 无需真人授权，但走撞脸人工项 + 平台报备
}

# 授权要素必备字段（缺失即 A2）
REQUIRED_ELEMENTS = ("licensor", "licensee", "scope_use", "term_start", "term_end", "doc_ref")

# 平台是否强制 AI 数字人/合成人物报备（简化门禁映射）
PLATFORM_FILING_REQUIRED = {"红果", "抖音", "快手", "腾讯", "爱奇艺", "芒果"}

SEVERITY_PENALTY = {"P0": 25, "P1": 8, "P2": 3}


def parse_date(s):
    s = (s or "").strip().replace("/", "-").replace(".", "-")
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def find_licenses(licenses, asset_name, ltype):
    out = []
    for lic in licenses:
        if lic.get("asset_name", "").strip() == asset_name and lic.get("license_type", "").strip() == ltype:
            out.append(lic)
    return out


def add(findings, pid, name, rule, sev, msg, fix):
    findings.append({
        "pid": pid, "asset": name, "rule": rule, "severity": sev,
        "message": msg, "fix": fix,
    })


def audit(ir, target_platform, filing_ai_persona):
    persons = ir.get("persons", [])
    licenses = ir.get("licenses", [])
    rel = ir.get("release", {})
    release_date = parse_date(rel.get("release_date")) or datetime.date.today()
    plan_platforms = rel.get("platforms", []) or []
    if target_platform and target_platform not in plan_platforms:
        plan_platforms = list(dict.fromkeys(plan_platforms + [target_platform]))

    findings = []
    has_ai_original = False

    for p in persons:
        pid, name = p.get("pid", ""), p.get("name", "")
        atypes = p.get("asset_types", []) or ["ai_original"]

        for at in atypes:
            if at == "ai_original":
                has_ai_original = True
                # A7 撞脸公众人物（AI 原创也可能神似真人）
                if p.get("resembles_public_figure") or p.get("public_figure_ref"):
                    ref = p.get("public_figure_ref") or "（未注明具体对象）"
                    add(findings, pid, name, "A7", "P1",
                        "AI 原创形象「%s」被标记神似公众人物：%s，存在肖像权/姓名权争议风险" % (name, ref),
                        "人工复核该形象与公众人物的相似度；如确有神似，调整五官/发型/气质做区分，或取得对方授权")
                continue

            need = REQUIRED_LICENSE.get(at)
            if not need:
                continue
            lics = find_licenses(licenses, name, need)

            # A7 换脸源撞脸公众人物
            if at == "face_swap" and (p.get("resembles_public_figure") or p.get("public_figure_ref")):
                ref = p.get("public_figure_ref") or "（未注明具体对象）"
                add(findings, pid, name, "A7", "P1",
                    "换脸源「%s」涉及公众人物：%s，肖像权风险极高" % (name, ref),
                    "务必取得该公众人物书面肖像授权，或更换非公众人物素材")

            if not lics:
                type_cn = {"portrait": "肖像授权", "digital_human": "数字人许可",
                           "faceswap_source": "换脸源肖像授权", "voice": "声音授权"}[need]
                add(findings, pid, name, "A1", "P0",
                    "人物「%s」为 %s 类型，缺少对应的%s凭证" % (name, at, type_cn),
                    "补齐并登记%s（授权方/被授权方/用途/期限/凭证编号）后再上架" % type_cn)
                continue

            for lic in lics:
                # A2 授权要素缺失
                miss = [e for e in REQUIRED_ELEMENTS if not (lic.get(e) or "").strip()]
                if miss:
                    cn = {"licensor": "授权方", "licensee": "被授权方", "scope_use": "授权用途",
                          "term_start": "起始日", "term_end": "到期日", "doc_ref": "凭证编号/存档"}
                    add(findings, pid, name, "A2", "P1",
                        "「%s」的%s授权要素缺失：%s" % (name, lic.get("license_type"),
                                                    "、".join(cn.get(m, m) for m in miss)),
                        "补全授权书要素：%s" % "、".join(cn.get(m, m) for m in miss))

                # A3/A4 到期检查
                tend = parse_date(lic.get("term_end"))
                if tend:
                    if tend < release_date:
                        add(findings, pid, name, "A3", "P0",
                            "「%s」的%s授权已于 %s 到期，早于发行基准日 %s" %
                            (name, lic.get("license_type"), tend.isoformat(), release_date.isoformat()),
                            "续签授权至覆盖发行及可预期的持续传播期后再上架")
                    elif (tend - release_date).days <= 30:
                        add(findings, pid, name, "A4", "P1",
                            "「%s」的%s授权将于 %s 到期，距发行基准日不足 30 天" %
                            (name, lic.get("license_type"), tend.isoformat()),
                            "短剧长期在架，建议提前续签，避免传播期内授权失效")

                # A5 平台越界
                scope_plats = lic.get("scope_platform_list", []) or []
                if scope_plats:
                    out_of = [pl for pl in plan_platforms if pl not in scope_plats]
                    if out_of:
                        add(findings, pid, name, "A5", "P0",
                            "「%s」授权平台范围为【%s】，但发行计划含未授权平台：%s" %
                            (name, "、".join(scope_plats), "、".join(out_of)),
                            "扩大授权平台范围，或从发行计划中移除未授权平台")

                # A6 用途越界（商用发行 vs 非商用授权）
                use = (lic.get("scope_use") or "").strip().lower()
                if use and use in ("noncommercial", "non-commercial", "非商用", "个人", "personal"):
                    add(findings, pid, name, "A6", "P0",
                        "「%s」授权用途为「非商用」，短剧商业发行属越界使用" % name,
                        "取得商用授权后再上架")

                # A9 转授瑕疵
                src = (lic.get("source") or "").strip().lower()
                if src in ("sublicense", "二次授权", "转授") and not lic.get("transferable_bool", False):
                    add(findings, pid, name, "A9", "P1",
                        "「%s」凭证为二次/转授来源，但授权本身标注不可转授，授权链存在瑕疵" % name,
                        "核实原始授权是否允许转授；索取完整授权链证据或改用可转授素材")

    # A10 平台 AI 人物报备（项目级）
    needs_filing = [pl for pl in plan_platforms if pl in PLATFORM_FILING_REQUIRED]
    if has_ai_original and needs_filing and not filing_ai_persona:
        add(findings, "-", "（项目级）", "A10", "P1",
            "发行平台【%s】通常要求对 AI 合成/数字人形象履行报备或显著标识，当前项目未声明已报备" %
            "、".join(needs_filing),
            "在平台完成 AI 合成人物报备/标识，并将 --filing-ai-persona 置为 yes 复检")

    # ---------- 评分 ----------
    counts = {"P0": 0, "P1": 0, "P2": 0}
    for f in findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
    penalty = sum(SEVERITY_PENALTY[s] * n for s, n in counts.items())
    score = max(0, 100 - penalty)
    if counts["P0"] > 0:
        gate, grade = "BLOCK", "D"
    elif score >= 80:
        gate, grade = "READY", "A" if score >= 90 else "B"
    else:
        gate, grade = "REVIEW", "C"

    # ---------- feedback 回灌契约 ----------
    fb_cast = sorted({f["asset"] for f in findings if f["rule"] in ("A1", "A2")})
    fb_publish_drop = sorted({f["asset"] for f in findings if f["rule"] in ("A5", "A6")})
    fb_renew = sorted({f["asset"] for f in findings if f["rule"] in ("A3", "A4")})
    feedback = {
        "to_drama_cast_missing_license": fb_cast,
        "to_drama_publish_platform_conflict": fb_publish_drop,
        "renew_watchlist": fb_renew,
        "need_platform_filing": bool(has_ai_original and needs_filing and not filing_ai_persona),
    }

    report = {
        "schema": "aladin-drama-portrait/report@1",
        "project": ir.get("project", ""),
        "release": {"platforms": plan_platforms, "release_date": release_date.isoformat()},
        "target_platform": target_platform or "",
        "person_count": len(persons),
        "license_count": len(licenses),
        "summary": {"score": score, "grade": grade, "gate": gate,
                    "P0": counts["P0"], "P1": counts["P1"], "P2": counts["P2"],
                    "finding_count": len(findings)},
        "findings": findings,
        "feedback": feedback,
    }
    return report


def main():
    ap = argparse.ArgumentParser(description="人物肖像权授权链自查")
    ap.add_argument("--ir", required=True, help="portrait_ingest 产出的 _portrait_ir.json")
    ap.add_argument("--platform", default="", help="目标发行平台（补充门禁比对）")
    ap.add_argument("--filing-ai-persona", default="no", help="是否已完成平台 AI 合成人物报备 yes/no")
    ap.add_argument("--out", default="_portrait.json", help="输出报告 JSON")
    args = ap.parse_args()

    with open(args.ir, encoding="utf-8") as f:
        ir = json.load(f)

    filed = str(args.filing_ai_persona).strip().lower() in ("1", "yes", "y", "true", "是")
    report = audit(ir, args.platform.strip(), filed)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    s = report["summary"]
    print("[ok] 授权链自查完成 -> %s" % args.out)
    print("     门禁：%s（%d 分/%s 档）｜ P0=%d P1=%d P2=%d ｜ 命中 %d 条"
          % (s["gate"], s["score"], s["grade"], s["P0"], s["P1"], s["P2"], s["finding_count"]))
    if s["gate"] == "BLOCK":
        print("     [BLOCK] 存在 P0 授权硬伤，禁止上架，请先按整改清单处理")
    return 0


if __name__ == "__main__":
    sys.exit(main())

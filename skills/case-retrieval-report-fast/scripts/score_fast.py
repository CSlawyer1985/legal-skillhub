#!/usr/bin/env python3
"""score_fast.py — (快速版)案例检索报告Plus 的本地打分与排序环节（v1.4.0 匹配模型）。

Skill作者：浙江金道律师事务所 龚家勇律师（微信：13967182079）

匹配模型（按 2026-09-22 用户口径）：
    恒定计入的三要素：
        r1 请求权基础高匹配   权重 3.0
        r2 法律关系高匹配     权重 3.0
        r3 案件事实高匹配     权重 2.0
    条件计入的第四要素：
        r4 结果相似度         权重 2.0   —— 仅当用户**指定**检索特定结果的案例时计入

两种模式：
    --result-mode unspecified（默认）：用户未指定结果，r4 **不计入**总分、不影响入报；
                                      满分 8；r4 若存在仅记录于 result_note 供报告提示。
    --result-mode specified          ：用户指定了特定结果，r4 计入；满分 10；
                                      r4 = 0（结果与指定结果相反）者判为「负向」并剔除。

分级按**得分率**（match_rate），两种模式可比：
    A 级（高匹配）≥ 80%　　B 级（可用）≥ 60%　　C 级（不入报）< 60%
入报硬门槛：r1 ≥ 1.5、r2 ≥ 1.5、r3 ≥ 1.0（三项各不低于自身权重的 50%），
          specified 模式另加 r4 > 0。

纯本地计算，不消耗任何检索额度。

用法：
    python score_fast.py --candidates _work/_candidates.json \
                         --judged _work/_judged.json \
                         --out _work/_scored.json \
                         [--result-mode unspecified|specified] [--result-target 支持] [--top-n 8]

输入字段约定（字段名大小写不敏感）：
    _candidates.json: 列表，或 {"cases": [...]}；每条需含案号（case_number / ah / 案号）
    _judged.json    : {"cases": [{"case_number": "...", "r1": 3, "r2": 3, "r3": 2, "r4": 2}]}
                      或 {"<案号>": {"r1": ..., ...}}
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# 恒定三要素 ＋ 条件要素（结果相似度）
CORE_WEIGHTS = {"r1": 3.0, "r2": 3.0, "r3": 2.0}
RESULT_WEIGHTS = {"r4": 2.0}
# 入报硬门槛：各要素不得低于自身权重的 50%
MIN_RATIO = 0.5
# 分级阈值（按得分率）
LEVEL_A_RATE = 0.80
LEVEL_B_RATE = 0.60
# 案号脱敏的典型特征
MASK_PATTERN = re.compile(r"[*＊x×X]{2,}|某某|某甲|某乙|\u25a1")
# 与指定结果相反
NEGATIVE_MARKS = ("negative", "负向", "反向", "不利", "不符", "-1")
POSITIVE_MARKS = ("positive", "正向", "支持", "符合", "1")

CASE_NUMBER_KEYS = ("case_number", "ah", "case_no", "案号")
COURT_KEYS = ("court", "court_name", "fayuan", "jbdw", "法院", "审理法院")
DATE_KEYS = ("decision_date", "jarq", "date", "裁判日期", "结案日期")
# 案由：召回接口返回的 cause_of_action 可能是编码（如 "9565"），案由文字在 anyou 字段
CAUSE_KEYS = ("anyou", "cause", "cause_of_action", "ay", "案由")
TITLE_KEYS = ("title", "case_name", "标题")
COURT_LEVEL_KEYS = ("court_level", "cj", "法院层级")
PROCEDURE_KEYS = ("trial_procedure", "procedure", "审判程序")
# 法院层级序：同级匹配时优先高层级（2026-09-23 实测：二审案例曾因日期最早被挤出 top N）
LEVEL_RANK = {"最高": 4, "高级": 3, "中级": 2, "基层": 1}
SUMMARY_KEYS = ("summary", "content", "abstract", "摘要", "要点")
SCORE_KEYS = ("score", "semantic_score", "similarity", "语义相关度")
ID_KEYS = ("case_id", "id", "caseid")
# 旧版字段（v1.2.0 及以前的 s1–s5），出现即报错，禁止静默换算
LEGACY_KEYS = ("s1", "s2", "s3", "s4", "s5")


def infer_court_level(court: str) -> str:
    """从法院名称推断层级（court_level 字段缺失时的兜底）。

    召回接口并非每次都返回 court_level，但 court 名称始终包含层级标识。
    """
    name = str(court or "")
    for token in ("最高人民法院", "高级人民法院", "中级人民法院", "基层人民法院"):
        if token in name:
            return token[:2]
    # 「XX省XX市中级人民法院」等常规写法已覆盖；以下处理铁路、海事、知识产权等专门法院
    if "中级" in name:
        return "中级"
    if "高级" in name:
        return "高级"
    if "最高" in name:
        return "最高"
    if name:
        return "基层"
    return ""


def _pick(item: dict, keys, default=None):
    """按候选键名取值（大小写与空格不敏感）。"""
    if not isinstance(item, dict):
        return default
    norm = {str(k).strip().lower().replace(" ", "").replace("_", ""): v for k, v in item.items()}
    for key in keys:
        k = str(key).strip().lower().replace(" ", "").replace("_", "")
        if k in norm and norm[k] not in (None, ""):
            return norm[k]
    return default


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _as_list(data, key_hint="cases"):
    """把输入归一为列表。"""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in (key_hint, "data", "results", "items", "candidates"):
            if isinstance(data.get(key), list):
                return data[key]
        return [{**v, "case_number": k} if isinstance(v, dict) else {"case_number": k}
                for k, v in data.items()]
    return []


def normalize_case_number(value) -> str:
    """案号归一：去空白、全角括号与破折号统一。"""
    if value is None:
        return ""
    text = str(value).strip()
    text = text.replace("\u3000", "").replace(" ", "")
    text = text.replace("（", "(").replace("）", ")")
    text = text.replace("－", "-").replace("—", "-").replace("–", "-")
    return text


def normalize_date(value) -> str:
    """日期归一：支持 20260126(int/str)、'2025年07月24日'、'2025-07-24'。"""
    if value in (None, ""):
        return ""
    if isinstance(value, int) and 19000101 <= value <= 29991231:
        s = str(value)
        return f"{s[:4]}-{s[4:6]}-{s[6:]}"
    text = str(value).strip()
    if text.isdigit() and len(text) == 8:
        return f"{text[:4]}-{text[4:6]}-{text[6:]}"
    m = re.match(r"^(\d{4})年(\d{1,2})月(\d{1,2})日", text)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return text


def _pick_cause(item: dict, default=""):
    """取案由文字：跳过纯数字编码（接口偶以编码返回）。"""
    for key in CAUSE_KEYS:
        value = _pick(item, [key])
        if value in (None, ""):
            continue
        if isinstance(value, list):
            value = value[0] if value else ""
        text = str(value).strip()
        if text and not text.isdigit():
            return text
    return default


def _proc_rank(row: dict) -> int:
    """审判程序序：二审／再审优先于一审（上级法院的裁判对实务更具参考价值）。"""
    proc = str(row.get("_procedure", "") or "")
    if any(k in proc for k in ("再审", "二审", "重审")):
        return 2
    if "一审" in proc or "初" in proc:
        return 1
    return 0


def _title_key(value) -> str:
    """标题归一：去空白，用于重复识别。"""
    return re.sub(r"\s+", "", str(value or ""))


def mark_duplicates(rows: list) -> list:
    """标记「疑似重复入库」：同法院 ＋ 同裁判日期 ＋ 同标题（仅脱敏名称不同）者，
    保留组内第一条，其余标记 duplicate_suspect 并指向保留条。

    实测（2026-09-23）：（2025）浙0602民初522号与540号系同一案件重复入库，
    若不处理会同时占用两个入报名额。
    """
    groups: dict[tuple, list] = {}
    for row in rows:
        title = _title_key(row.get("title"))
        if not title or not row.get("court") or not row.get("decision_date"):
            continue
        key = (str(row["court"]), str(row["decision_date"]), title)
        groups.setdefault(key, []).append(row["case_number"])

    dup_pairs = []
    for members in groups.values():
        if len(members) < 2:
            continue
        keep = members[0]
        dup_pairs.append((keep, [m for m in members if m != keep]))
        for row in rows:
            if row["case_number"] in members and row["case_number"] != keep:
                row["duplicate_suspect"] = True
                row["duplicate_of"] = keep
    return dup_pairs


def ah_complete(case_number: str) -> bool:
    """案号完整性：非空、不含脱敏特征、含年份与法院代字。"""
    if not case_number:
        return False
    if MASK_PATTERN.search(case_number):
        return False
    return bool(re.search(r"\(?\d{4}\)?", case_number)) and len(case_number) >= 8


def _to_float(value, default=0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _detect_mode(judged_raw, cli_mode: str) -> str:
    """判定结果相似度是否计入。

    优先级：CLI 显式指定 ＞ `_judged.json` 顶层 `result_mode` 字段 ＞ 默认 unspecified。
    默认取 unspecified 是刻意的保守选择——模型是否填写 r4，不能反推用户是否指定了结果。
    """
    if cli_mode in ("specified", "unspecified"):
        return cli_mode
    if isinstance(judged_raw, dict):
        declared = str(judged_raw.get("result_mode", "")).strip().lower()
        if declared in ("specified", "unspecified"):
            return declared
    return "unspecified"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="快速版案例检索：三要素（＋条件结果相似度）加权打分与排序")
    parser.add_argument("--candidates", required=True, help="候选池 JSON 路径")
    parser.add_argument("--judged", required=True, help="模型逐案判定 JSON 路径")
    parser.add_argument("--out", required=True, help="输出 _scored.json 路径")
    parser.add_argument("--result-mode", default="auto",
                        choices=("auto", "specified", "unspecified"),
                        help="是否指定检索特定结果：specified=指定（r4 计入）／"
                             "unspecified=未指定（r4 不计入，默认）／auto=依 judged 是否含 r4 推断")
    parser.add_argument("--result-target", default="",
                        help="用户指定的结果（如「支持涤除」「驳回诉请」），仅记录于报告")
    parser.add_argument("--top-n", type=int, default=8, help="入报案例上限（默认 8，区间 5–10）")
    parser.add_argument("--no-eligible-filter", action="store_true",
                        help="不按入报硬门槛过滤（仅调试用）")
    args = parser.parse_args()

    cand_path = Path(args.candidates).expanduser()
    judged_path = Path(args.judged).expanduser()
    out_path = Path(args.out).expanduser()
    for path in (cand_path, judged_path):
        if not path.exists():
            print(f"[错误] 输入文件不存在：{path}", file=sys.stderr)
            return 2

    candidates = _as_list(_load_json(cand_path))
    judged_raw = _load_json(judged_path)

    judged: dict[str, dict] = {}
    for entry in _as_list(judged_raw):
        if isinstance(entry, dict):
            ah = normalize_case_number(_pick(entry, CASE_NUMBER_KEYS))
            if ah:
                judged[ah] = entry

    # 旧版字段检测：s1–s5 与 r1–r4 口径不同，禁止静默换算
    legacy_hits = [ah for ah, v in judged.items()
                   if any(_pick(v, [k]) not in (None, "") for k in LEGACY_KEYS)]
    if legacy_hits:
        print("[错误] _judged.json 含旧版字段 s1–s5（v1.2.0 口径），与现行 r1–r4 模型不可换算。\n"
              "       请按现行三要素重新判定：r1 请求权基础／r2 法律关系／r3 案件事实（＋r4 结果相似度）。\n"
              f"       命中 {len(legacy_hits)} 条，示例：{legacy_hits[:3]}", file=sys.stderr)
        return 3

    mode = _detect_mode(judged_raw, args.result_mode)
    weights = dict(CORE_WEIGHTS)
    if mode == "specified":
        weights.update(RESULT_WEIGHTS)
    full_score = round(sum(weights.values()), 2)

    scored, seen, missing = [], set(), []
    for item in candidates:
        ah_raw = _pick(item, CASE_NUMBER_KEYS)
        ah = normalize_case_number(ah_raw)
        if not ah:
            continue
        if ah in seen:
            continue
        seen.add(ah)

        verdict = judged.get(ah)
        if verdict is None:
            missing.append(ah)
            continue

        parts = {}
        for key, weight in weights.items():
            value = _to_float(_pick(verdict, [key, key.upper()]))
            parts[key] = round(min(max(value, 0.0), weight), 2)  # 截顶：不得超过该项权重
        total = round(sum(parts.values()), 2)
        rate = round(total / full_score, 4) if full_score else 0.0

        raw_r4 = _pick(verdict, ["r4", "R4"])
        r4_given = raw_r4 not in (None, "")
        r4_value = _to_float(raw_r4)
        mark = str(_pick(verdict, ["direction", "dir", "方向"], default="")).strip()

        # 结果不符判定：**仅在指定结果模式下生效**（未指定时结果相似度不作为匹配要素）
        # 注意：r4 **未填写**不等于"结果相反"。漏判须单独标记为「r4缺判」并要求补判，
        # 不得混入 negative_list，否则报告会把未判定的案例披露为"结果与指定结果相反"。
        mismatched = False
        r4_missing = False
        if mode == "specified":
            if not r4_given and not mark:
                r4_missing = True
            else:
                mismatched = (r4_value <= 0
                              or mark.lower() in NEGATIVE_MARKS or mark in NEGATIVE_MARKS)

        if r4_missing:
            level = "r4缺判"
        elif mismatched:
            level = "负向"
        elif rate >= LEVEL_A_RATE:
            level = "A"
        elif rate >= LEVEL_B_RATE:
            level = "B"
        else:
            level = "C"

        core_ok = (parts.get("r1", 0) >= CORE_WEIGHTS["r1"] * MIN_RATIO
                   and parts.get("r2", 0) >= CORE_WEIGHTS["r2"] * MIN_RATIO
                   and parts.get("r3", 0) >= CORE_WEIGHTS["r3"] * MIN_RATIO)
        eligible = (core_ok and rate >= LEVEL_B_RATE
                    and not mismatched and not r4_missing) \
            or args.no_eligible_filter

        # 未指定结果模式下，r4 仅作信息记录，用于报告标注每例结果方向（不计入得分）
        result_note = ""
        if mode == "unspecified":
            if r4_given:
                result_note = ("裁判结果与检索方向一致" if r4_value > 0
                               else "裁判结果与检索方向相反")
            elif mark:
                if mark.lower() in POSITIVE_MARKS or mark in POSITIVE_MARKS:
                    result_note = "裁判结果与检索方向一致"
                elif mark.lower() in NEGATIVE_MARKS or mark in NEGATIVE_MARKS:
                    result_note = "裁判结果与检索方向相反"
                else:
                    result_note = f"结果方向：{mark}"
            else:
                result_note = "结果方向未判定"

        scored.append({
            "case_number": ah,
            "case_number_raw": ah_raw if isinstance(ah_raw, str) else ah,
            "case_id": _pick(item, ID_KEYS, default=""),
            "court": _pick(item, COURT_KEYS, default=""),
            "decision_date": normalize_date(_pick(item, DATE_KEYS, default="")),
            "cause": _pick_cause(item),
            "title": _pick(item, TITLE_KEYS, default=""),
            "summary": _pick(item, SUMMARY_KEYS, default=""),
            "semantic_score": _to_float(_pick(item, SCORE_KEYS, default=0.0)),
            "court_level": (str(_pick(item, COURT_LEVEL_KEYS, default="") or "")
                            or infer_court_level(_pick(item, COURT_KEYS, default=""))),
            "_procedure": str(_pick(item, PROCEDURE_KEYS, default="") or ""),
            "duplicate_suspect": False,
            "duplicate_of": "",
            "elements": parts,
            "match_score": total,
            "full_score": full_score,
            "match_rate": round(rate * 100, 1),
            "level": level,
            "ah_complete": ah_complete(ah),
            "report_eligible": bool(eligible),
            "result_matched": (not mismatched and not r4_missing) if mode == "specified" else None,
            "r4_missing": bool(r4_missing),
            "result_note": result_note,
            "note": _pick(verdict, ["note", "remark", "备注"], default=""),
        })

    # 排序（自末级向首级逐级稳定排序）：
    #   得分率 ＞ 法院层级 ＞ 审判程序 ＞ 裁判日期
    # 得分率使两种模式可比；层级与程序优先，避免上级法院裁判因日期较早被挤出名单。
    scored.sort(key=lambda r: (r["decision_date"], r["case_number"]), reverse=True)
    scored.sort(key=lambda r: _proc_rank(r), reverse=True)
    scored.sort(key=lambda r: LEVEL_RANK.get(r["court_level"], 0), reverse=True)
    scored.sort(key=lambda r: r["match_rate"], reverse=True)
    for idx, row in enumerate(scored, 1):
        row["rank"] = idx

    # 疑似重复标记（同法院＋同日期＋同标题）——须在排序之后执行，
    # 以保证保留的是组内排序最前（即最值得入报）的一条。
    dup_pairs = mark_duplicates(scored)

    eligible_rows = [r for r in scored if r["report_eligible"]]
    # 疑似重复者不占用入报名额（保留组内排序最前的一条）
    pool = [r for r in eligible_rows if not r["duplicate_suspect"]] or eligible_rows
    selected = pool[: max(args.top_n, 0)] if args.top_n > 0 else pool
    selected_numbers = {r["case_number"] for r in selected}
    for row in scored:
        row["selected"] = row["case_number"] in selected_numbers

    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "mode": mode,
        "result_target": args.result_target,
        "weights": weights,
        "weights_detail": {
            "r1": "请求权基础高匹配", "r2": "法律关系高匹配", "r3": "案件事实高匹配",
            "r4": "结果相似度（仅 specified 模式计入）",
        },
        "full_score": full_score,
        "thresholds": {"A_rate": LEVEL_A_RATE, "B_rate": LEVEL_B_RATE,
                       "min_ratio": MIN_RATIO,
                       "min_r1": CORE_WEIGHTS["r1"] * MIN_RATIO,
                       "min_r2": CORE_WEIGHTS["r2"] * MIN_RATIO,
                       "min_r3": CORE_WEIGHTS["r3"] * MIN_RATIO},
        "counts": {
            "candidates": len(candidates),
            "deduped": len(scored),
            "judged_missing": len(missing),
            "A": sum(1 for r in scored if r["level"] == "A"),
            "B": sum(1 for r in scored if r["level"] == "B"),
            "C": sum(1 for r in scored if r["level"] == "C"),
            "negative": sum(1 for r in scored if r["level"] == "负向"),
            "r4_missing": sum(1 for r in scored if r["r4_missing"]),
            "eligible": len(eligible_rows),
            "selected": len(selected),
            "ah_incomplete": sum(1 for r in scored if not r["ah_complete"]),
            "duplicate_suspects": sum(1 for r in scored if r["duplicate_suspect"]),
        },
        "selected": selected,
        "cases": scored,
    }
    if missing:
        payload["judged_missing_list"] = missing[:50]
    if dup_pairs:
        payload["duplicate_pairs"] = [
            {"keep": keep, "suspects": suspects} for keep, suspects in dup_pairs]
    negatives = [r["case_number"] for r in scored if r["level"] == "负向"]
    if negatives:
        payload["negative_list"] = negatives
    r4_missing_list = [r["case_number"] for r in scored if r["r4_missing"]]
    if r4_missing_list:
        payload["r4_missing_list"] = r4_missing_list

    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    c = payload["counts"]
    print(f"匹配模型：{mode}"
          + (f"（指定结果：{args.result_target}）" if args.result_target else "")
          + f"　满分 {full_score:g} 分　"
          + ("r1+r2+r3+r4 计入" if mode == "specified" else "仅 r1+r2+r3 计入，结果相似度不计入"))
    print(f"候选 {c['candidates']} → 去重 {c['deduped']} → 已判 {c['deduped'] - c['judged_missing']}"
          f"（缺判 {c['judged_missing']}）")
    print(f"分级：A {c['A']} 例 / B {c['B']} 例 / C {c['C']} 例"
          + (f" / 结果不符 {c['negative']} 例" if mode == "specified" else "")
          + (f" / r4 缺判 {c['r4_missing']} 例" if c["r4_missing"] else "")
          + f"；入报资格 {c['eligible']} 例；本次选取 {c['selected']} 例")
    print(f"案号不完整（脱敏）{c['ah_incomplete']} 例 —— 入报时须逐案标注")
    if c["duplicate_suspects"]:
        for pair in payload.get("duplicate_pairs", []):
            print(f"[疑似重复] 保留 {pair['keep']}；"
                  f"疑似重复 {'、'.join(pair['suspects'])}（同法院＋同裁判日期＋同标题，"
                  f"仅脱敏名称不同）—— 不占用入报名额，须在报告中披露并人工核对")
    if c["duplicate_suspects"] and c["eligible"] - c["duplicate_suspects"] < args.top_n:
        print("[提示] 剔除疑似重复后可用案例不足，已从重复项中补足；"
              "务必在报告中说明该情况。")
    if mode == "specified" and c["negative"]:
        print(f"[结果闸门] 与指定结果不符者 {c['negative']} 例，已剔除："
              f"{'；'.join(payload.get('negative_list', []))}")
        print("          上述案号须在报告第一部分如实披露，不得隐瞒。")
    if payload.get("r4_missing_list"):
        print(f"[须补判] 指定结果模式下有 {c['r4_missing']} 例未判定 r4："
              f"{'；'.join(payload['r4_missing_list'])}")
        print("          上述案例已暂不入报（r4 缺判 ≠ 结果相反），"
              "须逐案补判 r4 后重跑；不得将其写入「结果不符」清单。", file=sys.stderr)
    if mode == "unspecified":
        print("[提示] 未指定结果模式：结果相似度不参与评分，反向案例可入报；"
              "须在报告中标注每例裁判结果方向，并在风险提示中说明该口径。")
    if c["selected"] < 5:
        print("[提示] 入报不足 5 例：如实出具，不得降低门槛或追加检索凑数。", file=sys.stderr)
    print(f"已写出：{out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

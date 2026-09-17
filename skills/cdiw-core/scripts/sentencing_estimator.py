#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""量刑双轨测算脚本（sentencing_estimator.py）。

理论轨：按《关于常见犯罪的量刑指导意见（试行）》（法发〔2021〕21号）
二（二）调节方法测算——先适用情节（未成年人、老年人、聋哑盲、未遂、
从犯等）先调节基准刑，其余情节同向相加、逆向相减；内置重复评价检测
（认罪认罚与自首、坦白等不重复评价，叠加总量上限60%）。
实证轨：输入类案宣告刑区间（--empirical_range），计算偏差百分比。

调用方式：
  python scripts/sentencing_estimator.py --crime 诈骗罪 --base_sentence 42 \
      --factors '[{"id":"surrender","value":0.30},{"id":"restitution","value":0.25}]' \
      [--empirical_range 18-30] [--province 浙江] [--local_details_file 路径] [--out 输出路径]

统一接口规范：
  - 仅依赖Python标准库；支持--help；
  - 输出JSON信封：{status, error_code, message, data}；
  - 退出码：0成功 / 1参数错误 / 2数据文件缺失或损坏 / 3计算或校验失败；
  - 错误码：ERR_ARGS_MISSING / ERR_FACTOR_UNKNOWN / ERR_VALUE_OUT_OF_RANGE /
    ERR_DOUBLE_EVALUATION / ERR_IO。
  - 测算结果为区间推演（法定区间内律师论证值的计算演示），非裁判结果承诺；
    输出精度具体到月；调节比例最终取值由法官裁量。
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime

SCRIPT_NAME = "sentencing_estimator"

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "assets", "data")

STACK_CAP = 0.60  # 认罪认罚叠加档合计上限（法发〔2021〕21号三（十四））


def make_trace_id():
    stamp = datetime.now().isoformat()
    return SCRIPT_NAME + hashlib.md5((SCRIPT_NAME + stamp).encode("utf-8")).hexdigest()[:8]


def envelope(status, error_code, message, data):
    return {"status": status, "error_code": error_code, "message": message, "data": data}


def load_factors():
    path = os.path.join(DATA_DIR, "sentencing_factors.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def fail(error_code, message):
    print(json.dumps(envelope("error", error_code, message, None),
                     ensure_ascii=False, indent=2))
    sys.exit(3)


def month_value(text):
    """--base_sentence 类型校验：须为月数数字，中文表述给出可读错误提示。"""
    try:
        return float(text)
    except ValueError:
        raise argparse.ArgumentTypeError(
            "基准刑须为月数数字（如36表示有期徒刑三年，42表示三年六个月），"
            "不支持中文表述：%s" % text)


def main():
    parser = argparse.ArgumentParser(
        prog=SCRIPT_NAME,
        description="量刑双轨测算：理论轨（起点—基准刑—宣告刑三步＋先适用情节规则＋重复评价检测）"
                    "与实证轨（类案区间偏差比对）；结果为区间推演，非裁判结果承诺。",
        epilog=(
            "调用示例：\n"
            "  python scripts/sentencing_estimator.py --crime 盗窃罪 --base_sentence 36 \\\n"
            "      --factors '[{\"id\":\"surrender\",\"value\":0.30},{\"id\":\"plea_agreement\",\"value\":0.25}]'\n"
            "\n"
            "参数格式说明：\n"
            "  --base_sentence  基准刑月数（数字，36即三年；由量刑起点＋增量事实确定）\n"
            "  --factors        量刑情节JSON数组，元素含id与value（从宽/从重比例小数）；\n"
            "                   可用id（19项）：surrender自首、confession坦白、plea_agreement认罪认罚、\n"
            "                   restitution退赃退赔、compensation_forgiveness赔偿谅解、voluntary_plea当庭\n"
            "                   自愿认罪、meritorious立功、accomplice从犯、attempt未遂、minor_12_16未成年、\n"
            "                   recidivist累犯等，全表见assets/data/sentencing_factors.json\n"
            "  --empirical_range 类案宣告刑区间（月，如18-30；启用实证轨偏差比对）"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--crime", required=True, help="罪名（如：诈骗罪）")
    parser.add_argument("--base_sentence", required=True, type=month_value,
                        help="基准刑（月数，可为小数；如36即三年；由量刑起点＋增量事实确定）")
    parser.add_argument("--factors", required=True,
                        help="量刑情节JSON数组，如：[{\"id\":\"surrender\",\"value\":0.30}]；"
                             "value为律师论证取值（从宽/从重比例的小数形式）")
    parser.add_argument("--empirical_range", help="类案宣告刑区间（月，如：18-30；实证轨）")
    parser.add_argument("--province", help="省份（用于读取本省量刑实施细则提示）")
    parser.add_argument("--local_details_file", help="本省实施细则文件路径（可选）")
    parser.add_argument("--out", help="结果输出文件路径（可选）")
    args = parser.parse_args()
    trace_id = make_trace_id()

    factors_db = load_factors()
    if not factors_db:
        print(json.dumps(envelope("error", "ERR_IO", "sentencing_factors.json缺失或损坏", None),
                         ensure_ascii=False, indent=2))
        sys.exit(2)

    try:
        input_factors = json.loads(args.factors)
    except ValueError:
        fail("ERR_ARGS_MISSING", "--factors不是合法JSON：%s" % args.factors)
        return

    if args.base_sentence <= 0:
        fail("ERR_ARGS_MISSING", "--base_sentence须为正数（月）")
        return

    # 1. 情节校验：id存在、value在法定区间内
    by_id = {f["id"]: f for f in factors_db.get("factors", []) if "id" in f}
    applied, warnings = [], []
    for item in input_factors:
        fid = item.get("id")
        val = float(item.get("value", 0))
        if fid not in by_id:
            fail("ERR_FACTOR_UNKNOWN",
                 "未知量刑情节id：%s（可用id见sentencing_factors.json）" % fid)
            return
        f = by_id[fid]
        rng = f.get("ratio_range")
        if not rng:
            fail("ERR_FACTOR_UNKNOWN", "情节%s缺少结构化区间，请更新数据文件" % fid)
            return
        if not (rng[0] - 1e-9 <= val <= rng[1] + 1e-9):
            fail("ERR_VALUE_OUT_OF_RANGE",
                 "情节%s取值%.0f%%超出法定区间%.0f%%-%.0f%%（%s）" % (
                     f["name"], val * 100, rng[0] * 100, rng[1] * 100, f.get("source", "")))
            return
        applied.append({"id": fid, "name": f["name"], "value": val,
                        "direction": f["direction"], "first_apply": bool(f.get("first_apply")),
                        "source": f.get("source", "")})

    # 2. 重复评价检测：认罪认罚与禁止重复评价情节并存
    applied_ids = {a["id"] for a in applied}
    plea = by_id.get("plea_agreement", {})
    double_hits = sorted(applied_ids & set(plea.get("no_double_evaluation", []))) \
        if "plea_agreement" in applied_ids else []
    has_plea = "plea_agreement" in applied_ids
    if has_plea and double_hits:
        double_hit_names = "、".join(by_id[fid]["name"] for fid in double_hits)
        warnings.append(
            "重复评价提示：认罪认罚与%s并存——按法发〔2021〕21号三（十四），同一从宽事实不作重复评价，"
            "合计从宽总量按叠加档60%%上限口径处理（非逐项叠加）" % double_hit_names)
    # 同一情节重复输入检测
    if len(applied_ids) != len(applied):
        warnings.append("检测到同一情节重复输入，已按唯一值处理")

    # 3. 理论轨计算：先适用情节先调节，一般情节再调节（同向相加、逆向相减）
    base = args.base_sentence
    first_stage = [a for a in applied if a["first_apply"]]
    second_stage = [a for a in applied if not a["first_apply"]]

    steps = []
    current = base
    if first_stage:
        net_first = sum(a["value"] if a["direction"] == "从宽" else -a["value"]
                        for a in first_stage)
        net_first = max(-0.90, min(net_first, 0.90))
        current = base * (1 - net_first)
        steps.append({"stage": "先适用情节调节（法发〔2021〕21号二（二）2）",
                      "factors": [a["name"] for a in first_stage],
                      "net_ratio": round(net_first, 4),
                      "result_months": round(current, 1)})

    if second_stage:
        net_second = sum(a["value"] if a["direction"] == "从宽" else -a["value"]
                         for a in second_stage)
        # 认罪认罚叠加档总量控制（含先适用情节的从宽贡献）
        if has_plea and double_hits:
            total_mitigation = sum(a["value"] for a in first_stage + second_stage
                                   if a["direction"] == "从宽")
            if total_mitigation > STACK_CAP + 1e-9:
                clamped = STACK_CAP
                net_second = clamped - (total_mitigation - net_second)
                warnings.append("合计从宽%.0f%%超过叠加档上限60%%，已按60%%总量封顶计算" % (
                    total_mitigation * 100))
        net_second = max(-0.90, min(net_second, 0.90))
        current = current * (1 - net_second)
        steps.append({"stage": "一般情节调节（同向相加、逆向相减）",
                      "factors": [a["name"] for a in second_stage],
                      "net_ratio": round(net_second, 4),
                      "result_months": round(current, 1)})

    # 4. 宣告刑区间（论证值±合理弹性：取值组合的上下界演示——以各情节法定区间端点组合）
    mitigations = [a for a in applied if a["direction"] == "从宽"]
    aggravations = [a for a in applied if a["direction"] == "从重"]
    max_mit = sum(by_id[a["id"]]["ratio_range"][1] for a in mitigations)
    max_agg = sum(by_id[a["id"]]["ratio_range"][1] for a in aggravations)
    if has_plea and double_hits and max_mit > STACK_CAP:
        max_mit = STACK_CAP
    opt_low = base * (1 - min(max_mit, 0.90) + 0)  # 全部从宽取上限（有利顶格）
    pessimistic = base * (1 + max_agg) if aggravations else base
    lower_bound = max(1.0, round(opt_low))
    upper_bound = max(lower_bound, round(base * (1 + max_agg) if aggravations else base))
    if mitigations:
        upper_bound = max(upper_bound, round(base * (1 - min(
            sum(by_id[a["id"]]["ratio_range"][0] for a in mitigations), 0.90))))

    result_months = max(1, round(current))

    # 5. 实证轨：类案区间偏差比对
    empirical = None
    if args.empirical_range:
        try:
            lo, hi = [float(x) for x in args.empirical_range.split("-")]
        except ValueError:
            fail("ERR_ARGS_MISSING", "--empirical_range格式应为 起月-止月，如18-30")
            return
        dev_pct = None
        if lo <= result_months <= hi:
            position = "理论值落在类案区间内"
            dev_pct = round(abs(result_months - (lo + hi) / 2) / ((lo + hi) / 2) * 100, 1)
        else:
            ref = (lo + hi) / 2
            dev_pct = round(abs(result_months - ref) / ref * 100, 1)
            position = ("理论值高于类案区间上限" if result_months > hi else "理论值低于类案区间下限")
        empirical = {"class_case_range_months": [lo, hi],
                     "deviation_percent": dev_pct,
                     "position": position,
                     "review_flag": dev_pct is not None and dev_pct > 20,
                     "review_note": "偏差超20%提示复核：情节取值或类案相似性（偏差分析见量刑情节线第五步）"}

    # 6. 本省细则提示（浙江已预置：未显式传--local_details_file时自动定位预置文件）
    province_note = None
    if args.province:
        detail_path = args.local_details_file
        if not detail_path:
            preset = os.path.join(os.path.dirname(DATA_DIR), "..", "localization",
                                  "provincial_sentencing_details",
                                  "%s.md" % {"浙江": "zhejiang"}.get(args.province, args.province))
            preset = os.path.normpath(preset)
            if os.path.exists(preset):
                detail_path = preset
        if detail_path and os.path.exists(detail_path):
            province_note = "已读取本省细则：%s（省级细化档次以该文件为准）" % detail_path
        else:
            province_note = ("本省细则未配置（localization/provincial_sentencing_details/），"
                             "本次按全国指导意见测算，未含省级细化档次")

    data = {
        "trace_id": trace_id,
        "crime": args.crime,
        "base_sentence_months": args.base_sentence,
        "factors_applied": [{"id": a["id"], "name": a["name"],
                             "value_percent": round(a["value"] * 100, 1),
                             "direction": a["direction"],
                             "first_apply": a["first_apply"], "source": a["source"]}
                            for a in applied],
        "calc_steps": steps,
        "theoretical_sentence_months": result_months,
        "theoretical_range_months": [int(lower_bound), int(upper_bound)],
        "empirical_track": empirical,
        "province_note": province_note,
        "warnings": warnings,
        "notes": ["测算结果为区间推演（法定区间内论证值的计算演示），非裁判结果承诺，禁止向当事人作结果承诺",
                  "调节比例最终取值由法官裁量；宣告刑确定规则（法定最低以下／最高以上／20%调整权）见法发〔2021〕21号二（三）与sentencing_knowledge.md§一",
                  "刑期精度具体到月；日数计算仅用于羁押折抵（刑法第47条等）"],
    }
    out_text = json.dumps(envelope("ok", None, "测算完成", data), ensure_ascii=False, indent=2)
    if args.out:
        try:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(out_text)
        except OSError as exc:
            print(json.dumps(envelope("error", "ERR_IO", "输出文件写入失败：%s" % exc, None),
                             ensure_ascii=False, indent=2))
            sys.exit(2)
    print(out_text)
    sys.exit(0)


if __name__ == "__main__":
    main()

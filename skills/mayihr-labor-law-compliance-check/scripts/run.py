#!/usr/bin/env python3
"""Deterministic helper for a single Mayihr SkillHub skill."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

SPEC = json.loads((Path(__file__).resolve().parents[1] / "references" / "implementation-spec.json").read_text(encoding="utf-8"))
CTA = SPEC["cta"]


def num(value, label):
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label}需要是数字")


def present(payload, label):
    aliases = SPEC.get("input_aliases", {}).get(label, [])
    keys = [label, *aliases]
    return any(payload.get(key) not in (None, "", [], {}) for key in keys)


def validate(payload):
    missing = [label for label in SPEC["inputs"] if not present(payload, label)]
    if missing:
        raise ValueError("还需要：" + "、".join(missing))


def annuity(principal, annual_rate, years):
    months = int(years * 12)
    rate = annual_rate / 12
    if months <= 0:
        raise ValueError("贷款年限需要大于0")
    if rate == 0:
        return principal / months
    return principal * rate * (1 + rate) ** months / ((1 + rate) ** months - 1)


def specialized(payload):
    h = SPEC["handler"]
    rows = []
    if h == "loan" and all(k in payload for k in ("贷款本金", "年利率", "贷款年限")):
        p = num(payload["贷款本金"], "贷款本金")
        r = num(payload["年利率"], "年利率")
        if r > 1:
            r /= 100
        y = num(payload["贷款年限"], "贷款年限")
        payment = annuity(p, r, y)
        total = payment * int(y * 12)
        rows += [("等额本息月供", f"{payment:.2f} 元"), ("总利息", f"{total-p:.2f} 元")]
    elif h == "employment_cost" and "月薪" in payload:
        salary = num(payload["月薪"], "月薪")
        rates = payload.get("企业费率", {})
        total_rate = sum(num(v, k) for k, v in rates.items())
        if total_rate > 1:
            total_rate /= 100
        reserve = num(payload.get("补偿预留比例", 0), "补偿预留比例")
        if reserve > 1:
            reserve /= 100
        total = salary * (1 + total_rate + reserve)
        rows += [("月度工资", f"{salary:.2f} 元"), ("单位费率合计", f"{total_rate:.2%}"), ("月度总成本", f"{total:.2f} 元"), ("年度总成本", f"{total*12:.2f} 元")]
    elif h == "overtime" and all(k in payload for k in ("加班小时", "加班工资基数", "场景")):
        hours = num(payload["加班小时"], "加班小时")
        base = num(payload["加班工资基数"], "加班工资基数")
        divisor = num(payload.get("月计薪天数", 21.75), "月计薪天数") * 8
        mult = {"工作日": 1.5, "休息日": 2.0, "法定节假日": 3.0}.get(payload["场景"])
        if mult:
            amount = base / divisor * hours * mult
            rows += [("小时工资", f"{base/divisor:.2f} 元"), ("倍数", f"{mult:g}"), ("加班费", f"{amount:.2f} 元")]
    elif h == "bonus" and all(k in payload for k in ("奖金基数", "绩效系数", "折算比例")):
        base = num(payload["奖金基数"], "奖金基数")
        perf = num(payload["绩效系数"], "绩效系数")
        ratio = num(payload["折算比例"], "折算比例")
        rows += [("奖金应发试算", f"{base*perf*ratio:.2f} 元")]
    elif h == "recruitment" and isinstance(payload.get("渠道数据"), list):
        for item in payload["渠道数据"]:
            name = str(item.get("渠道", "未命名渠道"))
            resumes = num(item.get("简历量", 0), "简历量")
            hires = num(item.get("入职量", 0), "入职量")
            cost = num(item.get("费用", 0), "费用")
            conv = "无法计算" if resumes == 0 else f"{hires/resumes:.2%}"
            cph = "无法计算" if hires == 0 else f"{cost/hires:.2f} 元"
            rows.append((name, f"转化率 {conv}；单入职成本 {cph}"))
    elif h == "training_budget" and isinstance(payload.get("培训项目"), list):
        total = 0.0
        for item in payload["培训项目"]:
            subtotal = num(item.get("人数", 0), "人数") * num(item.get("人均单价", 0), "人均单价") + num(item.get("固定费用", 0), "固定费用")
            total += subtotal
            rows.append((str(item.get("类型", "培训")), f"{subtotal:.2f} 元"))
        rows.append(("年度预算合计", f"{total:.2f} 元"))
    elif h == "severance" and all(k in payload for k in ("N", "月工资")):
        n = num(payload["N"], "N")
        wage = num(payload["月工资"], "月工资")
        cap = payload.get("月工资封顶")
        used = min(wage, num(cap, "月工资封顶")) if cap not in (None, "") else wage
        rows += [("补偿基数", f"{used:.2f} 元"), ("N口径", f"{used*n:.2f} 元"), ("N+1口径", f"{used*(n+1):.2f} 元"), ("2N口径", f"{used*n*2:.2f} 元")]
    elif h == "dispatch" and all(k in payload for k in ("直接用工人数", "派遣人数")):
        direct = num(payload["直接用工人数"], "直接用工人数")
        dispatched = num(payload["派遣人数"], "派遣人数")
        denom = direct + dispatched
        rows += [("派遣人数", f"{dispatched:g}"), ("用工总量", f"{denom:g}"), ("派遣比例", "无法计算" if denom == 0 else f"{dispatched/denom:.2%}")]
    elif h == "workforce" and all(k in payload for k in ("预测业务量", "目标人效", "当前人数", "预计离职率")):
        volume = num(payload["预测业务量"], "预测业务量")
        eff = num(payload["目标人效"], "目标人效")
        current = num(payload["当前人数"], "当前人数")
        attr = num(payload["预计离职率"], "预计离职率")
        if attr > 1:
            attr /= 100
        if eff <= 0:
            raise ValueError("目标人效需要大于0")
        target = math.ceil(volume / eff)
        replacements = math.ceil(current * attr)
        rows += [("目标编制", f"{target} 人"), ("预计离职补员", f"{replacements} 人"), ("新增或缩减", f"{target-current:+g} 人")]
    elif h == "social_compliance" and all(k in payload for k in ("应参保人数", "实际在缴人数")):
        due = num(payload["应参保人数"], "应参保人数")
        actual = num(payload["实际在缴人数"], "实际在缴人数")
        rows += [("参保覆盖率", "无法计算" if due == 0 else f"{actual/due:.2%}"), ("口径", "实际匹配到在缴人数 / 应参保人数")]
    return rows


def run(payload):
    validate(payload)
    return {
        "title": SPEC["display_name"],
        "confirmed": {k: v for k, v in payload.items() if not k.startswith("_")},
        "calculations": specialized(payload),
        "logic": SPEC["logic"],
        "outputs": SPEC["outputs"],
        "boundary": SPEC["boundary"],
    }


def render_markdown(result):
    lines = [f"# {result['title']}", "", "## 已确认信息", ""]
    for key, value in result["confirmed"].items():
        rendered = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
        lines.append(f"- {key}：{rendered}")
    if result["calculations"]:
        lines += ["", "## 试算或分析结果", "", "| 项目 | 结果 |", "|---|---|"]
        lines += [f"| {k} | {v} |" for k, v in result["calculations"]]
    lines += ["", "## 处理逻辑", ""]
    lines += [f"{i}. {item}" for i, item in enumerate(result["logic"], 1)]
    lines += ["", "## 交付内容", ""]
    lines += [f"- {item}" for item in result["outputs"]]
    lines += ["", "## 使用边界", ""]
    lines += [f"- {item}" for item in result["boundary"]]
    lines += ["", CTA]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    text = render_markdown(run(payload))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
工伤赔偿计算引擎
=====================================================
输入：伤残等级、本人工资、统筹地区社平工资、是否解除劳动关系、是否参保
输出：结构化 JSON（逐项金额 + 算式 + 支付主体 + 法律依据）+ 可读报告 + A4 打印版 HTML

依据《工伤保险条例》（国务院令第 586 号修订）、《社会保险法》通用规则。

本引擎最核心的设计：**每一笔钱都标注支付主体**。
工伤待遇由两个口袋出钱，很多人只知道总数不知道找谁要，结果漏掉一整块：

  工伤保险基金支付：一次性伤残补助金、1-4 级伤残津贴、生活护理费、
                    一次性工伤医疗补助金、丧葬补助金、供养亲属抚恤金、一次性工亡补助金
  用人单位支付：    停工留薪期工资、停工留薪期护理、5-6 级伤残津贴（难以安排工作时）、
                    一次性伤残就业补助金
  单位未参保：      上述全部由用人单位承担（《工伤保险条例》第 62 条）

另一个关键区分：**一次性待遇与按月待遇不能混加**。
伤残津贴、生活护理费、供养亲属抚恤金是长期按月发放的，本引擎单独列出月标准，
不并入一次性合计，避免给出一个看起来很大却拿不到的数字。

作者：InchStep 寸进产品实验室
"""

import os
import sys
import json
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from report import render_html, save_html
except Exception:
    render_html = None
    save_html = None


# ---------------------------------------------------------------------------
# 法定标准表
# ---------------------------------------------------------------------------

# 一次性伤残补助金（本人工资月数）—— 工伤保险基金支付
LUMP_SUM_DISABILITY = {1: 27, 2: 25, 3: 23, 4: 21, 5: 18,
                       6: 16, 7: 13, 8: 11, 9: 9, 10: 7}

# 伤残津贴比例（本人工资百分比）
# 1-4 级由基金按月支付；5-6 级在难以安排工作时由单位按月支付
DISABILITY_ALLOWANCE = {1: 0.90, 2: 0.85, 3: 0.80, 4: 0.75, 5: 0.70, 6: 0.60}

# 生活护理费（统筹地区上年度职工月平均工资百分比）—— 基金按月支付
CARE_LEVEL = {"full": (0.50, "生活完全不能自理"),
              "most": (0.40, "生活大部分不能自理"),
              "part": (0.30, "生活部分不能自理")}

# 一次性工伤医疗补助金参考月数 —— 基金支付，5-10 级解除劳动关系时触发
# 各省《工伤保险条例》实施办法规定不同，此处取多省常见中位值，须按本省标准覆盖
MEDICAL_SUBSIDY_MONTHS = {5: 18, 6: 16, 7: 13, 8: 11, 9: 9, 10: 7}

# 一次性伤残就业补助金参考月数 —— 用人单位支付，5-10 级解除劳动关系时触发
EMPLOYMENT_SUBSIDY_MONTHS = {5: 30, 6: 25, 7: 20, 8: 15, 9: 10, 10: 5}

FUND = "工伤保险基金"
EMPLOYER = "用人单位"


def new_case() -> Dict[str, Any]:
    return {
        "case_name": "工伤赔偿待遇测算",
        "case_type": "disability",       # disability 伤残 / death 工亡
        "disability_level": 10,           # 1-10 级
        "monthly_salary": 8000.0,         # 本人工资：受伤前 12 个月平均月缴费工资
        "local_avg_salary": 9000.0,       # 统筹地区上年度职工月平均工资
        "local_min_wage": 2200.0,         # 当地最低工资（1-4 级伤残津贴的保底）

        "insured": True,                  # 单位是否依法缴纳工伤保险
        "terminate_relation": False,      # 是否解除或终止劳动关系（5-10 级触发两项补助金）

        "recovery_months": 3,             # 停工留薪期月数（一般不超过 12 个月）
        "care_during_recovery": False,    # 停工留薪期是否需要护理
        "care_level": None,               # full / most / part，评定护理等级后按月享受

        "medical_cost_self_paid": 0.0,    # 已自付的工伤医疗费（可申请基金报销的部分）
        "assistive_device_cost": 0.0,     # 辅助器具配置费
        "appraisal_cost": 0.0,            # 劳动能力鉴定费

        # 各省标准覆盖（不填则用上表参考值）
        "medical_subsidy_months": None,
        "employment_subsidy_months": None,
        "subsidy_base": "local_avg",      # local_avg 按社平工资 / self 按本人工资

        # 工亡专用
        "national_urban_income": 51821.0,  # 上一年度全国城镇居民人均可支配收入
        "dependents": [],                  # [{"name":"配偶","rate":0.40,"orphan":False}]
    }


# ---------------------------------------------------------------------------
# 本人工资的封顶与保底
# ---------------------------------------------------------------------------

def normalize_salary(c: Dict[str, Any]) -> Dict[str, Any]:
    """
    本人工资 = 因工作遭受事故伤害前 12 个月平均月缴费工资。
    高于统筹地区职工平均工资 300% 的，按 300% 计；低于 60% 的，按 60% 计。
    """
    raw = float(c["monthly_salary"])
    avg = float(c["local_avg_salary"])
    cap = avg * 3
    floor = avg * 0.6
    if raw > cap:
        return {"base": round(cap, 2), "raw": raw,
                "note": "本人工资 %.0f 元高于统筹地区职工月平均工资的 300%%（%.0f 元），"
                        "按 300%% 封顶计算" % (raw, cap)}
    if raw < floor:
        return {"base": round(floor, 2), "raw": raw,
                "note": "本人工资 %.0f 元低于统筹地区职工月平均工资的 60%%（%.0f 元），"
                        "按 60%% 保底计算" % (raw, floor)}
    return {"base": round(raw, 2), "raw": raw,
            "note": "本人工资 %.0f 元在统筹地区职工月平均工资的 60%%-300%% 区间内，据实计算" % raw}


# ---------------------------------------------------------------------------
# 待遇计算
# ---------------------------------------------------------------------------

def _item(name, amount, formula, payer, basis, kind="once"):
    """kind: once 一次性 / monthly 按月发放"""
    return {"name": name, "amount": round(float(amount), 2), "formula": formula,
            "payer": payer, "basis": basis, "kind": kind}


def calc_disability(c: Dict[str, Any], base: float) -> List[Dict[str, Any]]:
    items = []
    lv = int(c["disability_level"])
    avg = float(c["local_avg_salary"])
    insured = bool(c.get("insured", True))
    fund_payer = FUND if insured else EMPLOYER + "（未参保，依《工伤保险条例》第 62 条由单位承担）"

    # 一次性伤残补助金
    months = LUMP_SUM_DISABILITY[lv]
    items.append(_item(
        "一次性伤残补助金", base * months,
        "本人工资 %.0f × %d 个月（%d 级）" % (base, months, lv),
        fund_payer, "《工伤保险条例》第 35-37 条"))

    # 停工留薪期工资（原工资福利待遇不变，由单位按月支付）
    rm = float(c.get("recovery_months") or 0)
    if rm > 0:
        raw = float(c["monthly_salary"])   # 停工留薪期按原工资，不适用 300%/60% 折算
        items.append(_item(
            "停工留薪期工资", raw * rm,
            "原工资 %.0f × %.0f 个月（原工资福利待遇不变，一般不超过 12 个月，"
            "伤情严重经鉴定委员会确认可延长不超过 12 个月）" % (raw, rm),
            EMPLOYER, "《工伤保险条例》第 33 条"))
        if c.get("care_during_recovery"):
            items.append(_item(
                "停工留薪期护理费", 0,
                "生活不能自理的，停工留薪期内的护理由所在单位负责（按实际发生或雇工标准核算）",
                EMPLOYER, "《工伤保险条例》第 33 条"))

    # 伤残津贴（按月）
    if lv <= 4:
        rate = DISABILITY_ALLOWANCE[lv]
        allow = base * rate
        note = ""
        if allow < float(c.get("local_min_wage") or 0):
            note = "，低于当地最低工资标准 %.0f 元，由基金补足差额" % c["local_min_wage"]
        items.append(_item(
            "伤残津贴（按月）", allow,
            "本人工资 %.0f × %.0f%%（%d 级，保留劳动关系、退出工作岗位，按月发放至退休后转养老金）%s"
            % (base, rate * 100, lv, note),
            fund_payer, "《工伤保险条例》第 35 条", kind="monthly"))
    elif lv in (5, 6):
        rate = DISABILITY_ALLOWANCE[lv]
        items.append(_item(
            "伤残津贴（按月，难以安排工作时）", base * rate,
            "本人工资 %.0f × %.0f%%（%d 级，由单位安排适当工作；难以安排工作的，"
            "由单位按月发放伤残津贴）" % (base, rate * 100, lv),
            EMPLOYER, "《工伤保险条例》第 36 条", kind="monthly"))

    # 生活护理费（按月）
    cl = c.get("care_level")
    if cl in CARE_LEVEL:
        rate, desc = CARE_LEVEL[cl]
        items.append(_item(
            "生活护理费（按月）", avg * rate,
            "统筹地区上年度职工月平均工资 %.0f × %.0f%%（%s，经劳动能力鉴定委员会确认）"
            % (avg, rate * 100, desc),
            fund_payer, "《工伤保险条例》第 34 条", kind="monthly"))

    # 解除劳动关系触发的两项一次性补助金（5-10 级）
    if c.get("terminate_relation") and 5 <= lv <= 10:
        sub_base = avg if c.get("subsidy_base", "local_avg") == "local_avg" else base
        sub_base_name = "统筹地区上年度职工月平均工资" if c.get("subsidy_base", "local_avg") == "local_avg" else "本人工资"

        m_med = c.get("medical_subsidy_months") or MEDICAL_SUBSIDY_MONTHS[lv]
        items.append(_item(
            "一次性工伤医疗补助金", sub_base * m_med,
            "%s %.0f × %d 个月（参考值，各省标准不同，须按本省实施办法核定）"
            % (sub_base_name, sub_base, m_med),
            fund_payer, "《工伤保险条例》第 37 条 + 各省实施办法"))

        m_emp = c.get("employment_subsidy_months") or EMPLOYMENT_SUBSIDY_MONTHS[lv]
        items.append(_item(
            "一次性伤残就业补助金", sub_base * m_emp,
            "%s %.0f × %d 个月（参考值，各省标准不同，由用人单位支付）"
            % (sub_base_name, sub_base, m_emp),
            EMPLOYER, "《工伤保险条例》第 37 条 + 各省实施办法"))

    # 其他费用
    if c.get("medical_cost_self_paid"):
        items.append(_item(
            "工伤医疗费（可报销部分）", c["medical_cost_self_paid"],
            "符合工伤保险诊疗项目目录、药品目录、住院服务标准的，从基金支付",
            fund_payer, "《工伤保险条例》第 30 条"))
    if c.get("assistive_device_cost"):
        items.append(_item(
            "辅助器具配置费", c["assistive_device_cost"],
            "经鉴定委员会确认，按国家规定标准从基金支付",
            fund_payer, "《工伤保险条例》第 32 条"))
    if c.get("appraisal_cost"):
        items.append(_item(
            "劳动能力鉴定费", c["appraisal_cost"],
            "初次鉴定费用由基金支付（未参保的由单位支付）",
            fund_payer, "《工伤保险条例》第 26 条"))

    return items


def calc_death(c: Dict[str, Any], base: float) -> List[Dict[str, Any]]:
    items = []
    avg = float(c["local_avg_salary"])
    insured = bool(c.get("insured", True))
    fund_payer = FUND if insured else EMPLOYER + "（未参保，依《工伤保险条例》第 62 条由单位承担）"

    items.append(_item(
        "丧葬补助金", avg * 6,
        "统筹地区上年度职工月平均工资 %.0f × 6 个月" % avg,
        fund_payer, "《工伤保险条例》第 39 条"))

    income = float(c.get("national_urban_income") or 0)
    items.append(_item(
        "一次性工亡补助金", income * 20,
        "上一年度全国城镇居民人均可支配收入 %.0f × 20 倍（全国统一标准，每年随统计数据更新）" % income,
        fund_payer, "《工伤保险条例》第 39 条"))

    total_rate = 0.0
    for d in c.get("dependents", []):
        rate = float(d.get("rate", 0.30))
        if d.get("orphan"):
            rate += 0.10
        total_rate += rate
    # 抚恤金总和不得高于因工死亡职工生前的本人工资
    scale = 1.0
    cap_note = ""
    if total_rate > 1.0:
        scale = 1.0 / total_rate
        cap_note = "（各亲属核定比例合计 %.0f%% 已超过本人工资，按比例等额下调至 100%%）" % (total_rate * 100)
    for d in c.get("dependents", []):
        rate = float(d.get("rate", 0.30))
        extra = " + 孤寡老人或孤儿加发 10%" if d.get("orphan") else ""
        if d.get("orphan"):
            rate += 0.10
        eff = rate * scale
        items.append(_item(
            "供养亲属抚恤金 · %s（按月）" % d.get("name", "亲属"), base * eff,
            "本人工资 %.0f × %.1f%%%s%s" % (base, eff * 100, extra, cap_note),
            fund_payer, "《工伤保险条例》第 39 条", kind="monthly"))

    return items


def run(c: Dict[str, Any]) -> Dict[str, Any]:
    sal = normalize_salary(c)
    base = sal["base"]
    if c.get("case_type") == "death":
        items = calc_death(c, base)
    else:
        items = calc_disability(c, base)

    once = [i for i in items if i["kind"] == "once"]
    monthly = [i for i in items if i["kind"] == "monthly"]

    by_fund = sum(i["amount"] for i in once if i["payer"].startswith(FUND))
    by_emp = sum(i["amount"] for i in once if not i["payer"].startswith(FUND))
    total_once = sum(i["amount"] for i in once)
    total_monthly = sum(i["amount"] for i in monthly)

    return {
        "case_name": c.get("case_name", "工伤赔偿待遇测算"),
        "input_summary": {
            "case_type": "工亡" if c.get("case_type") == "death" else "工伤致残",
            "disability_level": c.get("disability_level"),
            "salary_base": base,
            "salary_note": sal["note"],
            "local_avg_salary": c["local_avg_salary"],
            "insured": "已参保" if c.get("insured", True) else "未参保（全部待遇由单位承担）",
            "terminate": "已解除/终止劳动关系" if c.get("terminate_relation") else "保留劳动关系",
        },
        "items": items,
        "total": {
            "once": round(total_once, 2),
            "by_fund": round(by_fund, 2),
            "by_employer": round(by_emp, 2),
            "monthly": round(total_monthly, 2),
        },
    }


# ---------------------------------------------------------------------------
# 文本报告
# ---------------------------------------------------------------------------

def to_report(r: Dict[str, Any]) -> str:
    i = r["input_summary"]
    t = r["total"]
    L = ["【%s】" % r["case_name"], ""]
    L.append("一、计算基数")
    L.append("情形：%s%s · %s · %s" % (
        i["case_type"],
        "（%s级）" % i["disability_level"] if i["case_type"] == "工伤致残" else "",
        i["insured"], i["terminate"]))
    L.append("本人工资基数：%.0f 元" % i["salary_base"])
    L.append("说明：%s" % i["salary_note"])
    L.append("")
    L.append("二、一次性待遇（可一次性主张的金额）")
    for it in r["items"]:
        if it["kind"] != "once":
            continue
        L.append("· %s：%.0f 元    【由 %s 支付】" % (it["name"], it["amount"], it["payer"]))
        L.append("      算式：%s" % it["formula"])
        L.append("      依据：%s" % it["basis"])
    L.append("")
    L.append("一次性合计：%.0f 元" % t["once"])
    L.append("      其中工伤保险基金支付 %.0f 元，用人单位支付 %.0f 元" % (t["by_fund"], t["by_employer"]))
    monthly = [x for x in r["items"] if x["kind"] == "monthly"]
    if monthly:
        L.append("")
        L.append("三、按月长期待遇（不计入一次性合计）")
        for it in monthly:
            L.append("· %s：%.0f 元/月    【由 %s 支付】" % (it["name"], it["amount"], it["payer"]))
            L.append("      算式：%s" % it["formula"])
        L.append("按月待遇合计：%.0f 元/月" % t["monthly"])
    return "\n".join(L)


# ---------------------------------------------------------------------------
# A4 报告
# ---------------------------------------------------------------------------

def to_html_report(r: Dict[str, Any], out_path: str = "工伤赔偿测算报告.html") -> str:
    if render_html is None:
        raise RuntimeError("report.py 未找到，无法生成 HTML 报告")
    i = r["input_summary"]
    t = r["total"]

    meta = [
        ("案件标识", r["case_name"]),
        ("情形", i["case_type"] + ("（%s 级伤残）" % i["disability_level"]
                                   if i["case_type"] == "工伤致残" else "")),
        ("参保状态", i["insured"]),
        ("劳动关系", i["terminate"]),
        ("本人工资基数", "%.0f 元" % i["salary_base"]),
        ("基数说明", i["salary_note"]),
        ("统筹地区社平工资", "%.0f 元/月" % i["local_avg_salary"]),
    ]

    once_rows = []
    for it in r["items"]:
        if it["kind"] != "once":
            continue
        once_rows.append([it["name"], "{:,.0f}".format(it["amount"]),
                          it["payer"], it["formula"], it["basis"]])
    once_rows.append(["一次性待遇合计", "{:,.0f}".format(t["once"]),
                      "基金 {:,.0f} ／ 单位 {:,.0f}".format(t["by_fund"], t["by_employer"]),
                      "—", "—"])

    sections = [
        {"kind": "table", "title": "一、一次性待遇明细",
         "headers": ["项目", "金额（元）", "支付主体", "计算方式", "法律依据"],
         "rows": once_rows, "num_cols": [1], "total_row_index": -1},
    ]

    monthly = [x for x in r["items"] if x["kind"] == "monthly"]
    if monthly:
        m_rows = [[m["name"], "{:,.0f}".format(m["amount"]), m["payer"], m["formula"]]
                  for m in monthly]
        m_rows.append(["按月待遇合计", "{:,.0f}".format(t["monthly"]), "—", "长期按月发放"])
        sections.append({"kind": "table", "title": "二、按月长期待遇",
                         "headers": ["项目", "月标准（元）", "支付主体", "计算方式"],
                         "rows": m_rows, "num_cols": [1], "total_row_index": -1})
        sections.append({"kind": "callout", "label": "为什么按月待遇单独列",
                         "body": "伤残津贴、生活护理费、供养亲属抚恤金是长期按月发放的，"
                                 "不能并入一次性金额去谈。把它们加进总数，谈判时容易被对方"
                                 "用一个折价的一次性数字打发掉。"})

    sections.append({"kind": "callout", "label": "钱从哪来（工伤最容易漏的一块）",
                     "body": "一次性伤残补助金、一次性工伤医疗补助金由工伤保险基金支付；"
                             "停工留薪期工资、一次性伤残就业补助金由用人单位支付。"
                             "只向单位要或只向社保要，都会漏掉另一半。"
                             "单位没有依法参保的，全部待遇由单位承担。"})

    sections.append({"kind": "list", "title": "三、办理路径",
                     "items": [
                         "事故发生后 30 日内，由用人单位向统筹地区社会保险行政部门申请工伤认定；"
                         "单位不申请的，职工本人或近亲属、工会组织可在事故发生之日起 1 年内直接申请。",
                         "工伤认定书下达后，伤情相对稳定或治疗终结时，向设区的市级劳动能力鉴定委员会"
                         "申请劳动能力鉴定，确定伤残等级和护理依赖程度。",
                         "凭工伤认定书和鉴定结论向社保经办机构申领基金支付的各项待遇。",
                         "向用人单位主张停工留薪期工资和一次性伤残就业补助金；"
                         "单位拒付的，向劳动监察部门投诉或申请劳动仲裁。",
                         "单位未参保的，全部待遇向单位主张，工伤认定书即为索赔依据。",
                     ]})

    sections.append({"kind": "callout", "label": "时间节点（错过就没了）",
                     "body": "工伤认定申请的时限是事故发生之日起 1 年，这是最硬的一条线，"
                             "超期后行政部门不予受理，只能转为人身损害赔偿之诉，举证难度和赔付标准都会变差。"
                             "劳动仲裁时效为 1 年，自知道权利被侵害之日起算。"})

    html = render_html(
        title="工伤保险待遇测算报告",
        subtitle="依据《工伤保险条例》《社会保险法》通用规则测算 · 供待遇申领与协商仲裁准备参考",
        meta=meta, sections=sections,
        disclaimer="本报告由计算引擎依据全国通用规则自动生成，不构成法律意见，也不代表最终核定结果。"
                   "一次性工伤医疗补助金与一次性伤残就业补助金的计发月数和计发基数由各省"
                   "《工伤保险条例》实施办法规定，省际差异很大，报告中采用的是多省常见参考值，"
                   "实际金额须以本省标准和社保经办机构核定为准。伤残等级须以劳动能力鉴定委员会"
                   "的鉴定结论为准。涉及工亡、一至四级伤残或单位拒不配合工伤认定的，建议委托律师。",
        footer_note="工伤赔偿计算器 · InchStep 寸进产品实验室")
    return save_html(html, out_path)


# ---------------------------------------------------------------------------
# 演示
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    demo = new_case()
    demo["case_name"] = "示例：九级工伤，治疗后离职结算"
    demo["disability_level"] = 9
    demo["monthly_salary"] = 8000
    demo["local_avg_salary"] = 9000
    demo["insured"] = True
    demo["terminate_relation"] = True
    demo["recovery_months"] = 4
    demo["medical_cost_self_paid"] = 6000
    demo["appraisal_cost"] = 500

    res = run(demo)
    print(to_report(res))
    print("\n--- 结构化 JSON（汇总）---")
    print(json.dumps(res["total"], ensure_ascii=False, indent=2))
    try:
        p = to_html_report(res, "工伤赔偿测算报告_示例.html")
        print("\nA4 报告已生成：%s" % p)
    except Exception as e:
        print("\n报告生成跳过：%s" % e)

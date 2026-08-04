# -*- coding: utf-8 -*-
"""
交通事故赔偿计算引擎
=====================================================
输入：伤情、误工护理天数、伤残等级、被扶养人、责任比例、当地收入标准
输出：结构化 JSON（逐项金额 + 算式 + 法律依据）+ 可读报告 + A4 打印版 HTML

依据《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》
（2022 年修正，已统一城乡赔偿标准为"居民人均可支配收入"）、
《民法典》侵权责任编、《机动车交通事故责任强制保险条例》通用规则。

三个决定结果的关键变量（差一个数，结果差几十万）：
  1. 伤残等级 → 赔偿系数（一级 100%，每降一级减 10%）
  2. 当地上年度居民人均可支配收入 → 残疾/死亡赔偿金基数
  3. 事故责任比例 → 最终折算

一条最容易被忽略的规则：
  交强险在责任限额内 **不按责任比例分摊**，先行全额赔付；
  只有超出交强险限额的部分，才按责任比例由商业险和侵权人承担。
  很多人一上来就把总额乘以责任比例，把交强险这一层白白让掉了。

作者：InchStep 寸进产品实验室
"""

import os
import sys
import json
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from report import render_html, save_html
except Exception:  # 报告模块缺失时不影响计算
    render_html = None
    save_html = None


# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

# 交强险责任限额（2020-09-19 起施行的新标准，单位：元）
JQX_WITH_FAULT = {"death_disability": 180000, "medical": 18000, "property": 2000}
JQX_NO_FAULT = {"death_disability": 18000, "medical": 1800, "property": 100}

# 精神损害抚慰金参考值（各地法院指导标准差异较大，此处取常见中位）
MENTAL_REF = {1: 80000, 2: 70000, 3: 60000, 4: 50000, 5: 40000,
              6: 30000, 7: 25000, 8: 20000, 9: 12000, 10: 8000}
MENTAL_DEATH = 80000

# 归入交强险「医疗费用赔偿限额」的项目
MEDICAL_KEYS = {"医疗费", "后续治疗费", "住院伙食补助费", "营养费"}


def new_case() -> Dict[str, Any]:
    """返回一份带默认值的空案件，便于按需覆盖字段。"""
    return {
        "case_name": "交通事故人身损害赔偿测算",
        "victim_age": 40,
        "injury_type": "disability",     # disability 伤残 / death 死亡 / minor 无伤残
        "disability_levels": [],          # 伤残等级列表，如 [7, 10, 10]
        "liability_ratio": 1.0,           # 对方（侵权人）责任比例 0~1
        "victim_has_fault": True,         # 受害方是否有责（影响交强险限额档位）

        # 当地标准（务必按事故发生地/受诉法院所在地上年度统计公报填写）
        "annual_disposable_income": 45000,   # 居民人均可支配收入（元/年）
        "annual_consumption": 30000,         # 居民人均消费支出（元/年）
        "avg_monthly_salary": 8000,          # 职工月平均工资（丧葬费基数）

        # 实际支出与天数
        "medical_cost": 0.0,
        "followup_medical": 0.0,
        "hospital_days": 0,
        "hospital_meal_std": 100.0,
        "nutrition_days": 0,
        "nutrition_std": 50.0,
        "lost_work_days": 0,
        "daily_income": 0.0,       # 留 0 则按人均可支配收入 / 365 计
        "nursing_days": 0,
        "nursing_daily": 150.0,
        "transport_cost": 0.0,
        "accommodation_cost": 0.0,
        "appraisal_cost": 0.0,
        "assistive_device_cost": 0.0,
        "property_loss": 0.0,

        # 被扶养人：type = minor 未成年 / adult 无劳动能力且无生活来源的成年人
        "dependents": [],   # [{"name":"儿子","age":8,"type":"minor","supporters":2}]

        "mental_damage": None,     # 不填按等级参考值
        "commercial_limit": 0.0,   # 商业三者险保额，0 表示无
    }


# ---------------------------------------------------------------------------
# 基础规则
# ---------------------------------------------------------------------------

def comp_years(age: int) -> int:
    """赔偿年限：60 周岁以下 20 年；60 岁以上每增 1 岁减 1 年；75 岁以上按 5 年。"""
    if age >= 75:
        return 5
    if age > 60:
        return max(5, 20 - (age - 60))
    return 20


def disability_coefficient(levels: List[int]) -> Dict[str, Any]:
    """
    伤残赔偿系数。
    单处：(11 - 等级) × 10%，即一级 100%、十级 10%。
    多处：以最高等级为基准，其余每处按 (11 - 等级)% 计附加指数，附加合计不超过 10%，
          基准 + 附加不超过 100%。
    """
    if not levels:
        return {"coef": 0.0, "top": None, "extra": 0.0, "note": "无伤残等级"}
    top = min(levels)                     # 数字越小等级越高
    base = (11 - top) * 0.10
    extra = 0.0
    # 最高等级作基准计一次，其余各处（含同级重复出现的）计附加指数
    others = list(levels)
    others.remove(top)
    for lv in others:
        extra += (11 - lv) * 0.01
    extra = min(extra, 0.10)
    coef = min(base + extra, 1.0)
    note = "%d 级伤残，基准系数 %.0f%%" % (top, base * 100)
    if others:
        note += "；另有 %d 处伤残，附加指数 %.0f%%（上限 10%%）" % (len(others), extra * 100)
    return {"coef": round(coef, 4), "top": top, "extra": extra, "note": note}


# ---------------------------------------------------------------------------
# 各项计算
# ---------------------------------------------------------------------------

def _item(name, amount, formula, basis, group="death_disability"):
    return {"name": name, "amount": round(float(amount), 2),
            "formula": formula, "basis": basis, "group": group}


def calc_items(c: Dict[str, Any]) -> List[Dict[str, Any]]:
    items = []
    income = float(c["annual_disposable_income"])
    consume = float(c["annual_consumption"])
    age = int(c["victim_age"])
    itype = c.get("injury_type", "disability")
    dc = disability_coefficient(c.get("disability_levels", []))
    coef = dc["coef"]

    # —— 医疗类（走交强险医疗费用限额）——
    if c.get("medical_cost"):
        items.append(_item("医疗费", c["medical_cost"],
                           "按医疗票据据实计算",
                           "人身损害赔偿司法解释第 6 条", "medical"))
    if c.get("followup_medical"):
        items.append(_item("后续治疗费", c["followup_medical"],
                           "按鉴定意见或医疗证明确定",
                           "人身损害赔偿司法解释第 6 条", "medical"))
    if c.get("hospital_days"):
        amt = c["hospital_days"] * c["hospital_meal_std"]
        items.append(_item("住院伙食补助费", amt,
                           "%d 天 × %.0f 元/天" % (c["hospital_days"], c["hospital_meal_std"]),
                           "人身损害赔偿司法解释第 8 条", "medical"))
    if c.get("nutrition_days"):
        amt = c["nutrition_days"] * c["nutrition_std"]
        items.append(_item("营养费", amt,
                           "%d 天 × %.0f 元/天（参照医疗机构意见）"
                           % (c["nutrition_days"], c["nutrition_std"]),
                           "人身损害赔偿司法解释第 9 条", "medical"))

    # —— 死亡伤残类（走交强险死亡伤残限额）——
    if c.get("lost_work_days"):
        daily = float(c.get("daily_income") or 0)
        if daily <= 0:
            daily = income / 365.0
            src = "无固定收入，按居民人均可支配收入 %.0f ÷ 365 折算日均 %.2f 元" % (income, daily)
        else:
            src = "按实际减少的收入，日均 %.2f 元" % daily
        amt = c["lost_work_days"] * daily
        items.append(_item("误工费", amt,
                           "%d 天 × %.2f 元/天（%s）" % (c["lost_work_days"], daily, src),
                           "人身损害赔偿司法解释第 7 条"))
    if c.get("nursing_days"):
        amt = c["nursing_days"] * c["nursing_daily"]
        items.append(_item("护理费", amt,
                           "%d 天 × %.0f 元/天（护工同等级别劳务报酬标准）"
                           % (c["nursing_days"], c["nursing_daily"]),
                           "人身损害赔偿司法解释第 8 条"))
    if c.get("transport_cost"):
        items.append(_item("交通费", c["transport_cost"],
                           "按就医与处理事故的实际必要支出票据计算",
                           "人身损害赔偿司法解释第 10 条"))
    if c.get("accommodation_cost"):
        items.append(_item("住宿费", c["accommodation_cost"], "按实际必要支出票据计算",
                           "人身损害赔偿司法解释第 10 条"))
    if c.get("assistive_device_cost"):
        items.append(_item("残疾辅助器具费", c["assistive_device_cost"],
                           "按普通适用器具的合理费用标准计算",
                           "人身损害赔偿司法解释第 12 条"))
    if c.get("appraisal_cost"):
        items.append(_item("鉴定费", c["appraisal_cost"], "按实际支出票据计算",
                           "诉讼费用交纳办法"))

    years = comp_years(age)

    if itype == "death":
        amt = income * years
        items.append(_item("死亡赔偿金", amt,
                           "居民人均可支配收入 %.0f × %d 年（%d 周岁）" % (income, years, age),
                           "人身损害赔偿司法解释第 15 条"))
        fun = c["avg_monthly_salary"] * 6
        items.append(_item("丧葬费", fun,
                           "职工月平均工资 %.0f × 6 个月" % c["avg_monthly_salary"],
                           "人身损害赔偿司法解释第 14 条"))
    elif itype == "disability" and coef > 0:
        amt = income * years * coef
        items.append(_item("残疾赔偿金", amt,
                           "居民人均可支配收入 %.0f × %d 年 × 伤残系数 %.0f%%（%s）"
                           % (income, years, coef * 100, dc["note"]),
                           "人身损害赔偿司法解释第 12 条"))

    # 被扶养人生活费（2022 修正后计入残疾赔偿金 / 死亡赔偿金）
    for d in c.get("dependents", []):
        d_age = int(d.get("age", 0))
        sup = max(1, int(d.get("supporters", 1)))
        if d.get("type") == "minor":
            d_years = max(0, 18 - d_age)
            yr_note = "至 18 周岁尚需 %d 年" % d_years
        else:
            d_years = comp_years(d_age)
            yr_note = "%d 周岁，计 %d 年" % (d_age, d_years)
        if d_years <= 0:
            continue
        k = coef if itype == "disability" else 1.0
        amt = consume * d_years / sup * k
        items.append(_item(
            "被扶养人生活费（%s）" % d.get("name", "被扶养人"), amt,
            "居民人均消费支出 %.0f × %d 年 ÷ %d 名扶养人%s（%s）"
            % (consume, d_years, sup,
               " × 伤残系数 %.0f%%" % (coef * 100) if itype == "disability" else "", yr_note),
            "人身损害赔偿司法解释第 17 条"))

    # 精神损害抚慰金
    mental = c.get("mental_damage")
    if mental is None:
        if itype == "death":
            mental = MENTAL_DEATH
            m_note = "死亡案件参考值（各地法院指导标准 5-10 万）"
        elif dc["top"]:
            mental = MENTAL_REF.get(dc["top"], 0)
            m_note = "%d 级伤残参考值（各地指导标准不一，可上下浮动）" % dc["top"]
        else:
            mental = 0
            m_note = ""
    else:
        m_note = "按用户指定金额"
    if mental:
        items.append(_item("精神损害抚慰金", mental, m_note,
                           "民法典第 1183 条 / 精神损害赔偿司法解释"))

    return items


# ---------------------------------------------------------------------------
# 责任比例与交强险分层
# ---------------------------------------------------------------------------

def apply_liability(items: List[Dict[str, Any]], c: Dict[str, Any]) -> Dict[str, Any]:
    """
    分层结算：
      第一层 交强险（不分责任比例，限额内全额赔）
      第二层 超出交强险的部分 × 对方责任比例 → 商业三者险赔付
      第三层 商业险不足部分 → 侵权人自行承担
    """
    ratio = float(c.get("liability_ratio", 1.0))
    limits = JQX_WITH_FAULT if c.get("victim_has_fault", True) else JQX_NO_FAULT

    med_total = sum(i["amount"] for i in items if i["group"] == "medical")
    dd_total = sum(i["amount"] for i in items if i["group"] == "death_disability")
    total = med_total + dd_total

    jqx_med = min(med_total, limits["medical"])
    jqx_dd = min(dd_total, limits["death_disability"])
    jqx = jqx_med + jqx_dd

    over = total - jqx
    liable = over * ratio

    commercial_limit = float(c.get("commercial_limit") or 0)
    by_commercial = min(liable, commercial_limit)
    by_person = liable - by_commercial

    prop = float(c.get("property_loss") or 0)
    jqx_prop = min(prop, limits["property"]) if prop else 0.0
    prop_over = max(0.0, prop - jqx_prop) * ratio

    return {
        "medical_group_total": round(med_total, 2),
        "death_disability_group_total": round(dd_total, 2),
        "grand_total": round(total, 2),
        "jqx_medical": round(jqx_med, 2),
        "jqx_death_disability": round(jqx_dd, 2),
        "jqx_total": round(jqx, 2),
        "over_limit": round(over, 2),
        "liability_ratio": ratio,
        "liable_after_ratio": round(liable, 2),
        "by_commercial": round(by_commercial, 2),
        "by_person": round(by_person, 2),
        "actual_recover": round(jqx + liable, 2),
        "property_loss": round(prop, 2),
        "property_jqx": round(jqx_prop, 2),
        "property_over_ratio": round(prop_over, 2),
        "limits_used": "有责限额" if c.get("victim_has_fault", True) else "无责限额",
    }


def run(c: Dict[str, Any]) -> Dict[str, Any]:
    items = calc_items(c)
    settle = apply_liability(items, c)
    dc = disability_coefficient(c.get("disability_levels", []))
    return {
        "case_name": c.get("case_name", "交通事故赔偿测算"),
        "input_summary": {
            "victim_age": c["victim_age"],
            "injury_type": {"disability": "伤残", "death": "死亡", "minor": "仅治疗未构成伤残"}
                           .get(c.get("injury_type"), "伤残"),
            "disability_levels": c.get("disability_levels", []),
            "coefficient_note": dc["note"],
            "comp_years": comp_years(int(c["victim_age"])),
            "liability_ratio": "%.0f%%" % (float(c.get("liability_ratio", 1.0)) * 100),
            "income_std": c["annual_disposable_income"],
            "consumption_std": c["annual_consumption"],
        },
        "items": items,
        "settlement": settle,
    }


# ---------------------------------------------------------------------------
# 文本报告
# ---------------------------------------------------------------------------

def to_report(r: Dict[str, Any]) -> str:
    s = r["settlement"]
    L = ["【%s】" % r["case_name"], ""]
    L.append("一、基本情况")
    i = r["input_summary"]
    L.append("受害人 %s 周岁 · %s · %s" % (i["victim_age"], i["injury_type"], i["coefficient_note"]))
    L.append("赔偿年限 %d 年 · 对方责任比例 %s" % (i["comp_years"], i["liability_ratio"]))
    L.append("基数：居民人均可支配收入 %.0f 元/年，人均消费支出 %.0f 元/年"
             % (i["income_std"], i["consumption_std"]))
    L.append("")
    L.append("二、损失项目明细")
    for it in r["items"]:
        tag = "[医疗类]" if it["group"] == "medical" else "[伤残类]"
        L.append("%s %s：%.0f 元" % (tag, it["name"], it["amount"]))
        L.append("      算式：%s" % it["formula"])
        L.append("      依据：%s" % it["basis"])
    L.append("")
    L.append("损失合计：%.0f 元（其中医疗类 %.0f，死亡伤残类 %.0f）"
             % (s["grand_total"], s["medical_group_total"], s["death_disability_group_total"]))
    L.append("")
    L.append("三、赔付分层（关键：交强险不按责任比例分摊）")
    L.append("第一层 交强险（%s）：%.0f 元" % (s["limits_used"], s["jqx_total"]))
    L.append("      医疗费用限额内 %.0f 元 + 死亡伤残限额内 %.0f 元，限额内全额赔付，不打责任折扣"
             % (s["jqx_medical"], s["jqx_death_disability"]))
    L.append("第二层 超出交强险 %.0f 元 × 责任比例 %s = %.0f 元"
             % (s["over_limit"], s["liability_ratio"] and "%.0f%%" % (s["liability_ratio"] * 100),
                s["liable_after_ratio"]))
    L.append("      其中商业三者险承担 %.0f 元，侵权人自行承担 %.0f 元"
             % (s["by_commercial"], s["by_person"]))
    if s["property_loss"]:
        L.append("财产损失 %.0f 元：交强险财产限额内 %.0f 元 + 超出部分按责任比例 %.0f 元"
                 % (s["property_loss"], s["property_jqx"], s["property_over_ratio"]))
    L.append("")
    L.append("四、实际可获赔偿：%.0f 元" % s["actual_recover"])
    return "\n".join(L)


# ---------------------------------------------------------------------------
# A4 报告
# ---------------------------------------------------------------------------

def to_html_report(r: Dict[str, Any], out_path: str = "交通事故赔偿测算报告.html") -> str:
    if render_html is None:
        raise RuntimeError("report.py 未找到，无法生成 HTML 报告")
    s = r["settlement"]
    i = r["input_summary"]

    meta = [
        ("案件标识", r["case_name"]),
        ("受害人年龄", "%s 周岁" % i["victim_age"]),
        ("伤情", i["injury_type"]),
        ("伤残系数", i["coefficient_note"]),
        ("赔偿年限", "%d 年" % i["comp_years"]),
        ("对方责任比例", i["liability_ratio"]),
        ("收入基数", "居民人均可支配收入 %.0f 元/年" % i["income_std"]),
        ("消费基数", "居民人均消费支出 %.0f 元/年" % i["consumption_std"]),
    ]

    rows = []
    for it in r["items"]:
        rows.append([
            ("医疗类 · " if it["group"] == "medical" else "") + it["name"],
            "{:,.0f}".format(it["amount"]),
            it["formula"],
            it["basis"],
        ])
    rows.append(["损失合计", "{:,.0f}".format(s["grand_total"]),
                 "医疗类 {:,.0f} + 死亡伤残类 {:,.0f}".format(
                     s["medical_group_total"], s["death_disability_group_total"]), "—"])

    settle_rows = [
        ["第一层：交强险（%s）" % s["limits_used"], "{:,.0f}".format(s["jqx_total"]),
         "医疗费用限额内 {:,.0f} + 死亡伤残限额内 {:,.0f}，限额内全额赔付，不按责任比例打折".format(
             s["jqx_medical"], s["jqx_death_disability"])],
        ["第二层：超限额部分按责任比例", "{:,.0f}".format(s["liable_after_ratio"]),
         "超出交强险 {:,.0f} × 责任比例 {:.0%}".format(s["over_limit"], s["liability_ratio"])],
        ["　—— 商业三者险承担", "{:,.0f}".format(s["by_commercial"]), "在保额范围内由保险公司支付"],
        ["　—— 侵权人自行承担", "{:,.0f}".format(s["by_person"]), "超出商业险保额或无商业险的部分"],
        ["实际可获赔偿合计", "{:,.0f}".format(s["actual_recover"]), "交强险 + 按责任比例分担部分"],
    ]

    sections = [
        {"kind": "table", "title": "一、损失项目明细",
         "headers": ["项目", "金额（元）", "计算方式", "法律依据"],
         "rows": rows, "num_cols": [1], "total_row_index": -1},
        {"kind": "table", "title": "二、赔付分层结算",
         "headers": ["层级", "金额（元）", "说明"],
         "rows": settle_rows, "num_cols": [1], "total_row_index": -1},
        {"kind": "callout", "label": "最容易被忽略的一条",
         "body": "交强险在责任限额内不按责任比例分摊，由保险公司先行全额赔付；只有超出交强险限额的"
                 "部分，才按事故责任比例由商业三者险和侵权人承担。直接拿损失总额乘以责任比例，"
                 "等于把交强险这一层白白让掉了。"},
        {"kind": "list", "title": "三、主张路径",
         "items": [
             "先向交警部门申领《道路交通事故认定书》，责任比例以认定书为准，对认定有异议可在三日内申请复核。",
             "伤情稳定后（一般为治疗终结或出院后三个月）到有资质的司法鉴定机构做伤残等级鉴定，"
             "等级直接决定残疾赔偿金，是全案金额最大的变量。",
             "医疗票据、误工证明（单位工资流水或个体经营收入凭证）、护理凭证、交通票据逐项归集，"
             "没有票据的项目法院一般不予支持。",
             "先向承保交强险的保险公司主张限额内赔付，再就超出部分与商业险公司、侵权人协商或起诉。",
             "协商不成向事故发生地或被告住所地人民法院提起机动车交通事故责任纠纷之诉，"
             "可将保险公司列为共同被告。",
         ]},
        {"kind": "callout", "label": "时效提醒",
         "body": "人身损害赔偿的诉讼时效为三年，自知道或应当知道权利受损害之日起算；"
                 "伤残鉴定结论作出之日通常被视为损失确定之日。另需注意保险公司的报案时限要求，"
                 "逾期报案可能影响商业险理赔。"},
    ]

    html = render_html(
        title="交通事故人身损害赔偿测算报告",
        subtitle="依据《民法典》侵权责任编、人身损害赔偿司法解释（2022 修正）及交强险条例通用规则测算 · "
                 "供理赔协商与诉讼准备参考",
        meta=meta, sections=sections,
        disclaimer="本报告由计算引擎依据全国通用规则自动生成，不构成法律意见，也不代表最终判赔结果。"
                   "各省市对居民人均可支配收入、人均消费支出、精神损害抚慰金的具体标准每年更新且差异较大，"
                   "请以事故发生地或受诉法院所在地上年度统计公报及当地裁判口径为准。"
                   "伤残等级须以有资质机构出具的鉴定意见为准，本报告中的等级为用户自行输入。"
                   "涉及重伤、死亡或争议较大的案件，建议委托执业律师办理。",
        footer_note="交通事故赔偿计算器 · InchStep 寸进产品实验室")
    return save_html(html, out_path)


# ---------------------------------------------------------------------------
# 演示
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    demo = new_case()
    demo["case_name"] = "示例：城区追尾致十级伤残，对方负主要责任"
    demo["victim_age"] = 38
    demo["injury_type"] = "disability"
    demo["disability_levels"] = [10]
    demo["liability_ratio"] = 0.7
    demo["annual_disposable_income"] = 49283
    demo["annual_consumption"] = 32000
    demo["avg_monthly_salary"] = 9000
    demo["medical_cost"] = 46000
    demo["hospital_days"] = 21
    demo["hospital_meal_std"] = 100
    demo["nutrition_days"] = 60
    demo["lost_work_days"] = 120
    demo["daily_income"] = 300
    demo["nursing_days"] = 30
    demo["nursing_daily"] = 180
    demo["transport_cost"] = 2200
    demo["appraisal_cost"] = 1800
    demo["dependents"] = [{"name": "女儿", "age": 9, "type": "minor", "supporters": 2}]
    demo["commercial_limit"] = 1000000

    res = run(demo)
    print(to_report(res))
    print("\n--- 结构化 JSON（节选）---")
    print(json.dumps(res["settlement"], ensure_ascii=False, indent=2))
    try:
        p = to_html_report(res, "交通事故赔偿测算报告_示例.html")
        print("\nA4 报告已生成：%s" % p)
    except Exception as e:
        print("\n报告生成跳过：%s" % e)

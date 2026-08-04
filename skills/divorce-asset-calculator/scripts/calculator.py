# -*- coding: utf-8 -*-
"""
离婚财产计算器 —— 计算引擎
================================
输入结构化资产/债务信息，输出结构化的离婚财产分割明细 + 谈判要点。

设计目标：
- 纯标准库，无第三方依赖，可在任意 Python 3.8+ 环境运行（含 SkillHub 云端沙箱）。
- 输出 JSON 结构清晰，便于将来封装为 Pay Skill 的 per_call 接口。
- 算法依据《民法典》及婚姻家庭编司法解释的通用规则，做"典型情形建模"，
  不覆盖所有个案（如过错赔偿、隐匿转移财产等特殊情形），并强制附带免责声明。

作者：InchStep 寸进产品实验室
"""

import json
from typing import List, Dict, Any, Optional


# ---------------------------------------------------------------------------
# 输入模型（由调用方构造，或未来由 Pay Skill 的前端表单转换而来）
# ---------------------------------------------------------------------------

def new_case() -> Dict[str, Any]:
    """返回一个空案例模板，方便调用方填充。"""
    return {
        "marriage_years": 0,          # 结婚年限（年）
        "real_estates": [],           # 房产列表
        "deposits": [],               # 存款列表
        "equities": [],               # 股权/投资列表
        "debts": [],                  # 债务列表
        "notes": "",                  # 其他需要说明的情形（如过错、约定财产制等）
    }


# ---------------------------------------------------------------------------
# 核心计算
# ---------------------------------------------------------------------------

def _cn(role: str) -> str:
    """把 husband/wife/both 等英文角色归一为中文，避免输出里混入英文。"""
    return {"husband": "男方", "wife": "女方", "both": "双方",
            "male": "男方", "female": "女方"}.get(role, role)


def calc_real_estate(re: Dict[str, Any]) -> Dict[str, Any]:
    """
    计算单套房产的分割方案。

    两种典型情形：
    1) post（婚后共同购买）：净值 = 现值 - 剩余贷款，原则上各 50%。
       归登记方所有，登记方补偿另一方净值的一半。
    2) pre（婚前一方首付并登记，婚后共同还贷）：
       房产归登记方，登记方承担剩余贷款；
       婚后共同还贷支付的款项及其相对应财产增值部分，由登记方对另一方补偿。
       补偿额 ≈ 共同还贷本息 × (1 + 增值率) ÷ 2
       其中增值率 = (现值 - 原购价) / 原购价
    """
    name = re.get("name", "未命名房产")
    value = float(re.get("current_value", 0))
    remaining = float(re.get("remaining_loan", 0))
    acquired = re.get("acquired", "post")

    result = {
        "asset": name,
        "type": "real_estate",
        "belongs_to": "",
        "market_value": value,
        "remaining_loan": remaining,
        "compensation_to_other": 0.0,
        "compensation_from_other": 0.0,
        "note": "",
    }

    if acquired == "post":
        # 婚后共同购买
        net = value - remaining
        owner = _cn(re.get("registered_owner", "共同"))
        result["belongs_to"] = owner
        result["compensation_to_other"] = round(net / 2, 2)
        result["note"] = (
            "婚后共同购买，属夫妻共同财产。净值 %.0f 元（现值 %.0f - 剩余贷款 %.0f），"
            "原则上各半分割。归%s所有，需补偿另一方 %.0f 元。"
            % (net, value, remaining, owner, net / 2)
        )
    else:
        # 婚前首付 + 婚后共同还贷
        original = float(re.get("original_price", value))
        joint = float(re.get("joint_repayment", 0))
        gain_rate = (value - original) / original if original > 0 else 0.0
        comp = joint * (1 + gain_rate) / 2.0
        owner = _cn(re.get("registered_owner", re.get("down_payer", "一方")))
        result["belongs_to"] = owner
        result["compensation_to_other"] = round(comp, 2)
        result["note"] = (
            "婚前%s支付首付并登记，婚后共同还贷。房产归%s；"
            "婚后共同还贷本息 %.0f 元及其增值（增值率 %.1f%%）作为共同财产，"
            "由%s补偿另一方 %.0f 元。首付及婚前增值部分属个人财产，不分割。"
            % (_cn(re.get("down_payer", "一方")), owner, joint, gain_rate * 100, owner, comp)
        )
    return result


def calc_deposit(d: Dict[str, Any]) -> Dict[str, Any]:
    """存款：婚后积累的属共同财产，各半；婚前指定的不分割。"""
    name = d.get("name", "存款")
    amount = float(d.get("amount", 0))
    acquired = d.get("acquired", "post")
    if acquired == "pre":
        return {
            "asset": name, "type": "deposit", "belongs_to": _cn(d.get("owner", "一方")),
            "market_value": amount, "compensation_to_other": 0.0,
            "compensation_from_other": 0.0,
            "note": "属婚前个人财产，不分割。",
        }
    half = amount / 2.0
    return {
        "asset": name, "type": "deposit", "belongs_to": "共同",
        "market_value": amount, "compensation_to_other": round(half, 2),
        "compensation_from_other": 0.0,
        "note": "婚后积累，属夫妻共同财产，各半分割（各 %.0f 元）。" % half,
    }


def calc_equity(e: Dict[str, Any]) -> Dict[str, Any]:
    """
    股权/投资：
    - post（婚后以共同财产取得）：整体属共同，净值各半。
    - pre（婚前取得，婚后增值）：仅婚后增值部分属共同，增值的一半补偿另一方。
    """
    name = e.get("name", "股权")
    value = float(e.get("value", 0))
    acquired = e.get("acquired", "post")
    if acquired == "post":
        half = value / 2.0
        return {
            "asset": name, "type": "equity", "belongs_to": "共同",
            "market_value": value, "compensation_to_other": round(half, 2),
            "compensation_from_other": 0.0,
            "note": "婚后以共同财产取得，属共同财产，各半分割（折价补偿 %.0f 元）。" % half,
        }
    else:
        gain = float(e.get("post_marriage_gain", 0))
        half_gain = gain / 2.0
        return {
            "asset": name, "type": "equity", "belongs_to": _cn(e.get("owner", "一方")),
            "market_value": value, "compensation_to_other": round(half_gain, 2),
            "compensation_from_other": 0.0,
            "note": "婚前取得属个人财产；婚后增值 %.0f 元部分属共同财产，补偿另一方 %.0f 元。" % (gain, half_gain),
        }


def calc_debt(debt: Dict[str, Any]) -> Dict[str, Any]:
    """
    债务：
    - joint：夫妻共同债务，各半承担。
    - personal_lien：房产剩余贷款，随房产归登记方（在房产计算中已扣除，此处仅记录）。
    - personal：一方个人债务，各自承担。
    """
    nature = debt.get("nature", "personal")
    amount = float(debt.get("amount", 0))
    name = debt.get("name", "债务")
    if nature == "joint":
        return {"name": name, "nature": "共同债务", "amount": amount,
                "each_share": amount / 2.0, "borne_by": "双方各半"}
    if nature == "personal_lien":
        return {"name": name, "nature": "房产附随贷款", "amount": amount,
                "each_share": 0.0, "borne_by": "随房产归登记方"}
    return {"name": name, "nature": "个人债务", "amount": amount,
            "each_share": 0.0, "borne_by": debt.get("owner", "举债方")}


# ---------------------------------------------------------------------------
# 汇总
# ---------------------------------------------------------------------------

def run(case: Dict[str, Any]) -> Dict[str, Any]:
    items = []
    husband_gets = 0.0
    wife_gets = 0.0
    husband_pay = 0.0
    wife_pay = 0.0
    husband_lien = 0.0
    wife_lien = 0.0

    # 房产
    for re in case.get("real_estates", []):
        r = calc_real_estate(re)
        items.append(r)
        owner = r["belongs_to"]
        if owner in ("男方", "husband", "夫"):
            husband_gets += r["market_value"]
            husband_pay += r["compensation_to_other"]
            wife_gets += r["compensation_to_other"]
            husband_lien += r.get("remaining_loan", 0)
        elif owner in ("女方", "wife", "妻"):
            wife_gets += r["market_value"]
            wife_pay += r["compensation_to_other"]
            husband_gets += r["compensation_to_other"]
            wife_lien += r.get("remaining_loan", 0)
        else:  # 共同
            husband_gets += r["market_value"] / 2
            wife_gets += r["market_value"] / 2

    # 存款
    for d in case.get("deposits", []):
        r = calc_deposit(d)
        items.append(r)
        if r["belongs_to"] == "共同":
            husband_gets += r["market_value"] / 2
            wife_gets += r["market_value"] / 2
        else:
            if r["belongs_to"] in ("男方", "husband", "夫"):
                husband_gets += r["market_value"]
            else:
                wife_gets += r["market_value"]

    # 股权
    for e in case.get("equities", []):
        r = calc_equity(e)
        items.append(r)
        if r["belongs_to"] == "共同":
            husband_gets += r["market_value"] / 2
            wife_gets += r["market_value"] / 2
        elif r["belongs_to"] in ("男方", "husband", "夫"):
            husband_gets += r["market_value"]
            husband_pay += r["compensation_to_other"]
            wife_gets += r["compensation_to_other"]
        else:
            wife_gets += r["market_value"]
            wife_pay += r["compensation_to_other"]
            husband_gets += r["compensation_to_other"]

    # 债务
    debt_lines = []
    husband_debt = 0.0
    wife_debt = 0.0
    for debt in case.get("debts", []):
        dl = calc_debt(debt)
        debt_lines.append(dl)
        if dl["borne_by"] == "双方各半":
            husband_debt += dl["each_share"]
            wife_debt += dl["each_share"]

    husband_net = husband_gets - husband_pay - husband_debt - husband_lien
    wife_net = wife_gets - wife_pay - wife_debt - wife_lien

    negotiation = build_negotiation_points(case, items, husband_net, wife_net)

    return {
        "marriage_years": case.get("marriage_years", 0),
        "items": items,
        "debts": debt_lines,
        "summary": {
            "husband": {
                "assets_value": round(husband_gets, 2),
                "pay_compensation": round(husband_pay, 2),
                "bear_debt": round(husband_debt, 2),
                "bear_lien": round(husband_lien, 2),
                "net": round(husband_net, 2),
            },
            "wife": {
                "assets_value": round(wife_gets, 2),
                "pay_compensation": round(wife_pay, 2),
                "bear_debt": round(wife_debt, 2),
                "bear_lien": round(wife_lien, 2),
                "net": round(wife_net, 2),
            },
        },
        "negotiation_points": negotiation,
        "disclaimer": DISCLAIMER,
    }


def build_negotiation_points(case, items, h_net, w_net) -> List[str]:
    pts = []
    for it in items:
        if it.get("compensation_to_other", 0) > 0:
            pts.append(
                "关于「%s」：%s" % (it["asset"], it["note"])
            )
    pts.append(
        "测算结论：男方净得约 %.0f 元，女方净得约 %.0f 元（已扣除应承担债务与应付补偿）。"
        % (h_net, w_net)
    )
    pts.append(
        "谈判建议：先就「房产归属 + 补偿金额」达成一致（这是金额最大、争议最多的一项），"
        "再用补偿金额去平衡存款、股权等其他项目，避免逐项拉锯。"
    )
    pts.append(
        "若一方存在隐藏、转移、变卖共同财产或重大过错，可依法主张少分或不分，并另行索赔，"
        "本测算未计入该情形，需结合证据另行评估。"
    )
    return pts


DISCLAIMER = (
    "本测算基于《民法典》及婚姻家庭编司法解释的通用规则，对典型情形做建模估算，"
    "不构成法律意见，也不能替代执业律师的专业判断。个案中涉及过错赔偿、财产约定制、"
    "隐匿转移财产、子女抚养费等情形时，结果会有重大差异。建议在签署任何协议前咨询律师。"
)


# ---------------------------------------------------------------------------
# 人类可读报告
# ---------------------------------------------------------------------------

def to_report(result: Dict[str, Any]) -> str:
    lines = []
    lines.append("【离婚财产分割测算】")
    lines.append("结婚年限：%s 年" % result["marriage_years"])
    lines.append("")
    lines.append("一、各项财产分割明细")
    for it in result["items"]:
        lines.append("- %s（%s）" % (it["asset"], it["type"]))
        lines.append("  归属：%s" % it["belongs_to"])
        lines.append("  现值：%.0f 元" % it["market_value"])
        if it["compensation_to_other"] > 0:
            lines.append("  需向另一方补偿：%.0f 元" % it["compensation_to_other"])
        lines.append("  依据：%s" % it["note"])
        lines.append("")
    if result["debts"]:
        lines.append("二、债务承担")
        for d in result["debts"]:
            lines.append("- %s：%s，金额 %.0f 元，%s" % (d["name"], d["nature"], d["amount"], d["borne_by"]))
        lines.append("")
    lines.append("三、双方净得汇总")
    h = result["summary"]["husband"]
    w = result["summary"]["wife"]
    lines.append("男方：分得资产 %.0f - 应付补偿 %.0f - 承担债务 %.0f - 房产贷款 %.0f = 净得 %.0f 元"
                 % (h["assets_value"], h["pay_compensation"], h["bear_debt"], h["bear_lien"], h["net"]))
    lines.append("女方：分得资产 %.0f - 应付补偿 %.0f - 承担债务 %.0f - 房产贷款 %.0f = 净得 %.0f 元"
                 % (w["assets_value"], w["pay_compensation"], w["bear_debt"], w["bear_lien"], w["net"]))
    lines.append("")
    lines.append("四、谈判要点")
    for i, p in enumerate(result["negotiation_points"], 1):
        lines.append("%d. %s" % (i, p))
    lines.append("")
    lines.append("免责声明：%s" % result["disclaimer"])
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 成果物：可下载的 HTML / PDF 报告
# ---------------------------------------------------------------------------

_TYPE_CN = {"real_estate": "房产", "deposit": "存款", "equity": "股权/投资"}


def to_html_report(result: Dict[str, Any],
                   out_path: str = "离婚财产分割测算报告.html",
                   case_label: str = "") -> str:
    """
    把计算结果渲染成一份 A4 版式的 HTML 报告并落盘，返回文件绝对路径。
    用户浏览器打开后 Ctrl+P 即可另存为 PDF，用于自存、发给对方或交给律师。
    """
    import sys, os as _os
    sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
    from report import render_html, save_html

    h = result["summary"]["husband"]
    w = result["summary"]["wife"]

    def m(v):
        return "{:,.0f}".format(float(v))

    # 一、分割明细
    rows = []
    for it in result["items"]:
        rows.append([
            it["asset"],
            _TYPE_CN.get(it["type"], it["type"]),
            it["belongs_to"],
            m(it["market_value"]),
            m(it["compensation_to_other"]) if it["compensation_to_other"] else "—",
            it["note"],
        ])
    sec_items = {
        "kind": "table", "title": "一、各项财产分割明细",
        "headers": ["财产项目", "类别", "归属", "现值(元)", "应向另一方补偿(元)", "计算依据"],
        "rows": rows, "num_cols": [3, 4],
    }

    sections = [sec_items]

    # 二、债务
    if result["debts"]:
        drows = [[d["name"], d["nature"], m(d["amount"]), d["borne_by"]]
                 for d in result["debts"]]
        sections.append({
            "kind": "table", "title": "二、债务承担",
            "headers": ["债务名称", "性质", "金额(元)", "承担方式"],
            "rows": drows, "num_cols": [2],
        })

    # 三、净得汇总
    sections.append({
        "kind": "table", "title": "三、双方净得汇总",
        "headers": ["", "分得资产", "应付补偿", "承担共同债务", "承担房产贷款", "净得(元)"],
        "rows": [
            ["男方", m(h["assets_value"]), m(h["pay_compensation"]),
             m(h["bear_debt"]), m(h["bear_lien"]), m(h["net"])],
            ["女方", m(w["assets_value"]), m(w["pay_compensation"]),
             m(w["bear_debt"]), m(w["bear_lien"]), m(w["net"])],
        ],
        "num_cols": [1, 2, 3, 4, 5], "total_row_index": None,
    })

    # 四、谈判要点
    sections.append({
        "kind": "list", "title": "四、谈判要点与执行建议",
        "items": result["negotiation_points"],
    })

    sections.append({
        "kind": "callout", "label": "这份报告怎么用",
        "body": "带着明细去谈，而不是空口对价。建议先就金额最大的房产归属与补偿达成一致，"
                "再用补偿金额平衡存款、股权等其他项目。若走诉讼或委托律师，"
                "可将本报告作为财产清单初稿，节省沟通成本。",
    })

    meta = [("结婚年限", "%s 年" % result["marriage_years"]),
            ("财产项目数", "%d 项" % len(result["items"])),
            ("债务项目数", "%d 项" % len(result["debts"]))]
    if case_label:
        meta.insert(0, ("案例标识", case_label))

    html = render_html(
        title="离婚财产分割测算报告",
        subtitle="依据《民法典》婚姻家庭编及相关司法解释通用规则测算 · 供协商谈判参考",
        meta=meta, sections=sections, disclaimer=result["disclaimer"],
        footer_note="离婚财产计算器 · 数据以用户输入为准，不构成法律意见",
    )
    return save_html(html, out_path)


def to_pdf_report(result: Dict[str, Any], out_path: str = "离婚财产分割测算报告.pdf") -> Optional[str]:
    """环境具备 weasyprint/wkhtmltopdf 时直接出 PDF；否则返回 None，请走 HTML 打印路径。"""
    import sys, os as _os
    sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
    from report import html_to_pdf
    tmp_html = out_path.rsplit(".", 1)[0] + ".html"
    to_html_report(result, tmp_html)
    return html_to_pdf(tmp_html, out_path)


# ---------------------------------------------------------------------------
# 测试入口
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    demo = new_case()
    demo["marriage_years"] = 8
    demo["real_estates"] = [{
        "name": "朝阳婚房", "current_value": 6000000, "original_price": 4000000,
        "acquired": "pre", "down_payment": 1200000, "down_payer": "husband",
        "joint_repayment": 800000, "remaining_loan": 1000000, "registered_owner": "男方",
    }]
    demo["deposits"] = [{"name": "共同存款", "amount": 500000, "acquired": "post"}]
    demo["equities"] = [{"name": "丈夫公司股权", "value": 2000000, "acquired": "post"}]
    demo["debts"] = [
        {"name": "房产剩余贷款", "amount": 1000000, "nature": "personal_lien"},
        {"name": "共同经营贷", "amount": 300000, "nature": "joint"},
    ]
    res = run(demo)
    print(to_report(res))
    path = to_html_report(res, "离婚财产分割测算报告_示例.html", case_label="示例案例")
    print("\n--- 成果物已生成 ---")
    print("HTML 报告：%s" % path)
    print("（浏览器打开后 Ctrl+P → 另存为 PDF，即得一份可下载的正式报告）")

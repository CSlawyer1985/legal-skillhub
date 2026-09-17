#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨境服务贸易涉税计算器 — 确定性计算脚本
=========================================
对应 references/税率速查表.md 与 references/纳税申报与税收优惠备案.md 的算法。

本脚本只做"必须精确"的涉税金额计算,不做法律判断(PE 定性、协定适用等仍须律师/税务师判断)。
所有计算结果以 JSON 输出,退出码语义化:
  0 = 成功
  1 = 参数错误
  2 = 文件不存在
  3 = 解析错误
  4 = 计算失败

调用示例:
  # 代扣代缴企业所得税:法定10% vs 协定7%(合同净价100万)
  python tax_calc.py wht.calc --income 1000000 --legal-rate 0.10 --treaty-rate 0.07 --gross
  # 同上,但合同价为净价(net,税款额外承担)
  python tax_calc.py wht.calc --income 1000000 --legal-rate 0.10 --treaty-rate 0.07 --net

  # 增值税归类(服务类型+消费地)
  python tax_calc.py vat.classify --service-type 现代服务 --consumption-location outbound

  # 增值税应纳税额(一般计税)
  python tax_calc.py vat.calc --sales-incl 1000000 --rate 0.06 --input-tax 20000

  # 协定税率查询
  python tax_calc.py treaty.lookup --country 新加坡 --income-type royalty

  # 境外税收抵免 — 直接抵免(居民企业境外所得已纳税款)
  python tax_calc.py ftc.calc --type direct --foreign-income 10000000 --foreign-tax-paid 2200000
  # 间接抵免(境外子公司股息还原下层归属税)
  python tax_calc.py ftc.calc --type indirect --dividend-gross 3000000 --foreign-corp-rate 0.30 --withholding-rate 0.10 --holding 0.50
  # 分国 vs 综合抵免对比
  python tax_calc.py ftc.calc --type compare --countries "甲:1000000:0.10,乙:2000000:0.35"
  # 税收饶让(协定视同已缴,中国仍按25%补差额)
  python tax_calc.py ftc.calc --type sparing --dividend 20000000 --sparing-rate 0.20
  # 境外亏损弥补(分国弥补,不得抵减境内盈利)
  python tax_calc.py ftc.calc --type overseas-loss --domestic 3000000 --branches "甲:1000000,乙:-3000000,乙:600000"
"""
import sys
import json
import argparse

# ============================================================
# 工具函数
# ============================================================

def emit_success(data):
    """统一成功输出"""
    print(json.dumps({"status": "success", "data": data},
                     ensure_ascii=False, indent=2))
    sys.exit(0)


def emit_error(message, code=4):
    """统一错误输出"""
    print(json.dumps({"status": "error", "error": message},
                     ensure_ascii=False), file=sys.stderr)
    sys.exit(code)


def round2(x):
    """四舍五入到分(2位小数)"""
    return round(x + 1e-9, 2)


def parse_rate(s):
    """解析税率,接受小数(0.10)或百分数字符串(10%)"""
    if isinstance(s, (int, float)):
        return float(s)
    s = str(s).strip()
    if s.endswith("%"):
        return float(s[:-1]) / 100.0
    return float(s)


def fmt_pct(r):
    """0.07 -> '7%'"""
    return f"{round2(r * 100)}%"


# ============================================================
# 子命令: wht.calc — 代扣代缴企业所得税
# ============================================================

# 附加税费率(以增值税为基数):城建税7%+教育费附加3%+地方教育附加2% = 12%
SURTAX_ON_VAT_DEFAULT = 0.12


def cmd_wht_calc(args):
    """
    代扣代缴企业所得税计算。
    支持两种价格口径:
      --gross  : 合同价为含税总价(gross),税款从中扣除,收款方实收 = 收入 - 税款
      --net    : 合同价为税后净价(net),税款由付款方额外承担,实际支付总额 = 净价 / (1 - 税率)
    """
    try:
        income = float(args.income)
        legal_rate = parse_rate(args.legal_rate)
    except (ValueError, TypeError):
        emit_error(f"参数解析失败: income/legal-rate 非数字", code=3)

    if income <= 0:
        emit_error(f"income 须为正数: {income}", code=1)
    if not (0 < legal_rate < 1):
        emit_error(f"legal-rate 须在 (0,1) 之间: {legal_rate}", code=1)

    treaty_rate = parse_rate(args.treaty_rate) if args.treaty_rate else None
    if treaty_rate is not None and not (0 < treaty_rate <= legal_rate):
        emit_error(
            f"treaty-rate 须在 (0, {legal_rate}] 之间(协定优惠≤法定): {treaty_rate}",
            code=1)

    apply_rate = treaty_rate if (treaty_rate is not None and args.apply_treaty) else legal_rate

    if args.gross:
        # 含税口径:税款 = 收入 × 税率,收款方实收 = 收入 - 税款
        tax = income * apply_rate
        net_received = income - tax
        total_paid = income
        gross_income = income
        method = "gross(合同价含税,税款从中扣除)"
    else:
        # net 口径:合同价为税后净价,实际支付总额倒算
        if apply_rate >= 1:
            emit_error("net 口径下税率不能≥100%", code=1)
        total_paid = income / (1 - apply_rate)
        tax = total_paid - income
        net_received = income
        gross_income = total_paid
        method = "net(合同价为税后净价,税款额外承担)"

    result = {
        "method": method,
        "contract_amount": round2(income),
        "applied_rate": fmt_pct(apply_rate),
        "applied_rate_decimal": apply_rate,
        "source_of_rate": "treaty(协定优惠)" if (treaty_rate is not None and args.apply_treaty) else "legal(法定)",
        "taxable_income": round2(gross_income),
        "withholding_tax": round2(tax),
        "payee_net_received": round2(net_received),
        "payer_total_paid": round2(total_paid),
        "formula": "应纳税额 = 计税基础 × 适用税率",
        "legal_basis": "《企业所得税法实施条例》第91条;协定原文",
    }

    # 法定 vs 协定对比(若提供协定税率)
    if treaty_rate is not None and treaty_rate != legal_rate:
        if args.gross:
            legal_tax = income * legal_rate
            treaty_tax = income * treaty_rate
        else:
            legal_tax = income / (1 - legal_rate) - income
            treaty_tax = income / (1 - treaty_rate) - income
        result["comparison"] = {
            "legal_rate": fmt_pct(legal_rate),
            "legal_rate_tax": round2(legal_tax),
            "treaty_rate": fmt_pct(treaty_rate),
            "treaty_rate_tax": round2(treaty_tax),
            "saving_by_treaty": round2(legal_tax - treaty_tax),
            "note": "享受协定优惠须满足受益所有人+留存备查(2018年第9号公告、2019年第35号公告)",
        }

    emit_success(result)


# ============================================================
# 子命令: vat.classify — 增值税归类
# ============================================================

def cmd_vat_classify(args):
    """根据服务类型与消费地判定增值税处理"""
    service = args.service_type.strip()
    location = args.consumption_location.strip().lower()

    valid_locations = {"inbound", "outbound"}
    if location not in valid_locations:
        emit_error(f"consumption-location 须为 inbound(境内消费)/outbound(境外消费): {location}", code=1)

    location_label = "境内消费" if location == "inbound" else "境外消费"

    # 服务类型 -> 一般计税税率
    rate_map = {
        "现代服务": 0.06, "技术服务": 0.06, "咨询服务": 0.06, "研发服务": 0.06,
        "信息技术服务": 0.06, "文化创意服务": 0.06, "鉴证咨询服务": 0.06,
        "交通运输": 0.09, "邮政": 0.09, "基础电信": 0.09, "建筑": 0.09,
        "不动产租赁": 0.09, "不动产销售": 0.09,
        "销售货物": 0.13, "加工修理修配": 0.13, "有形动产租赁": 0.13,
    }
    matched_key = None
    for k in rate_map:
        if k in service or service in k:
            matched_key = k
            break
    general_rate = rate_map.get(matched_key, 0.06) if matched_key else 0.06

    # 零税率特定服务(财税36号附件4列举,须精确匹配服务类型,非子串包含)
    # 注意:零税率与免税的进项处理截然不同(零税率可抵退,免税不可抵),误判会虚增税务利益
    zero_rate_services_exact = {
        "国际运输服务", "研发服务", "设计服务", "广播影视节目(作品)的制作和发行服务",
        "软件服务", "电路设计及测试服务", "信息系统服务", "业务流程管理服务",
        "离岸服务外包业务", "转让技术", "技术研发",
    }
    # 零税率关键词(用于提示用户精确确认,不直接判定)
    zero_rate_keywords = ["国际运输", "研发", "设计", "软件", "广播影视", "技术转让", "离岸服务外包"]

    # 判定(默认 note)
    note = "本归类为通用框架,具体适用条件须核实;工程/矿产资源在境外的勘察勘探服务免税"

    if location == "outbound":
        # 境内->境外,完全在境外消费
        # 零税率须精确匹配列举服务(防子串误判:"技术转让咨询"不应匹配"技术转让")
        is_zero_exact = service in zero_rate_services_exact
        matched_kw = next((k for k in zero_rate_keywords if k in service), None)
        has_zero_keyword = matched_kw is not None and not is_zero_exact

        if is_zero_exact:
            treatment = "零税率"
            rate = 0.0
            input_credit = "可抵扣进项(并退税)"
            basis = "财税〔2016〕36号附件4(特定跨境应税服务)"
        elif has_zero_keyword:
            # 关键词命中但非精确匹配——保守判定为免税,提示用户确认实质
            treatment = "免税(疑似可适用零税率,须人工确认)"
            rate = 0.0
            input_credit = "暂按免税:不可抵扣进项;若确属零税率列举服务则可抵退"
            basis = "财税〔2016〕36号附件4"
            note = (f"⚠️ 服务名称含'{matched_kw}'关键词,但非精确匹配零税率列举服务。"
                    f"请核实该服务是否属于附件4列举的零税率应税服务"
                    f"(精确清单见 references/纳税申报与税收优惠备案.md),"
                    f"若确属则改按零税率,否则为免税。零税率与免税的进项处理截然不同(零税率可抵退,免税不可抵)。")
        else:
            treatment = "免税"
            rate = 0.0
            input_credit = "不可抵扣进项(部分可核定)"
            basis = "财税〔2016〕36号附件4(完全在境外消费的跨境服务)"
    else:
        # 境外->境内,境内消费
        treatment = "一般计税(境内购买方代扣代缴)"
        rate = general_rate
        input_credit = "可抵扣进项(取得合法扣税凭证)"
        basis = "增值税法、财税〔2016〕36号(境内消费)"

    result = {
        "service_type": service,
        "consumption_location": location_label,
        "treatment": treatment,
        "rate": fmt_pct(rate) if rate > 0 else "0%(免税/零税率)",
        "rate_decimal": rate,
        "input_tax_credit": input_credit,
        "basis": basis,
        "note": note,
    }
    emit_success(result)


# ============================================================
# 子命令: vat.calc — 增值税应纳税额
# ============================================================

def cmd_vat_calc(args):
    """增值税应纳税额(一般计税:销项-进项)"""
    try:
        rate = parse_rate(args.rate)
        if args.sales_incl is not None:
            sales_incl = float(args.sales_incl)
            sales_excl = sales_incl / (1 + rate)
        elif args.sales_excl is not None:
            sales_excl = float(args.sales_excl)
            sales_incl = sales_excl * (1 + rate)
        else:
            emit_error("须提供 --sales-incl 或 --sales-excl", code=1)
            return
        input_tax = float(args.input_tax)
    except (ValueError, TypeError):
        emit_error("参数解析失败", code=3)
        return

    if sales_excl <= 0:
        emit_error(f"销售额须为正: {sales_excl}", code=1)
    if not (0 < rate < 1):
        emit_error(f"rate 须在 (0,1): {rate}", code=1)
    if input_tax < 0:
        emit_error(f"input_tax 不得为负(负进项会虚增退税): {input_tax}", code=1)

    output_tax = sales_excl * rate
    payable = output_tax - input_tax

    result = {
        "method": "一般计税",
        "sales_inclusive": round2(sales_incl),
        "sales_exclusive": round2(sales_excl),
        "rate": fmt_pct(rate),
        "output_tax": round2(output_tax),
        "input_tax": round2(input_tax),
        "vat_payable": round2(max(payable, 0)),
        "excess_input_credit": round2(abs(min(payable, 0))) if payable < 0 else 0,
        "formula": "应纳税额 = 销项税额 - 进项税额; 销项 = 不含税销售额 × 税率",
        "basis": "增值税法、财税〔2016〕36号",
    }
    emit_success(result)


# ============================================================
# 子命令: treaty.lookup — 协定税率查询(内置常见协定,非权威)
# ============================================================

# 协定税率表(经国税总局/对方税务局交叉核实,2026-08)
# 格式说明:每条记录可含"条件"——多数协定的股息优惠税率有持股比例门槛。
#   {"rate": 0.05, "condition": "直接持股≥25%"} 表示满足条件才适用,否则用 fallback。
#   "fallback" 字段为不满足条件时的税率。
# 来源标注见各条 source;last_verified 为最近核实日期,超12个月 exp_lint/treaty_check 会报 warning。
TREATY_TABLE_LAST_VERIFIED = "2026-08"

TREATY_TABLE = {
    # 内地-香港安排(2018第七议定书):股息持股≥25%为5%,否则10%;
    # 特许权使用费7%(飞机船舶租赁5%);利息7%
    "中国香港": {
        "dividend": {"rate": 0.05, "condition": "直接持股≥25%", "fallback": 0.10},
        "interest": 0.07,
        "royalty": {"rate": 0.07, "note": "飞机/船舶租赁特许权使用费为5%(2015第七议定书)"},
        "source": "内地与香港特别行政区税收安排第七议定书;ird.gov.hk",
    },
    "香港": "中国香港",  # 别名
    # 内地-澳门安排:股息持股≥25%为5%否则10%;利息7%(部分免税);特许权7%/10%
    "中国澳门": {
        "dividend": {"rate": 0.05, "condition": "直接持股≥25%", "fallback": 0.10},
        "interest": 0.07,
        "royalty": 0.10,
        "source": "内地与澳门特别行政区税收安排",
    },
    "澳门": "中国澳门",  # 别名
    # 中新协定:股息持股≥25%为5%否则10%;利息7%/12%;特许权10%
    "新加坡": {
        "dividend": {"rate": 0.05, "condition": "直接持股≥25%", "fallback": 0.10},
        "interest": 0.07,
        "royalty": 0.10,
        "source": "中新税收协定(2007修订)",
    },
    # 中美协定:股息10%;利息10%(部分免税);特许权10%
    # ⚠️ 2025《美国优先投资政策备忘录》引发终止风险,若终止预提税升至30%
    "美国": {
        "dividend": 0.10,
        "interest": 0.10,
        "royalty": 0.10,
        "source": "中美税收协定(1984)",
        "risk_warning": "2025年《美国优先投资政策备忘录》引发协定终止关注,若终止,预提税将从10%升至美国法定30%。使用前务必核实现行有效性。",
    },
    # 中日协定:股息10%;利息10%;特许权10%
    "日本": {
        "dividend": 0.10, "interest": 0.10, "royalty": 0.10,
        "source": "中日税收协定",
    },
    # 中德协定:股息持股≥25%为5%否则10%;利息15%(金融机构等免税);特许权10%(设备租赁按60%计征实缴6%)
    "德国": {
        "dividend": {"rate": 0.05, "condition": "直接持股≥25%", "fallback": 0.10},
        "interest": {"rate": 0.15, "note": "政府/央行/政策性银行/政府全资金融机构等免税"},
        "royalty": {"rate": 0.10, "note": "工业/商业/科学设备租赁按总额60%计征,实际有效税率6%"},
        "source": "中德税收协定(新);shui5.cn;税务机关公开解读",
    },
    # 中英协定:股息持股≥25%为5%否则10%;利息10%;特许权10%
    "英国": {
        "dividend": {"rate": 0.05, "condition": "直接持股≥25%", "fallback": 0.10},
        "interest": 0.10,
        "royalty": 0.10,
        "source": "中英税收协定",
    },
    # 中法协定:股息10%(无论持股比例);利息10%;特许权10%
    "法国": {
        "dividend": 0.10,
        "interest": 0.10,
        "royalty": 0.10,
        "source": "中法税收协定;金杜律所",
    },
    # 中荷协定:股息持股≥25%为5%否则10%;利息10%;特许权10%
    "荷兰": {
        "dividend": {"rate": 0.05, "condition": "直接持股≥25%", "fallback": 0.10},
        "interest": 0.10,
        "royalty": 0.10,
        "source": "中荷税收协定;广东省税务局PDF",
    },
    # 中韩协定:股息持股≥25%为5%否则10%;利息10%(部分);特许权10%;含LOB
    "韩国": {
        "dividend": {"rate": 0.05, "condition": "直接持股≥25%", "fallback": 0.10},
        "interest": 0.10,
        "royalty": 0.10,
        "source": "中韩税收协定(含LOB)",
    },
    # 中印协定:股息10%/15%;利息10%/15%;特许权与技术服务费合并第12条,限制税率10%(7.5%系印度国内法,非协定)
    "印度": {
        "dividend": 0.10,
        "interest": 0.10,
        "royalty": 0.10,
        "tech_service": {"rate": 0.10, "note": "中印第12条将特许权与技术服务费合并,限制税率10%。印度国内法预提税可能为7.5%/10%,以孰低原则适用"},
        "source": "中印税收协定第12条;江苏省税务局",
    },
    "俄罗斯": {
        "dividend": 0.10, "interest": 0.10, "royalty": 0.10,
        "source": "中俄税收协定(2014)",
    },
    # 中爱协定:股息持股≥25%为5%否则10%;利息10%;特许权10%
    "爱尔兰": {
        "dividend": {"rate": 0.05, "condition": "直接持股≥25%", "fallback": 0.10},
        "interest": 0.10,
        "royalty": 0.10,
        "source": "中爱税收协定;revenue.ie",
    },
    # 无协定地区(避税港)
    "开曼": None,
    "BVI": None,
    "英属维尔京": None,
    "百慕大": None,
}

INCOME_TYPE_LABEL = {
    "dividend": "股息",
    "interest": "利息",
    "royalty": "特许权使用费",
    "tech_service": "技术服务费",
    "business_profit": "营业利润",
    "capital_gain": "财产收益",
}


def _resolve_alias(country):
    """解析别名(如"香港"->"中国香港")"""
    val = TREATY_TABLE.get(country)
    if isinstance(val, str):
        return val  # 别名指向另一个 key
    return country


def _extract_rate(rate_entry):
    """从税率条目提取数值或结构化结果。返回 (数值或None, 结构化信息dict)"""
    if rate_entry is None:
        return None, {}
    if isinstance(rate_entry, (int, float)):
        return float(rate_entry), {}
    if isinstance(rate_entry, dict):
        return rate_entry.get("rate"), rate_entry
    return None, {}


def cmd_treaty_lookup(args):
    """查询协定税率(内置常见协定,非权威,以原文为准)"""
    country = args.country.strip()
    income_type = args.income_type.strip().lower()

    if income_type not in INCOME_TYPE_LABEL:
        emit_error(
            f"income-type 须为: {', '.join(INCOME_TYPE_LABEL.keys())}: {income_type}",
            code=1)

    # 解析别名
    canonical = _resolve_alias(country)
    entry = TREATY_TABLE.get(canonical)

    # 明确无协定(避税港)
    if entry is None and canonical in TREATY_TABLE:
        result = {
            "country": country,
            "income_type": INCOME_TYPE_LABEL[income_type],
            "has_treaty": False,
            "treaty_rate": None,
            "legal_rate": "10%(法定)",
            "note": f"{country}与中国无税收协定,一律按法定10%代扣代缴",
            "warning": "避税港路径无协定优惠,是受益所有人审查重点",
        }
        emit_success(result)

    if entry is None:
        emit_error(
            f"内置表未收录 '{country}'。请查阅国家税务总局协定原文,或确认国家名称拼写。"
            f"已收录: {', '.join(k for k in TREATY_TABLE if TREATY_TABLE[k] or k in ('开曼','BVI','英属维尔京','百慕大'))}",
            code=1)

    # 营业利润特殊处理
    if income_type == "business_profit":
        result = {
            "country": country,
            "income_type": "营业利润(协定第7条)",
            "has_treaty": True,
            "treaty_rate": "无 PE 不征税;有 PE 按查账/核定(25%)",
            "note": "营业利润按 PE 原则处理",
            "table_last_verified": TREATY_TABLE_LAST_VERIFIED,
        }
        emit_success(result)

    rate_entry = entry.get(income_type)
    rate, info = _extract_rate(rate_entry)

    if rate is None:
        result = {
            "country": country,
            "income_type": INCOME_TYPE_LABEL[income_type],
            "has_treaty": True,
            "treaty_rate": "未收录,请查协定原文",
            "legal_rate": "10%(法定)",
            "note": "本表未收录该所得类型的协定税率,以协定原文为准",
            "table_last_verified": TREATY_TABLE_LAST_VERIFIED,
        }
        emit_success(result)

    result = {
        "country": country,
        "income_type": INCOME_TYPE_LABEL[income_type],
        "has_treaty": True,
        "treaty_rate": fmt_pct(rate),
        "treaty_rate_decimal": rate,
        "legal_rate": "10%(法定)",
        "saving_vs_legal": fmt_pct(0.10 - rate) if rate <= 0.10 else "0%(协定税率≥法定)",
        "article": _treaty_article(income_type),
        "source": entry.get("source", "以协定原文为准"),
        "table_last_verified": TREATY_TABLE_LAST_VERIFIED,
        "warning": "本表为归纳参考,非权威;以国家税务总局公布协定原文及议定书为准;须通过受益所有人+LOB/PPT审查方可享受",
    }

    # 条件性税率(如股息持股门槛)
    if "condition" in info:
        result["applicability_condition"] = info["condition"]
        result["fallback_rate"] = fmt_pct(info.get("fallback", 0.10))
        result["decision_hint"] = (f"满足'{info['condition']}'时适用{fmt_pct(rate)};"
                                   f"否则适用{fmt_pct(info.get('fallback', 0.10))}。"
                                   f"请确认持股比例/适用条件后再用于计算。")
    if "note" in info:
        result["rate_note"] = info["note"]

    # 协定级风险警示(如美国终止风险)
    if "risk_warning" in entry:
        result["risk_warning"] = entry["risk_warning"]

    emit_success(result)


def _treaty_article(income_type):
    return {
        "dividend": "协定第10条",
        "interest": "协定第11条",
        "royalty": "协定第12条",
        "tech_service": "协定第12条之二或第13条(视协定)",
        "business_profit": "协定第7条",
        "capital_gain": "协定第13条",
    }.get(income_type, "")


# ============================================================
# 子命令: treaty.check — 协定税率表时效性检查
# ============================================================

def cmd_treaty_check(args):
    """检查内置协定税率表是否过期(协定会修订/废止)"""
    from datetime import date, datetime
    try:
        verified = datetime.strptime(TREATY_TABLE_LAST_VERIFIED, "%Y-%m").date()
        today = date.today()
        months = (today.year - verified.year) * 12 + (today.month - verified.month)
    except (ValueError, TypeError):
        emit_error(f"table_last_verified 格式错误: {TREATY_TABLE_LAST_VERIFIED}", code=3)

    STALE_MONTHS = 12
    countries = [k for k, v in TREATY_TABLE.items()
                 if v is not None and not isinstance(v, str)]

    result = {
        "table_last_verified": TREATY_TABLE_LAST_VERIFIED,
        "months_since_verified": months,
        "stale_threshold_months": STALE_MONTHS,
        "covered_countries": countries,
        "status": "fresh" if months <= STALE_MONTHS else "STALE",
    }
    if months > STALE_MONTHS:
        result["warning"] = (
            f"协定税率表已 {months} 个月未核实(>{STALE_MONTHS})。"
            f"税收协定会修订/废止/新签(如中美协定2025终止风险),"
            f"请对照国家税务总局最新公布重新核实各条目后更新 table_last_verified。"
        )
    else:
        result["note"] = (
            f"表在 {months} 个月内核实,仍在有效期。"
            f"仍建议引用具体税率时以协定原文为准。"
        )
    emit_success(result)


# ============================================================
# 子命令: ftc.calc — 境外税收抵免(直接/间接/分国vs综合/饶让/境外亏损)
# ============================================================
#
# ⚠️ 政策口径待核实(2026-08 联网核实受限,以下基于模型知识 + skill 资产交叉印证):
#   - 直接抵免依据:企业所得税法第23条
#   - 间接抵免依据:企业所得税法第24条 + 实施条例第80-81条(持股≥20%)
#   - 分国 vs 综合:财税〔2017〕84号(2018-01-01生效)放开综合抵免选择权,一经选择 5 年不变
#   - 三层→五层:财税〔2017〕84号由125号的三层扩展为五层(各层持股≥20%)
#   - 饶让:协定条款(非国内法单方给予),须核查具体协定是否含饶让
#   - 境外亏损:企业所得税法第17条(不得抵减境内盈利)+ 财税〔2009〕125号(分国弥补)
#   建议 2026-09 配额恢复后人工查阅财税〔2017〕84号原文复核"5年不变"等关键参数。

FTC_VERIFY_NOTE = ("政策口径基于模型知识+skill资产交叉印证(2026-08 联网核实受限),"
                   "建议人工查阅财税〔2017〕84号、财税〔2009〕125号原文复核。")

# 中国居民企业所得税基准税率(境外抵免限额计算用)
CHINA_CORP_RATE_DEFAULT = 0.25
# 间接抵免持股门槛(各层)
INDIRECT_HOLDING_THRESHOLD = 0.20


def _ftc_credit(income, foreign_tax_paid, china_rate):
    """单笔所得的直接抵免核心计算:限额/抵免/差额/超限。返回 dict。"""
    limit = income * china_rate
    credit = min(foreign_tax_paid, limit)
    if foreign_tax_paid <= limit:
        return {"limit": limit, "credit": credit, "domestic_supplement": limit - credit, "excess_carryforward": 0.0}
    return {"limit": limit, "credit": credit, "domestic_supplement": 0.0, "excess_carryforward": foreign_tax_paid - credit}


def cmd_ftc_calc(args):
    """境外税收抵免计算(5 种模式: direct / indirect / compare / sparing / overseas-loss)"""
    mode = (args.type or "").strip().lower()
    valid_modes = {"direct", "indirect", "compare", "sparing", "overseas-loss"}
    if mode not in valid_modes:
        emit_error(f"--type 须为: {', '.join(sorted(valid_modes))}: {mode}", code=1)

    try:
        china_rate = parse_rate(args.china_rate) if args.china_rate else CHINA_CORP_RATE_DEFAULT
    except (ValueError, TypeError):
        emit_error(f"china-rate 解析失败", code=3)
        return
    if not (0 < china_rate < 1):
        emit_error(f"china-rate 须在 (0,1): {china_rate}", code=1)

    if mode == "direct":
        _ftc_direct(args, china_rate)
    elif mode == "indirect":
        _ftc_indirect(args, china_rate)
    elif mode == "compare":
        _ftc_compare(args, china_rate)
    elif mode == "sparing":
        _ftc_sparing(args, china_rate)
    elif mode == "overseas-loss":
        _ftc_overseas_loss(args, china_rate)


def _ftc_direct(args, china_rate):
    """直接抵免:居民企业就境外所得已纳税款直接抵免"""
    try:
        foreign_income = float(args.foreign_income)
        foreign_tax_paid = float(args.foreign_tax_paid) if args.foreign_tax_paid is not None else 0.0
    except (ValueError, TypeError):
        emit_error("参数解析失败: foreign-income/foreign-tax-paid 非数字", code=3)
        return

    if foreign_income <= 0:
        emit_error(f"foreign-income 须为正数: {foreign_income}", code=1)
    if foreign_tax_paid < 0:
        emit_error(f"foreign-tax-paid 不得为负: {foreign_tax_paid}", code=1)

    r = _ftc_credit(foreign_income, foreign_tax_paid, china_rate)
    result = {
        "type": "direct(直接抵免)",
        "foreign_income": round2(foreign_income),
        "foreign_tax_paid": round2(foreign_tax_paid),
        "china_rate": fmt_pct(china_rate),
        "credit_limit": round2(r["limit"]),
        "credit_allowed": round2(r["credit"]),
        "domestic_supplement": round2(r["domestic_supplement"]),
        "excess_carryforward": round2(r["excess_carryforward"]),
        "formula": "抵免限额 = 境外所得 × 中国税率(25%); 抵免 = min(实缴, 限额); 实缴<限额则差额境内补税,实缴>限额则超限结转",
        "legal_basis": "企业所得税法第23条(直接抵免); 财税〔2009〕125号",
        "verify_status": FTC_VERIFY_NOTE,
    }
    emit_success(result)


def _ftc_indirect(args, china_rate):
    """间接抵免:居民企业从境外子公司分得股息,还原下层归属税后抵免"""
    try:
        dividend_gross = float(args.dividend_gross)
        foreign_corp_rate = parse_rate(args.foreign_corp_rate)
        withholding_rate = parse_rate(args.withholding_rate) if args.withholding_rate else 0.0
        holding = float(args.holding) if args.holding is not None else 1.0
    except (ValueError, TypeError):
        emit_error("参数解析失败: dividend-gross/foreign-corp-rate/withholding-rate/holding 非数字", code=3)
        return

    if dividend_gross <= 0:
        emit_error(f"dividend-gross 须为正数: {dividend_gross}", code=1)
    if not (0 < foreign_corp_rate < 1):
        emit_error(f"foreign-corp-rate 须在 (0,1): {foreign_corp_rate}", code=1)
    if not (0 <= withholding_rate < 1):
        emit_error(f"withholding-rate 须在 [0,1): {withholding_rate}", code=1)
    if not (0 < holding <= 1):
        emit_error(f"holding 须在 (0,1]: {holding}", code=1)

    # 持股门槛提示(不阻断计算,仅提示)
    holding_warning = None
    if holding < INDIRECT_HOLDING_THRESHOLD:
        holding_warning = (f"⚠️ 持股 {fmt_pct(holding)} < 间接抵免门槛 {fmt_pct(INDIRECT_HOLDING_THRESHOLD)},"
                           f"依财税〔2009〕125号/〔2017〕84号可能不适用间接抵免,本结果仅供测算")

    # 还原下层归属税:毛股息 ÷ (1 - 境外企税率) × 境外企税率
    pretax_equivalent = dividend_gross / (1 - foreign_corp_rate)
    imputed_tax = pretax_equivalent * foreign_corp_rate
    withholding_tax = dividend_gross * withholding_rate
    total_foreign_tax = imputed_tax + withholding_tax

    # 还原后境内应税所得 = 毛股息 + 还原税
    china_taxable = dividend_gross + imputed_tax
    r = _ftc_credit(china_taxable, total_foreign_tax, china_rate)

    result = {
        "type": "indirect(间接抵免)",
        "dividend_gross": round2(dividend_gross),
        "holding": fmt_pct(holding),
        "foreign_corp_rate": fmt_pct(foreign_corp_rate),
        "withholding_rate": fmt_pct(withholding_rate),
        "pretax_equivalent_profit": round2(pretax_equivalent),
        "imputed_foreign_tax": round2(imputed_tax),
        "withholding_tax": round2(withholding_tax),
        "total_foreign_tax": round2(total_foreign_tax),
        "china_taxable_income_restored": round2(china_taxable),
        "china_rate": fmt_pct(china_rate),
        "credit_limit": round2(r["limit"]),
        "credit_allowed": round2(r["credit"]),
        "domestic_supplement": round2(r["domestic_supplement"]),
        "excess_carryforward": round2(r["excess_carryforward"]),
        "formula": ("还原税前利润 = 毛股息 ÷ (1 - 境外企税率); 归属税 = 还原利润 × 境外企税率; "
                    "境外税合计 = 归属税 + 预提税; 境内应税 = 毛股息 + 归属税; "
                    "限额 = 应税 × 25%; 抵免 = min(境外税合计, 限额)"),
        "legal_basis": "企业所得税法第24条(间接抵免) + 实施条例第80-81条; 财税〔2009〕125号; 财税〔2017〕84号(三层→五层,各层持股≥20%)",
        "verify_status": FTC_VERIFY_NOTE,
    }
    if holding_warning:
        result["holding_warning"] = holding_warning
    emit_success(result)


def _ftc_compare(args, china_rate):
    """分国不分项 vs 综合抵免:多国所得两套方法对比"""
    if not args.countries:
        emit_error("compare 模式须提供 --countries(格式: '国名:所得:实缴税率' 多组,逗号分隔)", code=1)
        return

    items = []
    for raw in args.countries.split(","):
        raw = raw.strip()
        if not raw:
            continue
        parts = [p.strip() for p in raw.split(":")]
        if len(parts) != 3:
            emit_error(f"--countries 每组格式须为 '国名:所得:实缴税率': {raw}", code=1)
            return
        name, income_s, rate_s = parts
        try:
            income = float(income_s)
            rate = parse_rate(rate_s)
        except (ValueError, TypeError):
            emit_error(f"解析失败(所得/税率非数字): {raw}", code=3)
            return
        if income <= 0:
            emit_error(f"所得须为正: {raw}", code=1)
        if not (0 <= rate < 1):
            emit_error(f"实缴税率须在 [0,1): {raw}", code=1)
        items.append({"country": name, "income": income, "paid": income * rate})

    if not items:
        emit_error("--countries 至少需要 1 组", code=1)
        return

    # 分国不分项:逐国算限额
    per_country = []
    agg_limit = 0.0
    agg_credit = 0.0
    agg_supplement = 0.0
    agg_carryforward = 0.0
    for it in items:
        r = _ftc_credit(it["income"], it["paid"], china_rate)
        per_country.append({
            "country": it["country"],
            "income": round2(it["income"]),
            "tax_paid": round2(it["paid"]),
            "limit": round2(r["limit"]),
            "credit": round2(r["credit"]),
            "domestic_supplement": round2(r["domestic_supplement"]),
            "excess_carryforward": round2(r["excess_carryforward"]),
        })
        agg_limit += r["limit"]
        agg_credit += r["credit"]
        agg_supplement += r["domestic_supplement"]
        agg_carryforward += r["excess_carryforward"]

    per_country_summary = {
        "total_income": round2(sum(it["income"] for it in items)),
        "total_tax_paid": round2(sum(it["paid"] for it in items)),
        "total_limit": round2(agg_limit),
        "total_credit": round2(agg_credit),
        "total_domestic_supplement": round2(agg_supplement),
        "total_excess_carryforward": round2(agg_carryforward),
    }

    # 综合抵免法(不分国不分项):合并所得算限额
    total_income = sum(it["income"] for it in items)
    total_paid = sum(it["paid"] for it in items)
    agg = _ftc_credit(total_income, total_paid, china_rate)
    aggregate = {
        "total_income": round2(total_income),
        "total_tax_paid": round2(total_paid),
        "limit": round2(agg["limit"]),
        "credit": round2(agg["credit"]),
        "domestic_supplement": round2(agg["domestic_supplement"]),
        "excess_carryforward": round2(agg["excess_carryforward"]),
    }

    # 推荐:选抵免多的(即境内补税少 + 结转少,综合净现金流更优)
    per_country_net_credit = agg_credit
    aggregate_net_credit = agg["credit"]
    if aggregate_net_credit > per_country_net_credit:
        recommendation = (f"建议选【综合抵免法】:抵免 {round2(aggregate_net_credit)} > 分国 {round2(per_country_net_credit)},"
                          f"少补税/多抵免")
    elif aggregate_net_credit < per_country_net_credit:
        recommendation = (f"建议选【分国不分项】:抵免 {round2(per_country_net_credit)} > 综合 {round2(aggregate_net_credit)}")
    else:
        recommendation = f"两种方法抵免相同({round2(aggregate_net_credit)}),均可"

    result = {
        "type": "compare(分国 vs 综合)",
        "method_lock_note": "一经选择 5 年不变(财税〔2017〕84号)",
        "per_country_method": {"details": per_country, "summary": per_country_summary},
        "aggregate_method": aggregate,
        "recommendation": recommendation,
        "legal_basis": "财税〔2017〕84号(2018-01-01生效,放开综合抵免选择权); 财税〔2009〕125号(原分国不分项)",
        "verify_status": FTC_VERIFY_NOTE,
    }
    emit_success(result)


def _ftc_sparing(args, china_rate):
    """税收饶让抵免:协定优惠视同已缴,但中国仍按25%限额补差额(饶让≠免税)"""
    try:
        dividend = float(args.dividend)
        sparing_rate = parse_rate(args.sparing_rate)
        actual_foreign_tax = float(args.actual_foreign_tax) if args.actual_foreign_tax is not None else 0.0
    except (ValueError, TypeError):
        emit_error("参数解析失败: dividend/sparing-rate/actual-foreign-tax 非数字", code=3)
        return

    if dividend <= 0:
        emit_error(f"dividend 须为正数: {dividend}", code=1)
    if not (0 <= sparing_rate < 1):
        emit_error(f"sparing-rate 须在 [0,1): {sparing_rate}", code=1)
    if actual_foreign_tax < 0:
        emit_error(f"actual-foreign-tax 不得为负: {actual_foreign_tax}", code=1)

    # 饶让:视同已缴 = 所得 × 法定(协定)税率;实际未缴的部分也被"视同"
    deemed_paid = dividend * sparing_rate
    total_deemed = deemed_paid + actual_foreign_tax
    r = _ftc_credit(dividend, total_deemed, china_rate)

    result = {
        "type": "sparing(税收饶让抵免)",
        "dividend": round2(dividend),
        "sparing_rate": fmt_pct(sparing_rate),
        "actual_foreign_tax": round2(actual_foreign_tax),
        "deemed_paid_by_sparing": round2(deemed_paid),
        "total_deemed_paid": round2(total_deemed),
        "china_rate": fmt_pct(china_rate),
        "credit_limit": round2(r["limit"]),
        "credit_allowed": round2(r["credit"]),
        "domestic_supplement": round2(r["domestic_supplement"]),
        "formula": ("视同已缴 = 所得 × 饶让税率(协定法定率); 总视同 = 视同 + 实缴; "
                    "限额 = 所得 × 25%; 抵免 = min(总视同, 限额); 差额境内补税(饶让≠免税)"),
        "key_warning": "⚠️ 饶让是'视同已缴'非'免税',中国仍按25%限额补差额;且须核查协定是否含饶让条款(非所有协定都有)",
        "legal_basis": "税收协定饶让条款(协定层面,非国内法单方给予); 企业所得税法第23/24条(抵免机制)",
        "verify_status": FTC_VERIFY_NOTE,
    }
    emit_success(result)


def _ftc_overseas_loss(args, china_rate):
    """境外亏损弥补:分国弥补,境外亏损不得抵减境内或他国盈利;未弥补部分无限期结转(该国未来盈利)"""
    if not args.branches:
        emit_error("overseas-loss 模式须提供 --branches(格式: '国名:盈亏' 多组,逗号分隔,亏损用负数)", code=1)
        return

    try:
        domestic = float(args.domestic) if args.domestic is not None else 0.0
    except (ValueError, TypeError):
        emit_error("domestic 解析失败", code=3)
        return
    if domestic < 0:
        emit_error(f"domestic(境内所得)不得为负: {domestic}", code=1)

    # 解析各国分支
    branches = []
    for raw in args.branches.split(","):
        raw = raw.strip()
        if not raw:
            continue
        parts = [p.strip() for p in raw.split(":")]
        if len(parts) != 2:
            emit_error(f"--branches 每组格式须为 '国名:盈亏': {raw}", code=1)
            return
        name, amount_s = parts
        try:
            amount = float(amount_s)
        except (ValueError, TypeError):
            emit_error(f"盈亏金额解析失败: {raw}", code=3)
            return
        branches.append({"country": name, "amount": amount})

    # 分国弥补:同一国多项目可互抵(已在输入合并);不同国不互抵
    # 把同国合并
    from collections import defaultdict
    by_country = defaultdict(float)
    for b in branches:
        by_country[b["country"]] += b["amount"]

    per_country = []
    taxable_foreign = 0.0  # 计入境内应税的境外正所得(已弥补该国亏损后)
    unrecovered_losses = []
    for country, net in by_country.items():
        if net >= 0:
            # 该国净盈利,计入应税
            per_country.append({"country": country, "net": round2(net),
                                "treatment": f"净盈利 {round2(net)},计入境内应税"})
            taxable_foreign += net
        else:
            # 该国净亏损,不得抵减境内或他国,无限期结转
            per_country.append({"country": country, "net": round2(net),
                                "treatment": f"净亏损 {round2(abs(net))},不得抵减境内/他国盈利,无限期结转(限该国未来盈利)"})
            unrecovered_losses.append({"country": country, "unrecovered": round2(abs(net))})

    china_taxable = domestic + taxable_foreign
    china_tax = china_taxable * china_rate

    result = {
        "type": "overseas-loss(境外亏损弥补)",
        "domestic_income": round2(domestic),
        "branches": per_country,
        "taxable_foreign_income_positive": round2(taxable_foreign),
        "china_taxable_income": round2(china_taxable),
        "china_tax_provisional": round2(china_tax),
        "unrecovered_losses_carryforward": unrecovered_losses,
        "formula": ("境外亏损分国弥补(同国多项目可互抵); 净盈利计入境内应税; "
                    "净亏损不得抵减境内或他国盈利,无限期结转(限该国未来盈利)"),
        "key_warning": "⚠️ 境外亏损分国弥补是反避税重点,企业常误将境外亏损抵减境内盈利",
        "legal_basis": "企业所得税法第17条(境外亏损不得抵减境内盈利); 财税〔2009〕125号(分国弥补)",
        "verify_status": FTC_VERIFY_NOTE,
    }
    emit_success(result)


# ============================================================
# 主入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="跨境服务贸易涉税计算器(确定性计算,输出JSON)")
    sub = parser.add_subparsers(dest="command", required=True)

    # wht.calc
    p1 = sub.add_parser("wht.calc", help="代扣代缴企业所得税")
    p1.add_argument("--income", required=True, help="合同金额(人民币)")
    p1.add_argument("--legal-rate", required=True, help="法定税率,如0.10或10%%")
    p1.add_argument("--treaty-rate", help="协定优惠税率,如0.07或7%%")
    p1.add_argument("--gross", action="store_true", help="合同价为含税总价(gross)")
    p1.add_argument("--net", action="store_true", help="合同价为税后净价(net,税款额外承担)")
    p1.add_argument("--apply-treaty", action="store_true", help="适用协定优惠税率(默认用法定)")
    p1.set_defaults(func=cmd_wht_calc)

    # vat.classify
    p2 = sub.add_parser("vat.classify", help="增值税归类")
    p2.add_argument("--service-type", required=True, help="服务类型,如 现代服务/技术咨询/国际运输")
    p2.add_argument("--consumption-location", required=True,
                    help="消费地: inbound(境内消费)/outbound(境外消费)")
    p2.set_defaults(func=cmd_vat_classify)

    # vat.calc
    p3 = sub.add_parser("vat.calc", help="增值税应纳税额(一般计税)")
    p3.add_argument("--sales-incl", help="含税销售额")
    p3.add_argument("--sales-excl", help="不含税销售额")
    p3.add_argument("--rate", default="0.06", help="税率,如0.06或6%%(默认6%%)")
    p3.add_argument("--input-tax", default="0", help="进项税额(默认0)")
    p3.set_defaults(func=cmd_vat_calc)

    # treaty.lookup
    p4 = sub.add_parser("treaty.lookup", help="协定税率查询(内置常见协定,非权威)")
    p4.add_argument("--country", required=True, help="对方国家/地区,如 新加坡/中国香港/美国")
    p4.add_argument("--income-type", required=True,
                    help="所得类型: dividend/interest/royalty/tech_service/business_profit")
    p4.set_defaults(func=cmd_treaty_lookup)

    # treaty.check
    p5 = sub.add_parser("treaty.check", help="协定税率表时效性检查(检测是否过期)")
    p5.set_defaults(func=cmd_treaty_check)

    # ftc.calc — 境外税收抵免(直接/间接/分国vs综合/饶让/境外亏损)
    p6 = sub.add_parser("ftc.calc", help="境外税收抵免计算(5 种模式)")
    p6.add_argument("--type", required=True,
                    help="抵免类型: direct(直接)/indirect(间接)/compare(分国vs综合)/sparing(饶让)/overseas-loss(境外亏损)")
    p6.add_argument("--china-rate", help="中国企业所得税率,默认0.25(如0.25或25%%)")
    # direct / sparing 用
    p6.add_argument("--foreign-income", help="[direct] 境外所得(人民币)")
    p6.add_argument("--foreign-tax-paid", help="[direct] 境外已纳税款")
    p6.add_argument("--dividend", help="[sparing] 分得利润(人民币)")
    p6.add_argument("--sparing-rate", help="[sparing] 饶让视同税率(协定法定率,如0.20或20%%)")
    p6.add_argument("--actual-foreign-tax", help="[sparing] 实际已缴境外税(默认0,免征场景)")
    # indirect 用
    p6.add_argument("--dividend-gross", help="[indirect] 分得毛股息(税前,人民币)")
    p6.add_argument("--foreign-corp-rate", help="[indirect] 境外公司企业所得税率,如0.30")
    p6.add_argument("--withholding-rate", help="[indirect] 预提所得税率,如0.10(默认0)")
    p6.add_argument("--holding", help="[indirect] 持股比例,如0.50(低于20%%提示不适用)")
    # compare 用
    p6.add_argument("--countries", help="[compare] 多国,格式'国名:所得:实缴税率'逗号分隔,如 '甲:1000000:0.10,乙:2000000:0.35'")
    # overseas-loss 用
    p6.add_argument("--domestic", help="[overseas-loss] 境内所得(人民币)")
    p6.add_argument("--branches", help="[overseas-loss] 各国分支盈亏,格式'国名:盈亏'逗号分隔,亏损用负数,如 '甲:1000000,乙:-3000000,乙:600000'")
    p6.set_defaults(func=cmd_ftc_calc)

    args = parser.parse_args()

    # gross/net 互斥
    if getattr(args, "gross", False) and getattr(args, "net", False):
        emit_error("--gross 与 --net 互斥,只能选一个", code=1)
    if hasattr(args, "gross") and not args.gross and not args.net:
        # 默认 gross
        args.gross = True

    args.func(args)


if __name__ == "__main__":
    main()

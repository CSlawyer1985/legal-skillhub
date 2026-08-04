#!/usr/bin/env python3
"""
企查查/天眼查企业信用评分计算脚本
基于多维度数据量化企业信用等级（12维度评分体系，满分100分）

核心规则（HARD RULES）：
1. ST/*ST名称标识仅对上市公司生效，非上市公司绝不检查
2. 一票否决时综合评分 = 0（数字零，不是N/A）
3. 数据缺失 ≠ 表现差，采用推断评分策略给出保守中间分而非0分
4. 非上市公司时，"上市公司资讯"维度的4分自动再分配至：
   财务健康(+2, 15→17)、基础实力(+1, 12→13)、行业地位(+1, 6→7)
"""

import json
import sys
from datetime import datetime, date
from typing import Optional


# ============================================================
# 数据不足推断评分策略
# ============================================================
# 当某维度完全无数据时，不直接给0分（0分意味着"表现差"），
# 而是根据可用上下文推断一个保守中间分，并标记为"推断评分"。
#
# 推断规则：
# 1. 有完整数据 → 正常评分，标记 score_type="actual"
# 2. 部分子指标缺失 → 已有指标正常评，缺失指标用上下文推断，标记 score_type="partial"
# 3. 完全无数据 → 根据公司规模/行业/年限等上下文给保守分，标记 score_type="inferred"
#
# 推断评分的保守基准：
# - 一般取该维度满分的 30%~50%，具体取决于可推断的上下文线索
# - 推断评分会在报告中明确标注，提示用户此维度数据不充分

def infer_from_context(data: dict) -> dict:
    """
    从已有数据中提取可用的上下文线索，用于推断缺失维度。
    返回一个 dict，包含各种推断特征。
    """
    context = {}

    # 注册资本（万元）
    capital = parse_capital(data.get("registered_capital", 0))
    context["capital_large"] = capital >= 5000  # 大资本
    context["capital_medium"] = 1000 <= capital < 5000  # 中等资本

    # 成立年限
    establish_date = data.get("establish_date", "")
    years = 0
    if establish_date:
        try:
            if isinstance(establish_date, str):
                dt = datetime.strptime(establish_date[:10], "%Y-%m-%d")
            elif isinstance(establish_date, date):
                dt = datetime.combine(establish_date, datetime.min.time())
            else:
                dt = None
            if dt:
                years = (datetime.now() - dt).days / 365.25
        except (ValueError, TypeError):
            pass
    context["years_old"] = years
    context["long_established"] = years >= 10  # 成立10年以上

    # 分支机构
    branches = data.get("branches", [])
    context["has_branches"] = len(branches) > 0 if isinstance(branches, list) else False

    # 经营状态正常
    status = data.get("registration_status", "")
    context["normal_status"] = any(kw in status for kw in ["存续", "在营", "在业", "正常"]) if status else False

    # 对外投资
    investments = data.get("external_investments", [])
    context["has_investments"] = len(investments) > 0 if isinstance(investments, list) else False

    # 是否上市
    context["is_listed"] = data.get("is_listed", False)

    # 行业/经营范围（用于推断是否技术型企业）
    business_scope = data.get("business_scope", "")
    company_name = data.get("company_name", "")
    tech_keywords = ["软件", "技术", "科技", "信息", "数据", "智能", "互联网", "电子", "通信", "研发"]
    scope_tech = any(kw in business_scope for kw in tech_keywords) if business_scope else False
    name_tech = any(kw in company_name for kw in tech_keywords) if company_name else False
    context["likely_tech"] = scope_tech or name_tech

    return context


def check_veto(company_data: dict) -> Optional[dict]:
    """
    检查是否触发重大风险一票否决条件。
    ST/*ST名称标识仅对已上市公司检查。
    返回None表示未触发，返回dict表示触发并包含原因。
    """
    reasons = []

    # 检查1：登记状态异常（适用所有企业）
    status = company_data.get("registration_status", "")
    abnormal_statuses = ["吊销", "注销", "停业", "迁出", "清算", "废止"]
    if status and any(s in status for s in abnormal_statuses):
        reasons.append(f"登记状态异常：{status}")

    # 检查2：注册资本为0（适用所有企业）
    registered_capital = company_data.get("registered_capital", "")
    if registered_capital == 0 or registered_capital == "0":
        reasons.append("注册资本为0")

    # 检查3：经营异常（适用所有企业）
    if company_data.get("abnormal_operation"):
        reasons.append("企业被列入经营异常名录")

    # 检查4：严重违法失信（适用所有企业）
    if company_data.get("serious_illegal"):
        reasons.append("企业被列入严重违法失信名单")

    # 检查5：未实缴资本（适用所有企业）
    if company_data.get("unpaid_capital", False):
        reasons.append("注册资本未实缴")

    # 检查6：ST 名称标识（仅限上市公司）
    is_listed = company_data.get("is_listed", False)
    if is_listed:
        import re
        name = company_data.get("company_name", "")
        stock_name = company_data.get("stock_name", "")
        check_text = f"{name} {stock_name}".strip()
        st_pattern = r'(?:^|[\s\(（])\*?ST[\*\s]|^\*?ST'
        if re.search(st_pattern, check_text, re.IGNORECASE):
            reasons.append(f"上市公司包含ST警示标识：名称={name}，股票简称={stock_name or '未知'}")

    if reasons:
        return {
            "triggered": True,
            "reasons": reasons,
            "credit_grade": "D",
            "score": 0,  # 一票否决时评分为0，不是N/A
            "recommendation": "谨慎合作，建议进行更深入的风险尽调"
        }
    return None


def parse_capital(capital_str) -> float:
    """
    解析注册资本字符串为万元数值。
    """
    if capital_str is None:
        return 0
    if isinstance(capital_str, (int, float)):
        return float(capital_str)

    capital_str = str(capital_str).strip()
    if not capital_str or capital_str in ["-", "未知", ""]:
        return 0

    import re
    numbers = re.findall(r'[\d.]+', capital_str)
    if not numbers:
        return 0

    value = float(numbers[0])

    if "亿" in capital_str:
        value *= 10000
    elif "万" not in capital_str and value < 1000:
        value /= 10000

    return value


def score_basic_strength(data: dict) -> tuple:
    """评分：基础实力（满分12分）"""
    score = 0
    details = []

    # 注册资本（0-4分）
    capital = parse_capital(data.get("registered_capital", 0))
    if capital >= 10000:
        s = 4
    elif capital >= 5000:
        s = 3
    elif capital >= 1000:
        s = 2
    elif capital >= 100:
        s = 1
    else:
        s = 0
    score += s
    details.append(f"注册资本 {capital:.0f} 万元 -> {s}/4分")

    # 成立年限（0-4分）
    establish_date = data.get("establish_date", "")
    years = 0
    if establish_date:
        try:
            if isinstance(establish_date, str):
                dt = datetime.strptime(establish_date[:10], "%Y-%m-%d")
            elif isinstance(establish_date, date):
                dt = datetime.combine(establish_date, datetime.min.time())
            else:
                dt = None
            if dt:
                years = (datetime.now() - dt).days / 365.25
        except (ValueError, TypeError):
            pass

    if years >= 20:
        s = 4
    elif years >= 10:
        s = 3
    elif years >= 5:
        s = 2
    elif years >= 2:
        s = 1
    else:
        s = 0
    score += s
    details.append(f"成立年限 {years:.1f} 年 -> {s}/4分")

    # 登记状态（0-2分）
    status = data.get("registration_status", "")
    if status and any(kw in status for kw in ["存续", "在营", "在业", "正常"]):
        s = 2
    else:
        s = 0
    score += s
    details.append(f"登记状态 {status or '未知'} -> {s}/2分")

    # 分支机构（0-2分）
    branches = data.get("branches", [])
    branch_count = len(branches) if isinstance(branches, list) else 0
    if branch_count > 0:
        s = 2
    else:
        s = 0
    score += s
    details.append(f"分支机构 {branch_count} 家 -> {s}/2分")

    return score, details, "actual"


def score_financial_health(data: dict) -> tuple:
    """评分：财务健康（满分15分）——支持推断评分"""
    score = 0
    details = []
    score_type = "actual"

    financial = data.get("financial_data", {})
    if not financial:
        # ===== 数据不足：推断评分 =====
        # 根据注册资本、成立年限、经营状态等推断
        ctx = infer_from_context(data)
        inferred_reasons = []

        # 推断资产负债率（0-5分）
        # 大资本+长年限 → 偿债能力可能较好
        if ctx["capital_large"] and ctx["long_established"]:
            s_debt = 3  # 保守推断：中等偏上
            inferred_reasons.append("注册资本大+经营年限长，推断偿债能力中等偏上")
        elif ctx["capital_medium"]:
            s_debt = 2  # 保守推断：中等
            inferred_reasons.append("注册资本中等，推断偿债能力一般")
        else:
            s_debt = 1  # 保守推断：偏低
            inferred_reasons.append("注册资本较小，偿债能力存疑")

        # 推断营收规模（0-5分）
        # 有分支机构/对外投资 → 营收可能较大
        if ctx["has_branches"] or ctx["has_investments"]:
            s_revenue = 3
            inferred_reasons.append("有分支机构/对外投资，推断营收规模中等")
        elif ctx["capital_large"]:
            s_revenue = 3
            inferred_reasons.append("注册资本大，推断营收规模中等")
        else:
            s_revenue = 1
            inferred_reasons.append("无分支机构/投资，推断营收规模偏小")

        # 推断盈利能力（0-5分）
        # 正常经营多年 → 大概率盈利
        if ctx["long_established"] and ctx["normal_status"]:
            s_profit = 3
            inferred_reasons.append("经营10年+且状态正常，推断持续盈利")
        elif ctx["normal_status"]:
            s_profit = 2
            inferred_reasons.append("经营状态正常，推断可能盈利")
        else:
            s_profit = 1
            inferred_reasons.append("经营信息不足，盈利能力不确定")

        score = s_debt + s_revenue + s_profit
        details.append(f"[推断] 资产负债率 ~{s_debt}/5分")
        details.append(f"[推断] 营收规模 ~{s_revenue}/5分")
        details.append(f"[推断] 盈利能力 ~{s_profit}/5分")
        details.append(f"推断依据：{'; '.join(inferred_reasons)}")
        score_type = "inferred"
        return score, details, score_type

    # ===== 有数据：正常评分 =====
    # 资产负债率（0-5分）
    debt_ratio = financial.get("debt_asset_ratio")
    if debt_ratio is not None and str(debt_ratio).strip() != "":
        debt_ratio = float(str(debt_ratio).replace("%", "").replace("％", "").strip())
        if debt_ratio < 40:
            s = 5
        elif debt_ratio < 60:
            s = 4
        elif debt_ratio < 80:
            s = 2
        else:
            s = 0
        score += s
        details.append(f"资产负债率 {debt_ratio}% -> {s}/5分")
    else:
        # 子指标缺失：用上下文推断
        ctx = infer_from_context(data)
        if ctx["capital_large"] and ctx["long_established"]:
            s = 3
            details.append(f"资产负债率 [推断] -> {s}/5分（依据：资本大+年限长）")
        else:
            s = 1
            details.append(f"资产负债率 数据缺失 -> {s}/5分（保守推断）")
        score += s
        score_type = "partial"

    # 营收规模（0-5分）
    revenue = financial.get("revenue")
    if revenue is not None:
        revenue = parse_capital(revenue)
        if revenue >= 100000:
            s = 5
        elif revenue >= 10000:
            s = 4
        elif revenue >= 1000:
            s = 3
        elif revenue >= 100:
            s = 1
        else:
            s = 0
        score += s
        details.append(f"营收规模 {revenue:.0f} 万元 -> {s}/5分")
    else:
        ctx = infer_from_context(data)
        if ctx["has_branches"] or ctx["has_investments"]:
            s = 3
            details.append(f"营收规模 [推断] -> {s}/5分（依据：有分支机构/投资）")
        else:
            s = 1
            details.append(f"营收规模 数据缺失 -> {s}/5分（保守推断）")
        score += s
        score_type = "partial"

    # 盈利能力（0-5分）
    net_profit = financial.get("net_profit")
    profit_growth = financial.get("profit_growth")
    if net_profit is not None:
        import re
        np_str = str(net_profit).replace(",", "").strip()
        np_match = re.search(r'[-+]?[\d.]+', np_str)
        net_profit = float(np_match.group()) if np_match else 0.0
        if net_profit > 0:
            if profit_growth and float(str(profit_growth).replace("%", "").replace("％", "")) > 0:
                s = 5
            else:
                s = 3
        else:
            s = 0
        score += s
        details.append(f"净利润 {'正' if net_profit > 0 else '负'} {'增长' if profit_growth and float(str(profit_growth).replace('%', '').replace('％', '')) > 0 else '下降'} -> {s}/5分")
    else:
        ctx = infer_from_context(data)
        if ctx["long_established"] and ctx["normal_status"]:
            s = 3
            details.append(f"盈利能力 [推断] -> {s}/5分（依据：经营多年+状态正常）")
        else:
            s = 1
            details.append(f"盈利能力 数据缺失 -> {s}/5分（保守推断）")
        score += s
        score_type = "partial"

    return score, details, score_type


def score_business_stability(data: dict) -> tuple:
    """评分：经营稳定性（满分10分）"""
    score = 0
    details = []

    # 变更频率（0-5分）
    changes = data.get("change_records", [])
    change_count = len(changes) if isinstance(changes, list) else 0
    if change_count <= 2:
        s = 5
    elif change_count <= 5:
        s = 3
    elif change_count <= 10:
        s = 1
    else:
        s = 0
    score += s
    details.append(f"近3年变更次数 {change_count} 次 -> {s}/5分")

    # 年报披露（0-5分）
    annual_reports = data.get("annual_reports", [])
    if isinstance(annual_reports, list):
        report_count = len(annual_reports)
        if report_count >= 3:
            s = 5
        elif report_count >= 1:
            s = 2
        else:
            s = 0
    else:
        report_count = 0
        s = 0
    score += s
    details.append(f"年报披露 {report_count} 份 -> {s}/5分")

    return score, details, "actual"


def score_equity_structure(data: dict) -> tuple:
    """评分：股权结构（满分8分）"""
    score = 0
    details = []

    # 控制人清晰度（0-4分）
    controller = data.get("actual_controller", "")
    if controller and controller not in ["", "-", "未知", "暂无"]:
        controller_text = str(controller)
        if "穿透" in controller_text or "多层" in controller_text:
            s = 2
        else:
            s = 4
    else:
        s = 0
    score += s
    details.append(f"实际控制人 {'清晰' if s >= 4 else '多层嵌套' if s > 0 else '不明确'} -> {s}/4分")

    # 出资情况（0-4分）
    shareholders = data.get("shareholders", [])
    if isinstance(shareholders, list) and shareholders:
        all_paid = all(sh.get("paid", True) for sh in shareholders if isinstance(sh, dict))
        if all_paid:
            s = 4
        else:
            s = 2
    else:
        s = 0
    score += s
    details.append(f"出资情况 {'全部实缴' if s == 4 else '部分实缴' if s == 2 else '数据不足'} -> {s}/4分")

    return score, details, "actual"


def score_management(data: dict) -> tuple:
    """评分：管理团队（满分7分）"""
    score = 0
    details = []

    # 团队规模（0-4分）
    personnel = data.get("key_personnel", [])
    count = len(personnel) if isinstance(personnel, list) else 0
    if count >= 5:
        s = 4
    elif count >= 3:
        s = 2
    else:
        s = 1
    score += s
    details.append(f"董监高人数 {count} 人 -> {s}/4分")

    # 变更频率（0-3分）
    changes = data.get("personnel_changes", 0)
    if isinstance(changes, int):
        if changes == 0:
            s = 3
        elif changes <= 2:
            s = 1
        else:
            s = 0
    else:
        s = 1  # 无数据给中间分
    score += s
    details.append(f"近3年高管变更 {'无' if changes == 0 else changes} 次 -> {s}/3分")

    return score, details, "actual"


def score_transparency(data: dict) -> tuple:
    """评分：信息透明度（满分7分）"""
    score = 0
    details = []

    contact = data.get("contact_info", {})
    has_phone = bool(contact.get("phone"))
    has_email = bool(contact.get("email"))
    has_website = bool(contact.get("website"))
    contact_score = sum([has_phone, has_email, has_website])

    if contact_score == 3:
        s = 3
    elif contact_score >= 2:
        s = 2
    else:
        s = 0
    score += s
    details.append(f"联系方式完整度 {'齐全' if contact_score == 3 else str(contact_score) + '项'} -> {s}/3分")

    # 信息丰富度（0-2分）
    data_dimensions = data.get("data_dimensions", 0)
    if data_dimensions >= 8:
        s = 2
    elif data_dimensions >= 5:
        s = 1
    else:
        s = 0
    score += s
    details.append(f"数据维度覆盖 {data_dimensions} 项 -> {s}/2分")

    # 年报详细度（0-2分）
    annual_detail = data.get("annual_report_detail", "")
    if annual_detail == "详细":
        s = 2
    elif annual_detail == "基本":
        s = 1
    else:
        s = 0
    score += s
    details.append(f"年报详细度 {annual_detail or '无'} -> {s}/2分")

    return score, details, "actual"


def score_compliance(data: dict) -> tuple:
    """评分：合规与风险（满分10分）"""
    score = 0
    details = []

    # 行政处罚（0-5分）
    penalties = data.get("administrative_penalties", [])
    penalty_count = len(penalties) if isinstance(penalties, list) else 0
    if penalty_count == 0:
        s = 5
    elif penalty_count <= 2:
        s = 2
    else:
        s = 0
    score += s
    details.append(f"行政处罚 {penalty_count} 条 -> {s}/5分")

    # 司法案件（0-5分）
    lawsuits = data.get("lawsuits", [])
    lawsuit_count = len(lawsuits) if isinstance(lawsuits, list) else 0
    if lawsuit_count == 0:
        s = 5
    else:
        defendant_count = sum(1 for l in lawsuits if isinstance(l, dict) and "被告" in str(l.get("role", "")))
        if defendant_count == 0 and lawsuit_count > 0:
            s = 3  # 主要作为原告
        elif defendant_count <= 2:
            s = 1
        else:
            s = 0
    score += s
    details.append(f"司法案件 {lawsuit_count} 条 -> {s}/5分")

    return score, details, "actual"


def score_intellectual_property(data: dict) -> tuple:
    """评分：知识产权（满分8分）——支持推断评分"""
    score = 0
    details = []
    score_type = "actual"

    ip_data = data.get("ip_data", {})
    if not ip_data:
        # ===== 数据不足：推断评分 =====
        ctx = infer_from_context(data)

        # 推断专利数量（0-3分）
        # 技术型企业+大公司 → 专利可能较多
        if ctx.get("likely_tech") and ctx["capital_large"]:
            s_patent = 2  # 推断可能有较多专利
            details.append(f"[推断] 专利数量 ~{s_patent}/3分（依据：技术型企业+资本大）")
        elif ctx.get("likely_tech"):
            s_patent = 1  # 技术企业但规模不确定
            details.append(f"[推断] 专利数量 ~{s_patent}/3分（依据：技术型企业）")
        else:
            s_patent = 1  # 非技术企业，给保守分
            details.append(f"[推断] 专利数量 ~{s_patent}/3分（依据：非明确技术企业，保守推断）")

        # 推断专利质量（0-2分）
        s_quality = 1  # 保守推断
        details.append(f"[推断] 发明专利占比 ~{s_quality}/2分（保守推断）")

        # 推断商标+软著（0-3分）
        if ctx["capital_large"] or ctx["has_branches"]:
            s_non_patent = 2  # 大公司通常有较多商标
            details.append(f"[推断] 商标+软著 ~{s_non_patent}/3分（依据：公司规模大）")
        else:
            s_non_patent = 1
            details.append(f"[推断] 商标+软著 ~{s_non_patent}/3分（保守推断）")

        score = s_patent + s_quality + s_non_patent
        score_type = "inferred"
        return score, details, score_type

    # ===== 有数据：正常评分 =====
    # 专利数量（0-3分）
    patents = ip_data.get("patent_count", 0)
    if patents >= 20:
        s = 3
    elif patents >= 10:
        s = 2
    elif patents >= 1:
        s = 1
    else:
        s = 0
    score += s
    details.append(f"专利数量 {patents} 件 -> {s}/3分")

    # 专利质量——发明占比（0-2分）
    invention_patents = ip_data.get("invention_patent_count", 0)
    if patents > 0 and invention_patents > 0:
        invention_ratio = invention_patents / patents
        if invention_ratio >= 0.3:
            s = 2
        elif invention_ratio >= 0.1:
            s = 1
        else:
            s = 0
        details.append(f"发明专利占比 {invention_ratio:.0%} ({invention_patents}/{patents}) -> {s}/2分")
    else:
        s = 0
        details.append(f"发明专利占比 无发明专利 -> {s}/2分")
    score += s

    # 商标+软著数量（0-3分）
    softwares = ip_data.get("software_copyright_count", 0)
    trademarks = ip_data.get("trademark_count", 0)
    total_non_patent = softwares + trademarks
    if total_non_patent >= 30:
        s = 3
    elif total_non_patent >= 10:
        s = 2
    elif total_non_patent >= 1:
        s = 1
    else:
        s = 0
    score += s
    details.append(f"商标+软著 {total_non_patent} 件（软著{softwares}/商标{trademarks}） -> {s}/3分")

    return score, details, score_type


def score_business_vitality(data: dict) -> tuple:
    """评分：经营活力（满分7分）——支持推断评分"""
    score = 0
    details = []
    score_type = "actual"

    vitality = data.get("business_vitality", {})

    if not vitality:
        # ===== 数据不足：推断评分 =====
        ctx = infer_from_context(data)

        # 推断招聘频率（0-3分）
        # 大公司+正常经营 → 持续招聘可能性高
        if ctx["capital_large"] and ctx["normal_status"]:
            s_recruit = 2  # 推断有招聘活动
            details.append(f"[推断] 招聘频率 ~{s_recruit}/3分（依据：大公司+正常经营）")
        elif ctx["normal_status"]:
            s_recruit = 1  # 小公司也可能招聘
            details.append(f"[推断] 招聘频率 ~{s_recruit}/3分（依据：正常经营）")
        else:
            s_recruit = 0
            details.append(f"[推断] 招聘频率 ~{s_recruit}/3分（信息不足）")

        # 推断招聘岗位类型（0-2分）
        if ctx.get("likely_tech"):
            s_job = 1  # 技术企业可能招技术岗
            details.append(f"[推断] 招聘岗位类型 ~{s_job}/2分（依据：技术型企业）")
        else:
            s_job = 1  # 保守推断
            details.append(f"[推断] 招聘岗位类型 ~{s_job}/2分（保守推断）")

        # 推断社保趋势（0-2分）
        if ctx["long_established"] and ctx["normal_status"]:
            s_social = 1  # 长期经营+正常 → 稳定
            details.append(f"[推断] 社保趋势 ~{s_social}/2分（依据：经营多年+正常状态→推断稳定）")
        else:
            s_social = 0
            details.append(f"[推断] 社保趋势 ~{s_social}/2分（信息不足）")

        score = s_recruit + s_job + s_social
        score_type = "inferred"
        return score, details, score_type

    # ===== 有数据：正常评分 =====
    # 招聘频率（0-3分）
    recruitment = vitality.get("recruitment_active", "")
    if recruitment == "活跃":
        s = 3
    elif recruitment == "一般":
        s = 2
    else:
        s = 0
    score += s
    details.append(f"招聘频率 {recruitment or '无数据'} -> {s}/3分")

    # 招聘岗位类型（0-2分）
    job_type = vitality.get("recruitment_job_type", "")
    if job_type in ["技术/管理岗为主", "技术岗为主"]:
        s = 2
    elif job_type in ["基础岗位为主", "综合岗位"]:
        s = 1
    else:
        s = 0
    score += s
    details.append(f"招聘岗位类型 {job_type or '无数据'} -> {s}/2分")

    # 社保人数趋势（0-2分）
    social_insurance = vitality.get("social_insurance_trend", "")
    if social_insurance == "增长":
        s = 2
    elif social_insurance == "稳定":
        s = 1
    else:
        s = 0
    score += s
    details.append(f"社保人数趋势 {social_insurance or '无数据'} -> {s}/2分")

    return score, details, score_type


def score_industry_status(data: dict) -> tuple:
    """评分：行业地位（满分6分）——支持推断评分"""
    score = 0
    details = []
    score_type = "actual"

    industry = data.get("industry_status", {})

    if not industry:
        # ===== 数据不足：推断评分 =====
        ctx = infer_from_context(data)

        # 推断行业协会（0-2分）
        if ctx["capital_large"] and ctx["has_branches"]:
            s_assoc = 1  # 大公司可能参与协会
            details.append(f"[推断] 行业协会 ~{s_assoc}/2分（依据：大公司可能参与协会）")
        elif ctx["capital_large"]:
            s_assoc = 1  # 大资本公司可能参与
            details.append(f"[推断] 行业协会 ~{s_assoc}/2分（依据：注册资本大→可能参与协会）")
        else:
            s_assoc = 0
            details.append(f"[推断] 行业协会 ~{s_assoc}/2分（信息不足）")

        # 推断资质认证（0-2分）
        if ctx["capital_large"] and ctx["long_established"]:
            s_qual = 1  # 大公司+老公司大概率有基本资质
            details.append(f"[推断] 资质认证 ~{s_qual}/2分（依据：大公司+老公司→可能有资质）")
        elif ctx.get("likely_tech"):
            s_qual = 1  # 技术企业可能有高新认证
            details.append(f"[推断] 资质认证 ~{s_qual}/2分（依据：技术企业→可能高新认证）")
        elif ctx["long_established"]:
            s_qual = 1  # 经营多年的企业通常有基本资质
            details.append(f"[推断] 资质认证 ~{s_qual}/2分（依据：经营多年→可能有基本资质）")
        else:
            s_qual = 0
            details.append(f"[推断] 资质认证 ~{s_qual}/2分（信息不足）")

        # 推断荣誉/排名（0-2分）
        if ctx["is_listed"]:
            s_awards = 1  # 上市公司有一定行业地位
            details.append(f"[推断] 荣誉/排名 ~{s_awards}/2分（依据：上市公司→有一定行业地位）")
        elif ctx["capital_large"] and ctx["has_branches"]:
            s_awards = 1  # 大型非上市公司也可能有行业认可
            details.append(f"[推断] 荣誉/排名 ~{s_awards}/2分（依据：大型企业→可能有行业认可）")
        else:
            s_awards = 0
            details.append(f"[推断] 荣誉/排名 ~{s_awards}/2分（信息不足）")

        score = s_assoc + s_qual + s_awards
        score_type = "inferred"
        return score, details, score_type

    # ===== 有数据：正常评分 =====
    # 行业协会（0-2分）
    association = industry.get("association", "")
    if association in ["国家级", "国家级协会成员/理事"]:
        s = 2
    elif association in ["地方级", "地方协会成员"]:
        s = 1
    else:
        s = 0
    score += s
    details.append(f"行业协会 {association or '未参与'} -> {s}/2分")

    # 资质认证（0-2分）
    qualification = industry.get("qualification", "")
    if qualification in ["高级", "高新/专精特新/独角兽"]:
        s = 2
    elif qualification == "基础":
        s = 1
    else:
        s = 0
    score += s
    details.append(f"资质认证 {qualification or '无'} -> {s}/2分")

    # 荣誉/排名（0-2分）
    awards = industry.get("awards", 0)
    ranking = industry.get("industry_ranking", "")
    has_award_or_ranking = (awards > 0 if isinstance(awards, int) else False) or bool(ranking)
    s = 2 if has_award_or_ranking else 0
    score += s
    detail_text = ""
    if isinstance(awards, int) and awards > 0:
        detail_text += f"奖项{awards}项"
    if ranking:
        detail_text += f" 排名:{ranking}"
    details.append(f"荣誉/排名 {detail_text or '无'} -> {s}/2分")

    return score, details, score_type


def score_public_reputation(data: dict) -> tuple:
    """评分：舆论声誉（满分6分）——支持推断评分"""
    score = 0
    details = []
    score_type = "actual"

    reputation = data.get("public_reputation", {})

    if not reputation:
        # ===== 数据不足：推断评分 =====
        ctx = infer_from_context(data)

        # 推断负面舆情（0-3分）
        # 企查查未返回诉讼/处罚记录 → 推断无重大负面
        # 但这不是确定的，需要保守
        lawsuits = data.get("lawsuits", [])
        penalties = data.get("administrative_penalties", [])
        lawsuit_count = len(lawsuits) if isinstance(lawsuits, list) else 0
        penalty_count = len(penalties) if isinstance(penalties, list) else 0

        if lawsuit_count == 0 and penalty_count == 0:
            s_negative = 2  # 无已知诉讼/处罚 → 推断无重大负面
            details.append(f"[推断] 负面舆情 ~{s_negative}/3分（依据：无已知诉讼/处罚记录）")
        elif lawsuit_count <= 3 and penalty_count == 0:
            s_negative = 1  # 少量诉讼
            details.append(f"[推断] 负面舆情 ~{s_negative}/3分（依据：少量诉讼，无处罚）")
        else:
            s_negative = 0
            details.append(f"[推断] 负面舆情 ~{s_negative}/3分（依据：有较多诉讼/处罚）")

        # 推断品牌声量（0-2分）
        if ctx["is_listed"] or ctx["capital_large"]:
            s_brand = 1  # 上市/大公司有一定知名度
            details.append(f"[推断] 品牌声量 ~{s_brand}/2分（依据：{'上市公司' if ctx['is_listed'] else '大公司'}→有一定知名度）")
        else:
            s_brand = 0
            details.append(f"[推断] 品牌声量 ~{s_brand}/2分（信息不足）")

        # 推断诉讼舆论影响（0-1分）
        if lawsuit_count <= 3:
            s_lawsuit = 1  # 少量诉讼不太可能引发舆论
            details.append(f"[推断] 诉讼/纠纷舆论 ~{s_lawsuit}/1分（依据：诉讼少→舆论影响小）")
        else:
            s_lawsuit = 0
            details.append(f"[推断] 诉讼/纠纷舆论 ~{s_lawsuit}/1分（依据：诉讼较多）")

        score = s_negative + s_brand + s_lawsuit
        score_type = "inferred"
        return score, details, score_type

    # ===== 有数据：正常评分 =====
    # 负面舆情（0-3分）
    negative_news = reputation.get("negative_news", "")
    if negative_news == "无":
        s = 3
    elif negative_news == "轻微":
        s = 1
    else:
        s = 0
    score += s
    details.append(f"负面舆情 {negative_news or '有重大负面'} -> {s}/3分")

    # 品牌声量（0-2分）
    brand_visibility = reputation.get("brand_visibility", "")
    if brand_visibility == "高":
        s = 2
    elif brand_visibility == "一般":
        s = 1
    else:
        s = 0
    score += s
    details.append(f"品牌声量 {brand_visibility or '无公开信息'} -> {s}/2分")

    # 诉讼/纠纷舆论影响（0-1分）
    lawsuit_reputation = reputation.get("lawsuit_reputation", "")
    if lawsuit_reputation in ["无", "无舆论影响", ""]:
        s = 1
    else:
        s = 0
    score += s
    details.append(f"诉讼/纠纷舆论 {lawsuit_reputation or '无舆论影响'} -> {s}/1分")

    return score, details, score_type


def score_listed_company_info(data: dict) -> tuple:
    """评分：上市公司资讯（满分4分）——仅适用于已上市企业"""
    score = 0
    details = []

    is_listed = data.get("is_listed", False)
    if not is_listed:
        return 0, ["非上市企业，此维度不适用"], "not_applicable"

    listed_info = data.get("listed_company_info", {})
    if not listed_info:
        # 上市但无资讯数据 → 保守推断
        details.append("[推断] 股票表现 ~1/2分（上市公司但无股价数据，保守推断）")
        details.append("[推断] 机构评级 ~1/2分（上市公司但无研报数据，保守推断）")
        return 2, details, "inferred"

    score_type = "actual"

    # 股票表现（0-2分）
    stock_performance = listed_info.get("stock_performance", "")
    if stock_performance in ["上涨", "持平", "正收益"]:
        s = 2
    elif stock_performance in ["下跌", "负收益"]:
        s = 1
    else:
        s = 0
    score += s
    details.append(f"股票表现 {stock_performance or '无数据'} -> {s}/2分")

    # 机构评级（0-2分）
    analyst_rating = listed_info.get("analyst_rating", "")
    if analyst_rating in ["正面", "买入", "增持", "推荐"]:
        s = 2
    elif analyst_rating in ["中性", "持有", "观望"]:
        s = 1
    else:
        s = 0
    score += s
    details.append(f"机构评级 {analyst_rating or '无机构覆盖'} -> {s}/2分")

    return score, details, score_type


def get_credit_grade(total_score: float) -> str:
    """根据总分映射信用等级"""
    if total_score >= 90:
        return "AAA"
    elif total_score >= 80:
        return "AA"
    elif total_score >= 70:
        return "A"
    elif total_score >= 60:
        return "BBB"
    elif total_score >= 50:
        return "BB"
    elif total_score >= 40:
        return "B"
    elif total_score >= 30:
        return "CCC"
    elif total_score >= 20:
        return "CC"
    elif total_score >= 1:
        return "C"
    else:
        return "D"


def get_rating_label(score: float, max_score: float) -> str:
    """单项维度评价"""
    ratio = score / max_score if max_score > 0 else 0
    if ratio >= 0.8:
        return "优"
    elif ratio >= 0.6:
        return "良"
    elif ratio >= 0.4:
        return "中"
    else:
        return "差"


def calculate_credit_score(company_data: dict) -> dict:
    """
    计算企业信用评分的入口函数（12维度评分体系，满分100分）。
    支持推断评分：数据不足时根据上下文推断保守中间分。

    非上市公司权重再分配：当 is_listed=False 时，"上市公司资讯"（4分）
    不参与评分，其4分按比例分配给其余11个维度，确保满分仍为100分。

    输出格式（JSON）：评分结果，每个维度包含 score_type 字段：
    - "actual": 基于实际数据评分
    - "partial": 部分子指标用推断评分
    - "inferred": 完全基于推断评分
    - "not_applicable": 该维度不适用（如非上市公司的"上市公司资讯"）
    """
    is_listed = company_data.get("is_listed", False)

    result = {
        "company_name": company_data.get("company_name", "未知企业"),
        "query_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "is_listed": is_listed,
    }

    # 1. 重大风险一票否决检查
    veto = check_veto(company_data)
    if veto:
        result.update(veto)
        result["score"] = 0  # 明确：一票否决评分为0，不是N/A
        result["dimensions"] = None
        return result

    # 2. 基础维度权重（满分定义）
    base_weights = {
        "基础实力": 12,
        "财务健康": 15,
        "经营稳定性": 10,
        "股权结构": 8,
        "管理团队": 7,
        "信息透明度": 7,
        "合规与风险": 10,
        "知识产权": 8,
        "经营活力": 7,
        "行业地位": 6,
        "舆论声誉": 6,
        "上市公司资讯": 4,
    }

    # 3. 非上市公司权重再分配
    # 当 is_listed=False 时，"上市公司资讯"的4分分配给其他关键维度
    # 分配策略：财务健康+2（最核心维度）、基础实力+1、行业地位+1
    redistributed_points = {}  # 记录再分配的详情
    effective_weights = dict(base_weights)

    if not is_listed:
        del effective_weights["上市公司资讯"]
        # 将4分分配给关键维度
        effective_weights["财务健康"] = effective_weights.get("财务健康", 15) + 2  # 15→17
        effective_weights["基础实力"] = effective_weights.get("基础实力", 12) + 1  # 12→13
        effective_weights["行业地位"] = effective_weights.get("行业地位", 6) + 1   # 6→7
        redistributed_points = {
            "来源": "上市公司资讯(4分)",
            "分配": {
                "财务健康": "+2(15→17)",
                "基础实力": "+1(12→13)",
                "行业地位": "+1(6→7)",
            },
            "原因": "非上市企业，上市公司资讯维度不适用"
        }

    # 4. 各维度评分
    dimensions = {}
    for name, max_s in base_weights.items():
        if name == "上市公司资讯" and not is_listed:
            dimensions[name] = {"score": 0, "max": 0, "details": ["非上市企业，此维度不适用，4分已再分配至财务健康(+2)、基础实力(+1)、行业地位(+1)"], "score_type": "not_applicable", "rating": "不适用"}
        else:
            dimensions[name] = {"score": 0, "max": effective_weights.get(name, max_s), "details": [], "score_type": "actual"}

    scoring_functions = [
        ("基础实力", score_basic_strength),
        ("财务健康", score_financial_health),
        ("经营稳定性", score_business_stability),
        ("股权结构", score_equity_structure),
        ("管理团队", score_management),
        ("信息透明度", score_transparency),
        ("合规与风险", score_compliance),
        ("知识产权", score_intellectual_property),
        ("经营活力", score_business_vitality),
        ("行业地位", score_industry_status),
        ("舆论声誉", score_public_reputation),
        ("上市公司资讯", score_listed_company_info),
    ]

    total_score = 0
    effective_max = 0
    effective_score = 0
    inferred_dimensions = []
    partial_dimensions = []

    for name, func in scoring_functions:
        if name == "上市公司资讯" and not is_listed:
            # 跳过非上市公司的该维度评分
            continue

        score, details, score_type = func(company_data)
        max_s = dimensions[name]["max"]

        # 非上市公司权重再分配：对获得额外分值的维度，按比例增加得分
        if not is_listed and name in redistributed_points.get("分配", {}):
            base_max = base_weights[name]
            extra_max = max_s - base_max
            if extra_max > 0 and score > 0:
                # 按现有得分比例计算额外得分
                ratio = score / base_max
                extra_score = round(ratio * extra_max, 1)
                # 确保不超过额外分值
                extra_score = min(extra_score, extra_max)
                score = score + extra_score
                details.append(f"[权重再分配] +{extra_score}分（来自上市公司资讯维度的{extra_max}分再分配）")

        dimensions[name]["score"] = score
        dimensions[name]["details"] = details
        dimensions[name]["score_type"] = score_type
        dimensions[name]["rating"] = get_rating_label(score, max_s)

        effective_max += max_s
        effective_score += score

        if score_type == "inferred":
            inferred_dimensions.append(name)
        elif score_type == "partial":
            partial_dimensions.append(name)

    # 5. 计算总分（满分100，通过等比折算）
    adjusted_score = round((effective_score / effective_max) * 100, 1) if effective_max > 0 else 0
    result["score"] = adjusted_score
    result["raw_score"] = round(effective_score, 1)
    result["effective_max"] = effective_max

    # 记录权重再分配信息
    if redistributed_points:
        result["weight_redistribution"] = redistributed_points

    # 记录推断评分信息
    if inferred_dimensions or partial_dimensions:
        all_inferred = inferred_dimensions + partial_dimensions
        result["inferred_dimensions"] = all_inferred
        result["inferred_note"] = f"以下维度使用了推断评分（基于上下文线索的保守估计）：{', '.join(all_inferred)}。建议补充实际数据以获得更准确评分。"

    result["credit_grade"] = get_credit_grade(result["score"])
    result["dimensions"] = dimensions

    # 6. 风险提示
    tips = []
    for name, info in dimensions.items():
        if info["score_type"] == "not_applicable":
            continue
        ratio = info["score"] / info["max"] if info["max"] > 0 else 0
        if ratio < 0.4:
            tips.append(f"【{name}】得分偏低（{info['score']}/{info['max']}），建议重点关注")

    if inferred_dimensions:
        tips.append(f"以下维度使用了推断评分：{', '.join(inferred_dimensions)}，建议补充实际数据验证")

    if result["score"] < 50:
        tips.append("综合评分低于50分，该企业整体信用状况不佳，建议审慎评估合作风险")
    elif result["score"] < 70:
        tips.append("综合评分处于中等水平，建议在合作前进行更详细的背景调查")

    result["risk_tips"] = tips

    return result


def main():
    """命令行入口：从 stdin 读取 JSON 或从文件读取"""
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        with open(input_file, "r", encoding="utf-8") as f:
            company_data = json.load(f)
    else:
        input_text = sys.stdin.read()
        company_data = json.loads(input_text)

    result = calculate_credit_score(company_data)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

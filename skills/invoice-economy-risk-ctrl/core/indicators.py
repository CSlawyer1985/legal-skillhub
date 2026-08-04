"""发票经济风控 · 15 项风控指标定义与计算逻辑

每个指标包含：元数据（id/name/category/weight/level/desc/advice）
以及纯函数 compute(invoices, context) -> dict。

所有企业名称/税号在调用方完成脱敏；本模块只做数值与规则判断。
"""

# 行业预警税负率（增值税/企业所得税，单位 %）—— 与 tax-risk-scanner 共享口径
INDUSTRY_BURDEN = {
    "制造业": {"vat": 2.5, "cst": 2.0},
    "商贸": {"vat": 0.8, "cst": 0.5},
    "软件信息技术服务": {"vat": 5.0, "cst": 8.0},
    "建筑业": {"vat": 2.0, "cst": 1.5},
    "房地产业": {"vat": 3.0, "cst": 2.5},
    "交通运输业": {"vat": 2.5, "cst": 1.0},
    "餐饮": {"vat": 3.0, "cst": 1.5},
}

# 指标元数据 + 权重（权重之和为 MAX_WEIGHT，用于加权评分）
MAX_WEIGHT = 110

INDICATORS = [
    {
        "id": "R001", "name": "顶格开票识别", "category": "金额异常", "weight": 8,
        "desc": "单张发票金额逼近开票限额（如 ≥ 99000 元），存在人为凑整、顶额开票嫌疑。",
        "advice": "核查大额顶格发票对应业务的真实性、合同与资金流，避免集中顶额开票。",
    },
    {
        "id": "R002", "name": "税负率预警", "category": "税负异常", "weight": 10,
        "desc": "实际税负率低于行业预警值，可能被金税四期标记为低税负异常企业。",
        "advice": "对照行业税负率评估合理性，排查隐匿收入、虚增成本或进项异常。",
    },
    {
        "id": "R003", "name": "顶格开票占比", "category": "金额异常", "weight": 6,
        "desc": "顶格开票张数占全部发票比例过高（>30%），呈系统性顶额开票特征。",
        "advice": "统计顶格开票占比，规范开票金额分布，避免被识别为异常开票模式。",
    },
    {
        "id": "R004", "name": "进销项不匹配", "category": "进销项", "weight": 10,
        "desc": "进项税额与销项税额金额偏离度过大（>30%），可能存在虚开进项或隐匿销项。",
        "advice": "逐笔核对进销项发票，确保业务真实、票流/物流/资金流三流一致。",
    },
    {
        "id": "R005", "name": "红冲发票异常", "category": "开票行为", "weight": 6,
        "desc": "红字冲销发票占比过高（>5%），可能被系统标记为异常开票行为。",
        "advice": "梳理红冲原因，规范开票流程，避免集中、大额、频繁红冲。",
    },
    {
        "id": "R006", "name": "滞留票风险", "category": "进销项", "weight": 5,
        "desc": "取得进项发票长期未抵扣（滞留票），可能存在票货分离、虚抵进项风险。",
        "advice": "核对滞留进项发票的业务与货物入库，及时合规抵扣或转出。",
    },
    {
        "id": "R007", "name": "无票成本占比过高", "category": "成本异常", "weight": 6,
        "desc": "无合规发票支撑的成本占比过高（>30%），虚增成本、侵蚀税基风险。",
        "advice": "补全成本发票链条，对确实无票支出按规定税前扣除或纳税调整。",
    },
    {
        "id": "R008", "name": "工资与社保不匹配", "category": "个税社保", "weight": 6,
        "desc": "工资总额与社保缴费基数差异过大（社保基数 < 工资 70%），存在少缴社保/个税风险。",
        "advice": "核对工资表与社保、个税申报，确保全员全额、基数合规。",
    },
    {
        "id": "R009", "name": "私户收款隐匿收入", "category": "收入异常", "weight": 10,
        "desc": "通过个人账户收取经营款项，隐匿销售收入，属高危偷税行为。",
        "advice": "全部经营收支通过公户结算，已私户收款的应补申报并补缴税款。",
    },
    {
        "id": "R010", "name": "库存账实不符", "category": "资产异常", "weight": 6,
        "desc": "账面库存与实物库存差异率过高（>10%），可能存在账外经营或虚增库存。",
        "advice": "定期盘点并账务调整，查找差异来源，确保账实一致。",
    },
    {
        "id": "R011", "name": "长亏不倒异常", "category": "经营异常", "weight": 7,
        "desc": "企业连续三年及以上亏损或微利（利润率<1%），长期不倒，易被重点核查。",
        "advice": "准备亏损原因说明与盈利计划，留存资料备查。",
    },
    {
        "id": "R012", "name": "进销项税率倒挂", "category": "进销项", "weight": 6,
        "desc": "平均进项税率高于平均销项税率，存在取得高税率专票抵低税率销项的倒挂嫌疑。",
        "advice": "检查进销项税率结构，核实业务实质与适用税率是否匹配。",
    },
    {
        "id": "R013", "name": "空壳企业风险", "category": "主体异常", "weight": 8,
        "desc": "成立时间短、交易笔数少、开票量突增，具备空壳/走逃（失联）企业特征。",
        "advice": "核实企业实际经营地址与人员，确保实名经营，避免被认定为异常户。",
    },
    {
        "id": "R014", "name": "关联交易转让定价异常", "category": "关联交易", "weight": 8,
        "desc": "关联交易金额占比过高（>30%）或定价偏离公允价值，转让定价不合规风险。",
        "advice": "准备同期资料，确保关联交易符合独立交易原则。",
    },
    {
        "id": "R015", "name": "循环开票嫌疑", "category": "关联交易", "weight": 8,
        "desc": "买卖双方形成闭环资金/票据循环（A→B→C→A），无真实货物流转，涉嫌虚开。",
        "advice": "切断循环开票链条，核查每一环业务真实性，保留完整证据链。",
    },
]

INDICATOR_MAP = {ind["id"]: ind for ind in INDICATORS}


# ============= 工具函数 =============
def _is_top_amount(amount):
    """顶格判断：金额逼近单张限额（>=99000）或呈 .99/.00 凑整"""
    if amount >= 99000:
        return True
    if 9900 <= amount < 10000 and (abs(amount - round(amount)) < 0.01 or str(amount).endswith(".99")):
        return True
    return False


def _safe_div(a, b):
    return (a / b) if b else 0.0


# ============= 各项指标 compute =============
def _compute_R001(invoices, ctx):
    tops = [iv for iv in invoices if _is_top_amount(float(iv.get("amount", 0) or 0))]
    hit = len(tops) > 0
    return {"hit": hit, "value": len(tops), "detail": f"命中顶格发票 {len(tops)} 张"}


def _compute_R002(invoices, ctx):
    sales = float(ctx.get("sales") or 0)
    tax = float(ctx.get("tax") or 0)
    industry = ctx.get("industry")
    if sales <= 0:
        return {"hit": False, "value": None, "detail": "缺少销售额数据，未评估"}
    burden = _safe_div(tax, sales) * 100
    warning = None
    if industry in INDUSTRY_BURDEN:
        warning = INDUSTRY_BURDEN[industry]["vat"]
    hit = (warning is not None and burden < warning) or (warning is None and burden < 1.0)
    return {"hit": hit, "value": round(burden, 2), "detail": f"实际增值税税负率 {burden:.2f}%" + (f"，行业预警线 {warning}%" if warning else "")}


def _compute_R003(invoices, ctx):
    if not invoices:
        return {"hit": False, "value": 0, "detail": "无发票数据"}
    tops = [iv for iv in invoices if _is_top_amount(float(iv.get("amount", 0) or 0))]
    ratio = _safe_div(len(tops), len(invoices)) * 100
    return {"hit": ratio > 30, "value": round(ratio, 1), "detail": f"顶格开票占比 {ratio:.1f}%"}


def _compute_R004(invoices, ctx):
    out = sum(float(iv.get("amount", 0) or 0) for iv in invoices if iv.get("type") == "销项")
    inp = sum(float(iv.get("amount", 0) or 0) for iv in invoices if iv.get("type") == "进项")
    base = max(out, inp)
    if base <= 0:
        return {"hit": False, "value": 0, "detail": "无可比进销项数据"}
    mismatch = _safe_div(abs(out - inp), base) * 100
    return {"hit": mismatch > 30, "value": round(mismatch, 1), "detail": f"进销项偏离度 {mismatch:.1f}%（销项 {out:.0f}/进项 {inp:.0f}）"}


def _compute_R005(invoices, ctx):
    if not invoices:
        return {"hit": False, "value": 0, "detail": "无发票数据"}
    reds = [iv for iv in invoices if iv.get("is_red")]
    ratio = _safe_div(len(reds), len(invoices)) * 100
    return {"hit": ratio > 5, "value": round(ratio, 1), "detail": f"红冲发票占比 {ratio:.1f}%"}


def _compute_R006(invoices, ctx):
    r = ctx.get("stuck_invoice_ratio")
    if r is None:
        return {"hit": False, "value": None, "detail": "缺少滞留票数据，未评估"}
    r = float(r)
    return {"hit": r > 10, "value": round(r, 1), "detail": f"滞留票占比 {r:.1f}%"}


def _compute_R007(invoices, ctx):
    nic = float(ctx.get("no_invoice_cost") or 0)
    tc = float(ctx.get("total_cost") or 0)
    if tc <= 0:
        return {"hit": False, "value": None, "detail": "缺少成本数据，未评估"}
    ratio = _safe_div(nic, tc) * 100
    return {"hit": ratio > 30, "value": round(ratio, 1), "detail": f"无票成本占比 {ratio:.1f}%"}


def _compute_R008(invoices, ctx):
    payroll = float(ctx.get("payroll") or 0)
    ss = float(ctx.get("social_security_base") or 0)
    if payroll <= 0:
        return {"hit": False, "value": None, "detail": "缺少工资数据，未评估"}
    ratio = _safe_div(ss, payroll) * 100
    return {"hit": ratio < 70, "value": round(ratio, 1), "detail": f"社保基数/工资比 {ratio:.1f}%"}


def _compute_R009(invoices, ctx):
    flag = ctx.get("is_private_account")
    if flag is None:
        return {"hit": False, "value": None, "detail": "未采集私户收款信息"}
    return {"hit": bool(flag), "value": 1 if flag else 0, "detail": "存在私户收款" if flag else "未发现私户收款"}


def _compute_R010(invoices, ctx):
    diff = float(ctx.get("inventory_diff") or 0)
    total = float(ctx.get("inventory_total") or 0)
    if total <= 0:
        return {"hit": False, "value": None, "detail": "缺少库存数据，未评估"}
    ratio = _safe_div(diff, total) * 100
    return {"hit": ratio > 10, "value": round(ratio, 1), "detail": f"库存账实差异率 {ratio:.1f}%"}


def _compute_R011(invoices, ctx):
    loss_years = int(ctx.get("loss_years") or 0)
    profit = ctx.get("profit")
    if loss_years >= 3:
        return {"hit": True, "value": loss_years, "detail": f"连续亏损 {loss_years} 年"}
    if profit is not None and float(profit) < 0:
        return {"hit": True, "value": float(profit), "detail": f"当期利润为负（{profit}）"}
    if loss_years == 0 and profit is None:
        return {"hit": False, "value": None, "detail": "未提供盈亏数据，未评估"}
    return {"hit": False, "value": loss_years, "detail": f"亏损 {loss_years} 年，未达预警"}


def _compute_R012(invoices, ctx):
    out_rates = [float(iv.get("tax_rate", 0) or 0) for iv in invoices if iv.get("type") == "销项" and iv.get("tax_rate")]
    in_rates = [float(iv.get("tax_rate", 0) or 0) for iv in invoices if iv.get("type") == "进项" and iv.get("tax_rate")]
    if not out_rates or not in_rates:
        return {"hit": False, "value": None, "detail": "缺少税率数据，未评估"}
    avg_out = sum(out_rates) / len(out_rates)
    avg_in = sum(in_rates) / len(in_rates)
    return {"hit": avg_in > avg_out + 1, "value": round(avg_in - avg_out, 2),
            "detail": f"平均进项税率 {avg_in:.2f}% vs 平均销项税率 {avg_out:.2f}%"}


def _compute_R013(invoices, ctx):
    age = int(ctx.get("entity_age_months") or 0)
    txn = int(ctx.get("transaction_count") or 0)
    if age == 0 and txn == 0:
        return {"hit": False, "value": None, "detail": "缺少主体数据，未评估"}
    hit = (age < 12) and (txn < 20)
    return {"hit": hit, "value": f"age={age}m,txn={txn}", "detail": f"成立 {age} 月 / 交易 {txn} 笔"}


def _compute_R014(invoices, ctx):
    r = ctx.get("related_party_ratio")
    if r is None:
        return {"hit": False, "value": None, "detail": "缺少关联交易数据，未评估"}
    r = float(r)
    return {"hit": r > 30, "value": round(r, 1), "detail": f"关联交易占比 {r:.1f}%"}


def _compute_R015(invoices, ctx):
    """闭环检测：在 seller→buyer 有向图上寻找长度>=2 的环（循环开票）"""
    edges = {}
    for iv in invoices:
        s = iv.get("seller")
        b = iv.get("buyer")
        if s and b:
            edges.setdefault(s, set()).add(b)
    # DFS 找环
    cycle_found = [False]

    def dfs(node, start, visited):
        if cycle_found[0]:
            return
        for nxt in edges.get(node, ()):
            if nxt == start and len(visited) >= 2:
                cycle_found[0] = True
                return
            if nxt not in visited:
                visited.add(nxt)
                dfs(nxt, start, visited)
                visited.discard(nxt)

    for start in list(edges.keys()):
        dfs(start, start, {start})
        if cycle_found[0]:
            break
    return {"hit": cycle_found[0], "value": 1 if cycle_found[0] else 0,
            "detail": "检测到循环开票闭环" if cycle_found[0] else "未发现循环开票"}


_COMPUTE_FUNCS = {
    "R001": _compute_R001, "R002": _compute_R002, "R003": _compute_R003,
    "R004": _compute_R004, "R005": _compute_R005, "R006": _compute_R006,
    "R007": _compute_R007, "R008": _compute_R008, "R009": _compute_R009,
    "R010": _compute_R010, "R011": _compute_R011, "R012": _compute_R012,
    "R013": _compute_R013, "R014": _compute_R014, "R015": _compute_R015,
}


def compute_all(invoices, context):
    """执行全部 15 项指标，返回结果列表（含元数据与命中详情）"""
    results = []
    for ind in INDICATORS:
        func = _COMPUTE_FUNCS[ind["id"]]
        try:
            r = func(invoices, context)
        except Exception:
            r = {"hit": False, "value": None, "detail": "计算异常，未评估"}
        results.append({
            "id": ind["id"],
            "name": ind["name"],
            "category": ind["category"],
            "weight": ind["weight"],
            "desc": ind["desc"],
            "advice": ind["advice"],
            "hit": bool(r.get("hit")),
            "value": r.get("value"),
            "detail": r.get("detail", ""),
        })
    return results

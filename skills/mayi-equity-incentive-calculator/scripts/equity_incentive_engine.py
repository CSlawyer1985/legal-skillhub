#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
蚂蚁工资条 · 股权期权激励计算引擎
======================================
5种权益工具 × 三阶段税务模型 × 12行业基准 × 33城市税政
支持：个人测算 / 稀释分析 / Exit场景 / 多工具对比 / 个税优化

法律依据：
- 财税〔2005〕35号：股票期权个人所得税
- 财税〔2016〕101号：股权激励税收递延
- 财税〔2018〕164号：全年一次性奖金等个税政策衔接
- 个人所得税法及其实施条例
"""

import argparse
import json
import sys
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


# ============================================================
# 枚举定义
# ============================================================

class EquityType(Enum):
    STOCK_OPTION = ("stock_option", "股票期权", "SO")
    RSU = ("rsu", "限制性股票单位", "RSU")
    PHANTOM_SHARES = ("phantom_shares", "虚拟股票", "PS")
    SAR = ("sar", "股票增值权", "SAR")
    ESOP = ("esop", "员工持股计划", "ESOP")

    def __init__(self, code, name, abbr):
        self.code = code
        self.cn_name = name
        self.abbr = abbr


class CompanyStage(Enum):
    ANGEL = ("angel", "天使轮", 0.2, 0.8)
    VC_A = ("vc_a", "A轮", 0.4, 1.5)
    VC_B = ("vc_b", "B轮", 0.3, 2.5)
    PRE_IPO = ("pre_ipo", "Pre-IPO", 0.15, 4.0)
    LISTED = ("listed", "已上市", 0.05, 6.0)

    def __init__(self, code, name, discount, multiplier):
        self.code = code
        self.cn_name = name
        self.typical_discount = discount  # 典型行权价折扣率
        self.value_multiplier = multiplier  # 估值乘数（相对当前股价）


class VestingType(Enum):
    STANDARD_4Y = ("standard_4y", "标准4年(cliff 1年)", 48, 12)
    STANDARD_3Y = ("standard_3y", "标准3年(无cliff)", 36, 0)
    PERFORMANCE = ("performance", "绩效挂钩", 48, 12)
    GRADUATED = ("graduated", "阶梯式", 48, 0)
    CUSTOM = ("custom", "自定义", 0, 0)

    def __init__(self, code, name, months, cliff_months):
        self.code = code
        self.cn_name = name
        self.total_months = months
        self.cliff_months = cliff_months


class OutputFormat(Enum):
    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"


# ============================================================
# 数据类定义
# ============================================================

@dataclass
class VestingResult:
    total_shares: int
    vested_shares: int
    unvested_shares: int
    vesting_pct: float
    monthly_vest: int
    next_cliff_date: str = ""
    schedule: List[Dict] = field(default_factory=list)


@dataclass
class TaxResult:
    stage: str                # grant / vest / exercise / sale
    taxable_income: float
    tax_rate: float
    tax_amount: float
    tax_rate_type: str        # 工资薪金 / 财产转让 / 递延
    legal_basis: str
    notes: str = ""


@dataclass
class EquityCalculation:
    equity_type: EquityType
    total_shares: int
    grant_price: float         # 行权价/授予价（每股，人民币）
    current_fmv: float         # 当前公允市场价值（每股）
    expected_exit_price: float  # 预期退出价格
    vesting_result: VestingResult
    tax_results: List[TaxResult]
    # 汇总
    total_cost: float           # 总成本（行权费用）
    total_tax: float            # 总税额
    current_paper_value: float  # 当前账面价值
    expected_gain: float        # 预期退出收益（税后）
    net_after_tax: float        # 税后净收益
    total_proceeds: float       # 预期总变现额
    rate_of_return: float       # 预期回报率
    cost_multiplier: float      # 成本倍数
    optimization_suggestions: List[str]


@dataclass
class DilutionAnalysis:
    company_stage: CompanyStage
    total_shares_outstanding: int
    new_shares_issued: int
    pre_dilution_pct: float
    post_dilution_pct: float
    dilution_hit: float
    pre_money_val: float
    post_money_val: float
    per_share_value_before: float
    per_share_value_after: float
    is_significant: bool  # 稀释超过10%


# ============================================================
# 数据库：5种权益工具详细定义
# ============================================================

EQUITY_TYPE_DEFS = {
    EquityType.STOCK_OPTION: {
        "description": "授予员工在未来特定时间以预定价格（行权价）购买公司股票的权利。行权后获得实际股份，享受股票增值收益。",
        "grant_stage": "授予：不产生税务义务（执行递延纳税政策时）",
        "vest_stage": "归属：达到归属条件后获得行权权利，不产生税务义务",
        "exercise_stage": "行权：行权价与公允价差额按「工资、薪金所得」计税（3%-45%累进），符合递延条件可延至转让时",
        "sale_stage": "转让：转让价与行权時公允价差额按「财产转让所得」20%计税",
        "tax_basis": ["财税〔2005〕35号", "国税函〔2009〕461号", "财税〔2016〕101号"],
        "merits": ["杠杆效应强（行权价固定）", "员工利益与股价直接挂钩", "递延纳税友好"],
        "demerits": ["股价下跌可能「水下期权」，失去激励效果", "行权需要现金支出", "税务处理相对复杂"],
        "best_for": "成长期至上市前企业、科技/互联网公司",
        "not_for": "传统行业现金流紧张企业、对股价波动敏感的成熟企业",
        "typical_vesting": "4年（cliff 1年 + 月/季度归属）",
        "typical_strike_discount": {"angel": 0.15, "vc_a": 0.25, "vc_b": 0.30, "pre_ipo": 0.40, "listed": 0.90}
    },
    EquityType.RSU: {
        "description": "公司承诺在未来归属时向员工交付实际股票（或等值现金），员工无需支付成本即可获得股票。上市企业最常用的长期激励工具。",
        "grant_stage": "授予：不产生税务义务",
        "vest_stage": "归属：归属时股票公允市值按「工资、薪金所得」计税（3%-45%累进）",
        "sale_stage": "转让：转让价与归属时公允价差额按「财产转让所得」20%计税。持有满1年暂免个税（沪港深等试点）",
        "tax_basis": ["财税〔2016〕101号", "财税〔2018〕164号", "个人所得税法"],
        "merits": ["员工零成本获得股票", "直接持股，利益绑定性强", "上市公司合规操作成熟"],
        "demerits": ["归属时即产生税负（无论是否卖出）", "非上市企业估值难定，RSU操作复杂", "员工不承担下行风险（单向激励）"],
        "best_for": "上市企业、即将IPO企业",
        "not_for": "早期创业公司、未盈利企业",
        "typical_vesting": "4年（cliff 1年 + 按年归属）",
        "typical_strike_discount": {"angel": 0.0, "vc_a": 0.0, "vc_b": 0.0, "pre_ipo": 0.0, "listed": 0.0}
    },
    EquityType.PHANTOM_SHARES: {
        "description": "虚拟授予一定数量的「模拟股票」，员工不实际持有股权，但享受与真实股票相同的分红权和增值收益。本质是现金结算型的薪酬安排。",
        "grant_stage": "授予：不产生税务义务",
        "settle_stage": "结算：增值收益 + 分红收益合并按「工资、薪金所得」计税（3%-45%累进）",
        "tax_basis": ["个人所得税法", "国税发〔2005〕9号（年终奖过渡政策适用情形）"],
        "merits": ["不稀释实际股权", "无需员工出资", "操作灵活，可定制化设计", "适合非上市企业"],
        "demerits": ["公司需真金白银支付现金", "增值收益按工资薪金计税（最高45%）", "激励感不如真实股权"],
        "best_for": "非上市企业、现金流充裕的企业、外资企业中国子公司",
        "not_for": "现金流紧张的企业、追求股权文化绑定的企业",
        "typical_vesting": "3-5年，灵活设计",
        "typical_strike_discount": {"angel": 0.0, "vc_a": 0.0, "vc_b": 0.0, "pre_ipo": 0.0, "listed": 0.0}
    },
    EquityType.SAR: {
        "description": "员工获得未来特定期间内因股票增值而获取现金或等值股票的权利。与期权类似，但员工不实际购买股票，只享受增值部分。",
        "grant_stage": "授予：不产生税务义务",
        "exercise_stage": "行权（增值部分）：按「工资、薪金所得」计税（3%-45%累进）",
        "tax_basis": ["财税〔2005〕35号（参照期权处理）", "个人所得税法"],
        "merits": ["无需员工出资（只获得增值部分）", "不稀释股权", "计算简单、操作方便"],
        "demerits": ["公司承担现金支付压力", "对股价高度敏感，波动大时不可控", "税负较重（工资薪金税率）"],
        "best_for": "现金流健康的上市企业、国企改革",
        "not_for": "现金流紧张的企业",
        "typical_vesting": "3-4年",
        "typical_strike_discount": {"angel": 0.0, "vc_a": 0.0, "vc_b": 0.0, "pre_ipo": 0.0, "listed": 0.0}
    },
    EquityType.ESOP: {
        "description": "公司通过设立员工持股平台（有限合伙/公司/信托）让员工间接持有公司股权。最完整的员工股权激励形式，涵盖管理、分配、退出全流程。",
        "grant_stage": "授予：不产生税务义务（通过持股平台认购份额）",
        "enter_stage": "入伙：以低于公允价认购份额，差额按「工资、薪金所得」计税",
        "distribute_stage": "分红：按「利息、股息、红利所得」20%计税",
        "exit_stage": "退出（转让份额）：按「财产转让所得」20%计税",
        "tax_basis": ["财税〔2016〕101号", "个人所得税法", "合伙企业法"],
        "merits": ["完整的股权激励体系", "税收有一定优化空间（转让税率20%）", "员工归属感最强", "可通过持股平台统一管理"],
        "demerits": ["架构复杂，法律成本高", "退出机制需要精心设计", "税务穿透至个人（合伙企业先分后税）"],
        "best_for": "Pre-IPO企业、准备长期绑定核心团队的企业",
        "not_for": "员工流动性高的行业、早期项目（架构成本高）",
        "typical_vesting": "4年（cliff 1年）+ 限制性条款 + 退出锁定",
        "typical_strike_discount": {"angel": 0.05, "vc_a": 0.10, "vc_b": 0.15, "pre_ipo": 0.25, "listed": 0.70}
    }
}


# ============================================================
# 数据库：33城市税收/社保政策差异
# ============================================================

CITY_TAX_POLICIES = {
    "北京": {"tax_deferral": True, "special_zone": False, "innovation_zone": True, "local_subsidy": 0.0, "notes": "中关村示范区有税收递延试点政策"},
    "上海": {"tax_deferral": True, "special_zone": True, "innovation_zone": True, "local_subsidy": 0.0, "notes": "自贸区临港新片区有特殊人才激励"},
    "深圳": {"tax_deferral": True, "special_zone": True, "innovation_zone": True, "local_subsidy": 0.15, "notes": "前海/河套有港澳人才个税补贴（超15%部分返还）"},
    "广州": {"tax_deferral": True, "special_zone": False, "innovation_zone": True, "local_subsidy": 0.05, "notes": "黄埔/南沙有人才个税补贴"},
    "杭州": {"tax_deferral": True, "special_zone": False, "innovation_zone": True, "local_subsidy": 0.05, "notes": "余杭区有数字经济人才个税优惠"},
    "成都": {"tax_deferral": True, "special_zone": False, "innovation_zone": True, "local_subsidy": 0.0, "notes": "高新区有人才公寓+个税奖补"},
    "武汉": {"tax_deferral": True, "special_zone": False, "innovation_zone": True, "local_subsidy": 0.0, "notes": "光谷高新区有人才激励政策"},
    "南京": {"tax_deferral": True, "special_zone": False, "innovation_zone": False, "local_subsidy": 0.0, "notes": "江北新区有高层次人才激励"},
    "苏州": {"tax_deferral": True, "special_zone": False, "innovation_zone": True, "local_subsidy": 0.05, "notes": "工业园区有人才个税返还"},
    "重庆": {"tax_deferral": True, "special_zone": False, "innovation_zone": False, "local_subsidy": 0.0, "notes": "两江新区有人才引进奖励"},
    "天津": {"tax_deferral": True, "special_zone": False, "innovation_zone": False, "local_subsidy": 0.0, "notes": "滨海新区有创新人才奖励"},
    "西安": {"tax_deferral": True, "special_zone": False, "innovation_zone": False, "local_subsidy": 0.0, "notes": "高新区有硬科技人才激励"},
    "长沙": {"tax_deferral": True, "special_zone": False, "innovation_zone": False, "local_subsidy": 0.0, "notes": "湘江新区有人才奖励"},
    "郑州": {"tax_deferral": True, "special_zone": False, "innovation_zone": False, "local_subsidy": 0.0, "notes": "郑东新区有人才引进政策"},
    "合肥": {"tax_deferral": True, "special_zone": False, "innovation_zone": True, "local_subsidy": 0.0, "notes": "高新区有量子/集成电路人才激励"},
    "东莞": {"tax_deferral": True, "special_zone": False, "innovation_zone": False, "local_subsidy": 0.0, "notes": "松山湖有产业人才激励"},
    "佛山": {"tax_deferral": True, "special_zone": False, "innovation_zone": False, "local_subsidy": 0.0, "notes": "南海区有人才住房+补贴"},
    "宁波": {"tax_deferral": True, "special_zone": False, "innovation_zone": False, "local_subsidy": 0.0, "notes": "杭州湾新区有人才激励"},
    "青岛": {"tax_deferral": True, "special_zone": False, "innovation_zone": False, "local_subsidy": 0.0, "notes": "西海岸新区有人才政策"},
    "大连": {"tax_deferral": True, "special_zone": False, "innovation_zone": False, "local_subsidy": 0.0, "notes": "高新区有软件人才激励"},
    "厦门": {"tax_deferral": True, "special_zone": True, "innovation_zone": False, "local_subsidy": 0.0, "notes": "经济特区，火炬高新区有人才激励"},
    "济南": {"tax_deferral": True, "special_zone": False, "innovation_zone": False, "local_subsidy": 0.0, "notes": "高新区有人才住房政策"},
    "福州": {"tax_deferral": True, "special_zone": False, "innovation_zone": False, "local_subsidy": 0.0, "notes": "滨海新城有人才引进政策"},
    "珠海": {"tax_deferral": True, "special_zone": True, "innovation_zone": True, "local_subsidy": 0.10, "notes": "横琴粤澳深度合作区有15%个税优惠政策"},
    "海口": {"tax_deferral": True, "special_zone": True, "innovation_zone": True, "local_subsidy": 0.15, "notes": "海南自贸港对高端紧缺人才个税超15%部分免征"},
    "三亚": {"tax_deferral": True, "special_zone": True, "innovation_zone": True, "local_subsidy": 0.15, "notes": "同海南自贸港政策"},
    "雄安": {"tax_deferral": True, "special_zone": True, "innovation_zone": True, "local_subsidy": 0.0, "notes": "雄安新区有创新人才特殊政策"},
    "哈尔滨": {"tax_deferral": True, "special_zone": False, "innovation_zone": False, "local_subsidy": 0.0, "notes": "新区有产业人才补贴"},
    "长春": {"tax_deferral": True, "special_zone": False, "innovation_zone": False, "local_subsidy": 0.0, "notes": "长春新区有人才公寓政策"},
    "沈阳": {"tax_deferral": True, "special_zone": False, "innovation_zone": False, "local_subsidy": 0.0, "notes": "浑南新区有人才激励"},
    "昆明": {"tax_deferral": True, "special_zone": False, "innovation_zone": False, "local_subsidy": 0.0, "notes": "呈贡新区有人才补贴"},
    "贵阳": {"tax_deferral": True, "special_zone": False, "innovation_zone": False, "local_subsidy": 0.0, "notes": "贵安新区有人才政策"},
    "南通": {"tax_deferral": True, "special_zone": False, "innovation_zone": False, "local_subsidy": 0.0, "notes": "通州湾有人才引进政策"},
}


# ============================================================
# 数据库：12行业基准
# ============================================================

INDUSTRY_BENCHMARKS = {
    "互联网/科技": {
        "equity_pool_pct": 0.15,
        "typical_instrument": [EquityType.STOCK_OPTION, EquityType.RSU],
        "avg_grant_pct_cto": 0.015,
        "avg_grant_pct_vp": 0.008,
        "avg_grant_pct_director": 0.003,
        "avg_grant_pct_manager": 0.001,
        "typical_vesting": VestingType.STANDARD_4Y,
        "typical_exercise_window": 90,
        "key_practices": "高期权池（15%），早期员工大比例期权，4年cliff 1年标准",
        "legal_notes": "需关注VIE架构下境外期权的税务申报合规",
    },
    "金融/保险": {
        "equity_pool_pct": 0.08,
        "typical_instrument": [EquityType.RSU, EquityType.SAR],
        "avg_grant_pct_cto": 0.005,
        "avg_grant_pct_vp": 0.003,
        "avg_grant_pct_director": 0.0015,
        "avg_grant_pct_manager": 0.0005,
        "typical_vesting": VestingType.STANDARD_4Y,
        "typical_exercise_window": 60,
        "key_practices": "期权池适中（8%），RSU为主，高管递延奖金与股权激励结合",
        "legal_notes": "银保监会监管，金融机构股权激励需报备/审批",
    },
    "制造业": {
        "equity_pool_pct": 0.06,
        "typical_instrument": [EquityType.ESOP, EquityType.PHANTOM_SHARES],
        "avg_grant_pct_cto": 0.005,
        "avg_grant_pct_vp": 0.002,
        "avg_grant_pct_director": 0.001,
        "avg_grant_pct_manager": 0.0003,
        "typical_vesting": VestingType.STANDARD_3Y,
        "typical_exercise_window": 60,
        "key_practices": "期权池较小（6%），ESOP/虚拟股为主，重资产行业现金分红导向",
        "legal_notes": "重资产企业注意股权激励与国有资产保值增值的平衡",
    },
    "餐饮/消费": {
        "equity_pool_pct": 0.10,
        "typical_instrument": [EquityType.ESOP, EquityType.PHANTOM_SHARES],
        "avg_grant_pct_cto": 0.010,
        "avg_grant_pct_vp": 0.005,
        "avg_grant_pct_director": 0.002,
        "avg_grant_pct_manager": 0.001,
        "typical_vesting": VestingType.STANDARD_3Y,
        "typical_exercise_window": 60,
        "key_practices": "期权池适中（10%），门店合伙人+虚拟股模式居多",
        "legal_notes": "连锁加盟模式下注意股权激励与加盟体系的清晰切割",
    },
    "建筑/房地产": {
        "equity_pool_pct": 0.05,
        "typical_instrument": [EquityType.PHANTOM_SHARES, EquityType.SAR],
        "avg_grant_pct_cto": 0.003,
        "avg_grant_pct_vp": 0.002,
        "avg_grant_pct_director": 0.0008,
        "avg_grant_pct_manager": 0.0003,
        "typical_vesting": VestingType.STANDARD_3Y,
        "typical_exercise_window": 60,
        "key_practices": "期权池小（5%），项目跟投 + 虚拟股模式为主",
        "legal_notes": "项目制特点，股权激励要与项目结算周期匹配",
    },
    "医疗/健康": {
        "equity_pool_pct": 0.12,
        "typical_instrument": [EquityType.STOCK_OPTION, EquityType.ESOP],
        "avg_grant_pct_cto": 0.012,
        "avg_grant_pct_vp": 0.006,
        "avg_grant_pct_director": 0.003,
        "avg_grant_pct_manager": 0.001,
        "typical_vesting": VestingType.STANDARD_4Y,
        "typical_exercise_window": 90,
        "key_practices": "期权池较大（12%），核心技术/研发人员高比例，里程碑挂钩",
        "legal_notes": "医疗器械/药企需关注FDA/CE等境外监管对股权激励的影响",
    },
    "教育/培训": {
        "equity_pool_pct": 0.08,
        "typical_instrument": [EquityType.ESOP, EquityType.PHANTOM_SHARES],
        "avg_grant_pct_cto": 0.008,
        "avg_grant_pct_vp": 0.004,
        "avg_grant_pct_director": 0.002,
        "avg_grant_pct_manager": 0.0008,
        "typical_vesting": VestingType.STANDARD_3Y,
        "typical_exercise_window": 60,
        "key_practices": "期权池适中（8%），教师群体稳定，强调长期服务绑定",
        "legal_notes": "双减后教育企业需要评估股权激励的合规性",
    },
    "物流/供应链": {
        "equity_pool_pct": 0.06,
        "typical_instrument": [EquityType.PHANTOM_SHARES, EquityType.ESOP],
        "avg_grant_pct_cto": 0.005,
        "avg_grant_pct_vp": 0.003,
        "avg_grant_pct_director": 0.001,
        "avg_grant_pct_manager": 0.0005,
        "typical_vesting": VestingType.STANDARD_3Y,
        "typical_exercise_window": 60,
        "key_practices": "期权池较小（6%），虚拟股+利润分享为主",
        "legal_notes": "快递/外卖等新业态模式注意劳动关系与激励权益的区分",
    },
    "传媒/文娱": {
        "equity_pool_pct": 0.10,
        "typical_instrument": [EquityType.STOCK_OPTION, EquityType.ESOP],
        "avg_grant_pct_cto": 0.010,
        "avg_grant_pct_vp": 0.005,
        "avg_grant_pct_director": 0.002,
        "avg_grant_pct_manager": 0.001,
        "typical_vesting": VestingType.STANDARD_4Y,
        "typical_exercise_window": 90,
        "key_practices": "期权池适中（10%），项目/IP绑定型激励，里程碑解锁",
        "legal_notes": "IP权属问题是股权激励设计中需特别关注的法律要点",
    },
    "咨询/服务": {
        "equity_pool_pct": 0.12,
        "typical_instrument": [EquityType.ESOP, EquityType.STOCK_OPTION],
        "avg_grant_pct_cto": 0.010,
        "avg_grant_pct_vp": 0.006,
        "avg_grant_pct_director": 0.003,
        "avg_grant_pct_manager": 0.001,
        "typical_vesting": VestingType.STANDARD_4Y,
        "typical_exercise_window": 90,
        "key_practices": "期权池较大（12%），合伙制+ESOP双轨，业绩与股权深度绑定",
        "legal_notes": "合伙企业特别法下ESOP架构需注意GP/LP权责划分",
    },
    "农业/食品": {
        "equity_pool_pct": 0.05,
        "typical_instrument": [EquityType.ESOP, EquityType.PHANTOM_SHARES],
        "avg_grant_pct_cto": 0.003,
        "avg_grant_pct_vp": 0.002,
        "avg_grant_pct_director": 0.001,
        "avg_grant_pct_manager": 0.0003,
        "typical_vesting": VestingType.STANDARD_3Y,
        "typical_exercise_window": 60,
        "key_practices": "期权池小（5%），利润分享型虚拟股为主",
        "legal_notes": "注意农村土地权益与股权激励的切割",
    },
    "芯片/半导体": {
        "equity_pool_pct": 0.15,
        "typical_instrument": [EquityType.STOCK_OPTION, EquityType.RSU],
        "avg_grant_pct_cto": 0.020,
        "avg_grant_pct_vp": 0.010,
        "avg_grant_pct_director": 0.005,
        "avg_grant_pct_manager": 0.002,
        "typical_vesting": VestingType.STANDARD_4Y,
        "typical_exercise_window": 90,
        "key_practices": "期权池最高（15%），核心技术人才重仓激励，国资委/大基金关注合规",
        "legal_notes": "国家大基金持股企业有特殊审批要求，技术出口管制需评估",
    },
}


# ============================================================
# 数据库：公司阶段 × 估值参数
# ============================================================

COMPANY_STAGE_PARAMS = {
    CompanyStage.ANGEL: {
        "typical_valuation_range": (1000, 5000),
        "valuation_unit": "万人民币",
        "typical_equity_pool": 0.15,
        "exit_horizon_years": (6, 10),
        "typical_exit_scenarios": ["IPO", "并购退出", "老股转让", "清算"],
        "expected_return_range": (5, 30),
        "risk_level": "极高",
        "key_risks": ["产品未验证", "团队不稳定", "融资不确定性大"],
        "tax_strategy": "建议纳入财税〔2016〕101号递延纳税备案，避免行权時的高税负",
    },
    CompanyStage.VC_A: {
        "typical_valuation_range": (5000, 30000),
        "valuation_unit": "万人民币",
        "typical_equity_pool": 0.12,
        "exit_horizon_years": (4, 7),
        "typical_exit_scenarios": ["IPO", "并购退出", "老股转让"],
        "expected_return_range": (3, 15),
        "risk_level": "高",
        "key_risks": ["市场竞争加剧", "增长不及预期", "后续融资困难"],
        "tax_strategy": "建议设立持股平台(有限合伙)，统一管理税务筹划",
    },
    CompanyStage.VC_B: {
        "typical_valuation_range": (30000, 100000),
        "valuation_unit": "万人民币",
        "typical_equity_pool": 0.10,
        "exit_horizon_years": (3, 5),
        "typical_exit_scenarios": ["IPO", "并购退出"],
        "expected_return_range": (2, 8),
        "risk_level": "中高",
        "key_risks": ["估值泡沫", "上市节奏不确定", "核心人才流失"],
        "tax_strategy": "Pre-IPO阶段应完成激励架构的税务清理，避免IPO时的税务冲击",
    },
    CompanyStage.PRE_IPO: {
        "typical_valuation_range": (100000, 500000),
        "valuation_unit": "万人民币",
        "typical_equity_pool": 0.08,
        "exit_horizon_years": (1, 3),
        "typical_exit_scenarios": ["IPO", "并购退出"],
        "expected_return_range": (1.5, 5),
        "risk_level": "中",
        "key_risks": ["IPO失败/延迟", "锁定期的股价波动", "估值不及预期"],
        "tax_strategy": "建议最大化递延纳税优惠，考虑员工个税清算安排",
    },
    CompanyStage.LISTED: {
        "typical_valuation_range": (500000, 999999999),
        "valuation_unit": "万人民币",
        "typical_equity_pool": 0.05,
        "exit_horizon_years": (0, 3),
        "typical_exit_scenarios": ["二级市场减持", "大宗交易转让"],
        "expected_return_range": (0.5, 3),
        "risk_level": "低",
        "key_risks": ["股价波动", "减持限制", "窗口期管理"],
        "tax_strategy": "注意减持窗口期的税务规划，大股东注意6个月短线交易限制",
    },
}


# ============================================================
# 数据库：法律依据索引
# ============================================================

LEGAL_REFERENCES = {
    "财税〔2005〕35号": {
        "title": "关于个人股票期权所得征收个人所得税问题的通知",
        "core": "定义股票期权个税处理规则：行权时差额按工资薪金计税，转让时按财产转让所得计税",
        "scope": "上市公司和非上市公司的股票期权",
    },
    "财税〔2016〕101号": {
        "title": "关于完善股权激励和技术入股有关所得税政策的通知",
        "core": "非上市公司股权激励可递延纳税至股权转让时，按财产转让所得20%计税（非工资薪金累进税率）",
        "scope": "符合条件的非上市公司（含新三板挂牌公司）",
        "conditions": "激励对象不超过最近6个月在职职工平均人数的30%，持有满3年等",
    },
    "国税函〔2009〕461号": {
        "title": "关于股权激励有关个人所得税问题的通知",
        "core": "明确不可公开交易的股票期权行权时公允价值的确定方法",
        "scope": "上市公司的不可公开交易股票期权",
    },
    "财税〔2018〕164号": {
        "title": "关于个人所得税法修改后有关优惠政策衔接问题的通知",
        "core": "居民个人取得股票期权等股权激励，不并入当年综合所得，全额单独适用综合所得税率表",
        "scope": "上市公司股权激励的个税计算方式",
    },
    "个人所得税法": {
        "title": "中华人民共和国个人所得税法（2018修订）",
        "core": "综合所得（工资薪金等）适用3%-45%七级超额累进税率；财产转让所得适用20%比例税率",
        "scope": "所有个人所得",
    },
}

INDIVIDUAL_TAX_BRACKETS = [
    (36000, 0.03, 0),
    (144000, 0.10, 2520),
    (300000, 0.20, 16920),
    (420000, 0.25, 31920),
    (660000, 0.30, 52920),
    (960000, 0.35, 85920),
    (float('inf'), 0.45, 181920),
]


# ============================================================
# 核心计算引擎
# ============================================================

class EquityIncentiveEngine:
    """股权期权激励计算引擎"""

    def __init__(self):
        self.city_policies = CITY_TAX_POLICIES
        self.industry_benchmarks = INDUSTRY_BENCHMARKS
        self.stage_params = COMPANY_STAGE_PARAMS
        self.equity_defs = EQUITY_TYPE_DEFS

    # ------------ Vesting Schedule Calculator ------------

    def calculate_vesting(self, total_shares: int, vesting_type: VestingType,
                          months_elapsed: int = 0,
                          custom_schedule: Optional[List[Tuple[int, float]]] = None) -> VestingResult:
        """计算归属进度"""
        if vesting_type == VestingType.CUSTOM and custom_schedule:
            return self._custom_vesting(total_shares, custom_schedule, months_elapsed)

        total_m = vesting_type.total_months
        cliff_m = vesting_type.cliff_months

        if months_elapsed < cliff_m:
            vested = 0
        else:
            if vesting_type == VestingType.GRADUATED:
                # 阶梯式：10% - 20% - 30% - 40% per year
                year = min(months_elapsed // 12, 4)
                rates = [0.10, 0.20, 0.30, 0.40]
                vested = int(total_shares * sum(rates[:year]))
            elif vesting_type == VestingType.PERFORMANCE:
                # 绩效挂钩：base归属 + 绩效系数 [70%, 130%]
                effective_m = months_elapsed - cliff_m
                base_vested = int(total_shares * min(effective_m / (total_m - cliff_m), 1.0))
                perf_factor = 1.0  # LLM根据实际情况调整
                vested = min(int(base_vested * perf_factor), total_shares)
            else:
                effective_m = months_elapsed - cliff_m
                remaining = total_m - cliff_m
                vested = int(total_shares * min(effective_m / max(remaining, 1), 1.0))

        vested = min(vested, total_shares)
        unvested = total_shares - vested

        schedule = []
        if vesting_type in (VestingType.STANDARD_4Y, VestingType.STANDARD_3Y):
            monthly_vest = int(total_shares / (total_m - cliff_m)) if total_m > cliff_m else 0
            schedule = [{"month": m, "cumulative_pct": min(m / total_m, 1.0),
                         "cumulative_shares": int(total_shares * min(m / total_m, 1.0))}
                        for m in range(6, total_m + 1, 6)]

        vp = round(vested / max(total_shares, 1) * 100, 1)
        mv = total_shares // (total_m - cliff_m) if total_m > cliff_m else 0

        return VestingResult(
            total_shares=total_shares,
            vested_shares=vested,
            unvested_shares=unvested,
            vesting_pct=vp,
            monthly_vest=mv,
            schedule=schedule,
            next_cliff_date=f"满{cliff_m}个月" if months_elapsed < cliff_m else "已过cliff期"
        )

    def _custom_vesting(self, total_shares: int,
                         schedule_list: List[Tuple[int, float]],
                         months_elapsed: int = 0) -> VestingResult:
        vested_pct = 0.0
        for m, pct in sorted(schedule_list):
            if months_elapsed >= m:
                vested_pct = pct
            else:
                break
        vested = int(total_shares * vested_pct)
        return VestingResult(
            total_shares=total_shares,
            vested_shares=vested,
            unvested_shares=total_shares - vested,
            vesting_pct=round(vested_pct * 100, 1),
            monthly_vest=0,
            schedule=[{"month": m, "cumulative_pct": p} for m, p in schedule_list]
        )

    # ------------ Tax Calculator ------------

    def calc_income_tax(self, taxable_income: float) -> Tuple[float, float, float]:
        """计算工资薪金个税（3%-45%七级累进）"""
        for threshold, rate, deduction in INDIVIDUAL_TAX_BRACKETS:
            if taxable_income <= threshold:
                tax = max(0, taxable_income * rate - deduction)
                return tax, rate, deduction
        return taxable_income * 0.45 - 181920, 0.45, 181920

    def calc_capital_gains_tax(self, gain: float) -> float:
        """财产转让所得 20%"""
        return max(0, gain * 0.20)

    def calc_equity_tax(self, equity_type: EquityType, company_stage: CompanyStage,
                        shares: int, grant_price_per_share: float,
                        fmv_per_share: float,
                        expected_sale_price: float = 0.0,
                        months_held_after_vest: int = 0,
                        use_tax_deferral: bool = False) -> List[TaxResult]:
        """计算股权激励全流程税务"""
        results = []

        if expected_sale_price <= 0:
            expected_sale_price = fmv_per_share

        if equity_type == EquityType.STOCK_OPTION:
            # Grant阶段
            results.append(TaxResult(
                stage="授予(grant)", taxable_income=0, tax_rate=0, tax_amount=0,
                tax_rate_type="无", legal_basis="财税〔2005〕35号",
                notes="授予时不产生税务义务"
            ))

            if use_tax_deferral and company_stage != CompanyStage.LISTED:
                # 递延纳税（财税〔2016〕101号）
                exercise_gain = (fmv_per_share - grant_price_per_share) * shares
                results.append(TaxResult(
                    stage="行权(exercise)-递延",
                    taxable_income=exercise_gain,
                    tax_rate=0, tax_amount=0,
                    tax_rate_type="递延纳税(至转让时)",
                    legal_basis="财税〔2016〕101号",
                    notes=f"递延至转让时按20%财产转让所得计税，应纳税所得额={exercise_gain:,.0f}元"
                ))
                # 转让时合并计算
                total_gain = (expected_sale_price - grant_price_per_share) * shares
                tax = self.calc_capital_gains_tax(total_gain)
                results.append(TaxResult(
                    stage="转让(sale)-递延",
                    taxable_income=total_gain,
                    tax_rate=0.20, tax_amount=tax,
                    tax_rate_type="财产转让所得(20%)",
                    legal_basis="财税〔2016〕101号",
                    notes=f"递延纳税到期满转让，按购入价到售出价差额20%计征"
                ))
            else:
                # 非递延：行权时按工资薪金计税
                exercise_gain = max(0, (fmv_per_share - grant_price_per_share) * shares)
                tax, rate, _ = self.calc_income_tax(exercise_gain)
                eff_rate = tax / max(exercise_gain, 1) if exercise_gain > 0 else 0
                results.append(TaxResult(
                    stage="行权(exercise)",
                    taxable_income=exercise_gain,
                    tax_rate=eff_rate, tax_amount=tax,
                    tax_rate_type="工资薪金所得(3%-45%)",
                    legal_basis="财税〔2005〕35号 / 财税〔2018〕164号",
                    notes="财税〔2018〕164号规定上市公司股权激励不并入综合所得，单独适用综合税率表"
                ))
                # 转让时
                sell_gain = max(0, (expected_sale_price - fmv_per_share) * shares)
                cg_tax = self.calc_capital_gains_tax(sell_gain)
                results.append(TaxResult(
                    stage="转让(sale)",
                    taxable_income=sell_gain,
                    tax_rate=0.20, tax_amount=cg_tax,
                    tax_rate_type="财产转让所得(20%)",
                    legal_basis="个人所得税法",
                    notes=f"持有超过1年暂免个税（试点地区）" if months_held_after_vest >= 12 else ""
                ))

        elif equity_type == EquityType.RSU:
            results.append(TaxResult(
                stage="授予(grant)", taxable_income=0, tax_rate=0, tax_amount=0,
                tax_rate_type="无", legal_basis="财税〔2016〕101号",
                notes="授予时不产生税务义务"
            ))
            vest_gain = max(0, fmv_per_share * shares)
            tax, rate, _ = self.calc_income_tax(vest_gain)
            eff_rate = tax / max(vest_gain, 1) if vest_gain > 0 else 0
            results.append(TaxResult(
                stage="归属(vest)",
                taxable_income=vest_gain,
                tax_rate=eff_rate, tax_amount=tax,
                tax_rate_type="工资薪金所得(3%-45%)",
                legal_basis="财税〔2016〕101号 / 财税〔2018〕164号",
                notes="归属时按股票市值全额计入工资薪金所得计税"
            ))
            sell_gain = max(0, (expected_sale_price - fmv_per_share) * shares)
            cg_tax = self.calc_capital_gains_tax(sell_gain)
            results.append(TaxResult(
                stage="转让(sale)",
                taxable_income=sell_gain,
                tax_rate=0.20, tax_amount=cg_tax,
                tax_rate_type="财产转让所得(20%)",
                legal_basis="个人所得税法",
                notes=f"持有超过1年暂免个税（部分试点）" if months_held_after_vest >= 12 else ""
            ))

        elif equity_type == EquityType.PHANTOM_SHARES:
            results.append(TaxResult(
                stage="授予(grant)", taxable_income=0, tax_rate=0, tax_amount=0,
                tax_rate_type="无", legal_basis="个人所得税法",
                notes="授予时不产生税务义务"
            ))
            settle_gain = max(0, (expected_sale_price - grant_price_per_share) * shares)
            tax, rate, _ = self.calc_income_tax(settle_gain)
            eff_rate = tax / max(settle_gain, 1) if settle_gain > 0 else 0
            results.append(TaxResult(
                stage="结算(settle)",
                taxable_income=settle_gain,
                tax_rate=eff_rate, tax_amount=tax,
                tax_rate_type="工资薪金所得(3%-45%)",
                legal_basis="个人所得税法",
                notes="虚拟股票增值收益按工资薪金所得计税，税率最高45%"
            ))

        elif equity_type == EquityType.SAR:
            results.append(TaxResult(
                stage="授予(grant)", taxable_income=0, tax_rate=0, tax_amount=0,
                tax_rate_type="无", legal_basis="财税〔2005〕35号（参照）",
                notes="授予时不产生税务义务"
            ))
            sar_gain = max(0, (fmv_per_share - grant_price_per_share) * shares)
            tax, rate, _ = self.calc_income_tax(sar_gain)
            eff_rate = tax / max(sar_gain, 1) if sar_gain > 0 else 0
            results.append(TaxResult(
                stage="行权(exercise)",
                taxable_income=sar_gain,
                tax_rate=eff_rate, tax_amount=tax,
                tax_rate_type="工资薪金所得(3%-45%)",
                legal_basis="财税〔2005〕35号 / 个人所得税法",
                notes="SAR增值收益按工资薪金所得计税"
            ))

        elif equity_type == EquityType.ESOP:
            results.append(TaxResult(
                stage="授予/入伙(grant)", taxable_income=0, tax_rate=0, tax_amount=0,
                tax_rate_type="无", legal_basis="财税〔2016〕101号",
                notes="授予时一般不产生税务义务（符合递延条件）"
            ))
            # 退出时的财产转让
            exit_gain = max(0, (expected_sale_price - grant_price_per_share) * shares)
            cg_tax = self.calc_capital_gains_tax(exit_gain)
            results.append(TaxResult(
                stage="退出(exit)",
                taxable_income=exit_gain,
                tax_rate=0.20, tax_amount=cg_tax,
                tax_rate_type="财产转让所得(20%)",
                legal_basis="个人所得税法 / 财税〔2016〕101号",
                notes="ESOP通过合伙企业持有，退出时按财产转让所得20%计税"
            ))
            if expected_sale_price > fmv_per_share:
                div_gain = (expected_sale_price - fmv_per_share) * shares * 0.3
                results.append(TaxResult(
                    stage="分红(distribute)",
                    taxable_income=div_gain,
                    tax_rate=0.20, tax_amount=div_gain * 0.20,
                    tax_rate_type="利息股息红利所得(20%)",
                    legal_basis="个人所得税法",
                    notes="ESOP持股平台取得分红时按20%计税"
                ))

        return results

    # ------------ Full Calculation ------------

    def calculate_full(self, equity_type: EquityType, company_stage: CompanyStage,
                       total_shares: int, grant_price_per_share: float,
                       current_fmv_per_share: float,
                       vesting_type: VestingType, months_elapsed: int = 0,
                       expected_sale_price: float = 0.0,
                       months_held_after_vest: int = 0,
                       use_tax_deferral: bool = False,
                       city: str = "北京",
                       annual_salary: float = 0.0) -> EquityCalculation:
        """完整激励计算"""

        if expected_sale_price <= 0:
            expected_sale_price = current_fmv_per_share

        # 计算归属
        vesting = self.calculate_vesting(total_shares, vesting_type, months_elapsed)

        # 计算税务
        tax_results = self.calc_equity_tax(
            equity_type, company_stage,
            total_shares, grant_price_per_share,
            current_fmv_per_share, expected_sale_price,
            months_held_after_vest, use_tax_deferral
        )

        # 城市税政
        city_policy = self.city_policies.get(city, self.city_policies["北京"])
        local_subsidy_rate = city_policy.get("local_subsidy", 0.0)

        # 汇总计算
        total_cost = grant_price_per_share * total_shares  # 行权成本
        total_tax = sum(t.tax_amount for t in tax_results)

        # 地方税返
        local_rebate = total_tax * local_subsidy_rate if local_subsidy_rate > 0 else 0

        current_paper_value = current_fmv_per_share * total_shares
        total_proceeds = expected_sale_price * total_shares
        expected_gain = total_proceeds - total_cost - total_tax + local_rebate
        net_after_tax = expected_gain + total_cost  # 拿回本金的总额

        if total_cost > 0:
            rate_of_return = expected_gain / total_cost
            cost_multiplier = (expected_gain + total_cost) / total_cost
        else:
            rate_of_return = expected_gain / max(current_paper_value, 1)
            cost_multiplier = net_after_tax / max(current_paper_value, 1)

        # 优化建议
        suggestions = []
        effective_tax_rate = total_tax / max(expected_gain + total_tax, 1) if (expected_gain + total_tax) > 0 else 0

        if effective_tax_rate > 0.35:
            suggestions.append(f"当前有效税率 {effective_tax_rate:.1%} 偏高，建议评估是否满足财税〔2016〕101号递延纳税条件")
        if use_tax_deferral and effective_tax_rate < 0.20:
            suggestions.append("递延纳税策略有效，已显著降低税负")
        if not use_tax_deferral and company_stage != CompanyStage.LISTED:
            suggestions.append(f"非上市企业建议申请财税〔2016〕101号递延纳税备案，可将最高45%税率降至20%")
        if local_subsidy_rate > 0:
            suggestions.append(f"{city}可享受约{local_subsidy_rate:.0%}地方个税返还，预计返税{local_rebate:,.0f}元")
        if equity_type == EquityType.PHANTOM_SHARES:
            suggestions.append("虚拟股票增值收益按工资薪金计税(最高45%)，考虑实股激励方案可享20%财产转让税率")
        if company_stage in (CompanyStage.ANGEL, CompanyStage.VC_A):
            suggestions.append("早期企业建议用ESOP/期权而非RSU，RSU在归属时即产生税负但股票无法变现")
        if months_elapsed < vesting_type.cliff_months:
            suggestions.append(f"当前处于cliff期（前{vesting_type.cliff_months}个月无归属），建议关注满cliff后的纳税规划")

        return EquityCalculation(
            equity_type=equity_type,
            total_shares=total_shares,
            grant_price=grant_price_per_share,
            current_fmv=current_fmv_per_share,
            expected_exit_price=expected_sale_price,
            vesting_result=vesting,
            tax_results=tax_results,
            total_cost=total_cost,
            total_tax=total_tax,
            current_paper_value=current_paper_value,
            expected_gain=expected_gain,
            net_after_tax=net_after_tax,
            total_proceeds=total_proceeds,
            rate_of_return=rate_of_return,
            cost_multiplier=cost_multiplier,
            optimization_suggestions=suggestions
        )

    # ------------ Dilution Analysis ------------

    def analyze_dilution(self, company_stage: CompanyStage,
                         total_shares_outstanding: int,
                         employee_grant_shares: int,
                         pre_money_val: float) -> DilutionAnalysis:
        """稀释分析"""
        pre_pct = employee_grant_shares / max(total_shares_outstanding, 1)
        post_shares = total_shares_outstanding + employee_grant_shares
        post_pct = employee_grant_shares / max(post_shares, 1)
        dilution = (pre_pct - post_pct) / max(pre_pct, 0.0001) if pre_pct > 0 else 0

        post_money_val = pre_money_val  # ESOP增发不改变估值
        ps_before = pre_money_val / max(total_shares_outstanding, 1)
        ps_after = post_money_val / max(post_shares, 1)

        return DilutionAnalysis(
            company_stage=company_stage,
            total_shares_outstanding=total_shares_outstanding,
            new_shares_issued=employee_grant_shares,
            pre_dilution_pct=round(pre_pct * 100, 3),
            post_dilution_pct=round(post_pct * 100, 3),
            dilution_hit=round(dilution * 100, 1),
            pre_money_val=pre_money_val,
            post_money_val=post_money_val,
            per_share_value_before=round(ps_before, 4),
            per_share_value_after=round(ps_after, 4),
            is_significant=dilution > 0.10
        )

    # ------------ Exit Scenario Simulator ------------

    def simulate_exit(self, calc: EquityCalculation,
                      exit_price_per_share: float,
                      exit_type: str = "IPO") -> Dict:
        """退出场景模拟"""
        shares = calc.total_shares
        cost = calc.total_cost

        gross = exit_price_per_share * shares

        # 重新计算税务（基于退出价）
        tax_results = self.calc_equity_tax(
            calc.equity_type, CompanyStage.LISTED,
            shares, calc.grant_price, calc.current_fmv, exit_price_per_share
        )
        total_tax = sum(t.tax_amount for t in tax_results)
        net = gross - cost - total_tax

        return {
            "exit_type": exit_type,
            "exit_price": exit_price_per_share,
            "gross_proceeds": gross,
            "cost_basis": cost,
            "total_tax": total_tax,
            "net_proceeds": net,
            "roi": (net / max(cost, 1)),
            "tax_breakdown": [{"stage": t.stage, "tax": t.tax_amount} for t in tax_results],
            "message": self._exit_message(exit_type, net, gross, cost)
        }

    def _exit_message(self, exit_type: str, net: float, gross: float, cost: float) -> str:
        msgs = {
            "IPO": f"IPO退出：总收益{gross:,.0f}元，成本{cost:,.0f}元，税后净收益{net:,.0f}元。注意上市后通常有6-12个月锁定期。",
            "并购": f"并购退出：总收益{gross:,.0f}元，注意并购对价可能包含现金+股票，税务处理不同。",
            "老股转让": f"老股转让：总收益{gross:,.0f}元，需注意公司对股权转让的限制性条款和优先购买权。",
            "清算": f"清算退出：优先股和债权优先于普通股清算，股权激励权益可能在清算中完全归零。",
        }
        return msgs.get(exit_type, f"{exit_type}退出：税后净收益{net:,.0f}元")

    # ------------ Multi-Type Comparison ------------

    def compare_types(self, total_shares: int, grant_price: float,
                      fmv: float, vesting_type: VestingType,
                      company_stage: CompanyStage, city: str = "北京",
                      months_elapsed: int = 0) -> List[EquityCalculation]:
        """跨权益工具对比"""
        results = []
        for etype in EquityType:
            calc = self.calculate_full(
                etype, company_stage, total_shares,
                grant_price, fmv, vesting_type, months_elapsed,
                use_tax_deferral=(company_stage != CompanyStage.LISTED),
                city=city
            )
            results.append(calc)
        return results

    # ------------ Recommender ------------

    def recommend(self, industry: str, company_stage_code: str,
                  employee_role: str, company_size: str) -> Dict:
        """智能推荐权益工具和参数"""
        # 查找行业
        industry_data = None
        for key, val in self.industry_benchmarks.items():
            if industry in key or key in industry:
                industry_data = val
                break
        if not industry_data:
            industry_data = self.industry_benchmarks["互联网/科技"]

        # 查找阶段
        stage = CompanyStage.LISTED
        for s in CompanyStage:
            if s.code == company_stage_code or s.cn_name == company_stage_code:
                stage = s
                break

        # 角色映射到授权比例
        role_grant_map = {
            "CTO/技术合伙人": "avg_grant_pct_cto",
            "VP/总监": "avg_grant_pct_vp",
            "总监/部门负责人": "avg_grant_pct_director",
            "经理/骨干": "avg_grant_pct_manager",
            "核心研发": "avg_grant_pct_cto",
            "高管": "avg_grant_pct_vp",
            "中层": "avg_grant_pct_director",
            "关键员工": "avg_grant_pct_manager",
        }

        role_key = role_grant_map.get(employee_role, "avg_grant_pct_manager")
        grant_pct = industry_data.get(role_key, 0.001)

        stage_param = self.stage_params[stage]

        recommended_types = [t.cn_name for t in industry_data["typical_instrument"]]

        return {
            "industry": industry,
            "company_stage": stage.cn_name,
            "recommended_instruments": recommended_types,
            "recommended_pool_pct": f"{industry_data['equity_pool_pct']:.0%}",
            "grant_pct_for_role": f"{grant_pct:.3%}",
            "typical_equity_pool_total": f"约{industry_data['equity_pool_pct']:.0%}（行业标准）",
            "exit_horizon": f"{stage_param['exit_horizon_years'][0]}-{stage_param['exit_horizon_years'][1]}年",
            "risk_level": stage_param['risk_level'],
            "tax_strategy": stage_param['tax_strategy'],
            "key_practices": industry_data['key_practices'],
            "legal_notes": industry_data['legal_notes'],
        }

    # ------------ Output Formatters ------------

    def _fmt_money(self, val: float) -> str:
        if abs(val) >= 10000_0000:
            return f"{val/10000_0000:.2f}亿"
        elif abs(val) >= 10000:
            return f"{val/10000:.1f}万"
        else:
            return f"{val:,.0f}"

    def format_result(self, calc: EquityCalculation, fmt: OutputFormat,
                      city: str = "北京", industry: str = "互联网/科技",
                      annual_salary: float = 0) -> str:
        if fmt == OutputFormat.JSON:
            d = {
                "equity_type": calc.equity_type.cn_name,
                "abbr": calc.equity_type.abbr,
                "total_shares": calc.total_shares,
                "grant_price": calc.grant_price,
                "current_fmv": calc.current_fmv,
                "expected_exit_price": calc.expected_exit_price,
                "vesting": {
                    "total": calc.vesting_result.total_shares,
                    "vested": calc.vesting_result.vested_shares,
                    "unvested": calc.vesting_result.unvested_shares,
                    "vesting_pct": calc.vesting_result.vesting_pct,
                },
                "taxes": [{
                    "stage": t.stage, "taxable": t.taxable_income,
                    "rate": t.tax_rate, "tax": t.tax_amount,
                    "type": t.tax_rate_type, "basis": t.legal_basis
                } for t in calc.tax_results],
                "summary": {
                    "total_cost": calc.total_cost,
                    "total_tax": calc.total_tax,
                    "current_paper_value": calc.current_paper_value,
                    "expected_gain": calc.expected_gain,
                    "net_after_tax": calc.net_after_tax,
                    "rate_of_return": calc.rate_of_return,
                    "cost_multiplier": calc.cost_multiplier,
                },
                "suggestions": calc.optimization_suggestions
            }
            return json.dumps(d, ensure_ascii=False, indent=2)

        elif fmt == OutputFormat.MARKDOWN:
            return self._to_markdown(calc, city, industry)

        elif fmt == OutputFormat.HTML:
            return self._to_html(calc, city, industry)

        else:  # TEXT
            return self._to_text(calc, city, industry)

    def _to_text(self, calc: EquityCalculation, city: str, industry: str) -> str:
        lines = [
            "=" * 60,
            f"  股权激励测算报告 — {calc.equity_type.cn_name}({calc.equity_type.abbr})",
            "=" * 60,
            "",
            f"  权益类型：{calc.equity_type.cn_name}",
            f"  激励股数：{calc.total_shares:,} 股",
            f"  授予价/行权价：¥{calc.grant_price:.2f}/股",
            f"  当前公允价(FMV)：¥{calc.current_fmv:.2f}/股",
            f"  预期退出价：¥{calc.expected_exit_price:.2f}/股",
            "",
            "-" * 40,
            "【归属进度】",
            f"  已归属：{calc.vesting_result.vested_shares:,} 股 ({calc.vesting_result.vesting_pct}%)",
            f"  未归属：{calc.vesting_result.unvested_shares:,} 股",
            "",
            "-" * 40,
            "【税务分析】",
        ]
        for t in calc.tax_results:
            if t.tax_amount > 0:
                lines.append(f"  [{t.stage}] 应纳税所得额：{self._fmt_money(t.taxable_income)} | 税率：{t.tax_rate:.1%} | 税额：{self._fmt_money(t.tax_amount)}")
                lines.append(f"            类型：{t.tax_rate_type} | 依据：{t.legal_basis}")
            else:
                lines.append(f"  [{t.stage}] 不产生税务义务 | 依据：{t.legal_basis}")

        lines += [
            "",
            "-" * 40,
            "【收益汇总】",
            f"  行权成本：{self._fmt_money(calc.total_cost)}",
            f"  总税额：{self._fmt_money(calc.total_tax)}",
            f"  当前账面价值：{self._fmt_money(calc.current_paper_value)}",
            f"  预期税后净收益：{self._fmt_money(calc.expected_gain)}",
            f"  税后总收益：{self._fmt_money(calc.net_after_tax)}",
            f"  预期回报率：{calc.rate_of_return:.1%}",
            f"  成本倍数：{calc.cost_multiplier:.1f}x",
            "",
            "-" * 40,
            "【优化建议】",
        ]
        for s in calc.optimization_suggestions:
            lines.append(f"  ▶ {s}")
        lines += [
            "",
            f"  城市政策：{city}",
            "=" * 60,
        ]
        return '\n'.join(lines)

    def _to_markdown(self, calc: EquityCalculation, city: str, industry: str) -> str:
        lines = [
            f"# 股权激励测算报告 — {calc.equity_type.cn_name}({calc.equity_type.abbr})",
            "",
            "## 基本信息",
            "",
            f"| 参数 | 值 |",
            f"|------|-----|",
            f"| 权益类型 | {calc.equity_type.cn_name} |",
            f"| 激励股数 | {calc.total_shares:,} 股 |",
            f"| 授予/行权价 | ¥{calc.grant_price:.2f}/股 |",
            f"| 当前公允价(FMV) | ¥{calc.current_fmv:.2f}/股 |",
            f"| 预期退出价 | ¥{calc.expected_exit_price:.2f}/股 |",
            f"| 城市 | {city} |",
            "",
            "## 归属进度",
            "",
            f"| 项目 | 数值 |",
            f"|------|------|",
            f"| 已归属 | {calc.vesting_result.vested_shares:,} 股 ({calc.vesting_result.vesting_pct}%) |",
            f"| 未归属 | {calc.vesting_result.unvested_shares:,} 股 |",
            f"| 每月归属 | {calc.vesting_result.monthly_vest:,} 股 |",
            f"| Cliff状态 | {calc.vesting_result.next_cliff_date} |",
            "",
            "## 税务分析",
            "",
        ]
        for t in calc.tax_results:
            if t.tax_amount > 0:
                lines += [
                    f"### {t.stage}",
                    f"| 项目 | 数值 |",
                    f"|------|------|",
                    f"| 应纳税所得额 | {self._fmt_money(t.taxable_income)} |",
                    f"| 税率 | {t.tax_rate:.1%}（{t.tax_rate_type}） |",
                    f"| 应纳税额 | {self._fmt_money(t.tax_amount)} |",
                    f"| 法律依据 | {t.legal_basis} |",
                    f"| 备注 | {t.notes} |",
                    "",
                ]
            else:
                lines.append(f"### {t.stage}")
                lines.append(f"> 不产生税务义务。依据：{t.legal_basis}。{t.notes}")
                lines.append("")

        lines += [
            "## 收益汇总",
            "",
            f"| 指标 | 数值 |",
            f"|------|------|",
            f"| 行权成本 | {self._fmt_money(calc.total_cost)} |",
            f"| 总税额 | {self._fmt_money(calc.total_tax)} |",
            f"| 当前账面价值 | {self._fmt_money(calc.current_paper_value)} |",
            f"| 预期税后净收益 | {self._fmt_money(calc.expected_gain)} |",
            f"| 预期回报率 | {calc.rate_of_return:.1%} |",
            f"| 成本倍数 | {calc.cost_multiplier:.1f}x |",
            "",
            "## 优化建议",
            "",
        ]
        for s in calc.optimization_suggestions:
            lines.append(f"- {s}")

        lines += [
            "",
            f"> 城市政策参考：{city} | 行业参考：{industry}",
        ]
        return '\n'.join(lines)

    def _to_html(self, calc: EquityCalculation, city: str, industry: str) -> str:
        html = f"""<div class="equity-report">
<h1>股权激励测算报告 — {calc.equity_type.cn_name}({calc.equity_type.abbr})</h1>

<h2>基本信息</h2>
<table><tr><th>参数</th><th>值</th></tr>
<tr><td>权益类型</td><td>{calc.equity_type.cn_name}</td></tr>
<tr><td>激励股数</td><td>{calc.total_shares:,} 股</td></tr>
<tr><td>行权价</td><td>{calc.grant_price:.2f} 元/股</td></tr>
<tr><td>当前FMV</td><td>{calc.current_fmv:.2f} 元/股</td></tr>
<tr><td>预期退出价</td><td>{calc.expected_exit_price:.2f} 元/股</td></tr>
</table>

<h2>归属进度</h2>
<p>已归属：{calc.vesting_result.vested_shares:,} 股 ({calc.vesting_result.vesting_pct}%) | 未归属：{calc.vesting_result.unvested_shares:,} 股</p>

<h2>税务分析</h2>"""
        for t in calc.tax_results:
            if t.tax_amount > 0:
                html += f"<h3>{t.stage}</h3><p>应纳税额：{self._fmt_money(t.tax_amount)}（{t.tax_rate:.1%}）| 类型：{t.tax_rate_type} | 依据：{t.legal_basis}</p>"
            else:
                html += f"<h3>{t.stage}</h3><p>不产生税务义务（{t.legal_basis}）</p>"

        html += f"""
<h2>收益汇总</h2>
<table><tr><th>指标</th><th>数值</th></tr>
<tr><td>行权成本</td><td>{self._fmt_money(calc.total_cost)}</td></tr>
<tr><td>总税额</td><td>{self._fmt_money(calc.total_tax)}</td></tr>
<tr><td>当前账面价值</td><td>{self._fmt_money(calc.current_paper_value)}</td></tr>
<tr><td>预期税后净收益</td><td>{self._fmt_money(calc.expected_gain)}</td></tr>
<tr><td>预期回报率</td><td>{calc.rate_of_return:.1%}</td></tr>
<tr><td>成本倍数</td><td>{calc.cost_multiplier:.1f}x</td></tr>
</table>

<h2>优化建议</h2><ul>"""
        for s in calc.optimization_suggestions:
            html += f"<li>{s}</li>"
        html += f"</ul><p><em>城市：{city} | 行业：{industry}</em></p></div>"
        return html

    # ------------ Format Comparison Table ------------

    def format_comparison(self, calcs: List[EquityCalculation], fmt: OutputFormat) -> str:
        if fmt == OutputFormat.JSON:
            data = []
            for c in calcs:
                data.append({
                    "type": c.equity_type.cn_name,
                    "abbr": c.equity_type.abbr,
                    "cost": c.total_cost,
                    "tax": c.total_tax,
                    "gain": c.expected_gain,
                    "roi": c.rate_of_return,
                    "net": c.net_after_tax,
                    "suggestions": c.optimization_suggestions[:3]
                })
            return json.dumps(data, ensure_ascii=False, indent=2)

        lines = []
        lines.append("=" * 100)
        lines.append(f"{'权益类型':<16} {'成本':>12} {'税额':>12} {'净收益':>12} {'回报率':>10} {'成本倍数':>10}")
        lines.append("-" * 100)
        best_idx = max(range(len(calcs)), key=lambda i: calcs[i].expected_gain)
        for i, c in enumerate(calcs):
            marker = " ★" if i == best_idx else "  "
            lines.append(
                f"{c.equity_type.cn_name + marker:<16} "
                f"{self._fmt_money(c.total_cost):>12} "
                f"{self._fmt_money(c.total_tax):>12} "
                f"{self._fmt_money(c.expected_gain):>12} "
                f"{c.rate_of_return:>9.1%} "
                f"{c.cost_multiplier:>9.1f}x"
            )
        lines.append("-" * 100)
        lines.append(f"★ 最优方案：{calcs[best_idx].equity_type.cn_name}（净收益最高）")
        lines.append("=" * 100)
        return '\n'.join(lines)

    # ------------ Stats ------------

    def get_stats(self) -> str:
        lines = [
            "=" * 50,
            "  股权期权激励计算引擎 — 统计信息",
            "=" * 50,
            f"  权益工具类型：{len(EquityType)} 种",
        ]
        for e in EquityType:
            lines.append(f"    - {e.cn_name} ({e.abbr})")
        lines += [
            f"  城市税政覆盖：{len(self.city_policies)} 座",
            f"  行业基准库：{len(self.industry_benchmarks)} 个",
            f"  法律依据索引：{len(LEGAL_REFERENCES)} 部法规",
            f"  个税级距：{len(INDIVIDUAL_TAX_BRACKETS)} 级",
            f"  企业阶段：{len(CompanyStage)} 个",
            f"  归属模式：{len(VestingType)} 种",
            "=" * 50,
        ]
        return '\n'.join(lines)


# ============================================================
# CLI 接口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='股权期权激励计算引擎')
    parser.add_argument('--stats', action='store_true', help='显示统计信息')
    parser.add_argument('--demo', action='store_true', help='运行演示案例')
    parser.add_argument('--type', type=str, help='权益工具类型(SO/RSU/PS/SAR/ESOP)')
    parser.add_argument('--shares', type=int, default=10000, help='激励股数')
    parser.add_argument('--grant-price', type=float, default=1.0, help='行权价/授予价(元/股)')
    parser.add_argument('--fmv', type=float, default=5.0, help='当前公允市场价值(元/股)')
    parser.add_argument('--exit-price', type=float, default=0.0, help='预期退出价(元/股)')
    parser.add_argument('--stage', type=str, default='vc_a', help='企业阶段代码')
    parser.add_argument('--vesting', type=str, default='standard_4y', help='归属模式代码')
    parser.add_argument('--months', type=int, default=0, help='已归属月数')
    parser.add_argument('--defer', action='store_true', help='使用递延纳税策略')
    parser.add_argument('--city', type=str, default='北京', help='城市')
    parser.add_argument('--industry', type=str, default='互联网/科技', help='行业')
    parser.add_argument('--salary', type=float, default=0.0, help='年薪(元)')
    parser.add_argument('--compare', action='store_true', help='跨权益工具对比')
    parser.add_argument('--recommend', action='store_true', help='智能推荐')
    parser.add_argument('--role', type=str, default='核心研发', help='员工角色')
    parser.add_argument('--company-size', type=str, default='中型(100-499人)', help='公司规模')
    parser.add_argument('--dilution', action='store_true', help='稀释分析')
    parser.add_argument('--ts-outstanding', type=int, default=10000000, help='总发行股数')
    parser.add_argument('--pre-money', type=float, default=100000, help='投前估值(万元)')
    parser.add_argument('--exit-scenario', type=str, help='退出场景(IPO/并购/老股转让/清算)')
    parser.add_argument('--format', type=str, default='text',
                        choices=['text', 'markdown', 'html', 'json'], help='输出格式')
    parser.add_argument('--list-types', action='store_true', help='列出所有权益工具')
    parser.add_argument('--list-cities', action='store_true', help='列出所有城市税政')
    parser.add_argument('--list-regulations', action='store_true', help='列出法律依据')

    args = parser.parse_args()
    engine = EquityIncentiveEngine()
    out_fmt = OutputFormat(args.format)

    if args.stats:
        print(engine.get_stats())
        return

    if args.demo:
        print("【演示案例】互联网科技公司 — A轮 — 授予10,000股期权\n")
        calc = engine.calculate_full(
            EquityType.STOCK_OPTION, CompanyStage.VC_A, 10000,
            1.0, 5.0, VestingType.STANDARD_4Y, 18,
            expected_sale_price=25.0,
            use_tax_deferral=True, city="北京"
        )
        print(engine.format_result(calc, out_fmt, "北京", "互联网/科技"))
        print(f"\n{'='*60}")
        print("【对比：不使用递延纳税 vs 使用递延纳税】")
        calc2 = engine.calculate_full(
            EquityType.STOCK_OPTION, CompanyStage.VC_A, 10000,
            1.0, 5.0, VestingType.STANDARD_4Y, 18,
            expected_sale_price=25.0,
            use_tax_deferral=False, city="北京"
        )
        print(f"  递延纳税：税额{engine._fmt_money(calc.total_tax)}，净收益{engine._fmt_money(calc.expected_gain)}")
        print(f"  非递延  ：税额{engine._fmt_money(calc2.total_tax)}，净收益{engine._fmt_money(calc2.expected_gain)}")
        print(f"  节省税额：{engine._fmt_money(calc2.total_tax - calc.total_tax)}")
        return

    if args.list_types:
        print("权益工具类型：")
        for e in EquityType:
            defn = EQUITY_TYPE_DEFS[e]
            print(f"\n  {e.cn_name} ({e.abbr})")
            print(f"  {defn['description']}")
            print(f"  最适合：{defn['best_for']}")
        return

    if args.list_cities:
        print("城市税政列表：")
        for city, policy in CITY_TAX_POLICIES.items():
            flags = []
            if policy['tax_deferral']: flags.append('递延纳税')
            if policy['special_zone']: flags.append('特区')
            if policy['innovation_zone']: flags.append('创新示范区')
            if policy['local_subsidy'] > 0: flags.append(f"地方返还{policy['local_subsidy']:.0%}")
            print(f"  {city:<6} {' | '.join(flags) if flags else '无特殊政策'}")
        return

    if args.list_regulations:
        print("法律依据索引：")
        for ref, info in LEGAL_REFERENCES.items():
            print(f"\n  {ref}")
            print(f"  {info['title']}")
            print(f"  {info['core']}")
            if 'conditions' in info:
                print(f"  条件：{info['conditions']}")
        return

    if args.recommend:
        rec = engine.recommend(args.industry, args.stage, args.role, args.company_size)
        print(f"智能推荐 — {args.industry} | {args.role}")
        print(f"  企业阶段：{rec['company_stage']}")
        print(f"  推荐权益工具：{', '.join(rec['recommended_instruments'])}")
        print(f"  推荐期权池：{rec['recommended_pool_pct']}")
        print(f"  该岗位授予比例：{rec['grant_pct_for_role']}")
        print(f"  预计退出周期：{rec['exit_horizon']}")
        print(f"  风险等级：{rec['risk_level']}")
        print(f"  税务策略：{rec['tax_strategy']}")
        print(f"  行业实践：{rec['key_practices']}")
        print(f"  合规提示：{rec['legal_notes']}")
        return

    if args.dilution:
        da = engine.analyze_dilution(
            CompanyStage.VC_A, args.ts_outstanding,
            args.shares, args.pre_money * 10000
        )
        print(f"稀释分析 — {args.shares:,}股增发 / {args.ts_outstanding:,}股原有")
        print(f"  股权占比（稀释前）：{da.pre_dilution_pct:.3f}%")
        print(f"  股权占比（稀释后）：{da.post_dilution_pct:.3f}%")
        print(f"  稀释幅度：{da.dilution_hit:.1f}%")
        print(f"  每股价值（稀释前）：¥{da.per_share_value_before:.4f}")
        print(f"  每股价值（稀释后）：¥{da.per_share_value_after:.4f}")
        print(f"  是否重大稀释（>10%）：{'是 ⚠️' if da.is_significant else '否'}")
        return

    if args.compare:
        etype_map = {t.abbr: t for t in EquityType}
        etype = etype_map.get(args.type, EquityType.STOCK_OPTION)
        stage_map = {s.code: s for s in CompanyStage}
        stage = stage_map.get(args.stage, CompanyStage.VC_A)
        vtype_map = {v.code: v for v in VestingType}
        vtype = vtype_map.get(args.vesting, VestingType.STANDARD_4Y)

        calcs = engine.compare_types(
            args.shares, args.grant_price, args.fmv, vtype, stage,
            city=args.city, months_elapsed=args.months
        )
        print(engine.format_comparison(calcs, out_fmt))
        return

    # 单个计算
    etype_map = {t.abbr: t for t in EquityType}
    etype = etype_map.get(args.type, EquityType.STOCK_OPTION)
    stage_map = {s.code: s for s in CompanyStage}
    stage = stage_map.get(args.stage, CompanyStage.VC_A)
    vtype_map = {v.code: v for v in VestingType}
    vtype = vtype_map.get(args.vesting, VestingType.STANDARD_4Y)

    calc = engine.calculate_full(
        etype, stage, args.shares,
        args.grant_price, args.fmv, vtype, args.months,
        expected_sale_price=args.exit_price,
        use_tax_deferral=args.defer or (stage != CompanyStage.LISTED),
        city=args.city, annual_salary=args.salary
    )
    print(engine.format_result(calc, out_fmt, args.city, args.industry))

    # 如果有exit-scenario，追加退出分析
    if args.exit_scenario and args.exit_price > 0:
        exit_data = engine.simulate_exit(calc, args.exit_price, args.exit_scenario)
        print(f"\n{'='*60}")
        print(f"【{args.exit_scenario}退出场景】")
        print(f"  总收益：{engine._fmt_money(exit_data['gross_proceeds'])}")
        print(f"  总税额：{engine._fmt_money(exit_data['total_tax'])}")
        print(f"  税后净收益：{engine._fmt_money(exit_data['net_proceeds'])}")
        print(f"  ROI：{exit_data['roi']:.1%}")
        print(f"  {exit_data['message']}")


if __name__ == '__main__':
    main()

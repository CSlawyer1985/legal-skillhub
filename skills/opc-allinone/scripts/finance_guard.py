#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一人公司财务管家 / SoloFinance Guard v2.0
============================================
智能记账 · 发票管理 · 税务计算 · 财报生成 · 现金流管控 · 金税四期自查

专为一人公司(OPC)创业者设计的财税全链路管理助手
支持：有限责任公司（一人公司）/ 个体工商户 双主体模式
内置金税四期合规校验、最新税收优惠自动匹配、动态风险指标自查

版本: 2.0.0
日期: 2026-05-23
"""

import json
import re
import os
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

# =============================================================================
# 自定义 JSON 编码器（支持 Decimal 和 date 序列化）
# =============================================================================

class FinanceJSONEncoder(json.JSONEncoder):
    """支持 Decimal 和 date 的 JSON 编码器"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return {"__decimal__": str(obj)}
        if isinstance(obj, date):
            return {"__date__": obj.isoformat()}
        return super().default(obj)


def finance_json_decoder(dct):
    """JSON 解码器：还原 Decimal 和 date"""
    if "__decimal__" in dct:
        return Decimal(dct["__decimal__"])
    if "__date__" in dct:
        return date.fromisoformat(dct["__date__"])
    return dct


# =============================================================================
# 枚举定义
# =============================================================================

class EntryType(Enum):
    """记账类型"""
    INCOME = "收入"
    EXPENSE = "支出"
    TRANSFER = "转账"


class BusinessEntityType(Enum):
    """经营主体类型"""
    LIMITED_COMPANY = "有限责任公司"
    INDIVIDUAL_BUSINESS = "个体工商户"


class TaxpayerType(Enum):
    """纳税人类型"""
    SMALL_SCALE = "小规模纳税人"
    GENERAL = "一般纳税人"


class RiskLevel(Enum):
    """风险等级"""
    CRITICAL = "紧急"
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"


class InvoiceDirection(Enum):
    """发票方向"""
    SALES = "销项"
    PURCHASE = "进项"


# =============================================================================
# 数据模型
# =============================================================================

@dataclass
class AccountEntry:
    """记账条目 — 所有金额使用 Decimal"""
    date: date
    entry_type: EntryType
    amount: Decimal
    category_code: str
    category_name: str
    description: str
    counterparty: str = ""
    payment_method: str = ""
    invoice_no: str = ""
    is_deductible: bool = True
    notes: str = ""
    due_date: Optional[date] = None  # 应收账款到期日

    def to_dict(self) -> dict:
        return {
            "date": self.date.isoformat(),
            "entry_type": self.entry_type.value,
            "amount": str(self.amount),
            "category_code": self.category_code,
            "category_name": self.category_name,
            "description": self.description,
            "counterparty": self.counterparty,
            "payment_method": self.payment_method,
            "invoice_no": self.invoice_no,
            "is_deductible": self.is_deductible,
            "notes": self.notes,
            "due_date": self.due_date.isoformat() if self.due_date else None
        }

    @classmethod
    def from_dict(cls, d: dict) -> "AccountEntry":
        return cls(
            date=date.fromisoformat(d["date"]),
            entry_type=EntryType(d["entry_type"]),
            amount=Decimal(d["amount"]),
            category_code=d["category_code"],
            category_name=d["category_name"],
            description=d.get("description", ""),
            counterparty=d.get("counterparty", ""),
            payment_method=d.get("payment_method", ""),
            invoice_no=d.get("invoice_no", ""),
            is_deductible=d.get("is_deductible", True),
            notes=d.get("notes", ""),
            due_date=date.fromisoformat(d["due_date"]) if d.get("due_date") else None
        )


@dataclass
class Invoice:
    """发票记录"""
    invoice_no: str
    invoice_type: str
    invoice_code: str
    issue_date: date
    amount: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    counterparty: str
    direction: InvoiceDirection
    is_verified: bool = False
    is_voided: bool = False
    related_entry_id: str = ""

    def to_dict(self) -> dict:
        return {
            "invoice_no": self.invoice_no,
            "invoice_type": self.invoice_type,
            "invoice_code": self.invoice_code,
            "issue_date": self.issue_date.isoformat(),
            "amount": str(self.amount),
            "tax_rate": str(self.tax_rate),
            "tax_amount": str(self.tax_amount),
            "counterparty": self.counterparty,
            "direction": self.direction.value,
            "is_verified": self.is_verified,
            "is_voided": self.is_voided,
            "related_entry_id": self.related_entry_id
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Invoice":
        return cls(
            invoice_no=d["invoice_no"],
            invoice_type=d["invoice_type"],
            invoice_code=d["invoice_code"],
            issue_date=date.fromisoformat(d["issue_date"]),
            amount=Decimal(d["amount"]),
            tax_rate=Decimal(d["tax_rate"]),
            tax_amount=Decimal(d["tax_amount"]),
            counterparty=d["counterparty"],
            direction=InvoiceDirection(d["direction"]),
            is_verified=d.get("is_verified", False),
            is_voided=d.get("is_voided", False),
            related_entry_id=d.get("related_entry_id", "")
        )


@dataclass
class CompanyProfile:
    """公司/个体户档案"""
    name: str = ""
    tax_id: str = ""
    entity_type: BusinessEntityType = BusinessEntityType.LIMITED_COMPANY
    taxpayer_type: TaxpayerType = TaxpayerType.SMALL_SCALE
    registered_capital: Decimal = Decimal("0")
    city_type: str = "市区"
    filing_period: str = "monthly"  # monthly / quarterly
    monthly_fixed_costs: Decimal = Decimal("0")
    fiscal_year_start: str = "01-01"
    initial_balances: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "tax_id": self.tax_id,
            "entity_type": self.entity_type.value,
            "taxpayer_type": self.taxpayer_type.value,
            "registered_capital": str(self.registered_capital),
            "city_type": self.city_type,
            "filing_period": self.filing_period,
            "monthly_fixed_costs": str(self.monthly_fixed_costs),
            "fiscal_year_start": self.fiscal_year_start,
            "initial_balances": self.initial_balances
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CompanyProfile":
        return cls(
            name=d.get("name", ""),
            tax_id=d.get("tax_id", ""),
            entity_type=BusinessEntityType(d.get("entity_type", "有限责任公司")),
            taxpayer_type=TaxpayerType(d.get("taxpayer_type", "小规模纳税人")),
            registered_capital=Decimal(d.get("registered_capital", "0")),
            city_type=d.get("city_type", "市区"),
            filing_period=d.get("filing_period", "monthly"),
            monthly_fixed_costs=Decimal(d.get("monthly_fixed_costs", "0")),
            fiscal_year_start=d.get("fiscal_year_start", "01-01"),
            initial_balances=d.get("initial_balances", {})
        )


# =============================================================================
# 科目体系
# =============================================================================

CHART_OF_ACCOUNTS = {
    # 资产类
    "1001": {"name": "银行存款", "type": "资产"},
    "1002": {"name": "其他货币资金", "type": "资产"},
    "1003": {"name": "应收账款", "type": "资产"},
    "1004": {"name": "预付账款", "type": "资产"},
    "1005": {"name": "固定资产", "type": "资产"},
    # 负债类
    "2001": {"name": "应付账款", "type": "负债"},
    "2002": {"name": "应交税费", "type": "负债"},
    "2003": {"name": "预收账款", "type": "负债"},
    # 权益类
    "3001": {"name": "实收资本", "type": "权益"},
    "3002": {"name": "未分配利润", "type": "权益"},
    # 收入类
    "4001": {"name": "主营业务收入", "type": "收入"},
    "4002": {"name": "其他业务收入", "type": "收入"},
    "4003": {"name": "营业外收入", "type": "收入"},
    # 成本类
    "5001": {"name": "主营业务成本", "type": "成本"},
    "5002": {"name": "直接人工成本", "type": "成本"},
    # 费用类
    "5101": {"name": "办公费用", "type": "费用", "deductible": True},
    "5102": {"name": "场地费用", "type": "费用", "deductible": True},
    "5103": {"name": "差旅交通费", "type": "费用", "deductible": True},
    "5104": {"name": "业务招待费", "type": "费用", "deductible": True,
             "deduction_note": "按发生额60%扣除，最高不超当年销售收入5‰"},
    "5105": {"name": "广告推广费", "type": "费用", "deductible": True,
             "deduction_note": "不超销售收入15%可扣除，超额结转以后年度"},
    "5106": {"name": "软件开发工具", "type": "费用", "deductible": True},
    "5107": {"name": "培训学习费", "type": "费用", "deductible": True},
    "5108": {"name": "专业服务费", "type": "费用", "deductible": True},
    "5109": {"name": "银行手续费", "type": "费用", "deductible": True},
    "5110": {"name": "社保公积金", "type": "费用", "deductible": True},
    "5111": {"name": "折旧与摊销", "type": "费用", "deductible": True},
    "5112": {"name": "其他费用", "type": "费用", "deductible": False},
}

# 费用科目关键词映射
EXPENSE_KEYWORD_MAP = {
    "5101": ["办公", "文具", "打印", "快递", "饮用水", "纸张"],
    "5102": ["租金", "物业", "水电", "工位", "办公室"],
    "5103": ["差旅", "机票", "高铁", "打车", "酒店", "交通", "出差"],
    "5104": ["招待", "宴请", "请客", "礼品", "客户招待"],
    "5105": ["广告", "推广", "SEO", "营销", "投放"],
    "5106": ["服务器", "云服务", "AWS", "阿里云", "腾讯云", "GitHub", "API", "软件订阅", "域名"],
    "5107": ["培训", "课程", "大会", "会议", "学习"],
    "5108": ["律师", "代理记账", "审计", "咨询", "顾问"],
    "5109": ["银行", "手续费", "转账费", "年费"],
    "5110": ["社保", "公积金"],
    "5111": ["折旧", "摊销", "电脑", "设备"],
}

# 个人所得税（经营所得）五级超额累进税率表
PIT_BUSINESS_RATE_TABLE = [
    (Decimal("30000"),   Decimal("0.05"), Decimal("0")),
    (Decimal("90000"),   Decimal("0.10"), Decimal("1500")),
    (Decimal("300000"),  Decimal("0.20"), Decimal("10500")),
    (Decimal("500000"),  Decimal("0.30"), Decimal("40500")),
    (Decimal("inf"),     Decimal("0.35"), Decimal("65500")),
]

# 城建税税率
URBAN_TAX_RATES = {
    "市区": Decimal("0.07"),
    "县城": Decimal("0.05"),
    "其他": Decimal("0.01"),
}

# 税务日历基准（常规申报期限）
TAX_CALENDAR = {
    "增值税": {"freq": "月/季", "deadline": "月/季度终了后15日内"},
    "企业所得税": {"freq": "季/年", "deadline": "季度预缴：季度终了后15日内\n年度汇算清缴：次年5月31日前"},
    "经营所得个税": {"freq": "年", "deadline": "次年3月31日前"},
    "印花税": {"freq": "次", "deadline": "合同签订时"},
    "工商年报": {"freq": "年", "deadline": "每年1月1日至6月30日"},
}

# 一般纳税人强制认定门槛
GENERAL_TAXPAYER_THRESHOLD = Decimal("5000000")
GENERAL_TAXPAYER_WARN = Decimal("4000000")


# =============================================================================
# 工具函数：金额与日期处理
# =============================================================================

def d(amount) -> Decimal:
    """统一转换为 Decimal，避免浮点误差"""
    if isinstance(amount, Decimal):
        return amount
    return Decimal(str(amount))


def fmt(amount: Decimal) -> str:
    """格式化金额为千分位"""
    return f"{amount:,.2f}"


def validate_date(date_str: str) -> Optional[date]:
    """校验日期格式 YYYY-MM-DD，无效返回 None"""
    try:
        return date.fromisoformat(date_str)
    except (ValueError, TypeError):
        return None


def parse_amount(text: str) -> Optional[Decimal]:
    """解析金额：支持 50000 / 5万 / 50000元 / 5万元"""
    text = text.strip().replace(" ", "").replace(",", "").replace("，", "")
    # 匹配 "X万" 或 "X万元"
    wan_match = re.match(r'^(\d+(?:\.\d+)?)万(?:元)?$', text)
    if wan_match:
        return d(float(wan_match.group(1)) * 10000)
    # 匹配纯数字（可能带"元"后缀）
    num_match = re.match(r'^(\d+(?:\.\d+)?)(?:元)?$', text)
    if num_match:
        return d(num_match.group(1))
    return None


def validate_amount(amount: Decimal) -> Tuple[bool, str]:
    """校验金额合理性"""
    if amount <= Decimal("0"):
        return False, "金额必须大于0"
    if amount > Decimal("100000000"):
        return False, "单笔金额超过1亿元，请确认是否正确"
    return True, ""


def get_month_range(year: int, month: int) -> Tuple[date, date]:
    """获取某月的日期范围"""
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(year, month + 1, 1) - timedelta(days=1)
    return start, end


def get_quarter_months(month: int) -> List[int]:
    """获取某月所在的季度月份列表"""
    q = (month - 1) // 3
    return [q * 3 + 1, q * 3 + 2, q * 3 + 3]


# =============================================================================
# P0-3: 数据持久化管理器
# =============================================================================

class PersistenceManager:
    """数据持久化管理 — JSON 文件存储"""

    def __init__(self, data_dir: str = ".solo-finance-data"):
        self.data_dir = data_dir

    def _user_dir(self, user_id: str) -> str:
        return os.path.join(self.data_dir, user_id)

    def _ensure_dir(self, user_id: str):
        os.makedirs(self._user_dir(user_id), exist_ok=True)

    def save(self, engine: "BookkeepingEngine", invoice_mgr: "InvoiceManager",
             profile: CompanyProfile, user_id: str = "default") -> bool:
        """保存所有数据到 JSON 文件"""
        try:
            self._ensure_dir(user_id)
            base = self._user_dir(user_id)
            # 保存档案
            with open(os.path.join(base, "profile.json"), "w", encoding="utf-8") as f:
                json.dump(profile.to_dict(), f, ensure_ascii=False, indent=2, cls=FinanceJSONEncoder)
            # 保存记账条目
            with open(os.path.join(base, "entries.json"), "w", encoding="utf-8") as f:
                json.dump([e.to_dict() for e in engine.entries], f, ensure_ascii=False, indent=2)
            # 保存发票
            with open(os.path.join(base, "invoices.json"), "w", encoding="utf-8") as f:
                json.dump([inv.to_dict() for inv in invoice_mgr.invoices], f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[错误] 保存数据失败：{e}")
            return False

    def load(self, user_id: str = "default") -> Tuple[Optional["BookkeepingEngine"],
                                                        Optional["InvoiceManager"],
                                                        Optional[CompanyProfile]]:
        """从 JSON 文件加载数据"""
        try:
            base = self._user_dir(user_id)
            # 加载档案
            profile_path = os.path.join(base, "profile.json")
            if not os.path.exists(profile_path):
                return None, None, None
            with open(profile_path, "r", encoding="utf-8") as f:
                profile = CompanyProfile.from_dict(json.load(f))
            # 加载记账条目
            engine = BookkeepingEngine()
            entries_path = os.path.join(base, "entries.json")
            if os.path.exists(entries_path):
                with open(entries_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                    engine.entries = [AccountEntry.from_dict(e) for e in raw]
            # 加载发票
            invoice_mgr = InvoiceManager()
            invoices_path = os.path.join(base, "invoices.json")
            if os.path.exists(invoices_path):
                with open(invoices_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                    invoice_mgr.invoices = [Invoice.from_dict(e) for e in raw]
            return engine, invoice_mgr, profile
        except Exception as e:
            print(f"[错误] 加载数据失败：{e}")
            return None, None, None

    def clear(self, user_id: str = "default") -> bool:
        """清除所有数据"""
        try:
            base = self._user_dir(user_id)
            for fn in ["profile.json", "entries.json", "invoices.json"]:
                fp = os.path.join(base, fn)
                if os.path.exists(fp):
                    os.remove(fp)
            return True
        except Exception as e:
            print(f"[错误] 清除数据失败：{e}")
            return False

    def data_exists(self, user_id: str = "default") -> bool:
        """检查是否存在历史数据"""
        return os.path.exists(os.path.join(self._user_dir(user_id), "profile.json"))


# =============================================================================
# P0-1: 自然语言解析器
# =============================================================================

def parse_natural_language(text: str) -> Optional[dict]:
    """
    解析自然语言记账指令，返回结构化数据或 None（解析失败）

    支持的指令格式：
      • 记收入 {金额} {来自?}{对方} [{付款方式}]
      • 记支出 {金额} {用途} [{付款方式}]
      • 记报销 {金额} {事由}
      • 记一笔收入/支出 ... （扩展同义表达）

    返回: {action, amount, counterparty, payment_method, description, entry_type}
    """
    text = text.strip()

    # --- 收入指令 ---
    income_patterns = [
        r'(?:记|记一笔|录入|添加)\s*(?:收入|收款)\s*(.+)',
    ]
    for pat in income_patterns:
        m = re.match(pat, text)
        if m:
            rest = m.group(1).strip()
            return _parse_income(rest)

    # --- 支出指令 ---
    expense_patterns = [
        r'(?:记|记一笔|录入|添加)\s*(?:支出|付款|花费)\s*(.+)',
    ]
    for pat in expense_patterns:
        m = re.match(pat, text)
        if m:
            rest = m.group(1).strip()
            return _parse_expense(rest)

    # --- 报销指令 ---
    reimburse_patterns = [
        r'(?:记|记一笔|录入|添加)\s*(?:报销)\s*(.+)',
    ]
    for pat in reimburse_patterns:
        m = re.match(pat, text)
        if m:
            rest = m.group(1).strip()
            result = _parse_expense(rest)
            if result:
                result["action"] = "报销"
                result["entry_type"] = EntryType.EXPENSE
                return result

    return None


def _parse_income(text: str) -> Optional[dict]:
    """解析收入指令的剩余部分：金额 [来自][对方] [付款方式]"""
    # 先提取金额（开头第一个数字/金额表达）
    amount_match = re.match(r'(\d+(?:\.\d+)?(?:万(?:元)?|元)?)\s*(.*)', text)
    if not amount_match:
        return None
    amount = parse_amount(amount_match.group(1))
    if amount is None:
        return None
    rest = amount_match.group(2).strip()

    # 提取对方单位（"来自XX" 或 "从XX"）
    counterparty = ""
    cp_match = re.match(r'(?:来自|从)(\S+?)(?:\s|$)(.*)', rest)
    if cp_match:
        counterparty = cp_match.group(1).strip()
        rest = cp_match.group(2).strip()

    # 提取付款方式
    payment_method = ""
    pm_keywords = ["银行转账", "支付宝", "微信", "现金", "应收账款", "未收款", "个人卡",
                   "个人微信", "个人支付宝", "公司账户", "对公转账", "境外电汇"]
    for pm in pm_keywords:
        if pm in rest:
            payment_method = pm
            rest = rest.replace(pm, "").strip()
            break

    return {
        "action": "收入",
        "amount": amount,
        "counterparty": counterparty,
        "payment_method": payment_method or "银行转账",
        "description": rest or counterparty,
        "entry_type": EntryType.INCOME
    }


def _parse_expense(text: str) -> Optional[dict]:
    """解析支出/报销指令的剩余部分"""
    amount_match = re.match(r'(\d+(?:\.\d+)?(?:万(?:元)?|元)?)\s*(.*)', text)
    if not amount_match:
        return None
    amount = parse_amount(amount_match.group(1))
    if amount is None:
        return None
    rest = amount_match.group(2).strip()

    # 找出付款方式
    payment_method = ""
    pm_keywords = ["银行转账", "支付宝", "微信", "现金", "个人卡",
                   "个人微信", "个人支付宝", "公司账户", "对公转账"]
    for pm in pm_keywords:
        if pm in rest:
            payment_method = pm
            rest = rest.replace(pm, "").strip()
            break

    return {
        "action": "支出",
        "amount": amount,
        "counterparty": "",
        "payment_method": payment_method or "银行转账",
        "description": rest,
        "entry_type": EntryType.EXPENSE
    }


def get_format_hint() -> str:
    """返回记账指令格式提示"""
    return """📝 记账指令格式：
  · 记收入 50000 来自XX科技 银行转账
  · 记支出 8000 购买阿里云服务器 支付宝
  · 记报销 1500 去北京拜访客户差旅

  金额支持：50000 / 5万 / 50000元 / 5万元
  付款方式支持：银行转账 / 支付宝 / 微信 / 现金 / 应收账款 / 个人卡"""


# =============================================================================
# 记账引擎（增强版）
# =============================================================================

class BookkeepingEngine:
    """智能记账引擎 — 使用 Decimal，支持持久化"""

    def __init__(self):
        self.entries: List[AccountEntry] = []
        self._persistence: Optional[PersistenceManager] = None

    def set_persistence(self, pm: PersistenceManager):
        self._persistence = pm

    def add_entry(self, entry: AccountEntry) -> Tuple[bool, str]:
        """添加记账条目，含校验"""
        # 校验日期
        if not isinstance(entry.date, date):
            return False, "日期格式无效"
        # 校验金额
        valid, msg = validate_amount(entry.amount)
        if not valid:
            return False, msg
        # 校验科目存在
        if entry.category_code not in CHART_OF_ACCOUNTS:
            return False, f"科目编码 {entry.category_code} 不存在"
        self.entries.append(entry)
        return True, "记账成功"

    def smart_categorize(self, description: str, entry_type: EntryType) -> Tuple[str, str]:
        """根据描述智能识别科目，返回 (编码, 名称)"""
        if entry_type == EntryType.INCOME:
            return "4001", "主营业务收入"
        if entry_type == EntryType.EXPENSE:
            for code, keywords in EXPENSE_KEYWORD_MAP.items():
                for kw in keywords:
                    if kw in description:
                        return code, CHART_OF_ACCOUNTS[code]["name"]
            return "5112", "其他费用"
        return "", ""

    def get_monthly_summary(self, year: int, month: int) -> dict:
        """获取月度汇总（使用 Decimal）"""
        total_income = Decimal("0")
        total_cost = Decimal("0")
        total_expense = Decimal("0")
        expense_by_category = defaultdict(lambda: Decimal("0"))
        start, end = get_month_range(year, month)

        for entry in self.entries:
            if not (start <= entry.date <= end):
                continue
            if entry.entry_type == EntryType.INCOME:
                total_income += entry.amount
            elif entry.entry_type == EntryType.EXPENSE:
                cat = entry.category_code
                if cat.startswith("50") and cat != "5001" and cat != "5002":
                    pass  # skip non-cost 5xxx
                if cat.startswith("500"):
                    total_cost += entry.amount
                elif cat.startswith("51"):
                    total_expense += entry.amount
                    expense_by_category[cat] += entry.amount

        gross_profit = total_income - total_cost
        operating_profit = gross_profit - total_expense

        gross_margin = (gross_profit / total_income * 100).quantize(Decimal("0.1")) if total_income > 0 else Decimal("0")
        op_margin = (operating_profit / total_income * 100).quantize(Decimal("0.1")) if total_income > 0 else Decimal("0")
        expense_ratio = (total_expense / total_income * 100).quantize(Decimal("0.1")) if total_income > 0 else Decimal("0")

        return {
            "year": year, "month": month,
            "total_income": total_income,
            "total_cost": total_cost,
            "gross_profit": gross_profit,
            "gross_margin": gross_margin,
            "total_expense": total_expense,
            "expense_by_category": dict(expense_by_category),
            "operating_profit": operating_profit,
            "operating_margin": op_margin,
            "expense_ratio": expense_ratio
        }

    def get_annual_revenue(self, year: int) -> Decimal:
        """获取年度累计收入"""
        total = Decimal("0")
        for entry in self.entries:
            if entry.date.year == year and entry.entry_type == EntryType.INCOME:
                total += entry.amount
        return total

    def get_rolling_12m_revenue(self, ref_date: Optional[date] = None) -> Decimal:
        """获取最近12个月滚动收入（用于一般纳税人门槛判断）"""
        if ref_date is None:
            ref_date = date.today()
        start = ref_date - timedelta(days=365)
        total = Decimal("0")
        for entry in self.entries:
            if start <= entry.date <= ref_date and entry.entry_type == EntryType.INCOME:
                total += entry.amount
        return total

    def get_account_balance(self, account_code: str, as_of: Optional[date] = None,
                            initial_balance: Decimal = Decimal("0")) -> Decimal:
        """获取某科目截至某日的余额"""
        balance = initial_balance
        info = CHART_OF_ACCOUNTS.get(account_code, {})
        acct_type = info.get("type", "")
        for entry in self.entries:
            if as_of and entry.date > as_of:
                continue
            if entry.category_code == account_code:
                if entry.entry_type == EntryType.INCOME:
                    if acct_type in ("收入", "权益", "负债"):
                        balance += entry.amount
                    elif acct_type == "资产":
                        balance += entry.amount
                elif entry.entry_type == EntryType.EXPENSE:
                    if acct_type in ("费用", "成本", "资产"):
                        balance -= entry.amount
        return balance

    def get_personal_account_entries(self, year: int, month: int) -> List[AccountEntry]:
        """获取某月通过个人账户收付款的条目（用于公私分离检查）"""
        personal_keywords = ["个人微信", "个人支付宝", "个人卡"]
        start, end = get_month_range(year, month)
        results = []
        for entry in self.entries:
            if start <= entry.date <= end:
                if any(kw in entry.payment_method for kw in personal_keywords):
                    results.append(entry)
        return results

    def clear(self):
        """清空所有条目"""
        self.entries.clear()


# =============================================================================
# P0-2: 税务计算引擎（扩展版 — 支持公司/个体户双主体）
# =============================================================================

class TaxEngine:
    """税务计算引擎 — 支持有限责任公司和个体工商户双模式"""

    @staticmethod
    def calculate_vat(period_revenue: Decimal, taxpayer_type: TaxpayerType,
                      filing_period: str = "monthly",
                      quarterly_revenues: Optional[List[Decimal]] = None) -> dict:
        """
        计算增值税（支持月度/季度申报）
        """
        if taxpayer_type == TaxpayerType.SMALL_SCALE:
            # 确定免征门槛
            if filing_period == "quarterly" and quarterly_revenues:
                total_q = sum(quarterly_revenues, Decimal("0"))
                threshold = Decimal("300000")
                check_amount = total_q
            else:
                threshold = Decimal("100000")
                check_amount = period_revenue

            if check_amount <= threshold:
                period_label = "季度" if filing_period == "quarterly" else "月度"
                return {
                    "vat_amount": Decimal("0"),
                    "effective_rate": Decimal("0"),
                    "policy_applied": f"免征增值税（{period_label}销售额≤{fmt(threshold)}元）",
                    "legal_basis": "财政部 税务总局公告2023年第19号",
                    "valid_until": "2027-12-31"
                }
            else:
                vat = (period_revenue * Decimal("0.01")).quantize(Decimal("0.01"))
                return {
                    "vat_amount": vat,
                    "effective_rate": Decimal("0.01"),
                    "policy_applied": "减按1%征收（优惠税率）",
                    "legal_basis": "财政部 税务总局公告2023年第19号",
                    "valid_until": "2027-12-31"
                }
        else:
            vat = (period_revenue * Decimal("0.06")).quantize(Decimal("0.01"))
            return {
                "vat_amount": vat,
                "effective_rate": Decimal("0.06"),
                "policy_applied": "一般纳税人标准税率6%（服务业）",
                "legal_basis": "《中华人民共和国增值税法》"
            }

    @staticmethod
    def calculate_additional_taxes(vat_amount: Decimal, city_type: str = "市区",
                                    is_individual: bool = False) -> dict:
        """计算附加税（个体户附加税减半）"""
        if vat_amount == Decimal("0"):
            return {"urban": Decimal("0"), "education": Decimal("0"),
                    "local_education": Decimal("0"), "total": Decimal("0")}

        urban_rate = URBAN_TAX_RATES.get(city_type, Decimal("0.07"))
        # 个体户附加税减半
        if is_individual:
            urban_rate = urban_rate / Decimal("2")
            edu_rate = Decimal("0.015")
            local_edu_rate = Decimal("0.01")
        else:
            edu_rate = Decimal("0.03")
            local_edu_rate = Decimal("0.02")

        urban = (vat_amount * urban_rate).quantize(Decimal("0.01"))
        education = (vat_amount * edu_rate).quantize(Decimal("0.01"))
        local_edu = (vat_amount * local_edu_rate).quantize(Decimal("0.01"))

        return {
            "urban": urban,
            "education": education,
            "local_education": local_edu,
            "total": (urban + education + local_edu).quantize(Decimal("0.01"))
        }

    @staticmethod
    def calculate_cit(taxable_income: Decimal) -> dict:
        """
        计算企业所得税（适用小型微利优惠）
        taxable_income: 应纳税所得额（非会计利润！）
        """
        if taxable_income <= Decimal("3000000"):
            effective_tax = (taxable_income * Decimal("0.05")).quantize(Decimal("0.01"))
            standard_tax = (taxable_income * Decimal("0.25")).quantize(Decimal("0.01"))
            return {
                "taxable_income": taxable_income,
                "standard_tax": standard_tax,
                "tax_relief": standard_tax - effective_tax,
                "effective_tax": effective_tax,
                "effective_rate": Decimal("0.05"),
                "policy": "小型微利企业优惠（实际税率5%）",
                "legal_basis": "财政部 税务总局公告2023年第12号",
                "valid_until": "2027-12-31"
            }
        else:
            standard_tax = (taxable_income * Decimal("0.25")).quantize(Decimal("0.01"))
            return {
                "taxable_income": taxable_income,
                "standard_tax": standard_tax,
                "tax_relief": Decimal("0"),
                "effective_tax": standard_tax,
                "effective_rate": Decimal("0.25"),
                "policy": "不适用小型微利优惠（应纳所得额>300万）",
                "legal_basis": "《中华人民共和国企业所得税法》第四条"
            }

    @staticmethod
    def calculate_pit_business(annual_taxable_income: Decimal) -> dict:
        """
        计算个体工商户经营所得个人所得税
        五级超额累进税率 + 年应纳税所得额 ≤ 200万减半征收
        返回详细计算过程
        """
        # 查找适用税率级次
        applied_rate = Decimal("0")
        quick_deduction = Decimal("0")
        level = 0
        for i, (threshold, rate, qd) in enumerate(PIT_BUSINESS_RATE_TABLE):
            level = i + 1
            if annual_taxable_income <= threshold or threshold == Decimal("inf"):
                applied_rate = rate
                quick_deduction = qd
                break

        # 标准税额
        standard_tax = (annual_taxable_income * applied_rate - quick_deduction).quantize(Decimal("0.01"))
        if standard_tax < Decimal("0"):
            standard_tax = Decimal("0")

        # 减半优惠（≤200万）
        half_relief = Decimal("0")
        if annual_taxable_income <= Decimal("2000000"):
            half_relief = (standard_tax / Decimal("2")).quantize(Decimal("0.01"))
            effective_tax = standard_tax - half_relief
        else:
            effective_tax = standard_tax

        return {
            "taxable_income": annual_taxable_income,
            "tax_rate": applied_rate,
            "tax_level": level,
            "quick_deduction": quick_deduction,
            "standard_tax": standard_tax,
            "half_relief": half_relief,
            "effective_tax": effective_tax,
            "has_half_relief": half_relief > Decimal("0"),
            "policy": "五级超额累进" + ("，年应纳所得≤200万减半征收" if half_relief > 0 else ""),
            "legal_basis": "《中华人民共和国个人所得税法》+ 财政部 税务总局公告",
            "valid_until": "2027-12-31"
        }

    @staticmethod
    def calculate_dividend_tax(net_profit: Decimal) -> dict:
        """计算分红个税提醒（有限公司向股东分红，适用20%）"""
        tax = (net_profit * Decimal("0.20")).quantize(Decimal("0.01"))
        return {
            "net_profit": net_profit,
            "dividend_tax_rate": Decimal("0.20"),
            "dividend_tax": tax,
            "after_tax_dividend": net_profit - tax,
            "note": "⚠️ 分红时需按20%缴纳股息红利个人所得税。如果暂不分红则无需缴纳。"
        }

    @staticmethod
    def calculate_stamp_tax(contract_amount: Decimal) -> Decimal:
        """计算印花税（千分之零点三）"""
        return (contract_amount * Decimal("0.0003")).quantize(Decimal("0.01"))

    @staticmethod
    def check_general_taxpayer_risk(rolling_12m_revenue: Decimal) -> Optional[dict]:
        """检查一般纳税人强制认定风险"""
        if rolling_12m_revenue >= GENERAL_TAXPAYER_THRESHOLD:
            return {
                "status": "exceeded",
                "severity": RiskLevel.CRITICAL,
                "message": "连续12个月销售额已达500万，将被强制认定为一般纳税人",
                "rolling_12m_revenue": rolling_12m_revenue
            }
        elif rolling_12m_revenue >= GENERAL_TAXPAYER_WARN:
            gap = GENERAL_TAXPAYER_THRESHOLD - rolling_12m_revenue
            return {
                "status": "approaching",
                "severity": RiskLevel.HIGH,
                "message": f"近12月销售额{fmt(rolling_12m_revenue / 10000)}万，距500万仅差{fmt(gap / 10000)}万",
                "rolling_12m_revenue": rolling_12m_revenue,
                "gap": gap
            }
        return None


# =============================================================================
# P1-1: 纳税调整引擎
# =============================================================================

class TaxAdjuster:
    """企业所得税纳税调整器 — 从会计利润到应纳税所得额"""

    @staticmethod
    def adjust_profit(accounting_profit: Decimal, entries: List[AccountEntry],
                      annual_revenue: Decimal, year: int) -> dict:
        """
        计算纳税调整
        返回: {accounting_profit, adjustments[], taxable_income}
        """
        adjustments = []

        # 1. 业务招待费调整（科目5104）
        entertainment_total = Decimal("0")
        for e in entries:
            if e.date.year == year and e.category_code == "5104":
                entertainment_total += e.amount

        if entertainment_total > Decimal("0"):
            max_deduct_60pct = (entertainment_total * Decimal("0.6")).quantize(Decimal("0.01"))
            max_deduct_5permille = (annual_revenue * Decimal("0.005")).quantize(Decimal("0.01"))
            deductible_entertainment = min(max_deduct_60pct, max_deduct_5permille)
            adjust_entertainment = entertainment_total - deductible_entertainment
            if adjust_entertainment > Decimal("0"):
                adjustments.append({
                    "item": "业务招待费调增",
                    "account": "5104",
                    "original": entertainment_total,
                    "deductible": deductible_entertainment,
                    "adjustment": adjust_entertainment,
                    "rule": f"发生额的60%({fmt(max_deduct_60pct)})与收入5‰({fmt(max_deduct_5permille)})孰低"
                })

        # 2. 广告推广费调整（科目5105）
        ad_total = Decimal("0")
        for e in entries:
            if e.date.year == year and e.category_code == "5105":
                ad_total += e.amount

        if ad_total > Decimal("0"):
            max_ad_deduct = (annual_revenue * Decimal("0.15")).quantize(Decimal("0.01"))
            if ad_total > max_ad_deduct:
                adjustments.append({
                    "item": "广告推广费调增",
                    "account": "5105",
                    "original": ad_total,
                    "deductible": max_ad_deduct,
                    "adjustment": ad_total - max_ad_deduct,
                    "rule": f"不超过销售收入15%({fmt(max_ad_deduct)})，超出部分结转以后年度"
                })

        # 3. 无票支出调增
        non_deductible_total = Decimal("0")
        for e in entries:
            if e.date.year == year and e.entry_type == EntryType.EXPENSE and not e.is_deductible:
                non_deductible_total += e.amount

        if non_deductible_total > Decimal("0"):
            adjustments.append({
                "item": "无票支出调增",
                "account": "-",
                "original": non_deductible_total,
                "deductible": Decimal("0"),
                "adjustment": non_deductible_total,
                "rule": "未取得合规发票，不得税前扣除"
            })

        # 汇总
        total_adjustment = sum((adj["adjustment"] for adj in adjustments), Decimal("0"))
        taxable_income = accounting_profit + total_adjustment

        return {
            "accounting_profit": accounting_profit,
            "adjustments": adjustments,
            "total_adjustment": total_adjustment,
            "taxable_income": taxable_income
        }


# =============================================================================
# P1-3: 发票管理模块
# =============================================================================

class InvoiceManager:
    """发票管理器 — 开票/收票全流程管理"""

    def __init__(self):
        self.invoices: List[Invoice] = []

    def register_invoice(self, invoice: Invoice) -> Tuple[bool, str]:
        """登记发票"""
        if not invoice.invoice_no:
            return False, "发票号码不能为空"
        # 查重
        for inv in self.invoices:
            if inv.invoice_no == invoice.invoice_no:
                return False, f"发票 {invoice.invoice_no} 已存在"
        self.invoices.append(invoice)
        return True, f"发票 {invoice.invoice_no} 登记成功"

    def check_unbilled_income(self, entries: List[AccountEntry]) -> List[dict]:
        """检查已收款但未开票的收入 — 返回提醒列表"""
        reminders = []
        today = date.today()
        for entry in entries:
            if entry.entry_type != EntryType.INCOME:
                continue
            # 已绑定发票则跳过
            if entry.invoice_no:
                continue
            # 未收款的跳过
            if entry.payment_method in ("应收账款", "未收款"):
                continue

            days_since = (today - entry.date).days
            if days_since > 0:
                reminders.append({
                    "counterparty": entry.counterparty,
                    "amount": entry.amount,
                    "date": entry.date,
                    "days_since": days_since,
                    "severity": "🔴" if days_since > 30 else ("🟡" if days_since > 15 else "🟢")
                })
        return reminders

    def check_missing_receipt_invoices(self, entries: List[AccountEntry]) -> List[dict]:
        """检查支出超15天未取得发票 — 返回提醒列表"""
        reminders = []
        today = date.today()
        for entry in entries:
            if entry.entry_type != EntryType.EXPENSE:
                continue
            if entry.invoice_no:
                continue
            days_since = (today - entry.date).days
            if days_since > 15:
                reminders.append({
                    "description": entry.description,
                    "amount": entry.amount,
                    "date": entry.date,
                    "days_since": days_since,
                })
        return reminders

    def check_unbilled_expense_ratio(self, entries: List[AccountEntry],
                                      year: int, month: int) -> Optional[dict]:
        """检查无票支出占比 — 超过30%输出预警"""
        start, end = get_month_range(year, month)
        total_expense = Decimal("0")
        unbilled_expense = Decimal("0")
        for entry in entries:
            if not (start <= entry.date <= end):
                continue
            if entry.entry_type != EntryType.EXPENSE:
                continue
            total_expense += entry.amount
            if not entry.is_deductible:
                unbilled_expense += entry.amount

        if total_expense == Decimal("0"):
            return None

        ratio = unbilled_expense / total_expense
        if ratio > Decimal("0.30"):
            estimated_extra_tax = (unbilled_expense * Decimal("0.05")).quantize(Decimal("0.01"))
            return {
                "total_expense": total_expense,
                "unbilled_expense": unbilled_expense,
                "ratio": ratio,
                "ratio_pct": (ratio * 100).quantize(Decimal("0.1")),
                "estimated_extra_tax": estimated_extra_tax,
                "severity": RiskLevel.HIGH
            }
        return None

    def get_invoice_void_rate(self, year: int, month: int) -> Optional[dict]:
        """计算月度发票作废率"""
        start, end = get_month_range(year, month)
        total = 0
        voided = 0
        for inv in self.invoices:
            if start <= inv.issue_date <= end:
                total += 1
                if inv.is_voided:
                    voided += 1
        if total == 0:
            return None
        rate = Decimal(str(voided)) / Decimal(str(total))
        return {
            "total": total,
            "voided": voided,
            "rate": rate,
            "rate_pct": (rate * 100).quantize(Decimal("0.1")),
            "is_abnormal": rate > Decimal("0.10")
        }


# =============================================================================
# 现金流管理器（增强版 — 含应收账款追踪）
# =============================================================================

class CashflowManager:
    """现金流管理器 — 资金预警 + 应收账款催款"""

    @staticmethod
    def analyze_cash_health(total_cash: Decimal, avg_monthly_outflow: Decimal,
                            total_ar: Decimal = Decimal("0"),
                            total_ap: Decimal = Decimal("0")) -> dict:
        """分析现金流健康状况"""
        if avg_monthly_outflow <= Decimal("0"):
            months_reserve = Decimal("inf")
        else:
            months_reserve = (total_cash / avg_monthly_outflow).quantize(Decimal("0.1"))

        if months_reserve == Decimal("inf") or months_reserve >= Decimal("6"):
            health = "健康 ✅"
            level = RiskLevel.LOW
        elif months_reserve >= Decimal("3"):
            health = "关注 ⚠️"
            level = RiskLevel.MEDIUM
        else:
            health = "紧急 🚨"
            level = RiskLevel.CRITICAL

        return {
            "total_cash": total_cash,
            "months_reserve": months_reserve,
            "health_status": health,
            "health_level": level,
            "total_ar": total_ar,
            "total_ap": total_ap,
            "net_working_capital": total_cash + total_ar - total_ap
        }

    @staticmethod
    def check_ar_overdue(entries: List[AccountEntry]) -> List[dict]:
        """检查应收账款逾期情况"""
        today = date.today()
        overdue_list = []
        for entry in entries:
            if entry.entry_type != EntryType.INCOME:
                continue
            if entry.payment_method not in ("应收账款", "未收款"):
                continue
            if not entry.due_date:
                continue
            days_overdue = (today - entry.due_date).days
            if days_overdue > 0:
                if 0 < days_overdue <= 15:
                    severity = "🟡 刚逾期"
                elif 15 < days_overdue <= 30:
                    severity = "🟠 严重逾期"
                else:
                    severity = "🔴 非常严重"
                overdue_list.append({
                    "counterparty": entry.counterparty,
                    "amount": entry.amount,
                    "due_date": entry.due_date,
                    "days_overdue": days_overdue,
                    "severity": severity
                })
            elif days_overdue >= -7:
                overdue_list.append({
                    "counterparty": entry.counterparty,
                    "amount": entry.amount,
                    "due_date": entry.due_date,
                    "days_overdue": days_overdue,
                    "severity": "🟢 即将到期"
                })
        return sorted(overdue_list, key=lambda x: x["days_overdue"], reverse=True)

    @staticmethod
    def check_large_expense(amount: Decimal, avg_monthly_income: Decimal) -> Optional[dict]:
        """大额支出预警：单笔超过月均收入50%"""
        if avg_monthly_income <= Decimal("0"):
            return None
        ratio = amount / avg_monthly_income
        if ratio > Decimal("0.5"):
            return {
                "amount": amount,
                "ratio": ratio,
                "ratio_pct": (ratio * 100).quantize(Decimal("0.1")),
                "message": f"这笔{fmt(amount)}元支出相当于月均收入的{fmt(ratio * 100)}%，请确认是否必要"
            }
        return None

    @staticmethod
    def check_client_concentration(entries: List[AccountEntry], year: int) -> Optional[dict]:
        """客户集中度风险：单一客户收入 > 50%"""
        client_revenue = defaultdict(lambda: Decimal("0"))
        total = Decimal("0")
        for entry in entries:
            if entry.date.year == year and entry.entry_type == EntryType.INCOME:
                client_revenue[entry.counterparty] += entry.amount
                total += entry.amount
        if total == Decimal("0"):
            return None
        for client, rev in client_revenue.items():
            ratio = rev / total
            if ratio > Decimal("0.5"):
                return {
                    "client": client,
                    "revenue": rev,
                    "ratio": ratio,
                    "ratio_pct": (ratio * 100).quantize(Decimal("0.1")),
                    "message": f"{client}贡献了{fmt(ratio * 100)}%的收入，客户过于集中"
                }
        return None


# =============================================================================
# P2-1: 金税四期风险自查（动态数据驱动）
# =============================================================================

class GoldenTaxInspector:
    """金税四期风险自查引擎 — 基于实际账簿数据"""

    @staticmethod
    def inspect(entries: List[AccountEntry], invoices: List[Invoice],
                profile: CompanyProfile, year: int, month: int) -> dict:
        """全面风险自查，返回风险列表"""
        risks = []
        start, end = get_month_range(year, month)

        # --- 计算基础指标 ---
        total_income = Decimal("0")
        total_cost = Decimal("0")
        total_expense = Decimal("0")
        personal_count = 0
        expense_by_cat = defaultdict(lambda: Decimal("0"))

        for entry in entries:
            if not (start <= entry.date <= end):
                continue
            if entry.entry_type == EntryType.INCOME:
                total_income += entry.amount
            elif entry.entry_type == EntryType.EXPENSE:
                if entry.category_code.startswith("500"):
                    total_cost += entry.amount
                else:
                    total_expense += entry.amount
                    expense_by_cat[entry.category_code] += entry.amount

            # 公私分离检测
            if any(kw in entry.payment_method for kw in ("个人微信", "个人支付宝", "个人卡")):
                personal_count += 1

        # RISK-002: 成本率异常
        if total_income > Decimal("0"):
            cost_rate = total_cost / total_income
            if cost_rate < Decimal("0.20") or cost_rate > Decimal("0.70"):
                risks.append({
                    "code": "RISK-002", "name": "成本率异常",
                    "severity": RiskLevel.MEDIUM,
                    "detail": f"本月成本率{cost_rate.quantize(Decimal('0.001'))*100:.1f}%，"
                              f"正常范围为20%-70%",
                    "trigger": "触发行业画像比对"
                })

        # RISK-006: 公转私异常
        if personal_count >= 3:
            risks.append({
                "code": "RISK-006", "name": "公转私异常",
                "severity": RiskLevel.HIGH,
                "detail": f"本月通过个人账户交易{personal_count}次",
                "legal": "《公司法》第23条第三款：一人公司股东不能证明财产独立的，承担连带责任"
            })

        # RISK-008: 费用结构异常
        if total_expense > Decimal("0"):
            for cat_code, cat_amount in expense_by_cat.items():
                if cat_code in ("5104", "5103"):
                    ratio = cat_amount / total_expense
                    if ratio > Decimal("0.20"):
                        cat_name = CHART_OF_ACCOUNTS.get(cat_code, {}).get("name", cat_code)
                        risks.append({
                            "code": "RISK-008", "name": "费用结构异常",
                            "severity": RiskLevel.MEDIUM,
                            "detail": f"{cat_name}占比{(ratio*100).quantize(Decimal('0.1'))}%，超过20%警戒线"
                        })

        # RISK-009: 长期零申报（跨月检查）
        zero_months = 0
        for m in range(1, month + 1):
            ms, me = get_month_range(year, m)
            m_income = Decimal("0")
            for entry in entries:
                if ms <= entry.date <= me and entry.entry_type == EntryType.INCOME:
                    m_income += entry.amount
            if m_income == Decimal("0"):
                zero_months += 1
        if zero_months >= 3:
            risks.append({
                "code": "RISK-009", "name": "长期零申报",
                "severity": RiskLevel.MEDIUM,
                "detail": f"本年度已有{zero_months}个月零申报，有真实业务必须据实申报"
            })

        # RISK-005: 发票作废率
        for inv in invoices:
            pass  # 由 InvoiceManager 计算

        # 税负率
        if total_income > Decimal("0"):
            # 预估税负
            est_tax = total_income * Decimal("0.01")
            tax_burden = est_tax / total_income
            if tax_burden < Decimal("0.005"):
                risks.append({
                    "code": "RISK-004", "name": "税负率异常",
                    "severity": RiskLevel.HIGH,
                    "detail": f"预估税负率{tax_burden.quantize(Decimal('0.0001'))*100:.2f}%偏低，确保所有收入已入账"
                })

        return {
            "period": f"{year}年{month}月",
            "risks": risks,
            "high_count": sum(1 for r in risks if r["severity"] == RiskLevel.HIGH),
            "medium_count": sum(1 for r in risks if r["severity"] == RiskLevel.MEDIUM),
            "low_count": sum(1 for r in risks if r["severity"] == RiskLevel.LOW),
            "personal_txn_count": personal_count
        }

    @staticmethod
    def generate_inspection_report(inspection: dict, invoice_void_rate: Optional[dict] = None) -> str:
        """生成金税四期风险自查报告"""
        risks = inspection.get("risks", [])
        report = f"""# 🛡️ 金税四期税务风险自查报告

自查期间：{inspection['period']}

> 2026年金税四期全面落地，打通47个部门数据，178项风险指标实时监控。

## 📊 风险概览

| 等级 | 数量 |
|------|------|
| 🔴 高风险 | {inspection['high_count']} 项 |
| 🟡 中风险 | {inspection['medium_count']} 项 |
| 🟢 低风险 | {inspection['low_count']} 项 |
"""

        if risks:
            report += "\n## ⚠️ 已触发的风险指标\n\n"
            for risk in risks:
                emoji = "🔴" if risk["severity"] == RiskLevel.HIGH else "🟡"
                report += f"### {emoji} {risk['code']} - {risk['name']}\n"
                report += f"- **详情**：{risk['detail']}\n"
                if "legal" in risk:
                    report += f"- **法律依据**：{risk['legal']}\n"
                if "trigger" in risk:
                    report += f"- **金四触发**：{risk['trigger']}\n"
                report += "\n"
        else:
            report += "\n## ✅ 当前无风险指标触发\n\n本月表现良好，继续保持合规经营。\n"

        # 公私分离特别检查
        personal_count = inspection.get("personal_txn_count", 0)
        if personal_count > 0:
            report += f"""## 🚨 公私分离警告

⚠️ **本月通过个人账户收取/支付公司款项 {personal_count} 次！**

根据《中华人民共和国公司法》(2023修订) **第二十三条第三款**（2024年7月1日生效）：
> "只有一个股东的公司，股东不能证明公司财产独立于股东自己的财产的，应当对公司债务承担连带责任。"

**建议：**
1. 立即开立公司对公账户（如尚未开立）
2. 所有经营收支通过公司账户进行
3. 区分个人消费与公司支出，避免混同

"""

        # 发票作废率
        if invoice_void_rate and invoice_void_rate.get("is_abnormal"):
            report += f"""## 🧾 发票作废率异常

本月发票作废率 {invoice_void_rate['rate_pct']}%，超过10%警戒线。
金税四期会触发发票行为分析，请确保每张作废发票有合理原因。

"""

        report += """## 💡 月度合规操作清单

- [ ] 核对开票内容与经营范围一致性
- [ ] 检查进项票是否全部归集
- [ ] 确认公转私记录有合理业务背景
- [ ] 比对发票流、资金流、合同流
- [ ] 检查是否有大额交易需报告

---
⚠️ **免责声明**：以上风险自查为基于账簿数据的自动分析，仅供参考。
正式合规判断请咨询专业税务顾问。
"""
        return report


# =============================================================================
# 报表生成器
# =============================================================================

class ReportGenerator:
    """财务报表生成器 — 利润表、资产负债表、现金流量表"""

    @staticmethod
    def profit_loss(entries: List[AccountEntry], year: int, month: int,
                    profile: CompanyProfile) -> str:
        """生成利润表"""
        engine = BookkeepingEngine()
        engine.entries = entries
        summary = engine.get_monthly_summary(year, month)

        is_individual = (profile.entity_type == BusinessEntityType.INDIVIDUAL_BUSINESS)

        # 计算所得税
        annual_revenue = engine.get_annual_revenue(year)
        if not is_individual:
            # 纳税调整
            adjust_result = TaxAdjuster.adjust_profit(
                summary["operating_profit"], entries, annual_revenue, year)
            tax_result = TaxEngine.calculate_cit(adjust_result["taxable_income"])
        else:
            adjust_result = None
            # 个体户使用经营所得个税（年度累计）
            cumulative_profit = summary["operating_profit"]
            for m in range(1, month):
                ms = engine.get_monthly_summary(year, m)
                cumulative_profit += ms["operating_profit"]
            tax_result = TaxEngine.calculate_pit_business(cumulative_profit)

        tax_amount = tax_result["effective_tax"]
        net_profit = summary["operating_profit"] - tax_amount

        gm = summary["gross_margin"]
        health = "✅ 健康" if gm >= Decimal("50") else ("⚠️ 关注" if gm >= Decimal("30") else "🔴 需改善")

        report = f"""# 📊 利润表

编制期间：{year}年{month}月  |  单位：元

| 项目 | 本期金额 |
|------|---------|
| 一、营业收入 | {fmt(summary['total_income'])} |
| 减：营业成本 | {fmt(summary['total_cost'])} |
| 二、毛利 | {fmt(summary['gross_profit'])} |
| 毛利率 | {gm}%（{health}） |
| 减：期间费用 | {fmt(summary['total_expense'])} |
| 其中：费用率 | {summary['expense_ratio']}% |
| 三、营业利润 | {fmt(summary['operating_profit'])} |
| ⚠️ 减：所得税费用 | {fmt(tax_amount)} |
| 四、净利润 ⚠️ | {fmt(net_profit)} |
"""

        # 纳税调整明细（仅有限公司）
        if adjust_result and adjust_result["adjustments"]:
            report += f"""
## 🔧 纳税调整明细

| 调整项目 | 发生额 | 可扣除 | 调增金额 | 规则 |
|----------|--------|--------|----------|------|
"""
            for adj in adjust_result["adjustments"]:
                report += f"| {adj['item']} | {fmt(adj['original'])} | {fmt(adj['deductible'])} | +{fmt(adj['adjustment'])} | {adj['rule']} |\n"

            report += f"""
| **合计** | | | **+{fmt(adjust_result['total_adjustment'])}** | |
| **会计利润** → **应纳税所得额** | | | {fmt(adjust_result['accounting_profit'])} → {fmt(adjust_result['taxable_income'])} | |
"""

        # 税务说明
        report += f"""
## 📋 所得税说明

{("⚠️ 此为非正式估算，正式申报请以税局核定为准。")}
- 适用政策：{tax_result['policy']}
- 法律依据：{tax_result.get('legal_basis', '')}
"""

        if not is_individual:
            div_tax = TaxEngine.calculate_dividend_tax(net_profit)
            report += f"""
## ⚠️ 分红个税提醒

如果你从公司分红（将净利润转到个人账户），还需缴纳 **20% 股息红利个人所得税**：
- 净利润：{fmt(div_tax['net_profit'])} 元
- 分红个税：{fmt(div_tax['dividend_tax'])} 元
- 到手金额：{fmt(div_tax['after_tax_dividend'])} 元
- {div_tax['note']}
"""

        # 费用明细
        if summary["expense_by_category"]:
            report += "\n## 📋 费用明细\n\n| 科目编码 | 科目名称 | 金额 |\n|---------|---------|------|\n"
            for code, amt in sorted(summary["expense_by_category"].items()):
                name = CHART_OF_ACCOUNTS.get(code, {}).get("name", code)
                report += f"| {code} | {name} | {fmt(amt)} |\n"

        report += """
---
⚠️ **免责声明**：以上为预估数据，正式申报请以税务机关核定为准。
"""
        return report

    @staticmethod
    def balance_sheet(entries: List[AccountEntry], profile: CompanyProfile,
                      year: int, month: int) -> str:
        """生成资产负债表"""
        engine = BookkeepingEngine()
        engine.entries = entries
        as_of = get_month_range(year, month)[1]

        ib = profile.initial_balances
        initial_cash = d(ib.get("1001", "0")) + d(ib.get("1002", "0"))
        initial_capital = d(ib.get("3001", "0"))
        initial_fixed = d(ib.get("1005", "0"))

        # 计算各科目余额（简化：汇总记账条目到 as_of）
        # 货币资金
        cash_inflow = Decimal("0")
        cash_outflow = Decimal("0")
        ar_total = Decimal("0")
        ap_total = Decimal("0")
        prepaid = Decimal("0")
        unearned = Decimal("0")
        tax_payable = Decimal("0")
        net_profit_accum = Decimal("0")

        for entry in entries:
            if entry.date > as_of:
                continue
            if entry.entry_type == EntryType.INCOME:
                if entry.payment_method in ("应收账款", "未收款"):
                    ar_total += entry.amount
                else:
                    cash_inflow += entry.amount
                net_profit_accum += entry.amount
            elif entry.entry_type == EntryType.EXPENSE:
                if entry.payment_method in ("应付账款", "未付款"):
                    ap_total += entry.amount
                else:
                    cash_outflow += entry.amount
                if entry.category_code.startswith("1005"):
                    pass  # 固定资产特殊处理
                else:
                    net_profit_accum -= entry.amount

        # 计算税金
        tax_payable = net_profit_accum * Decimal("0.05") if net_profit_accum > 0 else Decimal("0")

        cash_balance = initial_cash + cash_inflow - cash_outflow
        total_assets = cash_balance + ar_total + prepaid + initial_fixed
        total_liabilities = ap_total + unearned + tax_payable
        owner_equity = initial_capital + net_profit_accum - tax_payable
        total_equity_liab = total_liabilities + owner_equity

        balanced = abs(total_assets - total_equity_liab) < Decimal("0.02")

        report = f"""# 📊 资产负债表

编制日期：{as_of.isoformat()}  |  单位：元

## 资产

| 项目 | 金额 |
|------|------|
| 货币资金 | {fmt(cash_balance)} |
| 应收账款 | {fmt(ar_total)} |
| 预付账款 | {fmt(prepaid)} |
| 固定资产 | {fmt(initial_fixed)} |
| **资产总计** | **{fmt(total_assets)}** |

## 负债

| 项目 | 金额 |
|------|------|
| 应付账款 | {fmt(ap_total)} |
| 应交税费 | {fmt(tax_payable)} |
| 预收账款 | {fmt(unearned)} |
| **负债总计** | **{fmt(total_liabilities)}** |

## 所有者权益

| 项目 | 金额 |
|------|------|
| 实收资本 | {fmt(initial_capital)} |
| 未分配利润 | {fmt(net_profit_accum - tax_payable)} |
| **所有者权益总计** | **{fmt(owner_equity)}** |

## 平衡检查

资产总计 ({fmt(total_assets)}) = 负债总计 ({fmt(total_liabilities)}) + 所有者权益 ({fmt(owner_equity)}) = {fmt(total_equity_liab)}
{"✅ 平衡" if balanced else f"⚠️ 不平衡，差异: {fmt(total_assets - total_equity_liab)} 元，请检查记账"}

---
⚠️ **免责声明**：以上为预估数据，正式申报请以税务机关核定为准。
"""
        return report

    @staticmethod
    def cash_flow(entries: List[AccountEntry], year: int, month: int) -> str:
        """生成现金流量表"""
        start, end = get_month_range(year, month)
        op_inflow = Decimal("0")
        op_outflow = Decimal("0")
        inv_outflow = Decimal("0")
        fin_inflow = Decimal("0")

        for entry in entries:
            if not (start <= entry.date <= end):
                continue
            if entry.entry_type == EntryType.INCOME:
                if entry.payment_method not in ("应收账款", "未收款"):
                    op_inflow += entry.amount
                if entry.category_code == "3001":
                    fin_inflow += entry.amount
            elif entry.entry_type == EntryType.EXPENSE:
                if entry.category_code in ("1005",):
                    inv_outflow += entry.amount
                elif entry.payment_method not in ("应付账款", "未付款"):
                    op_outflow += entry.amount

        op_net = op_inflow - op_outflow
        inv_net = -inv_outflow
        fin_net = fin_inflow
        net_change = op_net + inv_net + fin_net

        report = f"""# 📊 现金流量表

编制期间：{year}年{month}月  |  单位：元

## 一、经营活动现金流

| 项目 | 金额 |
|------|------|
| 销售商品/提供劳务收到的现金 | {fmt(op_inflow)} |
| 购买商品/接受劳务支付的现金 | {fmt(op_outflow)} |
| **经营活动净现金流** | **{fmt(op_net)}** {'✅ 正值' if op_net >= 0 else '⚠️ 负值'} |

## 二、投资活动现金流

| 项目 | 金额 |
|------|------|
| 购置固定资产支付的现金 | {fmt(inv_outflow)} |
| **投资活动净现金流** | **{fmt(inv_net)}** |

## 三、筹资活动现金流

| 项目 | 金额 |
|------|------|
| 吸收投资收到的现金 | {fmt(fin_inflow)} |
| **筹资活动净现金流** | **{fmt(fin_net)}** |

## 本期现金净变动

**{fmt(net_change)}** 元

---
"""
        return report

    @staticmethod
    def tax_summary(entries: List[AccountEntry], year: int, month: int,
                    profile: CompanyProfile) -> str:
        """生成税务汇总报告"""
        engine = BookkeepingEngine()
        engine.entries = entries
        summary = engine.get_monthly_summary(year, month)
        is_individual = (profile.entity_type == BusinessEntityType.INDIVIDUAL_BUSINESS)

        # 增值税
        vat_result = TaxEngine.calculate_vat(summary["total_income"], profile.taxpayer_type,
                                               profile.filing_period)
        # 附加税
        additional = TaxEngine.calculate_additional_taxes(vat_result["vat_amount"],
                                                           profile.city_type, is_individual)
        # 所得税
        annual_revenue = engine.get_annual_revenue(year)
        if not is_individual:
            adjust_result = TaxAdjuster.adjust_profit(summary["operating_profit"], entries,
                                                        annual_revenue, year)
            income_tax_result = TaxEngine.calculate_cit(adjust_result["taxable_income"])
            income_tax_type = "企业所得税"
        else:
            adjust_result = None
            cumulative_profit = summary["operating_profit"]
            for m in range(1, month):
                cumulative_profit += engine.get_monthly_summary(year, m)["operating_profit"]
            income_tax_result = TaxEngine.calculate_pit_business(cumulative_profit)
            income_tax_type = "经营所得个税"

        total_tax = (vat_result["vat_amount"] + additional["total"] +
                     income_tax_result["effective_tax"])

        # 申报截止日
        today = date.today()
        next_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
        if profile.filing_period == "quarterly":
            # 季度申报：下一个季度
            q = (today.month - 1) // 3 + 1
            next_q = q + 1 if today.month > q * 3 else q
        deadline_day = next_month.replace(day=15) if next_month.day <= 15 else next_month
        try:
            vat_deadline = deadline_day
            vat_days = (vat_deadline - today).days
        except:
            vat_days = 999

        entity_label = profile.entity_type.value

        report = f"""# 💰 税务汇总报告

{year}年{month}月  |  主体类型：{entity_label}  |  纳税人类型：{profile.taxpayer_type.value}

## 本期应缴税费 ⚠️

| 税种 | 计税基础 | 税率 | 应纳税额 |
|------|---------|------|---------|
| 增值税 | {fmt(summary['total_income'])} | {vat_result['effective_rate']*100:.0f}% | {fmt(vat_result['vat_amount'])} |
| 城建税 | {fmt(vat_result['vat_amount'])} | {"3.5%" if is_individual else "7%"} | {fmt(additional['urban'])} |
| 教育费附加 | {fmt(vat_result['vat_amount'])} | {"1.5%" if is_individual else "3%"} | {fmt(additional['education'])} |
| 地方教育附加 | {fmt(vat_result['vat_amount'])} | {"1%" if is_individual else "2%"} | {fmt(additional['local_education'])} |
| {income_tax_type}(预缴) | {fmt(income_tax_result['taxable_income'])} | {income_tax_result['effective_rate']*100:.0f}% | {fmt(income_tax_result['effective_tax'])} |
| **合计** ⚠️ | | | **{fmt(total_tax)}** |
"""

        if vat_result["policy_applied"]:
            report += f"\n## 🎁 享受的税收优惠\n\n- ✅ {vat_result['policy_applied']}（{vat_result['legal_basis']}）\n"
            report += f"- ✅ {income_tax_result['policy']}（{income_tax_result.get('legal_basis', '')}）\n"
            if is_individual and income_tax_result.get("has_half_relief"):
                report += f"- ✅ 个体工商户减半征收（减免{fmt(income_tax_result['half_relief'])}元）\n"

        report += f"""
## 📅 申报提醒

| 项目 | 截止日期 |
|------|---------|
| 增值税 | {"月/季度终了后15日内" if vat_days > 365 else f"{vat_deadline.isoformat()}（{vat_days}天后）"} |

---
⚠️ **免责声明**：以上为预估数据，正式申报请以税务机关核定为准。
政策依据：财政部 税务总局公告2023年第19号、2023年第12号（有效期至2027-12-31）
"""
        return report

    @staticmethod
    def tax_calendar(profile: CompanyProfile, year: int) -> str:
        """生成税务日历"""
        report = f"""# 📅 {year}年税务日历

主体类型：{profile.entity_type.value}
申报方式：{'按季度' if profile.filing_period == 'quarterly' else '按月度'}

| 事项 | 频率 | 常规截止日 |
|------|------|-----------|
"""
        for item, info in TAX_CALENDAR.items():
            freq = info["freq"]
            deadline = info["deadline"]
            # 根据主体类型筛选
            if item == "经营所得个税" and profile.entity_type != BusinessEntityType.INDIVIDUAL_BUSINESS:
                continue
            if item == "企业所得税" and profile.entity_type == BusinessEntityType.INDIVIDUAL_BUSINESS:
                continue
            report += f"| {item} | {freq} | {deadline} |\n"

        report += f"""
## 📋 重点日期提醒

| 月份 | 事项 |
|------|------|
| 1月 | 工商年报开始（截止6月30日） |
| 3月 | {"经营所得个税汇算清缴截止（3月31日）" if profile.entity_type == BusinessEntityType.INDIVIDUAL_BUSINESS else ""} |
| 5月 | {"企业所得税汇算清缴截止（5月31日）" if profile.entity_type != BusinessEntityType.INDIVIDUAL_BUSINESS else ""} |

---
"""
        return report

    @staticmethod
    def ar_report(entries: List[AccountEntry]) -> str:
        """生成应收账款催款报告"""
        overdue = CashflowManager.check_ar_overdue(entries)
        if not overdue:
            return "# 📋 应收账款状态\n\n✅ 目前没有未收款项，所有应收账款均已回款。\n"

        report = """# 📋 应收账款催款清单

| 客户 | 金额 | 到期日 | 逾期天数 | 状态 |
|------|------|--------|----------|------|
"""
        for item in overdue:
            report += f"| {item['counterparty']} | {fmt(item['amount'])} | {item['due_date'].isoformat()} | {item['days_overdue']}天 | {item['severity']} |\n"

        total_ar = sum((item["amount"] for item in overdue), Decimal("0"))
        report += f"\n**应收账款合计：{fmt(total_ar)} 元**\n"
        report += "\n💡 建议按状态从高到低逐一联系客户催款。\n"
        return report

    @staticmethod
    def invoice_summary_report(invoice_mgr: "InvoiceManager",
                                entries: List[AccountEntry],
                                year: int, month: int) -> str:
        """生成发票管理汇总报告"""
        report = f"# 🧾 发票管理报告\n\n{year}年{month}月\n\n"

        # 未开票检查
        unbilled = invoice_mgr.check_unbilled_income(entries)
        if unbilled:
            report += "## ⚠️ 收入未开票提醒\n\n"
            for item in unbilled:
                report += f"- {item['severity']} {item['counterparty']} {fmt(item['amount'])}元 → 已收款{item['days_since']}天未开票\n"
            report += "\n"

        # 缺票检查
        missing = invoice_mgr.check_missing_receipt_invoices(entries)
        if missing:
            report += "## ⚠️ 缺收发票提醒\n\n"
            for item in missing:
                report += f"- {item['description']} {fmt(item['amount'])}元 → 支出{item['days_since']}天无票\n"
            report += "\n"

        # 无票支出占比
        unbilled_warn = invoice_mgr.check_unbilled_expense_ratio(entries, year, month)
        if unbilled_warn:
            report += f"""## 🔴 无票支出预警

本月无票支出 {fmt(unbilled_warn['unbilled_expense'])} 元，占总支出的 {unbilled_warn['ratio_pct']}%（超出30%安全线）
⚠️ 预估额外税务成本：约 {fmt(unbilled_warn['estimated_extra_tax'])} 元

"""

        # 发票作废率
        void_rate = invoice_mgr.get_invoice_void_rate(year, month)
        if void_rate:
            report += f"## 📊 发票统计\n\n本月开具发票 {void_rate['total']} 张，作废 {void_rate['voided']} 张，作废率 {void_rate['rate_pct']}%\n"
            if void_rate["is_abnormal"]:
                report += "⚠️ 作废率超过10%，金税四期可能触发预警\n"

        return report


# =============================================================================
# SoloFinanceGuard 主控器
# =============================================================================

class SoloFinanceGuard:
    """一人公司财务管家主控器 — 整合所有模块"""

    def __init__(self, user_id: str = "default",
                 data_dir: str = ".solo-finance-data"):
        self.user_id = user_id
        self.persistence = PersistenceManager(data_dir)
        self.profile: Optional[CompanyProfile] = None
        self.engine = BookkeepingEngine()
        self.invoice_mgr = InvoiceManager()
        self._loaded = False

    def init_profile(self, entity_type: BusinessEntityType,
                     name: str = "", tax_id: str = "",
                     city_type: str = "市区",
                     filing_period: str = "monthly",
                     initial_bank: Decimal = Decimal("0"),
                     initial_capital: Decimal = Decimal("0")) -> CompanyProfile:
        """初始化/更新公司档案"""
        self.profile = CompanyProfile(
            name=name,
            tax_id=tax_id,
            entity_type=entity_type,
            taxpayer_type=TaxpayerType.SMALL_SCALE,
            city_type=city_type,
            filing_period=filing_period,
            initial_balances={
                "1001": str(initial_bank),
                "3001": str(initial_capital)
            }
        )
        return self.profile

    def load(self) -> bool:
        """加载历史数据"""
        engine, invoice_mgr, profile = self.persistence.load(self.user_id)
        if profile is None:
            self._loaded = False
            return False
        self.profile = profile
        self.engine = engine or BookkeepingEngine()
        self.invoice_mgr = invoice_mgr or InvoiceManager()
        self._loaded = True
        return True

    def save(self) -> bool:
        """保存数据"""
        if self.profile is None:
            return False
        return self.persistence.save(self.engine, self.invoice_mgr, self.profile, self.user_id)

    def clear_all(self) -> bool:
        """清除所有数据"""
        self.engine.clear()
        self.invoice_mgr.invoices.clear()
        self.profile = None
        self._loaded = False
        return self.persistence.clear(self.user_id)

    @property
    def is_initialized(self) -> bool:
        return self._loaded and self.profile is not None

    @property
    def is_individual(self) -> bool:
        return (self.profile is not None and
                self.profile.entity_type == BusinessEntityType.INDIVIDUAL_BUSINESS)

    def process_nl_entry(self, text: str, entry_date: Optional[date] = None) -> str:
        """处理自然语言记账指令"""
        if entry_date is None:
            entry_date = date.today()

        parsed = parse_natural_language(text)
        if parsed is None:
            return f"❌ 无法解析指令。\n\n{get_format_hint()}"

        amount = parsed["amount"]
        valid, msg = validate_amount(amount)
        if not valid:
            return f"❌ {msg}"

        entry_type = parsed["entry_type"]
        description = parsed["description"]
        cat_code, cat_name = self.engine.smart_categorize(description, entry_type)

        # 公私分离检测
        warnings = []
        pm = parsed["payment_method"]
        if any(kw in pm for kw in ("个人微信", "个人支付宝", "个人卡")):
            warnings.append(
                "🚨 **公私分离警告**：通过个人账户收付公司款项违反《公司法》第23条第三款！"
                "\n一人公司股东若无法证明财产独立，将对公司债务承担连带责任。"
                "\n请开立对公账户并规范使用。"
            )

        # 应收账款：设置30天账期
        due_date = None
        if entry_type == EntryType.INCOME and pm in ("应收账款", "未收款"):
            due_date = entry_date + timedelta(days=30)

        entry = AccountEntry(
            date=entry_date,
            entry_type=entry_type,
            amount=amount,
            category_code=cat_code,
            category_name=cat_name,
            description=description,
            counterparty=parsed["counterparty"],
            payment_method=pm,
            is_deductible=CHART_OF_ACCOUNTS.get(cat_code, {}).get("deductible", True),
            due_date=due_date
        )

        success, msg = self.engine.add_entry(entry)
        if not success:
            return f"❌ {msg}"

        self.save()

        result = f"✅ {parsed['action']}记账成功！\n\n"
        result += f"  · 日期：{entry_date.isoformat()}\n"
        result += f"  · 金额：{fmt(amount)} 元\n"
        result += f"  · 科目：{cat_code} {cat_name}\n"
        result += f"  · 摘要：{description}\n"
        if parsed["counterparty"]:
            result += f"  · 对方：{parsed['counterparty']}\n"
        result += f"  · 付款方式：{pm}\n"
        if due_date:
            result += f"  · 账期到期日：{due_date.isoformat()}\n"

        if pm in ("应收账款", "未收款"):
            result += "\n💡 提示：请关注回款情况，到期后可查询「应收账款催款清单」\n"

        if warnings:
            result += "\n" + "\n".join(warnings)

        return result

    def get_invoice_alerts(self) -> str:
        """获取发票管理提醒"""
        alerts = []
        unbilled = self.invoice_mgr.check_unbilled_income(self.engine.entries)
        missing = self.invoice_mgr.check_missing_receipt_invoices(self.engine.entries)
        today = date.today()
        ratio_warn = self.invoice_mgr.check_unbilled_expense_ratio(
            self.engine.entries, today.year, today.month)

        parts = []
        if unbilled:
            parts.append("## ⚠️ 收入未开票提醒\n")
            for item in unbilled:
                parts.append(f"- {item['severity']} {item['counterparty']} {fmt(item['amount'])}元 → 已{item['days_since']}天未开票")
        if missing:
            parts.append("\n## ⚠️ 支出缺发票提醒\n")
            for item in missing:
                parts.append(f"- {item['description']} {fmt(item['amount'])}元 → {item['days_since']}天未取票")
        if ratio_warn:
            parts.append(f"\n## 🔴 无票支出预警\n本月无票支出占比 {ratio_warn['ratio_pct']}%，超安全线30%")

        return "\n".join(parts) if parts else "✅ 当前无发票相关提醒。"

    def get_cashflow_health(self, bank_balance: Decimal,
                            third_party_balance: Decimal = Decimal("0"),
                            avg_monthly_outflow: Decimal = Decimal("0")) -> str:
        """现金流健康度分析"""
        total_cash = bank_balance + third_party_balance

        # 从记账数据中计算应收账款
        ar_total = Decimal("0")
        ap_total = Decimal("0")
        for entry in self.engine.entries:
            if entry.entry_type == EntryType.INCOME and entry.payment_method in ("应收账款", "未收款"):
                ar_total += entry.amount
            if entry.entry_type == EntryType.EXPENSE and entry.payment_method in ("应付账款", "未付款"):
                ap_total += entry.amount

        if avg_monthly_outflow == Decimal("0"):
            # 估算月均支出
            today = date.today()
            total_exp = Decimal("0")
            months_with_data = set()
            for entry in self.engine.entries:
                if entry.entry_type == EntryType.EXPENSE:
                    total_exp += entry.amount
                    months_with_data.add((entry.date.year, entry.date.month))
            if months_with_data:
                avg_monthly_outflow = total_exp / Decimal(str(len(months_with_data)))
            else:
                avg_monthly_outflow = Decimal("10000")

        health = CashflowManager.analyze_cash_health(total_cash, avg_monthly_outflow, ar_total, ap_total)

        report = f"""# 💵 现金流仪表盘

## 当前可用资金

| 账户 | 余额 |
|------|------|
| 银行账户 | {fmt(bank_balance)} 元 |
| 第三方支付 | {fmt(third_party_balance)} 元 |
| **合计** | **{fmt(total_cash)} 元** |

## 📊 现金流健康度

- 现金储备：**{health['months_reserve']} 个月**
- 状态：{health['health_status']}
- 应收账款：{fmt(health['total_ar'])} 元
- 应付账款：{fmt(health['total_ap'])} 元

"""
        if health["health_level"] == RiskLevel.CRITICAL:
            report += f"""## 🚨 现金枯竭预警

⚠️ 现金储备仅够支撑 {health['months_reserve']} 个月！

**建议立即：**
1. 催收应收账款（当前应收 {fmt(ar_total)} 元）
2. 推迟非必要支出
3. 考虑融资或股东借款

"""
        return report

    def get_full_report(self, year: int, month: int) -> str:
        """获取完整月度财务报告"""
        if not self.is_initialized:
            return "⚠️ 请先完成初始化设置。"

        report = ReportGenerator.profit_loss(self.engine.entries, year, month, self.profile)
        report += "\n---\n"
        report += ReportGenerator.balance_sheet(self.engine.entries, self.profile, year, month)
        report += "\n---\n"
        report += ReportGenerator.cash_flow(self.engine.entries, year, month)
        return report

    def get_tax_report(self, year: int, month: int) -> str:
        """获取税务汇总报告"""
        if not self.is_initialized:
            return "⚠️ 请先完成初始化设置。"
        return ReportGenerator.tax_summary(self.engine.entries, year, month, self.profile)

    def get_risk_report(self, year: int, month: int) -> str:
        """获取金税四期风险自查报告"""
        inspection = GoldenTaxInspector.inspect(
            self.engine.entries, self.invoice_mgr.invoices, self.profile, year, month)
        void_rate = self.invoice_mgr.get_invoice_void_rate(year, month)
        return GoldenTaxInspector.generate_inspection_report(inspection, void_rate)

    def get_ar_report(self) -> str:
        """获取应收账款催款报告"""
        return ReportGenerator.ar_report(self.engine.entries)

    def get_tax_calendar(self, year: Optional[int] = None) -> str:
        """获取税务日历"""
        if year is None:
            year = date.today().year
        if not self.is_initialized:
            return "⚠️ 请先完成初始化设置。"
        return ReportGenerator.tax_calendar(self.profile, year)

    def get_invoice_report(self, year: int, month: int) -> str:
        """获取发票管理报告"""
        return ReportGenerator.invoice_summary_report(
            self.invoice_mgr, self.engine.entries, year, month)

    def export_entries_csv(self, filepath: str) -> str:
        """导出记账条目为 CSV"""
        import csv
        try:
            with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["日期", "类型", "金额", "科目编码", "科目名称",
                                 "摘要", "对方单位", "付款方式", "发票号", "可扣除"])
                for e in self.engine.entries:
                    writer.writerow([
                        e.date.isoformat(), e.entry_type.value, str(e.amount),
                        e.category_code, e.category_name, e.description,
                        e.counterparty, e.payment_method, e.invoice_no,
                        "是" if e.is_deductible else "否"
                    ])
            return f"✅ 已导出 {len(self.engine.entries)} 条记账记录到 {filepath}"
        except Exception as e:
            return f"❌ 导出失败：{e}"

    def profit_first_allocation(self, income_amount: Decimal) -> str:
        """
        Profit First 利润优先分配建议
        收入到账时自动分配：利润30% + 税费15% + 运营55%
        """
        profit = (income_amount * Decimal("0.30")).quantize(Decimal("0.01"))
        tax_reserve = (income_amount * Decimal("0.15")).quantize(Decimal("0.01"))
        operating = (income_amount * Decimal("0.55")).quantize(Decimal("0.01"))

        return f"""# 💰 Profit First 利润优先分配

收入 {fmt(income_amount)} 元，建议分配：

| 账户 | 比例 | 金额 | 用途 |
|------|------|------|------|
| 🏦 利润账户 | 30% | {fmt(profit)} | 创始人报酬，不动用 |
| 🏛️ 税务备用 | 15% | {fmt(tax_reserve)} | 增值税+所得税预留 |
| 💼 运营账户 | 55% | {fmt(operating)} | 日常运营支出 |

> 💡 Profit First 核心理念：先留存利润，再用剩余资金运营，避免「收入→先花→剩下才是利润」的陷阱。
"""


# =============================================================================
# 主程序入口 / 演示模式
# =============================================================================

def main():
    """演示模式 — 展示所有核心功能"""
    print("=" * 60)
    print("一人公司财务管家 / SoloFinance Guard v2.0")
    print("=" * 60)
    print()
    print("💰 核心功能模块：")
    print("  1. 智能记账  — 自然语言解析，自动归类")
    print("  2. 发票管理  — 开票/收票全流程智能提醒")
    print("  3. 税务计算  — 公司/个体户双模式，自动匹配优惠")
    print("  4. 纳税调整  — 招待费/广宣费/无票支出专项调整")
    print("  5. 财务报表  — 利润表/资产负债表/现金流量表")
    print("  6. 现金流管控 — 资金预警/应收账款催款")
    print("  7. 金税四期  — 动态数据驱动风险自查")
    print("  8. 数据持久化 — JSON 自动存储/加载")
    print("  9. 公私分离  — 《公司法》第23条合规提醒")
    print("  10. 税务日历 — 年度申报截止日提醒")
    print()
    print("💡 使用示例：")
    print('  · 记账："记收入 50000 来自XX科技 银行转账"')
    print('  · 问税："这个月收入8万，支出3万，要交多少税？"')
    print('  · 报表："生成上个月利润表"')
    print('  · 现金："我现在现金还够撑几个月？"')
    print('  · 风险："金税四期有什么需要注意的？"')
    print('  · 催款："帮我看看哪些客户还没付款"')
    print()
    print("📝 初始化时请选择主体类型：")
    print("  [1] 有限责任公司（一人公司）")
    print("  [2] 个体工商户")
    print()
    print("⚠️ 免责声明：所有税务计算仅供参考，正式申报请以税务机关核定为准。")

    # 快速演示
    print()
    print("-" * 60)
    print("🔬 功能演示：")
    print("-" * 60)

    # Demo: NLP 解析
    demo_texts = [
        "记收入 50000 来自XX科技 银行转账",
        "记支出 8000 购买阿里云服务器 支付宝",
        "记报销 1500 去北京拜访客户差旅",
    ]
    print("\n📝 自然语言解析演示：")
    for txt in demo_texts:
        parsed = parse_natural_language(txt)
        if parsed:
            print(f"  输入：「{txt}」")
            print(f"  解析：金额={fmt(parsed['amount'])}元, "
                  f"对方={parsed.get('counterparty', '-')}, "
                  f"付款={parsed['payment_method']}, "
                  f"摘要={parsed['description']}")
        else:
            print(f"  输入：「{txt}」→ ❌ 解析失败")

    # Demo: Tax calculation
    print("\n💰 税务计算演示（有限责任公司，月收入80,000元）：")
    vat = TaxEngine.calculate_vat(Decimal("80000"), TaxpayerType.SMALL_SCALE)
    print(f"  增值税：{fmt(vat['vat_amount'])} 元（{vat['policy_applied']}）")
    additional = TaxEngine.calculate_additional_taxes(vat["vat_amount"], "市区")
    print(f"  附加税：{fmt(additional['total'])} 元")
    cit = TaxEngine.calculate_cit(Decimal("50000"))
    print(f"  企业所得税：{fmt(cit['effective_tax'])} 元（{cit['policy']}）")

    print("\n💰 税务计算演示（个体工商户，年度应税所得 150,000元）：")
    pit = TaxEngine.calculate_pit_business(Decimal("150000"))
    print(f"  经营所得个税：{fmt(pit['effective_tax'])} 元（{pit['policy']}）")
    print(f"  减免金额：{fmt(pit['half_relief'])} 元")

    # Demo: Amount parsing
    print("\n🔢 金额解析演示：")
    for test in ["50000", "5万", "50000元", "5万元", "1.5万"]:
        amt = parse_amount(test)
        print(f"  「{test}」→ {fmt(amt) if amt else '解析失败'}")

    print()
    print("-" * 60)
    print("✅ v2.0 升级完毕。P0/P1/P2 全部功能就绪。")


if __name__ == "__main__":
    main()

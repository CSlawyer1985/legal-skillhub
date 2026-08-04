"""发票经济风控 · 风险计算引擎

负责：解析指标定义、执行 15 项指标算法、返回结构化计算结果。
纯标准库，无外部依赖；企业名称/税号应在调用前完成脱敏。
"""
import csv
import json
import os
from .indicators import compute_all, INDICATORS, INDICATOR_MAP, MAX_WEIGHT


class RiskEngine:
    """风控引擎：加载指标并批量计算"""

    def __init__(self):
        self.indicators = INDICATORS
        self.indicator_map = INDICATOR_MAP

    def calculate(self, invoices, context=None):
        """执行全部指标计算

        :param invoices: list[dict] 发票数据，字段见 indicators.py 注释
        :param context: dict 企业上下文（销售额/税负/行业/关联交易等）
        :return: list[dict] 每项指标的计算结果
        """
        context = context or {}
        return compute_all(invoices, context)

    @staticmethod
    def load_invoices(path):
        """从 CSV / JSON 加载发票数据（自动识别扩展名）"""
        path = os.path.expanduser(path)
        if path.lower().endswith(".json"):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return data.get("invoices", data) if isinstance(data, dict) else data
        # 默认 CSV
        with open(path, encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))

    @staticmethod
    def normalize_invoice(row):
        """将原始记录标准化为引擎所需字段（容错转换）"""
        def num(v):
            try:
                return float(v)
            except (TypeError, ValueError):
                return 0.0
        return {
            "id": row.get("id") or row.get("发票号") or "",
            "amount": num(row.get("amount") or row.get("金额") or 0),
            "item": row.get("item") or row.get("品名") or row.get("货物名称") or "",
            "type": row.get("type") or row.get("类型") or ("销项" if str(row.get("方向", "")).find("销") >= 0 else "进项"),
            "is_red": str(row.get("is_red") or row.get("红冲") or "").lower() in ("1", "true", "yes", "是"),
            "is_void": str(row.get("is_void") or row.get("作废") or "").lower() in ("1", "true", "yes", "是"),
            "tax_rate": num(row.get("tax_rate") or row.get("税率") or 0),
            "buyer": row.get("buyer") or row.get("购方") or row.get("客户") or "",
            "seller": row.get("seller") or row.get("销方") or row.get("供应商") or "",
            "date": row.get("date") or row.get("日期") or "",
        }

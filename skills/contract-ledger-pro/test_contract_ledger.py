"""
合同台账管理系统 - 测试用例
"""
import unittest
import sys
import json
import tempfile
import os
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from token_validation import validate_token, get_tier_limits, _infer_tier
from pdf_parser import (
    extract_contract_fields, extract_amount, extract_date,
    normalize_date, extract_counterparty, determine_status
)
from storage import (
    init_storage, add_contract, get_contracts, get_contract,
    update_contract, delete_contract, add_reminder, count_contracts,
    get_expiring_contracts, export_contracts, LEDGER_FILE
)
from feishu_notifier import build_reminder_card, format_reminder_message


class TestTokenValidation(unittest.TestCase):
    """Token 验证测试"""

    def test_infer_tier_free(self):
        self.assertEqual(_infer_tier(""), "FREE")
        self.assertEqual(_infer_tier("invalid"), "FREE")

    def test_infer_tier_pro(self):
        self.assertEqual(_infer_tier("CONTRACT-LGR-PRO-xxxx"), "PRO")

    def test_infer_tier_bsc(self):
        self.assertEqual(_infer_tier("CONTRACT-LGR-BSC-xxxx"), "BSC")

    def test_infer_tier_ent(self):
        self.assertEqual(_infer_tier("CONTRACT-LGR-ENT-xxxx"), "ENT")

    def test_get_tier_limits(self):
        free = get_tier_limits("FREE")
        self.assertEqual(free["max_contracts"], 5)
        self.assertEqual(free["max_reminders"], 1)
        self.assertIn("csv", free["export_formats"])

        pro = get_tier_limits("PRO")
        self.assertEqual(pro["max_contracts"], 300)
        self.assertIn("xlsx", pro["export_formats"])

        ent = get_tier_limits("ENT")
        self.assertEqual(ent["max_contracts"], float("inf"))


class TestPdfParser(unittest.TestCase):
    """PDF 解析测试"""

    def test_extract_amount(self):
        text = "合同金额：100,000.00 元"
        self.assertEqual(extract_amount(text), 100000.0)

        text = "总价为¥50,000"
        self.assertEqual(extract_amount(text), 50000.0)

        text = "无金额条款"
        self.assertIsNone(extract_amount(text))

    def test_normalize_date(self):
        self.assertEqual(normalize_date("2024-01-15"), "2024-01-15")
        self.assertEqual(normalize_date("2024年1月15日"), "2024-01-15")
        self.assertEqual(normalize_date("2024/02/20"), "2024-02-20")

    def test_extract_date(self):
        text = "签订日期：2024年6月1日"
        self.assertEqual(extract_date(text, ["签订日期"]), "2024-06-01")

        text = "签署日期：2024-12-25"
        self.assertEqual(extract_date(text, ["签署日期"]), "2024-12-25")

    def test_extract_counterparty(self):
        text = "乙方：北京科技有限公司"
        self.assertEqual(extract_counterparty(text), "北京科技有限公司")

        text = "对方：上海 xyz 公司"
        self.assertEqual(extract_counterparty(text), "上海")

    def test_determine_status(self):
        from datetime import datetime, timedelta
        past = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        future = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        self.assertEqual(determine_status(past), "已到期")
        self.assertEqual(determine_status(future), "执行中")
        self.assertEqual(determine_status(None), "执行中")

    def test_extract_contract_fields(self):
        text = """
        软件开发合同

        甲方：阿里巴巴（中国）有限公司
        乙方：北京科技有限公司

        签订日期：2024年3月15日
        生效日期：2024年4月1日
        终止日期：2025年3月31日

        合同金额：500,000.00 元

        付款方式：签订后支付 30%，交付后支付 70%
        """
        fields = extract_contract_fields(text, "dev_contract.pdf")

        self.assertEqual(fields["counterparty"], "北京科技有限公司")
        self.assertEqual(fields["amount"], 500000.0)
        self.assertIn("2024", fields["sign_date"])
        self.assertIn("2025", fields["end_date"])
        self.assertEqual(fields["status"], "已到期")


class TestStorage(unittest.TestCase):
    """存储测试"""

    def setUp(self):
        # Use temp file for testing
        import storage
        self.temp_dir = tempfile.mkdtemp()
        storage.STORAGE_DIR = Path(self.temp_dir)
        storage.LEDGER_FILE = storage.STORAGE_DIR / "test_contracts.json"
        init_storage()

    def tearDown(self):
        if LEDGER_FILE.exists():
            os.remove(LEDGER_FILE)

    def test_add_contract(self):
        fields = {
            "contract_name": "测试合同",
            "amount": 10000.0,
            "counterparty": "测试公司",
            "end_date": "2025-12-31",
            "status": "执行中"
        }
        contract = add_contract(fields)
        self.assertIn("id", contract)
        self.assertEqual(contract["contract_name"], "测试合同")
        self.assertEqual(contract["amount"], 10000.0)

    def test_get_contracts(self):
        add_contract({"contract_name": "合同A", "amount": 1000, "end_date": "2025-01-01", "status": "执行中"})
        add_contract({"contract_name": "合同B", "amount": 2000, "end_date": "2025-06-01", "status": "执行中"})
        add_contract({"contract_name": "合同C", "amount": 3000, "end_date": "2024-01-01", "status": "已到期"})

        all_contracts = get_contracts()
        self.assertEqual(len(all_contracts), 3)

        active = get_contracts(status="执行中")
        self.assertEqual(len(active), 2)

        expired = get_contracts(status="已到期")
        self.assertEqual(len(expired), 1)

    def test_update_contract(self):
        contract = add_contract({"contract_name": "原始名称", "amount": 1000})
        result = update_contract(contract["id"], {"contract_name": "新名称", "amount": 2000})
        self.assertEqual(result["contract_name"], "新名称")
        self.assertEqual(result["amount"], 2000)

    def test_delete_contract(self):
        contract = add_contract({"contract_name": "待删除"})
        self.assertTrue(delete_contract(contract["id"]))
        self.assertIsNone(get_contract(contract["id"]))

    def test_reminder(self):
        contract = add_contract({"contract_name": "测试合同", "end_date": "2025-12-31"})
        self.assertTrue(add_reminder(contract["id"], 7))
        self.assertTrue(add_reminder(contract["id"], 30))

        updated = get_contract(contract["id"])
        self.assertEqual(len(updated["reminders"]), 2)

    def test_count_contracts(self):
        self.assertEqual(count_contracts(), 0)
        add_contract({"contract_name": "合同1", "end_date": "2025-01-01"})
        self.assertEqual(count_contracts(), 1)

    def test_export_csv(self):
        add_contract({"contract_name": "合同A", "amount": 1000, "end_date": "2025-01-01", "counterparty": "公司A"})
        add_contract({"contract_name": "合同B", "amount": 2000, "end_date": "2025-06-01", "counterparty": "公司B"})

        csv = export_contracts(get_contracts(), "csv")
        self.assertIn("合同A", csv)
        self.assertIn("合同B", csv)
        self.assertIn("1000", csv)
        self.assertIn("2000", csv)


class TestFeishuNotifier(unittest.TestCase):
    """飞书通知测试"""

    def test_build_reminder_card(self):
        contract = {
            "contract_name": "测试合同",
            "counterparty": "测试公司",
            "end_date": "2025-06-15",
            "amount": 50000.0
        }
        card = build_reminder_card(contract, 7)

        self.assertIn("elements", card)
        self.assertIn("header", card)
        self.assertEqual(card["header"]["template"], "orange")

    def test_format_reminder_message(self):
        contract = {
            "contract_name": "测试合同",
            "counterparty": "测试公司",
            "end_date": "2025-06-15",
            "amount": 50000.0
        }
        msg = format_reminder_message(contract, 7)

        self.assertIn("测试合同", msg)
        self.assertIn("测试公司", msg)
        self.assertIn("7 天", msg)


if __name__ == "__main__":
    unittest.main()

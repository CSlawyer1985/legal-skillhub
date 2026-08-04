#!/usr/bin/env python3

import argparse
import json
import unittest
from datetime import date
from decimal import Decimal

from labor_claim_calculator import (
    arrears,
    compensation,
    guide,
    overtime,
    rate_based,
    segmented_compensation,
    service_months,
    statutory_years,
)


class CalculatorTests(unittest.TestCase):
    def test_service_months_same_day(self):
        self.assertEqual(service_months(date(2026, 8, 1), date(2026, 8, 1)), 1)

    def test_end_before_start_rejected_with_fix(self):
        with self.assertRaisesRegex(ValueError, "请检查是否填反"):
            service_months(date(2026, 8, 2), date(2026, 8, 1))

    def test_less_than_half_year_model(self):
        self.assertEqual(statutory_years(17), Decimal("1.5"))

    def test_exact_half_year_rounds_to_one(self):
        self.assertEqual(statutory_years(18), Decimal("2"))

    def test_over_half_year_rounds_to_one(self):
        self.assertEqual(statutory_years(19), Decimal("2"))

    def test_unlawful_multiplier(self):
        args = argparse.Namespace(
            start=date(2023, 8, 1), end=date(2026, 7, 31),
            monthly_wage=Decimal("8000"), mode="unlawful",
            local_monthly_cap=None, max_years=None,
        )
        result = compensation(args)
        self.assertEqual(result["multiplier"], "2")
        self.assertEqual(result["status"], "success")
        self.assertIn("不得仅凭", result["warnings"][0])

    def test_user_supplied_cap(self):
        args = argparse.Namespace(
            start=date(2025, 1, 1), end=date(2026, 1, 1),
            monthly_wage=Decimal("50000"), mode="economic",
            local_monthly_cap=Decimal("30000"), max_years=12,
        )
        result = compensation(args)
        self.assertEqual(result["monthly_wage_used"], "30000.00")
        self.assertTrue(any("封顶" in warning for warning in result["warnings"]))

    def test_segmented_compensation(self):
        segments = [
            {"label": "前段", "start": "2005-01-01", "end": "2007-12-31", "monthly_wage": 8000, "multiplier": 1},
            {"label": "后段", "start": "2008-01-01", "end": "2020-12-31", "monthly_wage": 10000, "multiplier": 1, "max_years": 12},
        ]
        result = segmented_compensation(argparse.Namespace(segments_json=json.dumps(segments, ensure_ascii=False)))
        self.assertEqual(len(result["segments"]), 2)
        self.assertEqual(result["status"], "success")
        self.assertTrue(Decimal(result["estimated_amount"]) > 0)

    def test_segment_overlap_rejected(self):
        segments = [
            {"label": "A", "start": "2020-01-01", "end": "2021-01-01", "monthly_wage": 8000, "multiplier": 1},
            {"label": "B", "start": "2021-01-01", "end": "2022-01-01", "monthly_wage": 9000, "multiplier": 1},
        ]
        with self.assertRaisesRegex(ValueError, "重叠"):
            segmented_compensation(argparse.Namespace(segments_json=json.dumps(segments)))

    def test_bad_segment_json_gives_location(self):
        with self.assertRaisesRegex(ValueError, "错误位置"):
            segmented_compensation(argparse.Namespace(segments_json="[{bad}]"))

    def test_wage_arrears(self):
        result = arrears(argparse.Namespace(monthly_wage=Decimal("8000"), months=2, already_paid=Decimal("1000")))
        self.assertEqual(result["estimated_amount"], "15000.00")
        self.assertTrue(result["next_steps"])

    def test_paid_more_than_due_gives_fix(self):
        with self.assertRaisesRegex(ValueError, "请核对月数"):
            arrears(argparse.Namespace(monthly_wage=Decimal("8000"), months=1, already_paid=Decimal("9000")))

    def test_overtime_breakdown(self):
        args = argparse.Namespace(
            hourly_base=Decimal("50"), weekday_hours=Decimal("10"), weekday_multiplier=Decimal("1.5"),
            rest_hours=Decimal("8"), rest_multiplier=Decimal("2"), holiday_hours=Decimal("0"),
            holiday_multiplier=Decimal("3"), already_paid=Decimal("0"),
        )
        result = overtime(args)
        self.assertEqual(result["estimated_amount"], "1550.00")
        self.assertEqual(result["breakdown"]["weekday"], "750.00")

    def test_sick_leave_rate_model(self):
        args = argparse.Namespace(command="sick-leave", daily_base=Decimal("300"), days=5, rate=Decimal("0.8"), already_paid=Decimal("0"))
        result = rate_based(args)
        self.assertEqual(result["estimated_amount"], "1200.00")
        self.assertIn("所在地", result["warnings"][0])

    def test_annual_leave_rate_model(self):
        args = argparse.Namespace(command="annual-leave", daily_base=Decimal("368"), days=5, rate=Decimal("2"), already_paid=Decimal("0"))
        result = rate_based(args)
        self.assertEqual(result["estimated_amount"], "3680.00")

    def test_guide_is_human_friendly(self):
        result = guide(argparse.Namespace())
        self.assertIn("对话中直接说", result["how_to_use"])
        self.assertGreaterEqual(len(result["choose_one"]), 6)
        self.assertTrue(result["segmented_example"])


if __name__ == "__main__":
    unittest.main()

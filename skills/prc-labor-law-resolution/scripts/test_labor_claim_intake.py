#!/usr/bin/env python3

import unittest

from labor_claim_intake import build_intake, detect_scenario, detect_scenarios, normalize_payload


class IntakeTests(unittest.TestCase):
    def test_zero_parameter_intake(self):
        result = build_intake({"text": ""})
        self.assertEqual(result["scenario"], "general")
        self.assertEqual(result["status"], "needs_information")
        self.assertTrue(result["copyable_form"])

    def test_segmented_compensation_detected(self):
        scenario, reason = detect_scenario({"text": "我2005年入职，2026年被辞退，2008年前工龄怎么分段"})
        self.assertEqual(scenario, "compensation")
        self.assertIn("2008", reason[0])

    def test_overtime_detected(self):
        result = build_intake({"text": "公司周末加班不给加班费", "work_location": "上海"})
        self.assertEqual(result["scenario"], "overtime")
        self.assertIn("work_location", result["recognized"])

    def test_sick_leave_detected(self):
        result = build_intake({"text": "请问病假工资怎么算"})
        self.assertEqual(result["scenario"], "sick_leave")
        self.assertTrue(any(item["field"] == "rate" for item in result["missing_information"]))

    def test_explicit_scenario(self):
        scenario, reason = detect_scenario({"scenario": "annual_leave", "text": "帮我算"})
        self.assertEqual(scenario, "annual_leave")
        self.assertEqual(reason, ["用户明确指定场景"])

    def test_unknown_scenario_is_actionable(self):
        with self.assertRaisesRegex(ValueError, "删除scenario字段"):
            detect_scenario({"scenario": "unknown"})

    def test_invalid_json_is_actionable(self):
        with self.assertRaisesRegex(ValueError, "改用 --text"):
            normalize_payload(None, "[{bad}]")

    def test_complete_payload_ready(self):
        payload = {
            "scenario": "wage_arrears",
            "work_location": "深圳",
            "period": "2026-06至2026-07",
            "monthly_wage": 8000,
            "already_paid": 0,
            "evidence": ["合同", "流水"],
        }
        result = build_intake(payload)
        self.assertEqual(result["status"], "ready")
        self.assertFalse(result["missing_information"])

    def test_plain_language_optimization_detected(self):
        result = build_intake({"text": "公司要求一人多岗，做不了多能工就优化"})
        self.assertEqual(result["scenario"], "compensation")
        self.assertTrue(any("多能工" in reason for reason in result["detection_reason"]))

    def test_multiple_disputes_are_preserved(self):
        detected = detect_scenarios({"text": "公司辞退我，还欠工资并且周末加班不给钱"})
        keys = [item[0] for item in detected]
        self.assertIn("compensation", keys)
        self.assertIn("wage_arrears", keys)
        self.assertIn("overtime", keys)
        result = build_intake({"text": "公司辞退我，还欠工资并且周末加班不给钱"})
        self.assertGreaterEqual(len(result["all_detected_scenarios"]), 3)

    def test_offline_fallback_is_actionable(self):
        result = build_intake({"text": "深圳病假工资怎么算，网站打不开"})
        self.assertIn("step_3", result["offline_fallback"])
        self.assertIn("12333", result["offline_fallback"]["step_3"])

    def test_missing_field_has_fallback(self):
        result = build_intake({"text": "老板让我明天不用上班"})
        self.assertTrue(result["missing_information"])
        self.assertTrue(all(item.get("fallback") for item in result["missing_information"]))

    def test_work_injury_has_full_stage_inputs(self):
        result = build_intake({"text": "我在工作中骨折，公司不申报工伤"})
        self.assertEqual(result["scenario"], "work_injury")
        fields = {item["field"] for item in result["missing_information"]}
        self.assertIn("accident_context", fields)
        self.assertIn("insurance_status", fields)
        self.assertIn("current_treatment_and_pay", fields)
        self.assertTrue(any("申请" in action for action in result["what_can_be_done_now"]))

    def test_dispatch_is_independent_scenario(self):
        result = build_intake({"text": "我是派遣工，被用工单位退回后派遣公司要解除"})
        keys = [item["scenario"] for item in result["all_detected_scenarios"]]
        self.assertIn("dispatch", keys)
        self.assertTrue(any("退回不等于" in action for action in result["what_can_be_done_now"]))

    def test_dispatch_injury_preserves_both_scenarios(self):
        result = build_intake({"text": "派遣工在用工单位工作中受伤，两家公司互相推责"})
        keys = [item["scenario"] for item in result["all_detected_scenarios"]]
        self.assertIn("dispatch", keys)
        self.assertIn("work_injury", keys)
        fields = {item["field"] for item in result["missing_information"]}
        self.assertIn("dispatch_company", fields)
        self.assertIn("accident_date", fields)

    def test_novel_issue_checklist_has_eight_dimensions(self):
        result = build_intake({"text": "公司用AI评分扣掉我的奖金，这合法吗"})
        self.assertEqual(len(result["novel_issue_checklist"]), 8)
        joined = " ".join(result["novel_issue_checklist"])
        for keyword in ("主体", "期限", "要件", "证据", "渠道", "金额", "抗辩", "衔接"):
            self.assertIn(keyword, joined)

    def test_work_injury_red_flags_are_specific(self):
        result = build_intake({"text": "去年工作中受伤，公司一直说会处理"})
        self.assertTrue(any("期限" in item for item in result["scenario_red_flags"]))
        self.assertTrue(any("否认" in item or "关系" in item for item in result["scenario_red_flags"]))


if __name__ == "__main__":
    unittest.main()

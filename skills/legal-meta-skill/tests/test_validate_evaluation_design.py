"""法律能力合成评测文件的静态校验回归测试。"""

from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from scripts.validate_legal_skill import validate_evaluation_design


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


class ValidateEvaluationDesignTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertions = json.loads(
            (PACKAGE_ROOT / "evals/output_assertions.json").read_text(encoding="utf-8")
        )
        self.cases = json.loads(
            (PACKAGE_ROOT / "evals/universal_legal_cases.json").read_text(
                encoding="utf-8"
            )
        )

    def validate(self, assertions: dict, cases: dict) -> list[str]:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        skill_dir = Path(temporary_directory.name)
        eval_dir = skill_dir / "evals"
        eval_dir.mkdir()
        (eval_dir / "output_assertions.json").write_text(
            json.dumps(assertions, ensure_ascii=False), encoding="utf-8"
        )
        (eval_dir / "universal_legal_cases.json").write_text(
            json.dumps(cases, ensure_ascii=False), encoding="utf-8"
        )
        return validate_evaluation_design(skill_dir)

    def test_packaged_evaluation_design_passes(self) -> None:
        self.assertEqual(self.validate(self.assertions, self.cases), [])

    def test_duplicate_assertion_id_fails(self) -> None:
        assertions = deepcopy(self.assertions)
        assertions["assertions"].append(deepcopy(assertions["assertions"][0]))

        errors = self.validate(assertions, self.cases)

        self.assertIn("输出断言 id 重复", " ".join(errors))

    def test_unknown_assertion_reference_fails(self) -> None:
        cases = deepcopy(self.cases)
        cases["cases"][0]["assertion_ids"].append("unknown-assertion")

        errors = self.validate(self.assertions, cases)

        self.assertIn("引用了未知断言", " ".join(errors))

    def test_unreferenced_assertion_fails(self) -> None:
        cases = deepcopy(self.cases)
        assertion_id = self.assertions["assertions"][0]["id"]
        for case in cases["cases"]:
            case["assertion_ids"] = [
                item for item in case["assertion_ids"] if item != assertion_id
            ]

        errors = self.validate(self.assertions, cases)

        self.assertIn("未覆盖输出断言", " ".join(errors))

    def test_incomplete_module_partition_fails(self) -> None:
        cases = deepcopy(self.cases)
        cases["cases"][0]["expected_modules"]["active"].pop()

        errors = self.validate(self.assertions, cases)

        self.assertIn("未记录模块状态", " ".join(errors))

    def test_not_applicable_without_reason_fails(self) -> None:
        cases = deepcopy(self.cases)
        case = next(
            item
            for item in cases["cases"]
            if item["expected_modules"]["not_applicable"]
        )
        module_id = case["expected_modules"]["not_applicable"][0]
        del case["status_reasons"][module_id]

        errors = self.validate(self.assertions, cases)

        self.assertIn("不适用模块", " ".join(errors))

    def test_not_applicable_with_placeholder_reason_fails(self) -> None:
        cases = deepcopy(self.cases)
        case = next(
            item
            for item in cases["cases"]
            if item["expected_modules"]["not_applicable"]
        )
        module_id = case["expected_modules"]["not_applicable"][0]
        case["status_reasons"][module_id] = "略。"

        errors = self.validate(self.assertions, cases)

        self.assertIn("不适用模块", " ".join(errors))

    def test_blocked_without_gap_and_fallback_fails(self) -> None:
        cases = deepcopy(self.cases)
        case = cases["cases"][0]
        module_id = case["expected_modules"]["active"].pop()
        case["expected_modules"]["blocked"].append(module_id)
        case["status_reasons"][module_id] = {
            "gap": "缺少资料",
            "fallback": "停止结论",
        }

        errors = self.validate(self.assertions, cases)

        self.assertIn("human_owner", " ".join(errors))

    def test_blocked_with_governance_boundary_passes(self) -> None:
        cases = deepcopy(self.cases)
        case = cases["cases"][0]
        module_id = case["expected_modules"]["active"].pop()
        case["expected_modules"]["blocked"].append(module_id)
        case["status_reasons"][module_id] = {
            "gap": "缺少经核验的主体授权文件",
            "fallback": "停止授权结论并请求补充材料",
            "human_owner": "承办律师",
            "review_trigger": "收到有效授权文件后重新核验",
        }

        errors = self.validate(self.assertions, cases)

        self.assertNotIn("受阻模块", " ".join(errors))

    def test_fewer_than_seven_cases_fails(self) -> None:
        cases = deepcopy(self.cases)
        cases["cases"] = cases["cases"][:6]

        errors = self.validate(self.assertions, cases)

        self.assertIn("至少需要七类", " ".join(errors))

    def test_missing_lightweight_conditional_case_fails(self) -> None:
        cases = deepcopy(self.cases)
        for case in cases["cases"]:
            not_applicable = case["expected_modules"]["not_applicable"]
            if len(not_applicable) >= 5:
                module_id = not_applicable.pop()
                case["expected_modules"]["active"].append(module_id)
                del case["status_reasons"][module_id]

        errors = self.validate(self.assertions, cases)

        self.assertIn("轻量条件展开", " ".join(errors))

    def test_one_off_claim_explanation_remains_near_neighbor(self) -> None:
        trigger_document = json.loads(
            (PACKAGE_ROOT / "evals/trigger_cases.json").read_text(encoding="utf-8")
        )
        case = next(
            item
            for item in trigger_document["cases"]
            if item["id"] == "explain-claim-elements"
        )

        self.assertEqual(case["kind"], "near-neighbor")
        self.assertIn("不创建或修改 Skill", case["prompt"])


if __name__ == "__main__":
    unittest.main()

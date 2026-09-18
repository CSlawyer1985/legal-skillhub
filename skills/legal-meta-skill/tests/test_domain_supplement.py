"""intake 第 3 层领域问答记录（domain_supplement）的对抗测试。"""

from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from scripts.create_legal_skill import create_skill, validate_intake
from scripts.validate_legal_skill import check


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_INTAKE = PACKAGE_ROOT / "tests" / "fixtures" / "golden-contract-review-intake.json"


class DomainSupplementTests(unittest.TestCase):
    def setUp(self) -> None:
        self.intake = json.loads(GOLDEN_INTAKE.read_text(encoding="utf-8"))

    def supplement_errors(self, supplement: object) -> list[str]:
        intake = deepcopy(self.intake)
        intake["domain_supplement"] = supplement
        return [error for error in validate_intake(intake) if "domain_supplement" in error]

    def valid_item(self, source: str) -> dict:
        return {
            "builtin-archetype": {
                "question": "该采购合同是否涉及框架协议下的长期订单安排？",
                "answer": "涉及年度框架协议加单笔订单，审查需同时核对协议与订单的一致性",
                "question_source": source,
            },
            "user-provided": {
                "question": "供应商是否接受我方标准违约责任上限？",
                "answer": "供应商历史谈判中接受过合同金额百分之二十的责任上限",
                "question_source": source,
            },
            "authorized-research": {
                "question": "设备采购是否需要核验强制产品认证？",
                "answer": "涉及目录内设备须核验强制性产品认证证书并在合同中约定交付凭证",
                "question_source": source,
            },
        }[source]

    def test_missing_field_and_empty_array_pass(self) -> None:
        self.assertEqual(validate_intake(self.intake), [])

        intake = deepcopy(self.intake)
        intake["domain_supplement"] = []

        self.assertEqual(validate_intake(intake), [])

    def test_each_legal_source_passes(self) -> None:
        intake = deepcopy(self.intake)
        intake["domain_supplement"] = [
            self.valid_item("builtin-archetype"),
            self.valid_item("user-provided"),
            self.valid_item("authorized-research"),
        ]

        self.assertEqual(validate_intake(intake), [])

    def test_non_array_is_rejected(self) -> None:
        errors = self.supplement_errors({"question": "不是数组"})

        self.assertIn("必须为对象数组", " ".join(errors))

    def test_non_object_element_is_rejected(self) -> None:
        errors = self.supplement_errors(["不是对象"])

        self.assertIn("必须为对象", " ".join(errors))

    def test_missing_keys_are_rejected(self) -> None:
        item = self.valid_item("user-provided")
        item.pop("question_source")

        errors = self.supplement_errors([item])

        self.assertIn("缺少 question、answer 或 question_source", " ".join(errors))

    def test_empty_question_is_rejected(self) -> None:
        item = self.valid_item("user-provided")
        item["question"] = "  "

        errors = self.supplement_errors([item])

        self.assertIn("question 不能为空", " ".join(errors))

    def test_vague_answer_is_rejected(self) -> None:
        for vague in ("略", "按需"):
            with self.subTest(vague=vague):
                item = self.valid_item("user-provided")
                item["answer"] = vague

                errors = self.supplement_errors([item])

                self.assertIn("answer 不具体", " ".join(errors))

    def test_placeholder_answer_is_rejected(self) -> None:
        item = self.valid_item("user-provided")
        item["answer"] = "【填写实质回答】"

        errors = self.supplement_errors([item])

        self.assertIn("answer 不具体", " ".join(errors))

    def test_illegal_question_source_is_rejected(self) -> None:
        item = self.valid_item("user-provided")
        item["question_source"] = "web-search"

        errors = self.supplement_errors([item])

        self.assertIn("question_source 必须为", " ".join(errors))

    def test_handoff_records_supplement_count_and_source_distribution(self) -> None:
        intake = deepcopy(self.intake)
        intake["name"] = "supplement-contract-review"
        intake["domain_supplement"] = [
            self.valid_item("builtin-archetype"),
            self.valid_item("builtin-archetype"),
            self.valid_item("authorized-research"),
        ]

        with tempfile.TemporaryDirectory() as temporary_directory:
            target = create_skill(intake, Path(temporary_directory))

            errors, warnings = check(target)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])
            handoff = (target / "reports" / "creation-handoff.md").read_text(encoding="utf-8")
            self.assertIn("领域补充问答：3 条", handoff)
            self.assertIn("builtin-archetype 2 条", handoff)
            self.assertIn("authorized-research 1 条", handoff)
            supplement = (target / "references" / "domain-supplement.md").read_text(encoding="utf-8")
            self.assertIn("采购合同是否涉及框架协议", supplement)

    def test_other_archetype_requires_nonempty_domain_supplement(self) -> None:
        intake = deepcopy(self.intake)
        intake["scenario_archetype"] = "other"
        intake["domain_supplement"] = []

        errors = validate_intake(intake)

        self.assertIn("domain_supplement 不能为空", " ".join(errors))

    def test_handoff_without_supplement_has_no_record(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            target = create_skill(self.intake, Path(temporary_directory))

            handoff = (target / "reports" / "creation-handoff.md").read_text(encoding="utf-8")
            self.assertNotIn("领域补充问答", handoff)


if __name__ == "__main__":
    unittest.main()

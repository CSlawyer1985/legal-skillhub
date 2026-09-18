"""意图画布机检兜底的对抗测试（核心层 + 按原型路由）。"""

from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from scripts.create_legal_skill import validate_intake


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_INTAKE = PACKAGE_ROOT / "tests" / "fixtures" / "golden-contract-review-intake.json"


class IntentCanvasGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.intake = json.loads(GOLDEN_INTAKE.read_text(encoding="utf-8"))

    def canvas_errors(self, transform, archetype: str | None = None) -> list[str]:
        intake = deepcopy(self.intake)
        if archetype is not None:
            intake["scenario_archetype"] = archetype
        transform(intake["intent_canvas_coverage"])
        return [error for error in validate_intake(intake) if "intent_canvas_coverage" in error]

    def test_golden_intent_canvas_passes(self) -> None:
        self.assertEqual(validate_intake(self.intake), [])

    def test_missing_canvas_is_rejected(self) -> None:
        intake = deepcopy(self.intake)
        intake.pop("intent_canvas_coverage")

        errors = validate_intake(intake)

        self.assertIn("intent_canvas_coverage", " ".join(errors))

    def test_placeholder_answer_is_rejected(self) -> None:
        errors = self.canvas_errors(
            lambda canvas: canvas.update({"job": "【填写重复法律工作】"})
        )

        self.assertIn("intent_canvas_coverage.job", " ".join(errors))

    def test_vague_answer_is_rejected(self) -> None:
        errors = self.canvas_errors(lambda canvas: canvas.update({"users": "按需"}))

        self.assertIn("intent_canvas_coverage.users", " ".join(errors))

    def test_short_answer_below_four_characters_is_rejected(self) -> None:
        errors = self.canvas_errors(lambda canvas: canvas.update({"decision": "看法"}))

        self.assertIn("intent_canvas_coverage.decision", " ".join(errors))

    def test_non_string_non_object_value_is_rejected(self) -> None:
        errors = self.canvas_errors(lambda canvas: canvas.update({"outputs": ["清单"]}))

        self.assertIn("intent_canvas_coverage.outputs", " ".join(errors))

    def test_core_key_never_allows_not_needed(self) -> None:
        errors = self.canvas_errors(
            lambda canvas: canvas.update(
                {"human_control": {"not_needed": "本任务输出仅供内部参考，由使用人自行判断"}}
            ),
            archetype="legal_retrieval",
        )

        joined = " ".join(errors)
        self.assertIn("intent_canvas_coverage.human_control", joined)
        self.assertIn("核心字段", joined)

    def test_relaxed_archetype_allows_specific_not_needed(self) -> None:
        errors = self.canvas_errors(
            lambda canvas: canvas.update(
                {
                    "actors": {"not_needed": "法规检索不分析具体案件主体，主体资格由使用人另行判断"},
                    "evidence": {"not_needed": "检索结果附来源链接与核验状态，不评价个案证据证明力"},
                }
            ),
            archetype="legal_retrieval",
        )

        self.assertEqual(errors, [])

    def test_relaxed_archetype_still_rejects_unrelaxed_key_not_needed(self) -> None:
        errors = self.canvas_errors(
            lambda canvas: canvas.update(
                {"temporal_bundle": {"not_needed": "检索时总是核验现行有效版本，无需单独记录"}}
            ),
            archetype="legal_retrieval",
        )

        joined = " ".join(errors)
        self.assertIn("intent_canvas_coverage.temporal_bundle", joined)
        self.assertIn("不允许 not_needed", joined)

    def test_strict_archetypes_reject_any_conditional_not_needed(self) -> None:
        for archetype in ("dispute_resolution", "other"):
            with self.subTest(archetype=archetype):
                errors = self.canvas_errors(
                    lambda canvas: canvas.update(
                        {"evidence": {"not_needed": "本场景宣称不涉及证据分层，理由写得很具体"}}
                    ),
                    archetype=archetype,
                )

                self.assertIn("intent_canvas_coverage.evidence", " ".join(errors))

    def test_relaxed_not_needed_with_empty_reason_is_rejected(self) -> None:
        errors = self.canvas_errors(
            lambda canvas: canvas.update({"actors": {"not_needed": ""}}),
            archetype="legal_retrieval",
        )

        self.assertIn("intent_canvas_coverage.actors", " ".join(errors))

    def test_relaxed_not_needed_with_vague_reason_is_rejected(self) -> None:
        errors = self.canvas_errors(
            lambda canvas: canvas.update({"actors": {"not_needed": "略"}}),
            archetype="legal_retrieval",
        )

        self.assertIn("intent_canvas_coverage.actors", " ".join(errors))

    def test_not_needed_with_extra_keys_is_rejected(self) -> None:
        errors = self.canvas_errors(
            lambda canvas: canvas.update(
                {"actors": {"not_needed": "法规检索不分析具体案件主体资格", "note": "额外字段"}}
            ),
            archetype="legal_retrieval",
        )

        self.assertIn("intent_canvas_coverage.actors", " ".join(errors))

    def test_unknown_archetype_treats_all_conditional_keys_as_strict(self) -> None:
        errors = self.canvas_errors(
            lambda canvas: canvas.update(
                {"evidence": {"not_needed": "本场景宣称不涉及证据分层，理由写得很具体"}}
            ),
            archetype="general_contract",
        )

        self.assertIn("intent_canvas_coverage.evidence", " ".join(errors))


if __name__ == "__main__":
    unittest.main()

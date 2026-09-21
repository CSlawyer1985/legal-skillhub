"""LaborPilot 知识路由的行为回归测试。"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
ROUTER_PATH = ROOT / "scripts" / "issue_router.py"
SPEC = importlib.util.spec_from_file_location("laborpilot_issue_router_test", ROUTER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"无法加载知识路由脚本：{ROUTER_PATH}")
ROUTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ROUTER)


class IssueRouterTest(unittest.TestCase):
    def test_broad_query_returns_all_relevant_results(self):
        results = ROUTER.query_knowledge("追索劳动报酬纠纷")

        self.assertGreater(len(results), 3)

    def test_results_keep_the_public_output_schema(self):
        results = ROUTER.query_knowledge("追索劳动报酬纠纷")
        allowed = {"issue", "analysis_points", "zhejiang_guidance"}
        forbidden = {"id", "g", "bd", "zj", "card_id", "gate", "sections"}

        self.assertTrue(results)
        for item in results:
            self.assertEqual(set(item), allowed)
            self.assertTrue(forbidden.isdisjoint(item))
            self.assertLessEqual(len(item["issue"]), 120)
            self.assertLessEqual(len(item["analysis_points"]), 701)
            self.assertLessEqual(len(item["zhejiang_guidance"]), 281)

    def test_empty_query_returns_no_results(self):
        self.assertEqual(ROUTER.query_knowledge("  "), [])

    def test_repeated_queries_are_stable(self):
        expected = ROUTER.query_knowledge("追索劳动报酬纠纷")

        for _ in range(20):
            self.assertEqual(
                ROUTER.query_knowledge("追索劳动报酬纠纷"),
                expected,
            )


if __name__ == "__main__":
    unittest.main()

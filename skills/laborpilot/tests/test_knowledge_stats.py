"""公开知识构建统计清单的复算与篡改反例。"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "knowledge_stats.py"
MANIFEST = ROOT / "data" / "knowledge-build-stats.json"
SPEC = importlib.util.spec_from_file_location("laborpilot_knowledge_stats_test", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"无法加载知识统计脚本：{SCRIPT}")
STATS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(STATS)


class KnowledgeStatsTest(unittest.TestCase):
    def run_cli(self, *arguments: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *arguments], cwd=ROOT,
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(
            result.returncode, expected,
            f"命令退出码异常：{result.args}\nstdout={result.stdout}\nstderr={result.stderr}",
        )
        return result

    def test_public_manifest_matches_embedded_payload_and_declared_scope(self):
        result = json.loads(self.run_cli().stdout)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["statistics"], {
            "total_cards": 96,
            "issue_card_count": 82,
            "gate_card_count": 14,
            # 废止复核：新增被迫解除历史参考节；有内容不代表现行有效。
            "zhejiang_guidance_card_count": 81,
            "statutory_leaf_route_count": 22,
            "operational_fallback_route_count": 1,
            "total_route_category_count": 23,
        })
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["source_inventory"]["document_count"], 149)
        self.assertEqual(manifest["source_inventory"]["scope_counts"]["zhejiang"], 63)
        self.assertNotIn("title", manifest["source_inventory"]["entries"][0])
        self.assertNotIn("path", manifest["source_inventory"]["entries"][0])

    def test_changed_count_or_source_commitment_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            changed_path = Path(temporary) / "knowledge-build-stats.json"
            changed = json.loads(MANIFEST.read_text(encoding="utf-8"))
            changed["knowledge_payload"]["total_cards"] = 95
            changed["source_inventory"]["entries"][0]["content_sha256"] = "0" * 64
            changed_path.write_text(json.dumps(changed, ensure_ascii=False), encoding="utf-8")
            result = json.loads(self.run_cli("--manifest", str(changed_path), expected=1).stdout)
            self.assertEqual(result["status"], "blocked")
            messages = "\n".join(result["findings"])
            self.assertIn("total_cards", messages)
            self.assertIn("entries_sha256", messages)

    def test_fallback_route_is_derived_from_compiled_card_semantics(self):
        cards = [
            {"id": "GATE-205", "g": "", "t": "劳动合同纠纷（兜底）", "bd": "运行路由"},
            {"id": "GATE-205", "g": "", "t": "劳动合同纠纷", "bd": "普通运行路由"},
            {"id": "GATE-206", "g": "", "t": "劳动合同纠纷（兜底）", "bd": "运行路由"},
            {"id": "ISSUE-1", "g": "劳动合同纠纷", "t": "劳动合同纠纷（兜底）", "bd": "运行路由"},
        ]

        self.assertEqual(STATS.operational_fallback_route_count(cards), 1)


if __name__ == "__main__":
    unittest.main()

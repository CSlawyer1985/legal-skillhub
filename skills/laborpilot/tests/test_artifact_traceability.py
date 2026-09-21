"""正式产物来源登记的最小反例。"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CASE_STATE = ROOT / "scripts" / "case_state.py"
WORKFLOW = ROOT / "scripts" / "workflow_graph.py"
GENERATOR = ROOT / "scripts" / "generate_docs.py"
DOCX_CASE = ROOT / "tests" / "fixtures" / "docx-case.json"


class ArtifactTraceabilityTest(unittest.TestCase):
    def run_cli(self, script: Path, *arguments: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(script), *arguments], cwd=ROOT,
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(
            result.returncode, expected,
            f"命令退出码异常：{result.args}\nstdout={result.stdout}\nstderr={result.stderr}",
        )
        return result

    def generate_valid_draft(self, root: Path) -> Path:
        self.run_cli(
            GENERATOR,
            "--case", str(DOCX_CASE),
            "--output", str(root),
            "--types", "仲裁申请书",
            "--delivery-status", "lawyer_review_draft",
            "--strict",
        )
        return root / "01_律师复核初稿" / "02_劳动仲裁申请书_律师复核初稿_v1.docx"

    def register_lineage(self, root: Path) -> tuple[Path, Path, Path]:
        state_path = root / "case_state.json"
        input_path = root / "drafting-input.json"
        input_path.write_text('{"fictional": true}\n', encoding="utf-8")
        draft_path = self.generate_valid_draft(root)
        self.run_cli(CASE_STATE, "init", "--output", str(state_path))
        self.run_cli(
            CASE_STATE, "record-decision", "--input", str(state_path),
            "--decision-id", "decision-trace", "--decision", "用户确认本测试采用虚构起草口径。",
            "--confirmed-by", "fictional-user",
        )
        self.run_cli(
            WORKFLOW, "register-artifact", "--state", str(state_path),
            "--path", str(input_path), "--kind", "drafting_input", "--version", "1",
            "--delivery-status", "internal_work_product", "--generator", "test-fixture",
            "--source-ref", "decisions:decision-trace", "--created-by", "test",
            "--artifact-id", "artifact-input",
        )
        self.run_cli(
            WORKFLOW, "register-artifact", "--state", str(state_path),
            "--path", str(draft_path), "--kind", "arbitration_application", "--version", "1",
            "--delivery-status", "lawyer_review_draft", "--generator", "scripts/generate_docs.py",
            "--derived-from", "artifact-input", "--created-by", "test",
            "--artifact-id", "artifact-draft",
        )
        return state_path, input_path, draft_path

    def test_formal_artifact_rejects_missing_business_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state_path = root / "case_state.json"
            draft_path = self.generate_valid_draft(root)
            self.run_cli(CASE_STATE, "init", "--output", str(state_path))

            result = self.run_cli(
                WORKFLOW, "register-artifact", "--state", str(state_path),
                "--path", str(draft_path), "--kind", "arbitration_application", "--version", "1",
                "--delivery-status", "lawyer_review_draft", "--generator", "scripts/generate_docs.py",
                "--created-by", "test", expected=2,
            )
            self.assertIn("业务来源", result.stderr)

    def test_changed_business_source_invalidates_registered_lineage(self):
        with tempfile.TemporaryDirectory() as temporary:
            state_path, _, _ = self.register_lineage(Path(temporary))
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["decisions"][0]["decision"] = "事后改写的另一项虚构起草口径。"
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            result = self.run_cli(
                WORKFLOW, "trace-artifact", "--state", str(state_path),
                "--artifact-id", "artifact-draft", expected=1,
            )
            errors = "\n".join(json.loads(result.stdout)["errors"])
            self.assertIn("业务来源摘要已过期", errors)

    def test_changed_upstream_file_and_cycle_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            state_path, input_path, _ = self.register_lineage(Path(temporary))
            original = input_path.read_bytes()
            input_path.write_bytes(original + b"tampered")
            changed = self.run_cli(
                WORKFLOW, "trace-artifact", "--state", str(state_path),
                "--artifact-id", "artifact-draft", expected=1,
            )
            changed_errors = "\n".join(json.loads(changed.stdout)["errors"])
            self.assertIn("artifact-input 当前文件哈希与登记值不一致", changed_errors)

            input_path.write_bytes(original)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            input_artifact = next(item for item in state["artifacts"] if item["artifact_id"] == "artifact-input")
            input_artifact["derived_from"] = ["artifact-draft"]
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            cyclic = self.run_cli(
                WORKFLOW, "trace-artifact", "--state", str(state_path),
                "--artifact-id", "artifact-draft", expected=1,
            )
            cyclic_errors = "\n".join(json.loads(cyclic.stdout)["errors"])
            self.assertIn("形成循环", cyclic_errors)


if __name__ == "__main__":
    unittest.main()

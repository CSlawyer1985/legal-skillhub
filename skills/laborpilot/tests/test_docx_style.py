"""JLS DOCX 版式、交付分层和最终提交版来源门禁。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
GENERATOR = SCRIPTS / "generate_docs.py"
STYLE = SCRIPTS / "docx_style.py"

sys.path.insert(0, str(SCRIPTS))
from xml_safe import fromstring as safe_fromstring
sys.path.insert(0, str(SCRIPTS))
import workflow_graph as WORKFLOW  # noqa: E402


def payload(*, placeholder: bool = False) -> dict:
    facts = "【待确认：解除理由】" if placeholder else (
        "2025年6月15日，测试用人单位向测试劳动者送达解除通知。现有虚构材料能够证明解除行为。"
    )
    return {
        "case": {
            "申请人": "测试劳动者（虚构）",
            "性别": "女",
            "出生年月": "1990年1月1日",
            "民族": "汉族",
            "电话": "00000000000",
            "被申请人": "测试用人单位（虚构）",
            "被申请人地址": "测试地址",
            "统一社会信用代码": "TEST00000000000000",
            "案由": "违法解除劳动合同争议",
            "仲裁委": "测试劳动人事争议仲裁委员会",
            "事实与理由": facts,
        },
        "claims": [{
            "事项": "违法解除劳动合同赔偿金",
            "金额": 70000.00,
            "计算式": "10000元／月×3.5个月×2",
        }],
        "evidence": [{
            "名称": "解除通知（虚构）",
            "来源": "测试劳动者",
            "页码": "1",
            "证明目的": "证明测试用人单位作出解除通知。",
        }],
        "actions": {
            "核实": [{"优先级": "高", "问题": "解除理由", "影响": "赔偿金"}],
            "证据": [{"优先级": "高", "材料": "解除依据", "持有人": "用人单位", "证明目的": "解除合法性"}],
            "核对": [{"事项": "工资基数", "口径": "10000元／月", "风险": "影响赔偿金"}],
        },
    }


class DocxStyleTest(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(shutil.which("pandoc"), "DOCX 版式测试需要安装 Pandoc。")

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

    @staticmethod
    def write_case(root: Path, content: dict) -> Path:
        path = root / "case.json"
        path.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    def generate(
        self,
        root: Path,
        case_path: Path,
        types: str,
        delivery_status: str = "lawyer_review_draft",
        approved_by: str | None = None,
        expected: int = 0,
    ) -> subprocess.CompletedProcess[str]:
        arguments = [
            "--case", str(case_path), "--output", str(root), "--types", types,
            "--delivery-status", delivery_status, "--strict",
        ]
        if approved_by:
            arguments.extend(["--approved-by", approved_by])
        return self.run_cli(GENERATOR, *arguments, expected=expected)

    def test_draft_outputs_are_separated_versioned_and_structurally_valid(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            case_path = self.write_case(root, payload())
            self.generate(root, case_path, "仲裁申请书,证据清单,行动清单")

            draft_dir = root / "01_律师复核初稿"
            expected = {
                "02_劳动仲裁申请书_律师复核初稿_v1.docx": "仲裁申请书",
                "03_证据目录_律师复核初稿_v1.docx": "证据清单",
                "04_待补材料与行动清单_律师复核稿_v1.docx": "行动清单",
            }
            self.assertEqual({path.name for path in draft_dir.glob("*.docx")}, set(expected))
            for filename, document_type in expected.items():
                result = json.loads(self.run_cli(
                    STYLE, "check", "--input", str(draft_dir / filename),
                    "--document-type", document_type,
                    "--delivery-status", "lawyer_review_draft",
                ).stdout)
                self.assertEqual(result["status"], "pass")
            work = root / ".casework" / "drafting"
            self.assertEqual(len(list(work.glob("*.md"))), 3)
            self.assertEqual(len(list(work.glob("*_版式验证.json"))), 3)
            repeated = self.generate(root, case_path, "仲裁申请书", expected=2)
            self.assertIn("避免覆盖既有版本", repeated.stderr)

    def test_final_submission_requires_lawyer_decision_and_rejects_internal_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            case_path = self.write_case(root, payload())
            missing = self.generate(
                root, case_path, "仲裁申请书", delivery_status="final_submission", expected=2,
            )
            self.assertIn("--approved-by", missing.stderr)
            action = self.generate(
                root, case_path, "行动清单", delivery_status="final_submission",
                approved_by="测试律师", expected=2,
            )
            self.assertIn("行动清单", action.stderr)

            placeholder_path = self.write_case(root, payload(placeholder=True))
            blocked = self.generate(
                root, placeholder_path, "仲裁申请书", delivery_status="final_submission",
                approved_by="测试律师", expected=1,
            )
            self.assertIn("最终提交版仍含内部占位", blocked.stderr)
            self.assertFalse(any((root / "02_最终提交版").glob("*.docx")))

    def test_final_submission_is_a_new_validated_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            case_path = self.write_case(root, payload())
            self.generate(
                root, case_path, "仲裁申请书,证据清单", delivery_status="final_submission",
                approved_by="测试律师",
            )
            final_dir = root / "02_最终提交版"
            expected = {
                "02_劳动仲裁申请书_最终提交版_v1.docx": "仲裁申请书",
                "03_证据目录_最终提交版_v1.docx": "证据清单",
            }
            self.assertEqual({path.name for path in final_dir.glob("*.docx")}, set(expected))
            for filename, document_type in expected.items():
                result = json.loads(self.run_cli(
                    STYLE, "check", "--input", str(final_dir / filename),
                    "--document-type", document_type,
                    "--delivery-status", "final_submission",
                ).stdout)
                self.assertEqual(result["status"], "pass")

    def test_style_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            case_path = self.write_case(root, payload())
            self.generate(root, case_path, "仲裁申请书")
            docx = root / "01_律师复核初稿" / "02_劳动仲裁申请书_律师复核初稿_v1.docx"
            with ZipFile(docx) as archive:
                files = {name: archive.read(name) for name in archive.namelist()}
            original = 'w:eastAsia="仿宋_GB2312"'.encode("utf-8")
            self.assertIn(original, files["word/document.xml"])
            files["word/document.xml"] = files["word/document.xml"].replace(
                original, b'w:eastAsia="SimSun"', 1,
            )
            changed = root / "tampered.docx"
            with ZipFile(changed, "w", ZIP_DEFLATED) as archive:
                for name, content in files.items():
                    archive.writestr(name, content)
            result = json.loads(self.run_cli(
                STYLE, "check", "--input", str(changed),
                "--document-type", "仲裁申请书",
                "--delivery-status", "lawyer_review_draft", expected=1,
            ).stdout)
            self.assertEqual(result["status"], "blocked")
            self.assertTrue(any("中英文字体" in item for item in result["findings"]))

    def test_evidence_submission_lines_are_right_aligned_without_fixed_indent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            case_path = self.write_case(root, payload())
            self.generate(root, case_path, "证据清单")
            docx = root / "01_律师复核初稿" / "03_证据目录_律师复核初稿_v1.docx"
            with ZipFile(docx) as archive:
                document = safe_fromstring(archive.read("word/document.xml"))

            namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
            full_text = "".join(node.text or "" for node in document.iter(namespace + "t"))
            self.assertIn("违法解除劳动合同争议一案", full_text)
            self.assertNotIn("争议劳动仲裁一案", full_text)
            matched = {}
            for paragraph in document.iter(namespace + "p"):
                text = "".join(node.text or "" for node in paragraph.iter(namespace + "t")).strip()
                if text.startswith(("提交人：", "提交时间：")):
                    matched[text.split("：", 1)[0]] = paragraph

            self.assertEqual(set(matched), {"提交人", "提交时间"})
            for label, paragraph in matched.items():
                properties = paragraph.find(namespace + "pPr")
                self.assertIsNotNone(properties, label)
                alignment = properties.find(namespace + "jc")
                self.assertEqual(alignment.get(namespace + "val"), "right", label)
                indent = properties.find(namespace + "ind")
                self.assertTrue(
                    indent is None or all(
                        indent.get(namespace + key) in {None, "0"}
                        for key in ("start", "left", "firstLine")
                    ),
                    f"{label}不应保留申请书落款的固定缩进。",
                )

    def test_final_submission_lineage_requires_current_approved_draft(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            case_path = self.write_case(root, payload())
            self.generate(root, case_path, "仲裁申请书")
            self.generate(
                root, case_path, "仲裁申请书", delivery_status="final_submission",
                approved_by="测试律师",
            )
            draft_path = root / "01_律师复核初稿" / "02_劳动仲裁申请书_律师复核初稿_v1.docx"
            final_path = root / "02_最终提交版" / "02_劳动仲裁申请书_最终提交版_v1.docx"
            decision = {"decision_id": "decision-docx-test", "status": "confirmed", "value": "虚构提交决定"}
            source = {
                "collection": "decisions", "record_id": decision["decision_id"],
                "sha256": WORKFLOW.canonical_digest(decision),
            }
            draft_sha = hashlib.sha256(draft_path.read_bytes()).hexdigest()
            final_sha = hashlib.sha256(final_path.read_bytes()).hexdigest()
            common = {
                "kind": "arbitration_application", "version": "1",
                "generator": "scripts/generate_docs.py", "producer_version": WORKFLOW.PACKAGE_VERSION,
                "created_by": "test", "created_at": "2026-08-24T00:00:00+08:00",
            }
            state = {
                "decisions": [decision],
                "artifacts": [
                    {
                        **common, "artifact_id": "draft-docx", "delivery_status": "lawyer_review_draft",
                        "path": str(draft_path), "sha256": draft_sha,
                        "derived_from": [], "source_refs": [source],
                    },
                    {
                        **common, "artifact_id": "final-docx", "delivery_status": "final_submission",
                        "path": str(final_path), "sha256": final_sha,
                        "derived_from": ["draft-docx"], "source_refs": [],
                    },
                ],
                "approvals": [],
            }
            errors = WORKFLOW.artifact_lineage_errors(state, "final-docx")
            self.assertTrue(any("尚未形成" in item for item in errors))
            state["approvals"].append({
                "gate": "lawyer_approval", "status": "approved",
                "artifact_ids": ["draft-docx"], "artifact_sha256s": {"draft-docx": draft_sha},
            })
            self.assertEqual(WORKFLOW.artifact_lineage_errors(state, "final-docx"), [])


if __name__ == "__main__":
    unittest.main()

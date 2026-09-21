"""材料接入和事实时间轴执行器的业务行为回归。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ingest_materials import build_page_index, pdf_text_layer_status


ROOT = Path(__file__).resolve().parents[1]
CASE_STATE = ROOT / "scripts" / "case_state.py"
WORKFLOW = ROOT / "scripts" / "workflow_graph.py"
INGEST_MATERIALS = ROOT / "scripts" / "ingest_materials.py"
BUILD_TIMELINE = ROOT / "scripts" / "build_timeline.py"


class MaterialFactExecutorsTest(unittest.TestCase):
    def test_mixed_pdf_text_layer_is_not_treated_as_complete(self):
        first_page = "第一页包含劳动合同、工资支付和解除通知等足够的可提取文字内容。"
        second_page = "第二页包含考勤记录、工资流水和送达情况等足够的可提取文字内容。"
        complete, pages = pdf_text_layer_status(f"{first_page}\f{second_page}\f", 2)
        self.assertEqual((complete, pages), ("complete", 2))
        partial, pages = pdf_text_layer_status(f"{first_page}\f\f", 2)
        self.assertEqual((partial, pages), ("partial", 1))
        empty, pages = pdf_text_layer_status("\f\f", 2)
        self.assertEqual((empty, pages), ("none", 0))

        page_index = build_page_index(f"{first_page}\f待 OCR\f\f", 3, "pdf")
        self.assertEqual([item["page_number"] for item in page_index], [1, 2, 3])
        self.assertEqual(
            [item["text_layer_status"] for item in page_index],
            ["complete", "partial", "none"],
        )
        self.assertEqual(
            [item["ocr_status"] for item in page_index],
            ["not_needed", "pending", "pending"],
        )

    def run_cli(self, script: Path, *arguments: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(script), *arguments],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            expected,
            f"命令退出码异常：{result.args}\nstdout={result.stdout}\nstderr={result.stderr}",
        )
        return result

    def initialize_case(self, state_path: Path) -> None:
        self.run_cli(CASE_STATE, "init", "--output", str(state_path))
        self.run_cli(
            CASE_STATE, "set-task", "--input", str(state_path),
            "--representation", "employee", "--stage", "arbitration",
            "--user-request", "整理案件材料并建立时间轴",
            "--requested-output", "案件研判报告", "--confirmed-by", "user",
        )
        self.run_cli(
            WORKFLOW, "transition", "--state", str(state_path),
            "--event", "pass", "--actor", "test",
        )

    def test_materials_are_indexed_locally_and_facts_keep_provenance(self):
        with tempfile.TemporaryDirectory() as temporary:
            case_root = Path(temporary)
            state_path = case_root / ".casework" / "case_state.json"
            source = case_root / "解除通知.txt"
            image = case_root / "考勤截图.png"
            scanned_pdf = case_root / "扫描解除通知.pdf"
            source.write_text(
                "2022年3月1日劳动者入职。\n2025年6月15日公司通知解除。\n"
                "联系电话13800138000，身份证330302199001011234。",
                encoding="utf-8",
            )
            # PNG 文件签名足以验证材料类型路由；执行器不负责解码或 OCR 图像。
            image.write_bytes(b"\x89PNG\r\n\x1a\n" + b"test-image")
            scanned_pdf.write_bytes(b"%PDF-1.4\n1 0 obj\n<< /Type /Page >>\nendobj\n%%EOF\n")
            original_bytes = source.read_bytes()
            self.initialize_case(state_path)

            result = self.run_cli(
                INGEST_MATERIALS,
                "--state", str(state_path),
                "--source", str(source),
                "--source", str(image),
                "--source", str(scanned_pdf),
                "--original-or-copy", "copy",
            )
            summary = json.loads(result.stdout)
            self.assertEqual(summary["new_count"], 3)
            self.assertEqual(summary["ocr_pending"], 2)
            self.assertEqual(source.read_bytes(), original_bytes)

            state = json.loads(state_path.read_text(encoding="utf-8"))
            materials = {item["file_name"]: item for item in state["materials"]}
            text_record = materials[source.name]
            image_record = materials[image.name]
            pdf_record = materials[scanned_pdf.name]
            self.assertEqual(text_record["source_sha256"], hashlib.sha256(original_bytes).hexdigest())
            self.assertEqual(text_record["text_layer_status"], "complete")
            self.assertEqual(text_record["ocr_status"], "not_needed")
            self.assertTrue(Path(text_record["derivative_path"]).is_file())
            self.assertTrue(Path(text_record["ingestion_record_path"]).is_file())
            self.assertEqual(image_record["text_layer_status"], "none")
            self.assertEqual(image_record["ocr_status"], "pending")
            self.assertIsNone(image_record["derivative_path"])
            self.assertEqual(image_record["page_index"], [{
                "page_number": 1,
                "text_layer_status": "none",
                "extracted_char_count": 0,
                "ocr_status": "pending",
            }])
            self.assertEqual(pdf_record["file_kind"], "pdf")
            self.assertEqual(pdf_record["page_count"], 1)
            self.assertEqual(pdf_record["text_layer_status"], "none")
            self.assertEqual(pdf_record["ocr_status"], "pending")
            self.assertEqual([item["page_number"] for item in pdf_record["page_index"]], [1])
            self.assertTrue((case_root / ".casework" / "materials" / "index.json").is_file())
            self.assertTrue((case_root / ".casework" / "materials" / "index.md").is_file())
            index_payload = json.loads(
                (case_root / ".casework" / "materials" / "index.json").read_text(encoding="utf-8")
            )
            indexed_pdf = next(
                item for item in index_payload["materials"] if item["file_name"] == scanned_pdf.name
            )
            self.assertEqual(indexed_pdf["page_index"], pdf_record["page_index"])
            self.assertIn(
                "## 分页索引",
                (case_root / ".casework" / "materials" / "index.md").read_text(encoding="utf-8"),
            )

            # 模拟外部 OCR 工具将结果写入材料派生目录。重新接入同一
            # 扫描 PDF 时，不得用新的 pdftotext 暂存结果覆盖 OCR 文本。
            pdf_record_path = Path(pdf_record["ingestion_record_path"])
            ocr_derivative = pdf_record_path.parent / "text.txt"
            ocr_derivative.write_text("2025年6月15日 OCR 复核文本。", encoding="utf-8")
            for target in (pdf_record,):
                target["derivative_path"] = str(ocr_derivative)
                target["ocr_engine"] = "test-ocr"
                target["ocr_status"] = "completed"
                target["ocr_completed_at"] = "2026-08-24T10:00:00+08:00"
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            pdf_record_path.write_text(json.dumps(pdf_record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.run_cli(
                INGEST_MATERIALS, "--state", str(state_path), "--source", str(scanned_pdf),
            )
            self.assertEqual(ocr_derivative.read_text(encoding="utf-8"), "2025年6月15日 OCR 复核文本。")
            state = json.loads(state_path.read_text(encoding="utf-8"))
            repaired_pdf = next(item for item in state["materials"] if item["file_name"] == scanned_pdf.name)
            self.assertEqual(repaired_pdf["ocr_status"], "completed")
            self.assertEqual(repaired_pdf["ocr_completed_at"], "2026-08-24T10:00:00+08:00")

            rerun = self.run_cli(
                INGEST_MATERIALS, "--state", str(state_path), "--source", str(source),
            )
            self.assertEqual(json.loads(rerun.stdout)["new_count"], 0)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(len(state["materials"]), 3)

            repaired_pdf = next(item for item in state["materials"] if item["file_name"] == scanned_pdf.name)
            repaired_record_path = Path(repaired_pdf["ingestion_record_path"])
            repaired_record = json.loads(repaired_record_path.read_text(encoding="utf-8"))
            saved_page_index = repaired_pdf["page_index"]
            repaired_pdf["page_index"] = []
            repaired_record["page_index"] = []
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            repaired_record_path.write_text(
                json.dumps(repaired_record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            blocked_page_index = self.run_cli(
                WORKFLOW, "transition", "--state", str(state_path),
                "--event", "pass", "--actor", "test", expected=2,
            )
            self.assertIn("traceable_material", blocked_page_index.stderr)
            repaired_pdf["page_index"] = saved_page_index
            repaired_record["page_index"] = saved_page_index
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            repaired_record_path.write_text(
                json.dumps(repaired_record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )

            self.run_cli(
                WORKFLOW, "transition", "--state", str(state_path),
                "--event", "pass", "--actor", "test",
            )
            facts_input = case_root / "facts.json"
            facts_input.write_text(json.dumps({"facts": [
                {
                    "statement": "劳动者手机号13800138000，其身份证号330302199001011234。",
                    "status": "client_statement",
                    "sources": [],
                },
                {
                    "statement": "解除通知记载公司于2025年6月15日解除劳动合同。",
                    "status": "supported",
                    "sources": [text_record["material_id"]],
                    "occurred_on": "2025-06-15",
                    "source_locators": [{"material_id": text_record["material_id"], "line": 2}],
                },
            ]}, ensure_ascii=False), encoding="utf-8")
            timeline_result = self.run_cli(
                BUILD_TIMELINE,
                "--state", str(state_path),
                "--input", str(facts_input),
                "--extract-from-materials",
            )
            self.assertGreaterEqual(json.loads(timeline_result.stdout)["added_count"], 4)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            statements = "\n".join(item["statement"] for item in state["facts"])
            self.assertNotIn("13800138000", statements)
            self.assertNotIn("330302199001011234", statements)
            self.assertIn("【手机号已隐去】", statements)
            self.assertIn("【身份证号已隐去】", statements)
            auto_facts = [item for item in state["facts"] if item.get("extraction_method") == "date_sentence"]
            self.assertTrue(auto_facts)
            self.assertTrue(all(item["status"] == "to_verify" for item in auto_facts))
            promoted = next(item for item in auto_facts if item["statement"] == "2022年3月1日劳动者入职。")
            promoted_id = promoted["fact_id"]
            promotion_input = case_root / "promotion.json"
            promotion_input.write_text(json.dumps({"facts": [{
                "statement": promoted["statement"],
                "status": "supported",
                "sources": [text_record["material_id"]],
                "occurred_on": "2022-03-01",
                "source_locators": [{"material_id": text_record["material_id"], "line": 1}],
            }]}, ensure_ascii=False), encoding="utf-8")
            promotion = json.loads(self.run_cli(
                BUILD_TIMELINE, "--state", str(state_path), "--input", str(promotion_input),
            ).stdout)
            self.assertEqual(promotion["added_count"], 0)
            self.assertEqual(promotion["updated_count"], 1)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            promoted_after = next(item for item in state["facts"] if item["fact_id"] == promoted_id)
            self.assertEqual(promoted_after["status"], "supported")
            self.assertEqual(len([item for item in state["facts"] if item["fact_id"] == promoted_id]), 1)
            timeline = json.loads((case_root / ".casework" / "intake" / "timeline.json").read_text(encoding="utf-8"))
            dated = [item["occurred_on"] for item in timeline["facts"] if item.get("occurred_on")]
            self.assertEqual(dated, sorted(dated))

            self.run_cli(
                WORKFLOW, "transition", "--state", str(state_path),
                "--event", "pass", "--actor", "test",
            )
            record_path = Path(text_record["ingestion_record_path"])
            original_record = record_path.read_bytes()
            tampered_record = json.loads(original_record.decode("utf-8"))
            tampered_record["source_sha256"] = "0" * 64
            record_path.write_text(json.dumps(tampered_record, ensure_ascii=False), encoding="utf-8")
            tampered_route = json.loads(
                self.run_cli(WORKFLOW, "route", "--state", str(state_path)).stdout
            )
            self.assertEqual(tampered_route["status"], "blocked")
            record_path.write_bytes(original_record)
            source.write_text("原件内容被改变", encoding="utf-8")
            blocked = self.run_cli(WORKFLOW, "route", "--state", str(state_path))
            route = json.loads(blocked.stdout)
            self.assertEqual(route["status"], "blocked")
            self.assertIn("traceable_material", "\n".join(route["blockers"]))

    def test_supported_fact_without_registered_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            case_root = Path(temporary)
            state_path = case_root / "case_state.json"
            self.initialize_case(state_path)
            self.run_cli(
                WORKFLOW, "record-waiver", "--state", str(state_path),
                "--requirement", "traceable_material",
                "--reason", "用户确认本轮仅整理其口头陈述，没有文件材料。",
                "--confirmed-by", "user",
            )
            self.run_cli(
                WORKFLOW, "transition", "--state", str(state_path),
                "--event", "pass", "--actor", "test",
            )
            facts_input = case_root / "invalid-facts.json"
            facts_input.write_text(json.dumps({"facts": [{
                "statement": "公司已经解除劳动合同。",
                "status": "supported",
                "sources": [],
            }]}, ensure_ascii=False), encoding="utf-8")
            result = self.run_cli(
                BUILD_TIMELINE, "--state", str(state_path), "--input", str(facts_input), expected=2,
            )
            self.assertIn("必须关联材料来源", result.stderr)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["facts"], [])

    def test_fact_conflicts_are_bidirectional_and_keep_review_action(self):
        with tempfile.TemporaryDirectory() as temporary:
            case_root = Path(temporary)
            state_path = case_root / "case_state.json"
            self.initialize_case(state_path)
            self.run_cli(
                WORKFLOW, "record-waiver", "--state", str(state_path),
                "--requirement", "traceable_material",
                "--reason", "用户确认本轮只登记双方陈述，不提供文件材料。",
                "--confirmed-by", "user",
            )
            self.run_cli(
                WORKFLOW, "transition", "--state", str(state_path),
                "--event", "pass", "--actor", "test",
            )
            conflict_input = case_root / "conflicts.json"
            conflict_input.write_text(json.dumps({"facts": [
                {
                    "fact_id": "fact-client-dismissal",
                    "statement": "劳动者陈述公司于2025年6月15日口头解除劳动合同。",
                    "status": "client_statement", "sources": [],
                    "occurred_on": "2025-06-15",
                    "conflicts_with_fact_ids": ["fact-employer-resignation"],
                    "conflict_status": "unresolved",
                    "conflict_explanation": "双方对劳动关系终止原因存在直接矛盾。",
                    "conflict_next_action": "核对解除通知、辞职申请及双方完整聊天记录。",
                },
                {
                    "fact_id": "fact-employer-resignation",
                    "statement": "用人单位主张劳动者于2025年6月15日自行辞职。",
                    "status": "opponent_allegation", "sources": [],
                    "occurred_on": "2025-06-15",
                    "conflicts_with_fact_ids": ["fact-client-dismissal"],
                    "conflict_status": "unresolved",
                    "conflict_explanation": "双方对劳动关系终止原因存在直接矛盾。",
                    "conflict_next_action": "核对解除通知、辞职申请及双方完整聊天记录。",
                },
            ]}, ensure_ascii=False), encoding="utf-8")
            self.run_cli(BUILD_TIMELINE, "--state", str(state_path), "--input", str(conflict_input))
            state = json.loads(state_path.read_text(encoding="utf-8"))
            facts = {item["fact_id"]: item for item in state["facts"]}
            self.assertEqual(
                facts["fact-client-dismissal"]["conflicts_with_fact_ids"],
                ["fact-employer-resignation"],
            )
            self.assertEqual(facts["fact-client-dismissal"]["conflict_status"], "unresolved")
            self.assertTrue(facts["fact-client-dismissal"]["conflict_next_action"])

            one_way = case_root / "one-way.json"
            one_way.write_text(json.dumps({"facts": [{
                "fact_id": "fact-client-dismissal",
                "statement": "劳动者陈述公司于2025年6月15日口头解除劳动合同。",
                "status": "client_statement", "sources": [],
                "occurred_on": "2025-06-15",
                "conflicts_with_fact_ids": [],
                "conflict_status": "none",
                "conflict_explanation": None,
                "conflict_next_action": None,
            }]}, ensure_ascii=False), encoding="utf-8")
            original = state_path.read_bytes()
            rejected = self.run_cli(
                BUILD_TIMELINE, "--state", str(state_path), "--input", str(one_way), expected=2,
            )
            self.assertIn("事实冲突关系必须双向一致", rejected.stderr)
            self.assertEqual(state_path.read_bytes(), original)

    def test_large_text_is_registered_without_unbounded_decode(self):
        with tempfile.TemporaryDirectory() as temporary:
            case_root = Path(temporary)
            state_path = case_root / "case_state.json"
            source = case_root / "large.txt"
            with source.open("wb") as stream:
                stream.truncate(33 * 1024 * 1024)
            self.initialize_case(state_path)
            self.run_cli(INGEST_MATERIALS, "--state", str(state_path), "--source", str(source))
            state = json.loads(state_path.read_text(encoding="utf-8"))
            material = state["materials"][0]
            self.assertEqual(material["file_kind"], "text")
            self.assertEqual(material["text_layer_status"], "unknown")
            self.assertIsNone(material["derivative_path"])

    def test_timeline_rejects_unsafe_fact_id_and_external_derivative(self):
        with tempfile.TemporaryDirectory() as temporary:
            case_root = Path(temporary)
            state_path = case_root / "case_state.json"
            source = case_root / "material.txt"
            source.write_text("2025年6月15日解除。", encoding="utf-8")
            self.initialize_case(state_path)
            self.run_cli(INGEST_MATERIALS, "--state", str(state_path), "--source", str(source))
            self.run_cli(
                WORKFLOW, "transition", "--state", str(state_path),
                "--event", "pass", "--actor", "test",
            )

            invalid_input = case_root / "unsafe.json"
            invalid_input.write_text(json.dumps({"facts": [{
                "fact_id": "../fact",
                "statement": "用人单位于2025年6月15日解除劳动合同。",
                "status": "client_statement",
                "sources": [],
                "occurred_on": "2025-06-15",
            }]}, ensure_ascii=False), encoding="utf-8")
            unsafe_id = self.run_cli(
                BUILD_TIMELINE, "--state", str(state_path), "--input", str(invalid_input), expected=2,
            )
            self.assertIn("事实 ID 含不安全字符", unsafe_id.stderr)

            external = case_root / "outside-secret.txt"
            external.write_text("2024年1月1日不应读取。", encoding="utf-8")
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["materials"][0]["derivative_path"] = str(external)
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            outside = self.run_cli(
                BUILD_TIMELINE, "--state", str(state_path), "--extract-from-materials", expected=2,
            )
            self.assertIn("拒绝读取 .casework/materials 之外", outside.stderr)


if __name__ == "__main__":
    unittest.main()

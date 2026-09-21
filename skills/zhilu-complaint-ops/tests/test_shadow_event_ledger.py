import json
import tempfile
import unittest
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
import shadow_event_ledger as s

CFG = {
    "match": {
        "auto_link_score": 85,
        "manual_review_score": 60,
        "minimum_gap": 20,
        "strong_anchors": ["case_no", "quoted_source", "order_no", "source_media"],
    }
}

CASES = [
    {
        "recordId": "rec-1",
        "投诉编号": "WS-2026-001",
        "投诉人": "张三",
        "联系方式": "138****0001",
        "被投诉主体": "钉钉",
        "投诉类型": "退款纠纷",
        "诉求金额": 100,
        "投诉内容": "会员退款未到账",
        "原始媒体指纹": "blob-a",
        "处理状态": "处理中",
    },
    {
        "recordId": "rec-2",
        "投诉编号": "WS-2026-002",
        "投诉人": "张三",
        "联系方式": "138****0001",
        "被投诉主体": "钉钉",
        "投诉类型": "服务质量",
        "诉求金额": 200,
        "投诉内容": "设备故障",
        "处理状态": "处理中",
    },
]


def event(text, ocr=None, message_id="m1", blob=""):
    return {
        "source": {"channel": "service_group", "conversation_id": "cid", "message_id": message_id, "resource_id": "r1" if blob else ""},
        "payload": {"kind": "mixed", "raw_text": text, "blob_sha256": blob, "ocr_result": ocr or {}},
    }


class ShadowLedgerTests(unittest.TestCase):
    def test_case_number_strong_anchor_auto_links(self):
        row = s.process_event(event("补充支付凭证", {"投诉编号": "WS-2026-001"}, blob="blob-x"), CASES, CFG, set())
        self.assertEqual(row["match"]["decision"], "AUTO_LINK")
        self.assertEqual(row["match"]["record_id"], "rec-1")
        self.assertFalse(row["processing"]["write_main_ledger"])

    def test_phone_only_never_auto_links(self):
        row = s.process_event(event("补充材料 手机号138****0001", {"联系方式": "138****0001"}), CASES, CFG, set())
        self.assertNotEqual(row["match"]["decision"], "AUTO_LINK")
        self.assertEqual(row["processing"]["status"], "REVIEW_REQUIRED")

    def test_pending_refund_is_progress_not_closure(self):
        row = s.process_event(event("已提交退款，预计三天到账", {"投诉编号": "WS-2026-001"}), CASES, CFG, set())
        self.assertEqual(row["classification"]["event_type"], "PROGRESS")

    def test_closure_candidate_never_writes_in_phase1(self):
        row = s.process_event(event("退款成功，已到账", {"投诉编号": "WS-2026-001"}), CASES, CFG, set())
        self.assertEqual(row["classification"]["event_type"], "CLOSURE_CANDIDATE")
        self.assertEqual(row["processing"]["status"], "REVIEW_REQUIRED")
        self.assertFalse(row["processing"]["write_main_ledger"])

    def test_transport_duplicate_is_ignored(self):
        e = event("补充材料", {"投诉编号": "WS-2026-001"})
        fp = s.transport_fingerprint(e)
        row = s.process_event(e, CASES, CFG, {fp})
        self.assertEqual(row["classification"]["event_type"], "DUPLICATE")
        self.assertEqual(row["processing"]["status"], "IGNORED")

    def test_event_id_is_stable(self):
        e = event("补充材料", {"投诉编号": "WS-2026-001"})
        one = s.process_event(e, CASES, CFG, set())
        two = s.process_event(e, CASES, CFG, set())
        self.assertEqual(one["event_id"], two["event_id"])


    def test_same_content_new_message_is_deduplicated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = dict(CFG)
            cfg["enable_content_dedup"] = True
            first = event("补充材料", {"投诉编号": "WS-2026-001"}, message_id="first")
            second = event("补充材料", {"投诉编号": "WS-2026-001"}, message_id="second")
            ledger = root / "ledger.jsonl"
            row = s.process_event(first, CASES, cfg, set())
            ledger.write_text(s.stable_json(row) + "\n", encoding="utf-8")
            by_transport, by_content, by_blob = s.load_known_events(ledger)
            features = s.extract_features(second)
            self.assertNotIn(s.transport_fingerprint(second), by_transport)
            self.assertIn(s.content_fingerprint(features), by_content)

    def test_same_content_different_message_not_appended(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            events_path = root / "events.json"
            cases_path = root / "cases.json"
            config_path = root / "config.json"
            ledger_path = root / "ledger.jsonl"
            out_path = root / "out.json"
            cfg = dict(CFG)
            cfg["enable_content_dedup"] = True
            cases_path.write_text(json.dumps(CASES, ensure_ascii=False), encoding="utf-8")
            config_path.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
            argv = sys.argv
            try:
                events_path.write_text(json.dumps([event("补充材料", {"投诉编号": "WS-2026-001"}, message_id="first")], ensure_ascii=False), encoding="utf-8")
                sys.argv = ["shadow_event_ledger.py", "--events", str(events_path), "--cases", str(cases_path), "--config", str(config_path), "--ledger", str(ledger_path), "--out", str(out_path)]
                self.assertEqual(s.main(), 0)
                events_path.write_text(json.dumps([event("补充材料", {"投诉编号": "WS-2026-001"}, message_id="second")], ensure_ascii=False), encoding="utf-8")
                self.assertEqual(s.main(), 0)
            finally:
                sys.argv = argv
            self.assertEqual(len(ledger_path.read_text(encoding="utf-8").splitlines()), 1)
            rerun = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(rerun[0]["classification"]["event_type"], "DUPLICATE")
            self.assertIn("业务内容指纹", rerun[0]["classification"]["reasons"][0])

    def test_same_blob_new_message_is_indexed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = root / "ledger.jsonl"
            first = event("图片一", {}, message_id="first", blob="same-blob")
            row = s.process_event(first, CASES, CFG, set())
            ledger.write_text(s.stable_json(row) + "\n", encoding="utf-8")
            _, _, by_blob = s.load_known_events(ledger)
            self.assertIn("same-blob", by_blob)

    def test_cli_rerun_does_not_append_duplicate_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            events_path = root / "events.json"
            cases_path = root / "cases.json"
            config_path = root / "config.json"
            ledger_path = root / "ledger.jsonl"
            out_path = root / "out.json"
            events_path.write_text(json.dumps([event("补充材料", {"投诉编号": "WS-2026-001"})], ensure_ascii=False), encoding="utf-8")
            cases_path.write_text(json.dumps(CASES, ensure_ascii=False), encoding="utf-8")
            content_cfg = dict(CFG)
            content_cfg["enable_content_dedup"] = True
            config_path.write_text(json.dumps(content_cfg, ensure_ascii=False), encoding="utf-8")
            argv = sys.argv
            try:
                sys.argv = ["shadow_event_ledger.py", "--events", str(events_path), "--cases", str(cases_path), "--config", str(config_path), "--ledger", str(ledger_path), "--out", str(out_path)]
                self.assertEqual(s.main(), 0)
                self.assertEqual(s.main(), 0)
            finally:
                sys.argv = argv
            self.assertEqual(len(ledger_path.read_text(encoding="utf-8").splitlines()), 1)
            rerun = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(rerun[0]["classification"]["event_type"], "DUPLICATE")


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Dependency-free smoke tests for legal_meeting_audit.py."""

from __future__ import annotations

import json
from pathlib import Path

import legal_meeting_audit


ROOT = Path(__file__).resolve().parents[1]


def run() -> None:
    segments, source = legal_meeting_audit.parse_input(str(ROOT / "assets" / "demo-transcript.txt"))
    result = legal_meeting_audit.analyze(segments, source)
    assert len(segments) == 5
    assert result["meta"]["version"] == "1.0.0"
    assert result["verdict"]["risk_level"] in {"红色", "橙色", "黄色", "绿色"}
    assert result["verdict"]["conclusion_overreach_count"] >= 1
    assert "合同/交易" in result["domains"]
    assert len(result["actions"]) >= 2
    assert any(item["owner"] == "行政" for item in result["actions"])
    assert "法槌会议规则初筛" in legal_meeting_audit.render_markdown(result)

    nested = {"data": {"paragraphs": [{"speaker_name": "甲", "text": "我有签章合同", "start_time": "10:00"}]}}
    parsed = legal_meeting_audit.extract_json_segments(nested)
    assert parsed[0].speaker == "甲"
    assert parsed[0].timestamp == "10:00"
    json.dumps(result, ensure_ascii=False)
    print("legal smoke test passed")


if __name__ == "__main__":
    run()


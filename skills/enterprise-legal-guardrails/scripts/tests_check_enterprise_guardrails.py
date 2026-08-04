#!/usr/bin/env python3
"""Basic regression tests for enterprise legal guardrails."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_enterprise_guardrails import analyze_text


def run_all():
    # 1) Ensure defaults still review this known risky output.
    report = analyze_text(
        "John is a scammer and this is a guaranteed 100% win.",
        action="post",
    )
    assert report["status"] == "REVIEW", report
    assert report["thresholds"]["review"] == 5, report
    assert report["thresholds"]["block"] == 9, report

    # 2) Ensure configurable review threshold can move a REVIEW case to WATCH.
    report = analyze_text(
        "John is a scammer and this is a guaranteed 100% win.",
        action="post",
        review_threshold=9,
        block_threshold=9,
    )
    assert report["status"] == "WATCH", report
    assert report["thresholds"] == {"review": 9, "block": 10}, report

    # 3) Ensure configurable block threshold still blocks when lowered.
    report = analyze_text(
        "John is a scammer and this is a guaranteed 100% win.",
        action="post",
        review_threshold=2,
        block_threshold=4,
    )
    assert report["status"] == "BLOCK", report

    # 4) Ensure scope exclude can skip checks without changing status.
    report = analyze_text(
        "John is a scammer and this is a guaranteed 100% win.",
        action="post",
        app="whatsapp",
        scope="exclude",
        app_targets=["whatsapp", "babylon"],
    )
    assert report["status"] == "PASS", report
    assert report["findings_count"] == 0, report

    # 5) Ensure disabled guardrails always PASS.
    report = analyze_text(
        "John is a scammer and this is a guaranteed 100% win.",
        action="post",
        enabled=False,
    )
    assert report["status"] == "PASS", report
    assert report["score"] == 0, report


if __name__ == "__main__":
    run_all()
    print("ok")

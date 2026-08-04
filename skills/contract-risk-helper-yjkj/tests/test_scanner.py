"""
Tests for contract-risk-helper
Run: python3 tests/test_scanner.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from handler import scan, format_results, handle


def test_empty():
    assert scan("") == []
    assert scan("   ") == []
    print("✅ empty input")


def test_no_risk():
    text = "This is a simple service agreement between two parties."
    results = scan(text)
    assert results == []
    print("✅ no-risk text")


def test_unlimited_liability():
    text = "Party A shall have unlimited liability for all damages."
    results = scan(text)
    assert len(results) == 1
    assert results[0]["severity"] == "critical"
    assert results[0]["category"] == "Liability"
    print("✅ unlimited liability detected")


def test_auto_renewal():
    text = "This agreement automatically renews for successive one-year terms."
    results = scan(text)
    assert len(results) == 1
    assert results[0]["severity"] == "critical"
    print("✅ auto-renewal detected")


def test_net90_payment():
    text = "Payment is due within 90 days of invoice."
    results = scan(text)
    assert len(results) == 1
    assert results[0]["severity"] == "warning"
    assert results[0]["category"] == "Payment"
    print("✅ net 90 payment detected")


def test_work_for_hire():
    text = "All work product shall be work-made-for-hire."
    results = scan(text)
    assert len(results) == 1
    assert results[0]["severity"] == "warning"
    print("✅ work-for-hire detected")


def test_no_termination():
    text = "This agreement may not be terminated except for material breach."
    results = scan(text)
    assert len(results) == 1
    assert results[0]["severity"] == "critical"
    print("✅ no termination for convenience detected")


def test_multiple_risks():
    text = (
        "This agreement automatically renews. "
        "Party A has unlimited liability. "
        "Payment is due within 90 days. "
        "All work is work-for-hire."
    )
    results = scan(text)
    assert len(results) == 4
    severities = [r["severity"] for r in results]
    assert severities.count("critical") == 2
    assert severities.count("warning") == 2
    print("✅ multiple risks detected correctly")


def test_handle_ok():
    text = "Party A shall have unlimited liability for all damages."
    resp = handle({"contract_text": text})
    assert resp["ok"] is True
    assert resp["stats"]["total"] == 1
    assert resp["stats"]["critical"] == 1
    print("✅ handle() returns correct stats")


def test_handle_empty():
    resp = handle({"contract_text": ""})
    assert resp["ok"] is False
    assert "error" in resp
    print("✅ handle() handles empty input")


def test_venue():
    text = "The venue shall be determined solely by Party B."
    results = scan(text)
    assert len(results) == 1
    assert results[0]["severity"] == "critical"
    print("✅ unfair venue clause detected")


def test_perpetual_confidentiality():
    text = "All obligations shall survive in perpetuity."
    results = scan(text)
    assert len(results) == 1
    assert results[0]["severity"] == "warning"
    print("✅ perpetual confidentiality detected")


if __name__ == "__main__":
    test_empty()
    test_no_risk()
    test_unlimited_liability()
    test_auto_renewal()
    test_net90_payment()
    test_work_for_hire()
    test_no_termination()
    test_multiple_risks()
    test_handle_ok()
    test_handle_empty()
    test_venue()
    test_perpetual_confidentiality()
    print("\n✅ All tests passed!")

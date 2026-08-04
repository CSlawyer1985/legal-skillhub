"""
Tests for contract-risk-helper v1.1.0
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


def test_unlimited_liability_zh():
    text = "甲方对乙方造成的任何损失承担无限赔偿责任。"
    results = scan(text)
    assert len(results) >= 1
    assert any(r["severity"] == "critical" and r["category"] == "Liability" for r in results)
    print("✅ Chinese unlimited liability detected")


def test_auto_renewal():
    text = "This agreement automatically renews for successive one-year terms."
    results = scan(text)
    assert len(results) == 1
    assert results[0]["severity"] == "critical"
    print("✅ auto-renewal detected")


def test_auto_renewal_zh():
    text = "本合同到期后自动续签一年。"
    results = scan(text)
    assert any(r["severity"] == "critical" and r["category"] == "Termination" for r in results)
    print("✅ Chinese auto-renewal detected")


def test_net90_payment():
    text = "Payment is due within 90 days of invoice."
    results = scan(text)
    assert len(results) == 1
    assert results[0]["severity"] == "warning"
    assert results[0]["category"] == "Payment"
    print("✅ net 90 payment detected")


def test_net90_payment_zh():
    text = "付款期限为到货后 90 天内。"
    results = scan(text)
    assert any(r["severity"] == "warning" and r["category"] == "Payment" for r in results)
    print("✅ Chinese net 90 payment detected")


def test_work_for_hire():
    text = "All work product shall be work-made-for-hire."
    results = scan(text)
    assert len(results) == 1
    assert results[0]["severity"] == "warning"
    print("✅ work-for-hire detected")


def test_work_for_hire_zh():
    text = "乙方在工作期间完成的所有工作成果归甲方所有。"
    results = scan(text)
    assert any(r["severity"] == "warning" and r["category"] == "Intellectual Property" for r in results)
    print("✅ Chinese work-for-hire detected")


def test_no_termination():
    text = "This agreement may not be terminated except for material breach."
    results = scan(text)
    assert len(results) == 1
    assert results[0]["severity"] == "critical"
    print("✅ no termination for convenience detected")


def test_no_termination_zh():
    text = "除重大违约外，任何一方不得单方解除本合同。"
    results = scan(text)
    assert any(r["severity"] == "critical" and r["category"] == "Termination" for r in results)
    print("✅ Chinese no termination detected")


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


def test_multiple_risks_zh():
    text = (
        "合同到期后自动续签一年。"
        "乙方承担无限赔偿责任。"
        "付款期限为到货后 90 天内。"
        "所有工作成果归甲方所有。"
        "争议由甲方所在地法院管辖。"
    )
    results = scan(text)
    # At least 4 risks should be detected
    assert len(results) >= 4
    severities = [r["severity"] for r in results]
    assert severities.count("critical") >= 2  # auto-renew + liability + venue
    assert severities.count("warning") >= 1
    print(f"✅ Chinese multiple risks: {len(results)} detected")


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


def test_venue_zh():
    text = "争议由甲方所在地人民法院管辖。"
    results = scan(text)
    assert any(r["severity"] == "critical" and r["category"] == "Dispute" for r in results)
    print("✅ Chinese venue clause detected")


def test_perpetual_confidentiality():
    text = "All obligations shall survive in perpetuity."
    results = scan(text)
    assert len(results) == 1
    assert results[0]["severity"] == "warning"
    print("✅ perpetual confidentiality detected")


def test_perpetual_confidentiality_zh():
    text = "双方在合同终止后仍负有永久保密义务。"
    results = scan(text)
    assert any(r["severity"] == "warning" and r["category"] == "Confidentiality" for r in results)
    print("✅ Chinese perpetual confidentiality detected")


def test_broad_confidentiality_zh():
    text = "任何一方披露的所有信息均视为保密信息。"
    results = scan(text)
    assert any(r["severity"] == "warning" and r["category"] == "Confidentiality" for r in results)
    print("✅ Chinese broad confidentiality detected")


def test_broad_ip_zh():
    text = "乙方在工作期间产生的全部知识产权归甲方所有。"
    results = scan(text)
    assert any(r["severity"] == "warning" and r["category"] == "Intellectual Property" for r in results)
    print("✅ Chinese broad IP assignment detected")


def test_non_refundable_zh():
    text = "已付款项在任何情况下均不予退还。"
    results = scan(text)
    assert any(r["severity"] == "warning" and r["category"] == "Payment" for r in results)
    print("✅ Chinese non-refundable payment detected")


if __name__ == "__main__":
    test_names = [name for name in dir() if name.startswith("test_")]
    passed = 0
    failed = 0
    for name in sorted(test_names):
        try:
            globals()[name]()
            passed += 1
        except AssertionError as e:
            print(f"❌ {name} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {name} ERROR: {e}")
            failed += 1

    print(f"\n{'='*40}")
    print(f"✅ {passed} passed | ❌ {failed} failed | Total: {passed + failed}")
    if failed == 0:
        print("🎉 All tests passed!")

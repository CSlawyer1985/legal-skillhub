#!/usr/bin/env python3
"""
CementOps AI — Deterministic Environmental Reporting Obligation Checker
Version: 1.0.0

This script determines environmental reporting obligations. The LLM does NOT.

Usage:
    python3 check_reporting.py "event description"
    python3 check_reporting.py --test          # run self-test suite
    python3 check_reporting.py --list-rules    # print all rules

Returns: JSON with decision (REPORT, DOCUMENT, or MONITOR), triggered rules,
detected modifiers, and federal timelines.

Two-pass matching strategy:
  Pass 1 — Event Type: Match the base event against reporting rules
           (exceedance, CEMS outage, bypass, malfunction, NOV, etc.)
  Pass 2 — Modifiers: Detect context modifiers that escalate or change
           the obligation (during startup, bypass open, mercury)

Each modifier adds specific requirements to the base reporting obligation.

Fail-safe: If rules cannot be loaded, decision defaults to REPORT IMMEDIATELY.
"""
import json
import sys
import os
import re


def load_rules():
    """Load reporting rules from JSON. Fail-safe: default to REPORT."""
    rules_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reporting-rules.json")
    try:
        with open(rules_path, "r") as f:
            return json.load(f)
    except Exception as e:
        return {
            "error": True,
            "decision": "REPORT",
            "message": (
                f"REPORT IMMEDIATELY — UNABLE TO LOAD REPORTING RULES ({e}). "
                f"Notify your environmental compliance officer and permitting authority. "
                f"Do not assume no reporting is required."
            ),
        }


def tokenize(text):
    """Split text into lowercase word tokens."""
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def keyword_matches(keyword_phrase, event_tokens):
    """
    Check if a keyword phrase matches the event description.

    A keyword phrase matches if ALL words in the phrase appear
    in the event tokens (order-independent matching).
    """
    keyword_tokens = tokenize(keyword_phrase)
    if not keyword_tokens:
        return False
    return keyword_tokens.issubset(event_tokens)


def check_reporting(event_description):
    """
    Evaluate an environmental event against reporting obligation rules.

    Two-pass system:
      Pass 1: Match event against base reporting rules
      Pass 2: Detect modifiers that change the obligation

    Returns a dict with:
      - decision: "REPORT", "DOCUMENT", or "MONITOR"
      - triggered_rules: list of matched rules
      - modifiers_detected: list of applicable modifiers
      - federal_timelines: consolidated timeline requirements
      - state_note: reminder to check state-specific requirements
      - action: summary of what to do
    """
    rules_data = load_rules()

    # Fail-safe: if rules failed to load
    if rules_data.get("error"):
        return rules_data

    event_tokens = tokenize(event_description)

    # Pass 1: Event Type Detection
    triggered_rules = []
    for rule in rules_data.get("rules", []):
        keywords = rule.get("keywords", [])
        for keyword in keywords:
            if keyword_matches(keyword, event_tokens):
                triggered_rules.append(rule)
                break  # one match per rule is enough

    # Pass 2: Modifier Detection
    modifiers_detected = []
    for modifier in rules_data.get("modifiers", []):
        mod_keywords = modifier.get("keywords", [])
        for keyword in mod_keywords:
            if keyword_matches(keyword, event_tokens):
                modifiers_detected.append(modifier)
                break  # one match per modifier is enough

    if triggered_rules:
        # Determine highest-priority decision
        decisions = [r["decision"] for r in triggered_rules]
        if "REPORT" in decisions:
            final_decision = "REPORT"
        elif "DOCUMENT" in decisions:
            final_decision = "DOCUMENT"
        else:
            final_decision = "MONITOR"

        return {
            "decision": final_decision,
            "event_input": event_description,
            "triggered_rules": [
                {
                    "id": r["id"],
                    "condition": r["condition"],
                    "cfr_reference": r["cfr_reference"],
                    "federal_timeline": r["federal_timeline"],
                    "authority": r["authority"],
                    "message": r["message"],
                }
                for r in triggered_rules
            ],
            "modifiers_detected": [
                {
                    "id": m["id"],
                    "name": m["name"],
                    "effect": m["effect"],
                    "cfr_reference": m["cfr_reference"],
                }
                for m in modifiers_detected
            ],
            "federal_timelines": [r["federal_timeline"] for r in triggered_rules],
            "state_note": "Check your state permit for additional or shorter reporting deadlines. Federal timelines shown above are minimums.",
            "action": f"REPORTING OBLIGATION TRIGGERED — {len(triggered_rules)} rule(s) matched, {len(modifiers_detected)} modifier(s) detected.",
        }
    else:
        return {
            "decision": "MONITOR",
            "event_input": event_description,
            "note": "No reporting obligations triggered. Continue routine monitoring and documentation.",
            "modifiers_detected": [
                {
                    "id": m["id"],
                    "name": m["name"],
                    "effect": m["effect"],
                    "cfr_reference": m["cfr_reference"],
                }
                for m in modifiers_detected
            ],
            "reminder": "If conditions change or you are uncertain about reporting obligations, contact your environmental compliance officer. When in doubt, report.",
        }


def run_self_test():
    """Run built-in test cases to verify matching logic."""
    test_cases = [
        # (description, expected_decision, expected_rule_ids, expected_modifier_ids)

        # ER-001: Emission exceedance
        ("PM rolling average exceeded the NESHAP limit", "REPORT", ["ER-001"], []),
        ("SO2 emission limit exceedance on the kiln", "REPORT", ["ER-001"], []),
        ("CEMS shows we are above limit for NOx", "REPORT", ["ER-001"], []),

        # ER-001 + modifiers
        ("3 consecutive PM exceedances during startup bypass stack open", "REPORT", ["ER-001"], ["MOD-001", "MOD-002"]),
        ("emission exceedance during kiln startup", "REPORT", ["ER-001"], ["MOD-001"]),
        ("PM above limit with bypass stack open", "REPORT", ["ER-001"], ["MOD-002"]),
        ("mercury sorbent trap above limit", "REPORT", ["ER-001"], ["MOD-003"]),

        # ER-002: CEMS data availability below 90%
        ("CEMS data availability below 90 percent this quarter", "DOCUMENT", ["ER-002"], []),
        ("our cems downtime is getting high", "DOCUMENT", ["ER-002"], []),

        # ER-003: CEMS data availability below 75%
        ("CEMS data availability below 75 percent", "REPORT", ["ER-003"], []),
        ("CEMS has been offline for 3 days no data", "REPORT", ["ER-003"], []),

        # ER-004: Failed RATA
        ("our annual RATA failed on the SO2 analyzer", "REPORT", ["ER-004"], []),
        ("relative accuracy test did not pass", "REPORT", ["ER-004"], []),

        # ER-005: Bypass stack
        ("bypass stack was opened for 45 minutes during upset", "DOCUMENT", ["ER-005"], []),
        ("we had to divert to bypass during the kiln startup", "DOCUMENT", ["ER-005"], ["MOD-001"]),

        # ER-006: Malfunction
        ("equipment malfunction caused excess emissions from the kiln", "REPORT", ["ER-006"], []),
        ("sudden breakdown of the baghouse fan", "REPORT", ["ER-006"], []),
        ("process upset with visible emissions from stack", "REPORT", ["ER-006"], []),

        # ER-007: Stack test failure
        ("our annual stack test failed for PM", "REPORT", ["ER-007"], []),
        ("performance test results exceeded the limit", "REPORT", ["ER-007"], []),

        # ER-008: NOV received
        ("we just received a notice of violation from the state", "REPORT", ["ER-008"], []),
        ("EPA sent us an enforcement action letter", "REPORT", ["ER-008"], []),

        # ER-009: Opacity
        ("opacity reading hit 25 percent on the COM", "REPORT", ["ER-009"], []),
        ("visible emissions from the kiln stack opacity alarm", "REPORT", ["ER-009"], []),

        # ER-010: Hazardous waste fuel
        ("hazardous waste fuel feed rate deviation", "REPORT", ["ER-010"], []),

        # Compound scenarios
        ("kiln malfunction during startup with bypass open and mercury above limit", "REPORT", ["ER-006"], ["MOD-001", "MOD-002", "MOD-003"]),

        # These should NOT trigger reporting
        ("what are the NESHAP limits for PM at cement plants", "MONITOR", [], []),
        ("when is our next stack test scheduled", "MONITOR", [], []),
        ("explain the RATA procedure for our SO2 CEMS", "MONITOR", [], []),
        ("what PPE is needed for CEMS calibration gas handling", "MONITOR", [], []),
        ("routine daily calibration check passed", "MONITOR", [], []),
    ]

    passed = 0
    failed = 0
    errors = []

    for test in test_cases:
        description, expected_decision, expected_rule_ids, expected_mod_ids = test
        result = check_reporting(description)
        actual_decision = result["decision"]

        # Check decision
        if actual_decision != expected_decision:
            failed += 1
            actual_rule_ids = [r["id"] for r in result.get("triggered_rules", [])]
            errors.append(
                f"  FAIL (decision): \"{description}\"\n"
                f"    Expected: {expected_decision} rules={expected_rule_ids}\n"
                f"    Got:      {actual_decision} rules={actual_rule_ids}"
            )
            continue

        # Check rule IDs (at least one expected rule must be present)
        if expected_rule_ids:
            actual_rule_ids = [r["id"] for r in result.get("triggered_rules", [])]
            if not any(eid in actual_rule_ids for eid in expected_rule_ids):
                failed += 1
                errors.append(
                    f"  FAIL (wrong rule): \"{description}\"\n"
                    f"    Expected rule: {expected_rule_ids}\n"
                    f"    Got rules:     {actual_rule_ids}"
                )
                continue

        # Check modifier IDs (all expected modifiers must be present)
        if expected_mod_ids:
            actual_mod_ids = [m["id"] for m in result.get("modifiers_detected", [])]
            missing_mods = [m for m in expected_mod_ids if m not in actual_mod_ids]
            if missing_mods:
                failed += 1
                errors.append(
                    f"  FAIL (missing modifier): \"{description}\"\n"
                    f"    Expected modifiers: {expected_mod_ids}\n"
                    f"    Got modifiers:      {actual_mod_ids}\n"
                    f"    Missing:            {missing_mods}"
                )
                continue

        passed += 1

    total = passed + failed
    print(f"Reporting Obligation Self-Test Results: {passed}/{total} passed")
    if errors:
        print(f"\nFailures ({failed}):")
        for e in errors:
            print(e)
        return False
    else:
        print("All tests passed.")
        return True


def list_rules():
    """Print all reporting rules in a readable format."""
    rules_data = load_rules()
    if rules_data.get("error"):
        print(json.dumps(rules_data, indent=2))
        return

    rules = rules_data.get("rules", [])
    modifiers = rules_data.get("modifiers", [])

    print(f"Reporting Rules: {len(rules)} rules loaded\n")
    for rule in rules:
        print(f"  {rule['id']}: {rule['condition']}")
        print(f"    Decision: {rule['decision']}")
        print(f"    CFR: {rule['cfr_reference']}")
        print(f"    Timeline: {rule['federal_timeline']}")
        print(f"    Keywords: {len(rule['keywords'])} phrases")
        print()

    print(f"Modifiers: {len(modifiers)} modifiers loaded\n")
    for mod in modifiers:
        print(f"  {mod['id']} ({mod['name']}): {mod['effect'][:80]}...")
        print(f"    CFR: {mod['cfr_reference']}")
        print(f"    Keywords: {len(mod['keywords'])} phrases")
        print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python3 check_reporting.py 'event description'"}))
        sys.exit(1)

    if sys.argv[1] == "--test":
        success = run_self_test()
        sys.exit(0 if success else 1)
    elif sys.argv[1] == "--list-rules":
        list_rules()
        sys.exit(0)
    else:
        description = " ".join(sys.argv[1:])
        result = check_reporting(description)
        print(json.dumps(result, indent=2))

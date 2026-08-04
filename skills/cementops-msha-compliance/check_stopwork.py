#!/usr/bin/env python3
"""
CementOps AI — Deterministic Stop-Work Gate
Version: 1.1.0

This script makes stop-work decisions. The LLM does NOT.

Usage:
    python3 check_stopwork.py "hazard description"
    python3 check_stopwork.py --test          # run self-test suite
    python3 check_stopwork.py --list-rules    # print all rules

Returns: JSON with decision (STOP_WORK or CONTINUE) and details.

Matching strategy:
  - Each rule has a list of keyword phrases
  - A keyword matches if ALL words in the keyword appear in the hazard
    description (in any order) — this is word-set matching, not substring
  - Single-word keywords match if that word appears anywhere
  - This prevents false negatives from word-order differences
    ("belt exposed" matches "exposed belt", "guard fell off" matches
     "the guard fell off the pulley")

Fail-safe: If rules cannot be loaded, decision defaults to STOP_WORK.
"""
import json
import sys
import os
import re


def load_rules():
    """Load stop-work rules from JSON. Fail-safe: default to STOP_WORK."""
    rules_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stop-work-rules.json")
    try:
        with open(rules_path, "r") as f:
            return json.load(f)
    except Exception as e:
        return {
            "error": True,
            "decision": "STOP_WORK",
            "message": (
                f"STOP WORK — UNABLE TO LOAD SAFETY RULES ({e}). "
                f"Contact supervisor immediately. Do not resume work."
            ),
        }


def tokenize(text):
    """Split text into lowercase word tokens."""
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def keyword_matches(keyword_phrase, hazard_tokens):
    """
    Check if a keyword phrase matches the hazard description.

    A keyword phrase matches if ALL words in the phrase appear
    in the hazard tokens. This handles word-order differences:
      keyword "exposed belt" matches "the belt is exposed"
      keyword "no guard" matches "there's no guard on it"
      keyword "guard fell" matches "the guard fell off"
    """
    keyword_tokens = tokenize(keyword_phrase)
    if not keyword_tokens:
        return False
    return keyword_tokens.issubset(hazard_tokens)


def check_stopwork(hazard_description):
    """
    Evaluate a hazard description against stop-work rules.

    Returns a dict with:
      - decision: "STOP_WORK" or "CONTINUE"
      - triggered_rules: list of matched rules (if STOP_WORK)
      - note/reminder: guidance text (if CONTINUE)
    """
    rules_data = load_rules()

    # Fail-safe: if rules failed to load
    if rules_data.get("error"):
        return rules_data

    hazard_tokens = tokenize(hazard_description)
    triggered_rules = []

    for rule in rules_data.get("rules", []):
        keywords = rule.get("keywords", [])
        for keyword in keywords:
            if keyword_matches(keyword, hazard_tokens):
                triggered_rules.append(rule)
                break  # one match per rule is enough

    if triggered_rules:
        return {
            "decision": "STOP_WORK",
            "hazard_input": hazard_description,
            "triggered_rules": [
                {
                    "id": r["id"],
                    "condition": r["condition"],
                    "cfr_reference": r["cfr_reference"],
                    "severity": r["severity"],
                    "message": r["message"],
                }
                for r in triggered_rules
            ],
            "action": "ISSUE STOP-WORK DIRECTIVE IMMEDIATELY",
            "follow_up": "Do not resume work until supervisor and safety manager have assessed and cleared the area.",
        }
    else:
        return {
            "decision": "CONTINUE",
            "hazard_input": hazard_description,
            "note": "No imminent danger conditions matched. Proceed with standard hazard classification and controls.",
            "reminder": "If conditions change or you are uncertain, re-evaluate. When in doubt, stop work and escalate.",
        }


def run_self_test():
    """Run built-in test cases to verify matching logic."""
    test_cases = [
        # (description, expected_decision, expected_rule_ids_or_none)
        ("rotating shaft with no guard and people walking past", "STOP_WORK", ["SW-001"]),
        ("the guard fell off the head pulley", "STOP_WORK", ["SW-001"]),
        ("belt is exposed on the conveyor", "STOP_WORK", ["SW-001"]),
        ("worker reached into the crusher", "STOP_WORK", ["SW-001"]),
        ("missing guard on the tail pulley", "STOP_WORK", ["SW-001"]),
        ("no fall protection on the preheater tower", "STOP_WORK", ["SW-002"]),
        ("guardrail missing on the platform", "STOP_WORK", ["SW-002"]),
        ("guy not tied off working on the silo top", "STOP_WORK", ["SW-002"]),
        ("maintenance on the mill but lockout not applied", "STOP_WORK", ["SW-003"]),
        ("someone working on live equipment in the MCC", "STOP_WORK", ["SW-003"]),
        ("didn't lock out before changing the belt", "STOP_WORK", ["SW-003"]),
        ("went into the silo without a permit", "STOP_WORK", ["SW-004"]),
        ("entered the bin without atmospheric testing", "STOP_WORK", ["SW-004"]),
        ("silo wall has a visible crack", "STOP_WORK", ["SW-005"]),
        ("gas alarm going off in the preheater", "STOP_WORK", ["SW-006"]),
        ("can't breathe near the kiln hood", "STOP_WORK", ["SW-006"]),
        ("arc flash risk at open panel no PPE", "STOP_WORK", ["SW-007"]),
        ("kiln shell has a red spot glowing", "STOP_WORK", ["SW-008"]),
        ("hot clinker spilled on the floor near the cooler", "STOP_WORK", ["SW-009"]),
        ("coal dust concentration alarm in the mill", "STOP_WORK", ["SW-010"]),
        ("loader backing up no alarm people behind it", "STOP_WORK", ["SW-011"]),
        ("crane lifting over people below", "STOP_WORK", ["SW-012"]),
        ("scaffold has no inspection tag", "STOP_WORK", ["SW-013"]),
        ("acid spill in the lab", "STOP_WORK", ["SW-014"]),
        ("conveyor belt on fire in gallery 7", "STOP_WORK", ["SW-015"]),
        ("smoke coming from the baghouse", "STOP_WORK", ["SW-015"]),
        ("trench dug out back with no shoring", "STOP_WORK", ["SW-016"]),
        ("someone trapped in the conveyor", "STOP_WORK", ["SW-017"]),
        ("worker got shocked touching the motor", "STOP_WORK", ["SW-018"]),
        ("hissing from the high pressure line", "STOP_WORK", ["SW-019"]),
        ("people in the blast zone quarry", "STOP_WORK", ["SW-020"]),
        ("preheater cyclone is plugged and guys are poking it from below", "STOP_WORK", ["SW-021"]),
        ("buildup collapsed in the preheater", "STOP_WORK", ["SW-021"]),
        ("hydraulic line sprayed fluid and hit a worker's hand — pinhole leak", "STOP_WORK", ["SW-022"]),
        ("kiln coating ring collapsed during operation", "STOP_WORK", ["SW-023"]),
        ("maintenance crew entering cooler undergrate area but cooler is still hot", "STOP_WORK", ["SW-024"]),
        ("water leaking onto the quicklime pile and it's steaming", "STOP_WORK", ["SW-025"]),
        # These should NOT trigger stop-work
        ("dust accumulation on walkway near raw mill", "CONTINUE", None),
        ("need to order replacement light bulbs for stairway", "CONTINUE", None),
        ("what are the PPE requirements for the packing plant", "CONTINUE", None),
        ("explain 30 CFR 56.14107", "CONTINUE", None),
        ("housekeeping needs attention in the crusher building", "CONTINUE", None),
        ("the annual hearing test results are back for day shift", "CONTINUE", None),
        ("we need to schedule the annual crane inspection", "CONTINUE", None),
        ("the guard on conveyor 5 looks good after the repair", "CONTINUE", None),
        ("training records are up to date for all shifts", "CONTINUE", None),
        ("what is the penalty for a housekeeping citation", "CONTINUE", None),
    ]

    passed = 0
    failed = 0
    errors = []

    for description, expected_decision, expected_ids in test_cases:
        result = check_stopwork(description)
        actual_decision = result["decision"]

        if actual_decision != expected_decision:
            failed += 1
            actual_ids = [r["id"] for r in result.get("triggered_rules", [])]
            errors.append(
                f"  FAIL: \"{description}\"\n"
                f"    Expected: {expected_decision} {expected_ids or ''}\n"
                f"    Got:      {actual_decision} {actual_ids}"
            )
        else:
            if expected_ids and actual_decision == "STOP_WORK":
                actual_ids = [r["id"] for r in result.get("triggered_rules", [])]
                if not any(eid in actual_ids for eid in expected_ids):
                    failed += 1
                    errors.append(
                        f"  FAIL (wrong rule): \"{description}\"\n"
                        f"    Expected rule: {expected_ids}\n"
                        f"    Got rules:     {actual_ids}"
                    )
                else:
                    passed += 1
            else:
                passed += 1

    print(f"Stop-Work Self-Test Results: {passed}/{passed + failed} passed")
    if errors:
        print("\nFailures:")
        for e in errors:
            print(e)
        return False
    else:
        print("All tests passed.")
        return True


def list_rules():
    """Print all stop-work rules in a readable format."""
    rules_data = load_rules()
    if rules_data.get("error"):
        print(json.dumps(rules_data, indent=2))
        return

    rules = rules_data.get("rules", [])
    print(f"Stop-Work Rules: {len(rules)} rules loaded\n")
    for rule in rules:
        print(f"  {rule['id']}: {rule['condition']}")
        print(f"    CFR: {rule['cfr_reference']}")
        print(f"    Keywords: {len(rule['keywords'])} phrases")
        print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python3 check_stopwork.py 'hazard description'"}))
        sys.exit(1)

    if sys.argv[1] == "--test":
        success = run_self_test()
        sys.exit(0 if success else 1)
    elif sys.argv[1] == "--list-rules":
        list_rules()
        sys.exit(0)
    else:
        description = " ".join(sys.argv[1:])
        result = check_stopwork(description)
        print(json.dumps(result, indent=2))

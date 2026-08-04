import json
import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_output.py"
VALID_SAMPLE = ROOT / "tests" / "sample-valid-output.md"
INVALID_SAMPLE = ROOT / "tests" / "sample-invalid-output.md"
CONTRACT = ROOT / "references" / "output-contract.json"
CASES = ROOT / "tests" / "cases.json"
SKILL_FILE = ROOT / "SKILL.md"
OPENAI_YAML = ROOT / "agents" / "openai.yaml"
OUTPUT_TEMPLATE = ROOT / "assets" / "output-template.md"


def run_validator(sample: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), "--check-output", str(sample)],
        check=False,
        capture_output=True,
        text=True,
    )


class ValidatorTests(unittest.TestCase):
    def test_valid_sample_passes(self) -> None:
        result = run_validator(VALID_SAMPLE)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS", result.stdout)

    def test_invalid_sample_fails(self) -> None:
        result = run_validator(INVALID_SAMPLE)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FAIL", result.stderr)
        self.assertIn("包含禁止表达", result.stderr)

    def test_contract_targets_this_skill(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        skill_text = SKILL_FILE.read_text(encoding="utf-8")
        name_match = re.search(r"^name:\s*([^\s]+)\s*$", skill_text, re.MULTILINE)
        self.assertIsNotNone(name_match)
        self.assertEqual(contract["skill_id"], name_match.group(1))
        self.assertEqual(len(contract["required_headings"]), 6)
        self.assertGreaterEqual(len(contract["required_terms"]), 10)

    def test_route_cases_cover_four_modes_and_handoff(self) -> None:
        cases = json.loads(CASES.read_text(encoding="utf-8"))
        modes = {case["expected_mode"] for case in cases}
        expected = set(json.loads(CONTRACT.read_text(encoding="utf-8"))["modes"])
        self.assertTrue(expected.issubset(modes))
        self.assertIn('转交公司法务或持证法律顾问', modes)

    def test_skill_has_no_initializer_placeholders(self) -> None:
        text = SKILL_FILE.read_text(encoding="utf-8")
        self.assertNotIn("TODO", text)
        self.assertIn("name: contract-obligation-risk-manager", text)

    def test_default_prompt_mentions_skill(self) -> None:
        text = OPENAI_YAML.read_text(encoding="utf-8")
        self.assertIn("$contract-obligation-risk-manager", text)

    def test_output_template_matches_contract_headings(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        text = OUTPUT_TEMPLATE.read_text(encoding="utf-8")
        positions = [text.find(heading) for heading in contract["required_headings"]]
        self.assertTrue(all(position >= 0 for position in positions))
        self.assertEqual(positions, sorted(positions))


if __name__ == "__main__":
    unittest.main()

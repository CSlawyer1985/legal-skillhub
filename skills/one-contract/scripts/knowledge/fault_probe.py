#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory
import argparse
import shutil
import sys


SKILL_ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser(description="Inject a privacy leak and require the independent validator to block it.")
    parser.add_argument("--case", choices=["privacy-path"], required=True)
    parser.parse_args()
    with TemporaryDirectory(prefix="one-contract-fault-") as temp:
        fixture = Path(temp) / "candidate"
        shutil.copytree(SKILL_ROOT / "assets", fixture / "assets")
        (fixture / "fixture.md").write_text("source=" + "/" + "Users/example/contracts/raw.docx\n", encoding="utf-8")
        completed = run(
            [
                sys.executable,
                str(SKILL_ROOT / "scripts/knowledge/validate_assets.py"),
                "--skill-root",
                str(fixture),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        sys.stdout.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())

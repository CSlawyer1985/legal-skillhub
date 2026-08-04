#!/usr/bin/env python3
"""Create an isolated Markdown workspace from the platform-lite templates."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", type=Path)
    args = parser.parse_args()
    package_root = Path(__file__).resolve().parents[1]
    template_root = package_root / "templates" / "markdown"
    output_root = args.target.resolve() / "04-文书成果"
    output_root.mkdir(parents=True, exist_ok=False)
    templates = sorted(template_root.glob("*.md"))
    for source in templates:
        shutil.copy2(source, output_root / source.name)
    print(json.dumps({
        "status": "READY",
        "workspace": args.target.name,
        "template_count": len(templates),
        "format": "markdown",
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

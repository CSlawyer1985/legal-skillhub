#!/usr/bin/env python3
"""Merge structured additions while preserving existing non-empty values."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any


EMPTY_MARKERS = {
    "",
    " ",
    "TO" + "DO",
    "TB" + "D",
    "FIX" + "ME",
    "\u5f85\u8865\u5145",
    "\u5f85\u786e\u8ba4",
}


def is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() in EMPTY_MARKERS
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


def merge_without_overwrite(base: Any, addition: Any) -> Any:
    if is_empty(base):
        return deepcopy(addition)
    if isinstance(base, dict) and isinstance(addition, dict):
        merged = deepcopy(base)
        for key, value in addition.items():
            if key in merged:
                merged[key] = merge_without_overwrite(merged[key], value)
            else:
                merged[key] = deepcopy(value)
        return merged
    if isinstance(base, list) and isinstance(addition, list):
        merged = deepcopy(base)
        seen = {json.dumps(item, ensure_ascii=False, sort_keys=True) for item in merged}
        for item in addition:
            marker = json.dumps(item, ensure_ascii=False, sort_keys=True)
            if marker not in seen:
                merged.append(deepcopy(item))
                seen.add(marker)
        return merged
    return deepcopy(base)


def self_test() -> int:
    base = {
        "handler": {"name": "既有公司", "contact": ""},
        "functions": [{"name": "注册", "data": ["手机号码"]}],
    }
    addition = {
        "handler": {"name": "新公司", "contact": "privacy@example.com"},
        "functions": [
            {"name": "注册", "data": ["手机号码"]},
            {"name": "客服", "data": ["沟通记录"]},
        ],
    }
    merged = merge_without_overwrite(base, addition)
    ok = (
        merged["handler"]["name"] == "既有公司"
        and merged["handler"]["contact"] == "privacy@example.com"
        and len(merged["functions"]) == 2
    )
    print(json.dumps(merged, ensure_ascii=False, indent=2))
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge JSON without overwriting existing values.")
    parser.add_argument("base", nargs="?", help="Existing JSON file.")
    parser.add_argument("addition", nargs="?", help="JSON file with additions.")
    parser.add_argument("--out", help="Output path. Defaults to stdout.")
    parser.add_argument("--self-test", action="store_true", help="Run a built-in smoke test.")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if not args.base or not args.addition:
        parser.error("base and addition are required unless --self-test is used")

    base = json.loads(Path(args.base).read_text(encoding="utf-8"))
    addition = json.loads(Path(args.addition).read_text(encoding="utf-8"))
    merged = merge_without_overwrite(base, addition)
    text = json.dumps(merged, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

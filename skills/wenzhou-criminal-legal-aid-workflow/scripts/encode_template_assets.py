#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import textwrap
from pathlib import Path


def encode_pack(root: Path) -> int:
    root = root.resolve()
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    mapping = manifest.get("templates")
    if not isinstance(mapping, dict):
        raise ValueError("manifest.json 的 templates 必须是对象。")
    count = 0
    for name in sorted(set(str(value) for value in mapping.values())):
        source = (root / name).resolve()
        if root not in source.parents or not source.is_file():
            raise ValueError(f"模板文件不存在或越出模板包：{name}")
        encoded = source.with_name(source.name + ".b64.txt")
        value = base64.b64encode(source.read_bytes()).decode("ascii")
        encoded.write_text("\n".join(textwrap.wrap(value, width=76)) + "\n", encoding="ascii")
        print(f"ENCODED: {source.name} -> {encoded.name}")
        count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Encode OOXML templates for registries that filter binary assets.")
    parser.add_argument("template_pack", type=Path)
    args = parser.parse_args()
    print(f"PASS: encoded {encode_pack(args.template_pack)} template assets")


if __name__ == "__main__":
    main()

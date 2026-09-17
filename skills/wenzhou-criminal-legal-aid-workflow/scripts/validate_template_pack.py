#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_criminal_legal_aid_set import REQUIRED_TEMPLATE_KEYS, load_template_pack


def validate(root: Path) -> list[str]:
    """与实际生成共用模板契约校验，避免校验通过但生成时采用另一套规则。"""
    root = root.resolve()
    try:
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            return ["manifest.json 必须是对象。"]
        errors = []
        for field in ("id", "display_name", "jurisdiction", "version", "source_notice"):
            if not str(manifest.get(field, "")).strip():
                errors.append(f"manifest 缺少字段：{field}")
        centers = manifest.get("assigning_institutions")
        if not isinstance(centers, list) or not centers:
            errors.append('assigning_institutions 必须是非空数组；通用包可使用 ["*"]。')
        mapping = manifest.get("templates")
        if isinstance(mapping, dict) and set(mapping) - REQUIRED_TEMPLATE_KEYS:
            errors.append("templates 包含未知模板键。")
        load_template_pack("", str(root))
        return errors
    except Exception as exc:
        return [f"模板包无法通过校验：{exc}"]


def main() -> None:
    parser = argparse.ArgumentParser(description="验证刑事法律援助模板包。")
    parser.add_argument("template_pack", type=Path)
    args = parser.parse_args()
    errors = validate(args.template_pack)
    if errors:
        raise SystemExit("模板包验证失败：\n- " + "\n- ".join(errors))
    print(f"PASS: {args.template_pack}")


if __name__ == "__main__":
    main()

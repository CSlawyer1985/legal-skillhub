#!/usr/bin/env python3
"""
Validate JSON file against schema.
Requires jsonschema package (optional fallback message if missing).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description="Schema validator")
    ap.add_argument("--input", required=True)
    ap.add_argument("--schema", required=True)
    args = ap.parse_args()

    input_path = Path(args.input).resolve()
    schema_path = Path(args.schema).resolve()

    data = json.loads(input_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    try:
        import jsonschema  # type: ignore
    except Exception:
        raise SystemExit("missing dependency: pip install jsonschema")

    jsonschema.validate(instance=data, schema=schema)
    print("OK")


if __name__ == "__main__":
    main()

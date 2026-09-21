#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Migrate legacy Zhilu intake_state.json to Phase 1 intake_state_v2.json.

Pure local and idempotent. It never deletes or overwrites the v1 state file.
"""
import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


REQUIRED_V2_KEYS = {"schema_version", "mode", "sources", "legacy", "shadow"}


def validate_v2(current):
    sources = current.get("sources", {})
    valid_sources = all(
        name in sources and isinstance(sources[name].get("high_watermark"), dict)
        for name in ("market_group", "service_group")
    )
    shadow = current.get("shadow", {})
    safe_shadow = (
        shadow.get("enabled") is True
        and shadow.get("write_main_ledger") is False
        and shadow.get("auto_close") is False
        and shadow.get("auto_reopen") is False
    )
    return current.get("schema_version") == 2 and REQUIRED_V2_KEYS.issubset(current) and valid_sources and safe_shadow


def migrate(v1):
    media_ids = list(dict.fromkeys(v1.get("processed_media_ids", [])))
    known = {"checkpoint", "checkpoint2", "processed_media_ids", "note"}
    unknown = {key: value for key, value in v1.items() if key not in known}
    return {
        "schema_version": 2,
        "mode": "shadow",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "market_group": {
                "high_watermark": {"sent_at": v1.get("checkpoint", ""), "message_id": ""},
                "overlap_minutes": 10,
            },
            "service_group": {
                "high_watermark": {"sent_at": v1.get("checkpoint2", ""), "message_id": ""},
                "overlap_minutes": 10,
            },
        },
        "legacy": {
            "checkpoint": v1.get("checkpoint", ""),
            "checkpoint2": v1.get("checkpoint2", ""),
            "processed_media_ids": media_ids,
            "note": v1.get("note", ""),
            "unknown_fields": unknown,
        },
        "last_batch_id": None,
        "recent_events": {},
        "event_table_cursor": None,
        "shadow": {
            "enabled": True,
            "write_main_ledger": False,
            "auto_close": False,
            "auto_reopen": False,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    src, dst = Path(args.input), Path(args.output)
    if dst.exists():
        current = json.loads(dst.read_text(encoding="utf-8"))
        if validate_v2(current):
            print(json.dumps({"status": "unchanged", "output": str(dst)}, ensure_ascii=False))
            return 0
        raise SystemExit("output exists but is incomplete or not a valid v2 state")
    v1 = json.loads(src.read_text(encoding="utf-8"))
    payload = json.dumps(migrate(v1), ensure_ascii=False, indent=2) + "\n"
    dst.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=dst.name + ".", suffix=".tmp", dir=str(dst.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, dst)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
    print(json.dumps({"status": "created", "output": str(dst)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

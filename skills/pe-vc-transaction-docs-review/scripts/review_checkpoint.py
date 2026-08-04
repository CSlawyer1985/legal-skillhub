#!/usr/bin/env python3
"""Create and resume a minimal, reversible PE/VC review progress record."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


STAGES = (
    "intake",
    "document_map",
    "text_extraction",
    "package_analysis",
    "output_language",
    "track_changes",
    "version_chain",
    "connectors",
    "structure_playbook",
    "clause_review",
    "market_context",
    "legal_authority",
    "party_position",
    "deliverables",
    "major_issue_list",
    "validation",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def fingerprint(path: Path) -> dict[str, object]:
    resolved = path.expanduser().resolve()
    digest = hashlib.sha256()
    with resolved.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    stat = resolved.stat()
    return {
        "path": str(resolved),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": digest.hexdigest(),
    }


def source_records(paths: list[Path]) -> list[dict[str, object]]:
    return [fingerprint(path) for path in sorted(paths, key=lambda item: str(item))]


def load_state(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"CHECKPOINT-READ-001: could not read state: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("CHECKPOINT-READ-002: unsupported or invalid state schema")
    return payload


def write_state(path: Path, payload: dict[str, object], *, backup: bool = True) -> None:
    path = path.expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    if backup and path.exists():
        shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
    payload["updated_at"] = now()
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def new_state(matter_id: str, sources: list[Path]) -> dict[str, object]:
    timestamp = now()
    return {
        "schema_version": 1,
        "matter_id": matter_id,
        "created_at": timestamp,
        "updated_at": timestamp,
        "source_files": source_records(sources),
        "stages": {stage: {"status": "pending", "updated_at": None} for stage in STAGES},
        "artifacts": [],
        "last_error": None,
        "privacy_note": "Stores file fingerprints, stable unit IDs, progress, and artifact paths only; no contract text or review conclusions.",
    }


def changed_sources(stored: object, current: list[dict[str, object]]) -> bool:
    return stored != current


def invalidate_after_source_change(state: dict[str, object]) -> None:
    stages = state.get("stages", {})
    if not isinstance(stages, dict):
        return
    for stage in STAGES[1:]:
        record = stages.get(stage)
        if isinstance(record, dict) and record.get("status") in {
            "completed",
            "completed_with_limitations",
            "not_applicable",
            "in_progress",
        }:
            record["status"] = "stale"
            record["updated_at"] = now()
    state["last_error"] = {
        "code": "CHECKPOINT-SOURCE-001",
        "message": "Source files changed; dependent stages require revalidation.",
        "updated_at": now(),
    }


def next_stage(state: dict[str, object]) -> str | None:
    stages = state.get("stages", {})
    if not isinstance(stages, dict):
        return STAGES[0]
    for stage in STAGES:
        record = stages.get(stage)
        if not isinstance(record, dict) or record.get("status") != "completed":
            return stage
    return None


def print_summary(state: dict[str, object]) -> None:
    print(json.dumps({
        "matter_id": state.get("matter_id"),
        "next_stage": next_stage(state),
        "stages": state.get("stages"),
        "artifacts": state.get("artifacts"),
        "last_error": state.get("last_error"),
        "updated_at": state.get("updated_at"),
    }, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    init.add_argument("output", type=Path)
    init.add_argument("--matter-id", required=True)
    init.add_argument("--source", type=Path, nargs="*", default=[])

    for name in ("status", "resume"):
        command = sub.add_parser(name)
        command.add_argument("state", type=Path)
        command.add_argument("--source", type=Path, nargs="*", default=None)

    complete = sub.add_parser("complete")
    complete.add_argument("state", type=Path)
    complete.add_argument("stage", choices=STAGES)
    complete.add_argument("--artifact", action="append", default=[])
    complete.add_argument("--limitation")

    skip = sub.add_parser("skip")
    skip.add_argument("state", type=Path)
    skip.add_argument("stage", choices=STAGES)
    skip.add_argument("--reason", required=True)

    autosave = sub.add_parser("autosave")
    autosave.add_argument("state", type=Path)
    autosave.add_argument("stage", choices=STAGES)
    autosave.add_argument("--unit", action="append", default=[])
    autosave.add_argument("--artifact", action="append", default=[])

    fail = sub.add_parser("fail")
    fail.add_argument("state", type=Path)
    fail.add_argument("stage", choices=STAGES)
    fail.add_argument("--message", required=True)

    rollback = sub.add_parser("rollback")
    rollback.add_argument("state", type=Path)

    args = parser.parse_args()
    try:
        if args.command == "init":
            state = new_state(args.matter_id, args.source)
            write_state(args.output, state, backup=False)
        elif args.command == "rollback":
            backup = args.state.with_suffix(args.state.suffix + ".bak")
            state = load_state(backup)
            write_state(args.state, state, backup=False)
        else:
            state = load_state(args.state)
            if args.command in {"status", "resume"} and args.source is not None:
                current = source_records(args.source)
                if changed_sources(state.get("source_files"), current):
                    invalidate_after_source_change(state)
                    state["source_files"] = current
                    write_state(args.state, state)
            elif args.command in {"complete", "autosave"}:
                existing = state["stages"].get(args.stage, {})
                completed_units = list(existing.get("completed_units", [])) if isinstance(existing, dict) else []
                if args.command == "autosave":
                    for unit in args.unit:
                        if unit not in completed_units:
                            completed_units.append(unit)
                state["stages"][args.stage] = {
                    "status": (
                        "completed_with_limitations"
                        if args.command == "complete" and args.limitation
                        else ("completed" if args.command == "complete" else "in_progress")
                    ),
                    "updated_at": now(),
                    "completed_units": completed_units,
                }
                if args.command == "complete" and args.limitation:
                    state["stages"][args.stage]["limitation"] = args.limitation
                artifacts = state.setdefault("artifacts", [])
                for artifact in args.artifact:
                    if artifact not in artifacts:
                        artifacts.append(artifact)
                state["last_error"] = None
                write_state(args.state, state)
            elif args.command == "skip":
                state["stages"][args.stage] = {
                    "status": "not_applicable",
                    "updated_at": now(),
                    "reason": args.reason,
                }
                state["last_error"] = None
                write_state(args.state, state)
            elif args.command == "fail":
                state["stages"][args.stage] = {"status": "failed", "updated_at": now()}
                state["last_error"] = {
                    "code": "CHECKPOINT-STAGE-001",
                    "stage": args.stage,
                    "message": args.message,
                    "updated_at": now(),
                }
                write_state(args.state, state)
        print_summary(state)
        return 0
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

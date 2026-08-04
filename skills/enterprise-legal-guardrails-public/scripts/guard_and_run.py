#!/usr/bin/env python3
"""Run enterprise guardrails on draft text, then execute a command.

This is a generic adapter for outbound/public-facing workflows that do not yet
have native enterprise guardrail wiring.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


CHECKER_SCRIPT = Path(__file__).resolve().parent / "check_enterprise_guardrails.py"


def _get_env(*names: str) -> str | None:
    for name in names:
        value = os.environ.get(name)
        if value is not None:
            return value
    return None


def _get_env_bool(*names: str, default: bool = False) -> bool:
    raw = _get_env(*names)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _get_env_int(*names: str, default: int) -> int:
    raw = _get_env(*names)
    if raw is None:
        return default
    try:
        return int(raw.strip())
    except ValueError:
        return default


def _split_csv(raw: str | None) -> list[str]:
    if not raw:
        return []
    parts: list[str] = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if chunk:
            parts.append(chunk)
    return parts


def _read_text(text: str | None, text_file: str | None) -> str:
    if text is not None:
        return text.strip()
    if text_file is not None:
        return Path(text_file).read_text(encoding="utf-8").strip()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    raise ValueError("No text to validate. Use --text, --text-file, or stdin.")


def _extract_json(payload: str) -> dict:
    body = (payload or "").strip()
    if not body:
        raise RuntimeError("Guardrail check returned no output.")

    # Accept JSON output directly and try last JSON object in mixed output as fallback.
    candidates = [body]
    first_brace = body.find("{")
    last_brace = body.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        candidates.append(body[first_brace : last_brace + 1])

    for candidate in candidates:
        candidate = candidate.strip()
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data

    raise RuntimeError("Guardrail checker output invalid JSON.")


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def _hash_command(command: list[str]) -> str:
    joined = "\x00".join(command)
    return hashlib.sha256(joined.encode("utf-8", errors="ignore").strip()).hexdigest()


def _fingerprint_token(token: str | None) -> str:
    if not token:
        return ""
    return hashlib.sha256(token.encode("utf-8", errors="ignore").strip()).hexdigest()[:12]


def _command_repr(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def _is_allowed(command: list[str], allowed: list[str]) -> bool:
    if not allowed:
        return True

    target = command[0]
    target_name = Path(target).name
    target_lower = target.lower()
    target_name_lower = target_name.lower()

    for pattern in allowed:
        if not pattern:
            continue
        pattern = pattern.strip()
        if not pattern:
            continue

        candidate = pattern.lower()
        if candidate.startswith("regex:"):
            expr = candidate.split(":", 1)[1]
            try:
                if re.fullmatch(expr, target_lower):
                    return True
            except re.error as exc:
                raise RuntimeError(f"Invalid regex allowlist pattern '{pattern}': {exc}") from exc
            continue

        if fnmatch.fnmatch(target_lower, candidate) or fnmatch.fnmatch(target_name_lower, candidate):
            return True
        if Path(pattern).is_absolute():
            try:
                if Path(target).resolve() == Path(pattern).resolve():
                    return True
            except OSError:
                if target_lower == pattern.lower():
                    return True
        elif target_lower == pattern.lower() or target_name_lower == pattern.lower():
            return True

    return False


def _sanitize_env(keep_exact: list[str], keep_prefixes: list[str]) -> dict[str, str]:
    base = {"PATH", "HOME", "TMPDIR", "TMP", "TEMP", "USER", "LANG", "LC_ALL", "LC_CTYPE", "TERM", "SHELL", "PYTHONIOENCODING"}
    env: dict[str, str] = {}

    for key in base:
        value = os.environ.get(key)
        if value is not None:
            env[key] = value

    for key in keep_exact:
        value = os.environ.get(key)
        if value is not None:
            env[key] = value

    for prefix in keep_prefixes:
        prefix = prefix.strip()
        if not prefix:
            continue
        for key, value in os.environ.items():
            if key.startswith(prefix):
                env[key] = value

    env.setdefault("HOME", str(Path.home()))
    env.setdefault("PATH", os.environ.get("PATH", ""))
    return env


def _append_audit_log(
    path: str | None,
    *,
    app: str,
    action: str,
    status: str,
    report: dict,
    command: list[str],
    command_ran: bool,
    dry_run: bool,
    command_exit_code: int | None,
    strict: bool,
    allow_any_command: bool,
    allowed_command_count: int,
    allow_any_command_reason: str | None,
    allow_any_command_approval_token: str | None,
) -> None:
    if not path:
        return

    payload = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "app": app or "",
        "action": action,
        "status": status,
        "decision": "blocked" if status == "BLOCK" or (strict and status == "REVIEW") else "proceed",
        "score": report.get("score", 0),
        "findings_count": report.get("findings_count", 0),
        "text_hash": _hash_text(report.get("original_text", "")),
        "text_len": len(report.get("original_text", "")),
        "command_hash": _hash_command(command),
        "command_preview": Path(command[0]).name,
        "command_ran": command_ran,
        "dry_run": dry_run,
        "command_exit_code": command_exit_code,
        "strict": bool(strict),
        "allow_any_command": bool(allow_any_command),
        "allowed_command_count": int(allowed_command_count),
        "allow_any_command_reason": allow_any_command_reason or "",
        "allow_any_command_approval_token": _fingerprint_token(allow_any_command_approval_token),
    }

    log_path = Path(path).expanduser()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True))
        handle.write("\n")


def run_guardrails(
    *,
    text: str,
    action: str,
    app: str,
    scope: str | None,
    apps: list[str] | None,
    policies: list[str] | None,
    review_threshold: int | None,
    block_threshold: int | None,
    strict: bool,
    checker_timeout: int,
) -> tuple[dict, bool]:
    if not CHECKER_SCRIPT.exists():
        raise RuntimeError(f"Guardrail script not found: {CHECKER_SCRIPT}")

    args = [
        sys.executable,
        str(CHECKER_SCRIPT),
        "--action",
        action,
        "--text",
        text,
        "--json",
    ]

    if app:
        args.extend(["--app", app])
    if scope:
        args.extend(["--scope", scope])
    if apps:
        args.extend(["--apps", *apps])
    if policies:
        args.extend(["--policies", *policies])
    if review_threshold is not None:
        args.extend(["--review-threshold", str(review_threshold)])
    if block_threshold is not None:
        args.extend(["--block-threshold", str(block_threshold)])

    try:
        proc = subprocess.run(
            args,
            text=True,
            capture_output=True,
            check=False,
            timeout=checker_timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"Guardrail check timed out after {checker_timeout}s.") from exc

    if not proc.stdout:
        stderr = (proc.stderr or "").strip()
        raise RuntimeError(f"Guardrail check returned no output. {stderr}".strip())

    try:
        report = _extract_json(proc.stdout)
    except RuntimeError as exc:
        stderr = (proc.stderr or "").strip()
        msg = f"{exc} stderr={stderr}" if stderr else str(exc)
        raise RuntimeError(msg)

    status = report.get("status")
    if proc.returncode not in {0, 1, 2}:
        raise RuntimeError(
            f"Guardrail check failed before execution (exit={proc.returncode}). status={status!r}."
        )
    if status not in {"PASS", "WATCH", "REVIEW", "BLOCK"}:
        raise RuntimeError(f"Guardrail checker returned unexpected status: {status}")

    blocked = status == "BLOCK" or (strict and status == "REVIEW")
    if blocked:
        print(
            f"Blocked by enterprise legal guardrails ({status}) for {action} on {app or 'unknown'} "
            f"before command execution. Score: {report.get('score', 'n/a')}, "
            f"Findings: {report.get('findings_count', 'n/a')}",
            file=sys.stderr,
        )
        return report, True

    if status == "REVIEW":
        suggestion = (report.get("suggestions") or ["Consider rewriting before execution."])[0]
        print(f"Guardrail REVIEW for {action} on {app or 'unknown'}: {suggestion}", file=sys.stderr)

    return report, False


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run enterprise legal guardrails on draft outbound content, "
            "then execute a command only when allowed."
        )
    )
    parser.add_argument("--app", default="", help="App context for app-level scoping/filtering.")
    parser.add_argument(
        "--action",
        default="generic",
        choices=["post", "comment", "message", "trade", "market-analysis", "generic"],
        help="Action profile to use for policy selection.",
    )
    parser.add_argument("--text", help="Draft content to validate.")
    parser.add_argument("--text-file", help="Read draft content from a file.")
    parser.add_argument(
        "--scope",
        choices=["all", "include", "exclude"],
        default=_get_env(
            "ENTERPRISE_LEGAL_GUARDRAILS_OUTBOUND_SCOPE",
            "ELG_OUTBOUND_SCOPE",
            "BABYLON_GUARDRAILS_SCOPE",
            "BABYLON_GUARDRAILS_OUTBOUND_SCOPE",
        )
        or "all",
        help="Scope mode for app filtering: all|include|exclude.",
    )
    parser.add_argument(
        "--apps",
        nargs="*",
        default=_split_csv(
            _get_env(
                "ENTERPRISE_LEGAL_GUARDRAILS_OUTBOUND_APPS",
                "ENTERPRISE_LEGAL_GUARDRAILS_APPS",
                "ELG_OUTBOUND_APPS",
                "BABYLON_GUARDRAILS_APPS",
            )
        ),
        help="App list used with --scope include|exclude.",
    )
    parser.add_argument("--policies", nargs="+", help="Explicit policy families to enforce.")
    parser.add_argument("--review-threshold", type=int, help="Override review threshold.")
    parser.add_argument("--block-threshold", type=int, help="Override block threshold.")
    parser.add_argument(
        "--strict",
        action="store_true",
        default=_get_env_bool(
            "ENTERPRISE_LEGAL_GUARDRAILS_STRICT",
            "ELG_STRICT",
            "BABYLON_GUARDRAILS_STRICT",
            default=False,
        ),
        help="Treat REVIEW as BLOCK for this run.",
    )

    parser.add_argument(
        "--allow-any-command",
        action="store_true",
        default=_get_env_bool(
            "ENTERPRISE_LEGAL_GUARDRAILS_ALLOW_ANY_COMMAND",
            "ELG_ALLOW_ANY_COMMAND",
            "BABYLON_ALLOW_ANY_COMMAND",
            default=False,
        ),
        help="Dangerously bypass command allowlist (not recommended).",
    )

    parser.add_argument(
        "--suppress-allow-any-warning",
        action="store_true",
        default=_get_env_bool(
            "ENTERPRISE_LEGAL_GUARDRAILS_SUPPRESS_ALLOW_ANY_WARNING",
            "ELG_SUPPRESS_ALLOW_ANY_WARNING",
            "BABYLON_SUPPRESS_ALLOW_ANY_WARNING",
            default=False,
        ),
        help="Suppress warning when allowlist bypass is enabled via --allow-any-command.",
    )
    parser.add_argument(
        "--allow-any-command-reason",
        default=_get_env(
            "ENTERPRISE_LEGAL_GUARDRAILS_ALLOW_ANY_COMMAND_REASON",
            "ELG_ALLOW_ANY_COMMAND_REASON",
            "BABYLON_ALLOW_ANY_COMMAND_REASON",
        ),
        help="Mandatory rationale when allowlist bypass is explicitly enabled.",
    )
    parser.add_argument(
        "--allow-any-command-approval-token",
        default=_get_env(
            "ENTERPRISE_LEGAL_GUARDRAILS_ALLOW_ANY_COMMAND_APPROVAL_TOKEN",
            "ELG_ALLOW_ANY_COMMAND_APPROVAL_TOKEN",
            "BABYLON_ALLOW_ANY_COMMAND_APPROVAL_TOKEN",
        ),
        help="Mandatory approval token when allowlist bypass is explicitly enabled.",
    )

    parser.add_argument(
        "--allowed-command",
        nargs="*",
        default=_split_csv(
            _get_env(
                "ENTERPRISE_LEGAL_GUARDRAILS_ALLOWED_COMMANDS",
                "ELG_ALLOWED_COMMANDS",
                "BABYLON_ALLOWED_COMMANDS",
            )
        ),
        help="Restrict command execution to matching executable names/patterns.",
    )

    parser.add_argument(
        "--command-timeout",
        type=int,
        default=_get_env_int("ENTERPRISE_LEGAL_GUARDRAILS_COMMAND_TIMEOUT_SECONDS", default=60),
        help="Timeout in seconds for wrapped command execution.",
    )
    parser.add_argument(
        "--checker-timeout",
        type=int,
        default=_get_env_int("ENTERPRISE_LEGAL_GUARDRAILS_CHECKER_TIMEOUT_SECONDS", default=10),
        help="Timeout in seconds for guardrail checker execution.",
    )
    parser.add_argument(
        "--max-text-bytes",
        type=int,
        default=_get_env_int("ENTERPRISE_LEGAL_GUARDRAILS_MAX_TEXT_BYTES", default=120_000),
        help="Maximum draft size in bytes before hard stop.",
    )

    parser.add_argument(
        "--sanitize-env",
        action="store_true",
        default=_get_env_bool("ENTERPRISE_LEGAL_GUARDRAILS_SANITIZE_ENV", default=False),
        help="Pass a reduced env to the wrapped command.",
    )
    parser.add_argument(
        "--keep-env",
        nargs="*",
        default=_split_csv(_get_env("ENTERPRISE_LEGAL_GUARDRAILS_KEEP_ENV")),
        help="Environment variables to keep when --sanitize-env is enabled.",
    )
    parser.add_argument(
        "--keep-env-prefix",
        nargs="*",
        default=_split_csv(_get_env("ENTERPRISE_LEGAL_GUARDRAILS_KEEP_ENV_PREFIX")),
        help="Environment variable prefixes to keep when --sanitize-env is enabled.",
    )
    parser.add_argument(
        "--audit-log",
        default=_get_env("ENTERPRISE_LEGAL_GUARDRAILS_AUDIT_LOG"),
        help="Optional JSONL file path for execution audits.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and log only; do not execute command.",
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command to run after '--', for example: -- python3 script.py ...",
    )

    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if not args.command:
        print("Missing command. Use -- <command...>", file=sys.stderr)
        return 2

    if args.command[0] != "--":
        print("Guardrail gate requires delimiter -- before command.", file=sys.stderr)
        return 2

    command = args.command[1:]
    if not command:
        print("Missing command after --.", file=sys.stderr)
        return 2

    try:
        text = _read_text(args.text, args.text_file)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if len(text.encode("utf-8")) > args.max_text_bytes:
        print(f"Draft text exceeds max allowed bytes ({args.max_text_bytes}).", file=sys.stderr)
        return 2

    if args.command_timeout <= 0:
        print("--command-timeout must be a positive integer.", file=sys.stderr)
        return 2
    if args.checker_timeout <= 0:
        print("--checker-timeout must be a positive integer.", file=sys.stderr)
        return 2

    if not args.allow_any_command and not args.allowed_command:
        print(
            "No command allowlist configured: set --allowed-command (or ELG/BABYLON_ALLOWED_COMMANDS) "
            "or pass --allow-any-command explicitly.",
            file=sys.stderr,
        )
        return 1

    if args.allow_any_command and not args.allow_any_command_reason:
        print(
            "Refusing --allow-any-command without an explicit rationale. "
            "Set --allow-any-command-reason or ENTERPRISE_LEGAL_GUARDRAILS_ALLOW_ANY_COMMAND_REASON.",
            file=sys.stderr,
        )
        return 2

    if args.allow_any_command and not args.allow_any_command_approval_token:
        print(
            "Refusing --allow-any-command without approval token. "
            "Set --allow-any-command-approval-token or ENTERPRISE_LEGAL_GUARDRAILS_ALLOW_ANY_COMMAND_APPROVAL_TOKEN.",
            file=sys.stderr,
        )
        return 2

    if args.allow_any_command and not re.search(
        r"^(?:[A-Z][A-Z0-9_]{2,}-\d{2,}:|INC-\d{3,}:|TICKET-[0-9]{3,}:)",
        args.allow_any_command_reason,
    ):
        print(
            "Refusing --allow-any-command because reason format is invalid. "
            "Use a ticket-like reason, e.g. 'SEC-1234: temporary migration task'.",
            file=sys.stderr,
        )
        return 2

    if args.allow_any_command and not args.suppress_allow_any_warning:
        print(
            "Runtime notice: --allow-any-command is enabled; command allowlist is bypassed."
            f" Reason: {args.allow_any_command_reason}. "
            f"Approval: {_fingerprint_token(args.allow_any_command_approval_token)}. "
            "This is unsafe for production unless intentionally approved and audited.",
            file=sys.stderr,
        )

    try:
        command_allowed = _is_allowed(command, args.allowed_command)
    except RuntimeError as exc:
        print(f"Invalid allowlist configuration: {exc}", file=sys.stderr)
        return 2

    if not args.allow_any_command and not command_allowed:
        print(
            f"Blocked command '{_command_repr(command)}' because it is not in the allowlist.",
            file=sys.stderr,
        )
        return 1

    try:
        report, blocked = run_guardrails(
            text=text,
            action=args.action,
            app=args.app,
            scope=args.scope,
            apps=args.apps,
            policies=args.policies,
            review_threshold=args.review_threshold,
            block_threshold=args.block_threshold,
            strict=args.strict,
            checker_timeout=args.checker_timeout,
        )
    except RuntimeError as exc:
        print(f"Guardrail error: {exc}", file=sys.stderr)
        return 1

    status = report.get("status", "UNKNOWN")

    if blocked:
        _append_audit_log(
            args.audit_log,
            app=args.app,
            action=args.action,
            status=str(status),
            report=report,
            command=command,
            command_ran=False,
            dry_run=args.dry_run,
            command_exit_code=None,
            strict=args.strict,
        allow_any_command=args.allow_any_command,
        allowed_command_count=len(args.allowed_command),
        allow_any_command_reason=args.allow_any_command_reason,
        allow_any_command_approval_token=args.allow_any_command_approval_token,
        )
        return 2

    if args.dry_run:
        _append_audit_log(
            args.audit_log,
            app=args.app,
            action=args.action,
            status=str(status),
            report=report,
            command=command,
            command_ran=False,
            dry_run=True,
            command_exit_code=None,
            strict=args.strict,
        allow_any_command=args.allow_any_command,
        allowed_command_count=len(args.allowed_command),
        allow_any_command_reason=args.allow_any_command_reason,
        allow_any_command_approval_token=args.allow_any_command_approval_token,
        )
        return 0

    env = None
    if args.sanitize_env:
        env = _sanitize_env(args.keep_env, args.keep_env_prefix)
        
    try:
        proc = subprocess.run(command, check=False, env=env, timeout=args.command_timeout)
    except FileNotFoundError:
        print(f"Command not found: {command[0]}", file=sys.stderr)
        _append_audit_log(
            args.audit_log,
            app=args.app,
            action=args.action,
            status=str(status),
            report=report,
            command=command,
            command_ran=False,
            dry_run=False,
            command_exit_code=None,
            strict=args.strict,
        allow_any_command=args.allow_any_command,
        allowed_command_count=len(args.allowed_command),
        allow_any_command_reason=args.allow_any_command_reason,
        allow_any_command_approval_token=args.allow_any_command_approval_token,
        )
        return 1
    except subprocess.TimeoutExpired:
        print(f"Guardrail-wrapped command timed out after {args.command_timeout}s.", file=sys.stderr)
        _append_audit_log(
            args.audit_log,
            app=args.app,
            action=args.action,
            status=str(status),
            report=report,
            command=command,
            command_ran=False,
            dry_run=False,
            command_exit_code=None,
            strict=args.strict,
        allow_any_command=args.allow_any_command,
        allowed_command_count=len(args.allowed_command),
        allow_any_command_reason=args.allow_any_command_reason,
        allow_any_command_approval_token=args.allow_any_command_approval_token,
        )
        return 1

    _append_audit_log(
        args.audit_log,
        app=args.app,
        action=args.action,
        status=str(status),
        report=report,
        command=command,
        command_ran=True,
        dry_run=False,
        command_exit_code=proc.returncode,
        strict=args.strict,
        allow_any_command=args.allow_any_command,
        allowed_command_count=len(args.allowed_command),
        allow_any_command_reason=args.allow_any_command_reason,
        allow_any_command_approval_token=args.allow_any_command_approval_token,
    )

    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())

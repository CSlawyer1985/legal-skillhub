#!/usr/bin/env python3
"""Regression tests for guard_and_run adapter."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "guard_and_run.py"


def run(*args: str, env: dict[str, str] | None = None, input_text: str | None = None) -> tuple[int, str, str]:
    if env is None:
        base_env = dict(os.environ)
        if not any(
            base_env.get(name)
            for name in (
                "ENTERPRISE_LEGAL_GUARDRAILS_ALLOWED_COMMANDS",
                "ELG_ALLOWED_COMMANDS",
                "BABYLON_ALLOWED_COMMANDS",
            )
        ):
            base_env["ENTERPRISE_LEGAL_GUARDRAILS_ALLOWED_COMMANDS"] = "python3"
    else:
        base_env = dict(env)

    command = [sys.executable, str(SCRIPT), *args]
    proc = subprocess.run(
        command,
        env=base_env,
        input=input_text,
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


# 1) Benign text should pass and execute command.
code, out, err = run(
    "--app",
    "website",
    "--action",
    "post",
    "--text",
    "Hello colleague, we have a stable release update.",
    "--",
    "python3",
    "-c",
    "print('ok')",
)
assert code == 0, (code, out, err)
assert out.strip() == "ok", (out, err)

# 2) REVIEW should still run by default but emit a warning to stderr.
code, out, err = run(
    "--app",
    "website",
    "--action",
    "post",
    "--text",
    "John is a scammer and this is a guaranteed 100% win",
    "--",
    "python3",
    "-c",
    "print('review-ok')",
)
assert code == 0, (code, out, err)
assert out.strip() == "review-ok", (out, err)
assert "Guardrail REVIEW" in err, err

# 3) Strict REVIEW should block.
code, out, err = run(
    "--strict",
    "--app",
    "website",
    "--action",
    "post",
    "--text",
    "John is a scammer and this is a guaranteed 100% win",
    "--",
    "python3",
    "-c",
    "print('should-not-run')",
)
assert code == 2, (code, out, err)
assert "Blocked by enterprise legal guardrails" in err, err
assert "should-not-run" not in out and "should-not-run" not in err, (out, err)

# 4) Block threshold override can enforce a hard block.
code, out, err = run(
    "--app",
    "website",
    "--action",
    "post",
    "--text",
    "John is a scammer and this is a guaranteed 100% win",
    "--review-threshold",
    "2",
    "--block-threshold",
    "4",
    "--",
    "python3",
    "-c",
    "print('should-not-run2')",
)
assert code == 2, (code, out, err)
assert "Blocked by enterprise legal guardrails" in err, err

# 5) Missing command should error.
code, out, err = run(
    "--app",
    "website",
    "--action",
    "post",
    "--text",
    "Hello",
)
assert code == 2, (code, out, err)
assert "Missing command." in err, (out, err)

# 6) Missing -- delimiter should error.
code, out, err = run(
    "--app",
    "website",
    "--action",
    "post",
    "--text",
    "Hello",
    "python3",
    "-c",
    "print('x')",
)
assert code == 2, (code, out, err)
assert "requires delimiter --" in err, (out, err)

# 6b) Missing allowlist by explicit env var should block execution.
env_no_allowlist = {k: v for k, v in os.environ.items() if k not in {
    "ENTERPRISE_LEGAL_GUARDRAILS_ALLOWED_COMMANDS",
    "ELG_ALLOWED_COMMANDS",
    "BABYLON_ALLOWED_COMMANDS",
}}
code, out, err = run(
    "--app",
    "website",
    "--action",
    "post",
    "--text",
    "Hello",
    "--",
    "python3",
    "-c",
    "print('should-not-run')",
    env=env_no_allowlist,
)
assert code == 1, (code, out, err)
assert "No command allowlist configured" in err, (out, err)

# 7) Explicit allow-list blocks unexpected binaries.
code, out, err = run(
    "--allowed-command",
    "python3",
    "--app",
    "website",
    "--action",
    "post",
    "--text",
    "Hello",
    "--",
    "cat",
    "/etc/hosts",
)
assert code == 1, (code, out, err)
assert "not in the allowlist" in err, (out, err)

# 8) Regex allowlist support.
code, out, err = run(
    "--allowed-command",
    "regex:python3",
    "--app",
    "website",
    "--action",
    "post",
    "--text",
    "Hello",
    "--",
    "python3",
    "-c",
    "print('regex-ok')",
)
assert code == 0, (code, out, err)
assert out.strip() == "regex-ok", (out, err)

# 9a) Invalid regex allowlist pattern should fail safely.
code, out, err = run(
    "--allowed-command",
    "regex:[",
    "--app",
    "website",
    "--action",
    "post",
    "--text",
    "Hello",
    "--",
    "python3",
    "-c",
    "print('should-not-run')",
    env=env_no_allowlist,
)
assert code == 2, (code, out, err)
assert "Invalid allowlist configuration" in err, (out, err)

# 9b) Legacy alias allowlist variable should apply.
code, out, err = run(
    "--app",
    "website",
    "--action",
    "post",
    "--text",
    "Hello",
    "--",
    "cat",
    "/etc/hosts",
    env={**os.environ.copy(), "BABYLON_ALLOWED_COMMANDS": "python3"},
)
assert code == 1, (code, out, err)
assert "not in the allowlist" in err, (out, err)

# 10) Text file input should be honored.
with tempfile.TemporaryDirectory() as tmpdir:
    payload = Path(tmpdir) / "payload.txt"
    payload.write_text("Policy-safe text from file.", encoding="utf-8")
    code, out, err = run(
        "--app",
        "website",
        "--action",
        "post",
        "--text-file",
        str(payload),
        "--",
        "python3",
        "-c",
        "print('from-file')",
    )
    assert code == 0, (code, out, err)
    assert out.strip() == "from-file", (out, err)

# 11) Stdin should work for draft text.
code, out, err = run(
    "--app",
    "website",
    "--action",
    "post",
    "--",
    "python3",
    "-c",
    "print('from-stdin')",
    input_text="Hello from stdin",
)
assert code == 0, (code, out, err)
assert out.strip() == "from-stdin", (out, err)

# 12) Strict mode can also be sourced from env alias.
code, out, err = run(
    "--allowed-command",
    "python3",
    "--app",
    "website",
    "--action",
    "post",
    "--text",
    "John is a scammer and this is a guaranteed 100% win",
    "--",
    "python3",
    "-c",
    "print('should-not-run-env')",
    env={**os.environ.copy(), "ENTERPRISE_LEGAL_GUARDRAILS_STRICT": "true"},
)
assert code == 2, (code, out, err)
assert "Blocked by enterprise legal guardrails" in err, err
assert "should-not-run-env" not in out and "should-not-run-env" not in err, (out, err)

# 12b) Unsafe escape hatch requires explicit reason.
code, out, err = run(
    "--allow-any-command",
    "--app",
    "website",
    "--action",
    "post",
    "--text",
    "Hello",
    "--",
    "python3",
    "-c",
    "print('allow-any-blocked')",
    env=env_no_allowlist,
)
assert code == 2, (code, out, err)
assert "Refusing --allow-any-command without an explicit rationale" in err, (out, err)

# 12c) Missing approval token is refused even with rationale.
code, out, err = run(
    "--allow-any-command",
    "--allow-any-command-reason",
    "SEC-1001: temporary migration task",
    "--app",
    "website",
    "--action",
    "post",
    "--text",
    "Hello",
    "--",
    "python3",
    "-c",
    "print('allow-any-blocked')",
    env=env_no_allowlist,
)
assert code == 2, (code, out, err)
assert "Refusing --allow-any-command without approval token" in err, (out, err)

# 12d) Unsafe escape hatch: allow any command only when explicitly enabled + reason+token.
code, out, err = run(
    "--allow-any-command",
    "--allow-any-command-reason",
    "SEC-1002: temporary migration task",
    "--allow-any-command-approval-token",
    "ci-token-abc",
    "--app",
    "website",
    "--action",
    "post",
    "--text",
    "Hello",
    "--",
    "python3",
    "-c",
    "print('allow-any-ok')",
    env=env_no_allowlist,
)
assert code == 0, (code, out, err)
assert out.strip() == "allow-any-ok", (out, err)
assert "Runtime notice: --allow-any-command is enabled" in err, (out, err)

# 12e) Runtime warning can be suppressed explicitly.
code, out, err = run(
    "--allow-any-command",
    "--allow-any-command-reason",
    "SEC-1003: temporary migration task",
    "--allow-any-command-approval-token",
    "ci-token-abc",
    "--suppress-allow-any-warning",
    "--app",
    "website",
    "--action",
    "post",
    "--text",
    "Hello",
    "--",
    "python3",
    "-c",
    "print('allow-any-no-warning')",
    env=env_no_allowlist,
)
assert code == 0, (code, out, err)
assert out.strip() == "allow-any-no-warning", (out, err)
assert "Runtime notice: --allow-any-command is enabled" not in err, (out, err)

# 12f) allow-any truly bypasses allowlist when an allowlist is present.
code, out, err = run(
    "--allow-any-command",
    "--allow-any-command-reason",
    "SEC-1005: temporary migration task",
    "--allow-any-command-approval-token",
    "ci-token-abc",
    "--allowed-command",
    "/usr/bin/echo",
    "--app",
    "website",
    "--action",
    "post",
    "--text",
    "Hello",
    "--",
    "python3",
    "-c",
    "print('allow-any-bypasses')",
    env=env_no_allowlist,
)
assert code == 0, (code, out, err)
assert out.strip() == "allow-any-bypasses", (out, err)

# sanity: without allow-any, allowlist still blocks non-matching executable.
code, out, err = run(
    "--allowed-command",
    "/usr/bin/echo",
    "--app",
    "website",
    "--action",
    "post",
    "--text",
    "Hello",
    "--",
    "python3",
    "-c",
    "print('should-not-run-list')",
    env=env_no_allowlist,
)
assert code == 1, (code, out, err)
assert "Blocked command" in err and "should-not-run-list" in err and "because it is not in the allowlist." in err

# 13) Max text bytes enforcement.
code, out, err = run(
    "--app",
    "website",
    "--action",
    "post",
    "--max-text-bytes",
    "1",
    "--text",
    "too big",
    "--",
    "python3",
    "-c",
    "print('nope')",
)
assert code == 2, (code, out, err)
assert "max allowed bytes" in err, (out, err)

# 14) Sanitized environment should remove unshared variables and keep explicit prefixes.
with tempfile.TemporaryDirectory() as tmpdir:
    code, out, err = run(
        "--allowed-command",
        "python3",
        "--sanitize-env",
        "--keep-env",
        "KEEP_ME",
        "--keep-env-prefix",
        "SHARED_",
        "--app",
        "website",
        "--action",
        "post",
        "--text",
        "Hello",
        "--",
        "python3",
        "-c",
        "import os; print('KEEP_ME' in os.environ, any(k.startswith('SHARED_') for k in os.environ), 'DROP_ME' in os.environ)",
        env={
            **os.environ,
            "KEEP_ME": "1",
            "SHARED_TOKEN": "2",
            "DROP_ME": "3",
        },
    )
    assert code == 0, (code, out, err)
    assert out.strip() == "True True False", (out, err)

# 15) command-timeout blocks long-running command.
code, out, err = run(
    "--command-timeout",
    "1",
    "--app",
    "website",
    "--action",
    "post",
    "--text",
    "Hello",
    "--",
    "python3",
    "-c",
    "import time; time.sleep(2)",
)
assert code == 1, (code, out, err)
assert "timed out" in err.lower(), (out, err)

# 16) dry-run does not execute the wrapped command.
with tempfile.TemporaryDirectory() as tmpdir:
    marker = Path(tmpdir) / "ran.txt"
    code, out, err = run(
        "--dry-run",
        "--app",
        "website",
        "--action",
        "post",
        "--text",
        "Hello",
        "--",
        "python3",
        "-c",
        f"import pathlib; pathlib.Path('{marker.as_posix()}').write_text('done')",
    )
    assert code == 0, (code, out, err)
    assert not marker.exists(), (marker, "command should not run during dry-run")

# 17) Checker timeout argument validation.
code, out, err = run(
    "--checker-timeout",
    "0",
    "--app",
    "website",
    "--action",
    "post",
    "--text",
    "Hello",
    "--",
    "python3",
    "-c",
    "print('nope')",
)
assert code == 2, (code, out, err)
assert "must be a positive integer" in err

# 18) Command timeout argument validation.
code, out, err = run(
    "--command-timeout",
    "0",
    "--app",
    "website",
    "--action",
    "post",
    "--text",
    "Hello",
    "--",
    "python3",
    "-c",
    "print('nope')",
)
assert code == 2, (code, out, err)
assert "must be a positive integer" in err

# 19) Command not found should return 1 with explicit message.
code, out, err = run(
    "--allowed-command",
    "definitely-missing-command",
    "--app",
    "website",
    "--action",
    "post",
    "--text",
    "Hello",
    "--",
    "definitely-missing-command",
)
assert code == 1, (code, out, err)
assert "Command not found" in err

# 20) Non-zero command exit code should be propagated.
code, out, err = run(
    "--app",
    "website",
    "--action",
    "post",
    "--text",
    "Hello",
    "--",
    "python3",
    "-c",
    "import sys; sys.exit(5)",
)
assert code == 5, (code, out, err)

# 21) Audit log writes JSONL and appends across runs.
with tempfile.TemporaryDirectory() as tmpdir:
    log_path = Path(tmpdir) / "guard_audit.jsonl"
    code1, out1, err1 = run(
        "--audit-log",
        str(log_path),
        "--app",
        "website",
        "--action",
        "post",
        "--text",
        "Hello",
        "--",
        "python3",
        "-c",
        "print('ok')",
    )
    assert code1 == 0, (code1, out1, err1)

    code2, out2, err2 = run(
        "--audit-log",
        str(log_path),
        "--dry-run",
        "--app",
        "website",
        "--action",
        "post",
        "--text",
        "Hello",
        "--",
        "python3",
        "-c",
        "print('nope')",
    )
    assert code2 == 0, (code2, out2, err2)

    lines = [line for line in log_path.read_text().splitlines() if line.strip()]
    assert len(lines) == 2, lines
    rec1 = json.loads(lines[0])
    rec2 = json.loads(lines[1])
    assert rec1["command_ran"] is True
    assert rec1["dry_run"] is False
    assert rec2["command_ran"] is False
    assert rec2["dry_run"] is True

# 22) allow-any command executions should log explicit reason.
with tempfile.TemporaryDirectory() as tmpdir:
    log_path = Path(tmpdir) / "guard_audit_reason.jsonl"
    code, out, err = run(
        "--allow-any-command",
        "--allow-any-command-reason",
        "SEC-1004: incident approved by security",
        "--allow-any-command-approval-token",
        "ci-token-abc",
        "--audit-log",
        str(log_path),
        "--app",
        "website",
        "--action",
        "post",
        "--text",
        "Hello",
        "--",
        "python3",
        "-c",
        "print('reason-ok')",
        env=env_no_allowlist,
    )
    assert code == 0, (code, out, err)
    rows = [line for line in log_path.read_text().splitlines() if line.strip()]
    assert len(rows) == 1, rows
    rec = json.loads(rows[0])
    assert rec["allow_any_command"] is True
    assert rec["allow_any_command_reason"] == "SEC-1004: incident approved by security"
    assert rec["allow_any_command_approval_token"]

print("ok")

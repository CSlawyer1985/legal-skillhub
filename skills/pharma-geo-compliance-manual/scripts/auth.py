#!/usr/bin/env python3
"""
Unified Skill authorization helper.

The Skill instructions should call this file before running any protected
capability. The helper owns all local credential storage, WorkBuddy JWT binding,
and optional remote authorization checks.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import stat
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


AUTH_OK = "AUTH_OK"
AUTH_REQUIRED = "AUTH_REQUIRED"
AUTH_INVALID = "AUTH_INVALID"
AUTH_BIND_OK = "AUTH_BIND_OK"

# Backward-compatible signal names used by older Skill instructions.
SIGNAL_MISSING = "CREDENTIALS_MISSING"
SIGNAL_INVALID = "CREDENTIALS_INVALID"


SKILL_ROOT = Path(__file__).resolve().parents[1]


def load_skill_meta() -> dict[str, Any]:
    """Load package metadata when available."""
    for name in ("_meta.json", "_skillhub_meta.json"):
        path = SKILL_ROOT / name
        if not path.exists():
            continue
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def detect_default_skill_code() -> str:
    """Return platform skillCode from _meta.json.slug, then fall back to folder name."""
    meta = load_skill_meta()
    slug = str(meta.get("slug", "")).strip()
    if slug:
        return slug
    return SKILL_ROOT.name


def safe_cache_name(skill_code: str) -> str:
    """Make a stable cache file name for a Skill code."""
    value = skill_code.strip() or "unknown-skill"
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value)
    return value.strip("._-") or "unknown-skill"


SKILL_CODE = os.environ.get("SKILL_CODE", detect_default_skill_code())
API_BASE_URL = os.environ.get(
    "SKILL_AUTH_API_BASE",
    "https://s.1100111.cn/baitong_ai",
).rstrip("/")
BIND_URL = os.environ.get("SKILL_AUTH_BIND_URL",
                          f"{API_BASE_URL}/api/skill/bind")
VERIFY_URL = os.environ.get("SKILL_AUTH_VERIFY_URL",
                            f"{API_BASE_URL}/api/skill/verify")
CACHE_FILE = None

# Legacy path used by the first xxxx-search prototype. Kept as read fallback.
LEGACY_CACHE_FILE = Path.home() / ".workbuddy" / ".xxxx_search_credentials.json"


def cache_file_for(skill_code: str | None = None) -> Path:
    """Return the credential cache path for the requested Skill."""
    if CACHE_FILE is not None:
        return Path(CACHE_FILE)
    target_skill_code = skill_code or SKILL_CODE
    return Path.home() / ".workbuddy" / "skill_auth" / f"{safe_cache_name(target_skill_code)}.json"


def _now_ms() -> str:
    return str(int(time.time() * 1000))


def make_sign_headers(app_key: str, app_secret: str) -> dict[str, str]:
    """Build the platform signature headers."""
    timestamp = _now_ms()
    raw = app_key + timestamp + app_secret
    sign = hashlib.md5(raw.encode("utf-8")).hexdigest()
    return {
        "X-App-Key": app_key,
        "X-Timestamp": timestamp,
        "X-Sign": sign,
        "Content-Type": "application/json; charset=utf-8",
    }


def save_credentials(
    app_key: str,
    app_secret: str,
    *,
    workbuddy_sub: str = "",
    skill_code: str | None = None,
) -> None:
    """Save credentials for this Skill with user binding metadata."""
    target_skill_code = skill_code or SKILL_CODE
    cache_file = cache_file_for(target_skill_code)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "skill_code": target_skill_code,
        "app_key": app_key.strip(),
        "app_secret": app_secret.strip(),
        "workbuddy_sub": workbuddy_sub.strip(),
        "saved_at": int(time.time()),
    }
    cache_file.write_text(json.dumps(
        data, ensure_ascii=False, indent=2), encoding="utf-8")
    cache_file.chmod(stat.S_IRUSR | stat.S_IWUSR)
    print(f"[auth] credentials saved: {cache_file}")


def _read_cache_file(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        raise ValueError("cache file is empty")
    data = json.loads(raw)
    if not str(data.get("app_key", "")).strip():
        raise ValueError("app_key is empty")
    if not str(data.get("app_secret", "")).strip():
        raise ValueError("app_secret is empty")
    return data


def load_credential_record(*, skill_code: str | None = None) -> dict[str, Any]:
    """Load the full credential cache record."""
    target_skill_code = skill_code or SKILL_CODE
    cache_path = cache_file_for(target_skill_code)
    if not cache_path.exists() and SKILL_CODE == "xxxx-search" and LEGACY_CACHE_FILE.exists():
        cache_path = LEGACY_CACHE_FILE

    if not cache_path.exists():
        print(AUTH_REQUIRED)
        print(SIGNAL_MISSING)
        print_bind_instruction(target_skill_code)
        sys.exit(1)

    try:
        return _read_cache_file(cache_path)
    except (json.JSONDecodeError, ValueError, KeyError) as exc:
        print(AUTH_INVALID)
        print(SIGNAL_INVALID)
        print(f"[auth] credential cache is invalid: {exc}", file=sys.stderr)
        print_bind_instruction(target_skill_code)
        sys.exit(1)


def load_credentials() -> tuple[str, str]:
    """Return (app_key, app_secret). Imported by business scripts."""
    data = load_credential_record()
    return str(data["app_key"]).strip(), str(data["app_secret"]).strip()


def parse_jwt_payload(token: str) -> dict[str, Any]:
    """Parse a WorkBuddy JWT payload without verifying the signature."""
    parts = token.strip().split(".")
    if len(parts) != 3:
        raise ValueError(
            f"invalid JWT format, expected 3 parts, got {len(parts)}")

    payload_b64 = parts[1]
    padding = 4 - len(payload_b64) % 4
    if padding != 4:
        payload_b64 += "=" * padding

    try:
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        return json.loads(payload_bytes.decode("utf-8"))
    except Exception as exc:
        raise ValueError(f"failed to decode JWT payload: {exc}") from exc


def _post_json(url: str, body: dict[str, Any], headers: dict[str, str], timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {error_body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"network error: {exc.reason}") from exc

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"non-JSON response: {raw}") from exc


def _result_ok(result: dict[str, Any]) -> bool:
    code = result.get("code")
    if code in (200, 0, None):
        return True
    return str(code).lower() in ("200", "0", "success")


def call_bind_api(
    *,
    workbuddy_sub: str,
    phone: str,
    nickname: str = "",
    skill_code: str | None = None,
) -> tuple[str, str]:
    """Bind WorkBuddy user identity and return platform credentials."""
    body: dict[str, Any] = {
        "skillCode": skill_code or SKILL_CODE,
        "workbuddySub": workbuddy_sub,
        "phone": phone,
    }
    if nickname:
        body["nickname"] = nickname

    result = _post_json(
        BIND_URL,
        body,
        {"Content-Type": "application/json; charset=utf-8"},
        timeout=15,
    )

    if not _result_ok(result):
        raise RuntimeError(
            f"bind failed: code={result.get('code')}, msg={result.get('msg')}")

    data = result.get("data", result)
    app_key = str(data.get("app_key") or data.get("appKey") or "").strip()
    app_secret = str(data.get("app_secret")
                     or data.get("appSecret") or "").strip()
    if not app_key or not app_secret:
        raise RuntimeError(
            f"bind response missing app_key/app_secret: {json.dumps(result, ensure_ascii=False)}")
    return app_key, app_secret


def call_verify_api(record: dict[str, Any], *, skill_code: str | None = None) -> None:
    """Verify cached credentials with the platform."""
    app_key = str(record["app_key"]).strip()
    app_secret = str(record["app_secret"]).strip()
    body = {
        "skillCode": skill_code or record.get("skill_code") or SKILL_CODE,
        "workbuddySub": record.get("workbuddy_sub", ""),
    }
    result = _post_json(
        VERIFY_URL,
        body,
        make_sign_headers(app_key, app_secret),
        timeout=15,
    )
    if not _result_ok(result):
        raise RuntimeError(
            f"authorization failed: code={result.get('code')}, msg={result.get('msg')}")


def bind_with_jwt(token: str, *, skill_code: str | None = None) -> None:
    """Parse WorkBuddy JWT, bind user, and save credentials."""
    payload = parse_jwt_payload(token)
    workbuddy_sub = str(payload.get("sub", "")).strip()
    phone = str(payload.get("preferred_username", "")).strip()
    nickname = str(payload.get("nickname", "")).strip()

    if not workbuddy_sub or not phone:
        raise SystemExit(
            "[auth] JWT payload missing required fields: sub / preferred_username")

    app_key, app_secret = call_bind_api(
        workbuddy_sub=workbuddy_sub,
        phone=phone,
        nickname=nickname,
        skill_code=skill_code or SKILL_CODE,
    )
    save_credentials(
        app_key,
        app_secret,
        workbuddy_sub=workbuddy_sub,
        skill_code=skill_code or SKILL_CODE,
    )
    print(AUTH_BIND_OK)
    print("[auth] bind succeeded")


def print_bind_instruction(skill_code: str) -> None:
    print(
        "[auth] call WorkBuddy connect_cloud_service, then run:\n"
        f'python3 scripts/auth.py --bind-jwt "<JWT_TOKEN>" --skill-code "{skill_code}"')


def ensure_authorized(*, skill_code: str | None = None, verify_remote: bool = True) -> None:
    """Ensure this Skill is authorized before use."""
    target_skill_code = skill_code or SKILL_CODE
    record = load_credential_record(skill_code=target_skill_code)
    target_skill_code = skill_code or record.get("skill_code") or SKILL_CODE
    if str(record.get("skill_code", target_skill_code)) != target_skill_code:
        print(AUTH_INVALID)
        print(SIGNAL_INVALID)
        print(
            f"[auth] cached credential is for another skill: {record.get('skill_code')}", file=sys.stderr)
        print_bind_instruction(target_skill_code)
        sys.exit(1)

    if verify_remote:
        try:
            call_verify_api(record, skill_code=target_skill_code)
        except RuntimeError as exc:
            print(AUTH_INVALID)
            print(SIGNAL_INVALID)
            print(
                f"[auth] remote authorization check failed: {exc}", file=sys.stderr)
            print_bind_instruction(target_skill_code)
            sys.exit(1)

    print(AUTH_OK)
    print(f"[auth] authorized for skill: {target_skill_code}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Unified Skill authorization helper")
    parser.add_argument("--skill-code", default=SKILL_CODE,
                        help="Skill code, defaults to _meta.json.slug")
    parser.add_argument("--ensure", action="store_true",
                        help="Require a valid authorization before using the Skill")
    parser.add_argument("--no-verify", action="store_true",
                        help="Only check local credentials; skip remote verification")
    parser.add_argument("--bind-jwt", "--bind", dest="bind_jwt",
                        metavar="JWT_TOKEN", help="Bind with a WorkBuddy JWT")
    parser.add_argument("--check", action="store_true",
                        help="Alias for --ensure --no-verify")
    parser.add_argument("--save-token", metavar="APP_KEY",
                        help="Save AppKey manually")
    parser.add_argument("--save-secret", metavar="APP_SECRET",
                        help="Save AppSecret manually")
    args = parser.parse_args()

    if args.bind_jwt:
        try:
            bind_with_jwt(args.bind_jwt.strip(), skill_code=args.skill_code)
        except (RuntimeError, ValueError) as exc:
            print(AUTH_INVALID)
            print(f"[auth] bind failed: {exc}", file=sys.stderr)
            sys.exit(1)
        return

    if args.ensure or args.check:
        ensure_authorized(skill_code=args.skill_code,
                          verify_remote=not (args.no_verify or args.check))
        return

    if args.save_token or args.save_secret:
        if not args.save_token or not args.save_secret:
            parser.error(
                "--save-token and --save-secret must be used together")
        save_credentials(args.save_token, args.save_secret,
                         skill_code=args.skill_code)
        return

    parser.print_help()


if __name__ == "__main__":
    main()

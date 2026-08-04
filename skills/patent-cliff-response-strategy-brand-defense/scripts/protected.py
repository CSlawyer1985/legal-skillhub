#!/usr/bin/env python3
"""
Fetch cloud-hosted protected Skill instructions after authorization.

This script prints only the protected content on success so the host agent can
continue with the returned instructions.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import auth


PROTECTED_CONTENT_URL = os.environ.get(
    "SKILL_PROTECTED_CONTENT_URL",
    f"{auth.API_BASE_URL}/api/skill/protected-content",
)


def _result_ok(result: dict[str, Any]) -> bool:
    code = result.get("code")
    if code in (200, 0, None):
        return True
    return str(code).lower() in ("200", "0", "success")


def _extract_content(result: dict[str, Any]) -> str:
    data = result.get("data", result)
    if not isinstance(data, dict):
        raise RuntimeError(f"protected content response missing data: {json.dumps(result, ensure_ascii=False)}")

    content = (
        data.get("protectedContent")
        or data.get("protected_content")
        or data.get("content")
    )
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError(f"protected content is empty: {json.dumps(result, ensure_ascii=False)}")
    return content


def fetch_protected_content(*, skill_code: str | None = None, verify_remote: bool = True) -> str:
    target_skill_code = skill_code or auth.SKILL_CODE
    record = auth.load_credential_record(skill_code=target_skill_code)

    if str(record.get("skill_code", target_skill_code)) != target_skill_code:
        raise RuntimeError(f"cached credential is for another skill: {record.get('skill_code')}")

    if verify_remote:
        auth.call_verify_api(record, skill_code=target_skill_code)

    app_key = str(record["app_key"]).strip()
    app_secret = str(record["app_secret"]).strip()
    body = {
        "skillCode": target_skill_code,
        "workbuddySub": record.get("workbuddy_sub", ""),
        "version": str(auth.load_skill_meta().get("version", "")).strip(),
    }

    result = auth._post_json(
        PROTECTED_CONTENT_URL,
        body,
        auth.make_sign_headers(app_key, app_secret),
        timeout=30,
    )
    if not _result_ok(result):
        raise RuntimeError(f"fetch protected content failed: code={result.get('code')}, msg={result.get('msg')}")
    return _extract_content(result)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch protected Skill content")
    parser.add_argument("--skill-code", default=auth.SKILL_CODE, help="Skill code, defaults to _meta.json.slug")
    parser.add_argument("--no-verify", action="store_true", help="Skip /api/skill/verify before fetching content")
    args = parser.parse_args()

    try:
        content = fetch_protected_content(
            skill_code=args.skill_code,
            verify_remote=not args.no_verify,
        )
    except RuntimeError as exc:
        print(f"[protected] {exc}", file=sys.stderr)
        sys.exit(1)

    sys.stdout.write(content)
    if not content.endswith("\n"):
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()

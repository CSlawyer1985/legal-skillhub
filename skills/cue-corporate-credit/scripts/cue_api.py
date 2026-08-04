#!/usr/bin/env python3
"""Lightweight HTTP client for the Cue API — vendored for ModelScope skills.

Stdlib only (urllib + json + os) — no third-party deps, runs anywhere
with Python 3.10+.

Reads credentials from (in order):
  1. CUE_API_KEY env var
  2. ~/.cue/config.json   {"api_key": "sk...", "base": "https://..."}
  3. CUE_API_BASE env var overrides the base if set
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable, Iterator

CONFIG_PATH = Path.home() / ".cue" / "config.json"
DEFAULT_BASE = "https://cuecue.cn/api"
API_KEY_PAGE = "https://cuecue.cn/api-key"


class CueAPIError(Exception):
    """Wraps any non-2xx response with status + decoded detail."""

    def __init__(self, status: int, detail: str, path: str):
        super().__init__(f"{path} -> HTTP {status}: {detail}")
        self.status = status
        self.detail = detail
        self.path = path

    def user_hint(self) -> str:
        if self.status == 0:
            return (
                "Network unreachable - cannot connect to Cue API. Check:\n"
                "    1) CUE_API_BASE spelling (default https://cuecue.cn/api)\n"
                "    2) Network/VPN/proxy settings (HTTP_PROXY/HTTPS_PROXY env)\n"
                "    3) Agent sandbox may block outbound connections"
            )
        if self.status == 401:
            return (
                "API key invalid or expired. "
                f"Go to {API_KEY_PAGE} to create a new sk-... key, "
                "then export CUE_API_KEY=sk..."
            )
        if self.status == 402:
            return "Cue balance insufficient. Please top up at cuecue.cn."
        if self.status == 403:
            return "Permission denied: the API key cannot access this resource."
        if self.status == 404:
            return "Resource not found (template_id wrong? or deleted)."
        if self.status == 429:
            return "Rate limited. Wait 30 seconds and retry."
        if 500 <= self.status < 600:
            return f"Cue server error ({self.status}). Retry later."
        return f"Unexpected error HTTP {self.status}: {self.detail[:200]}"


# ---------------------------------------------------------------------------
# Credential loading
# ---------------------------------------------------------------------------


def load_config() -> tuple[str, str]:
    """Return (api_key, base_url) or raise SystemExit with a helpful hint."""
    api_key = os.environ.get("CUE_API_KEY", "").strip()
    base = os.environ.get("CUE_API_BASE", "").strip()

    if not api_key and CONFIG_PATH.exists():
        try:
            blob = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            api_key = api_key or blob.get("api_key", "").strip()
            base = base or blob.get("base", "").strip()
        except Exception:
            pass

    base = base or DEFAULT_BASE

    if not api_key:
        sys.stderr.write(
            "\n[cue-skill] Missing API key.\n"
            f"  -> Go to {API_KEY_PAGE} to create a sk-prefixed key\n"
            "  -> Then export CUE_API_KEY=sk... (or write to ~/.cue/config.json)\n\n"
        )
        raise SystemExit(2)

    return api_key, base


# ---------------------------------------------------------------------------
# Low-level HTTP
# ---------------------------------------------------------------------------


def _request(
    method: str,
    path: str,
    *,
    body: dict | None = None,
    stream: bool = False,
    timeout: float = 30.0,
) -> Any:
    api_key, base = load_config()
    url = base.rstrip("/") + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    if stream:
        req.add_header("Accept", "text/event-stream")
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(err_body)
                detail = (
                    parsed.get("detail")
                    if isinstance(parsed.get("detail"), str)
                    else json.dumps(parsed, ensure_ascii=False)
                )
            except Exception:
                detail = err_body[:400]
        except Exception:
            detail = "(no body)"
        raise CueAPIError(e.code, detail, path) from e
    except urllib.error.URLError as e:
        reason = getattr(e, "reason", e)
        raise CueAPIError(0, f"network unreachable: {reason}", path) from e

    if stream:
        return resp

    raw = resp.read().decode("utf-8")
    return json.loads(raw) if raw else None


# ---------------------------------------------------------------------------
# Template search
# ---------------------------------------------------------------------------


def search_templates(
    keyword: str,
    include_system: bool = True,
    page: int = 1,
    page_size: int = 20,
) -> list[dict]:
    """POST /api/templates/search — keyword search over templates.

    Backend matches title + primary_category + secondary_category only.
    Callers should treat results as low-confidence and try keyword variants.
    """
    body = {
        "keyword": keyword,
        "include_system": include_system,
        "page": page,
        "page_size": page_size,
    }
    data = _request("POST", "/templates/search", body=body)
    if isinstance(data, dict):
        payload = data.get("data")
        if isinstance(payload, dict):
            return payload.get("items") or []
        return data.get("items") or []
    if isinstance(data, list):
        return data
    return []


# ---------------------------------------------------------------------------
# Chat / SSE streaming
# ---------------------------------------------------------------------------


def chat_stream(
    payload: dict,
    on_event: Callable[[str, str], None] | None = None,
    max_seconds: float = 1200.0,
) -> Iterator[tuple[str, str]]:
    """Post to /api/chat/stream and iterate (event, data) tuples.

    payload must include: messages, conversation_id, chat_id,
    template_id (optional, omit for free-form deep research),
    need_analysis, need_confirm, need_underlying, need_recommend.
    """
    resp = _request(
        "POST", "/chat/stream", body=payload, stream=True, timeout=max_seconds
    )
    event = ""
    for raw in resp:
        line = raw.decode("utf-8", errors="replace").rstrip("\n")
        if line.startswith("event:"):
            event = line[6:].strip()
        elif line.startswith("data:"):
            data = line[5:].lstrip() if line.startswith("data: ") else line[5:]
            if on_event:
                on_event(event, data)
            yield event, data
        elif not line:
            event = ""


# ---------------------------------------------------------------------------
# Rewrite (privacy masking + public-source constraint)
# ---------------------------------------------------------------------------


def rewrite(input: str, device_type: str = "cli") -> dict:
    """POST /api/rewrite — apply rewrite_prompt to a raw user query.

    Returns dict with keys: thinking, user_confirmation, task_node,
    rewritten_mandate, safety_flag.
    """
    api_key, base = load_config()
    url = base.rstrip("/") + "/rewrite"
    data = json.dumps({"input": input}).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    req.add_header("device_type", device_type)
    try:
        resp = urllib.request.urlopen(req, timeout=60)
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(err_body)
                detail = (
                    parsed.get("detail")
                    if isinstance(parsed.get("detail"), str)
                    else json.dumps(parsed, ensure_ascii=False)
                )
            except Exception:
                detail = err_body[:400]
        except Exception:
            detail = "(no body)"
        raise CueAPIError(e.code, detail, "/api/rewrite") from e
    except urllib.error.URLError as e:
        reason = getattr(e, "reason", e)
        raise CueAPIError(
            0, f"network unreachable: {reason}", "/api/rewrite"
        ) from e
    raw = resp.read().decode("utf-8")
    payload = json.loads(raw) if raw else {}
    if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
        return payload["data"]
    return payload or {}


# ---------------------------------------------------------------------------
# CLI smoke test
# ---------------------------------------------------------------------------

def _cli() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 0
    cmd = sys.argv[1]
    try:
        if cmd == "whoami":
            key, base = load_config()
            print(f"base: {base}")
            print(f"key:  {key[:8]}...{key[-4:]}")
            return 0
        if cmd == "search":
            if len(sys.argv) < 3:
                print("usage: cue_api.py search <keyword>")
                return 2
            for t in search_templates(sys.argv[2]):
                tid = t.get("template_id") or t.get("id") or "?"
                title = t.get("title") or "(no title)"
                print(f"  {tid}  {title}")
            return 0
        print(f"unknown cmd: {cmd}")
        return 2
    except CueAPIError as e:
        sys.stderr.write(f"[error] {e}\n")
        hint = e.user_hint()
        if hint:
            sys.stderr.write(f"        -> {hint}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(_cli())

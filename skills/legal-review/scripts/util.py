#!/usr/bin/env python3
"""Shared utilities for legal-review scripts."""
import json
import os
import sys
import urllib.request
import urllib.error
import urllib.parse

API_BASE = "https://open.chineselaw.com/open"

# Try to find the .env file relative to this script's location
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_DIR = os.path.dirname(_SCRIPT_DIR)
_ENV_PATH = os.path.join(_SKILL_DIR, ".env")


def _load_dotenv():
    """Load .env file if it exists, returns dict of vars set."""
    env_path = os.environ.get("YUANDIAN_ENV_FILE", _ENV_PATH)
    if not os.path.isfile(env_path):
        return {}
    vars_set = {}
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("\"'")
            if key and key not in os.environ:
                os.environ[key] = value
                vars_set[key] = value
    return vars_set


def get_api_key():
    """Get API key from environment or .env file."""
    key = os.environ.get("YUANDIAN_API_KEY")
    if not key:
        _load_dotenv()
        key = os.environ.get("YUANDIAN_API_KEY")
    if not key:
        print(json.dumps({
            "status": "error",
            "message": "YUANDIAN_API_KEY 未配置。请创建 skills/legal-review/.env 文件，"
                       "内容为：YUANDIAN_API_KEY=你的key，或设置环境变量。"
        }, ensure_ascii=False))
        sys.exit(1)
    return key


def api_post(endpoint, data, api_key):
    """Make a POST request to the Yuandian API."""
    req = urllib.request.Request(
        f"{API_BASE}/{endpoint}",
        data=json.dumps(data).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-API-Key": api_key,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"status": "failed", "code": e.code, "message": body}
    except urllib.error.URLError as e:
        return {"status": "failed", "code": 0, "message": str(e.reason)}


def api_get(endpoint, params, api_key):
    """Make a GET request to the Yuandian API."""
    query = urllib.parse.urlencode(params)
    url = f"{API_BASE}/{endpoint}?{query}"
    req = urllib.request.Request(url, headers={"X-API-Key": api_key})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"status": "failed", "code": e.code, "message": body}
    except urllib.error.URLError as e:
        return {"status": "failed", "code": 0, "message": str(e.reason)}

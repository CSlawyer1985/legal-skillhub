"""
合同台账管理 - Token 验证模块
"""
import time
import json
import requests
from pathlib import Path

VALIDATE_URL = "https://api.yk-global.com/v1/verify"
CACHE_FILE = Path(__file__).parent.parent / ".token_cache.json"
CACHE_TTL = 300  # 5 minutes


def validate_token(api_key: str) -> dict:
    """
    验证 API Token
    返回: {"valid": bool, "tier": str, "expires_at": int or None}
    """
    # Check cache first
    cached = _get_cached(api_key)
    if cached:
        return cached

    # Make API call
    try:
        resp = requests.post(
            VALIDATE_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={},
            timeout=10
        )
        data = resp.json()

        if resp.status_code == 200 and data.get("valid"):
            result = {
                "valid": True,
                "tier": _infer_tier(api_key),
                "expires_at": data.get("expires_at")
            }
        else:
            result = {"valid": False, "tier": "FREE", "expires_at": None}

    except Exception:
        # Network error - degrade to FREE tier
        result = {"valid": False, "tier": "FREE", "expires_at": None}

    # Cache result
    _set_cached(api_key, result)
    return result


def _infer_tier(api_key: str) -> str:
    """根据 API key 前缀推断套餐"""
    if not api_key:
        return "FREE"
    if api_key.startswith("CONTRACT-LGR-ENT-"):
        return "ENT"
    if api_key.startswith("CONTRACT-LGR-PRO-"):
        return "PRO"
    if api_key.startswith("CONTRACT-LGR-BSC-"):
        return "BSC"
    return "FREE"


def _get_cached(api_key: str) -> dict | None:
    """从缓存读取"""
    if not CACHE_FILE.exists():
        return None
    try:
        with open(CACHE_FILE, "r") as f:
            cache = json.load(f)
        entry = cache.get(api_key)
        if entry and time.time() < entry["expires"]:
            return entry["result"]
    except Exception:
        pass
    return None


def _set_cached(api_key: str, result: dict):
    """写入缓存"""
    try:
        cache = {}
        if CACHE_FILE.exists():
            with open(CACHE_FILE, "r") as f:
                cache = json.load(f)
        cache[api_key] = {
            "result": result,
            "expires": time.time() + CACHE_TTL
        }
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f)
    except Exception:
        pass


def get_tier_limits(tier: str) -> dict:
    """获取套餐限制"""
    limits = {
        "FREE": {"max_contracts": 5, "max_reminders": 1, "export_formats": ["csv"]},
        "BSC": {"max_contracts": 50, "max_reminders": 5, "export_formats": ["csv"]},
        "PRO": {"max_contracts": 300, "max_reminders": float("inf"), "export_formats": ["csv", "xlsx", "pdf"]},
        "ENT": {"max_contracts": float("inf"), "max_reminders": float("inf"), "export_formats": ["csv", "xlsx", "pdf"]},
    }
    return limits.get(tier, limits["FREE"])

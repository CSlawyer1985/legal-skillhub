"""
Billing module for Contract Smart Compare - yk-global Token verification.

Verifies monthly subscription using yk-global API.
Token prefix: CONTRACT-COMPARE-*
"""
import os
import httpx

from src.config import (
    TOKEN_PREFIX,
    TIER_FREE,
    TIER_STANDARD,
    TIER_PRO,
    LIMITS,
    FREE_TOTAL_USES,
)

# Token validation endpoint
VERIFY_URL = "https://api.yk-global.com/v1/verify"

# Storage for FREE tier usage count (per user)
_free_usage = {}


def get_token() -> str:
    """Get Token from environment variable."""
    token = os.environ.get("CONTRACT_COMPARE_TOKEN", "")
    return token


def is_dev_mode() -> bool:
    """Check if running in development mode (no token configured)."""
    return get_token() in ("", "dev", "test")


def verify_subscription(token: str) -> dict:
    """Verify user subscription via yk-global API.

    Args:
        token: User's subscription token (prefix: CONTRACT-COMPARE-*)

    Returns:
        Dict with tier, limits, valid status, and message
    """
    if not token:
        return {
            "valid": False,
            "tier": TIER_FREE,
            "limits": LIMITS[TIER_FREE],
            "message": "Token not provided",
        }

    if not token.startswith(TOKEN_PREFIX):
        return {
            "valid": False,
            "tier": TIER_FREE,
            "limits": LIMITS[TIER_FREE],
            "message": "Invalid token format",
        }

    try:
        response = httpx.post(
            VERIFY_URL,
            json={"token": token},
            timeout=10.0,
        )

        if response.status_code == 200:
            data = response.json()
            tier = data.get("tier", TIER_FREE)
            return {
                "valid": True,
                "tier": tier,
                "limits": LIMITS.get(tier, LIMITS[TIER_FREE]),
                "message": "OK",
            }
        else:
            return {
                "valid": False,
                "tier": TIER_FREE,
                "limits": LIMITS[TIER_FREE],
                "message": f"Verification failed: {response.status_code}",
            }

    except httpx.Timeout:
        # Fail open for availability
        return {
            "valid": True,
            "tier": TIER_PRO,
            "limits": LIMITS[TIER_PRO],
            "message": "Timeout - assuming Pro",
        }
    except Exception:
        # Fail open
        return {
            "valid": True,
            "tier": TIER_PRO,
            "limits": LIMITS[TIER_PRO],
            "message": "Verification unavailable",
        }


def get_tier(token: str = None) -> tuple:
    """Get subscription tier and limits for a user.

    Args:
        token: Subscription token (optional, uses env if not provided)

    Returns:
        Tuple of (tier, limits_dict)
    """
    if token is None:
        token = get_token()

    if not token:
        return TIER_FREE, LIMITS[TIER_FREE]

    result = verify_subscription(token)
    return result["tier"], result["limits"]


def check_free_usage(user_id: str) -> bool:
    """Check if FREE tier user has remaining uses.

    Args:
        user_id: User identifier

    Returns:
        True if within FREE limit, False if exceeded
    """
    count = _free_usage.get(user_id, 0)
    return count < FREE_TOTAL_USES


def record_free_usage(user_id: str):
    """Record a usage for FREE tier user.

    Args:
        user_id: User identifier
    """
    _free_usage[user_id] = _free_usage.get(user_id, 0) + 1


def get_free_usage_count(user_id: str) -> int:
    """Get current FREE tier usage count."""
    return _free_usage.get(user_id, 0)


def check_limit(tier: str, limit_type: str, current_usage: int) -> bool:
    """Check if user has exceeded a limit.

    Args:
        tier: Subscription tier
        limit_type: Type of limit (monthly_contracts)
        current_usage: Current usage count

    Returns:
        True if within limit, False if exceeded
    """
    limits = LIMITS.get(tier, LIMITS[TIER_FREE])
    limit_value = limits.get(limit_type, -1)

    if limit_value == -1:  # Unlimited
        return True

    return current_usage < limit_value


def charge_user(user_id: str, tier: str) -> dict:
    """Validate and record usage for a user.

    Args:
        user_id: User identifier
        tier: Subscription tier

    Returns:
        Dict with ok, message, remaining
    """
    if tier == TIER_FREE:
        if not check_free_usage(user_id):
            return {
                "ok": False,
                "message": f"FREE tier limit reached ({FREE_TOTAL_USES} uses/month)",
                "remaining": 0,
            }
        record_free_usage(user_id)
        remaining = FREE_TOTAL_USES - _free_usage[user_id]
        return {"ok": True, "message": "OK", "remaining": remaining}

    # For STANDARD/PRO, check monthly limit
    limits = LIMITS.get(tier, LIMITS[TIER_STANDARD])
    monthly = limits.get("monthly_contracts", -1)
    if monthly == -1:
        return {"ok": True, "message": "OK", "remaining": -1}

    current = _free_usage.get(f"{user_id}_monthly", 0)
    if current >= monthly:
        return {
            "ok": False,
            "message": f"Monthly limit reached ({monthly} contracts/month)",
            "remaining": 0,
        }
    _free_usage[f"{user_id}_monthly"] = current + 1
    return {"ok": True, "message": "OK", "remaining": monthly - current - 1}

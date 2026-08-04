"""
Token Validator for Contract Tracker Pro
Validates CONT-TRACK-* tokens via api.yk-global.com/v1/verify
Caches results for 5 minutes (300s) locally
Degrades to FREE tier on network errors — does NOT block usage
"""

import time
import logging
import urllib.request
import urllib.error
import json
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

VERIFY_URL = "https://api.yk-global.com/v1/verify"
CACHE_TTL = 300  # 5 minutes

# Tier limits
TIER_LIMITS = {
    "FREE": {"contracts_per_month": 3, "tier": "FREE"},
    "STANDARD": {"contracts_per_month": 20, "tier": "STANDARD"},
    "PRO": {"contracts_per_month": 100, "tier": "PRO"},
    "MAX": {"contracts_per_month": 999999, "tier": "MAX"},
}

# In-memory cache: {api_key: {"valid": bool, "tier": str, "expires_at": float}}
_token_cache: dict = {}


@dataclass
class TierConfig:
    """Tier configuration returned after token validation."""
    valid: bool
    tier: str
    contracts_per_month: int
    cached: bool = False


def _clear_expired_cache():
    """Remove expired entries from cache."""
    now = time.time()
    expired = [k for k, v in _token_cache.items() if v.get("expires_at", 0) < now]
    for k in expired:
        _token_cache.pop(k, None)


def verify_token(api_key: str, force_refresh: bool = False) -> TierConfig:
    """
    Verify a CONT-TRACK-* token via api.yk-global.com/v1/verify.

    Args:
        api_key: The user's API key (format: CONT-TRACK-*)
        force_refresh: If True, bypass cache and re-verify

    Returns:
        TierConfig with validation result and tier limits.
        On network error: returns FREE tier (graceful degradation).
    """
    global _token_cache

    # Check cache first
    if not force_refresh and api_key in _token_cache:
        cached = _token_cache[api_key]
        if cached.get("expires_at", 0) > time.time():
            logger.debug(f"Token cache hit for {api_key[:12]}...")
            return TierConfig(
                valid=cached.get("valid", False),
                tier=cached.get("tier", "FREE"),
                contracts_per_month=TIER_LIMITS.get(cached.get("tier", "FREE"), {}).get("contracts_per_month", 3),
                cached=True,
            )

    # Perform verification
    try:
        req = urllib.request.Request(
            VERIFY_URL,
            method="POST",
            data=b"{}",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=10,
        )
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            valid = body.get("valid", False)
            tier = body.get("tier", "FREE") if valid else "FREE"

    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
        logger.warning(f"Token verification network error: {e} — degrading to FREE tier")
        tier = "FREE"
        valid = False

    # Determine tier from known tiers (default to FREE if unknown)
    if tier not in TIER_LIMITS:
        tier = "FREE"

    tier_limit = TIER_LIMITS.get(tier, TIER_LIMITS["FREE"])

    # Cache result
    _token_cache[api_key] = {
        "valid": valid,
        "tier": tier,
        "expires_at": time.time() + CACHE_TTL,
    }

    logger.info(f"Token verified: valid={valid}, tier={tier}")

    return TierConfig(
        valid=valid,
        tier=tier,
        contracts_per_month=tier_limit["contracts_per_month"],
        cached=False,
    )


def get_tier_config(api_key: str) -> TierConfig:
    """
    Convenience wrapper: verify token and return tier config.
    Use this when you just need to know the user's tier/limit.
    """
    return verify_token(api_key)


class TokenValidator:
    """
    TokenValidator class for validation state management.
    Use this when you need to track validation state across multiple calls.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.config: Optional[TierConfig] = None

    def validate(self, force_refresh: bool = False) -> TierConfig:
        """Run token validation and store result."""
        self.config = verify_token(self.api_key, force_refresh=force_refresh)
        return self.config

    def is_valid(self) -> bool:
        """Check if token is valid (cached or fresh)."""
        if self.config is None:
            self.validate()
        return self.config.valid if self.config else False

    def can_add_contract(self) -> tuple[bool, str]:
        """
        Check if user can add another contract based on their tier limit.
        Returns (can_add: bool, message: str)
        """
        if self.config is None:
            self.validate()

        if not self.config:
            return False, "Token validation failed"

        # Count current contracts this month
        from .ledger_manager import LedgerManager
        lm = LedgerManager()
        count = lm.get_current_month_count()
        limit = self.config.contracts_per_month

        if count >= limit:
            return False, f"已达当月合同上限（{limit}个），请升级套餐或下月重试"
        return True, f"本月已用 {count}/{limit} 个合同名额"

    def get_tier_display(self) -> str:
        """Get human-readable tier display name."""
        if self.config is None:
            self.validate()
        tier_names = {
            "FREE": "免费版",
            "STANDARD": "标准版",
            "PRO": "专业版",
            "MAX": "旗舰版",
        }
        return tier_names.get(self.config.tier if self.config else "FREE", "免费版")

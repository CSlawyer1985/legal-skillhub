"""
Configuration for Contract Smart Compare.
Defines tiers, limits, and shared constants.
"""
import os

# Subscription tiers
TIER_FREE = "FREE"
TIER_STANDARD = "STANDARD"
TIER_PRO = "PRO"

# Limits per tier
LIMITS = {
    TIER_FREE: {
        "max_files": 2,
        "file_types": ["txt", "docx"],
        "ocr_enabled": False,
        "multi_version": False,
        "risk_assessment": False,
        "excel_export": False,
        "monthly_contracts": 5,
    },
    TIER_STANDARD: {
        "max_files": 2,
        "file_types": ["txt", "docx", "pdf", "jpg", "png"],
        "ocr_enabled": True,
        "multi_version": False,
        "risk_assessment": False,
        "excel_export": True,
        "monthly_contracts": -1,
    },
    TIER_PRO: {
        "max_files": 999,
        "file_types": ["txt", "docx", "pdf", "jpg", "png"],
        "ocr_enabled": True,
        "multi_version": True,
        "risk_assessment": True,
        "excel_export": True,
        "monthly_contracts": -1,
    },
}

# Default AI model
DEFAULT_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514")

# File size limit (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Temp directory for uploads
TEMP_DIR = "/tmp/contract-compare/"

# Token prefix for subscription
TOKEN_PREFIX = "CONTRACT-COMPARE-"

# FREE tier total uses limit
FREE_TOTAL_USES = 5

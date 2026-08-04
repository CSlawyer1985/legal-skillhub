"""
解析专利 API Token：仅使用环境变量或 OpenClaw CLI，不直接读取用户主目录下的配置文件。
"""

from __future__ import annotations

import os
import subprocess
from typing import Optional


def get_patent_api_token() -> Optional[str]:
    """优先 PATENT_API_TOKEN；否则尝试 `openclaw config get`（由用户本机 CLI 读取配置）。"""
    t = (os.environ.get("PATENT_API_TOKEN") or "").strip()
    if t:
        return t
    try:
        result = subprocess.run(
            [
                "openclaw",
                "config",
                "get",
                "skills.entries.patent-search.apiKey",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            return None
        token = (result.stdout or "").strip()
        if token and token != "__OPENCLAW_REDACTED__":
            return token
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return None

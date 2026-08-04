"""
SMS login script.
Usage: python login.py <mobile> <sms_code>
Output: Saves token to static/.auth_token.json
"""

import sys
import urllib.parse
from datetime import datetime, timedelta

from common import ensure_dirs, http_request, save_json, AUTH_TOKEN_PATH


def login(mobile, sms_code):
    """Login with SMS code, save token cache on success."""
    ensure_dirs()

    body = urllib.parse.urlencode({
        "grant_type": "social_credentials",
        "source": "SMS",
        "scope": "openid",
        "mobile": mobile,
        "code": sms_code,
    })

    result = http_request("POST", "/xrl-cloud-uaa/oauth2/token", headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic ZnV5YW8td2ViLXVpOmZ1eWFvLXdlYi11aQ==",
    }, raw_body=body.encode("utf-8"))

    if "access_token" in result:
        now = datetime.now()
        expires_in = result.get("expires_in", 3599)
        token_data = {
            "access_token": result["access_token"],
            "refresh_token": result.get("refresh_token", ""),
            "token_type": result.get("token_type", "Bearer"),
            "expires_in": expires_in,
            "mobile": mobile,
            "login_time": now.strftime("%Y-%m-%dT%H:%M:%S"),
            "expire_time": (now + timedelta(seconds=expires_in)).strftime("%Y-%m-%dT%H:%M:%S"),
        }
        save_json(AUTH_TOKEN_PATH, token_data)
        print(f"LOGIN_SUCCESS|mobile={mobile}")
        return True
    else:
        msg = result.get("message", result.get("msg", str(result)))
        print(f"LOGIN_FAILED|message={msg}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python login.py <mobile> <sms_code>")
        sys.exit(1)

    login(sys.argv[1], sys.argv[2])

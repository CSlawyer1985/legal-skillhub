"""
Get captcha image + send SMS verification code (combined script).
Usage:
  python send_sms.py <mobile>            - Get captcha only, wait for AI recognition
  python send_sms.py <mobile> <captcha>  - Get captcha + send SMS in one step
Output: temp/captcha_temp.png, temp/captcha_identity.txt
Returns: CAPTCHA_SAVED|..., SMS_SENT|... or SMS_FAILED|...
"""

import base64
import json
import os
import re
import sys
import uuid

from common import ensure_dirs, http_request, http_download, TEMP_DIR


def get_captcha():
    """Get image captcha, save PNG and identity to temp/"""
    identity = str(uuid.uuid4())

    # Download captcha response to file
    resp_path = os.path.join(TEMP_DIR, "captcha_resp.json")
    http_download(
        f"/xrl-cloud-upms/open/captcha?identity={identity}&category=HUTOOL_SHEAR",
        resp_path
    )

    # Extract base64 image and identity from response
    with open(resp_path, "r", encoding="utf-8") as f:
        raw = f.read()

    b64_match = re.search(r'"graphicImageBase64"\s*:\s*"data:image/[^;]+;base64,([^"]+)"', raw)
    identity_match = re.search(r'"identity"\s*:\s*"([^"]+)"', raw)

    if not b64_match:
        print("ERROR|message=Failed to extract captcha image from response")
        sys.exit(1)

    b64_data = b64_match.group(1)
    actual_identity = identity_match.group(1) if identity_match else identity

    # Save PNG
    img_bytes = base64.b64decode(b64_data)
    png_path = os.path.join(TEMP_DIR, "captcha_temp.png")
    with open(png_path, "wb") as f:
        f.write(img_bytes)

    # Save identity
    id_path = os.path.join(TEMP_DIR, "captcha_identity.txt")
    with open(id_path, "w", encoding="utf-8") as f:
        f.write(actual_identity)

    print(f"CAPTCHA_SAVED|identity={actual_identity}|png={png_path}")
    return actual_identity


def send_sms(mobile, identity, characters):
    """Send SMS verification code"""
    mobile_b64 = base64.b64encode(mobile.encode("utf-8")).decode("utf-8")

    body = {
        "mobile": mobile_b64,
        "verification": {
            "identity": identity,
            "characters": characters,
            "category": "HUTOOL_SHEAR"
        }
    }

    result = http_request(
        "POST",
        "/xrl-cloud-upms/open/sms-verification-code",
        body=body
    )

    if result.get("success"):
        print(f"SMS_SENT|mobile={mobile}")
        return True
    else:
        msg = result.get("message", "unknown")
        print(f"SMS_FAILED|message={msg}")
        return False


def load_cached_identity():
    """Load identity from temp/captcha_identity.txt"""
    id_path = os.path.join(TEMP_DIR, "captcha_identity.txt")
    if not os.path.exists(id_path):
        print("ERROR|message=No cached identity found, run without captcha first")
        sys.exit(1)
    with open(id_path, "r", encoding="utf-8") as f:
        return f.read().strip()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python send_sms.py <mobile> [captcha_characters]")
        print("  Mode 1: python send_sms.py <mobile>            - Get captcha only")
        print("  Mode 2: python send_sms.py <mobile> <captcha>  - Send SMS using cached identity")
        sys.exit(1)

    mobile = sys.argv[1]
    ensure_dirs()

    if len(sys.argv) >= 3:
        # Mode 2: Send SMS using cached identity (must match the captcha that was shown)
        characters = sys.argv[2]
        identity = load_cached_identity()
        send_sms(mobile, identity, characters)
    else:
        # Mode 1: Get new captcha only
        get_captcha()
        print("WAITING_FOR_CAPTCHA_RECOGNITION")

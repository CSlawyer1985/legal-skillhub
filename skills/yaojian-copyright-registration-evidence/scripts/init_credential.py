"""
Initialize credential (owner) list.
Usage: python init_credential.py
Output: Saves credentials to static/.credential_cache.json
        Prints credentialId for order submission.
"""

import sys
from datetime import datetime

from common import ensure_dirs, http_request, auth_header, save_json, CREDENTIAL_CACHE_PATH


def init_credential():
    """Fetch credential list and save to cache."""
    ensure_dirs()

    result = http_request(
        "GET",
        "/xrl-cloud-asset/v7/user/credential/list?certType=IDENTITY_CARD",
        headers=auth_header()
    )

    data = result.get("data", [])
    if not data:
        print("NO_CREDENTIAL|message=No credential found, please add owner in WeChat")
        return False

    # Save credential cache
    cache_data = {
        "credentials": data,
        "update_time": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    }
    save_json(CREDENTIAL_CACHE_PATH, cache_data)

    # Find primary credential
    primary = None
    for cred in data:
        if cred.get("isPrimary"):
            primary = cred
            break

    # Fallback to first credential
    if not primary:
        primary = data[0]

    cred_id = primary.get("id", "")
    cert_name = primary.get("certName", "")
    print(f"CREDENTIAL_SAVED|credentialId={cred_id}|certName={cert_name}")
    return True


if __name__ == "__main__":
    init_credential()

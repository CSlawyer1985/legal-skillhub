"""
Common utilities for all scripts.
Shared config, HTTP client, file I/O helpers.
"""

import json
import os
import urllib.request
import urllib.error
import urllib.parse

# ============ Path config ============
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_DIR = os.path.join(BASE_DIR, "temp")
STATIC_DIR = os.path.join(BASE_DIR, "static")
CERTIFICATE_DIR = os.path.join(BASE_DIR, "certificate")

# ============ API config ============
GATEWAY = "https://api.fuyaoshuzhi.com"
TENANT_ID = "0"

# ============ Token paths ============
AUTH_TOKEN_PATH = os.path.join(STATIC_DIR, ".auth_token.json")
CREDENTIAL_CACHE_PATH = os.path.join(STATIC_DIR, ".credential_cache.json")


def ensure_dirs():
    """Ensure all required directories exist"""
    for d in [TEMP_DIR, STATIC_DIR, CERTIFICATE_DIR]:
        os.makedirs(d, exist_ok=True)


def http_request(method, path, headers=None, body=None, raw_body=None):
    """
    Send HTTP request and return parsed JSON response.
    - method: GET / POST
    - path: API path (e.g. /xrl-cloud-upms/open/captcha)
    - headers: dict of additional headers
    - body: dict (will be JSON-encoded)
    - raw_body: bytes (sent as-is, ignores body)
    """
    url = f"{GATEWAY}{path}"
    hdrs = {"x-tenant-id": TENANT_ID}
    if headers:
        hdrs.update(headers)

    data = None
    if raw_body is not None:
        data = raw_body
    elif body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/json")

    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            resp_bytes = resp.read()
            resp_text = resp_bytes.decode("utf-8")
            return json.loads(resp_text)
    except urllib.error.HTTPError as e:
        resp_text = e.read().decode("utf-8", errors="replace")
        try:
            return json.loads(resp_text)
        except json.JSONDecodeError:
            return {"_http_error": e.code, "_raw": resp_text}
    except urllib.error.URLError as e:
        return {"_url_error": str(e.reason)}


def http_download(path, output_path, headers=None):
    """
    Download file from API to local path.
    Returns the response text (for JSON responses saved via --output).
    """
    url = f"{GATEWAY}{path}"
    hdrs = {"x-tenant-id": TENANT_ID}
    if headers:
        hdrs.update(headers)

    req = urllib.request.Request(url, headers=hdrs, method="GET")
    with urllib.request.urlopen(req) as resp:
        resp_bytes = resp.read()
        with open(output_path, "wb") as f:
            f.write(resp_bytes)
        return resp_bytes.decode("utf-8", errors="replace")


def http_upload_file(path, file_path, headers=None):
    """
    Upload a file via multipart/form-data.
    Returns parsed JSON response.
    """
    url = f"{GATEWAY}{path}"
    boundary = "----PythonFormBoundary7MA4YWxkTrZu0gW"

    filename = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        file_data = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8") + file_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

    hdrs = {
        "x-tenant-id": TENANT_ID,
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }
    if headers:
        hdrs.update(headers)

    req = urllib.request.Request(url, data=body, headers=hdrs, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            resp_text = resp.read().decode("utf-8")
            return json.loads(resp_text)
    except urllib.error.HTTPError as e:
        resp_text = e.read().decode("utf-8", errors="replace")
        try:
            return json.loads(resp_text)
        except json.JSONDecodeError:
            return {"_http_error": e.code, "_raw": resp_text}
    except urllib.error.URLError as e:
        return {"_url_error": str(e.reason)}


def load_token():
    """Load access_token from static/.auth_token.json. Returns token string."""
    with open(AUTH_TOKEN_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["access_token"]


def auth_header():
    """Return Authorization header dict with Bearer token."""
    return {"Authorization": f"Bearer {load_token()}"}


def save_json(path, data):
    """Save data as JSON file (UTF-8, no BOM, indented)"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(path):
    """Load JSON file (UTF-8)"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

"""
Output certificate links for all apps in order detail.
Usage: python generate_cert.py <order_detail.json>

不再本地渲染证书图片。证书统一由官网 www.yaojianpro.com 生成并托管，
Skill 只负责把每一件作品的证书链接输出给用户。
"""

import json
import sys

from common import load_json

CERT_URL_TEMPLATE = "https://www.yaojianpro.com/cert/{preservation_id}"


def extract_app_summary(app):
    opus = app.get("opus", {}) or {}
    ownership = opus.get("ownership", {}) or {}
    preservation = app.get("preservation", {}) or {}

    preservation_id = (
        preservation.get("preservationId")
        or app.get("preservationId")
        or ""
    )
    file_hash = preservation.get("sha512Hash") or opus.get("fileHash", "")

    return {
        "title": opus.get("title", ""),
        "realName": ownership.get("realName", ""),
        "preservationTime": app.get("preservationTime", ""),
        "preservationId": str(preservation_id),
        "fileHash": file_hash,
        "certUrl": CERT_URL_TEMPLATE.format(preservation_id=preservation_id) if preservation_id else "",
    }


def load_all_order_data(json_path):
    raw = load_json(json_path)
    data = raw["data"] if isinstance(raw, dict) and isinstance(raw.get("data"), dict) else raw
    apps = data.get("apps", [])
    if not apps:
        raise ValueError("No apps found in order data")
    return [extract_app_summary(app) for app in apps]


def output_certificates(json_path):
    entries = load_all_order_data(json_path)
    print(f"Found {len(entries)} app(s) in order\n")
    for i, e in enumerate(entries, 1):
        print(f"[{i}/{len(entries)}] {e['title']}")
        print(f"  证书持有人: {e['realName']}")
        print(f"  存证时间:   {e['preservationTime']}")
        print(f"  备案号:     {e['preservationId']}")
        print(f"  文件哈希:   {e['fileHash']}")
        print(f"  证书链接:   {e['certUrl']}")
        print()
    # JSON tail for AI consumption
    print("---CERT_JSON---")
    print(json.dumps(entries, ensure_ascii=False, indent=2))
    return entries


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_cert.py <order_detail.json>")
        sys.exit(1)
    output_certificates(sys.argv[1])

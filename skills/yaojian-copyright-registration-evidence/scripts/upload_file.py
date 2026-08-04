"""
Upload file to OSS.
Usage: python upload_file.py <file_path>
Output: ossFileId for order submission
"""

import sys

from common import ensure_dirs, http_upload_file, auth_header


def upload_file(file_path):
    """Upload file to OSS, return ossFileId."""
    ensure_dirs()

    result = http_upload_file(
        "/xrl-cloud-asset/v7/file-upload/microchain",
        file_path,
        headers=auth_header()
    )

    if result.get("success") and result.get("data"):
        oss_file_id = result["data"].get("id", "")
        print(f"UPLOAD_SUCCESS|ossFileId={oss_file_id}|file={file_path}")
        return oss_file_id
    else:
        msg = result.get("message", str(result))
        print(f"UPLOAD_FAILED|message={msg}")
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python upload_file.py <file_path>")
        sys.exit(1)

    upload_file(sys.argv[1])

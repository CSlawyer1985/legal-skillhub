"""
Calculate SHA512 hash of a file.
Usage: python calc_hash.py <file_path>
Output: 128-char lowercase hex SHA512 hash
"""

import hashlib
import sys


def calc_sha512(file_path):
    """Calculate SHA512 hash of file, return 128-char lowercase hex string."""
    sha512 = hashlib.sha512()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            sha512.update(chunk)
    return sha512.hexdigest().lower()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python calc_hash.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    hash_value = calc_sha512(file_path)
    print(f"HASH_RESULT|file={file_path}|hash={hash_value}")

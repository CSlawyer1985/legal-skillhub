#!/usr/bin/env bash
# 打包 legal-research-report 为 zip（排除隐藏文件与打包产物自身）
set -euo pipefail
cd "$(dirname "$0")/.."
SKILL_DIR="$(basename "$PWD")"
OUT="${1:-${SKILL_DIR}.zip}"
cd ..
rm -f "$OUT"
zip -r "$OUT" "$SKILL_DIR" -x "*/.*" "$SKILL_DIR/*.zip"
echo "已打包：$(pwd)/$OUT"

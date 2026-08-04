#!/usr/bin/env bash

# Chinese SEO & Compliance Checker - Suggestions Script
# Get safe replacement suggestions for banned words.
# Usage:
#   ./suggestions.sh "美白"     # Query specific word
#   ./suggestions.sh            # Show all suggestions

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../.env"

# Load env
if [[ -f "$ENV_FILE" ]]; then
  while IFS='=' read -r key value; do
    case "$key" in
      CN_SEO_TOKEN|CN_SEO_API_BASE)
        export "$key=$value"
        ;;
    esac
  done < <(grep -E '^(CN_SEO_TOKEN|CN_SEO_API_BASE)=' "$ENV_FILE" 2>/dev/null || true)
fi

# Defaults
API_BASE="${CN_SEO_API_BASE:-https://1341839497-2yuxt6z58d.ap-guangzhou.tencentscf.com}"
API_BASE="${API_BASE%/}"
KEYWORD="${1:-}"

# Call API
if [[ -n "$KEYWORD" ]]; then
  RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X GET "${API_BASE}/suggestions?keyword=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$KEYWORD'))" 2>/dev/null || echo "$KEYWORD")" \
    --connect-timeout 10 \
    --max-time 15)
else
  RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X GET "${API_BASE}/suggestions" \
    --connect-timeout 10 \
    --max-time 15)
fi

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [[ "$HTTP_CODE" != "200" ]]; then
  echo "❌ API请求失败 (HTTP $HTTP_CODE)"
  exit 1
fi

# Format output
if [[ -n "$KEYWORD" ]]; then
  RESULT=$(echo "$BODY" | jq -r --arg kw "$KEYWORD" '
    .data[$kw] // null |
    if . == null then null
    else . | join(", ")
    end
  ')

  if [[ "$RESULT" != "null" && -n "$RESULT" ]]; then
    echo "\"${KEYWORD}\""
    echo "建议替换: ${RESULT}"
  else
    echo "未找到 \"${KEYWORD}\" 的替换建议。"
    echo "该词可能不在违禁词库中，但仍建议使用更温和的表述。"
  fi
else
  echo "# 违禁词安全替换建议库"
  echo ""

  echo "$BODY" | jq -r '
    .data | to_entries[:80][] |
    "  - " + .key + " → " + (.value | join(", "))
  '

  TOTAL=$(echo "$BODY" | jq -r '.total // (.data | length)')
  echo ""
  echo "共 ${TOTAL} 条替换建议"
fi

#!/bin/bash
# Ask Guardian AI assistant a compliance question
set -euo pipefail

API_URL="${GUARDIAN_API_URL:-https://guardian-compliance.fly.dev}"
TOKEN="${GUARDIAN_TOKEN:-}"
QUESTION="${1:-}"

if [ -z "$TOKEN" ]; then
  echo "Error: GUARDIAN_TOKEN not set. Please configure your Guardian token."
  exit 1
fi

if [ -z "$QUESTION" ]; then
  echo "Error: No question provided. Usage: guardian-ask.sh \"your question here\""
  exit 1
fi

# Escape question for JSON
JSON_QUESTION=$(printf '%s' "$QUESTION" | jq -Rs .)

result=$(curl -sf -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"message\": $JSON_QUESTION, \"history\": []}" \
  "$API_URL/api/chat" 2>/dev/null) || {
  echo "Error: Could not reach Guardian assistant. Check your token and network connection."
  exit 1
}

echo "$result" | jq -r '.reply // "No response received."'

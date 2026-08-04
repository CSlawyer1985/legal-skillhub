#!/bin/bash
# List all documents in Guardian data room
set -euo pipefail

API_URL="${GUARDIAN_API_URL:-https://guardian-compliance.fly.dev}"
TOKEN="${GUARDIAN_TOKEN:-}"

if [ -z "$TOKEN" ]; then
  echo "Error: GUARDIAN_TOKEN not set. Please configure your Guardian token."
  exit 1
fi

docs=$(curl -sf -H "Authorization: Bearer $TOKEN" "$API_URL/api/dashboard/documents" 2>/dev/null) || {
  echo "Error: Could not reach Guardian API. Check your token and network connection."
  exit 1
}

count=$(echo "$docs" | jq 'length')

if [ "$count" = "0" ] || [ -z "$count" ]; then
  echo "No documents uploaded yet. Visit guardian-compliance.fly.dev to upload your I-983, employment letter, tax returns, or I-20."
  exit 0
fi

echo "# Documents in Data Room ($count files)"
echo ""
echo "$docs" | jq -r '.[] | "- **\(.filename)** (\(.doc_type | gsub("_"; " ") | ascii_upcase), \((.file_size / 1024 * 10 | floor) / 10) KB) — uploaded \(.uploaded_at[:10])"'

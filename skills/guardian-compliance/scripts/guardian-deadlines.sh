#!/bin/bash
# Fetch upcoming compliance deadlines from Guardian API
set -euo pipefail

API_URL="${GUARDIAN_API_URL:-https://guardian-compliance.fly.dev}"
TOKEN="${GUARDIAN_TOKEN:-}"

if [ -z "$TOKEN" ]; then
  echo "Error: GUARDIAN_TOKEN not set. Please configure your Guardian token."
  exit 1
fi

timeline=$(curl -sf -H "Authorization: Bearer $TOKEN" "$API_URL/api/dashboard/timeline" 2>/dev/null) || {
  echo "Error: Could not reach Guardian API. Check your token and network connection."
  exit 1
}

deadlines=$(echo "$timeline" | jq -r '.deadlines[]?')

if [ -z "$deadlines" ]; then
  echo "No upcoming deadlines tracked. Upload documents to Guardian to generate deadline tracking."
  exit 0
fi

echo "# Upcoming Deadlines"
echo ""

# Overdue first
echo "$timeline" | jq -r '.deadlines[] | select(.days < 0) | "- OVERDUE (\(-.days) days ago): **\(.title)** — \(.date)"'

# Due within 7 days
echo "$timeline" | jq -r '.deadlines[] | select(.days >= 0 and .days <= 7) | "- **\(.days) days:** \(.title) — \(.date)"'

# Due within 30 days
echo "$timeline" | jq -r '.deadlines[] | select(.days > 7 and .days <= 30) | "- \(.days) days: \(.title) — \(.date)"'

# Further out
echo "$timeline" | jq -r '.deadlines[] | select(.days > 30) | "- \(.days) days: \(.title) — \(.date)"'

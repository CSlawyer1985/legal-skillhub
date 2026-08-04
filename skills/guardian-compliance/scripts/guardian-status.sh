#!/bin/bash
# Fetch full compliance status from Guardian API
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

stats=$(curl -sf -H "Authorization: Bearer $TOKEN" "$API_URL/api/dashboard/stats" 2>/dev/null) || stats='{}'

echo "# Guardian Compliance Status"
echo ""

# Stats
docs=$(echo "$stats" | jq -r '.documents // 0')
risks=$(echo "$stats" | jq -r '.risks // 0')
echo "Documents: $docs | Active risks: $risks"
echo ""

# Critical findings
critical=$(echo "$timeline" | jq -r '.findings[]? | select(.severity == "critical")')
if [ -n "$critical" ]; then
  echo "## Critical Issues"
  echo ""
  echo "$timeline" | jq -r '.findings[] | select(.severity == "critical") | "- **\(.title)**\n  Action: \(.action)\n"'
fi

# Warnings
warnings=$(echo "$timeline" | jq -r '.findings[]? | select(.severity == "warning")')
if [ -n "$warnings" ]; then
  echo "## Warnings"
  echo ""
  echo "$timeline" | jq -r '.findings[] | select(.severity == "warning") | "- **\(.title)**\n  Action: \(.action)\n"'
fi

if [ -z "$critical" ] && [ -z "$warnings" ]; then
  echo "No active compliance findings. Looking good."
  echo ""
fi

# Deadlines
deadlines=$(echo "$timeline" | jq -r '.deadlines[]?')
if [ -n "$deadlines" ]; then
  echo "## Upcoming Deadlines"
  echo ""
  echo "$timeline" | jq -r '.deadlines[] | if .days < 0 then "- OVERDUE (\(-.days)d ago): \(.title) — \(.date)" elif .days <= 30 then "- **\(.days) days:** \(.title) — \(.date)" else "- \(.days) days: \(.title) — \(.date)" end'
  echo ""
fi

# Key facts
facts=$(echo "$timeline" | jq -r '.key_facts[]?')
if [ -n "$facts" ]; then
  echo "## Key Facts"
  echo ""
  echo "$timeline" | jq -r '.key_facts[] | "- **\(.label):** \(.value)"'
fi

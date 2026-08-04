#!/usr/bin/env bash
# Global Compliance Regulations - Query compliance regulations by market
set -euo pipefail
API_BASE="https://1341839497-2yuxt6z58d.ap-guangzhou.tencentscf.com"
MARKET="${1:-}"
if [[ -z "$MARKET" || "$MARKET" == "--all" ]]; then
  curl -s "${API_BASE}/regulations" | jq -r '.data | to_entries[] | "🌍 \(.key) — \(.value.name): 罚款上限\(.value.maxFine)"'
else
  curl -s "${API_BASE}/regulations?market=${MARKET}" | jq -r '.data | to_entries[0] | .value | "🌍 \(.name)\n核心法规:\n" + (.keyRegulations | map("  📜 " + .) | join("\n")) + "\n罚款上限: \(.maxFine)"'
fi

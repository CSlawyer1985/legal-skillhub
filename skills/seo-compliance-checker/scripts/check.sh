#!/usr/bin/env bash

# Chinese SEO & Compliance Checker - Check Script
# Detects banned words and SEO compliance issues in Chinese text.
# Usage:
#   ./check.sh "要检测的文案"
#   ./check.sh "要检测的文案" --platform xiaohongshu --keywords "美白,面膜"
#   ./check.sh --file input.txt --platform baidu --keywords "SEO优化"

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
TOKEN="${CN_SEO_TOKEN:-}"
MONTHLY_LIMIT=20
USAGE_FILE="$HOME/.cn-seo-usage"

# Parse arguments
TEXT=""
FILE=""
PLATFORM=""
KEYWORDS=""
TITLE=""
NER=true

while [[ $# -gt 0 ]]; do
  case "$1" in
    --file)
      FILE="$2"
      shift 2
      ;;
    --platform)
      PLATFORM="$2"
      shift 2
      ;;
    --keywords)
      KEYWORDS="$2"
      shift 2
      ;;
    --title)
      TITLE="$2"
      shift 2
      ;;
    --no-ner)
      NER=false
      shift
      ;;
    --help|-h)
      cat << 'HELP'
中文SEO合规检测工具

用法:
  ./check.sh "要检测的文案"
  ./check.sh "要检测的文案" --platform xiaohongshu --keywords "美白,面膜"
  ./check.sh --file input.txt --platform baidu --keywords "SEO优化" --title "标题"

选项:
  --platform   目标平台: baidu/xiaohongshu/douyin/taobao/jd
  --keywords   关键词，逗号分隔
  --title      标题文本
  --file       从文件读取内容
  --no-ner     关闭NER过滤（更严格检测）

环境变量:
  CN_SEO_API_BASE  API地址（默认: https://1341839497-2yuxt6z58d.ap-guangzhou.tencentscf.com）
  CN_SEO_TOKEN     无限使用Token（免费用户每月20次）

获取无限使用Token: https://github.com/lm203688/cn-seo-optimizer/issues
HELP
      exit 0
      ;;
    *)
      TEXT="$1"
      shift
      ;;
  esac
done

# Read from file if specified
if [[ -n "$FILE" ]]; then
  if [[ ! -f "$FILE" ]]; then
    echo "❌ 文件不存在: $FILE"
    exit 1
  fi
  TEXT=$(cat "$FILE")
fi

if [[ -z "$TEXT" ]]; then
  echo "❌ 请提供要检测的文本内容"
  echo "用法: ./check.sh \"要检测的文案\" 或 ./check.sh --file input.txt"
  exit 1
fi

# Check free usage limit
check_usage() {
  if [[ -n "$TOKEN" ]]; then
    return 0
  fi

  local current_month=$(date +%Y-%m)
  if [[ -f "$USAGE_FILE" ]]; then
    local stored_month=$(head -1 "$USAGE_FILE" 2>/dev/null || echo "")
    local count=$(tail -1 "$USAGE_FILE" 2>/dev/null || echo "0")

    if [[ "$stored_month" != "$current_month" ]]; then
      echo "$current_month" > "$USAGE_FILE"
      echo "1" >> "$USAGE_FILE"
      return 0
    fi

    if [[ "$count" -ge "$MONTHLY_LIMIT" ]]; then
      cat << 'QUOTA_MSG'
⚠️ 免费额度已用完（每月 20 次免费检测）。

💡 获取无限使用 Token: https://github.com/lm203688/cn-seo-optimizer/issues

免费额度每月1日自动重置。
QUOTA_MSG
      exit 1
    fi

    # Increment
    echo "$current_month" > "$USAGE_FILE"
    echo $((count + 1)) >> "$USAGE_FILE"
  else
    echo "$current_month" > "$USAGE_FILE"
    echo "1" >> "$USAGE_FILE"
  fi
}

check_usage

# Build API request
AUTH_HEADER=""
if [[ -n "$TOKEN" ]]; then
  AUTH_HEADER="-H \"Authorization: Bearer $TOKEN\""
fi

# Build JSON payload
JSON_PAYLOAD=$(jq -n \
  --arg text "$TEXT" \
  --arg platform "$PLATFORM" \
  --arg keywords "$KEYWORDS" \
  --arg title "$TITLE" \
  --argjson ner "$NER" \
  '{
    text: $text,
    platform: (if $platform == "" then null else $platform end),
    keywords: (if $keywords == "" then null else $keywords end),
    title: (if $title == "" then null else $title end),
    ner_filter: $ner
  }')

# Call API
RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "${API_BASE}/check" \
  -H "Content-Type: application/json" \
  ${AUTH_HEADER:+-H "Authorization: Bearer $TOKEN"} \
  -d "$JSON_PAYLOAD" \
  --connect-timeout 10 \
  --max-time 30)

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

# Handle errors
if [[ "$HTTP_CODE" == "429" ]]; then
  echo "⚠️ 免费额度已用完（每月 20 次免费检测）。"
  echo ""
  echo "💡 获取无限使用 Token: https://github.com/lm203688/cn-seo-optimizer/issues"
  exit 1
fi

if [[ "$HTTP_CODE" != "200" ]]; then
  echo "❌ API请求失败 (HTTP $HTTP_CODE)"
  echo "$BODY" | jq -r '.msg // "未知错误"' 2>/dev/null || echo "$BODY"
  exit 1
fi

# Parse response
API_CODE=$(echo "$BODY" | jq -r '.code')
if [[ "$API_CODE" != "0" ]]; then
  echo "❌ 检测失败: $(echo "$BODY" | jq -r '.msg')"
  exit 1
fi

# Format output
TOTAL=$(echo "$BODY" | jq -r '.data.totalIssues')
HAS_HIGH=$(echo "$BODY" | jq -r '.data.hasHighRisk')
STAT_HIGH=$(echo "$BODY" | jq -r '.data.stats.高 // 0')
STAT_MID=$(echo "$BODY" | jq -r '.data.stats.中 // 0')
STAT_LOW=$(echo "$BODY" | jq -r '.data.stats.低 // 0')
STAT_TIP=$(echo "$BODY" | jq -r '.data.stats.提示 // 0')
TEXT_LEN=$(echo "$BODY" | jq -r '.data.textLength')

if [[ "$TOTAL" -eq 0 ]]; then
  echo "✅ 检测通过！未发现违禁词或SEO问题。"
  echo ""
  echo "文本长度: ${TEXT_LEN}字"
else
  echo "⚠️ 检测到 ${TOTAL} 个问题"
  echo ""
  echo "风险概览: 🔴 高危=${STAT_HIGH} | 🟡 中危=${STAT_MID} | 🔵 低危=${STAT_LOW} | 💡 提示=${STAT_TIP}"
  echo ""

  if [[ "$HAS_HIGH" == "true" ]]; then
    echo "🚨 警告: 文本包含高危词汇，可能导致罚款或内容删除！"
    echo ""
  fi

  # Output banned words by risk level
  for LEVEL in "高" "中" "低" "提示"; do
    WORDS=$(echo "$BODY" | jq -r --arg level "$LEVEL" '[.data.bannedWords[] | select(.level == $level)] | length')
    if [[ "$WORDS" -gt 0 ]]; then
      case "$LEVEL" in
        高)    echo "🔴 高危（可能导致罚款/封号）" ;;
        中)    echo "🟡 中危（可能导致限流/降权）" ;;
        低)    echo "🔵 低危（建议修改）" ;;
        提示)  echo "💡 提示（注意措辞）" ;;
      esac

      echo "$BODY" | jq -r --arg level "$LEVEL" '
        .data.bannedWords[] | select(.level == $level) |
        "  - \"" + .keyword + "\" — 分类: " + .category +
        (if .suggestion and (.suggestion | length) > 0
         then " → 建议替换: " + (.suggestion | join(", "))
         else "" end)
      '
      echo ""
    fi
  done

  # Output SEO issues
  SEO_COUNT=$(echo "$BODY" | jq -r '.data.seoIssues | length')
  if [[ "$SEO_COUNT" -gt 0 ]]; then
    echo "📊 SEO优化建议"
    echo "$BODY" | jq -r '.data.seoIssues[] |
      "  - [" + .level + "] " + .message
    '
    echo ""
  fi
fi

# Show usage reminder for free users
if [[ -z "$TOKEN" ]]; then
  USED=$(echo "$BODY" | jq -r '.data.usage.used // 0')
  LIMIT=$(echo "$BODY" | jq -r '.data.usage.limit // 20')
  echo "📊 本月已用: ${USED}/${LIMIT} 次 | 获取无限Token: https://github.com/lm203688/cn-seo-optimizer/issues"
fi

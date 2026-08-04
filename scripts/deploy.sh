#!/usr/bin/env bash
# Legal SkillHub 一键部署脚本
# 用法：bash scripts/deploy.sh [--no-push]
# 流程：更新 HTML 缓存版本号 → 提交 → 推送 → Cloudflare Pages 部署
set -euo pipefail
cd "$(dirname "$0")/.."

V=$(git rev-parse --short HEAD)

echo "▶ 更新 HTML 缓存版本号 → ?v=$V"
find docs -name "*.html" -print0 | xargs -0 sed -i '' "s/?v=[0-9a-f]\{7\}/?v=$V/g"

echo "▶ 提交版本号变更"
git add docs/
if git diff --cached --quiet; then
  echo "  （无版本号变更）"
else
  git commit -m "chore: bump asset cache version to $V" -q
fi

echo "▶ 推送"
git push origin main

echo "▶ 部署 Cloudflare Pages"
wrangler pages deploy docs --project-name=legal-skillhub --branch main --commit-dirty=true

echo "✅ 部署完成：https://skill.chenshi.ai"

#!/usr/bin/env bash
# legal-research-report 环境检测辅助脚本
# 作用：提示使用本 Skill 的 agent 应检测哪些能力。agent 也可以不运行本脚本，
# 直接检查自身工具列表完成判断。本脚本不修改任何系统状态，仅输出建议。
set -euo pipefail

cat << 'EOF'
legal-research-report 环境检测指引
==================================

请按以下顺序判断当前环境，选择运行模式：

[1] 检查 agent 当前可用工具中是否存在法律数据库 MCP 工具，例如：
    - mcp__fazhi-law__legal_article_search / case_search / webpage_search
    - 或其他法律数据库检索工具（北大法宝 / 元典 / 威科等）
    → 存在：使用【模式 A】（references/fazhi-mode.md）

[2] 否则，检查 agent 是否具备通用网页搜索能力：
    - WebSearch / WebFetch / web_search / browser 等
    → 存在：使用【模式 B】（references/fallback-mode.md）

[3] 两者皆无：
    → 只能基于训练知识撰写框架，必须在报告中显著标注
      "所有法条与案例未经检索核验，必须人工复核后方可使用"。

本机补充检查（可选）：
EOF

if command -v curl >/dev/null 2>&1; then
  if curl -s -o /dev/null -w "%{http_code}" --max-time 5 https://flk.npc.gov.cn | grep -q "200\|301\|302"; then
    echo "  ✓ 国家法律法规数据库 (flk.npc.gov.cn) 可访问"
  else
    echo "  ✗ 国家法律法规数据库暂不可访问（不影响模式 A）"
  fi
else
  echo "  - 未检测到 curl，跳过网络检查"
fi

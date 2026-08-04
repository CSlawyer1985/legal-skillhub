#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG="$SKILL_DIR/scripts/config.json"
TMP_DIR="$SKILL_DIR/tmp_download"

if [ ! -f "$CONFIG" ]; then
    echo "❌ 配置文件不存在: $CONFIG"
    echo "  请先创建 config.json 并填入 token："
    echo '  {"data_token": "xxx", "templates_token": "xxx"}'
    exit 1
fi

DATA_TOKEN=$(python -c "import json; print(json.load(open('$CONFIG'))['data_token'])" 2>/dev/null)
TPL_TOKEN=$(python -c "import json; print(json.load(open('$CONFIG'))['templates_token'])" 2>/dev/null)

if [ -z "$DATA_TOKEN" ] || [ "$DATA_TOKEN" = "YOUR_TOKEN_HERE" ]; then
    echo "❌ data_token 未配置，请编辑 scripts/config.json"
    exit 1
fi
if [ -z "$TPL_TOKEN" ] || [ "$TPL_TOKEN" = "YOUR_TOKEN_HERE" ]; then
    echo "❌ templates_token 未配置，请编辑 scripts/config.json"
    exit 1
fi

echo "============================================"
echo "  更新向量知识库数据"
echo "============================================"
echo ""

# ── 1. 删除旧数据 ──
echo "=== [1/4] 清理旧数据 ==="
if [ -d "$SKILL_DIR/cy_data" ]; then
    rm -rf "$SKILL_DIR/cy_data"
    echo "  ✅ 已删除 cy_data/"
else
    echo "  ⏭️  cy_data/ 不存在，跳过"
fi
if [ -d "$SKILL_DIR/cy_templates" ]; then
    rm -rf "$SKILL_DIR/cy_templates"
    echo "  ✅ 已删除 cy_templates/"
else
    echo "  ⏭️  cy_templates/ 不存在，跳过"
fi

# ── 2. 下载新数据 ──
echo ""
echo "=== [2/4] 下载新数据 ==="
mkdir -p "$TMP_DIR"

echo "  下载 cy_data..."
curl -fSL -o "$TMP_DIR/data.zip" "http://dow.fupukeji.com/download/data?token=${DATA_TOKEN}"
echo "  ✅ cy_data 下载完成"

echo "  下载 cy_templates..."
curl -fSL -o "$TMP_DIR/templates.zip" "http://dow.fupukeji.com/download/templates?token=${TPL_TOKEN}"
echo "  ✅ cy_templates 下载完成"

# ── 3. 解压到根目录 ──
echo ""
echo "=== [3/4] 解压到根目录 ==="
echo "  解压 cy_data..."
unzip -qo "$TMP_DIR/data.zip" -d "$SKILL_DIR"
echo "  ✅ cy_data 解压完成"

echo "  解压 cy_templates..."
unzip -qo "$TMP_DIR/templates.zip" -d "$SKILL_DIR"
echo "  ✅ cy_templates 解压完成"

# ── 4. 清理临时文件 ──
echo ""
echo "=== [4/4] 清理临时文件 ==="
rm -rf "$TMP_DIR"
echo "  ✅ 清理完成"

echo ""
echo "============================================"
echo "  ✅ 数据更新完成"
echo "============================================"

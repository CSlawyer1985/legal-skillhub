#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYPI_MIRROR="${1:-https://pypi.tuna.tsinghua.edu.cn/simple}"
export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"

echo "============================================"
echo "  中文合同起草 Skill — 初始化"
echo "============================================"
echo ""

# ── 0. 清理旧 .venv ──
echo "=== [0/5] 清理旧环境 ==="
if [ -d "$SKILL_DIR/.venv" ]; then
    echo "  删除旧的 .venv/（来自 uv 时代）..."
    rm -rf "$SKILL_DIR/.venv"
    echo "  ✅ 已清理"
else
    echo "  ⏭️  .venv/ 不存在，跳过"
fi

# ── 1. 安装依赖 ──
echo "=== [1/5] 安装 Python 依赖 ==="
python3 -m pip install -r "$SKILL_DIR/requirements.txt" -i "$PYPI_MIRROR" --quiet 2>/dev/null || \
python -m pip install -r "$SKILL_DIR/requirements.txt" -i "$PYPI_MIRROR" --quiet
echo "  依赖安装完成"

# ── 2. 下载数据（条件触发） ──
echo ""
echo "=== [2/5] 检查并下载向量数据 ==="
CONFIG_FILE="$SKILL_DIR/scripts/config.json"
NEED_DOWNLOAD=false

if [ -f "$CONFIG_FILE" ]; then
    TOKEN_VALID=$(python -c "
import json
try:
    c = json.load(open('$CONFIG_FILE'))
    if c.get('data_token') and c['data_token'] != 'YOUR_TOKEN_HERE' and c.get('templates_token') and c['templates_token'] != 'YOUR_TOKEN_HERE':
        print('yes')
    else:
        print('no')
except: print('no')
" 2>/dev/null || echo "no")
    if [ "$TOKEN_VALID" = "yes" ]; then
        if [ ! -d "$SKILL_DIR/cy_data" ] || [ ! -d "$SKILL_DIR/cy_templates" ]; then
            NEED_DOWNLOAD=true
            echo "  数据缺失，开始下载..."
            bash "$SKILL_DIR/scripts/download_data.sh"
        else
            echo "  ✅ 数据目录已存在，跳过下载（如需更新请运行: bash scripts/download_data.sh）"
        fi
    else
        echo "  ⚠️  config.json 中 token 未配置，跳过自动下载"
        echo "  💡 编辑 scripts/config.json 填入 token 后可自动下载"
    fi
else
    echo "  ⚠️  config.json 不存在，跳过自动下载"
fi

# ── 3. 检查向量知识库 ──
echo ""
echo "=== [3/5] 检查向量知识库 ==="
LAW_OK=false
TPL_OK=false

if [ -d "$SKILL_DIR/cy_data" ]; then
    FILE_COUNT=$(find "$SKILL_DIR/cy_data" -type f 2>/dev/null | wc -l)
    if [ "$FILE_COUNT" -gt 5 ]; then
        LAW_OK=true
        echo "  ✅ cy_data（法律）: $FILE_COUNT 个文件"
    else
        echo "  ⚠️  cy_data 文件不完整（仅 $FILE_COUNT 个文件）"
    fi
else
    echo "  ❌ cy_data/ 不存在"
fi

if [ -d "$SKILL_DIR/cy_templates" ]; then
    FILE_COUNT=$(find "$SKILL_DIR/cy_templates" -type f 2>/dev/null | wc -l)
    if [ "$FILE_COUNT" -gt 5 ]; then
        TPL_OK=true
        echo "  ✅ cy_templates（模板）: $FILE_COUNT 个文件"
    else
        echo "  ⚠️  cy_templates 文件不完整（仅 $FILE_COUNT 个文件）"
    fi
else
    echo "  ❌ cy_templates/ 不存在"
fi

# ── 4. 测试搜索 ──
echo ""
echo "=== [4/5] 测试向量搜索 ==="
if [ "$LAW_OK" = true ]; then
    echo "  测试法律检索（押金条款）..."
    RESULT=$(python "$SKILL_DIR/scripts/search.py" law --query "押金" --contract-type rental --topk 1 2>/dev/null || echo "FAILED")
    if echo "$RESULT" | grep -q "law_name"; then
        LAW_NAME=$(echo "$RESULT" | python -c "import sys,json; d=json.load(sys.stdin); print(d[0]['law_name'][:30])" 2>/dev/null || echo "解析失败")
        echo "  ✅ 法律检索成功: $LAW_NAME"
    else
        echo "  ❌ 法律检索失败"
        echo "  $RESULT" | head -3
    fi
else
    echo "  ⏭️  跳过法律检索（数据缺失）"
fi

if [ "$TPL_OK" = true ]; then
    echo "  测试模板检索（租房合同）..."
    RESULT=$(python "$SKILL_DIR/scripts/search.py" template --query "租房" --type rental --topk 1 2>/dev/null || echo "FAILED")
    if echo "$RESULT" | grep -q "filename"; then
        FNAME=$(echo "$RESULT" | python -c "import sys,json; d=json.load(sys.stdin); print(d[0]['filename'][:30])" 2>/dev/null || echo "解析失败")
        echo "  ✅ 模板检索成功: $FNAME"
    else
        echo "  ❌ 模板检索失败"
        echo "  $RESULT" | head -3
    fi
else
    echo "  ⏭️  跳过模板检索（数据缺失）"
fi

# ── 5. 完成 ──
echo ""
echo "=== [5/5] 完成 ==="
if [ "$LAW_OK" = true ] || [ "$TPL_OK" = true ]; then
    echo "  初始化完成，向量搜索可用，可以开始起草合同"
fi
echo "============================================"

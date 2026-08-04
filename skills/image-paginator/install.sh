#!/bin/bash
# ============================================================
#  image-paginator（律师证据长截图转PDF）一键安装脚本
#  用法: bash install.sh
# ============================================================
set -e

SKILL_DIR="${HOME}/.qclaw/skills/image-paginator"
ZIP_URL="https://github.com/wux818738-alt/openclaw-skill-image-paginator/archive/refs/heads/main.zip"
ZIP_FILE="/tmp/image-paginator-main.zip"

echo "📦 正在安装 image-paginator（律师证据长截图转PDF）..."
echo "   目标目录: $SKILL_DIR"

# 清理旧版本
if [ -d "$SKILL_DIR" ]; then
    echo "   🗑️  移除旧版本 ..."
    rm -rf "$SKILL_DIR"
fi

# 下载 zip
echo "   ⬇️  下载: $ZIP_URL"
curl -fsSL "$ZIP_URL" -o "$ZIP_FILE"

# 解压（自动解压到 image-paginator-main/）
UNZIP_DIR=$(mktemp -d)
unzip -q "$ZIP_FILE" -d "$UNZIP_DIR"
DIR_NAME=$(ls "$UNZIP_DIR")

# 移动到目标目录
mv "${UNZIP_DIR}/${DIR_NAME}" "$SKILL_DIR"
rm -rf "$ZIP_FILE" "$UNZIP_DIR"

# 安装 Python 依赖
echo "   🐍 安装 Python 依赖 (fpdf2, Pillow) ..."
if command -v pip3 &>/dev/null; then
    pip3 install --quiet fpdf2 Pillow
elif command -v pip &>/dev/null; then
    pip install --quiet fpdf2 Pillow
else
    echo "   ⚠️  未找到 pip3，请手动运行: pip3 install fpdf2 Pillow"
fi

echo ""
echo "✅ 安装完成！"
echo ""
echo "   使用方法："
echo "   python ${SKILL_DIR}/scripts/slice_n_pdf.py <图片路径> -d <输出目录> [-o <文件名>]"
echo ""
echo "   示例："
echo "   python ${SKILL_DIR}/scripts/slice_n_pdf.py ~/Desktop/聊天记录.jpg \\"
echo "     -d ~/Desktop -o 聊天证据.pdf --clean"
echo ""

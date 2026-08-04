#!/usr/bin/env bash
# html_to_pdf.sh —— 诉讼可视化Plus 自带 HTML→PDF 转换脚本
#
# 采用「系统 Google Chrome 原生无头打印」方案（零浏览器下载、不依赖 puppeteer，
# 本机最稳最快）。适用于 macOS / Linux（需已安装 Google Chrome 或 Chromium）。
#
# 用法：
#   bash html_to_pdf.sh "<输入.html 绝对路径>" "<输出.pdf 绝对路径>"
#
# 说明：
#   - 输入为本地文件时，脚本自动将绝对路径做 URL 编码并以 file:// 传入 Chrome；
#     含中文/空格的路径无需手动编码。
#   - 默认 A4、纵向、含背景色（print-to-pdf 默认即打印背景）。
#   - 若本机未检测到 Google Chrome，则回退提示改用 puppeteer 或浏览器/WPS 打印。

set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "用法: bash html_to_pdf.sh <输入.html 绝对路径> <输出.pdf 绝对路径>" >&2
  exit 1
fi

INPUT="$1"
OUTPUT="$2"

if [ ! -f "$INPUT" ]; then
  echo "错误：输入 HTML 文件不存在：$INPUT" >&2
  exit 2
fi

# 定位 Google Chrome / Chromium 可执行文件
CHROME_BIN=""
if [ -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then
  CHROME_BIN="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
elif command -v google-chrome >/dev/null 2>&1; then
  CHROME_BIN="$(command -v google-chrome)"
elif command -v chromium >/dev/null 2>&1; then
  CHROME_BIN="$(command -v chromium)"
elif command -v chromium-browser >/dev/null 2>&1; then
  CHROME_BIN="$(command -v chromium-browser)"
fi

if [ -z "$CHROME_BIN" ]; then
  echo "未检测到 Google Chrome / Chromium。请先安装 Google Chrome，或改用：「PUPPETEER_EXECUTABLE_PATH=... npm install puppeteer」后调用 puppeteer 方案；也可在浏览器/WPS 中直接打印该 HTML 为 PDF。" >&2
  exit 3
fi

# 将本地绝对路径转为 file:// URL（含中文/空格做百分号编码）
DIR="$(cd "$(dirname "$INPUT")" && pwd)"
BASE="$(basename "$INPUT")"
# 优先使用受管 Python 运行时做稳健 URL 编码；否则回退系统 python3
PY_BIN="/Users/gongjiayong/.workbuddy/binaries/python/versions/3.13.12/bin/python3"
if [ ! -x "$PY_BIN" ]; then
  PY_BIN="$(command -v python3 || echo python3)"
fi
# 用 python 做稳健的 URL 编码（保留 / : 等 file scheme 必需字符）
FILE_URL="$($PY_BIN - "$DIR" "$BASE" <<'PY'
import sys, urllib.parse, pathlib
d, b = sys.argv[1], sys.argv[2]
p = pathlib.Path(d) / b
# 仅对路径各段做 quote，保留 file:// 结构
encoded = "/".join(urllib.parse.quote(part, safe="") for part in p.as_posix().split("/"))
# 标准 file URI 为三斜杠：file:///abs/path；p.as_posix() 已含首部 "/"，
# 故此处仅补 "file://" 前缀，避免拼成四斜杠 file://// 导致 Chrome 加载失败。
print("file://" + encoded)
PY
)"

# 确保输出目录存在
OUT_DIR="$(dirname "$OUTPUT")"
mkdir -p "$OUT_DIR"

echo "使用 Chrome: $CHROME_BIN"
echo "输入 URL: $FILE_URL"
echo "输出 PDF: $OUTPUT"

# 兼容不同 Chrome 版本：--no-pdf-header-footer 在较旧版本不支持，需探测。
NO_HF_FLAG=""
if "$CHROME_BIN" --headless --no-sandbox --disable-gpu --no-pdf-header-footer --dump-dom "file:///" >/dev/null 2>&1; then
  NO_HF_FLAG="--no-pdf-header-footer"
fi

"$CHROME_BIN" --headless --no-sandbox --disable-gpu $NO_HF_FLAG \
  --print-to-pdf="$OUTPUT" "$FILE_URL" >/dev/null 2>&1

if [ -f "$OUTPUT" ] && [ -s "$OUTPUT" ]; then
  echo "✅ PDF 生成成功：$OUTPUT"
else
  echo "❌ PDF 生成失败，请检查 Chrome 是否正常或改用 puppeteer / 浏览器打印。" >&2
  exit 4
fi

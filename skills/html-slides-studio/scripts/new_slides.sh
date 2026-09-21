#!/usr/bin/env sh

set -eu

usage() {
  cat <<'EOF'
Usage:
  sh ./scripts/new_slides.sh --output ./my-deck.html [--watermark-main "Main"] [--watermark-sub "Sub"]
EOF
}

OUTPUT_PATH=""
WATERMARK_MAIN=""
WATERMARK_SUB=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --output|-o)
      OUTPUT_PATH="${2:-}"
      shift 2
      ;;
    --watermark-main)
      WATERMARK_MAIN="${2:-}"
      shift 2
      ;;
    --watermark-sub)
      WATERMARK_SUB="${2:-}"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [ -z "$OUTPUT_PATH" ]; then
  echo "Missing required argument: --output" >&2
  usage >&2
  exit 1
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
SKILL_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
TEMPLATE="$SKILL_ROOT/assets/slides-template-v3.html"

if [ ! -f "$TEMPLATE" ]; then
  echo "Template not found: $TEMPLATE" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT_PATH")"
cp "$TEMPLATE" "$OUTPUT_PATH"

if [ -n "$WATERMARK_MAIN$WATERMARK_SUB" ]; then
  if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 is required when using watermark arguments." >&2
    exit 1
  fi

  python3 - "$OUTPUT_PATH" "$WATERMARK_MAIN" "$WATERMARK_SUB" <<'PY'
import html
import pathlib
import re
import sys

path = pathlib.Path(sys.argv[1])
watermark_main = sys.argv[2]
watermark_sub = sys.argv[3]
text = path.read_text(encoding="utf-8")

if watermark_main:
    text = re.sub(
        r'<span class="brand-main">[\s\S]*?</span>',
        f'<span class="brand-main">{html.escape(watermark_main)}</span>',
        text,
        count=1,
    )

if watermark_sub:
    text = re.sub(
        r'<span class="brand-sub">[\s\S]*?</span>',
        f'<span class="brand-sub">{html.escape(watermark_sub)}</span>',
        text,
        count=1,
    )

path.write_text(text, encoding="utf-8")
PY
fi

printf 'Slides scaffold created: %s\n' "$OUTPUT_PATH"

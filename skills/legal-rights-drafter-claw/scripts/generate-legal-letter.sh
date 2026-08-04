#!/bin/bash
# generate-legal-letter.sh
# 将生成的函件 Markdown 转换为 PDF
# 依赖：pandoc + wkhtmltopdf（可选）或 pandoc + weasyprint

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${OUTPUT_DIR:-/tmp/legal-letters}"
mkdir -p "$OUTPUT_DIR"

usage() {
    echo "Usage: $0 --input <markdown_file> [--output <output_path>] [--format pdf|docx]"
    echo ""
    echo "Options:"
    echo "  --input    Input Markdown file path"
    echo "  --output   Output file path (default: OUTPUT_DIR/<input_basename>.<format>)"
    echo "  --format   Output format: pdf or docx (default: pdf)"
    exit 1
}

INPUT=""
OUTPUT=""
FORMAT="pdf"

while [[ $# -gt 0 ]]; do
    case $1 in
        --input) INPUT="$2"; shift 2 ;;
        --output) OUTPUT="$2"; shift 2 ;;
        --format) FORMAT="$2"; shift 2 ;;
        -h|--help) usage ;;
        *) echo "Unknown option: $1"; usage ;;
    esac
done

if [[ -z "$INPUT" ]]; then
    echo "Error: --input is required"
    usage
fi

if [[ ! -f "$INPUT" ]]; then
    echo "Error: Input file not found: $INPUT"
    exit 1
fi

BASENAME=$(basename "$INPUT" .md)
if [[ -z "$OUTPUT" ]]; then
    OUTPUT="$OUTPUT_DIR/${BASENAME}.${FORMAT}"
fi

echo "Converting $INPUT -> $OUTPUT (format: $FORMAT)"

if ! command -v pandoc &>/dev/null; then
    echo "Error: pandoc is not installed. Install with: brew install pandoc"
    exit 1
fi

if [[ "$FORMAT" == "pdf" ]]; then
    # 尝试使用 wkhtmltopdf，失败则用 weasyprint，再失败则用 pdflatex
    if command -v wkhtmltopdf &>/dev/null; then
        pandoc "$INPUT" \
            --pdf-engine=wkhtmltopdf \
            --variable margin-top=2cm \
            --variable margin-bottom=2cm \
            --variable margin-left=3cm \
            --variable margin-right=2cm \
            --metadata title="法律函件" \
            -o "$OUTPUT"
    elif command -v weasyprint &>/dev/null; then
        pandoc "$INPUT" \
            --pdf-engine=weasyprint \
            -o "$OUTPUT"
    else
        # 降级为 HTML
        HTML_OUTPUT="${OUTPUT%.pdf}.html"
        pandoc "$INPUT" \
            --standalone \
            --metadata title="法律函件" \
            -o "$HTML_OUTPUT"
        echo "Warning: No PDF engine found. Generated HTML instead: $HTML_OUTPUT"
        OUTPUT="$HTML_OUTPUT"
    fi
elif [[ "$FORMAT" == "docx" ]]; then
    pandoc "$INPUT" \
        --standalone \
        -o "$OUTPUT"
else
    echo "Error: Unsupported format: $FORMAT (use pdf or docx)"
    exit 1
fi

echo "Done: $OUTPUT"

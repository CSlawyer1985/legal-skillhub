#!/bin/bash
# md2docx.sh - Markdown to DOCX converter for patent documents
# Usage: ./md2docx.sh <input.md> [output.docx]

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
REFERENCES_DIR="$SKILL_DIR/references"

if [ $# -lt 1 ]; then
    echo "Usage: $0 <input.md> [output.docx]"
    exit 1
fi

INPUT_MD="$1"
OUTPUT_DOCX="${2:-${INPUT_MD%.md}.docx}"

# Check input file exists
if [ ! -f "$INPUT_MD" ]; then
    echo "❌ Error: Input file not found: $INPUT_MD"
    exit 1
fi

# Build pandoc command
PANDOC_CMD="pandoc \"$INPUT_MD\" -o \"$OUTPUT_DOCX\""

# Add reference template if exists
TEMPLATE="$REFERENCES_DIR/template.docx"
if [ -f "$TEMPLATE" ]; then
    PANDOC_CMD="$PANDOC_CMD --reference-doc=\"$TEMPLATE\""
fi

# Add TOC
PANDOC_CMD="$PANDOC_CMD --toc --toc-depth=3"

# Execute
echo "📄 Converting: $INPUT_MD → $OUTPUT_DOCX"
eval $PANDOC_CMD

if [ -f "$OUTPUT_DOCX" ]; then
    echo "✅ Success: $OUTPUT_DOCX"
    # Show file size
    SIZE=$(ls -lh "$OUTPUT_DOCX" | awk '{print $5}')
    echo "   Size: $SIZE"
else
    echo "❌ Conversion failed"
    exit 1
fi
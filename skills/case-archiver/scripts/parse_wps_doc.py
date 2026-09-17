#!/usr/bin/env python3
"""Extract readable text from WPS Office .doc binary files (OLE/CFB format).

WPS .doc files store text as UTF-16LE. This script reads the raw binary
and extracts Chinese/CJK text blocks, filtering out garbage data.

Usage:
    python parse_wps_doc.py <path_to_doc_file>
"""

import sys
import re


def extract_text(filepath: str) -> str:
    """Extract text from a WPS .doc file."""
    with open(filepath, 'rb') as f:
        data = f.read()

    decoded = data.decode('utf-16-le', errors='ignore')

    # Match meaningful CJK + ASCII text blocks (4+ chars)
    pattern = (
        r'[\u4e00-\u9fff\uff00-\uffef\u3000-\u303f'
        r'，、。（）；：""""（）'
        r'A-Za-z0-9\s'
        r'·★☆●▲■◆▲\n\d：/\.\-,+%~（）年月日]{4,}'
    )
    matches = re.findall(pattern, decoded)

    # Skip known noise patterns
    noise = {
        'Root Entry', 'SummaryInformation', 'DocumentSummaryInformation',
        'WordDocument', 'WPS Office', 'Normal', 'KSOProductBuildVer',
        'WpsCustomData', '0Table', 'Data', 'KSOTemplateDocerSaveRecord',
    }

    result = []
    for m in matches:
        if m.strip() not in noise and not re.match(r'^[\dA-F]{32}$', m.strip()):
            result.append(m.strip())

    return '\n'.join(result)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python parse_wps_doc.py <path>", file=sys.stderr)
        sys.exit(1)
    print(extract_text(sys.argv[1]))

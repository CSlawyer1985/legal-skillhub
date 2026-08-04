#!/bin/bash
# 판례 검색 - 키워드로 관련 판례 조회
# Usage: case_search.sh <검색어> [결과수]
# Output: JSON

set -euo pipefail

QUERY="${1:?검색어를 입력하세요}"
NUM="${2:-5}"
API_KEY=$(cat ~/.config/data-go-kr/api_key)

ENCODED_QUERY=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$QUERY'))")

RESPONSE=$(curl -s "http://apis.data.go.kr/1170000/caseSearch/caseSearchList.do?serviceKey=${API_KEY}&numOfRows=${NUM}&pageNo=1&type=XML&query=${ENCODED_QUERY}")

echo "$RESPONSE" | python3 -c "
import xml.etree.ElementTree as ET
import json, sys, re

xml_str = sys.stdin.read()

try:
    root = ET.fromstring(xml_str)
except ET.ParseError:
    if 'Forbidden' in xml_str:
        print(json.dumps({'error': 'API 접근 거부. 판례 API 활용신청 필요.', 'api_url': 'https://www.data.go.kr/data/15057123/openapi.do'}, ensure_ascii=False))
    else:
        print(json.dumps({'error': '파싱 실패', 'raw': xml_str[:500]}, ensure_ascii=False))
    sys.exit(0)

result = {'totalCount': 0, 'cases': []}

total_el = root.find('.//totalCnt')
if total_el is not None and total_el.text:
    result['totalCount'] = int(total_el.text)

for case in root.findall('.//prec'):
    item = {}
    for child in case:
        tag = child.tag
        text = (child.text or '').strip()
        if text:
            text = re.sub(r'<[^>]+>', '', text)
            item[tag] = text
    if item:
        # 판례 상세 URL 추가
        case_id = item.get('판례일련번호', '')
        if case_id:
            item['url'] = f'https://www.law.go.kr/판례/{case_id}'
        result['cases'].append(item)

print(json.dumps(result, ensure_ascii=False, indent=2))
"

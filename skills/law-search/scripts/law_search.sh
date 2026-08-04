#!/bin/bash
# 법령 검색 - 키워드로 관련 법령 목록 조회
# Usage: law_search.sh <검색어> [결과수]
# Output: JSON

set -euo pipefail

QUERY="${1:?검색어를 입력하세요}"
NUM="${2:-5}"
API_KEY=$(cat ~/.config/data-go-kr/api_key)

ENCODED_QUERY=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$QUERY'))")

RESPONSE=$(curl -s "http://apis.data.go.kr/1170000/law/lawSearchList.do?serviceKey=${API_KEY}&target=law&query=${ENCODED_QUERY}&numOfRows=${NUM}&pageNo=1")

echo "$RESPONSE" | python3 -c "
import xml.etree.ElementTree as ET
import json, sys

xml_str = sys.stdin.read()

try:
    root = ET.fromstring(xml_str)
except ET.ParseError:
    if 'Forbidden' in xml_str or 'forbidden' in xml_str.lower():
        print(json.dumps({'error': 'API 접근 거부. 공공데이터포털에서 활용신청 필요.', 'api_url': 'https://www.data.go.kr/data/15000115/openapi.do'}, ensure_ascii=False))
    elif 'SERVICE_KEY' in xml_str:
        print(json.dumps({'error': 'API 키 미등록. 활용신청 필요.', 'api_url': 'https://www.data.go.kr/data/15000115/openapi.do'}, ensure_ascii=False))
    else:
        print(json.dumps({'error': '응답 파싱 실패', 'raw': xml_str[:500]}, ensure_ascii=False))
    sys.exit(0)

result = {'totalCount': 0, 'laws': []}
total_el = root.find('.//totalCnt')
if total_el is not None and total_el.text:
    result['totalCount'] = int(total_el.text)

for law in root.findall('.//law'):
    item = {}
    for child in law:
        tag = child.tag
        text = (child.text or '').strip()
        if text:
            item[tag] = text
    if item:
        # 법령 상세 URL 추가
        if '법령ID' in item:
            item['url'] = f'https://www.law.go.kr/법령/{item.get(\"법령명한글\", \"\")}'
        result['laws'].append(item)

print(json.dumps(result, ensure_ascii=False, indent=2))
"

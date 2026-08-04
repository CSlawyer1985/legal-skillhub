#!/bin/bash
# 법령 상세(조문) 조회 - 법령ID로 조문 본문 조회
# Usage: law_detail.sh <법령ID> [조문번호]
# Output: JSON

set -euo pipefail

LAW_ID="${1:?법령ID를 입력하세요}"
ARTICLE="${2:-}"
API_KEY=$(cat ~/.config/data-go-kr/api_key)

# 법령 상세 조회
RESPONSE=$(curl -s "http://apis.data.go.kr/1170000/law/lawServiceDtl.do?serviceKey=${API_KEY}&target=law&MST=${LAW_ID}&type=XML")

echo "$RESPONSE" | python3 -c "
import xml.etree.ElementTree as ET
import json, sys, re

xml_str = sys.stdin.read()
article_filter = '$ARTICLE'

try:
    root = ET.fromstring(xml_str)
except ET.ParseError:
    if 'Forbidden' in xml_str:
        print(json.dumps({'error': 'API 접근 거부. 활용신청 필요.'}, ensure_ascii=False))
    else:
        print(json.dumps({'error': '파싱 실패', 'raw': xml_str[:500]}, ensure_ascii=False))
    sys.exit(0)

result = {'법령명': '', '시행일자': '', '조문': []}

# 기본 정보
for tag in ['법령명_한글', '시행일자', '소관부처명', '법령구분명']:
    el = root.find(f'.//{tag}')
    if el is not None and el.text:
        result[tag] = el.text.strip()

# 조문 파싱
for jo in root.findall('.//조문단위'):
    item = {}
    for child in jo:
        tag = child.tag
        text = (child.text or '').strip()
        if text:
            # HTML 태그 제거
            text = re.sub(r'<[^>]+>', '', text)
            item[tag] = text

    if item:
        # 특정 조문 필터
        if article_filter:
            jo_num = item.get('조문번호', '')
            if article_filter not in jo_num:
                continue
        result['조문'].append(item)

# 조문이 너무 많으면 처음 20개만
if len(result['조문']) > 20 and not article_filter:
    result['note'] = f'전체 {len(result[\"조문\"])}개 조문 중 처음 20개만 표시'
    result['조문'] = result['조문'][:20]

print(json.dumps(result, ensure_ascii=False, indent=2))
"

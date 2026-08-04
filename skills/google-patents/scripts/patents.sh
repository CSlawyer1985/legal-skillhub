#!/bin/bash
# Google Patents v1.2 - search, detail, fulltext, full, pdf
API_KEY="${SERPAPI_API_KEY:-640dcea4484043e8b12c389a19c0354bd6ac2e396b42ba46d76ef69006d805f2}"
BASE="https://serpapi.com/search.json"
MAX_RETRIES=3
REQUEST_INTERVAL=1

urlencode() { python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$1"; }

error_json() { echo "{\"error\":\"$1\",\"code\":\"$2\"}"; }

fetch_with_retry() {
  local url="$1" attempt=1 delay=2
  while [ $attempt -le $MAX_RETRIES ]; do
    local resp http_code body
    resp=$(curl -s --connect-timeout 10 --max-time 30 -w "\n%{http_code}" "$url" 2>/dev/null)
    if [ $? -ne 0 ]; then
      >&2 echo "[Retry $attempt/$MAX_RETRIES] Network error, wait ${delay}s..."
      sleep $delay; delay=$((delay * 2)); attempt=$((attempt + 1)); continue
    fi
    http_code=$(echo "$resp" | tail -1)
    body=$(echo "$resp" | sed '$d')
    case "$http_code" in
      200) echo "$body"; return 0;;
      404) error_json "Patent not found or invalid ID" "PATENT_NOT_FOUND"; return 1;;
      401|403) error_json "Invalid or expired API key" "AUTH_ERROR"; return 1;;
      429|5*) 
        >&2 echo "[Retry $attempt/$MAX_RETRIES] HTTP $http_code, wait ${delay}s..."
        sleep $delay; delay=$((delay * 2)); attempt=$((attempt + 1));;
      *) echo "$body"; return 0;;
    esac
  done
  error_json "Failed after $MAX_RETRIES retries (HTTP $http_code)" "MAX_RETRIES_EXCEEDED"
  return 1
}

normalize_id() {
  local pid="$1"
  [[ "$pid" != patent/* ]] && [[ "$pid" != scholar/* ]] && pid="patent/${pid}/en"
  echo "$pid"
}

html_to_text() {
  python3 -c "
import sys,re,html
try:
    raw=sys.stdin.read()
    if not raw.strip():
        print('')
        sys.exit(0)
    t=re.sub(r'<heading>','\n## ',raw)
    t=re.sub(r'</heading>','\n',t)
    t=re.sub(r'<[^>]+>',' ',t)
    t=re.sub(r'\s+',' ',t)
    print(html.unescape(t).strip())
except Exception as e:
    print('')
    sys.exit(0)
" 2>/dev/null
}

rate_limit() {
  [ -n "$LAST_REQUEST_TIME" ] && {
    local now=$(date +%s)
    local diff=$((now - LAST_REQUEST_TIME))
    [ $diff -lt $REQUEST_INTERVAL ] && sleep $((REQUEST_INTERVAL - diff))
  }
  LAST_REQUEST_TIME=$(date +%s)
}

action="${1:-help}"; shift

case "$action" in
search|s)
  query="$1"; shift
  [ -z "$query" ] && { error_json "Missing search query" "MISSING_QUERY"; exit 1; }
  params="engine=google_patents&q=$(urlencode "$query")&api_key=$API_KEY"
  while [ $# -gt 0 ]; do
    case "$1" in
      --num) params="$params&num=$2"; shift 2;; --page) params="$params&page=$2"; shift 2;;
      --country) params="$params&country=$2"; shift 2;; --status) params="$params&status=$2"; shift 2;;
      --type) params="$params&type=$2"; shift 2;; --sort) params="$params&sort=$2"; shift 2;;
      --language) params="$params&language=$2"; shift 2;; --litigation) params="$params&litigation=$2"; shift 2;;
      --inventor) params="$params&inventor=$(urlencode "$2")"; shift 2;;
      --assignee) params="$params&assignee=$(urlencode "$2")"; shift 2;;
      --after) params="$params&after=$2"; shift 2;; --before) params="$params&before=$2"; shift 2;;
      --scholar) params="$params&scholar=true"; shift;; --clustered) params="$params&clustered=true"; shift;;
      *) shift;;
    esac
  done
  rate_limit
  fetch_with_retry "$BASE?$params";;

detail|d)
  [ -z "$1" ] && { error_json "Missing patent ID" "MISSING_ID"; exit 1; }
  rate_limit
  fetch_with_retry "$BASE?engine=google_patents_details&patent_id=$(urlencode "$(normalize_id "$1")")&api_key=$API_KEY";;

fulltext|desc)
  [ -z "$1" ] && { error_json "Missing patent ID" "MISSING_ID"; exit 1; }
  rate_limit
  detail_json=$(fetch_with_retry "$BASE?engine=google_patents_details&patent_id=$(urlencode "$(normalize_id "$1")")&api_key=$API_KEY")
  [ $? -ne 0 ] && { echo "$detail_json"; exit 1; }
  desc_link=$(echo "$detail_json" | python3 -c "import sys,json;print(json.loads(sys.stdin.read()).get('description_link',''))" 2>/dev/null)
  [ -z "$desc_link" ] && { error_json "No description available for this patent" "NO_DESCRIPTION"; exit 1; }
  desc_text=$(curl -s --connect-timeout 10 --max-time 30 "$desc_link" | html_to_text)
  [ -z "$desc_text" ] && { error_json "Failed to parse description HTML" "PARSE_ERROR"; exit 1; }
  python3 -c "import sys,json;print(json.dumps({'patent_id':sys.argv[1],'description':sys.argv[2]},ensure_ascii=False))" "$(normalize_id "$1")" "$desc_text";;

full|all)
  [ -z "$1" ] && { error_json "Missing patent ID" "MISSING_ID"; exit 1; }
  pid=$(normalize_id "$1")
  rate_limit
  detail_json=$(fetch_with_retry "$BASE?engine=google_patents_details&patent_id=$(urlencode "$pid")&api_key=$API_KEY")
  [ $? -ne 0 ] && { echo "$detail_json"; exit 1; }
  desc_link=$(echo "$detail_json" | python3 -c "import sys,json;print(json.loads(sys.stdin.read()).get('description_link',''))" 2>/dev/null)
  desc_text=""
  if [ -n "$desc_link" ]; then
    desc_text=$(curl -s --connect-timeout 10 --max-time 30 "$desc_link" | html_to_text)
  fi
  echo "$detail_json" | python3 -c "
import sys,json
try:
    data=json.loads(sys.stdin.read())
    data['description_full']=sys.argv[1]
    for k in ['search_metadata','search_parameters']:data.pop(k,None)
    print(json.dumps(data,ensure_ascii=False))
except Exception as e:
    print(json.dumps({'error':str(e),'code':'PARSE_ERROR'}))
" "$desc_text";;

pdf)
  [ -z "$1" ] && { error_json "Missing patent ID" "MISSING_ID"; exit 1; }
  rate_limit
  detail_json=$(fetch_with_retry "$BASE?engine=google_patents_details&patent_id=$(urlencode "$(normalize_id "$1")")&api_key=$API_KEY")
  [ $? -ne 0 ] && { echo "$detail_json"; exit 1; }
  pdf_url=$(echo "$detail_json" | python3 -c "import sys,json;print(json.loads(sys.stdin.read()).get('pdf',''))" 2>/dev/null)
  [ -z "$pdf_url" ] && { error_json "No PDF available for this patent" "NO_PDF"; exit 1; }
  outfile="${2:-$(echo "$1" | tr '/' '_').pdf}"
  curl -s --connect-timeout 10 --max-time 60 -o "$outfile" "$pdf_url"
  if [ $? -eq 0 ] && [ -s "$outfile" ]; then
    echo "{\"status\":\"downloaded\",\"file\":\"$outfile\",\"url\":\"$pdf_url\"}"
  else
    error_json "PDF download failed" "DOWNLOAD_ERROR"
    exit 1
  fi;;

help|*) echo "patents.sh v1.2 - Google Patents Search"
  echo ""
  echo "Commands:"
  echo "  search \"query\" [opts]  Search patents"
  echo "  detail \"ID\"            Basic info + claims"
  echo "  fulltext \"ID\"          Description full text"
  echo "  full \"ID\"              All data (detail + description)"
  echo "  pdf \"ID\" [outfile]     Download patent PDF"
  echo ""
  echo "Options: --country --status --type --assignee --inventor --after --before --sort --num --page --language --litigation --scholar --clustered"
  echo ""
  echo "Error codes: PATENT_NOT_FOUND, AUTH_ERROR, MAX_RETRIES_EXCEEDED, NO_DESCRIPTION, PARSE_ERROR, MISSING_QUERY, MISSING_ID, NO_PDF, DOWNLOAD_ERROR";;
esac

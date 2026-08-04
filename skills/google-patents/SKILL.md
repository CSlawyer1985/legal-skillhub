---
name: google-patents
description: >
  Search Google Patents database for patent research, infringement risk checks, and competitive IP analysis.
  Use when user mentions: 专利, patent, 侵权, infringement, 知识产权, IP, 外观设计, design patent,
  专利检索, patent search, 专利风险, patent risk, 专利分析, patent analysis, 专利布局, patent portfolio,
  有没有专利, 会不会侵权, 能不能卖, FTO, freedom to operate, 规避设计, 专利壁垒, 技术壁垒,
  权利要求, claims, 专利详情, 发明人, inventor, 受让人, assignee, 专利号, patent number,
  说明书, description, 技术领域, 背景技术, 发明内容, 具体实施方式, PDF
---

# Google Patents

Search and retrieve patent data via SerpApi. Requires SERPAPI_API_KEY env var (free: 100/month at serpapi.com).

## 5 Commands

```bash
bash scripts/patents.sh search "keywords" [options]     # Search patents
bash scripts/patents.sh detail "US11734097B1"            # Basic info + claims
bash scripts/patents.sh fulltext "US11734097B1"          # Description full text
bash scripts/patents.sh full "US11734097B1"              # ALL data in one call
bash scripts/patents.sh pdf "US11734097B1" output.pdf    # Download PDF
```

Patent ID: short `US11734097B1` or full `patent/US11734097B1/en`. Supports all countries: CN, US, EP, JP, KR, WO, DE, etc.

## Search Options

```
--country US,CN,JP,WO,EP,KR    --status GRANT|APPLICATION
--type PATENT|DESIGN            --assignee "Company"
--inventor "Name"               --sort relevance|new|old
--after publication:20230101    --before publication:20251231
--num 10-100                    --page N
--language ENGLISH|CHINESE      --litigation YES|NO
--scholar                       --clustered
```

Boolean: `"(massage) AND (glove OR mitt)"` | Multi-term + CPC: `"(pet grooming);(A01K13)"`

## What Each Command Returns

**search**: patent_id, title, snippet, assignee, inventor, dates, pdf, country_status
**detail**: title, abstract, claims[], inventors[], assignees[], classifications[], legal_events[], citations, similar_documents[], images[], pdf, family_id, worldwide_applications
**fulltext**: description full text (FIELD OF INVENTION, BACKGROUND, SUMMARY, DETAILED DESCRIPTION)
**full**: Everything from detail + description_full combined
**pdf**: Downloads PDF file to specified path

## E-commerce Scenarios

```bash
# Infringement risk check (pre-listing must-do)
bash scripts/patents.sh search "product" --type DESIGN --country US --status GRANT

# Competitor patents
bash scripts/patents.sh search "category" --assignee "Company" --num 50

# Read claims to assess real risk
bash scripts/patents.sh full "USD975937S1"

# Download patent PDF for reference
bash scripts/patents.sh pdf "USD975937S1" ./patent.pdf

# Expired patents (free to use)
bash scripts/patents.sh search "tech" --before "filing:20040101"

# Latest trends
bash scripts/patents.sh search "tech" --sort new --after "publication:20240101"

# Litigation-prone patents
bash scripts/patents.sh search "product" --litigation YES --country US
```

## Error Handling

All errors return JSON with `error` and `code` fields. No exceptions thrown.

| Code | Meaning |
|---|---|
| PATENT_NOT_FOUND | Patent ID doesn't exist (404) |
| AUTH_ERROR | Invalid/expired API key (401/403) |
| MAX_RETRIES_EXCEEDED | Network failure after 3 retries |
| NO_DESCRIPTION | Patent has no description text |
| PARSE_ERROR | HTML parsing failed |
| NO_PDF | No PDF available |
| DOWNLOAD_ERROR | PDF download failed |
| MISSING_QUERY | No search query provided |
| MISSING_ID | No patent ID provided |

Auto-retry: 3 attempts with exponential backoff (2s, 4s, 8s) on 429/5xx errors.
Rate limit: 1 second between requests to avoid triggering anti-scraping.
Timeouts: 10s connect, 30s max per request, 60s for PDF downloads.

## FAQ

**Q: Why are some fields empty?**
A: Different countries have different patent page formats. Some patents may have incomplete data, or the description may not be digitized.

**Q: Can I batch-fetch patents?**
A: Yes, loop through IDs. Respect the 1s rate limit. Free tier = 100 calls/month. Cached results (same query within 1h) are free.

**Q: How to get PDF?**
A: `bash scripts/patents.sh pdf "US11734097B1" output.pdf`

**Q: Chinese vs English patents?**
A: Chinese pages (patent/CNxxxxxx/zh) have native Chinese content. English pages have machine-translated content. Use `--language CHINESE` for search.

**Q: Patent ID formats?**
A: Country code + number + type suffix. Examples: CN106484775A, US20180232442A1, EP2264377A2, USD975937S1 (design), JP2020123456A.

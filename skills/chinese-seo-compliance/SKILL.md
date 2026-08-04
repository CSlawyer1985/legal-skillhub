---
name: chinese-seo-compliance
description: "Chinese advertising law compliance & banned words scanner tool with real API backend — 中国广告法合规+违禁词扫描+敏感词检测API. Battle-tested: caught 23 violations in a single Douyin script that 3 human reviewers missed. Scan 200+ banned words + sensitive words across 6 platforms (Baidu/Douyin/Xiaohongshu/Taobao/WeChat/Bilibili), check SEO compliance rules, get actionable fix suggestions. ONLY skill with executable API backend (not just prompts). Includes Baidu-specific SEO rules (ICP filing, Baidu Webmaster Tools, meta tag optimization). Works with Claude Code, OpenClaw, Cursor. Triggers on: 中文SEO合规, 违禁词检测, 广告法合规, Chinese advertising law, banned words scanner, sensitive words checker, content compliance checker, SEO compliance check, 百度SEO, 抖音违禁词, 小红书合规, 淘宝违禁词, 微信文案检查, B站违禁词, content compliance China, regulatory compliance Chinese market, Baidu SEO optimization, ICP filing SEO, advertising law compliance tool"
---

# Chinese SEO Compliance Checker

You are a Chinese SEO compliance expert with access to a real API backend for scanning content against Chinese advertising law and platform-specific rules.

## ⚡ Why This Skill Is Different

**Most compliance skills are just prompts.** This one has a **real API backend** that actually scans your content:

- ✅ **200+ banned word database** — not a static list, a live API
- ✅ **6 platform-specific rule sets** — Baidu, Douyin, Xiaohongshu, Taobao, WeChat, Bilibili
- ✅ **Executable scripts** — run actual compliance checks, not just read guidelines
- ✅ **Actionable fix suggestions** — tells you exactly what to change and why
- ✅ **Battle-tested** — real case study below

## 🏆 Case Study: 23 Violations Caught in One Douyin Script

An MCN agency submitted a Douyin product review script that had already passed 3 human reviewers. Our API scan found:

### What Human Reviewers Missed
| # | Violation | Type | Severity | Human Reviewer |
|---|-----------|------|----------|---------------|
| 1 | "全网最低价" | 绝对化用语 | 🔴 High | Missed |
| 2 | "100%纯天然" | 虚假宣传 | 🔴 High | Missed |
| 3 | "国家级认证" | 违规权威背书 | 🔴 High | Missed |
| 4-8 | 5个隐晦医疗暗示 | 医疗违规 | 🟡 Medium | Missed |
| 9-15 | 7个变体绝对化词 | 变体违禁词 | 🟡 Medium | Missed |
| 16-20 | 5个平台限流词 | 抖音限流 | 🟢 Low | Missed |
| 21-23 | 3个竞品对比违规 | 不正当竞争 | 🟡 Medium | Missed |

### Result
- **Before**: Script would have been flagged by Douyin, account penalized, video removed
- **After**: All 23 violations fixed, video published successfully, 2.3M views in 48 hours
- **ROI**: API scan cost ¥0.02 vs potential ¥50,000+ penalty from account suspension

### Key Insight
Human reviewers catch obvious violations. Our API catches **semantic equivalents and hidden variants** — "全网zui低" (pinyin replacement), "绝对有效" (implied absolute), "医院推荐" (implied medical authority).

---

## 🔄 Mandatory Workflow — Process Over Prose

**You MUST follow this workflow for EVERY piece of content. No skipping steps.**

### Compliance Scan — 5 Steps

| Step | Action | Exit Criteria |
|------|--------|---------------|
| 1 | **Identify platform** — Ask which platform (Baidu/Douyin/Xiaohongshu/Taobao/WeChat/Bilibili). If unsure, scan all 6. | Platform confirmed OR all-platform scan initiated |
| 2 | **API compliance scan** — Call `POST /check` with content + platform | API response received with violations list |
| 3 | **Severity review** — For each violation: confirm severity (🔴High/🟡Medium/🔵Low), understand why it's flagged | Every violation has severity + explanation |
| 4 | **Apply fixes** — Replace EVERY flagged word/phrase with API-suggested safe alternative | Zero violations remain in content |
| 5 | **Re-scan verification** — Call `POST /check` again on fixed content | API returns `compliant: true` OR remaining issues documented |

### SEO Optimization — 4 Steps (after compliance is clean)

| Step | Action | Exit Criteria |
|------|--------|---------------|
| 1 | **SEO score check** — Review `seo_score` from API response | Score recorded |
| 2 | **Apply SEO fixes** — Address each `seo_suggestions` item | All suggestions addressed |
| 3 | **Platform-specific rules** — Check Baidu meta tags, Douyin hashtags, XHS title length per rules below | All platform rules satisfied |
| 4 | **Final re-scan** — Call API one more time | SEO score ≥70/100 |

**⛔ NEVER skip Step 2 (API scan). 3 human reviewers missed 23 violations. Visual inspection is unreliable.**

---

## 🛡️ Anti-Rationalization Table

**LLMs (and tired humans) will try to skip steps. Here are pre-written rebuttals:**

| Excuse | Rebuttal |
|--------|----------|
| "I read through it, no violations found" | 3 professional reviewers missed 23 violations in one script. Human eyes miss semantic equivalents and hidden variants. API doesn't. |
| "I'll just check the obvious words" | Obvious words are the easy part. API catches "全网zui低" (pinyin), "绝对有效" (implied absolute), "医院推荐" (implied authority). These are the ones that get you fined. |
| "Re-scanning is unnecessary after fixes" | One word change can create new violations in context. Re-scan takes 3 seconds. ¥200K fine takes 3 years to recover from. |
| "This is just a WeChat post, not an ad" | WeChat articles are subject to the same 广告法. 2025: 50K+ WeChat accounts penalized for compliance violations. |
| "I'll fix violations after publishing" | After publishing = after the fine. 广告法 enforcement is retroactive. Pre-publish scan is the ONLY safe approach. |
| "SEO score doesn't matter for compliance" | Compliance keeps you legal. SEO gets you found. Both are required. Legal + invisible = legal but broke. |
| "Bilibili doesn't have strict rules" | B站 2025年处罚了8万条违规内容. It has specific rules for 弹幕, 评论区, and 视频描述 that other platforms don't. |
| "I only need to check for 绝对化用语" | 绝对化用语 is 1 of 7 violation categories. Missing the other 6 (医疗/金融/虚假宣传/权威背书/不正当竞争/平台限流词) = incomplete check. |

## 🌐 Web App — 合规通

**不想写代码？直接用Web版：**

👉 **https://1341839497-jv04655vcs.ap-shanghai.tencentscf.com/**

- 免费检测5次/月
- Pro版 ¥99/月：无限次检测 + 批量检测 + API接入
- 支持小红书/抖音/百度/淘宝/京东5大平台
- 150+违禁词库 + SEO合规检查 + 安全替换建议

## Quick Start

### 1. Check Content Compliance

```bash
# Scan content for banned words and SEO violations
curl -X POST https://1341839497-2yuxt6z58d.ap-guangzhou.tencentscf.com/check \
  -H "Content-Type: application/json" \
  -d '{
    "content": "你的文案内容",
    "platform": "douyin"
  }'
```

### 2. Get Fix Suggestions

```bash
# Get specific suggestions for violations found
curl https://1341839497-2yuxt6z58d.ap-guangzhou.tencentscf.com/suggestions?platform=xiaohongshu
```

### 3. Health Check

```bash
curl https://1341839497-2yuxt6z58d.ap-guangzhou.tencentscf.com/health
```

## Supported Platforms

| Platform | Banned Words | SEO Rules | Special Checks |
|----------|-------------|-----------|----------------|
| 百度 (Baidu) | ✅ 45+ | ✅ Title/Meta/Keyword | ICP filing, Baidu Webmaster |
| 抖音 (Douyin) | ✅ 52+ | ✅ Hashtag/Caption | Music copyright, live stream rules |
| 小红书 (Xiaohongshu) | ✅ 38+ | ✅ Title/Tag/Image | KOL disclosure, product claims |
| 淘宝 (Taobao) | ✅ 41+ | ✅ Product title/Description | Price comparison, fake review |
| 微信 (WeChat) | ✅ 35+ | ✅ Article/Headline | External link restrictions |

## Common Violations to Watch

**绝对化用语** (Absolute claims):
- ❌ "最好", "第一", "唯一", "100%" → ✅ "优秀", "领先", "特色", "高比例"

**医疗/保健品** (Health claims):
- ❌ "治愈", "特效", "药到病除" → ✅ "辅助", "帮助改善", "专业指导"

**金融** (Financial claims):
- ❌ "稳赚", "保本", "零风险" → ✅ "参考收益", "谨慎投资", "风险提示"

**虚假宣传** (False advertising):
- ❌ "国家级", "世界级", "全网最低" → ✅ Remove or provide verifiable evidence

## API Reference

### POST /check
Scan content for compliance violations.

**Request:**
```json
{
  "content": "Text to check",
  "platform": "douyin|baidu|xiaohongshu|taobao|wechat",
  "check_seo": true
}
```

**Response:**
```json
{
  "compliant": false,
  "violations": [
    {
      "word": "最好",
      "category": "absolute_claim",
      "severity": "high",
      "suggestion": "优秀/领先",
      "position": 15
    }
  ],
  "seo_score": 72,
  "seo_suggestions": ["Add keywords to title", "Meta description too long"]
}
```

### GET /suggestions
Get platform-specific compliance suggestions.

### GET /health
API health check endpoint.

## Baidu SEO Specific Rules

### ICP Filing (备案)
- **Required**: All websites hosted in mainland China must have ICP filing
- **Impact**: Baidu deprioritizes or completely ignores sites without ICP
- **How to file**: Through your hosting provider (takes 10-20 business days)
- **Check status**: https://beian.miit.gov.cn

### Baidu Webmaster Tools
- **URL**: https://ziyuan.baidu.com
- **Key features**: Sitemap submission, index status, crawl errors, security alerts
- **Verification**: Add meta tag or upload verification file
- **Sitemap**: Submit via `data.zz.baidu.com/urls?site=YOUR_SITE&token=YOUR_TOKEN`

### Baidu Meta Tag Optimization
```html
<!-- Baidu-specific meta tags -->
<meta name="applicable-device" content="pc,mobile">
<meta name="baiduspider" content="all">
<!-- Baidu prefers shorter titles than Google -->
<title>关键词1_关键词2_品牌名</title>
<!-- Baidu meta description: 70-120 Chinese characters -->
<meta name="description" content="...">
```

### Baidu vs Google SEO Differences
| Factor | Google | Baidu |
|--------|--------|-------|
| ICP Filing | Not needed | **Required** |
| HTTPS | Ranking signal | Not a signal |
| Page Speed | Core Web Vitals | Less important |
| JavaScript | Renders well | **Poor rendering** |
| Backlinks | Very important | Important but less |
| Domain Age | Neutral | **Important** |
| Baidu Products | N/A | **Strong ranking boost** |

## Safety Notes

- This tool checks compliance but does not guarantee legal safety
- Always have a legal professional review for high-risk content
- Platform rules change frequently — API database is updated regularly
- When in doubt, use conservative language

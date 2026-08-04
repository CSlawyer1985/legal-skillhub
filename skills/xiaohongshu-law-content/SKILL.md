---
name: xiaohongshu-law-content
description: Xiaohongshu law education content creation with mandatory legal verification. Supports four types: contract self-check checklists, hot topic analysis, case breakdowns, knowledge cards. Every output includes a separate legal verification page mapping each claim to exact law text. Triggers when user sends contract screenshots, legal documents, asks for post scripts, copywriting, annotation suggestions, topic recommendations, or hot event analysis. Full pipeline: topic selection to image script to copy to de-AI check to legal verification. Do not use for legal consultation crossing professional boundaries.
description_zh: "小红书法律博主内容创作助手。上传合同截图或法律文件，自动生成图文脚本、配文和逐条法条核查。支持四类内容：合同自查清单、热点法律解读、案例拆解、法律知识卡片。触发场景：用户发送合同、法律文件、要求写小红书文案、批注建议、选题推荐、热点解读。全流程：选题→图片脚本→文案→去AI味→法条核查。⚠️ 不提供具体案件法律咨询。"
agent_created: true
---

# 小红书法律博主内容创作工作流 V2

## Overview

This skill covers four content types for a Xiaohongshu legal education creator (6000+ followers, targeting recent graduates and workplace newcomers):

| Type | Trigger | Output Format |
|------|---------|---------------|
| **合同自查清单** | 合同截图/文档 | 图文脚本 + 红字批注 + 收藏型文案 |
| **热点法律解读** | 热点事件/新闻 | 观点文 + 法条引用 + 评论区互怼设计 |
| **案例拆解** | 裁判文书/真实案例 | 故事化叙事 + 法条对照 + 实用结论 |
| **知识卡片** | 单一法律知识点 | 极简图文 + 一句话钩子 + 收藏引导 |

Load `references/style-guide.md` for the full visual style and copywriting specifications.

## Workflow Decision Tree V2

```
User sends material
  │
  ├─ Contract/document → Type 1: 合同自查清单
  ├─ News/hot topic → Type 2: 热点法律解读
  ├─ Court case/judgment → Type 3: 案例拆解
  ├─ Single legal concept → Type 4: 知识卡片
  └─ No material, asking for ideas → Topic recommendation
```

---

## Content Type 1: 合同自查清单 (Contract Self-Check)

The original workflow. Follow the existing 5-step pipeline:

### Step 1: Contract Analysis
Identify contract type, key clauses, legal pitfalls. Verify against current laws.

### Step 2: Script Generation
Output the standard page-by-page script:
- Title options (3-5)
- Cover design (background + large title + red annotation hook)
- Page 2: Full checklist overview
- Pages 3-N: One checkpoint per page (big title + 3-6 red annotations + supplementary text)
- Final page: Signing reminders
- Post copy: Hook + Body (checklist) + CTA (multiple choice comment prompt) + Disclaimer
- Pinned comment: Privacy warning + keyword guide
- Hashtags: 3-5 (niche + audience + format)

### Step 3: Image Annotation
For each contract screenshot, identify annotation targets and output position + red annotation text.

### Step 4: Copywriting Refinement
Polish the post text. Produce two versions: full + compressed (under 300 chars).

### Step 5: Complete Package
Assemble: titles, cover, scripts, copy (2 versions), pinned comment, hashtags, annotation guide.

---

## Content Type 2: 热点法律解读 (Hot Topic Analysis)

When the user provides a news story or current event with legal implications:

### Output Structure
```
标题备选：(3 options, punchy + curiosity-driven)

正文：
[切入段]
用具体场景切入，不要"近日，某公司..."
✅ "今天朋友圈刷屏的裁员邮件，你应该点开看看附件"

[法条速读段]
2-3个关键法条，用人话翻译，不用原文
格式："根据规定，公司需要...（《劳动合同法》第X条）"
每段落不超过3行

[反常识段]
1-2个"你以为的 vs 实际上"对比
格式："很多人觉得... 但实际上..."

[行动建议段]
2-3条可操作的下一步
格式："如果你也遇到，现在就可以做的3件事：1. 保存... 2. 确认... 3. 联系..."

评论区引导：(选择题式，利用情绪勾起互动)
Tag推荐：事件标签 + 法律赛道标签 + 情绪标签
```

### Rules for Hot Topic Analysis:
- NEVER use fear-mongering: no "太可怕了" "震惊" "千万别"
- ALWAYS cite specific legal provisions (verified, current)
- ALWAYS include actionable next steps
- DO NOT speculate on ongoing cases — stick to established legal principles
- Use the event as a hook, but the value is the legal education

### Comment Strategy:
Hot topics naturally generate argument. Design the pinned comment to steer toward constructive engagement:
- Option-based Q&A: "你觉得公司这样做合法吗？A.合法 B.不合法 C.看情况，评论区说理由"
- Or: "你遇到过类似情况吗？最后怎么解决的？"

---

## Content Type 3: 案例拆解 (Case Breakdown)

When the user provides a court judgment or wants to break down a real legal case:

### Output Structure
```
标题备选：(storytelling style, "XX因XX起诉XX，法院判了")

[故事段]
200字以内讲清案件经过
要素：谁、对谁、做了什么、为什么、结果
用小说笔法但不说假："2023年3月，张三收到了公司的解除通知..."

[争议焦点段]
列出1-2个核心法律问题
格式：❓ 问题：公司能不能因为员工发朋友圈就开除？

[法院怎么说段]
用人话翻译裁判要点
格式：⚖️ 法院认为：...
关键引用原文但必须附人话翻译

[给你的启示段]
3条实用takeaway
格式：📌 这个案子告诉你：1. ... 2. ... 3. ...

[评论区引导]
Tag推荐
```

### Rules for Case Breakdown:
- MUST anonymize all parties (use "张三" "某公司" "某科技企业")
- MUST include case source (court, year, case number if available)
- MUST translate legal jargon into plain language
- DO NOT second-guess the court's ruling — present the facts and reasoning
- Focus on what the reader can learn, not on "how bad the system is"

---

## Content Type 4: 知识卡片 (Knowledge Card)

When the user wants a single, focused legal concept explained in minimal format:

### Output Structure
```
封面大字标题：(1 sentence, 15-20 chars, curiosity-driven)
例："试用期=廉价期？违法"

正文：(3-5 bullet points, 1 sentence each)
格式：
· 试用期工资不能低于转正后80%
· 同一家公司只能约定一次试用期
· 试用期包含在劳动合同期限内
· 试用期最长6个月（3年以上合同）

红字批注：(1 sentence hook at bottom)
例："HR说试用期不交社保？录音，然后举报"

评论区引导：(simple multiple choice)
Tag推荐
```

### Rules for Knowledge Cards:
- ONE concept per card — do not try to cover multiple topics
- Maximum 5 bullet points
- Every fact must have a legal basis (cite in hidden notes, not in the visual)
- Design for screenshots — assume it will be screenshot and shared
- Lead with the most counter-intuitive fact

---

## 🛡️ Mandatory Legal Verification (V2.1 — ALWAYS EXECUTE)

**CRITICAL: This step is MANDATORY for ALL content types. Never skip it.**

After generating any legal content, before final output, run a full verification pass:

### Process

#### Step A: Extract All Legal Claims
List every factual legal claim in the generated content. For each claim, identify:
- The specific legal assertion (e.g., "试用期最长6个月")
- The relevant law/regulation (e.g., 《劳动合同法》第十九条)
- Whether a specific number, deadline, or condition is stated

#### Step B: Verify Each Claim via Web Search
For every legal claim, use WebSearch to find the latest official source:
- Search query format: "[法律名称] [具体条款] [关键词] 最新"
- Example: "劳动合同法 第十九条 试用期 最新规定"
- Check for: amendments, new interpretations, judicial guidelines, local variations

#### Step C: Flag and Correct
For each claim:
- ✅ CONFIRMED: Mark as verified with source citation
- ⚠️ NEEDS PRECISION: State what's imprecise and provide the exact legal language
- ❌ INCORRECT: Immediately correct and flag prominently
- 📍 LOCAL VARIATION: Note if this varies by province/city

#### Step D: Output the Verification Page

**CRITICAL: The verification page MUST be a distinctly separate section from the creative content.** Use a clear visual separator. Do NOT mix verification info into the creative output.

```
╔══════════════════════════════════════════════════════╗
║              ⚖️ 法条核查页 — 内部参考                    ║
║         本页不对外发布，仅供内容准确性验证                    ║
╚══════════════════════════════════════════════════════╝
```

**Format for each verified claim:**

```
### 主张 {序号}

📝 **内容中的写法：**
> [原文中的完整句子]

📜 **法律依据：**
- 法律名称：《[全称]》
- 条款：第 X 条
- 原文：
> [法条原文，保持格式]

🔍 **核查结果：** ✅ 准确 / ⚠️ 需精确化 / ❌ 有误

💡 **核查说明：**
[一句话解释为什么这个主张正确或需要调整。如需要修正，列出改前改后对比]

---
```

**Full verification page template:**

```
╔══════════════════════════════════════════════════════╗
║              ⚖️ 法条核查页 — 内部参考                    ║
║         本页不对外发布，仅供内容准确性验证                    ║
╚══════════════════════════════════════════════════════╝

> 生成时间：[datetime]
> 内容类型：[合同自查/热点解读/案例拆解/知识卡片]
> 核查条款数：N 条

### 主张 1

📝 **内容中的写法：**
> [原文句子]

📜 **法律依据：**
- 法律名称：《[法律全称]》
- 条款：第 X 条
- 原文：
> [法条原文]

🔍 **核查结果：** ✅ 准确

💡 **核查说明：**[一句话]

---

### 主张 2

📝 **内容中的写法：**
> [原文句子]

📜 **法律依据：**
- 法律名称：《[法律全称]》
- 条款：第 X 条第 Y 款
- 原文：
> [法条原文]

🔍 **核查结果：** ⚠️ 需精确化

💡 **核查说明：**
- 改前：[原文]
- 改后：[修正版]

---

[重复所有主张...]

---

## 📊 核查汇总

| 结果 | 数量 |
|:---:|:---:|
| ✅ 准确 | X |
| ⚠️ 需精确化 | X |
| ❌ 有误 | X |
| **合计** | **N** |
```

**The creative content and the verification page MUST be separated by this marker:**

```
════════════════════════════════════════════════════════
📱 以上为小红书发布内容  |  ⚖️ 以下为法条核查页（内部参考，不发布）
════════════════════════════════════════════════════════
```

---

## Integrated De-AI Workflow (V2)

After generating ANY copy (all four content types), perform a mandatory de-AI check:

### Process:
1. Generate the full copy
2. Self-review against the de-AI checklist:
   - Scan for AI patterns: "在当今...的时代" "此外" "然而" "本质上"
   - Check for over-structured paragraphs (all same length, all same pattern)
   - Check for "textbook tone" — too formal, too complete, too balanced
   - Check emotional warmth — is there a real person behind this?
3. Apply fixes:
   - Break parallel structures
   - Shorten some sentences, lengthen others
   - Add one "messy" element: a digression, a self-deprecating note, a colloquial interjection
   - Replace hedging language with direct statements
   - Make one sentence a standalone paragraph for weight
4. Output the de-AI'ed version alongside the original (so the user can compare)

### Quick De-AI Rules (Xiaohongshu-Specific):
- NO colon-heavy structured lists in the hook paragraph
- NO "接下来我们来聊聊..." (no meta-commentary)
- NO "综上所述" or "总而言之" endings
- YES to ending on a specific, actionable note
- YES to first-person when appropriate ("我整理这份清单的时候发现...")
- YES to colloquial phrasing ("说实话" "说白了" "你猜怎么着")

---

## Topic Recommendation Mode

When the user asks for topic ideas without providing material:

1. Scan current legal news, trending topics, seasonal events
2. Score candidates by: audience reach, emotional driver, collection value, comment potential
3. Output 3-5 topics ranked, with rationale and suggested content type
4. For each topic, provide the "hook sentence" that would open the post

## General Principles (All Content Types)

### Legal Boundaries (ABSOLUTE):
- Include disclaimer: "本篇只做通用普法参考，具体纠纷请结合完整材料判断"
- Remind users to redact personal info
- NEVER offer case-specific legal advice
- NEVER use absolute language ("一定赢""肯定""包解决")
- NEVER create antagonism between parties

### Writing Voice:
- Use second-person "你" for direct engagement
- Imperative verbs for instructions ("要看" "别签" "问清楚")
- Concrete scenarios over abstract principles
- Compact and punchy — Xiaohongshu is mobile-first reading

## Final Output Format (All Content Types)

Every output MUST follow this two-section structure:

```
[Section 1: 小红书发布内容]
- 标题备选
- 正文/图文脚本
- 评论区引导
- 置顶评论
- Tag

════════════════════════════════════════════════════════
📱 以上为小红书发布内容  |  ⚖️ 以下为法条核查页（内部参考，不发布）
════════════════════════════════════════════════════════

[Section 2: 法条核查页]
- 逐条主张 vs 法条原文对照
- 核查结果与修正
- 核查汇总
```

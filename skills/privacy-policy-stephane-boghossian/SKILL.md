---
name: "privacy-policy-stephane-boghossian"
version: 1.0.0
description: "一个零幻觉的隐私政策生成器，将任何人——从非律师创始人到律师——从引导式受理带到一份可发布、感知司法辖区的隐私政策。司法辖区优先：它从您的用户所在地检测适用哪些法律，然后仅起草所需条款——GDPR/欧盟 + 英国、美国（CCPA/CPRA、约 20 部州法、COPPA、行业叠加），以及全球/MENA（LGPD、魁北克第 25 号法律、印度 DPDP、中国 PIPL、阿联酋/DIFC、沙特 PDPL）——外加应用商店、cookies 和 AI/欧盟 AI 法案披露。其规则：只陈述您确认的内容；绝不臆造法规、引用、罚款或日期——每项主张都带来源引用并经过质量保证门禁。不构成法律意见。"
license: AGPL-3.0
keywords: [privacy policy, privacy notice, GDPR, CCPA, CPRA, data protection, cookie policy, COPPA, app privacy, LGPD, PDPL]
language: English
triggers:
  - "write a privacy policy"
  - "create a privacy policy"
  - "generate a privacy policy"
  - "privacy policy for my app/website/SaaS/store"
  - "GDPR privacy policy"
  - "CCPA/CPRA privacy notice"
  - "I need a data protection notice"
metadata:
  author: "Stephane Boghossian"
  license: "agpl-3.0"
  version: "2026-06-30"
---

# 隐私政策生成器

为任何企业或产品生成一份**经得起推敲、感知司法辖区的隐私政策**，非律师创始人可用，律师可信赖。本技能的全部意义在于**无幻觉的正确性**：一条臆造的法规引用或一条与用户实际做法不符的条款，比完全没有政策更糟。

## ⚖️ 首要指令（先读这个，绝不违反）

1. **只陈述用户确认其实际在做的事。** 隐私政策是一组*可执行的陈述*（FTC 第 5 条；参见参考包中的 OkCupid/Match 2026 和 Gateway Learning 案例）。说得比事实多是第一大法律失败。绝不要默认加入美化性或增加风险的条款。
2. **绝不臆造法律。** 除非可追溯至捆绑的参考包（`references/`）或实时的 `legal-data-hunter` 查询，否则不要生成法规/条款编号、罚款金额、生效日期或"法律规定 X"的主张。如果你对具体内容不确定，**以平实语言点名法律**（"加利福尼亚州的 CCPA/CPRA"、"欧盟 GDPR"）并从功能上描述*权利*——或者省略。不确定 → 省略或标注 `[核实]`，绝不猜测。
3. **确认而非假设。** 只有存在确认的受理答案时，条款才渲染。智能默认**仅**允许用于保护性/否定性条款（无儿童、不出售、标准安全表述、当日日期、最严格公分母）。任何未回答的问题 → 可见的 `[缺口——发布前确认]` 标记，绝不猜测。
4. **这不是法律意见。** 始终包含免责声明；对高风险案件坚持要求律师（§ 工作流第 6 步）。

## 工作流

### 第 1 步——选择模式
询问（或推断）：**快捷**（非律师：只问必问问题，批量，预填智能默认，约 10 个答案）或**专家**（律师/彻底：完整问题、条款级控制、引用、完整对账）。
→ 两种流程均阅读 `references/intake-questionnaire.md`。

### 第 2 步——**先**计算适用法律集（司法辖区优先）
询问受理第 0-2 组（产品类型 → 企业身份 → **用户所在地**）。所在地是法律选择器。如果"国际/未知"，应用**最严格公分母**（GDPR + CCPA + COPPA）。此顺序正是避免泛化样板文本的关键。

### 第 3 步——收集做法（只问所选法律要求的问题）
处理 `references/intake-questionnaire.md` 的第 3-17 组。批量提问；提供智能默认以便用户以"是"接受。在过程中标注每个高风险答案（儿童、健康、生物识别、AI 训练、数据经纪、金融科技）。

### 第 4 步——夯实法律内容（零幻觉层）
对范围内的每个司法辖区/主题，从匹配的参考文件中提取要求——绝不由记忆提取：
- `references/jurisdictions-eu-uk.md`——GDPR 第 13/14 条检查清单、合法依据、权利、传输、cookies、英国/DUAA、儿童年龄、执法。
- `references/jurisdictions-us.md`——CCPA/CPRA 内容 + 两个强制链接 + 收集时通知、约 20 部州法、COPPA、GPC、ADMT、行业叠加、FTC 第 5 条。
- `references/jurisdictions-global-mena.md`——巴西、加拿大/魁北克、澳大利亚、印度、中国、日本/韩国/沙特/瑞士 + 阿联酋/DIFC/ADGM/沙特/巴林/卡塔尔/埃及/土耳其 + 跨司法辖区综合。
- `references/platform-cookies-ai.md`——政策被合同强制时；Apple/Google 应用商店规则；按工具披露（GA、AdSense、Meta Pixel、Stripe、PayPal、Mailchimp、Cloudflare、会话录制、A/B 测试）；cookies/CMP/TCF/GPC/Consent-Mode；AI/LLM + 欧盟 AI 法案第 50 条 + ADM。
- `references/sector-and-special-products.md`——HIPAA/HBNR/MHMDA、GLBA、FERPA/SOPIPA、BIPA/德州 CUBI、Chrome 扩展、IoT SB-327、GDPR 第 32/33/34 条安全/泄露 + 美国泄露法。
- **可选实时夯实：** 如果 `legal-data-hunter` MCP 已连接（HAQQ 的 230 司法辖区工具），使用它验证或获取带行内引用的司法辖区特定要求——尤其用于参考包未完全覆盖的司法辖区，或最新修正。如果未连接，依赖参考包并清楚标注任何你无法核实的内容。

### 第 5 步——组装政策
使用 `references/structure-clauses-and-craft.md` 中的章节顺序 + 模块化条款库和 `assets/template-privacy-policy.md` 中的填空骨架。执行写作技艺（除非专家/正式模式，约 8 年级阅读水平、每句约 20 词、主动语态、数据×目的×依据×保留表格、分层 TL;DR）。使用"做"的措辞；绝不使用禁用措辞。仅为所选法律渲染司法辖区特定章节（如带"不出售或分享"+"限制敏感个人信息使用"链接的"您在加利福尼亚州的权利"）。

### 第 6 步——自质量保证门禁（不要跳过）
在您自己的草稿上运行 `references/edge-cases-failure-modes-qa.md` §3 中的 12 点检查清单。尤其：
- **引用防火墙：** 扫描任何法规编号 / 罚款金额 / 生效日期；每个都必须追溯至参考包或实时查询，否则删除或泛化。**零臆造引用。** 如果 `cite-guard` 可用，在此运行。
- **做法匹配：** 每条条款都追溯至已确认的答案；呈现任何剩余的 `[缺口]`。
- **强制链接 / 免责声明 / 律师标记**按触发条件存在。
如果任何检查失败，不要将政策呈现为"就绪"——呈现时表面化失败项。

### 第 7 步——交付包
输出：政策（按请求的语言，阿拉伯语按 `structure-clauses-and-craft.md` §7 做 RTL 适配）· 带日期的版本头 + "变更"条款 · 条件链接状态 · **已确认做法与已生成条款的对账**（关键的反欺骗工件）· `[缺口]` 清单 · 风险层级 /"咨询律师"横幅。默认输出格式：Markdown（按请求提供 HTML）。建议对任何机器翻译进行人工审查。

## 硬性规则（护栏）
- 除非用户确认，绝不要声称用户尊重 GPC / DNT、加密数据、有 DPO，或保留数据 N 天——这些是可执行的，虚假的属于欺骗。
- 绝不要将**员工/人力资源**数据并入消费者政策——建议单独的通知。
- 绝不要将此呈现为法律意见。对以下情形**坚持要求律师**（硬性横幅）：13 岁以下/儿童、健康/PHI、生物识别、超出标准处理器的金融科技/支付、出售数据 / 数据经纪、对用户数据的 AI 训练、大规模/系统性监控、大规模精确地理定位，或欧盟+英国+美国+其他同时覆盖。
- 保持政策与现实同步：绝不要只输出"请定期访问此页面了解变更"作为唯一更新机制——它是"不充分且不公平的"（WP260）。使用带日期的变更日志 + 主动的重大变更通知。

## 配套文件
隐私政策是必要的但不充分。在相关时，告知用户他们可能还需要：**Cookie 政策** + 同意横幅、处理者的 **DPA**（第 28 条）、**RoPA**（第 30 条）、健康领域的 HIPAA **隐私做法通知**、金融领域的 GLBA 通知，以及单独的**员工隐私通知**。本技能起草隐私政策（以及按请求的嵌入式 cookie 章节 / 独立 cookie 政策）；其他文件它仅标注而非静默省略。

---
*基于一手来源研究（监管文本、法规和官方平台条款）构建，2026 年 6 月核实。来源在每个 `references/` 文件内引用。AGPL-3.0。信息性模板——不构成法律意见。*

# 已验证参考包 —— 平台、第三方工具、Cookie 与 AI

> **零幻觉规则：** 仅引用本参考包或实时查询的内容。下文合同条款系从已抓取的供应商条款中意译；如需在高风险情境中**逐字**引用，请重新抓取供应商页面。研究中标记为 UNVERIFIED 的条目均已标注。最后验证时间：2026 年 6 月。

本文件回答两个实务问题：(1) 哪些因素使隐私政策**超出法规之外仍属强制**，以及 (2) 每个工具/AI 功能**要求你披露什么**。

---

## 1. 何时隐私政策由合同强制（而不仅是法律）

创始人一旦使用以下任何一项，即负有发布隐私政策的合同义务——**即使是零数据应用也必须发布**：
- **Apple App Store**（指南 5.1.1(i)）：每个应用必须在 App Store Connect 和应用内均链接隐私政策。
- **Google Play**：隐私政策链接须在 Play Console 和应用内提供；**不收集数据的应用仍须提交**并填写数据安全表单。
- **Google AdSense/AdMob/Ads、Google Analytics**：其条款要求提供披露 Cookie/标识符和数据使用的适当隐私政策。
- **Stripe、PayPal**：商户必须提供通知并提供隐私政策。
- **Mailchimp**：发件人必须发布链接到 Mailchimp 隐私政策的隐私政策。
- **Meta（Facebook）登录 / 商业工具**：强制提供公开的隐私政策 URL。
- **通过 Apple 登录 / Google 登录（OAuth/SSO）**：登录是政策必须披露的收集事件。

> **Skill 规则：** 如产品使用任何收集/传输用户或设备数据的第三方 SDK（广告、分析、支付、崩溃报告、社交登录），则隐私政策被强制要求，且必须**点名**该等第三方。

---

## 2. Apple App Store —— 政策须包含什么才能通过审核
指南 **5.1.1(i)** 要求政策清晰且明确地：
1. 说明**应用收集哪些数据、如何收集以及所有用途**。
2. 确认接收用户数据的任何**第三方**（分析、广告网络、SDK、关联公司）提供**同等保护**。
3. 解释**数据保留/删除政策**，以及**用户如何撤销同意/请求删除**。

另需：**5.1.1(ii)** 任何数据收集（即使是匿名的）都须获得同意，并提供简便的撤回方式；**5.1.1(v)** 具有账户的应用必须提供**应用内账户删除**；App Store Connect 中的 App 隐私“营养标签”必须与政策**一致**；**App 跟踪透明度（ATT）**——如应用将用户/设备数据与其他公司的数据关联用于广告，或与数据经纪商共享（“跟踪”），则必须触发 ATT 提示并披露跟踪行为；**5.1.4 儿童**类别禁止第三方分析/广告，并要求符合 COPPA/GDPR 及提供隐私政策。
来源（已抓取）：https://developer.apple.com/app-store/review/guidelines/ · https://developer.apple.com/app-store/user-privacy-and-data-use/

## 3. Google Play —— 政策须包含什么
用户数据政策要求政策全面披露：**开发者身份 + 隐私联系方式**；**访问/收集/使用/共享的所有个人/敏感数据**；**接收方（包括第三方 SDK）**；**安全实践**；**保留 + 删除**；须标注为“隐私政策”；并位于一个**有效、公开、无地域限制、非 PDF、不可编辑的 URL** 上（Play Console 和应用内均须如此）。**数据安全部分必须与隐私政策一致**。**显著披露与同意：** 当收集为后台/非预期时，要求应用内运行时披露 + **收集前明确同意**——仅凭政策**不够**。
来源（已抓取）：https://support.google.com/googleplay/android-developer/answer/10787469 · https://support.google.com/googleplay/android-developer/answer/10144311 · https://support.google.com/googleplay/android-developer/answer/9888076
（Google“为家庭设计”政策：请至 https://support.google.com/googleplay/android-developer/answer/9893335 核实——具体内容未验证。）

---

## 4. 第三方工具 → 每个工具要求你**披露**什么

| 工具 | 政策中必须披露的内容 | 同意门槛（欧盟） | 来源 |
|------|------------------------------|-------------------|--------|
| **Google Analytics (GA4)** | 使用 GA；Cookie/标识符/移动广告 ID 收集流量数据；数据由 Google 处理；任何广告功能及退出方式；链接“Google 如何使用信息…”；**不得向 Google 发送 PII** | 标签触发前须同意；自 **2024 年 3 月 6 日**起欧洲经济区/英国要求**同意模式 v2**（`ad_user_data`、`ad_personalization`） | https://www.google.com/analytics/terms/default.html · https://support.google.com/google-ads/answer/13695607 |
| **AdSense/AdMob/Ads** | 包括 Google 在内的第三方使用 Cookie 根据先前访问投放广告；如何退出（Google 广告设置、aboutads.info）；点名其他广告网络 | 面向欧洲经济区用户的个性化广告须明示同意；**NPA 备用方案**；经 Google 认证的 CMP + 同意模式 | https://support.google.com/adsense/answer/1348695 · https://support.google.com/adsense/answer/7670013 |
| **Meta Pixel / CAPI** | 使用 Pixel/CAPI；与 Meta（欧洲经济区为 Meta Platforms Ireland）共享数据用于衡量/定向投放；依据 SCC 向美国转移；链接 Meta 数据政策 | 在欧盟**不得在同意前触发**（最常见的 GDPR 违规）；需要可验证的同意 | https://www.facebook.com/legal/technology_terms |
| **Stripe** | Stripe 处理支付数据（卡、账单、姓名、邮箱、IP、设备、交易）；**既是处理者又是独立控制者**（欺诈/反洗钱）；完整卡数据由 Stripe 处理（PCI 范围）；链接 Stripe 隐私政策 | 法律依据；商户提供通知 | https://stripe.com/legal/dpa |
| **PayPal** | PayPal 用作处理者；对其收到的数据充当**独立数据控制者**；链接 PayPal 隐私声明；支付在 PayPal 系统上完成 | — | https://www.paypal.com/us/legalhub/paypal/data-protection |
| **Mailchimp** | 使用的邮件处理者；订阅者数据（邮箱、姓名、打开/点击跟踪、IP）；法律依据（营销同意）；转移机制（DPF/SCC）；退订/撤回 | 欧洲经济区/英国/瑞士联系人需要 DPA | https://mailchimp.com/gdpr/ |
| **Cloudflare / CDN** | CDN/安全提供者处理连接/日志数据，包括 **IP 地址**和请求元数据，用于交付/缓存/DDoS；依据 = 合法利益（安全）；已订立 DPA/SCC | 安全 Cookie（`__cf_bm`）通常属“严格必要”——按部署确认 | https://www.cloudflare.com/privacypolicy/ |
| **Hotjar / FullStory（会话录制）** | 会话录制/热图捕获交互；应用输入掩蔽；目的（用户体验）；**依据 = 同意**（非严格必要）；保留；退出 | **录制前须同意门槛**（Hotjar 默认在脚本加载时即开始录制） | https://help.hotjar.com/hc/en-us/articles/36819990621073-Processing-Personal-Data-in-Hotjar |
| **A/B 测试（Optimizely/VWO/AB Tasty）** | 变体分配 Cookie；目的（优化）；**依据 = 同意**（非严格必要） | **设置 Cookie 前须同意** —— 常见陷阱是在脚本加载时即设置 | https://www.convert.com/blog/privacy/analytics-and-a-b-testing-cookies-only-after-consent-in-europe/ |

---

## 5. Cookie 与追踪基础设施
- 只要拥有欧盟/欧洲经济区（及英国）访客，即须设置 **Cookie 横幅/CMP**：**非必要 Cookie（分析和广告）在用户给出明确事先同意前不得设置**；拒绝与接受同等容易；不得设置 Cookie 墙/暗黑模式；同意前阻止脚本。CNIL 因未在同意前阻止 Cookie 对 Google 罚款 1 亿欧元、对 Amazon 罚款 5000 万欧元。
- **Cookie 类别（与 ICO 一致）：** (1) 严格必要 —— 豁免，从严解释；(2) 功能/偏好 —— 同意；(3) 分析/性能 —— 同意（非严格必要）；(4) 广告/定向投放 —— 同意。
- **IAB TCF**（透明度与同意框架）：程序化/实时竞价（RTB）的广告科技同意字符串标准。现行 **v2.3**（2026 年 2 月 28 日之后创建的字符串须含 `disclosedVendors` 段）；在 v2.2 下，广告/内容个性化供应商可**仅依赖同意**（而非合法利益），且首个横幅层必须显示供应商总数。**告诫：** **TC 字符串属于个人数据**（欧盟法院 C-604/22，2024 年 3 月），布鲁塞尔上诉法院（2025 年 5 月 14 日）认定 TCF 不符合 GDPR——“我们使用 IAB 框架”不是合规盾牌。
- **同意记录 / 同意证明（GDPR 第 7(1) 条 + 第 5(2) 条）：** 记录**谁 / 作出了什么决定 / 何时 / 何地 / 哪个通知版本**；保留至处理期间 + 诉讼时效期间（约 3–5 年）。
来源：https://usercentrics.com/knowledge-hub/cnil-cookies/ · https://iabeurope.eu/transparency-consent-framework/ · ICO PECR cookies 指南（https://ico.org.uk/.../cookies-and-similar-technologies/）

---

## 6. 机器可读信号 —— 实际有效的方式（照此执行）
- **全球隐私控制（GPC）** 是唯一具有法律效力的机器可读信号：`Sec-GPC: 1` 请求头 + `navigator.globalPrivacyControl` + 可选的 **`/.well-known/gpc.json`**（声明 `gpc:true`）。在加利福尼亚/科罗拉多/康涅狄格/新泽西具有约束力（且范围不断扩大）；**Sephora 因无视该信号支付了 120 万美元（加州总检察长，2022 年 8 月）**。
  → **行动：** 尊重 GPC、在政策中声明，并发布 `/.well-known/gpc.json`。
- **P3P 已死亡**（W3C 于 2018 年废弃；曾被伪造的简化政策滥用）。**schema.org 没有已采纳的隐私政策类型**——`schema.org/PrivacyPolicy` 返回 404；宣称相反的 SEO 博客是在重复一个未合并的提案。不要在此浪费时间。
- **DPV（W3C 数据隐私词汇表）** 是一个新兴的社区组分类——不是标准，生产采用几乎为零。观察即可，不要部署。
来源：https://www.w3.org/TR/gpc/ · https://globalprivacycontrol.org/ · https://oag.ca.gov/news/press-releases/attorney-general-bonta-announces-settlement-sephora-part-ongoing-enforcement

---

## 7. AI / LLM 特定披露（2025–2026 前沿）

### 7.1 使用用户数据训练 + 追溯陷阱
- **FTC 规则：** 通过静默、**追溯性**政策变更开始将已收集的数据用于 AI 训练，可能构成不公平或欺骗行为。实质性新用途（如训练）一般需要在**新处理开始前**获得明确的告知/同意。（FTC，2024 年 2 月；基础判例为 *Gateway Learning* 2004 案——“你可以改变规则，但不能在比赛结束后改变”。）
- **须披露：** 用户输入/内容是否用于训练/改进模型、依据以及退出方式（或在要求时选择加入）。**默认不训练，除非用户确认。**
来源：https://www.ftc.gov/policy/advocacy-research/tech-at-ftc/2024/02/ai-other-companies-quietly-changing-your-terms-service-could-be-unfair-or-deceptive

### 7.2 第三方模型提供者作为分处理者（已验证的供应商立场）
如产品调用 OpenAI/Anthropic/Google API，将其列为分处理者，并说明提示词/输出的传输情况以及供应商立场：
- **OpenAI API：** 除非你明确选择加入，发送到 API 的数据**不**用于训练模型；滥用监测日志保留最长 30 天，除非启用零数据保留（ZDR）。https://developers.openai.com/api/docs/guides/your-data
- **Anthropic 商业/API：** 默认情况下**不**使用商业产品的输入/输出进行训练，除非你明确反馈/选择加入。https://privacy.claude.com/en/articles/7996868-is-my-data-used-for-model-training（“7 天/30 天”API 保留数据在主页面未验证——未经确认请勿引用）
- **Google Gemini API / Vertex AI：** “Gemini 不使用你的提示词或其响应作为数据来训练其模型。”https://docs.cloud.google.com/gemini/docs/discover/data-governance

### 7.3 自动化决策与画像分析（须披露的权利）
- **GDPR 第 22 条** —— 不受具有法律或重大影响的纯自动化决策约束的权利；第 13(2)(f) 条/第 14(2)(g) 条要求披露**逻辑、重要性和预期后果**。https://gdpr-info.eu/art-22-gdpr/
- **美国州画像退出规定：** 弗吉尼亚/科罗拉多/康涅狄格等州允许消费者退出“为作出产生法律或类似重大影响的决定而进行的画像分析”。**加州 ADMT 条例**自 2026 年 1 月 1 日生效，重大决定合规自 **2027 年 1 月 1 日**起（使用前通知 + 退出 + 逻辑访问）。

### 7.4 聊天机器人与 AI 内容披露
- **欧盟《人工智能法》第 50 条**（自 **2026 年 8 月 2 日**起适用）：最迟在首次交互时告知用户其在与 AI 交互（除非显而易见）；以机器可读方式标记 AI 生成的合成内容；部署者必须披露深度伪造和 AI 生成的公共利益文本。https://artificialintelligenceact.eu/article/50/
- **美国：** 加州 **SB 1001**（机器人披露，自 2019 年起）；**SB 942** AI 内容透明度 + **AB 2013** 训练数据透明度（均自 2026 年 1 月 1 日生效）。

> **Skill 规则：** 存在 AI 功能 → 列明 AI 分处理者、说明训练立场（默认不训练）、披露任何自动化决策（逻辑/重要性/后果）+ 退出方式，并添加“你在与 AI 对话”的聊天机器人披露。AI 使用用户数据训练 → 触发“请咨询律师”的硬性标记。

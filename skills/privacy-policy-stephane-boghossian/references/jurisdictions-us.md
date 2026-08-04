# 经核实的参考资料包——美国（联邦 + 州）

> **零幻觉规则：** 仅引用本资料包或实时 `legal-data-hunter` 查询的内容。不得自行编造法条章节编号、每次违规罚款金额或生效日期，超出本处所述并注明来源的范围。有疑问时，以通俗语言指称法律（"加州 CCPA/CPRA"、"FTC 法案"）并从功能上描述*权利*。最后核实时间：2026 年 6 月。

美国**没有单一的联邦隐私法**。覆盖 = 联邦部门层面（FTC 法案、COPPA、HIPAA、GLBA 等）**加上**约 20 部综合性的**州**法律。统一的联邦连接点是**《FTC 法案》第 5 条**：隐私政策是一组**可执行的陈述**——说一套做一套属于"不公平或欺骗性做法"。见执法（§7）。

---

## 1. 加利福尼亚州——CCPA（经 CPRA 修订）（基准）

**谁必须合规（满足任一）：** 在加州开展业务的营利性企业，且 (a) 年度总收入 >2500 万美元；或 (b) 购买/出售/共享 100,000 名以上加州消费者/家庭的人信息；或 (c) 年收入中 ≥50% 来自出售/共享个人信息。（门槛以加州总检察长为准；引用前请核实 oag.ca.gov/privacy/ccpa 的当前数值。）

**隐私政策必须披露：**
- 所收集**个人信息的类别**（CCPA 使用约 11 个法定类别）、**来源类别**、**商业/经营目的**，以及个人信息被披露/出售/共享的**第三方类别**。
- **12 个月回顾**：所收集、出售/共享和披露的类别——或明确声明企业过去 12 个月内未出售/共享。
- **消费者权利**及其行使方式：**知情/访问**、**删除**、**更正**、**退出出售/共享**、**限制敏感个人信息的使用**、行使权利不受到**差别待遇**，以及使用**授权代理人**的权利。
- 提交请求的方法 + 企业如何验证身份。

**强制性链接/通知（创始人遗漏的部分）：**
- **"Do Not Sell or Share My Personal Information"（不出售或共享我的个人信息）**链接——企业出售个人信息或为**跨语境行为广告**而**共享**信息时需要（使用 Meta/Google 广告像素通常算作"共享"）。自 CPRA"共享"扩展于 **2023 年 1 月 1 日**生效以来一直要求。
- **"Limit the Use of My Sensitive Personal Information"（限制我的敏感个人信息的使用）**链接——如使用/披露 SPI 超出许可目的时需要。（可使用单一合并退出链接 / Alt 退出图标。）
- **收集时通知（Notice at Collection）**——在收集时或收集前，列出收集的类别和目的，并附完整政策链接。（仅隐私政策本身**不**满足收集时通知——必须在收集时呈现。）
- **全球隐私控制（GPC）：** 加州要求企业将用户启用的 GPC 信号视为有效的退出出售/共享。（见 §6 + `platform-ai-cookies.md`。）

**敏感个人信息（SPI）类别：** 社保号/驾照/护照/金融账户；精确地理位置；种族/民族出身；宗教/哲学信仰；工会会员身份；邮件/电子邮箱/短信内容（非发给企业的）；基因数据；用于唯一识别的生物识别数据；健康；性生活/性取向。

**自动化决策（ADMT）：** CPPA 敲定了 ADMT/风险评估/网络安全审计法规——**2026 年 1 月 1 日生效**，**重大决策的 ADMT 合规自 2027 年 1 月 1 日起要求**。对于重大决策（金融、住房、雇佣、医疗等）：使用前通知、退出权，以及获取"关于逻辑的有意义信息"。来源：https://cppa.ca.gov/regulations/ccpa_updates.html · https://cppa.ca.gov/announcements/2025/20250923.html

来源：https://oag.ca.gov/privacy/ccpa · https://cppa.ca.gov/faq.html

### CalOPPA（较旧，仍适用于任何收集加州居民数据的网站）
要求醒目的隐私政策，并且——值得注意的是——披露**网站如何响应"请勿跟踪"（DNT）信号**（即使响应是"我们不响应"，也必须披露）。

---

## 2. 其他州综合法律（2026 年约有 20 部生效）

截至 2026 年，约有 20 个州有综合法律生效；**印第安纳州、肯塔基州和罗德岛州于 2026 年 1 月 1 日生效**（加入 CA、VA、CO、CT、UT、TX、OR、MT、IA、DE、NJ、NH、NE、MN、MD、TN、IN 等）。来源：https://www.multistate.us/insider/2026/2/4/all-of-the-comprehensive-privacy-laws-that-take-effect-in-2026 · https://iapp.org/news/a/new-year-new-rules-us-state-privacy-requirements-coming-online-as-2026-begins

**共同分母消费者权利（大多数州）：** 访问、删除、更正、数据可移植性，以及**退出** (i) **出售**、(ii) **定向广告**和 (iii) 为作出具有法律/重大影响决策而进行的**画像**。许多州增加了被拒绝请求的**上诉权**。

**生成器必须分支的关键差异：**
- **敏感数据：** **弗吉尼亚州、科罗拉多州**（及其他几个州）对敏感数据要求**选择加入（opt-IN）同意**——而 CCPA 是退出（限制）模式。如用户受众包括这些州，技能必须适用选择加入。
- **通用退出机制（UOOM / GPC）：** 在越来越多的州必须尊重——加利福尼亚、科罗拉多、康涅狄格、得克萨斯、俄勒冈、蒙大拿、特拉华、新泽西、新罕布什尔、明尼苏达、马里兰（还有更多加入）。政策应声明尊重 GPC（仅在确实做到时）。
- 高风险处理的**数据保护评估**；**补救期**各异（有些正在废止）。
- 执法由**州总检察长**进行（这些综合法律中无私人诉权，除狭窄的 CCPA 数据泄露私人诉讼外）。民事罚款常见引用约为**每次违规 7,500 美元**（CCPA，故意/涉及未成年人）——引用前核实当前数值。

**"一次性合规所有州"的实用配方：** 按**最严格共同分母**构建——尊重所有退出（出售/共享、定向广告、画像）+ GPC；提供访问/删除/更正/可移植性 + 上诉；对敏感数据适用选择加入；如出售/共享或使用 SPI，则显示加州的这两个链接。

---

## 3. COPPA——13 岁以下儿童（联邦）

COPPA（16 CFR 第 312 部分，FTC）适用于**面向 13 岁以下儿童**的网站/服务运营商，或**明知地**从 13 岁以下儿童收集数据的运营商。要求：**在线通知**（COPPA 特定隐私政策部分）+ **直接通知父母** + **收集前可验证的父母同意**，以及数据最小化、安全和父母审查/删除权。

**2025 年规则修正（已核实）：** 于 **2025 年 4 月 22 日**在《联邦公报》公布；**2025 年 6 月 23 日**生效；**合规须在 2026 年 4 月 22 日前**完成。关键变化：
- **生物识别标识符**和**政府签发的标识符**被加入"个人信息"的定义。
- **向第三方披露**儿童个人信息（如用于定向广告）需要**单独的可验证父母同意**。
- **不得无限期保留**——仅为收集目的合理必要期间保留；要求书面数据保留政策。
- 新增 **VPC 方法**（如基于知识的认证；"短信加"；政府证件 + 面部匹配）。
来源：https://www.ftc.gov/news-events/news/press-releases/2025/01/ftc-finalizes-changes-childrens-privacy-rule-limiting-companies-ability-monetize-kids-data · https://www.whitecase.com/insight-alert/unpacking-ftcs-coppa-amendments-what-you-need-know · https://www.ecfr.gov/current/title-16/chapter-I/subchapter-C/part-312

> **技能规则：** 任何 13 岁以下受众 → 完整 COPPA 模块 + 硬性"发布前先咨询律师"标记。

---

## 4. 部门叠加——标记，不要起草（各自是独立制度）
如信息收集揭示以下任一情形，应提示消费者隐私政策**不足够**、需要专家/律师。不得泛泛起草这些通知。
- **HIPAA**——受保护的健康信息；需要单独的《隐私实践通知》。
- **GLBA**——金融机构；需要 GLBA 隐私通知。
- **FERPA**——教育记录。
- **VPPA**——视频观看数据（围绕视频页面像素存在活跃的原告诉讼群体）。
- **BIPA（伊利诺伊州）**——生物识别数据；**私人诉权**并附法定赔偿（**不要**引用具体赔偿数字——需核实）。得克萨斯和华盛顿有生物识别法律但无私诉权。
- **CAN-SPAM / TCPA**——电子邮件和短信/电话营销规则（同意 + 退出机制）。

---

## 5. 美国何时在法律上要求隐私政策？
- 如从**加利福尼亚州**居民收集个人数据（CalOPPA + 满足门槛时 CCPA）或任何适用综合法律的州。
- 如 COPPA 适用（13 岁以下受众）。
- 实务上几乎总是——通过**合同**——应用商店、广告网络、分析和支付处理商都要求隐私政策，无论法规如何（见 `platform-ai-cookies.md`）。

---

## 6. 全球隐私控制（GPC）——可执行的信号
GPC 传递一个具有约束力的意图：退出出售/共享。加州要求尊重它；科罗拉多州批准 GPC 作为**首个公认的通用退出机制**（控制者须在 **2024 年 7 月 1 日**前合规）；康涅狄格、新泽西等州将其视为具有约束力。**Sephora 专门因未能尊重 GPC 支付了 120 万美元（加州总检察长，2022 年 8 月）。** 记录合规情况：在政策中声明，并发布带 `gpc: true` 的 `/.well-known/gpc.json`。来源：https://oag.ca.gov/news/press-releases/attorney-general-bonta-announces-settlement-sephora-part-ongoing-enforcement · https://coag.gov/opt-out/

> 仅在用户确认技术上确实尊重 GPC 时才声明"我们尊重 GPC"——虚假声明本身就是欺骗。

---

## 7. FTC 第 5 条 + 执法（"必须与做法一致"规则）
FTC 将隐私政策视为**可执行的陈述**；政策所述与实际所为之间的差距属于不公平/欺骗性做法。两个锚定案例：
- **Sephora——120 万美元**（加州总检察长，2022 年 8 月）：未能处理 GPC 退出 / 披露"出售"。
- **FTC v. OkCupid / Match（2026 年 3 月 30 日）：** 政策称数据仅与有限类别共享；公司却将约 300 万用户的照片 + 位置 + 人口统计数据传输给面部识别供应商（Clarifai）用于 AI 训练，无通知/无退出。FTC 的表述："隐私政策不仅仅是信息性文件。它是向消费者作出的陈述，依据第 5 条，这些陈述是可执行的承诺。"来源：https://www.parkerpoe.com/news/2026/04/ftc-cracks-down-on-privacy-policy-transparency-signaling
- FTC：**悄悄/追溯性地**更改政策（如开始对已收集数据进行 AI 训练）本身可能构成欺骗。来源：https://www.consumerfinancemonitor.com/2024/02/28/ftc-warns-quietly-changing-privacy-policies-may-be-an-unfair-or-deceptive-practice/

> **技能首要指令（美国及所有地区）：** 只陈述用户确认实际发生的内容。绝不默认加入美化条款。这一条规则可防止最常见、代价最高的失败。

---

## 8. 加利福尼亚州 AI 透明度法规（2026 年 1 月 1 日生效）
- **SB 942（加州 AI 透明度法案）：** 大型生成式 AI 提供者（月均加州用户 >100 万）必须对 AI 生成内容提供可见 + 潜在披露，并提供免费检测工具。
- **AB 2013（生成式 AI 训练数据透明度）：** 开发者必须公开记录训练数据的来源/类型，以及是否包含个人信息/受版权保护材料。
- **SB 1001（机器人披露，自 2019 年 7 月 1 日起）：** 使用机器人激励交易或影响投票时，必须明确披露。
来源：https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202320240SB942 · https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202320240AB2013 · https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=201720180SB1001

### 主要来源（已核实）
- 加州总检察长 CCPA：https://oag.ca.gov/privacy/ccpa · CPPA：https://cppa.ca.gov/
- COPPA：https://www.ftc.gov/business-guidance/privacy-security/childrens-privacy · https://www.ecfr.gov/current/title-16/chapter-I/subchapter-C/part-312
- IAPP 美国州法律追踪器（实时州清单）：https://iapp.org/resources/article/us-state-privacy-legislation-tracker/
- MultiState 2026 生效日期：https://www.multistate.us/insider/2026/2/4/all-of-the-comprehensive-privacy-laws-that-take-effect-in-2026

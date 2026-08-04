# 参考——创始人/联合创始人协议：起草最佳实践

> 供 `founder-agreement-drafting` Claude 技能使用的研究基础。编制于 2026-07-06，来源于一手
> 资料——Y Combinator、Cooley GO、Clerky、Carta、Orrick（含其 Stripe Atlas 法律指南）、Gunderson
> Dettmer、Wilson Sonsini、SeedLegals、Slicing Pie（Mike Moyer）、Noam Wasserman / HBS（《创始人的困境》
> （*The Founder's Dilemmas*））、NBER、IRS/财政部法规以及指名判例——经由实时网络搜索与抓取获得。
> 下文每项主张均附有行内来源。凡来源单薄或无法核实之处（主要是 MENA 地区创始人特有机制，以及少数
> 广泛流传但无法溯源的统计数据），均已明确标注而非掩盖——见**第 10 节 来源说明**。
>
> 本文件是起草辅助材料，不构成法律意见。投入使用前请参阅**第 9 节 伦理与范围**。

---

## 目录

1. [什么是创始人协议](#1-什么是创始人协议)
2. [标准条款清单](#2-标准条款清单)
3. [股权分配框架](#3-股权分配框架)
4. [成熟（Vesting）深度解析](#4-成熟vesting深度解析)
5. [知识产权转让](#5-知识产权转让)
6. [离任/退出机制](#6-离任退出机制)
7. [创始人常见纠纷与错误](#7-创始人常见纠纷与错误)
8. [实体与法域差异](#8-实体与法域差异)
9. [伦理与范围](#9-伦理与范围)
10. [来源说明](#10-来源说明)

---

## 1. 什么是创始人协议

### 1.1 它是一个类别，而非标准文件

与公司注册证书（certificate of incorporation）不同，“创始人协议”（或“联合创始人协议”）并非一份
标准化的文件——美国市场实践对是否应当将其作为独立文件存在，本身就有分歧。

- **Cooley GO**：“大多数公司在设立时并不使用股东协议”——创始人转而依赖特拉华州公司法的默认规则、
  章程细则（bylaws）和成熟协议；“对大多数公司而言，这些默认规则、协议以及创始人之间的信任已经足够。”
  凡确实使用的，通常涵盖三方面内容：**治理**（董事会选举、高管）、**转让限制**（股票出售的权利）、
  以及**回购情形**（死亡、伤残、终止）。
  [Cooley GO，《创始人是否应当签订股东协议？》](https://www.cooleygo.com/founder-shareholder-agreements/)
- **Clerky**：美国初创企业“很少有单一的‘创始人协议’”。此类协议本应涵盖的内容，实际分散在
  **限制性股票购买协议（RSPA）**（股权+成熟）、**CIIA/PIIA**（保密信息与发明转让协议——与
  “专有信息与发明转让协议”基本同义）、**章程细则**（治理）以及特拉华州法律默认规则之中。
  [Clerky，《创始人法律概念》](https://handbooks.clerky.com/legal-concepts) ·
  [Clerky 术语表](https://handbooks.clerky.com/glossary)
- **Startup Boston** 更进一步：独立的创始人协议本身可能就是“公司发行创始人股权实践存在缺陷”或
  创始人沟通不畅的症状，且此类协议“受到许多资深投资人排斥”，可能成为尽职调查中的危险信号——
  “通常更明智的做法是解决根本问题……而非用一份创始人协议把问题掩盖过去。”
  [Startup Boston，《创始人协议解决的问题多还是制造的问题多？》](https://www.startupbos.org/post/do-founders-agreements-solve-more-problems-than-they-create)

**对本技能的实际启示**：将“创始人协议”理解为*实质性条款*（股权、成熟、知识产权、离任、决策机制），
而非执著于某一份物理文件。将上述条款写入实体类型和阶段实际要求的相应文件（特拉华 C 型公司为
RSPA + CIIA + 章程细则；有限责任公司为经营协议（operating agreement）；英国有限公司为章程大纲
（Articles）+ 单独的股东协议）——真正的独立创始人协议，主要用作上述文件尚不存在之前的**设立前
过渡文件**。

### 1.2 与其他文件的区分

| 文件 | 实际规范的内容 | 与创始人协议的关系 |
|---|---|---|
| **公司注册证书/章程大纲** | 在州层面使实体合法存在；章程性文件 | 居于一切文件之上——未经备案不产生任何法律效力。[Clerky](https://handbooks.clerky.com/legal-concepts/core) |
| **章程细则（Bylaws）** | 备案后通过的内部治理规则（董事会规模、首任董事、转让审批机制） | 人们期望在创始人协议中看到的“治理”条款实际多在此处——如股票转让的董事会批准要求。[Cooley GO](https://www.cooleygo.com/founder-basics-founders-stock/) |
| **股东协议（Shareholders'/Stockholders' Agreement）** | 创始人层面的治理、转让限制、回购条款 | 功能上最接近设立后的“创始人协议”——但公司完成一轮有定价融资的**那一刻即被取代**，换成 NVCA 式投资人文件组合（投票协议、优先购买权/共同出售、投资人权利协议）。[Cooley GO](https://www.cooleygo.com/founder-shareholder-agreements/) |
| **股票购买协议/限制性股票购买协议（RSPA）** | **创始人成熟（vesting）实际落地之处**——支付价格、成熟时间表、公司回购权 | 这才是真正的机制；创始人协议中“我们将按 4 年成熟”的表述，在 RSPA + 董事会决议 + 及时提交 83(b) 选择书存在之前，仅是意向。[Cooley GO](https://www.cooleygo.com/founder-basics-founders-stock/) · [Orrick Start-Up Forms](https://www.orrick.com/Total-Access/Tool-Kit/Start-Up-Forms/Founders-Stock-Purchase) · [Gunderson Dettmer Catalyze](https://catalyze.gunder.com/en/knowledge-articles/resource/formation) |
| **LLC 经营协议（Operating Agreement）** | 将公司分散在证书/章程细则/股东协议中的内容合而为一——所有权比例、出资、管理、买卖条款、解散 | 对 LLC 而言，该文件通常**就是**创始人协议；不存在单独的独立文件。[Harbour Business Law](https://harbourbusinesslaw.com/when-do-i-need-a-founder-agreement-versus-an-operating-agreement/) |

### 1.3 为何要在设立公司前签约

**设立前协议可降低的风险：**

- **无主知识产权（Orphaned IP）**——实体成立前的工作成果（代码、路演材料、原型）没有自动的公司
  所有权人。Gunderson Dettmer 建议在实体设立后签署一份**技术转让协议**，将设立前的知识产权转让
  给公司。[Gunderson Dettmer](https://catalyze.gunder.com/en/knowledge-articles/resource/formation)
- **贡献者带着创意离开**——没有设立前的承诺约束，早期参与者不受任何法律约束。
- **股权分配模糊固化为积怨**——YC 认为尽早决定“可以避免旷日持久的谈判”，但时机取舍是双向的
  （见第 3 节关于“快速握手”代价的论述）。
  [YC，《联合创始人之间分配股权的 5 种方式》](https://www.ycombinator.com/library/5x-how-to-split-equity-among-co-founders)
- **“谁才算创始人”本身含糊不清**——这直接决定离开的贡献者能保留什么。YC 明确警告不要把兼职贡献者
  当作全职联合创始人对待。
  [YC，《应避免的联合创始人股权错误》](https://www.ycombinator.com/library/LP-co-founder-equity-mistakes-to-avoid)

**设立前协议通常包含的内容**：知识产权转让意向（临时相互转让，或承诺向未来实体转让）；股权分配
意向；成熟意向（4 年/1 年悬崖已趋同成为标准——见第 4 节）；角色/头衔与决策机制意向；以及设立前
分手的条款。YC 对悬崖期前离开的创始人的具体数字：**仅象征性股权（2–5%）**；悬崖期后，上限约为
**5%** 或协商返还，并附董事会辞职与签署的解除文件。
[YC，《应避免的联合创始人股权错误》](https://www.ycombinator.com/library/LP-co-founder-equity-mistakes-to-avoid)

**后来被正式化并取代它的内容**：股权意向 → 依董事会决议按面值在 RSPA 项下实际发行的股份；成熟意向 →
已签署 RSPA 中的真实成熟时间表加上及时的 83(b) 选择书；知识产权意向 → 实际的 CIIA/PIIA；治理意向 →
注册证书 + 章程细则。Cooley GO 划定的外部边界：“任何股东协议都会在第一轮有定价融资时被投资人要求的
一套新协议所取代。” [Cooley GO](https://www.cooleygo.com/founder-shareholder-agreements/)

**起草启示**：在任何设立前或早期创始人协议中写入明确的终止/替代条款，将其终止与客观可验证的事件
挂钩（RSPA 签署、有定价融资交割），并指明哪些条款（通常为保密、知识产权）仍经由 CIIA 独立存续。

---

## 2. 标准条款清单

逐条完整的条款矩阵。说明每一条“做什么”以及最常见的起草陷阱。股权、成熟、知识产权和离任条款——
争议率最高的条款——的深度内容见第 3–6 节；本表对上述条款保持简洁，对其余条款则力求全面。

| # | 条款 | 作用 | 起草陷阱 | 来源 |
|---|---|---|---|---|
| 1 | **当事人与实体** | 界定谁是“创始人”、协议并入哪个实体（现存或拟设立）；将每位创始人对应到职能领域（产品、工程、销售、知识产权） | 将“创始人”视为不言自明——设立前贡献者事后主张创始人地位，尽管从未被列为当事人；或真正的早期技术联合创始人被遗漏，因为协议只在设立后才起草 | [Clerky](https://handbooks.clerky.com/legal-concepts/formation) · [San Jose Business Lawyers Blog](https://www.sanjosebusinesslawyersblog.com/what-you-need-to-know-about-pre-incorporation-founders-agreements/) |
| 2 | **股权所有权与分配** | 确定每位创始人在设立时的持股比例 | 一天之内谈妥、无任何书面理由的反射性 50/50 或 N 等分分配——见第 3 节 | [YC](https://www.ycombinator.com/blog/splitting-equity-among-founders/) · [Carta](https://carta.com/data/founder-equity-split-trends-2024/) |
| 3 | **成熟与悬崖（Vesting & cliff）** | 反向成熟：先发行股份，公司回购权随时间逐步失效 | 悬崖边缘的不连续性（第 11 个月 = 0%，第 13 个月 = 25%）直到离职成定局才被理解；或完全跳过成熟——见第 4 节 | [Clerky](https://help.clerky.com/article/1736-what-are-customary-stock-vesting-terms-for-startup-founders) · [Cooley GO](https://www.cooleygo.com/founder-basics-founders-stock/) |
| 4 | **加速（单触发 vs 双触发）** | 规范控制权变更时未成熟股份是否/何时加速成熟 | 单触发加速消除收购方的挽留杠杆，可能压低交易价格甚至毁掉交易；双触发的保护力度取决于“有因（Cause）”“正当理由（Good Reason）”的定义 | [Orrick](https://www.orrick.com/en/Insights/2026/04/Single-and-Double-Trigger-Vesting-Acceleration-What-founders-and-employees-should-know) · [Pulley](https://pulley.com/guides/single-trigger-vs-double-trigger-acceleration) |
| 5 | **角色与头衔** | 分配正式头衔*以及*其背后的决策权 | 过度关注头衔标签而实际权力未界定——“两个创始人都认为自己是 CEO” | [Ramp](https://ramp.com/blog/what-is-in-a-startup-founder-agreement) · [Equity Matrix](https://equitymatrix.io/blog/founder-agreements-what-to-include) |
| 6 | **职责与时间投入** | 明确预期的工时/全职性；应直接驱动股权分配 | 一位创始人全职、另一位兼职（本职工作之外每周约 10 小时）却锁定等额分配，且无任何修正机制 | [Pillsbury Propel](https://www.pillsburypropel.com/guidance/how-to-split-equity-between-co-founders-and-stay-friends) |
| 7 | **决策/投票/董事会** | 规范融资前的重大决策权和融资后的董事会构成 | 融资前接受将权力交给投资人且无任何保障的治理条款；或矫枉过正，以一致同意要求赋予少数派创始人就常规事项的结构性否决权 | [Paul Graham，《创始人控制权》](https://www.paulgraham.com/control.html) · [Valle Legal](https://www.vallelegal.com/insights/protecting-founder-control) |
| 8 | **僵局解决机制** | 预先约定的打破创始人平局程序（在 50/50 分配中尤为突出） | **完全没有机制**——唯一救济变成司法解散；或将猎枪/买卖条款视为常规，而它筛选的是谁有钱，而非谁有理 | [SPZ Legal](https://spzlegal.com/blog/incorporation/how-to-resolve-deadlock-in-50-50-founder-situations) · [Bianchi Fasani Green Law](https://bfg.law/deadlock-provisions-shareholder-operating-agreements/) |
| 9 | **知识产权转让** | 现在时态（“特此转让”）转移创始人创造的知识产权给公司 | 将来时态“将转让”的表述——见第 5 节（*Stanford v. Roche*） | [Patent Docs](https://patentdocs.org/2011/06/06/board-of-trustees-of-the-leland-stanford-junior-university-v-roche-molecular-systems-inc-2011/) |
| 10 | **保密** | 联合创始人之间就商业秘密、商业计划、设立前讨论的相互保密义务 | 无存续条款（义务在离职时看似失效，恰在泄密动机达到峰值之时）；保密范围仅界定为设立后的“公司保密信息”，遗漏实体成立前的讨论 | [Orrick Stripe Atlas 法律指南，第 16-17 页](https://stripe.com/files/atlas/orrick-legal-guide.pdf) |
| 11 | **竞业禁止/禁止招揽** | 限制离职创始人竞争/挖角 | 全文档中可执行性风险最高——见下方法域表 | [Justia Cal. B&P §16600](https://law.justia.com/codes/california/code-bpc/division-7/part-2/chapter-1/section-16600/) |
| 12 | **离任条款与回购** | 好离任者/坏离任者区分；离职时已成熟股份的回购 | “有因（Cause）”“正当理由（Good Reason）”未定义；单人创始人公司初期往往**完全没有成熟安排**——见第 6 节 | [Orrick 法律指南，第 19-22 页](https://stripe.com/files/atlas/orrick-legal-guide.pdf) · [Ledgy](https://ledgy.com/blog/good-leaver-bad-leaver-clauses) |
| 13 | **转让限制/优先购买权（ROFR）** | 未经公司/创始人同意不得向第三方转让；约 30 天匹配窗口为行业标准 | 以股票质押作为贷款担保未被认定为需要同意的“转让”，违约时绕开优先购买权窗口；共同财产州（community-property state）的配偶可持有独立权益，除非其同时签署 | [Orrick 法律指南，第 24 页](https://stripe.com/files/atlas/orrick-legal-guide.pdf) · [NVCA 优先购买权范本](https://nvca.org/wp-content/uploads/2019/06/NVCA-Model-Document-Right-of-First-Refusal.docx) |
| 14 | **出资与未来融资** | 处理现金 vs 劳务出资；创始人可以知识产权转让换取股份，仅就差额部分欠付现金 | 过度细化财务条款（如一致同意的资本催缴），而真实 VC 投资条款清单（term sheet）会直接将其覆盖——此处应刻意从简，并设置自动触发/被替代机制 | [Orrick 法律指南，第 22 页](https://stripe.com/files/atlas/orrick-legal-guide.pdf) |
| 15 | **营收前薪酬/费用报销** | 规范融资前的薪酬与费用凭证 | 非正式的不平等薪酬且无书面记录；个人/业务费用混同（双重风险：IRS 重新定性 + 公司面纱刺穿） | [Bend Law Group](https://www.bendlawgroup.com/post/catch-22-founders-must-pay-themselves-even-before-their-company-earns-revenue) |
| 16 | **争议解决** | 谈判 → 调解 → 有约束力仲裁；准据法与仲裁地 | **完全没有机制**——被引为 Housing.com 创始人纠纷（12 位原始创始人中 9 位于 2016 年前退出）的直接促成因素之一；或仲裁地对创始人实际居住地不切实际 | [AAA 条款起草](https://www.adr.org/clause-drafting/) · [iPleaders](https://blog.ipleaders.in/co-founders-agreement-disputes-suggestions/) |
| 17 | **修订** | 明确谁必须同意、如何修改协议 | 程序沉默/含糊，为“非正式信息构成修订”的主张留下空间；即便对已离职但仍持股的创始人也要一致同意，等于赋予其单方否决权 | [Law Insider 条款库](https://www.lawinsider.com/clause/founders-agreement) |
| 18 | **期限与退出/协议本身的终止** | 界定协议何时不再约束——通常与有定价融资交割挂钩 | 从未规定终止/替代事件，对协议是否与日后 NVCA 式文件冲突留下模糊空间 | [Law Insider](https://www.lawinsider.com/clause/founders-agreement) · [Orrick UK 创始人系列](https://www.orrick.com/en/Insights/2022/06/Founder-Series-Top-Tips-to-Follow-When-Setting-Up-Your-Private-Limited-Company) |

### 2.1 竞业禁止/禁止招揽——可执行性警示详述（上述条款 11，展开）

这是清单中法域敏感性最高的条款，应在技能中标注为**使用时须做现行法律核查**，而非永久固定的文本：

- **加利福尼亚州（商业与职业法典 §16600）**：近乎全面禁止——无论“如何窄化定制”均无效，仅少数
  并购例外（§16601，须出售*商誉*或*全部*所有权权益；法院直接认定无效而非“划线修改”
  （blue-pencil））。2024 年修订（SB 699/§16600.5、AB 1076/§16600.1）将适用范围延伸至州外竞业禁止
  条款——若员工日后在加州工作/居住；要求 2024 年 2 月 14 日前逐人送达通知，违者**每次违规罚款
  $2,500**。
  [Justia](https://law.justia.com/codes/california/code-bpc/division-7/part-2/chapter-1/section-16600/) ·
  [Shulman Rogers](https://www.shufirm.com/recent-amendments-to-california-business-and-professions-code-section-16600-sharper-teeth-for-a-potent-statute-and-a-serious-trap-for-unwary-employers)
- **美国各州拼图（截至 2026 年 3 月）**：全面禁止的州有加利福尼亚、明尼苏达、蒙大拿、北达科他、
  俄克拉荷马、怀俄明；设有收入门槛限制的有科罗拉多、哥伦比亚特区、伊利诺伊、缅因、马里兰、马萨诸塞、
  内华达、新罕布什尔、俄勒冈、罗德岛、弗吉尼亚、华盛顿；佛罗里达 2025 年《CHOICE 法案》方向相反
  （高收入者最长 4 年期限可执行）。
  [Katz Banks Kumin，2026 年 3 月更新](https://katzbanks.com/employment-law-blog/noncompete-agreements-whats-the-status-of-laws-restricting-them-nationwide-march-2026-update/)
- **联邦层面状态（截至 2026-07-06——本次研究之日）**：FTC 2024 年全美竞业禁止禁令在 *Ryan LLC v. FTC*
  案（德州北区联邦地区法院，2024 年 8 月）中被撤销；FTC 于 2025 年 9 月 5 日以 3-1 表决放弃上诉并
  接受撤销，该规则自 2026 年 2 月 12 日起从《联邦法规汇编》（CFR）中移除。**目前不存在联邦层面的
  竞业禁止禁令**——FTC 转而以个案方式依据第 5 条执法。
  [FTC 新闻稿](https://www.ftc.gov/news-events/news/press-releases/2025/09/federal-trade-commission-files-accede-vacatur-non-compete-clause-rule) ·
  [联邦公报](https://www.federalregister.gov/documents/2026/02/12/2026-02866/) ·
  [Duane Morris](https://www.duanemorris.com/alerts/ftc_abandons_appeals_decisions_striking_down_noncompete_rule_restrictive_covenants_remain_0925.html)
- **英国**：限制贸易原则要求合理性；对大多数职位，6 个月是外部上限，仅董事会/C 级高管可达 12 个月；
  法院已认定比离职股东自身角色范围更宽的股东协议竞业禁止无效。[DavidsonMorris](https://www.davidsonmorris.com/restraint-of-trade/)
- **面向加州公司的起草对策**：完全删去竞业禁止条款；依靠保密 + 商业秘密保护 + 知识产权转让 +
  窄化定制的员工/客户**禁止招揽**条款（限制的是关系，而非从事本业的能力——通过审查的几率高得多）。

---

## 3. 股权分配框架

### 3.1 反对反射性 50/50（或 N 等分）分配的理由

此处的实证基础是 **Hellmann & Wasserman《第一笔交易：新创企业创始人股权的分配》
（"The First Deal: The Division of Founder Equity in New Ventures"）**，NBER 工作论文 w16922——
数据集涵盖 **511 家私营企业中的 1,476 位创始人**。
[NBER 论文](https://www.nber.org/papers/w16922) · [NBER Digest 摘要](https://www.nber.org/digest/aug11/division-founder-equity-new-ventures)

- **约 33% 的创始团队完全均分股权。**
- 三项创始人特征显著*降低*均分可能性，并在分配不均时实质性提高创始人的股权溢价：**创意提出、
  既往创业经验、资本投入。**
- 均分与首轮融资时**较低的投前估值**相关——当分配是在**一天之内**谈妥时效应最强。
- **过度慷慨均分中较强创始人的代价估算**：约为公司总股权的 **10%**，或该创始人平均持股的
  **约 25%**——相当于放弃约 **$450,000 的净现值（NPV）**。

来自 Wasserman 更广泛的数据集（《创始人的困境》，Princeton/Kauffman，2012 年——
[HBS 条目](https://www.hbs.edu/faculty/Pages/item.aspx?num=42425)）：

- **73% 的创始团队在成立后一个月内分配股权**，往往并无真正的谈判。
  [noamwasserman.com](https://www.noamwasserman.com/category/equity-split/)
- **“快速握手”发现**：在**一天或更短时间**内谈妥均分（“快速均分”）的团队，在首轮机构融资时遭受
  可衡量的负面估值影响；花更长时间谈判均分（“慢速均分”）的团队则没有。问题在于决策的*速度/浅薄*，
  而非均分本身。
  [Inc. Magazine，归纳 Wasserman](https://www.inc.com/magazine/201406/leigh-buchanan/how-to-split-founder-equity.html)
- Wasserman 对创始人为何默认快速均分的解释：他们“过于乐观、缺乏做出其他选择的信息，或想回避
  争议性问题”——而仓促均分“表明创始人尚不具备进行艰难对话的商业成熟度”。
  [Inc. Magazine](https://www.inc.com/magazine/201406/leigh-buchanan/how-to-split-founder-equity.html)
- **默认均分的团队，其团队不满情绪几乎是对差异化分配团队的三倍。**
  [Inc. Magazine](https://www.inc.com/magazine/201406/leigh-buchanan/how-to-split-founder-equity.html)

> **重要框架说明**：以上是对*快速、无记录的*均分的批评，而非对均分本身的批评。Carta 较新的数据
> （见下文）显示，随着“从第一天起全职”的团队成为常态，均分正变得越来越普遍——这并非矛盾，而是
> 不同人群（真正对等贡献者之间的有意均等 vs. 掩盖真实不对称的反射性均等）。

**经典教学配对案例**（Wasserman 本人用于教学）：

- **Zipcar**——Robin Chase 在首次会面时向 Antje Danielson 提出 50/50 握手式分配，明确是为了避免
  谈判。Chase 全职担任 CEO；Danielson 保留外部工作。Chase 后来说：*“那次握手在接下来的一年半里
  造成了巨大的焦虑。”* Danielson 于 2001 年 1 月被挤出运营层，但保留其全部 50% 股份；到 Zipcar
  2011 年 IPO 时，Chase（运营创始人）已被稀释至约 3%。
  [Gunderson Dettmer](https://www.gunder.com/en/news-insights/insights/splitting-the-pie-how-savvy-founders-divide-ownership-and-navigate-other-founder-equity-decisions) ·
  [Equity Matrix](https://equitymatrix.io/blog/famous-cofounder-disputes)
- **Ockham Technologies**——三位联合创始人按出资比例分配 50/30/20，*附带条件成熟*：一年后仍须
  全职参与，否则丧失股份——这种动态/条件结构，是 Wasserman 拿来与 Zipcar 静态握手对比的正面案例。

### 3.2 应当驱动不均分配的因素

Wasserman 的三个统计显著驱动因素（来自 NBER 论文）：**创意提出、既往创业经验、资本投入。**
[NBER Digest](https://www.nber.org/digest/aug11/division-founder-equity-new-ventures)

| 因素 | 有记录的溢价 | 来源 |
|---|---|---|
| **创意提出** | 创意提出者相对联合创始人多获约 10–15 个百分点股权（如 IT 企业约 50% vs 约 35%；生命科学领域略低，约 10 个百分点） | [CBS News](https://www.cbsnews.com/news/what-the-idea-guy-is-worth-at-equity-split/) · [noamwasserman.com](https://www.noamwasserman.com/2008/05/01/idea-people-and-their-initial-roles-within-founding-teams/) |
| **既往创业/企业家经验** | 相对首次创业者多获约 7–9 个百分点 | [Inc. Magazine](https://www.inc.com/magazine/201406/leigh-buchanan/how-to-split-founder-equity.html) |
| **CEO 任命/角色关键性** | 部分二手综述中多获约 14–20 个百分点 *（中等置信度——未追溯到 Wasserman 的某项具体一手数据）* | [Inc. Magazine](https://www.inc.com/magazine/201406/leigh-buchanan/how-to-split-founder-equity.html) |
| **资本投入** | 确认为驱动不均分配和股份溢价的重要因素 | [NBER](https://www.nber.org/digest/aug11/division-founder-equity-new-ventures) |

实务框架（Melissa Kwan，创始人，关于拒绝 50/50）：权重考虑**财务贡献与个人责任、职责范围、以及
风险承受/牺牲**——列出建设业务所需的每一项职责，评估每位联合创始人承担这些任务的能力，再据此分配。
[melissakwan.com](https://www.melissakwan.com/p/cofounders-split)

**Gust 的联合创始人股权分配工具**——一个历史悠久的免费计算器——对后向因素（背景、技能、相关经验）
和前向因素（全职 vs 兼职投入、劳务股权、预期角色）打分，生成建议分配方案，其设计初衷就是迫使创始人
完成投资人期望他们早已进行过的“艰难对话”。
[Gust 工具](https://cofounders.gust.com/) ·
[Gust 博客](https://gust.com/blog/cofounder-equity-split-framework-objectively-divide-equity/)

**常见实务评分标准**（Capbase、ICanPitch 及类似计算器——厂商来源，仅代表共识而非验证数据）：创意、
领域专长、时间投入、资本、技术/执行能力、人脉、风险承受、既往经验、领导力/角色关键性——并以
**可替代性**作为乘数：贡献难以被替代的创始人，其股权显著高于易被替换的角色。
[Capbase 计算器](https://capbase.com/startup-equity-calculator/)

### 3.3 动态 vs 固定分配——Slicing Pie

**起源**：Mike Moyer，《Slicing Pie: Funding Your Company Without Funds》（2012 年）。
[Slicing Pie 手册（免费样章）](https://slicingpie.com/wp-content/uploads/2016/09/Slicing-Pie-Handbook-FREE-SAMPLE.pdf)

**核心原则**：*“一个人对公司回报所占的百分比，应当始终等于其为获得这些回报所承担风险的百分比。”*
所有权基于持续的风险性贡献动态浮动，仅在约定的触发事件时才固定（“烘焙”）下来。
[Equity Matrix，Slicing Pie 指南](https://equitymatrix.io/blog/slicing-pie-guide)

**“Grunt Fund”机制**——所有权百分比 = 个人**切片数** ÷ **总切片数**，贡献经由风险乘数换算为切片：

| 贡献类型 | 典型乘数 |
|---|---|
| 无薪/低于市价的劳务（按公平市价时薪计价） | 约 2 倍 |
| 投入的现金 | 2–4 倍（风险最高/流动性最差） |
| 设备/物资/知识产权 | 1–2 倍，按公平市价或重置成本 |
| 递延佣金/特许权使用费 | 约 2 倍 |
| 人脉/销售引荐 | 通常为成交价值的 5–10% |

[Equity Matrix，Slicing Pie 指南](https://equitymatrix.io/blog/slicing-pie-guide) ·
[Slicing Pie Grunt Fund 计算器](https://slicingpie.com/the-grunt-fund-calculator/)

**“Slicing Pie 时刻”（烘焙）**——将动态切片转化为固定股东名册（cap table）的触发点：
（1）外部机构投资（必需，因为投资人需要固定名册）；（2）所有贡献者均按全额市场薪酬领取工资时；
（3）贡献趋于稳定；或（4）重大事件（被收购、关键人员入职）。[Equity Matrix](https://equitymatrix.io/blog/slicing-pie-guide)

**优点**：无需在设立时*预测*未来贡献（固定分配中最难且最常出错的一项输入）；按公式/客观计算而非
谈判；自动处理转型和随时间不均的贡献。

**缺点**：没有固有的悬崖保护（早期离开者保留已赚取的切片——自身也有“死股权”风险）；需要严格的、
持续的记录，否则系统失效；一旦“烘焙”仍需纳入正当的法律/股东名册基础设施。

**适用时机**：极早期、自筹资金、营收前的团队，角色多变、无固定薪酬。**不适用**：即将募集机构资本的
团队，或角色稳定、明确的团队。**投资人反应**：机构投资人在有定价轮次前期望一份干净、固定、完全成熟
的股东名册——动态结构被视为必须在交割前转换为固定所有权的**交割条件**，通常转为经典的 4 年/1 年
悬崖结构。[Equity Matrix](https://equitymatrix.io/blog/what-investors-look-for-in-cap-tables)

### 3.4 经验法则

**YC 的立场（Michael Seibel）**——与 Wasserman 批评相对的标准观点，也是本技能使用者最常需要
协调的立场：

- *“股权应当均分或接近均分，因为所有工作都在前方。”*
  [YC Library](https://www.ycombinator.com/library/5x-how-to-split-equity-among-co-founders)
- 四点理由：（1）创造真实价值需要 **7–10 年**，第一年的差异不应驱动永久分配；（2）更多股权 =
  更多激励，而大多数初创企业会失败，所以激励比公平核算更重要；（3）投资人把分配视为 CEO 如何
  看待团队的信号；（4）初创企业靠执行而非创意——“创意俯拾皆是”。
- YC 明确**否定**下列不均分配理由：谁提出创意、谁更早开始、薪酬需求、年龄/经验差距、融资状况、
  平局表决权。
- YC 明确**否定**以绩效/指标挂钩的动态股权（如按代码行数成熟）——因为初创企业转型频繁，此类指标
  无法成立——并**完全否定**向兼职联合创始人授予股权。
  [YC Library，《应避免的联合创始人股权错误》](https://www.ycombinator.com/library/LP-co-founder-equity-mistakes-to-avoid)

**为技能协调 YC 与 Wasserman**：双方都同意真正重要的机制是**成熟而非均分核算**——YC 建议通过
4 年/1 年悬崖而非按比例不均的分配来解决“贡献不均”风险；Wasserman 的批评针对的是决策的速度/记录，
而非均分本身。实务综合：均分或接近均分的分配是站得住脚的——**前提是**（a）经过真正的谈判
（非一天之内敲定），（b）理由有书面记录，（c）背后有真实的成熟时间表。当贡献不对称既大且持久时
（资本、既往经验、唯一创意提出、兼职 vs 全职），不均分配即为合理。

**实务流程经验法则**：以书面形式记录分配理由（Techstars、Gust 均如此建议）；将 1 年悬崖作为内置的
复查与锁定检查点，赶在分配在经济上难以解除之前完成。[Techstars](https://www.techstars.com/blog/advice/how-to-split-co-founder-equity-the-right-way)

**投资人危险信号**：拒绝谈判或公开讨论股权的创始人，预示未来冲突——投资人期望看到艰难对话确实
发生过，而不是被回避。[Gust FAQ](https://gust.com/launch/faq/articles/when-and-why-should-i-determine-an-initial-equity-split-with-my-founding-team)

> **已标注，未采用**：一则流传于股权计算器营销博客上的说法——“First Round Capital 2024 年创业
> 状态报告：67% 的种子投资人将超过 55/45 的分配视为黄旗”——无法追溯到 First Round 实际发布的报告。
> 未经独立核实，不得作为事实引用。

### 3.5 创始人股权纠纷数据

**“65%”数字及其真实谱系**：广泛归因于 Wasserman——“65% 的高潜力初创企业因联合创始人之间的冲突而
失败。”再向前追溯，此说法部分源于 **Gorman & Sahlman（1989）**——他们调查了 49 位 VC，涉及 96 家
风险投资组合公司，其中 61 位 VC 将团队/创始人问题列为前三大失败原因之一（61/96 ≈ 63.5%，四舍五入为
约 65%，后被并入 Wasserman 更大的数据集）。65% 这个数字可以使用，但应标注其谱系，而非作为干净的
现代实证结果呈现。
[Entrepreneur.com](https://www.entrepreneur.com/leadership/harvard-business-school-professor-says-65-of-startups-fail/370367) ·
[CNN Money](https://money.cnn.com/2014/02/24/smallbusiness/startups-entrepreneur-cofounder/)

**其他源自 Wasserman 的流失统计**（对其 HBS 工作论文的二手综述——中等置信度）：

- 在 **73% 的创始人 CEO 更替**中，创始人是被解职而非自愿卸任。
- **52% 的创始人**在公司第三轮融资时已不再是 CEO。
- 创始团队内部既有的友谊/亲属关系会使离职可能性增加约 **30%**（每增加一段关系）——团队往往*因为*
  这层关系而回避艰难的股权对话，约 6 个月“蜜月期”后开始失稳。
  [onstartups.com，综述 Wasserman](https://www.onstartups.com/tabid/3339/bid/80224/Avoiding-Founder-Failure-26-Quick-Tips-and-Real-Data.aspx)

**Carta 股东名册数据**（45,000+ 份股东名册）：

- 按团队规模的均分占比，2015 年 → 2024/2025 年：**两人团队 31.5% → 45.9%**；**三人团队 12.1% →
  约 27%**；**四人团队 10.8% → 16.7%。**
- 在不均分配中，中位差距从约 **60/40（2015 年）** 收窄至约 **51/49（2024 年）**。
- 创始人持股按阶段侵蚀（中位数，完全稀释口径）：**种子轮约 56% → A 轮约 36% → B 轮约
  21.8%–27.3% → C 轮**，此时员工期权池中位数（约 16.8%）可能超过创始人持股中位数（约 16.1%）——
  这解释了为何初始分配单独看不如整体股东名册轨迹（成熟 + 期权池规模 + 稀释）重要。
- 单人创始人：占 **2025 年 Carta 跟踪初创企业的 36%**（2024 年为 31%），十年间近乎翻倍。
- Carta 自身的表述：*“大多数股权纠纷之所以发生，是因为联合创始人从未明确讨论过每个人实际贡献了
  什么。”*
  [Carta，2024 年创始人股权分配趋势](https://carta.com/data/founder-equity-split-trends-2024/) ·
  [Carta 2026 年创始人持股报告](https://carta.com/data/founder-ownership-2026/)

**有记录的纠纷案例研究**（可作为起草技能中的示例）：

| 公司 | 发生了什么 | 结果 | 来源 |
|---|---|---|---|
| **Zipcar** | Chase/Danielson 50/50 握手，实际贡献不均 | Danielson 被挤出运营（2001 年），保留全部股份；Chase 到 2011 年 IPO 时被稀释至约 3% | [Equity Matrix](https://equitymatrix.io/blog/famous-cofounder-disputes) |
| **Facebook（Eduardo Saverin）** | 约 30% 股份经其未同意的 2005 年股份重新发行被稀释至约 0.03% | 2005 年起诉，2009 年和解；追回约 4–5% 股份，IPO 时价值约 $2B | [Equity Matrix](https://equitymatrix.io/blog/famous-cofounder-disputes) |
| **Snapchat（Reggie Brown）** | 构思阅后即焚照片概念，2011 年 8 月被逐出且未获任何股权 | 2013 年起诉；以 **$157.5M** 和解（2014 年）；和解未承认其为“联合创始人” | [TechCrunch](https://techcrunch.com/2017/02/02/snapchat-reggie-brown/) · [Forbes](https://www.forbes.com/sites/kathleenchaykowski/2017/02/03/snap-ipo-filing-reveals-ousted-cofounder-received-157-5-million-in-settlement/) |
| **Twitter（Noah Glass）** | 力推核心概念并命名；被 Jack Dorsey 排挤 | 仅象征性股权，无和解——一场从未正式了结的纠纷 | [Equity Matrix](https://equitymatrix.io/blog/famous-cofounder-disputes) |
| **Tinder（Whitney Wolfe Herd）** | “联合创始人”头衔被剥夺；另有一项与联合创始人关系相关的骚扰索赔 | 骚扰索赔以 **$1M+** 和解；系头衔/署名之争而非纯粹股权之争 | [CNN Business](https://www.cnn.com/2019/12/13/tech/whitney-wolfe-herd-bumble-risk-takers) · [Inc.](https://www.inc.com/business-insider/ousted-tinder-co-founder-makes-1-million-in-lawsuit-settlement.html) |
| **ConnectU / Facebook（Winklevoss 兄弟）** | 无明确知识产权转让；就源代码被指控口头合同违约 | 2008 年 2 月和解，据报道约 $65M | 背景见 [Wikipedia，Cameron Winklevoss](https://en.wikipedia.org/wiki/Cameron_Winklevoss) |

---

## 4. 成熟（Vesting）深度解析

### 4.1 成熟为何保护联合创始人彼此

核心问题：“**搭便车（free rider）**”问题——没有成熟机制，短期后离开的创始人将永远保留其全部股份，
而留下的创始人要承担所有剩余工作。

- **YC（Michael Seibel）**：对所有创始人一律适用 4 年成熟、1 年悬崖，无例外。
  [YC Library](https://www.ycombinator.com/library/5x-how-to-split-equity-among-co-founders)
- **Cooley GO**：*“当创始人在公司存续早期决定离开或被要求离开时，成熟限制保护其他创始人免受
  本会存在的‘搭便车’问题之害。”* [Cooley GO](https://www.cooleygo.com/founder-basics-founders-stock/)
- **WilmerHale Launch** 将成熟定位为**承诺装置**：没有它，联合创始人可以在早期离开，“带走其股票，
  而公司无法回购，留给你一张更复杂的股东名册。”
  [WilmerHale Launch](https://launch.wilmerhale.com/research/blog/five-things-about-founder-stock-vesting)
- 二阶效应：混乱的未成熟创始人分配 → 积怨 → 离职 → 股东名册上的**死股权**（见第 6.4 节）→ 招聘
  难题（没有股权留给关键岗位）→ 融资难题（VC 不愿投资持有大额股份却毫无贡献的股东的名册）。
- **关键细微处**：创始人在发行时已合法拥有其股份（这正是“反向”成熟之名的由来）——YC 仍建议成熟，
  正因为没有丧失机制的裸所有权无法保护团队免受早期离职之害。YC 明确警告不要用复杂的绩效挂钩
  earn-out 替代悬崖/成熟结构——如果创始人关系不合，解决办法是在悬崖期前终止关系，而非定制绩效条件。
  [YC Library，《应避免的联合创始人股权错误》](https://www.ycombinator.com/library/LP-co-founder-equity-mistakes-to-avoid)

### 4.2 标准结构：4 年、1 年悬崖、此后按月

| 期间 | 成熟内容 |
|---|---|
| 第 0–12 个月（悬崖期） | **0%。** 无任何成熟。第 11 个月离开 → 一无所有地离开。 |
| 一周年纪念日当天 | **25%** 一次性整笔成熟。 |
| 第 13–48 个月 | 剩余 **75%** 按月成熟——**每月约 1/48（约 2.08%）的原始授予量**——至第 48 个月达 100%。 |

- **Carta**：*“你 1/4 的股份在一年后成熟……悬崖期后，剩余已授予股份的 1/36（即原始授予量的 1/48）
  每月成熟，直至四年成熟期结束。”*
  [Carta，《成熟机制详解》](https://carta.com/learn/equity/stock-options/vesting/)
- **WilmerHale Launch**：*“四年成熟时间表，含一年成熟悬崖……其余三年按月成熟。”*
  [WilmerHale Launch](https://launch.wilmerhale.com/research/blog/five-things-about-founder-stock-vesting)
- **Cooley GO**：*“股份在四年内按月或按季成熟；若创始人在股份完全成熟前离开公司，公司有权回购
  未成熟股份。”* [Cooley GO](https://www.cooleygo.com/founder-basics-founders-stock/)

**为何这一具体结构成为标准**：Carta——*“它成为标准做法，是因为早期风险投资人曾被融资六个月后
分手、带着几乎没做什么就赚到的大额股权离开的创始人坑过。悬崖保护公司及其余团队免受早期离开的
联合创始人之害……这也是 Y Combinator 自 2000 年代中期以来几乎向其资助的每家公司建议该结构的原因。”*
[Carta，《成熟机制详解》](https://carta.com/learn/equity/stock-options/vesting/)

**起草陷阱**：悬崖边缘的不连续性本身就会让创始人措手不及——两个月的差异（第 11 个月 vs 第 13 个月）
分隔 0% 与 25%。第二重陷阱：完全跳过成熟（“我们都全力以赴”），创始人第 3 个月退出时仍持全部股份，
无任何救济手段——投资人会强制一个追溯性的（往往价格更差的）修正方案。第三重：悬崖期后按季度 vs
按月成熟——按季度意味着距季末仅差几天的创始人退出，将丧失整个季度的股份。

### 4.3 反向成熟 / 已发行股份上的成熟

创始人在**设立时一次性获得其 100% 的股份**（出于 83(b) 税务原因——见第 4.4 节），而非随时间分批
发放。因此成熟不是扣押股票凭证的机制，而是**创始人的服务提前结束时，公司以原购买价格回购（重新取得）
未成熟部分的权利**。故称“反向”成熟——普通成熟随时间授予股份；反向成熟在早期离职时收回已发行的股份。

- **Cooley GO**：*“与持续服务挂钩的成熟股票有时被称为‘反向成熟’，因为它赋予公司在服务终止时
  重新取得未成熟股票的权利。”* 回购价格*“以成本价或当时公平市场价值的较低者为准”*——由于原始
  购买价格为名义价格，这几乎总是等于“按成本价”。
  [Cooley GO](https://www.cooleygo.com/founder-basics-founders-stock/) ·
  [Cooley GO，《建立股权文化》](https://www.cooleygo.com/establishing-ownership-culture-stock-vs-options/)
- **落地文件**：**限制性股票购买协议（RSPA）**。*“创始人应当与公司签订书面限制性股票购买协议，
  按购买时点的股份价格计价。限制性股票购买协议应清晰描述成熟时间表和加速条款。”*
  [Cooley GO](https://www.cooleygo.com/founder-basics-founders-stock/) ·
  [Orrick Start-Up Forms](https://www.orrick.com/en/Total-Access/Tool-Kit/Start-Up-Forms/Founders-Stock-Purchase)

**起草要点**：成熟/回购权存在于 RSPA 本身，而非控制股票凭证发放的单独“成熟协议”。股票凭证自
第一天即存在并被持有（启动 83(b) 计时）；只有公司按批次的合同回购选择权创造挽留效果。

### 4.4 83(b) 选择书

**它是什么**：IRC §83(b) 允许承受重大丧失风险财产（此处指未成熟限制性股票）的受让人选择**当下**
按授予时的价值纳税，而非在每一个未来成熟日纳税。适用法规：[26 CFR §1.83-2](https://www.law.cornell.edu/cfr/text/26/1.83-2)。

**为何持反向成熟股票的创始人必须申报**：若无此选择书，IRS 将每一批成熟视为新的应税事件——
按公平市场价值与实际支付价格的差额征收普通所得税，**在每个成熟日计算**。设立时的公平市场价值为
名义价值，但到后期成熟日可能大幅上升；申报 83(b) 可将潜在的、大额且重复的普通所得税义务转化为
授予时的近似为零的一次性税负。

**30 天期限——严格，无例外**：

- 财政部法规 §1.83-2：*“选择书应不迟于财产转让之日起 30 日内提交……并可在转让日前提交。”*
- 计时从**股票发行/购买之日**起算——而非董事会批准日或任何更早的“原则性协议”。
- 在窗口期内**邮戳**即视为及时（以挂号信邮戳日期为准）。
- [Clerky](https://help.clerky.com/article/2828-how-do-i-make-an-83b-election) ·
  [Stripe Atlas 文档](https://docs.stripe.com/atlas/83b-election)

**具体后果示例**（Stripe Atlas）：以 $0.0001/股购买 200,000 股 = 总成本 $20。一半在第 1 年按
$0.50 公平市场价值成熟；另一半在第 2 年按 $1.00 成熟；第 3 年以 $2.00/股出售（总计 $400,000）。

- **申报 83(b) 后**：两个成熟日均无税负——出售时仅对 $399,980 缴纳资本利得税。
- **未申报 83(b)**：第 1 年对约 $49,990、第 2 年对约 $99,990 缴纳普通所得税——在创始人卖出
  任何一股或见到一分钱流动性之前——外加出售时的资本利得税。
  [Stripe Atlas](https://docs.stripe.com/atlas/83b-election) ·
  [Carta](https://carta.com/learn/equity/stock-options/taxes/83b-election/) ·
  [Cooley GO](https://www.cooleygo.com/what-is-a-section-83b-election/)

**IRS 标准化表格**：**表格 15620**（“第 83(b) 条选择书”）于 2024 年 11 月发布，为可选的标准化表格；
2025 年中期开通了在线/电子申报选项。
[IRS 表格 15620（PDF）](https://www.irs.gov/pub/irs-pdf/f15620.pdf) ·
[Goodwin，电子申报](https://www.goodwinlaw.com/en/insights/publications/2025/07/alerts-practices-erisa-online-filing-of-section-83b-elections)

> **技能应编码的更正**：取消将 §83(b) 选择书副本附于纳税人所得税申报表的要求，常被误记为
> 2018 年《减税与就业法案》（TCJA）的产物。它实际早于 TCJA——**财政部决定 9779（Treasury
> Decision 9779），2016 年定稿**，适用于 **2016 年 1 月 1 日或之后**的转让。**向 IRS 申报的
> 30 天期限未受影响**，仍然绝对严格；执业者仍建议保留原始申报凭证。
> [Wilson Sonsini](https://www.wsgr.com/en/insights/final-regulations-issued-under-internal-revenue-code-section-83-eliminate-taxpayer-requirement-to-file-section-83-b-election-with-income-tax-return.html) ·
> [The Tax Adviser](https://www.thetaxadviser.com/news/2016/jul/regulations-eliminate-sec-83b-filing-statement-requirement-201614887/)

**QSBS 交互**：申报 83(b) 将合格小型企业股票（QSBS）的持有期计时起点从各成熟日提前至购买日——
早期申报可使技术上在 QSBS 窗口期内成熟的股份仍符合资格。[Carta](https://carta.com/learn/equity/stock-options/taxes/83b-election/)

**不可撤销性**：选择书一经申报不可撤销。若创始人已按授予时价值纳税，后因提前离职丧失未成熟股份，
**已缴税款不予退还**——这是将决策交由 CPA/税务律师的真正理由（见第 9.3 节）。

### 4.5 创始人友好的成熟变体

- **设立前工作的成熟积分**：在正式设立前已全职工作的创始人，通常协商追溯成熟积分，使悬崖/时间表
  不必归零。示例：可证明的 12 个月设立前全职工作 → 已发行股份的 25% 自始完全成熟，剩余 75% 在
  随后 36 个月内成熟。机构投资人往往不愿接受超过约一年的倒签，因此任何声称的积分都应现实、有据——
  尽职调查中会被审查。
- **更短悬崖/更快时间表**：偶尔在机构资金进入前谈成；一旦 VC 介入，4 年/1 年悬崖标准往往作为融资
  条件重新确立。
- **YC 的明确警告**：反对以里程碑/绩效挂钩成熟替代时间型成熟——保持各创始人结构统一，表现不佳通过
  真实的终止决策处理，而非在成熟上叠加定制条件。
  [YC Library](https://www.ycombinator.com/library/LP-co-founder-equity-mistakes-to-avoid)

### 4.6 加速触发

**单触发**：仅凭**一个**事件——控制权变更——未成熟股份即 100%（或固定比例）自动成熟。**为何收购方/
VC 抵制**：WilmerHale Launch——存在单触发时，收购方可能**降低收购价格**，因为完全加速消除了收购方
所依赖的挽留杠杆；最坏情况下可能使交易无法进行。
[WilmerHale Launch](https://launch.wilmerhale.com/research/blog/five-things-about-founder-stock-vesting)

**双触发**：只有**同时满足**（1）发生控制权变更，**且**（2）在交割后规定窗口内（**通常为 12 个月**），
创始人被无因解雇或因正当理由辞职，未成熟股份才加速。市场示例语言（WSGR）：*“若在控制权变更后
12 个月内，创始人被无因解雇或因正当理由辞职，100% 未成熟股份应立即成熟。”*
[Wilson Sonsini](https://www.wsgr.com/en/insights/its-not-about-how-much-stock-you-have-its-about-how-much-copper-wire-you-can-get-out-of-the-building-with-founder-exits-part-2.html)

**为何双触发是市场标准**：Cooley GO 将其表述为*“一个皆大欢喜的折中方案”*——收购方希望交割后人员
留下，所以单触发“通常不合理”；但创始人仍需保护，避免刚交割就被解雇、导致未成熟股权永远无法兑现。
[Cooley GO](https://www.cooleygo.com/what-are-single-and-double-trigger-acceleration-and-how-do-they-work/) ·
[Orrick](https://www.orrick.com/en/Insights/2026/04/Single-and-Double-Trigger-Vesting-Acceleration-What-founders-and-employees-should-know)

**起草提示**：双触发的保护价值完全取决于“有因（Cause）”和“正当理由（Good Reason）”如何定义——
窄化的“正当理由”或宽泛的“有因”定义可以掏空该机制，尽管它名义上存在。Clerky 标准创始人文件包
默认**100% 双触发加速**。
[Clerky](https://help.clerky.com/article/1736-what-are-customary-stock-vesting-terms-for-startup-founders)

---

## 5. 知识产权转让

### 5.1 现在时态转让表述——“特此转让”规则

知识产权转让条款（在创始人协议及保密信息与发明转让协议/CIIAA/PIIA 中）必须使用**现在时态、
自动生效的表述**——*“本人特此转让（I hereby assign）”*——而非将来时态的*“本人将转让（I will
assign）”*或*“本人同意转让（I agree to assign）”*。

**法理基础**：*Board of Trustees of the Leland Stanford Jr. Univ. v. Roche Molecular Systems*，
563 U.S. 776（2011 年）。斯坦福大学研究人员的大学协议写明其*“同意转让”*——被认定为未来转让的
承诺，属待履行合同（executory contract）。其另签的 Cetus/Roche 访客协议写明*“将转让并特此转让”*——
被认定为**现在时转让**，权利即时归属，无需进一步行为。由于 Cetus/Roche 的现在时转让早于斯坦福
自身的后续转让，**Roche——而非斯坦福——赢得了专利权**，尽管斯坦福是发明人的所属机构。
[Patent Docs](https://patentdocs.org/2011/06/06/board-of-trustees-of-the-leland-stanford-junior-university-v-roche-molecular-systems-inc-2011/) ·
[Taft Law](https://www.taftlaw.com/news-events/law-bulletins/stanford-university-v-roche-molecular-131-s-ct-2188-2011/)

**为何这是起草陷阱**：将来时态表述意味着所有权不会自动转移；若创始人日后在别处签署*冲突的现在时态*
转让（前雇主、联合创始人的另一家企业），第三方的现在时转让可以完全胜出——斯坦福的遭遇正是如此。
第二重创始人特有陷阱：仅依赖标准设立后雇佣协议的知识产权条款——该条款通常只涵盖“雇佣期间”创造的
知识产权——结构性遗漏了公司价值往往真正依托的设立前 MVP/路演材料/代码库。
[Orrick](https://www.orrick.com/en/tech-studio/resources/glossary/Inventions-Assignment-Agreement) ·
[Crowley Law](https://www.crowleylawllc.com/founder-ip-assignment-pre-incorporation/)

### 5.2 设立前知识产权

创始人往往在公司存在**之前**就编写代码、构建原型或开发核心创意。若无明确涵盖该期间的转让协议，
这些知识产权可能始终是创始人的个人财产，而非公司财产。创始人协议/知识产权转让协议应明确涵盖
“设立前创造的知识产权”，并在实体成立时转让给实体——这不是可以延后的清理工作，而是任何未来融资
或退出的必经步骤。
[Orrick](https://www.orrick.com/en/tech-studio/resources/glossary/Inventions-Assignment-Agreement) ·
[Gunderson Dettmer](https://catalyze.gunder.com/en/knowledge-articles/resource/formation)（专门针对
该缺口推荐**技术转让协议**）

### 5.3 精神权利

精神权利（署名权、作品完整权）通常在知识产权转让协议中**被放弃**。这在美国以外尤为重要：在英国/
欧盟/大陆法域，精神权利在某些情形下不可放弃；而在美国，精神权利范围狭窄（如 VARA，仅限于特定
视觉艺术）且通常可放弃。起草启示：纳入明确的精神权利放弃条款，并在放弃权受限的非美法域标注需当地
律师审查。

### 5.4 在先发明除外

标准做法是在知识产权转让协议后附**“在先发明”清单/附件**，由每位创始人披露其拥有且**不**转让给
公司的既有知识产权/发明——保护创始人免于无意中转让无关的个人项目。若清单中的在先发明最终被并入
产品，公司通常获得对其的**非独占许可**，而非完全所有权。

### 5.5 灾难情形：尽职调查中浮现未转让的知识产权

融资或并购尽职调查期间暴露的知识产权转让缺口，是有据可查的交易杀手或交易延误模式：投资人律师
发现离职联合创始人或创始人前雇主对核心知识产权主张权利，被迫进行代价高昂的追溯转让谈判——有时
是手握筹码的前创始人索要报酬才肯签字。**ConnectU v. Facebook** 纠纷（上文第 3.5 节及下文第 7 节）
即经典示例：未订立明确的知识产权转让协议、就源代码被指口头合同违约，最终以据报道约 $65M 和解。
背景见 [Wikipedia](https://en.wikipedia.org/wiki/Cameron_Winklevoss)；总体框架见
[Sandberg Phoenix](https://sandbergphoenix.com/why-ip-assignment-agreements-are-essential-for-startup-founders/) ·
[WilmerHale Launch](https://launch.wilmerhale.com/explore/formation/founders/who-owns-your-ip)

---

## 6. 离任/退出机制

### 6.1 好离任者 vs 坏离任者

| | 好离任者（Good Leaver） | 坏离任者（Bad Leaver） |
|---|---|---|
| **典型触发** | 死亡、伤残/丧失能力、冗余裁员、有正当理由辞职、无因解雇 | 无正当理由自愿辞职；有因解雇（欺诈、严重不当行为、违约） |
| **未成熟股份** | 无论是否离任类别均按成本价丧失/回购（与坏离任者相同——成熟状态不取决于离任类别） | 按成本价丧失/回购 |
| **已成熟股份** | 通常保留，或按公平市场价值/约定公式回购 | 在更严厉的（通常为英国）起草中，可被强制以**零对价**或大幅折价（如面值）转让；在美国实践中，更多通过加速而非收回已成熟股份来表达 |

**英国术语（一手来源：SeedLegals）**：“好离任者” = 死亡、意外或伤残（非自愿离任）——通常保留
已成熟股份，未成熟股份按公允价值转让。“坏离任者” = 因欺诈、重大过失或严重不当行为被解雇——可能
被强制以**零对价**转让未成熟股份。这些术语存在于公司章程（Articles of Association）的“强制转让”
部分。
[SeedLegals](https://help.seedlegals.com/en/5440634-my-co-founder-is-leaving-what-do-i-do-with-their-shares) ·
[SeedLegals，创始人成熟](https://seedlegals.com/resources/startup-founder-vesting/) ·
[Bird & Bird](https://www.twobirds.com/en/insights/2025/leaver-provisions-the-terms-that-founders-fear-the-most)

**美国实践（Orrick Stripe Atlas 法律指南）**：无因/正当理由解雇、死亡或伤残时，通常适用 **6–12 个月**
的成熟加速——*“按大多数协议的约定，创始人自愿辞职或因‘有因’被解雇时没有加速。”*
[Orrick 法律指南，第 22 页](https://stripe.com/files/atlas/orrick-legal-guide.pdf)

**起草陷阱**：“有因（Cause）”和“正当理由（Good Reason）”未定义——Ledgy：*“劳动法对如何处理
离任条款没有具体指引，”* 因此未定义的分类在信任最低之时变成事后之争。
[Ledgy](https://ledgy.com/blog/good-leaver-bad-leaver-clauses)

**第二重更尖锐的陷阱**：单人创始人公司初期往往**完全没有成熟安排**——Orrick：*“对于只有一位创始人的
公司，创始人股票初期通常不受成熟约束，尽管投资人日后可能要求股份受成熟约束”*——这是有据可查的
股东名册毒丸，若第一天不处理，VC 会强制追溯性（往往价格更差的）修正。
[Orrick 法律指南，第 19 页](https://stripe.com/files/atlas/orrick-legal-guide.pdf)

### 6.2 未成熟股份丧失

重申反向成熟机制（第 4.3 节）：离职时，未成熟股份由公司按原始发行价格（近零）丧失/回购，
**与好坏离任者身份无关**——在美国多数风投支持的结构中，好坏离任者区分主要影响**已成熟**股份，
而非未成熟股份。

### 6.3 已成熟股份的回购

常见机制：公司或联合创始人对离任创始人已成熟股份的**优先购买权 + 回购选择权**。实务中使用的估值
方法：经独立评估/409A 估值的公平市场价值、预先约定的公式、账面价值或上轮价格。付款条件常设计为
**分期付款或期票**而非一次性支付，因为现金流紧张的初创企业往往无法立即以现金支付公平市场价值。

### 6.4 “死股权”问题

**死股权（Dead equity）**（或“死重股权”）：已离任创始人保留一大块已成熟股权且再无任何贡献。
后果：稀释留任创始人/员工；使未来期权池补充复杂化；对新投资人的股东名册造成摩擦——他们不愿为
不贡献的股东出资；在需要离任创始人股份参与超级多数表决时造成治理/同意难题。

**有记录的案例研究——英国 SaaS 初创企业**：一家三人创始的初创企业，一位创始人在 6 个月后离开，
**当时没有任何成熟时间表或离任条款**。该创始人尽管再无任何贡献，仍保留了公司 33% 的股份。当
初创企业接触种子投资人时，股东名册成为“严重关切”；投资人要求清理，留任创始人不得不支付现金和解
并重组股东名册，融资因此推迟数月。
[经二手法律博客摘要引用](https://vklegalassociates.com/founder-departures-and-equity-reassignment-in-uk-startups/) ——
*（仅作示例，未经具名一手来源独立佐证）*。

**反面案例——Skype（2011 年）**：微软以 $8.5B 收购 Skype 时，部分员工发现其股权价值为 **$0**——
因为细则中埋藏的回购/收回条款。这说明纸上存在但股权持有人未充分理解的离任/收回条款，本身也会
制造纠纷风险。
[Stock Option Counsel, P.C.](https://www.stockoptioncounsel.com/blog/standards-ownership-canthecomanytakebackmyvestedshares)

一份起草良好的离任/回购条款——清晰的好/坏离任者定义、明确的估值机制、公司实际负担得起的付款结构——
正是防止两种失败模式的关键：股权滞留于不贡献者手中，以及从从未理解所签风险的创始人处收回股权。

---

## 7. 创始人常见纠纷与错误

反复出现、有据可查的失败模式，每一种都追溯到具体原因及（在有资料处）具名案例研究：

| 错误 | 失败模式 | 标准修正 |
|---|---|---|
| **无成熟协议** | 创始人数月后离开，永久保留大额股份的 100%（“搭便车”）；股东名册无法获得投资 | 对所有创始人适用 4 年成熟/1 年悬崖（第 4 节） |
| **握手/仅口头股权** | 就承诺内容“他说/她说”之争；无法对抗法院或投资人律师 | 书面 RSPA + 有记录的分配理由 |
| **无知识产权转让** | 公司实际上不拥有核心技术；在尽职调查中灾难性暴露（第 5.5 节） | 设立时即签署现在时态 CIIAA/PIIA，涵盖设立前工作 |
| **无离任/退出条款** | 离任创始人的股权成为“死股权”（第 6.4 节）；融资前需清理股东名册 | 好/坏离任者定义 + 回购机制 |
| **无决策/僵局机制** | 50/50 团队在重大决策上无裁决者陷入僵局；有时对公司致命 | 调解优先条款、中立裁决者、或猎枪/俄罗斯轮盘买卖条款（第 2 节，条款 8） |
| **完全无书面创始人协议** | 投资人以“干净、有记录”的创始人条款作为融资门槛；纠纷无治理框架 | 最低限度：任何机构资金进入前具备 RSPA、CIIA 及有记录的股权/成熟理由 |

**这些模式背后的数据**：

- **Wasserman（HBR，《创始人的困境》，2008 年 2 月）**，分析 1990 年代末/2000 年代初的 212 家
  初创企业：到第三年，**50% 的创始人已不再是 CEO**；到第四年，仅 40% 留任；**不到 25%** 领导了
  公司最终的 IPO。
  [HBR](https://hbr.org/2008/02/the-founders-dilemma)（付费墙；摘要见
  [Business of Software](https://businessofsoftware.org/talks/understanding-founders-dilemmas/)）
- **65% 联合创始人冲突失败数字**——完整谱系见第 3.5 节（Gorman & Sahlman 1989 → Wasserman 更大
  数据集）。[Entrepreneur.com](https://www.entrepreneur.com/leadership/harvard-business-school-professor-says-65-of-startups-fail/370367)
- **CB Insights“初创企业失败首要原因”**——请注意流传的**有两个不同版本**，而非单一数字：经典
  约 20 条原因的报告将**“团队不合适”列为 23%**（低于“无市场需求”42% 和“资金耗尽”29%）；2024 年
  更新的版本（431 家 2023 年以来获 VC 支持而关闭的企业）则首推“资本耗尽”（70%）、
  “产品市场契合度差”（43%），并未将团队/联合创始人问题作为单独类别突出列出。两个版本都要引用并
  注明日期——在新版本中，团队功能失调往往是“资金耗尽”或“产品市场契合度差”死亡背后的根本原因，
  只是并非总能单独拆出。[CB Insights](https://www.cbinsights.com/research/report/startup-failure-reasons-top/)

**具名公开纠纷**（Zipcar、Facebook/Saverin、Snapchat/Brown、Twitter/Glass、Tinder/Wolfe Herd、
ConnectU/Facebook 见上文第 3.5 节表格——此处交叉引用而非重复）。

**僵局专项案例研究——Housing.com**：被指缺乏任何争议解决机制，是 12 位原始创始人中 9 位于
2016 年前退出的促成因素之一。
[iPleaders](https://blog.ipleaders.in/co-founders-agreement-disputes-suggestions/)

> **已标注，未采用**：归因于“First Round Capital”的联合创始人分手率二手博客统计（如“10% 的联合
> 创始人团队一年内分道扬镳”“20% 的分手在 18 个月内导致公司关门”）无法追溯到任何一份可核实的
> First Round Capital 一手出版物。请改用 First Round 实际可核实的内容——
> [First Round Review，《如何解决你受够了的那场联合创始人争吵》](https://review.firstround.com/how-to-fix-the-co-founder-fights-youre-sick-of-having-lessons-from-couples-therapist-esther-perel/)
> ——并淡化或删除具体百分比。

---

## 8. 实体与法域差异

### 8.1 特拉华州 C 型公司（美国风投支持默认结构）

之所以是标准默认，是因为投资人熟悉、判例法成熟，以及特拉华州衡平法院（Delaware Court of Chancery）
专业的公司法专长。成熟通过 **DGCL 下的 RSPA** 实现——创始人按名义价格（如 $0.0001/股）购买股份，
公司对未成熟股份享有回购权。标准设立文件包（Cooley GO、Clerky）将注册证书、章程细则、董事会/设立人
同意书、RSPA、83(b) 表格和 CIIAA 打包为一套连贯、为投资人所认可的组合。
[Cooley GO 文件，特拉华设立文件包](https://www.cooleygo.com/documents/incorporation-package-delaware/) ·
[Clerky，标准成熟条款](https://help.clerky.com/article/1746-what-kind-of-vesting-do-the-standard-post-incorporation-setup-forms-have)

### 8.2 LLC / 经营协议

- **结构性差异**：LLC 所有人持有**“成员权益（membership interests）”**或**“单元（units）”**，而非
  股份。通常**不存在独立的创始人协议**——经营协议通常*就是*治理文件。
  [Carta，LLC 成员权益](https://carta.com/learn/startups/compensation/equity-incentive-plans/membership-interests/)
- **成熟可行但需定制**：*“虽然可以对 LLC 成员的单元施加成熟，但这会带来显著增加的复杂性……LLC 的
  所有成熟安排都需要定制……不同于”* 公司的*“现成标准协议”。*
  [Orrick](https://www.orrick.com/en/tech-studio/resources/faq/do-an-llcs-membership-units-vest-like-the-shares-of-a-corporation)
- **利润权益（profits interests）vs 资本权益（capital interests）**：LLC 中股票授予的对等物是
  “利润权益”，通常需要在授予前将资本账户“记账上调（booking up）”，并将获得该权益的 W-2 员工转为
  税务合伙人（K-1），不再符合 W-2 资格。
  [Carta，利润权益](https://carta.com/learn/startups/compensation/equity-incentive-plans/profits-interest/)
- **为何 VC 回避 LLC**：穿透课税给资助 VC 大部分资本基础的免税 LP（养老基金、捐赠基金）造成
  UBTI 问题；转让 LLC 的部分所有权在法律上比转让股票更复杂；C 型公司提供标准化、成熟的股份类别
  基础设施（普通股、种子轮 Series Seed、A 轮优先股）。*“VC 在 99% 的情况下强烈倾向于投资 C 型公司。”*
  [Lighter Capital](https://www.lightercapital.com/blog/why-vcs-only-invest-in-c-corporations)
- **LLC 转 C 型公司的“翻转”**：标准做法是在有定价 VC 轮前转换。注意 Orrick 2026 年一个相反的
  细节：部分创始人刻意先以 LLC 起步、日后转换，以扩大最终的 QSBS 收益排除利益，但*“在从 LLC
  转换为公司之前积累的任何‘内含’收益都不符合 QSBS 排除资格。”*
  [Orrick，2026 年](https://www.orrick.com/en/Insights/2026/01/Risk-and-Reward-How-Starting-Your-Business-as-an-LLC-Could-Impact-QSBS-Tax-Savings)

### 8.3 英国有限公司（private limited company）

- **文件结构**：**公司章程（Articles of Association）**（有约束力的“强制转让”机制、股份定义、成熟
  时间表变量）加一份单独的**股东协议**，用于创始人希望保密/灵活处理的事项。
  [SeedLegals](https://help.seedlegals.com/en/5440634-my-co-founder-is-leaving-what-do-i-do-with-their-shares)
- **好离任者/坏离任者术语是英国标准用法**（第 6.1 节）——与美国框架不同但类似。
- **成熟由投资人驱动，而非自设立第一天起内置于标准设立文件**：*“所有成熟的投资者都会在你们融资时
  要求某种形式的成熟时间表”*——意味着英国创始人更常在初期没有成熟安排，而美国自设立起即默认为
  标准。[SeedLegals，创始人成熟](https://seedlegals.com/resources/startup-founder-vesting/)
- **SEIS/EIS 考量**：SEIS 给予投资人 50% 所得税减免和 0% 资本利得税（3 年持有期）；EIS 给予 30%
  所得税减免。投资人股份通常是单独的“A 类普通股”，附带措辞精心的（非字面的）清算优先权以保持
  SEIS/EIS 合规；复杂的持股/子公司结构可能危及减免。
  [SeedLegals，SEIS 与 EIS](https://seedlegals.com/resources/seis-eis-tax-relief-facts/)
- **成长股（Growth shares）**：英国特有的股份类别，仅对超过设定门槛价的增值有价值，用于 EMI
  （税务优惠期权计划，仅限全职英国雇员）不适用的场景。
  [SeedLegals，股份期权](https://seedlegals.com/grow/share-options-scheme/)
- **当地律师提示**：SEIS/EIS 结构安排是 HMRC 专属领域，持续受监管（减免可能被追溯取消），且直接
  与章程措辞交互——属于必须由合格的英国律师/会计师处理的事项，而非 DIY 起草。

### 8.4 MENA——DIFC / ADGM vs 岸上/本土大陆法域

**DIFC 和 ADGM（阿联酋自贸区）——普通法、投资人熟悉**：

- 两者均依**英国普通法框架**运作，拥有独立于阿联酋民事法院的自身法院；ADGM 直接采纳约 50 部英国
  成文法；两者均允许 100% 外资所有权，多数活动 0% 公司税。允许多种股份类别（普通投票股、多重投票股、
  优先分红股）；ADGM SPV 可提供零碎持股。
  [10 Leaves](https://10leaves.ae/publications/adgm/using-adgm-spvs-as-holding-structures-for-startups) ·
  [Al Tamimi & Company](https://www.tamimi.com/law-update-articles/remedies-for-shareholders-in-the-company-law-of-the-uae-and-the-difc/)
- **成熟/ESOP 结构安排**（Kayrouz & Associates，专注阿联酋的事务所）：阿联酋本土 LLC 面临 50 名
  股东上限及所有转让的强制优先购买权，使真实的股权成熟不切实际——执业者转而使用虚拟股份、股票增值权
  （SAR）或合同性利润参与（现金结算，非真实所有权）。**DIFC**（2018 年第 5 号公司法）和 **ADGM**
  允许在公司章程中排除优先购买权，从而在不受本土法定上限约束的情况下进行真实的股权发行。被引用的
  市场标准条款（10–15% 完全稀释 ESOP 池、4 年成熟/1 年悬崖）在使用 DIFC/ADGM 载体后与美国/特拉华
  惯例一致。
  [Kayrouz & Associates](https://www.kayrouzandassociates.com/insights/uae-employee-incentives-stock-options-esop-difc-adgm-mainland)

**阿联酋本土/岸上及其他 GCC 大陆法域**：

- 2021 年第 32 号联邦法令（2022 年 1 月 2 日生效，2025 年修订）取消了多数本土商业活动历史上
  51% 阿联酋人持股/本地代理人的要求，允许最高 100% 外资所有权（战略行业仍需批准）。
  [U.ae](https://u.ae/en/information-and-services/business/doing-business-on-the-mainland/full-foreign-ownership-of-commercial-companies)
- 2025 年修订现在允许通过股东协议拥有更多合同自由来安排投票权、转让限制、拖带/随售权和退出机制——
  *“前提是这些安排不与法律的强制性规定或公共政策冲突。”*
  [Middle East Briefing](https://www.middleeastbriefing.com/news/uaes-2025-commercial-companies-law-what-businesses-need-to-know/)
- **真实的灰色地带**：《商业公司法》认定任何“剥夺合伙人利润或免除其分担损失”的公司章程大纲条款
  无效——这一大陆法原则可能与特拉华/DIFC 式成熟丧失机制冲突。*此具体主张系由二手摘要重构，而非
  钉死在一份一手法律警报上；在视为定论前，请对照 2021 年第 32 号联邦法令文本或具名律所警报核实。*
- **沙特阿拉伯——值得注意的大陆法例外**：新《公司法》（2023 年 1 月生效）引入了**简化股份公司
  （SJSC）**——无最低资本、可单人股东设立、允许单一总裁/董事、多种股份类别（普通、优先、可赎回、
  可转换）——沙特 LLC 不适用。MISA 近期改革允许多数行业对 JSC 100% 外资持股。**未找到确认 SJSC
  特有成熟/丧失可执行性的来源**——标注为真实缺口。
  [HFA Firm](https://hfafirm.com/establishing-a-simplified-joint-stock-company-in-saudi-arabia/) ·
  [Al Tamimi](https://www.tamimi.com/law-update-articles/the-new-saudi-companies-law-what-you-need-to-know-1/)

**当地律师强制提示**：任何岸上/本土 GCC 实体（阿联酋本土、沙特 LLC/JSC/SJSC、埃及或其他 MENA
大陆法域）都应在技能中触发硬性“需当地律师”标记——既因为围绕默认利润分配/丧失规则的法定合同自由
仍在积极演变，也因为公开可得的、针对创始人协议机制（区别于一般公司/税法）的 MENA 一手资料确实
单薄——见第 10 节。

---

## 9. 伦理与范围

### 9.1 不构成法律意见；不建立律师-客户关系

参照知名法律科技工具的做法：

- **Cooley GO**：无意构成“具体的法律、税务和/或会计意见”，也无意替代合格律师；用户“不应基于其
  材料作为或不作为”。
  [Cooley GO 使用条款](https://www.cooleygo.com/terms-of-use/)
- **SeedLegals**：*“不是律师事务所，不提供任何法律或税务意见……仅提供信息参考……其不审查材料的
  准确性或法律充分性，不作出法律结论，也不将法律适用于具体情况。”*
  [SeedLegals 服务条款](https://seedlegals.com/us/terms-of-service/)

**对本技能**：以显著、通俗的语言声明其输出为起草辅助/文档组装工具，不构成法律意见，使用它不与
任何人建立律师-客户关系。

### 9.2 一位律师“代表公司”时的利益冲突

商业律师通常受聘担任**拟设立实体**的法律顾问，而非任何一位创始人的律师——尽管多位创始人依赖
同一份起草成果。
[ABA Business Law Today，《谁是客户？》](https://businesslawtoday.org/2021/12/who-is-the-client-ethics-issues-structuring-start-ups-representing-early-stage-companies/)

这为何构成真实冲突：创始人的个人利益（股权分配、成熟加速、离任条款、既往贡献积分）彼此之间及与
实体的抽象利益之间，可能而且确实存在分歧。依职业责任规范，认识到这一点的律师必须劝告各方
“充分理解尽管存在日后潜在冲突风险、仍由一位律师推进的后果”——
其依据为 [ABA 示范规则 1.7](https://www.americanbar.org/groups/professional_responsibility/publications/model_rules_of_professional_conduct/rule_1_7_conflict_of_interest_current_clients/comment_on_rule_1_7/)。

**建议**：每位创始人在签署前应获得**独立律师**——尤其是股权分配、成熟和离任条款，这些正是创始人
利益最常分歧之处。本技能（如同公司律师）为作为整体的实体起草；不为任何一位创始人的个人利益谈判，
并应在其输出中明确说明。
[ABA Business Law Today](https://businesslawtoday.org/2021/12/who-is-the-client-ethics-issues-structuring-start-ups-representing-early-stage-companies/)

### 9.3 税务意见警示——83(b) 与 QSBS

- **83(b) 不可撤销**——已申报的选择书日后被丧失（创始人未及成熟即离开）的，无法退税。是否申报的
  决定（考虑创始人具体的 AMT 敞口、州税状况和 QSBS 资格）并不简单，而 30 天期限不容事后咨询
  （第 4.4 节）。始终将该事项交由 CPA/税务律师处理。
- **QSBS（IRC §1202）复杂性**：要求美国国内 C 型公司；直接从公司购买（非二级市场）的股票；
  3 年（2025 年 7 月后）或 5 年（2025 年 7 月前）持有期；非公司股东；发行时的总资产门槛
  （2025 年 7 月后 $75M / 之前 $50M）；排除某些“合格贸易或业务”类别（会计、咨询、金融/法律服务、
  银行、农业、酒店等）；以及**持续合规**——即使股票最初以合格身份发行，若在“实质上全部”持有期内
  未满足要求，资格也可能丧失。
  [Cooley，QSBS 速查表](https://www.cooley.com/-/media/cooley/pdf/practices/qsbs-cheat-sheet) ·
  [Wilson Sonsini](https://www.wsgr.com/en/insights/understanding-section-1202-the-qualified-small-business-stock-exemption.html)

**对本技能**：将 83(b)/QSBS 输出仅视为信息参考，始终搭配 CPA/税务律师转介提示，未经该转介绝不
自动推荐具体选择。

### 9.4 律师协会 / 未经授权执业（UPL）背景

到 2025 年，超过 30 个美国州发布了针对 AI 的律师执业指引；核心原则：律师不得将构成法律执业的
任务委托给 AI 工具，允许 AI 在无律师审核的情况下直接向客户提供法律意见属于未经授权执业。监督
律师责任（ABA 示范规则 5.3，延伸至非人工辅助）无论使用何种工具均持续存在。
[Paxton，2025 年州律师协会指引](https://www.paxton.ai/post/2025-state-bar-guidance-on-legal-ai) ·
[Oregon State Bar 正式意见 2025-205](https://www.osbar.org/_docs/ethics/2025-205.pdf)

**启示**：由于本技能面向律师自身的起草工作流（而非面向消费者的工具），UPL 风险低于直接面向创始人
的产品——但同样的逻辑适用：将技能定位为律师审核并承担职业责任的起草*辅助*工具，绝不是直接向
创始人提供建议的自主咨询者。

---

## 10. 来源说明

供任何将其落实为 `SKILL.md` 的人参考的置信度分级：

- **高置信度，直接抓取/引文核验**：Orrick 的 Stripe Atlas 法律指南（支撑多数具体百分比/时间表的
  最丰富一手来源）、YC 的股权分配与成熟库文章、Clerky 帮助中心文章、Carta 的成熟/83(b)/创始人持股
  数据页、NBER《第一笔交易》论文及摘要、*Stanford v. Roche* 案例评述（Patent Docs、Taft Law）、
  Paul Graham《创始人控制权》、SeedLegals 英国专项指南、FTC 2025 年新闻稿及《联邦公报》2026 年
  2 月规则移除、财政部法规 §1.83-2、IRS 表格 15620。
- **源自搜索引擎索引，未直接抓取**（Cooley GO、Wilson Sonsini 和 Orrick 在多次检索中均以 HTTP 403
  阻断自动抓取）：归因于这些律所的引文系通过搜索引擎对所列精确 URL 的缓存提取获得，并非编造，但在
  编码为样板文本前**应独立对照实时页面复核**，因为这些律所会定期更新模板语言。
- **已更正，而非如最初假设**：“不再需要将 83(b) 副本附于纳税申报表”的规则出自**财政部决定 9779
  （2016 年）**，而非 2018 年 TCJA（第 4.4 节）。
- **标注为无法核实 / 不得作为确凿事实引用**：（1）“First Round Capital：67% 的种子投资人将超过
  55/45 的分配视为红旗”及其他具体的 First Round 分手百分比（第 3.4 节、第 7 节）——未追溯到
  First Round 的一手出版物；（2）“CEO 任命 = 14-20 个百分点溢价”数字（第 3.2 节）——对 Wasserman
  数据的二手转述，未追溯到其一手文本；（3）英国 SaaS“33% 死股权”案例研究（第 6.4 节）——仅来自
  单一二手法律博客，未经独立佐证。
- **真实来源缺口，未以虚构细节填充**：MENA 创始人协议特有机制（第 8.4 节）。一般公司法来源充足
  （DIFC/ADGM 普通法地位、阿联酋 CCL 2021/2025 改革、沙特 SJSC），但未找到 DIFC.ae/ADGM.com 官方
  指引或 Al Tamimi/Clyde & Co 客户警报，就创始人成熟/离任机制达到 SeedLegals 之于英国、或
  Cooley/Clerky 之于特拉华那样的深度。MENA 成熟可执行性主张仅作方向性参考；在技能中对任何 MENA
  岸上/大陆法域硬性标注“当地律师强制”。
- **时效敏感，使用时须做现行法律核查**：竞业禁止可执行性全景（第 2.1 节）——各州立法机关逐年修订
  竞业禁止法规，联邦态势刚于 2026 年 2 月改变；不可视为永久固定的文本。

---
name: "eac-habre-jeanne-sulzer"
description: "为非洲特别法庭（Chambres Africaines Extraordinaires，Hissène Habré 案，达喀尔）准备的「验证优先」方法论。所有引用均经验证（forumchambresafricaines.org、legal-tools.org）。涵盖 2016 年 5 月 30 日初审判决、2017 年 4 月 27 日上诉判决（对 7,396 名受害者的 822.9 亿非洲法郎赔偿），以及普遍管辖权。为研究辅助工具，不构成法律意见。属于开源库「Skills for International Justice」的一部分——方法论：github.com/jeannesulzer/international-criminal-tribunals-skills"
metadata:
  author: "Jeanne Sulzer"
  license: "agpl-3.0"
  version: "2026-06-10"
---

# CAE / EAC —— 非洲特别法庭（Habré 案）

本技能管辖一切涉及塞内加尔司法机构内非洲特别法庭（CAE）——英文称塞内加尔法院中的非洲特别法庭（EAC）——的输出。纪律很简单，理由很具体：EAC 只审判了一个人——乍得共和国前总统 Hissène Habré——并创造了国际刑事司法的一个奠基性时刻：**非洲机构首次因国际罪行起诉非洲前国家元首**，以及**非洲普遍管辖权起诉首次进入审判**。Habré 于 2021 年 8 月 24 日去世，终结了刑事阶段；赔偿阶段已移交非盟受害者信托基金，在实体上仍然开放。

## 一段话概括的纪律

对任何案件特定文件——判决、裁定、起诉书、呈件、民事当事人提交材料——先验证再引用。"验证"指在当前会话中通过 `web_fetch`（或等效检索工具）访问**EAC 档案**（历史域名 `chambresafricaines.org` 间歇性不可用；镜像站 `forumchambresafricaines.org` 和国际刑事法院法律工具数据库（ICC Legal Tools Database）仍是可靠的第一层级来源）。项目知识库中的基础文本（2012 年《非盟—塞内加尔协定》、CAE《章程》）是例外；可直接引用。其他一律不得。

## 验证是梯度式的，而非二元式

EAC 的文件语料是**有限且已充分映射的**——只有一名被告、四项关键裁决、一份界定的民事当事人名册。三个层级：

- **存在性已验证。** 裁决标题、日期、法庭已对照权威来源确认。
- **内容已验证。** 抓取的文本在实质上确认了该命题。
- **段落已验证。** 所引用的具体段落或页码包含所引命题。

在相关处标注层级。EAC 裁决卷帙浩繁（2016 年 5 月 30 日初审判决超过 600 页）；在段落编号不具权威性时使用页码引用。

## 标准工作流

**第 0 步——识别文件。** 在做任何其他事之前，区分：

- **2016 年 5 月 30 日初审判决**（Ministère Public v. Hissein Habré，Chambre Africaine Extraordinaire d'Assises）——实体刑事判决
- **2016 年 7 月 29 日赔偿裁定**（Décision sur les Réparations Civiles，Chambre Africaine Extraordinaire d'Assises）——一审民事/赔偿裁定，常附于初审判决之后
- **2017 年 4 月 27 日上诉判决**（Procureur Général v. Hissein Habré，Chambre Africaine Extraordinaire d'Assises d'Appel）——最终刑事和民事判决，维持定罪但在一项直接强奸罪名上改判无罪，并将赔偿总额确定为 822.9 亿非洲法郎
- **调查阶段裁定**（Chambre Africaine Extraordinaire d'Instruction）——2015 年 2 月 13 日起诉书、关于对 Habré 资产采取保全措施的裁定
- **为 EAC 设立奠定基础的先行判例**：西非国家经济共同体法院 2010 年 11 月 18 日判决（*Habré v. Senegal*）、国际法院 2012 年 7 月 20 日判决（*Belgium v. Senegal*）

**第 1 步——规划引用。** 列出将出现的每项引用及每项所支持的命题。区分刑事和民事判决主文。

**第 2 步——按回退阶梯验证。** EAC 档案（forumchambresafricaines.org）→ legal-tools.org → 非洲联盟法律门户（au.int）→ HRW Habré 案件页面（鉴于 Reed Brody 的核心文献角色，程序里程碑上属第一层级）→ 学术评论（第二层级）→ 询问用户。

**第 3 步——用验证过的材料起草。** 使用 `references/citation-format.md` 中的引用格式。验证不完整时，如实说明。

**第 4 步——自我审计。** 每项引用必须可追溯至项目知识库或本会话中一次成功的检索。

## 基础文本（项目知识库中有时直接引用）

- **《塞内加尔共和国政府与非洲联盟关于在塞内加尔司法机构内设立非洲特别法庭的协定》** —— 2012 年 8 月 22 日在达喀尔签署。非洲联盟与塞内加尔之间的双边设立文书。
- **《非洲特别法庭章程》** —— 附于《协定》。具有操作性的实体和程序框架。关键条款：
  - 第 3 条 —— 属时管辖（**1982 年 6 月 7 日至 1990 年 12 月 1 日**）、属地管辖（在乍得实施的罪行）、属人管辖（"主要责任人（le ou les principaux responsables）"）
  - 第 4-7 条 —— 属事管辖（灭绝种族罪、危害人类罪、战争罪、酷刑罪）
  - 第 8 条 —— 个人刑事责任形式（实施、命令、策划、教唆、帮助和纵容、共同正犯理论、指挥/上级责任）
  - 第 9 条 —— 豁免——明确排除豁免（包括国家元首）
  - 第 10 条 —— 诉讼时效（不适用于国际罪行）
  - 第 11-12 条 —— 组成：法官由塞内加尔提名，由非洲联盟委员会正式任命
  - 第 14-16 条 —— 调查庭、审判庭和上诉庭
  - 第 27-28 条 —— 对受害者的赔偿；信托基金
- **塞内加尔《刑事诉讼法典》**和**塞内加尔《刑法典》** —— 在未被《协定》和《章程》取代的范围内补充适用
- **2007 年 2 月 12 日第 2007-05 号法律** —— 修改塞内加尔《刑法典》以纳入国际罪行（灭绝种族罪、危害人类罪、战争罪）
- **2007 年 2 月 12 日第 2007-04 号法律** —— 确立塞内加尔法院对国际罪行的域外管辖权
- **先行区域文书：**
  - 国际法院判决，*Questions concerning the Obligation to Prosecute or Extradite (Belgium v. Senegal)*，2012 年 7 月 20 日（《禁止酷刑公约》第 7 条下的 *aut dedere, aut judicare*——或引渡或起诉）
  - 西非国家经济共同体法院判决，*Hissène Habré v. Republic of Senegal*，ECW/CCJ/JUD/06/10，2010 年 11 月 18 日——认定鉴于 2007 年塞内加尔立法的非溯及问题，对 Habré 的任何起诉必须在一个具有"国际性质"的特设法院进行

如项目知识库中没有，从 forumchambresafricaines.org 或 legal-tools.org 检索。

## 机构架构（务必正确）

- **设立依据：** 非洲联盟与塞内加尔共和国**2012 年 8 月 22 日**《协定》。
- **运行期：** **2013 年 2 月 8 日 — 2017 年 4 月 27 日**。
- **所在地：** 塞内加尔达喀尔（位于达喀尔司法宫内；EAC 作为融入塞内加尔司法体系的法庭运作）。
- **组成：** 塞内加尔—非洲混合——法官由塞内加尔提名、由非洲联盟委员会正式任命，审判庭庭长和上诉庭庭长为非塞内加尔非洲国民、由非洲联盟任命（审判庭由布基纳法索的 Gberdao Gustave Kam 法官主持）。
- **调查阶段：** Chambre Africaine Extraordinaire d'Instruction。Habré 于 2013 年 6 月 30 日被捕；2015 年 2 月 13 日确认起诉书。
- **审判：** Chambre Africaine Extraordinaire d'Assises。2015 年 7 月 20 日开庭；2016 年 2 月结案陈述；2016 年 5 月 30 日宣判。
- **上诉：** Chambre Africaine Extraordinaire d'Assises d'Appel。2017 年 1 月 9-12 日听证；2017 年 4 月 27 日宣判。
- **关闭：** EAC 于 2017 年 4 月 27 日完成其任务授权并于其后不久解散。残余职能（赔偿执行）移交非盟受害者信托基金。
- **显著特征：**
  - **非洲普遍管辖权起诉首次进入审判**
  - **非洲机构首次因国际罪行起诉非洲前国家元首**
  - **独具非洲特色的混合模式** —— 由非盟与单一非洲国家之间的协定设立，法官由非盟任命，同时适用塞内加尔法和国际法
  - **一名被告** —— 仅 Hissène Habré 一人（六名共同被告最初在 EAC 被起诉，但针对他们的程序未在 EAC 推进；其中一些于 2015 年在乍得法院受审）
  - **具条约锚定的普遍管辖权** —— EAC 的管辖权以塞内加尔在《禁止酷刑公约》下的 *aut dedere aut judicare* 义务为基础（国际法院在 *Belgium v. Senegal* 中确认）
  - **巨额赔偿裁决** —— 向 7,396 名具名民事当事人支付 822.9 亿非洲法郎（约 1.25 亿欧元 / 1.45 亿美元），是国际（化）刑事法庭作出时史上最大金额的赔偿

## 来源层级

**第一层级（权威）：**
- **forumchambresafricaines.org** —— 非洲特别法庭论坛（Forum des Chambres Africaines Extraordinaires），EAC 裁决、庭审记录和程序记录的镜像档案库。收录 2016 年 5 月 30 日初审判决、2016 年 7 月 29 日赔偿裁定和 2017 年 4 月 27 日上诉判决
- **chambresafricaines.org** —— 历史官方 EAC 网站。间歇性可用；两个都查
- **legal-tools.org** —— 国际刑事法院法律工具数据库，收录《章程》和主要裁决
- **au.int** —— 非洲联盟法律门户，用于 2012 年 8 月 22 日《协定》和信托基金文件
- **国际法院档案**（icj-cij.org）—— 用于 *Belgium v. Senegal*（2012）
- **西非国家经济共同体法院档案** —— 用于 *Habré v. Senegal*（ECW/CCJ/JUD/06/10，2010）

**第二层级（次要，必须标注）：**
- **Human Rights Watch**（hrw.org/habre-case）—— Reed Brody 近乎完整的 Habré 案件文献档案；鉴于 Brody 三十年来作为民事当事人律师和调查员的核心角色，程序里程碑上在实践中属第一层级
- **Amnesty International** —— 广泛报道；尤其是 *Chad: Hissène Habré appeal ruling closes dark chapter for victims*（2017 年 4 月 28 日）
- **REDRESS** —— 关于赔偿的法庭之友意见书（2017 年 2 月）；关于信托基金的分析工作
- **Sarah Williams** —— *The Extraordinary African Chambers in the Senegalese Courts: An African Solution to an African Problem?*，JICJ 11 (2013) 1139 —— 关于机构设计的主要学术论述
- **Naomi Roht-Arriaza** —— 关于普遍管辖权的比较研究
- *The President on Trial: Prosecuting Hissène Habré*（牛津大学出版社 2020）—— Sharon Williams 和 Sharan Srinivasan 主编 —— 标准学术卷
- **Oxford Public International Law** 词条 "Extraordinary African Chambers"（opil.ouplaw.com）
- **《Nordic Journal of Human Rights》**，第 34 卷第 3 期（2016）—— Habré 案专刊
- **《Journal of African Law》**（剑桥大学出版社）—— Diab 等人关于赔偿实践的文章
- **ATPDH**（乍得人权促进与保护协会）—— 由 Jacqueline Moudeina 领导的民事当事人组织
- **JusticeInfo.net** —— 审判和审后赔偿执行报道

**永不可作为权威：** 维基百科、Grokipedia、社交媒体、AI 生成摘要。

见 `references/authoritative-sources.md`。

## 引用格式

EAC 引用遵循适用于混合语境的塞内加尔大陆法惯例。两件事重要：

1. **案件称谓** —— 刑事诉讼在一审为 *Ministère Public v. Hissein Habré*；上诉为 *Procureur Général v. Hissein Habré*。民事维度体现在《民事赔偿裁定》（Décision sur les Réparations Civiles）中，该裁定列出民事当事人（民事当事人的主案常以主要民事当事人之名引用为 *Clément Abaïfouta and 6,999 Others*）。

2. **法庭称谓：**
   - **Chambre Africaine Extraordinaire d'Instruction**（调查庭）
   - **Chambre Africaine Extraordinaire d'Assises**（审判庭）
   - **Chambre Africaine Extraordinaire d'Assises d'Appel**（上诉庭）

**工作示例：**

- *Ministère Public v. Hissein Habré*，Chambre Africaine Extraordinaire d'Assises，Jugement（判决），2016 年 5 月 30 日。
- *Ministère Public v. Hissein Habré*，Chambre Africaine Extraordinaire d'Assises，Décision sur les Réparations Civiles（民事赔偿裁定），2016 年 7 月 29 日。
- *Procureur Général v. Hissein Habré*，Chambre Africaine Extraordinaire d'Assises d'Appel，Arrêt（上诉判决），2017 年 4 月 27 日。

完整惯例见 `references/citation-format.md`。

## 审计模式取决于文件类型

当用户提供文件时：
- **工作草稿**：审计引用的准确性。
- **最终 EAC 记录**：清点并抽查；EAC 语料规模足够小，全面审查可行。

无论哪种模式，第 0 步（识别文件和法庭）都先行。最常见的混淆发生在初审判决（2016 年 5 月 30 日）与上诉判决（2017 年 4 月 27 日）之间；两者的实体认定至少在重要罪名（直接实施强奸）上存在差异。

## 实体学说——指引

本技能不逐行编码学说。起点：

- **以条约义务为基础的普遍管辖权** → 《禁止酷刑公约》第 7 条（*aut dedere aut judicare*）；国际法院 2012 年 7 月 20 日 *Belgium v. Senegal* 确认塞内加尔的义务
- **属事管辖** → 灭绝种族罪、危害人类罪、战争罪、酷刑罪（《章程》第 4-7 条）
- **属时管辖——严格受限** → 1982 年 6 月 7 日至 1990 年 12 月 1 日（Habré 执政期）
- **属人管辖** → "责任最大的人（person or persons most responsible）"——实践中即仅 Habré 一人面对 EAC
- **责任形式** → EAC 适用了对**指挥/上级责任**和**共同正犯理论（JCE）**的独特构建，以适应威权国家的具体事实形态（DDS——国家文献与安全局——是 Habré 的秘密警察，镇压的主要工具）。Sarah Williams（上文注 6）和《Journal of International Criminal Justice》的报道讨论了这些学理创新
- **国家元首无豁免** → 《章程》第 9 条；与习惯国际法及国际法院在 *Belgium v. Senegal* 中的框架一致
- **民事当事人（parties civiles）** → 遵循塞内加尔大陆法传统的有力民事当事人参与；民事当事人由塞内加尔、乍得和国际律师代理（Jacqueline Moudeina 为乍得首席律师；Reed Brody 为主要调查员和辩护人）；7,396 名具名民事当事人获认证
- **赔偿** → 《章程》第 27-28 条；审判庭 2016 年 7 月 29 日裁定按类别设定个人赔偿（强奸和性暴力受害者：每人 2000 万非洲法郎 ≈ 33,880 美元；任意拘留、酷刑、战俘和幸存者：每人 1500 万非洲法郎 ≈ 25,410 美元；间接受害者：每人 1000 万非洲法郎 ≈ 16,935 美元）；上诉庭 2017 年 4 月 27 日确认该框架，并将总额确定为对 7,396 名受害者的 **822.9 亿非洲法郎**；由非洲联盟管理的受害者信托基金负责执行

对每一项，通过工作流验证具体裁决。

## 敏感语境

EAC 判决将 Habré 政权（1982-1990）定性为通过系统性杀戮、大规模酷刑、性暴力以及 DDS 秘密警察活动造成约 **40,000 名受害者**死亡。法庭的认定如今具有历史权威性。民事当事人包括强奸和性暴力幸存者，她们的作证勇气——尤其是中南部地区的女性——是判决的基础。

Habré 于 **2021 年 8 月 24 日**去世，这在法律上消灭了对他人身的刑事诉讼，但不影响 EAC 判决的有效性，也不影响非盟信托基金执行赔偿的义务。截至 2026 年，信托基金的运作状况仍是一个重大关切：仅追回极少量资产，赔偿尚未实质性发放。处理赔偿问题时，既要关注学理成就，也要关注实践层面的失望。

Habré 的辩护团队在整个程序中都质疑 EAC 的合法性（质疑塞内加尔的属时管辖、塞内加尔 2007 年立法的非溯及性以及非盟的制度角色）。Habré 拒绝承认该法庭，未出席庭审开始（法庭在指定法院指定律师后继续进行），且从未接受该程序。这些辩护论点有程序记录为证；它们不影响判决的实体有效性，但属于机构历史的一部分。

## 本技能不是什么

- 不是法律意见。输出是研究和起草辅助工具。
- 不是 EAC 记录的替代品。
- 未经 EAC、非洲联盟、塞内加尔共和国或乍得共和国背书。
- 不是对 EAC 判例提出的有争议学理问题（尤其是对整整 8 年期间整个国家机器的 JCE 和指挥责任的构建）的立场表态。本技能使 EAC 认定能够被准确引用；学术争议留给用户。

## 参考文件

- `references/authoritative-sources.md` —— 来源层级和 URL
- `references/citation-format.md` —— 案件名称惯例、法庭称谓、工作示例
- `references/verification-workflow.md` —— 回退阶梯、EAC 特定陷阱
- `references/foundational-texts.md` —— 2012 年《非盟—塞内加尔协定》、CAE《章程》、国际法院 *Belgium v. Senegal*、西非国家经济共同体法院 *Habré v. Senegal*
- `references/jurisprudence-map.md` —— EAC 认定的逐主题地图
- `examples/example-verification.md` —— 端到端验证一项 EAC 引用
- `examples/example-audit.md` —— 审计用户提供的文件

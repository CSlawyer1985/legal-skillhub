---
name: "cps-rca-central-african-republic-jeanne-sulzer"
description: "面向中非共和国特别刑事法院（混合法院，坐落在班吉）的「验证优先」方法论。每项引用均须核实（JusticeInfo、FIDH、HRW、legal-tools.org；官方网站经常返回 403 错误）。涵盖 Paoua 案、第 3 条中「notamment」一词的含义，以及与 ICC 的互补性。属研究辅助工具，不构成法律意见。为开源库「Skills for International Justice」的组成部分——方法论：github.com/jeannesulzer/international-criminal-tribunals-skills"
metadata:
  author: "Jeanne Sulzer"
  license: "cc-by-4.0"
  version: "2026-06-10"
---

# CPS——中非共和国特别刑事法院

本技能管辖所有涉及中非共和国特别刑事法院（CPS）的输出。纪律简单，理由具体：CPS 是**首个整合于国家司法体系之内、对国际罪行拥有管辖权的完全混合法院**，也是少数几个在持续武装冲突国家运作的此类法院之一。其案件编号和程序记录仍在发展中；法院主要以**法语**进行工作；其与国际刑事法院（ICC）的互补关系（ICC 在中非共和国有两个情势）在制度上独具特色。

## 一段话概括的纪律

对于任何案件特定文件——判决、决定、起诉书、诉讼文书、预审裁定（ordonnance d'instruction）、公诉书（requisitoire）——在引用前先验证。"验证"指在当前会话中使用 `web_fetch`（或等效检索）访问 **cpsrca.cf**（CPS 官方网站）。项目知识库中的基础文本（组织法 15.003、关于程序与证据规则的第 18.010 号法律、中非刑法典、与 ICC 的合作法）是例外，可直接引用。其他一律不行。

## 验证是渐进的，而非二元的

在实践中，cpsrca.cf **得到积极维护**（CPS 正在运作，定期有新的庭审、决定和新闻稿），但对其直接 `web_fetch`——如同几个 CPS 相关网站（JusticeInfo、HRW）一样——经常返回 403 或部分内容。将此视为预期情况，走逐级退让层级（legal-tools.org、MINUSCA、JusticeInfo、RJDH、Radio Ndeke Luka），而非视为死路。三个层级：

- **存在已验证。** 案件、文件类型、日期、分庭已确认。
- **内容已验证。** 抓取的文本在实质上确认了命题。
- **段落已验证。** 所引用的具体段落包含所引命题。

在相关处标注层级。CPS 在完整说理判决之外还发布判决摘要；对于实质性裁判结论，**arrêt motivé**（完整说理判决）具有权威性，而非新闻稿摘要。

## 标准工作流

**第 0 步——识别文件。** 在做其他事情之前，先区分：
- **案件**（l'affaire Paoua / Lemouna et Koundjili；l'affaire Ndélé 1；l'affaire Ndélé 1 contumace；后续案件）
- **分庭**——**Chambre d'instruction**（预审庭）、**Chambre d'assises**（重罪庭）、**Chambre d'appel**（上诉庭）、**Chambre de cassation**（终审法院，如适用）
- **文件类型**——裁定（Ordonnance）、公诉书（Réquisitoire）、起诉书（Acte d'accusation）、重罪庭判决（Jugement de la Chambre d'assises）、上诉庭判决（Arrêt de la Chambre d'appel）、民事利益决定（Décision sur les intérêts civils）

**第 1 步——规划引用。** 列出将出现的每项引用及其支撑的命题。

**第 2 步——用逐级退让层级验证。** cpsrca.cf → JusticeInfo.net（第二层级，用于案件摘要）→ MINUSCA 新闻稿（第一层级，用于机构合作事项）→ FIDH / Human Rights Watch 监测报告（第二层级）→ 询问用户。

**第 3 步——使用已核实材料起草。** 使用 `references/citation-format.md` 中的引用格式。

**第 4 步——自我审计。** 每项引用必须可追溯至项目知识库或本次会话中的成功检索。

## 基础文本（存在于项目知识库时从其引用）

- **2015 年 6 月 3 日第 15.003 号组织法**——设立、组织与运作特别刑事法院的法律（2015 年 4 月 22 日由全国过渡委员会通过；2015 年 6 月 3 日由过渡总统 Catherine Samba-Panza 颁布）——构成性文书。关键条款：
  - 第 1 条——设立 CPS
  - **第 3 条——属物管辖**（对**自 2003 年 1 月 1 日以来**在中非共和国领土内实施的"严重侵犯人权和违反国际人道法的行为……**包括**（notamment）灭绝种族罪、危害人类罪和战争罪"）。法律文本中的"notamment"（包括）一词具有承重意义——关于该清单是示例性而非穷尽性的争论见 `references/foundational-texts.md`。
  - 第 4 条——属人管辖
  - 第 5 条——并行管辖（与国家法院；CPS 具有优先性）
  - 第 6 条——与 ICC 的互补性（CPS **并非** ICC 的严格下级机构，但 ICC 已启动程序之处，其管辖权让位）
  - 第 7-12 条——组成（13 名本国 + 12 名国际法官）
  - 第 14-15 条——特别检察官及特别检察官办公室
  - 第 19-25 条——分庭结构（预审庭、重罪庭、上诉庭）
  - 第 39-47 条——辩护权、受害人、证人
  - 第 51-52 条——国际合作
  - 期限——5 年可续期（已续期）
- **2018 年 7 月 2 日第 18.010 号法律**——特别刑事法院程序与证据规则（"Règlement de procédure et de preuve"/"RPP"）——程序与证据框架。**鲜明地是一部《法律》**，而非法院采纳的规则（不同于大多数国际法庭的 RPE）。
- **中非共和国刑法典**（2010 年 1 月 6 日第 10.001 号法律）——将国际罪行定义纳入中非国内法；确认国际罪行不受时效限制、无豁免、国际罪行不适用大赦/赦免。**CPS 适用的实体刑法是中非刑法典**，必要时参照国际法。
- **中非共和国刑事诉讼法典**——在组织法 15.003 和 RPP 未替代的范围内适用。
- **中非政府与 MINUSCA 之间的谅解备忘录**（2014 年 8 月）——联合国与 CPS 合作的制度基础，签署于组织法通过之前。

如不在项目知识库中，从 cpsrca.cf/documentations/textes-juridiques 检索。

## 机构架构（务必弄对）

- **设立依据：** 组织法第 15.003 号（2015 年 4 月 22 日/2015 年 6 月 3 日颁布）。
- **首次开庭：** **2018 年 10 月 22 日**，标志着司法活动的开始。
- **所在地：** 中非共和国班吉（CPS 设于中非国家司法体系之内；法院大楼在班吉）。
- **组成：** 共 25 名法官——**13 名本国法官**（中非籍）和 **12 名国际法官**（来自不同司法辖区）。院长和副院长在本国与国际法官之间轮换；特别检察官为国际法官（首任特别检察官 Toussaint Muntazini Mukimapa 先生，原籍刚果民主共和国，2017 年任命，任职至其 2026 年 3 月 25 日去世；引用前核实现任任命）。
- **资金与支持：** 主要来自 **MINUSCA**（联合国中非共和国多层面综合稳定团）以及欧盟、美国、法国、荷兰等。
- **运作状态：** 截至 2026 年**积极运作**，定期开庭。
- **显著特征：**
  - **整合于中非国家司法体系**——非独立法院；CPS 是中非司法机关的一部分，拥有自己的特殊程序
  - **适用中非实体刑法**（中非刑法典）和中非刑事诉讼程序（受组织法 15.003 和 RPP 约束）——以国际法补充
  - **以法语运作**——主要工作与程序语言（为证人提供桑戈语口译）
  - **与 ICC 的互补性**——CPS 与 ICC 的中非情势一（中非共和国 2004 年 12 月 22 日提交，2007 年 5 月 22 日立案；在 ICC 产生 *Bemba* 案）和中非情势二（2014 年 5 月 30 日提交，2014 年 9 月 24 日立案；产生 *Yekatom & Ngaïssona* 和 *Said* 案）进行协调
  - **民事当事人（parties civiles）**——遵循中非大陆法传统的民事当事人参与（区别于 ICC 的受害人参与模式，也区别于普通法的受害人-证人框架）
  - **缺席审判（contumace）**——明确授权；在 *Ndélé contumace* 案中使用

## 来源层级

**第一层级（权威）：**
- **cpsrca.cf**——CPS 官方网站。载有组织法 15.003、RPP（第 18.010 号法律）、中非刑法典、新闻稿、庭审公告、判决摘要和案件动态。得到积极维护。
- **legal-tools.org**——ICC 法律工具数据库。载有组织法 15.003、RPP 和部分 CPS 决定
- **MINUSCA 新闻稿**（minusca.unmissions.org）——机构合作；部分判决公告
- **un.org/securitycouncil**——关于 MINUSCA 授权续期（联合国安理会第 2149 (2014) 号决议及后续决议），其中包含对 CPS 的支持

**第二层级（次要，须标注）：**
- **JusticeInfo.net**——CPS 程序的法语和英语报道；高质量的庭审监测
- **FIDH**（国际人权联合会）和 **OCDH**（中非人权组织）——民间社会监测
- **Human Rights Watch**——关于中非冲突和 CPS 的大量报道（尤其 2018 年"En quête de justice"报告）
- **Radio Ndeke Luka**——中非媒体，当地报道
- **Oubangui Médias**——中非媒体
- **学术评论**——Damien Scalia、Mark Kersten、Linda M. Keller、Patryk I. Labuda、Olivier Beauvallet（CPS 上诉法官）、Volker Nerlich（CPS 上诉法官）——关于混合司法机构的研究
- **Cairn.info**——关于 CPS 的法语学术文章
- **violences-sexuelles.ifjd.org**——IFJD（法语国家正义与民主研究所）——关于中非性暴力起诉的参考资料

**绝不具权威性：** Wikipedia、Grokipedia、社交媒体、AI 摘要。

## 引用格式

CPS 引用不同于国际法庭引用。案件按**案件名称**（而非国际法庭意义上的案件编号）和**分庭**指称。引用格式遵循法国/中非司法惯例：

**一般形式：**
> *Procureur spécial contre [被告人]*，[案件名称]，Chambre [分庭]，[文件类型]，[日期]。

**工作示例：**

- *Procureur spécial contre Issa Sallet Adoum, Yaouba Ousman et Mahamat Tahir*，**Paoua / Lemouna et Koundjili 案**，Chambre d'assises，**2022 年 10 月 31 日**判决。
- *Procureur spécial contre Issa Sallet Adoum, Yaouba Ousman et Mahamat Tahir*，**Paoua 案**，Chambre d'appel，**2023 年 7 月 20 日**上诉判决 [刑期减轻；Issa Sallet Adoum 被判处 30 年]。
- *Procureur spécial contre [被告人]*，**Ndélé 1 案**，Chambre d'assises，[日期][判决 / 决定]。

惯例详见 `references/citation-format.md`。

## 审计模式取决于文件类型

- **工作草稿**：审计引用准确性。
- **CPS 最终记录**：识别案件（l'affaire）、分庭、文件类型、日期。

在任一模式中，第 0 步（识别文件和案件）先行。**CPS 程序在各分庭之间流转迅速**（预审庭 → 重罪庭 → 上诉庭），同一被告出现在整个程序中的多份决定里——第 0 步防止混淆。

## 实体判例——要点

本技能不逐行编码判例。以下为起点（每项在引用前均须通过工作流验证）：

- **属物管辖（compétence matérielle）** → 组织法 15.003 第 3 条：严重侵犯人权和违反国际人道法的行为，包括灭绝种族罪、危害人类罪、战争罪，**按中非刑法典和国际法的定义**。
- **属时管辖** → 第 3 条：**自 2003 年 1 月 1 日以来**实施的犯罪（开放式、持续进行——在混合法庭中独树一帜）。
- **与 ICC 的互补性** → 第 6 条：ICC 已启动程序之处，CPS 的管辖权让位（实践中，ICC 的 Bemba 案是中非情势一的起诉；CPS 不重复 ICC 在办案件）。
- **个人刑事责任模式** → 中非刑法典（实行犯、共同实行犯、从犯；共同正犯；军事指挥官的上级责任）。
- **性暴力（强奸）的危害人类罪** → 在 *Paoua* 案审判判决中适用，包括对 Issa Sallet Adoum 就其下属实施的强奸**认定指挥责任**。
- **民事当事人（parties civiles）** → *Paoua* 案包含民事利益庭审（audience sur les intérêts civils）——大陆法受害人参与的特色。与 ICC 赔偿和黎巴嫩特别法庭（STL）受害人参与进行对比。
- **缺席审判（contumace）** → 在 *Ndélé 1 contumace* 案中使用；中非程序允许缺席审判，逮捕后可变更为重审，结构上类似于 STL 第 22 条，但根植于大陆法传统。
- **国际罪行不受时效限制** → 中非刑法典（2010 年）确认不受时效限制；CPS 一贯适用。

每一项都须通过工作流验证。

## 敏感背景

中非冲突（2003 年至今，历经数波）涉及基督教/泛灵论（anti-balaka）和穆斯林（Séléka、前 Séléka、3R、MPC、FPRC、UPC）武装团体，对平民的极端暴力、大规模性暴力、约五分之一人口流离失所，以及持续脆弱。CPS 面前的被告往往是仍活跃或近期活跃的武装团体成员。证人保护是重大的运营挑战。受害人和幸存者常常与施暴者近在咫尺。保持事实精确，避免煽情，使用法院自身使用的语言（通常为"武装团体"而非族裔或宗教简写），绝不可轻描淡写。班吉论坛（2015 年）是中非民族和解进程——将其作为 CPS 的政治制度基础加以引用是恰当的。

## 本技能不是什么

- 不是法律意见。输出是研究和起草辅助工具。
- 不是 CPS 记录的替代品。
- 未经 CPS、中非政府或联合国认可。
- 并非穷尽：CPS 定期发布；新案件不断出现。核实任何案件的当前状态。

## 参考文件

- `references/authoritative-sources.md`——来源层级和 URL（cpsrca.cf、JusticeInfo、MINUSCA、FIDH/OCDH）
- `references/citation-format.md`——引用惯例、具名案件（"Affaire Paoua / Lemouna et Koundjili"、"Affaire Ndélé 1"、"Affaire Ndélé 1 contumace"）、分庭指称
- `references/verification-workflow.md`——逐级退让层级、CPS 特定陷阱（国家法院与国
际法庭；CPS 与 ICC；法语为主要语言；民事当事人与 ICC 受害人参与；Paoua 案一审与上诉刑期差异；缺席审判的重审权）
- `references/foundational-texts.md`——组织法 15.003、RPP（第 18.010 号法律）、中非刑法典、MINUSCA 合作谅解备忘录
- `references/jurisprudence-map.md`——CPS 裁判结论的分主题图谱（截至 2026 年规模不大但不断增长）
- `examples/example-verification.md`——端到端核实一条 Paoua 案引用
- `examples/example-audit.md`——审计用户提供的文件（Paoua 案一审与上诉刑期；CPS 名称误用）

---
name: "jep-jeanne-sulzer"
description: "针对和平特别司法管辖区（Jurisdicción Especial para la Paz，JEP）的验证优先方法论。JEP 是哥伦比亚依据 2016 年与 FARC-EP 达成的《最终和平协议》设立的过渡期司法法院。所有引用在使用前均对照 jep.gov.co 核验。覆盖 11 个 macrocase（从案件 01 绑架案到案件 11 性暴力案，包括案件 03 虚假阳性案）、三个制裁层级（propias、alternativas、ordinarias）、TOAR，以及 SIVJRNR 的姊妹机构（CEV、UBPD）。守护关键结构性区分（Sala de Reconocimiento 与 Tribunal para la Paz；comparecientes 中 FARC-EP 与 Fuerza Pública 与第三方平民；Acto Legislativo 01/2017 与 Ley Estatutaria 1957/2019）。为研究辅助工具，不构成法律意见。"
metadata:
  author: "Jeanne Sulzer"
  license: "cc-by-4.0"
  version: "2026-07-04"
---

# JEP——和平特别司法管辖区（哥伦比亚）

本技能规范所有涉及和平特别司法管辖区（JEP）的输出。JEP 是哥伦比亚政府与 FARC-EP 于 **2016 年 11 月 24 日签署《最终和平协议》**所建立的哥伦比亚过渡期司法体系中的司法组成部分。这一纪律很简单，其理由也很具体：JEP 适用一种独特的修复性正义模式——它于 **2025 年 9 月作出首批判决**，对持续逾五十年的国内武装冲突中最严重罪行适用 *sanciones propias*（修复性非监禁制裁）。其程序融合了哥伦比亚大陆法系结构、国际刑法标准与一种独有的修复性正义进路。引用纪律至关重要。

## 一句话概括纪律

对任何具体案件文书——auto、providencia、resolución、sentencia、lineamiento——在引用前须核验。“核验”指在当前会话中通过 `web_fetch`（或等效检索工具）访问 **jep.gov.co**（JEP 官方网站）。项目知识库中的基础文本（《最终和平协议》、2017 年 1 号宪法修正案、2019 年第 1957 号法定法、《总章程》）为例外，可直接引用。除此之外别无其他。

## 核验是梯度性的，而非二元性的

JEP 发布大量资料，其网站**持续维护**，因此 jep.gov.co 是正确的第一站。但不要将成功抓取视为必然：直接检索可能失败——HTTP 403、超时或 PDF 无法渲染——而这种失败是**结构性的，并非死胡同**。发生此类情况时，沿 `references/verification-workflow.md` 中的降级阶梯走查，而非放弃核验或凭记忆引用。分为三个层级：

- **存在性已核验。** macrocase、文书类型、日期、机关已确认。
- **内容已核验。** 抓取的文本在实质上确认了该主张。
- **段落已核验。** 所引用的具体段落或章节包含所引主张。JEP 的判决和命令卷帙浩繁（2025 年 9 月的两份判决合计超过 1,247 页），采用编号章节而非国际法庭式的段落编号。无段落编号时，按章节和页码核验。

在相关处标注核验层级。

## 标准工作流

**第 0 步——识别文书。** 在任何其他操作之前，区分：
- **macrocase**（案件 01 至 11——见下文引用格式）
- 作出文书的**机关**：
  - **Salas de Justicia**——三个 Salas：**Sala de Reconocimiento de Verdad y Responsabilidad y de Determinación de los Hechos y Conductas**（SRVR 或“Sala de Reconocimiento”）；**Sala de Amnistía o Indulto**（SAI）；**Sala de Definición de Situaciones Jurídicas**（SDSJ）
  - **和平特别法庭（Tribunal Especial para la Paz）**——一审法院（下设四个“Secciones”：**Sección de Reconocimiento de Verdad y Responsabilidad**、**Sección de Ausencia de Reconocimiento de Verdad y Responsabilidad**、**Sección de Apelaciones**，以及**Sección de Revisión de Sentencias**）
  - **调查与起诉处（Unidad de Investigación y Acusación，UIA）**——检察机构
  - **全体会议（Sala Plena）**——处理行政和一般事项
- **文书类型**——Auto（程序性）、Providencia（临时性）、Resolución（行政性）、Sentencia（判决）、Lineamiento（指引）
- **Comparecientes 类型**——**FARC-EP**（前战斗人员）、**Fuerza Pública**（军警）或 **terceros civiles**（第三方平民，包括准军事人员、商人、出资者）
- **2025 年 9 月判决是 JEP 的首批判决**——是该机构的分水岭时刻

**第 1 步——规划引用。** 列出将出现的每项引用及其支持的主张。

**第 2 步——以降级阶梯核验。** jep.gov.co → 联合国哥伦比亚核查团（`colombia.unmissions.org`）→ 明确标注的第二层级学术/监测来源 → 询问用户。

**第 3 步——使用已核验材料起草。** 使用 `references/citation-format.md` 中的引用格式。

**第 4 步——自我审计。** 每项引用必须可追溯至项目知识库或本会话中的成功检索。

## 基础文本（项目知识库中有则从中引用）

- **《终止冲突与建设稳定持久和平最终协议》（Acuerdo Final para la Terminación del Conflicto y la Construcción de una Paz Estable y Duradera）**，哥伦比亚政府与 FARC-EP 于 **2016 年 11 月 24 日**在波哥大签署。**第 5 点（“关于冲突受害者的协议：综合真相、正义、赔偿与不重复体系”）**是 JEP、CEV 和 UBPD 的设立文本。学术界通常简称“Acuerdo Final”或“2016 年和平协议”。
- **2017 年 1 号宪法修正案（Acto Legislativo 01 de 2017）**（2017 年 4 月 4 日宪法修正案）——将 JEP 和综合体系纳入哥伦比亚宪法。**过渡性条款第 5 至 18 条**设立 JEP。2017 年 3 月 14 日经参议院批准（60 票赞成、2 票反对）。
- **2019 年 6 月 6 日第 1957 号法定法（Ley Estatutaria 1957 de 2019）**——**JEP 法定法（Estatutaria de la JEP）**。关于 JEP 管辖权、组织与程序的详细框架法律。**至关重要**：这是主要的实体法律框架，是引用最多的基础文本。
- **2018 年 7 月 18 日第 1922 号法律（Ley 1922 de 2018）**——JEP 程序规则（Reglas de Procedimiento de la JEP）。程序框架。
- **JEP《总章程》（Reglamento General de la JEP）**——由 Sala Plena 通过；内部组织规则。
- **《哥伦比亚刑法典》**（Ley 599 de 2000）与**《刑事诉讼法典》**——补充适用。
- **国际文书**——哥伦比亚是《罗马规约》（2002 年 8 月 5 日批准，对战争罪设 7 年排除期，2009 年届满）、《日内瓦四公约》及《第一、第二附加议定书》、《禁止酷刑公约》、《美洲强迫失踪公约》、《美洲人权公约》、《公民及政治权利国际公约》（ICCPR）和《灭绝种族罪公约》的缔约国。JEP 将这些文书与国内法一并适用。

如项目知识库中没有，从 jep.gov.co（Documentos / Marco Normativo）取回。

## 制度架构（务必弄对）

- **设立依据：**《最终和平协议》（2016 年），经 2017 年 1 号宪法修正案入宪，框架法律为 2019 年第 1957 号法定法。
- **所在地：**哥伦比亚波哥大。
- **运作：**自 **2018 年 3 月 15 日**起开展司法活动（正式启动）；2018 年 FARC-EP 领导人首次 comparecencias（出庭）；**2025 年 9 月 16 日和 18 日作出首批判决**，涉及案件 01（FARC 绑架案）和案件 03（Costa Caribe 虚假阳性案）。
- **组成：**38 名法官（Magistrados）及候补；法官均为哥伦比亚人；JEP 还拥有受过国际训练的国外专家（Amici Curiae 和 Expertos Extranjeros），可参与特定职能。2024–2026 年任主席：**Alejandro Ramelli Arteaga**（2024 年 10 月当选，任期两年）。
- **显著特征：**
  - **修复性正义为主要模式**——*sanciones propias*（对承认责任者适用的 5–8 年修复性非监禁制裁）；*sanciones alternativas*（替代性制裁，对迟延承认者适用 5–8 年实际限制自由）；*sanciones ordinarias*（普通刑事制裁，对不承认者适用最高 20 年监禁）
  - **TOAR**——*Trabajos, Obras y Actividades con contenido Reparador y Restaurador*——comparecientes 开展的具体修复活动（排雷、环境修复、为受害者建设基础设施、搜寻失踪者）
  - **条件性制度（Régimen de condicionalidad）**——优惠（sanciones propias、减刑）以完整供述真相、赔偿和不重复为条件
  - **11 个 macrocase**，按主题和属地分类
  - **大陆法系程序**，带有大量哥伦比亚传统特征（autos、providencias、sentencias）
  - **Comparecientes 既包括 FARC-EP 战斗人员也包括 Fuerza Pública**（JEP 对冲突双方及平民第三方均拥有管辖权）
  - **纳入 SIVJRNR**，与 CEV（真相委员会，2022 年结束工作）和 UBPD（搜寻失踪者，进行中）并列

## 来源层级

**第一层级（权威）：**
- **jep.gov.co**——JEP 官方网站。收录《最终和平协议》、《1 号宪法修正案》、第 1957 号法定法、第 1922 号法律、《总章程》、所有 macrocase 页面、autos、sentencias、新闻公报、听证会。持续维护。
- **legal-tools.org**——选择性镜像 JEP 基础文本
- **CEV / 真相委员会**（`comisiondelaverdad.co`）——真相委员会最终报告（2022 年 6 月）——对真相与历史记录类结论属第一层级，但并非 JEP 自身的司法记录
- **UBPD**（`ubpdbusquedadesaparecidos.co`）——涉及搜寻失踪者事项
- **哥伦比亚宪法法院**（`corteconstitucional.gov.co`）——涉及影响 JEP 的合宪性裁决（特别是 2018 年 C-080 号判决及后续关于法定法合宪性的决定）
- **联合国哥伦比亚核查团**（`colombia.unmissions.org`）——联合国报告与核查工作

**第二层级（次要，必须标注）：**
- **西班牙语学术评述**——Kai Ambos（与 JEP 深度合作的德国专家）、Manuel Iturralde、Camilo Umaña、Yesid Reyes、Rodrigo Uprimny、Mauricio García Villegas（Dejusticia）
- **英语学术评述**——Mark Kersten（Justice in Conflict）、Jennifer Easterday、Naomi Roht-Arriaza、EJIL:Talk! 分析
- **Dejusticia**（`dejusticia.org`）——哥伦比亚智库；高质量监测与分析
- **Rodeemos el Diálogo**——公民社会分析
- **哥伦比亚媒体**——*El Espectador*、*El Tiempo*、*Semana*、*La Silla Vacía*、*El Colombiano*、*Razón Pública*（后者刊载严肃法律分析）
- **JusticeInfo.net**——国际报道
- **CINEP / Programa por la Paz**——公民社会
- **Hacemos Memoria**（安蒂奥基亚大学）——记忆研究分析
- **Colombia Check**——事实核查，可用于核验 JEP 相关表述
- **大学评述**——洛斯安第斯大学（种族灭绝、政治与法律研究中心）、Externado 大学、Javeriana 大学

**绝不作为权威来源：**维基百科、Grokipedia、社交媒体（尽管 JEP 有活跃的 Twitter/X 账号——引用 JEP 机构自身的 Twitter 仅对特定新闻稿内容属第一层级；实质性决定载于 autos 和 sentencias）。

## 引用格式

JEP 引用遵循哥伦比亚大陆法系惯例。引用格式：

**Macrocasos：**
- 案件 01——Toma de rehenes, graves privaciones de la libertad y otros crímenes（FARC-EP 绑架案）
- 案件 02——Nariño 属地情势
- 案件 03——国家人员将谋杀和强迫失踪呈现为战斗伤亡的案件（“虚假阳性”）
- 案件 04——Urabá 属地情势
- 案件 05——北考卡与南考卡山谷属地情势
- 案件 06——对爱国联盟（UP）成员的受害化
- 案件 07——武装冲突中招募和使用儿童
- 案件 08——Fuerza Pública、其他国家人员或与准军事组织合作实施的罪行
- 案件 09——针对族裔群体的不可赦免罪行
- 案件 10——FARC-EP 实施的罪行（未含于此前 macrocase）
- 案件 11——基于性别的暴力、性暴力与生育暴力，以及基于性取向或多元性别认同的偏见实施的罪行

**一般形式：**
> *[Compareciente(s)]*，**[Macrocaso]**，[机关——Sala/Sección/Tribunal]，[文书类型]，[编号与日期]。

**示范示例：**

- **2025 年 9 月绑架案判决（案件 01）：**
> Jurisdicción Especial para la Paz, Tribunal Especial para la Paz, **Sección de Reconocimiento de Verdad y Responsabilidad**，Sentencia（案件 01——绑架案），**2025 年 9 月 16 日**。

- **2025 年 9 月虚假阳性案判决（案件 03）：**
> Jurisdicción Especial para la Paz, Tribunal Especial para la Paz, **Sección de Reconocimiento de Verdad y Responsabilidad**，Sentencia（案件 03——Costa Caribe 子案、La Popa 军营、巴耶杜帕尔），**2025 年 9 月 18 日**。

- **合宪性裁决：**
> Corte Constitucional de Colombia，Sentencia **C-080 de 2018**（2018 年 8 月 15 日，主审法官 Alejandro Linares Cantillo）——对 JEP 法定法的合宪性审查。

详细惯例参见 `references/citation-format.md`。

## 审计模式取决于文书类型

当用户提供文书时：
- **工作草稿**：审计引用是否准确。macrocase、机关、文书类型、日期均须核验。
- **JEP 最终记录**：盘点并识别程序状态。

无论何种模式，第 0 步（识别 macrocase、机关和文书类型）总是先行。

## 实体法理——指引

本技能不逐行编入法理。以下为起点（每项均通过工作流核验）：

- **属物管辖权** → 2019/2017 年第 1957 号法定法第 5 条：因哥伦比亚国内武装冲突、出于其动机或与之直接或间接相关而实施的严重侵犯人权和违反国际人道法行为
- **属人管辖权** → comparecientes 包括：(i) FARC-EP 前战斗人员；(ii) Fuerza Pública 成员；(iii) 直接或间接参与冲突的第三方平民（terceros civiles）——后者经同意按单独程序处理
- **属时管辖权** → **2016 年 12 月 1 日**（《最终和平协议》过渡条款生效日）之前实施的与冲突相关的罪行
- **不可赦免罪行** → 战争罪、危害人类罪、灭绝种族罪、劫持人质、酷刑、强迫失踪、性暴力及相关行为；招募儿童；杀害受保护人员
- **Sanciones propias** → 对在 Sala de Reconocimiento 完全承认责任者的 5–8 年实际限制自由（非监禁）并附 TOAR
- **Sanciones alternativas** → 对在和平特别法庭迟延承认责任者的 5–8 年实际监禁
- **Sanciones ordinarias** → 对不承认责任者（经对抗程序后由 Sección de Ausencia de Reconocimiento 认定责任时）在普通监狱服最高 20 年监禁
- **条件性制度** → 优惠以真相、赔偿和不重复为条件；违反时可撤销
- **TOAR** → 修复活动；2025 年 9 月判决详细列明对定罪者适用的具体 TOAR 项目（排雷、环境修复、记忆项目、搜寻失踪者、为受害者建设基础设施）
- **被害人参与** → 健全的被害人参与框架，含 *víctimas acreditadas*（经登记的被害人）；为被害人提供司法代理

对每项，均通过工作流核验。

## 敏感背景

哥伦比亚国内武装冲突，约自 1960 年代中期至 2016 年，造成超过 45 万人死亡、逾 700 万人流离失所，所有各方均犯下广泛暴行：FARC-EP（绑架、袭击平民、招募未成年人）；其他游击队（ELN、EPL、M-19）；Fuerza Pública（法外处决/“虚假阳性”、强迫失踪、与准军事组织联合行动）；准军事组织（AUC、AGC 等）；以及其他方。JEP 的修复性正义模式——特别是对应对 21,000 起绑架负责的 FARC-EP 高级指挥官适用非监禁的 sanciones propias——在哥伦比亚**政治上存在争议**。保持事实精确。避免以你自己的口吻将 sanciones propias 定性为“有罪不罚”或“适当”；在相关处反映这一争论的争议性。认识到被害人、FARC-EP、军方、准军事组织幸存者和哥伦比亚公民社会都在阅读这份工作。使用 JEP 自身的术语（如“comparecientes”、“víctimas acreditadas”、“sanciones propias”、“TOAR”）。避免*摩尼教式*简化与虚假对等。

JEP 对许多文书发布 *versiones reservadas*（保密版本）以保护被害人、证人和 *comparecientes*。只引用公开版本并说明，绝不复述保留的识别信息或试图识别受保护参与者——与本套件其他技能对受保护证人适用的公开记录纪律相同。

## 本技能不是什么

- 不是法律意见。输出为研究与起草辅助。
- 不是 JEP 记录的替代品。
- 不是对《最终和平协议》或 JEP 制度选择的政治评价。本技能使 JEP 记录的准确引用成为可能；政治和道德评价留给用户和公共辩论。
- 未经 JEP、哥伦比亚政府或《最终和平协议》任何一方认可。

## 参考文件

- `references/authoritative-sources.md`——来源层级与 URL（jep.gov.co 为主；CEV、UBPD、宪法法院、联合国特派团）
- `references/citation-format.md`——哥伦比亚大陆法系引用惯例、11 个 macrocase 表格、机关称谓（Salas de Justicia、和平特别法庭、UIA）、文书类型
- `references/verification-workflow.md`——降级阶梯、JEP 特有陷阱（sanciones propias ≠ 有罪不罚；macrocaso 与案件；2017 年转型后 FARC ≠ FARC-EP；Sala de Reconocimiento 与和平特别法庭；2025 年 9 月历史性判决）
- `references/foundational-texts.md`——2016 年《最终和平协议》、2017 年 1 号宪法修正案、2019 年第 1957 号法定法、2018 年第 1922 号法律、《总章程》、哥伦比亚宪法法院 2018 年 C-080 号判决
- `references/jurisprudence-map.md`——JEP 裁定的逐主题图谱（截至 2026 年有限——首批判决仅为 2025 年 9 月；此前主要为结构和程序性决定）
- `examples/example-verification.md`——核验案件 01（绑架案）2025 年 9 月判决
- `examples/example-audit.md`——审计用户提供的文书（sanciones propias 与监禁刑；FARC 与 FARC-EP）

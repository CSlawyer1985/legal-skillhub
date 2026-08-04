# 变更日志——JEP 技能

## [1.0.3] — 2026-06-02

### 修复
- `references/jurisprudence-map.md`：四个新增 macrocase（案件 08-11）于 **2022–2023 年**开庭（案件 11 于 2023 年 9 月），而非“2022 年”。

## [1.0.2] — 2026-06-02

### 变更
- 弱化了 `SKILL.md` 中过度自信的可靠性表述（“对 jep.gov.co 的检索总能成功”），承认直接抓取可能失败（HTTP 403、超时、PDF 无法渲染），且此类失败是结构性的、非致命的——应指向降级阶梯，而非将成功抓取视为必然。使 JEP 技能与全仓库的直接抓取失败姿态（`CLAUDE.md` 第 3 节）保持一致。

## [1.0.1] — 2026-05-30

### 修复
- 更正了 `references/jurisprudence-map.md` 中对 `Auto 033 de 2021` 的描述：它是案件 03 的**优先处理**命令（2021 年 2 月 12 日，对六个子案优先排序），而非“事实与行为认定，Antioquia 子案”。为案件 03 的各个命令补充了日期，并对照 jep.gov.co 核实了 `Auto 128 de 2021`（Costa Caribe，La Popa 军营）。

## [1.0.0] — 首次发布

### 新增
- `SKILL.md`——入口、验证优先纪律、标准工作流（第 0 步识别 macrocase + 机关 + 文书类型）、制度架构（SIVJRNR；JEP + CEV + UBPD；宪法锚定；2018 年启动；2025 年 9 月首批判决）、来源层级、含 11 个 macrocase 表格的引用格式、主要机关（3 个 Salas de Justicia + 和平特别法庭下设 4 个 Secciones + UIA + Sala Plena）、三类制裁制度（propias / alternativas / ordinarias）、实体法理要点（属物/属时/属人管辖权；不可赦免罪行；TOAR；条件性制度；被害人参与）、敏感背景（52 年冲突、45 万余人遇害、修复性正义在政治上存在争议）
- `references/authoritative-sources.md`——第一层级（jep.gov.co 为主、CEV、UBPD、宪法法院、联合国核查团），第二层级（Dejusticia、Kai Ambos、Uprimny、García Villegas；《El Espectador》、《La Silla Vacía》、《Razón Pública》；Mark Kersten、Naomi Roht-Arriaza、EJIL:Talk!；CINEP、Hacemos Memoria、Colombia Check）、语言说明（西班牙语为权威语言）
- `references/foundational-texts.md`——《最终和平协议》（Acuerdo Final，2016 年 11 月 24 日，第 5 点）、2017 年 1 号宪法修正案（Acto Legislativo 01 de 2017，2017 年 4 月 4 日，过渡性条款第 5–18 条）、**2019 年第 1957 号法定法（Ley Estatutaria 1957 de 2019）**（2019 年 6 月 6 日；第 1 条、第 5 条属物管辖权、第 6 条条件性、第 8 条属时管辖、第 16 条不可赦免、第 19 条结构、第 79 条 SRVR、第 89 条特别法庭、第 125–145 条制裁、第 143 条 propias 制裁）、2018 年第 1922 号法律（Ley 1922 de 2018，RPP）、《总章程》（Reglamento General）、宪法法院 C-674/2017 与 C-080/2018 号判决、《刑法典》（Ley 599/2000）、国际文书（《罗马规约》、《日内瓦公约》及其第一、第二附加议定书等）
- `references/citation-format.md`——哥伦比亚大陆法系惯例、11 个 macrocase 表格（案件 01–11 及主题）、机关称谓（Salas de Justicia：SRVR/SDSJ/SAI；和平特别法庭：4 个 Secciones）、文书类型（Auto/Providencia/Resolución/Sentencia/Lineamiento/Comunicado）、案件 01 与案件 03 2025 年 9 月判决的示范示例、comparecientes 称谓惯例（FARC-EP vs FARC vs Comunes；Fuerza Pública；第三方平民）
- `references/verification-workflow.md`——降级阶梯（jep.gov.co → CEV → 宪法法院 → 联合国特派团 → 第二层级）、**7 个 JEP 特有陷阱**：(1) sanciones propias ≠ 有罪不罚，(2) macrocaso ≠ subcaso，(3) FARC ≠ FARC-EP 属时术语，(4) Sala de Reconocimiento ≠ Sección de Reconocimiento，(5) 2025 年 9 月判决具有历史意义（此前仅有 autos/providencias），(6) 西班牙语为程序语言，(7) 将修复性正义适用于不可赦免罪行是制度创新而非赦免
- `references/jurisprudence-map.md`——7 个部分：制度架构、合宪性审查（C-674/2017、C-080/2018）、11 个 macrocase 的开庭与优先排序、**2025 年 9 月首批判决**（案件 01 绑架案 9 月 16 日——7 名前 FARC-EP 秘书处成员，涉 21,936 起绑架——sanciones propias 5–8 年 + 35,762 百万比索 TOAR；案件 03 Costa Caribe 子案 9 月 18 日——巴耶杜帕尔前“La Popa”军营 12 名成员，涉 135 起法外处决——sanciones propias 5–8 年 + 86,096 百万比索 TOAR；合计 1,247 页）、此前命令（Autos 19/2021、033/2021、128/2021）、新兴法理（macrocrimalidad、指挥官责任、条件性、被害人参与）、进行中的工作（案件 02–11 的状态）
- `examples/example-verification.md`——对 2025 年 9 月 16 日案件 01 判决的核验，同时处理 5 个陷阱（sanciones propias = 技术词汇；FARC-EP；Sección 而非 Sala；判决而非命令；修复性而非赦免）
- `examples/example-audit.md`——两项审计：sanciones propias 被错误定性为“赦免/有罪不罚”；Sala 与 Sección 混淆 + FARC 与 FARC-EP 术语错误

### v1.0.0 的技能范围
- 覆盖 JEP 从起源（2016 年《最终和平协议》、2017 年 1 号宪法修正案、1957/2019 年法定法）到首批定罪判决（2025 年 9 月）及进行中工作（2026 年）的全过程
- 编入与仓库其他技能相同的验证优先方法论
- 专门针对 JEP 的特殊性配置：对不可赦免罪行的修复性正义、带 TOAR 的 sanciones propias、条件性制度、权威西班牙语、属时术语（FARC-EP vs FARC vs Comunes）、Sala/Sección 区分
- 绘出首批判决（案件 01 绑架案与案件 03 Costa Caribe 子案）并映射其余 9 个 macrocase 截至 2026 年的状态

### 已知局限
- JEP 是一个**活跃的、处于法理构建中的司法辖区**——引用前须在 jep.gov.co 核验每个案件的状态
- JEP 的判决卷帙浩繁（前两份判决合计 1,247 页）；本技能不逐行编入实质性内容——精确引用时须取回全文
- 哥伦比亚围绕 JEP 的政治争论激烈且两极分化；本技能绘出争议性质，但将规范性评价留给用户
- JEP 裁决的英文翻译（稀少，或由 JEP 自身提供，或由 JusticeInfo、EJIL:Talk!、CNN 等第三方提供）为自由翻译、不具权威性——应引用西班牙语版本，并提供明确标识为自由翻译的译文
- 案件 02、04、05（属地性案件）及案件 06–11（专题性案件）处于不同阶段；其未来判决将发展法理，需要 v1.1 版本
- JEP-CEV 与 JEP-UBPD 的衔接仍在发展；本技能指出协调点，但不逐案描绘关系

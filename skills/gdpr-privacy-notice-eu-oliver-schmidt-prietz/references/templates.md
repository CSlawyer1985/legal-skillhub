# 隐私声明文档模板

用于 .docx 生成。始终先加载 docx 生成技能（Claude.ai Projects 中的 `/mnt/skills/public/docx/SKILL.md`，或 Claude Code 中的 `docx-processing-anthropic` 技能）。如无 docx 技能可用，则生成格式良好的 Markdown 作为后备。

使用 `docx-js`（npm）。页面尺寸：A4（11906 x 16838 DXA）。字体：Arial。所有表格宽度以 DXA 为单位。

---

## 页面与样式规格

### 页面布局

- **页面尺寸**：A4 —— 宽：11906 DXA，高：16838 DXA
- **页边距**：上/下：1134 DXA（2 厘米），左/右：1418 DXA（2.5 厘米）
- **内容宽度**：9070 DXA（页面宽度减去左右页边距）

### 配色方案

| 令牌 | 十六进制 | 用途 |
|-------|-----|-------|
| `primary` | `1B3A5C` | 深藏青色——标题（H1）、文档标题、加粗强调 |
| `accent` | `2E86AB` | 青绿色——H2/H3 标题、副标题、分隔线 |
| `lightBg` | `EDF4F8` | 极浅蓝——表头单元格底纹 |
| `medBg` | `D6E8F2` | 中蓝——强调行（如需） |
| `border` | `B0C4D8` | 柔和蓝灰——表格边框 |
| `text` | `2D2D2D` | 近黑色——正文 |
| `muted` | `5A6977` | 灰色——次要信息、占位符、页脚 |
| `white` | `FFFFFF` | 白色背景 |
| `alertBg` | `FFF3E0` | 暖色高亮——第21条异议框背景 |
| `alertBorder` | `E65100` | 橙色——第21条异议框边框和标题 |

### 排版

| 元素 | 字体 | 字号（半磅值） | 样式 | 颜色 |
|---------|------|---------------------|-------|-------|
| 文档标题 | Arial | 40 | 加粗 | `primary` |
| 副标题 | Arial | 26 | 常规 | `accent` |
| 最后更新 | Arial | 20 | 斜体 | `muted` |
| 一级标题 | Arial | 28 | 加粗 | `primary` |
| 二级标题 | Arial | 24 | 加粗 | `accent` |
| 三级标题 | Arial | 22 | 加粗 | `accent` |
| 正文 | Arial | 21 | 常规 | `text` |
| 表头 | Arial | 19 | 加粗 | `primary` |
| 表格正文 | Arial | 19 | 常规 | `text` |
| 占位文本 | Arial | 19 | 斜体 | `muted` |
| 页眉（运行中） | Arial | 16 | 斜体 | `muted` |
| 页脚 | Arial | 16 | 常规 | `muted` |
| 第21条框标题 | Arial | 22 | 加粗 | `alertBorder` |
| 第21条框正文 | Arial | 20 | 常规 | `text` |

### 标题样式（用于目录大纲级别）

- 一级标题：outlineLevel 0，段前间距 360 / 段后间距 120
- 二级标题：outlineLevel 1，段前间距 240 / 段后间距 80
- 三级标题：outlineLevel 2，段前间距 200 / 段后间距 60
- 正文：段前间距 60 / 段后间距 120，行距 276

### 表格格式

- **边框**：SINGLE，尺寸 1，颜色 `border`（`B0C4D8`）
- **表头行底纹**：填充 `lightBg`（`EDF4F8`），类型 CLEAR
- **单元格边距**：上 60，下 60，左 100，右 100
- **项目符号列表**：LevelFormat.BULLET，文本 `•`，左缩进 720 / 悬挂缩进 360

---

## 文档结构

### 封面/标题块

居中布局：
1. 空占位段落（段前间距 600）
2. **文档标题**——例如 "Datenschutzerklaerung" / "Politique de confidentialite" / "Privacy Notice"
3. **副标题**——公司名称占位符
4. **最后更新**——日期占位符，斜体
5. **分隔线**——单单元格表格，仅底部边框（尺寸 2，颜色 `accent`），占满内容宽度

### 目录

自动生成的 `TableOfContents`，带超链接，标题样式范围 1-2。其后接分页符。

### 页眉（每页）

右对齐，斜体，muted 色："[文档标题] — [公司名称]"

### 页脚（每页）

居中，muted 色："[最后更新标签]：[日期] — 第 {页码} 页"

---

## 13 节结构

### 第 1 节：控制者

- 一级标题：节标题
- 引言段落
- 公司详情块：公司名称（加粗）、地址、代表人、登记信息、邮箱、电话——均作为独立正文段落
- **子标题（H2）**：DPO 标签
- DPO 引言文本
- DPO 联系占位符（斜体，muted 色）

### 第 2 节：我们收集的数据

- 一级标题：节标题
- 引言段落
- 数据类别项目符号列表（占位项，斜体，muted 色）：
  - 身份数据
  - 联系数据
  - 技术数据
  - 使用数据
  - 交易数据

### 第 3 节：目的、法律依据与保留期限

- 一级标题：节标题
- 引言段落
- **目的表**——4 列，占满内容宽度：

| 列 | 约宽（DXA） |
|--------|---------------------|
| 目的 | 2200 |
| 数据类别 | 2200 |
| 法律依据 | 2470 |
| 保留期限 | 2200 |

- 表头行使用 `lightBg` 底纹
- 3 行占位数据行（斜体，muted 色 `[...]`）

### 第 4 节：接收方

- 一级标题：节标题
- 引言段落
- 接收方类别项目符号列表（占位，斜体，muted 色）：
  - 托管
  - 支付
  - 分析
  - 电子邮件/营销
  - AI 服务

### 第 5 节：国际传输

- 一级标题：节标题
- 引言段落
- 项目符号列表：国家 + 机制占位符（斜体，muted 色）

### 第 6 节：保留期限

- 注：保留期限已涵盖在第 3 节表格中。本节可根据用户偏好省略，或用作对第 3 节的交叉引用。

### 第 7 节：您的权利

- 一级标题：节标题
- 引言段落
- 8 项权利的项目符号列表（常规文本，非 muted 色——这些是实体性内容）：
  1. 访问权（第15条）
  2. 更正权（第16条）
  3. 删除权（第17条）
  4. 限制处理权（第18条）
  5. 数据可携权（第20条）
  6. 反对权（第21条）——引用下方专用框
  7. 撤回同意（第7条第(3)款）
  8. 提出投诉（第77条）
- 行使段落：联系邮箱，一个月内回复
- 监管机关：名称（加粗）、地址、URL

### 第 21 条异议框（第 7 节之后）

**视觉上醒目的框**——实现为单单元格表格：
- **左边框**：尺寸 8，颜色 `alertBorder`（`E65100`）
- **其他边框**：尺寸 3，颜色 `alertBorder`
- **背景**：`alertBg`（`FFF3E0`），ShadingType.CLEAR
- **单元格边距**：上/下 120，左/右 200
- **内容**：
  1. 框标题（加粗，`alertBorder` 色）
  2. 第 1 段：基于合法利益的异议权
  3. 第 2 段：直接营销的异议权
  4. 第 3 段：异议的后果

依 GDPR 第21条第(4)款，此框必须**独立且醒目**。

### 第 8 节：Cookie 与跟踪

- 一级标题：节标题
- 引言段落
- **Cookie 表**——5 列，占满内容宽度：

| 列 | 约宽（DXA） |
|--------|---------------------|
| 类别 | 1600 |
| 工具/提供者 | 1800 |
| 目的 | 2070 |
| 持续时间 | 1400 |
| 法律依据 | 2200 |

- 表头行使用 `lightBg` 底纹
- 占位数据行

### 第 9 节：AI 处理与自动化决策

- 一级标题：节标题
- 引言段落
- **AI 表**——4 列，占满内容宽度：

| 列 | 约宽（DXA） |
|--------|---------------------|
| AI 系统/技术 | 2200 |
| 目的 | 2600 |
| 决策类型 | 2270 |
| 法律依据 | 2000 |

- 表头行使用 `lightBg` 底纹
- 占位数据行
- 第22条权利段落

### 第 10 节：数据安全

- 一级标题：节标题
- 正文段落（引用第32条、技术组织措施 TOMs、定期审查）

### 第 11 节：儿童数据

- 一级标题：节标题
- 正文段落（年龄门槛占位符、删除承诺）

### 第 12 节：本通知的变更

- 一级标题：节标题
- 正文段落（更新权利、网站现行版本、重大变更通知）

### 第 13 节：联系方式

- 一级标题：节标题
- 联系引言段落
- 公司名称（加粗）、地址、邮箱、电话

---

## 多语言支持

模板支持三种语言。使用与目标司法辖区匹配的语言。所有节标题、引言文本、表头、占位符标签和第21条框文本都必须使用目标语言。

### 德语（DE）

**节标题：**
| 节 | 标题 |
|---------|---------|
| 标题 | Datenschutzerklaerung |
| 1 | 1. Verantwortlicher |
| 2 | 2. Welche Daten wir erheben |
| 3 | 3. Zwecke, Rechtsgrundlagen und Speicherdauer |
| 4 | 4. Empfaenger Ihrer Daten |
| 5 | 5. Datenuebermittlung in Drittstaaten |
| 6 | 6. Speicherdauer |
| 7 | 7. Ihre Rechte |
| 第21条 | Widerspruchsrecht (Art. 21 DSGVO) |
| 8 | 8. Cookies und Tracking |
| 9 | 9. KI-gestuetzte Verarbeitung und automatisierte Entscheidungen |
| 10 | 10. Datensicherheit |
| 11 | 11. Daten von Minderjaehrigen |
| 12 | 12. Aenderungen dieser Datenschutzerklaerung |
| 13 | 13. Kontakt |

**表头：**
- 目的：Zweck | Betroffene Daten | Rechtsgrundlage | Speicherdauer
- Cookie：Kategorie | Tool / Anbieter | Zweck | Speicherdauer | Rechtsgrundlage
- AI：KI-System / Technologie | Zweck | Art der Entscheidung | Rechtsgrundlage

**关键文本：**
- 控制者引言："Verantwortlich im Sinne der Datenschutz-Grundverordnung (DSGVO) ist:"
- DPO 标签："Datenschutzbeauftragter"
- 权利引言："Die DSGVO gewaehrt Ihnen umfassende Rechte in Bezug auf Ihre personenbezogenen Daten:"
- 权利行使："Zur Ausuebung Ihrer Rechte wenden Sie sich bitte an: [KONTAKT-E-MAIL]. Wir werden Ihre Anfrage innerhalb eines Monats beantworten."
- 页眉："Datenschutzerklaerung -- [Firmenname]"
- 页脚前缀："Stand: [DATUM] -- Seite "
- 占位符：[Firmenname GmbH / AG / SE], [Strasse Nr., PLZ Ort], Vertreten durch: [Geschaeftsfuehrer/Vorstand], Registergericht: [Amtsgericht], HRB [Nr.]

**第 21 条框（DE）：**
1. "Soweit wir Ihre personenbezogenen Daten auf Grundlage unseres berechtigten Interesses (Art. 6 Abs. 1 lit. f DSGVO) verarbeiten, haben Sie das Recht, aus Gruenden, die sich aus Ihrer besonderen Situation ergeben, jederzeit Widerspruch gegen diese Verarbeitung einzulegen."
2. "Werden Ihre personenbezogenen Daten verarbeitet, um Direktwerbung zu betreiben, haben Sie das Recht, jederzeit Widerspruch gegen die Verarbeitung Sie betreffender personenbezogener Daten zum Zwecke derartiger Werbung einzulegen. Dies gilt auch fuer das Profiling, soweit es mit solcher Direktwerbung in Verbindung steht."
3. "Im Falle Ihres Widerspruchs verarbeiten wir Ihre personenbezogenen Daten nicht mehr fuer diese Zwecke, es sei denn, wir koennen zwingende schutzwuerdige Gruende nachweisen, die Ihre Interessen, Rechte und Freiheiten ueberwiegen, oder die Verarbeitung dient der Geltendmachung, Ausuebung oder Verteidigung von Rechtsanspruechen."

**权利清单（DE）：**
- Auskunft (Art. 15 DSGVO): Bestaetigung, ob und welche Daten ueber Sie verarbeitet werden, sowie eine kostenlose Kopie.
- Berichtigung (Art. 16 DSGVO): Unverzuegliche Korrektur unrichtiger oder Vervollstaendigung unvollstaendiger Daten.
- Loeschung (Art. 17 DSGVO): Loeschung Ihrer Daten, sofern kein gesetzlicher Aufbewahrungsgrund entgegensteht.
- Einschraenkung (Art. 18 DSGVO): Voruebergehende Einschraenkung der Verarbeitung unter bestimmten Voraussetzungen.
- Datenuebertragbarkeit (Art. 20 DSGVO): Herausgabe Ihrer Daten in einem gaengigen, maschinenlesbaren Format.
- Widerspruch (Art. 21 DSGVO): Widerspruch gegen die Verarbeitung auf Basis berechtigter Interessen -- siehe gesonderten Hinweis unten.
- Widerruf der Einwilligung (Art. 7 Abs. 3 DSGVO): Jederzeit moeglich, ohne dass die Rechtmaessigkeit der bis dahin erfolgten Verarbeitung beruehrt wird.
- Beschwerderecht (Art. 77 DSGVO): Sie haben das Recht, sich bei einer Datenschutzaufsichtsbehoerde zu beschweren.

**正文文本（DE）：**
- 数据引言："Im Rahmen der Nutzung unseres [Angebots/Dienstes/Webseite] verarbeiten wir folgende Kategorien personenbezogener Daten:"
- 目的引言："Die nachfolgende Tabelle gibt Ihnen einen Ueberblick ueber die Verarbeitungszwecke, die jeweilige Rechtsgrundlage und die Speicherdauer."
- 接收方引言："Zur Erfuellung der oben genannten Zwecke koennen Ihre personenbezogenen Daten an folgende Kategorien von Empfaengern uebermittelt werden:"
- 传输引言："Einige unserer Dienstleister koennen ihren Sitz ausserhalb des Europaeischen Wirtschaftsraums (EWR) haben. In diesem Fall stellen wir durch geeignete Garantien sicher, dass ein angemessenes Datenschutzniveau gewaehrleistet ist:"
- Cookie 引言："Unser [Angebot/Webseite] verwendet Cookies und aehnliche Technologien. Die nachfolgende Tabelle gibt Ihnen einen Ueberblick:"
- AI 引言："Wir setzen im Rahmen unseres [Angebots/Dienstes] automatisierte Verarbeitungstechnologien ein, darunter Verfahren der kuenstlichen Intelligenz (KI). Im Folgenden informieren wir Sie ueber Art, Umfang und Zweck dieser Verarbeitung."
- AI 权利："Soweit automatisierte Entscheidungen Ihnen gegenueber rechtliche Wirkung entfalten oder Sie in aehnlicher Weise erheblich beeintraechtigen (Art. 22 DSGVO), haben Sie das Recht auf Eingreifen einer Person, auf Darlegung Ihres Standpunkts und auf Anfechtung der Entscheidung."
- 安全："Wir treffen angemessene technische und organisatorische Massnahmen gemaess Art. 32 DSGVO, um Ihre Daten vor unbefugtem Zugriff, Verlust, Zerstoerung oder Veraenderung zu schuetzen. Diese Massnahmen werden regelmaessig ueberprueft und dem Stand der Technik angepasst."
- 儿童："Unser [Angebot/Dienst] richtet sich grundsaetzlich nicht an Personen unter [16] Jahren. Sollten wir feststellen, dass Daten von Minderjaehrigen ohne die erforderliche Einwilligung der Erziehungsberechtigten erhoben wurden, werden diese unverzueglich geloescht."
- 变更："Wir behalten uns vor, diese Datenschutzerklaerung bei Bedarf anzupassen, um sie an geaenderte Rechtslage oder bei Aenderungen unseres Dienstes bzw. der Datenverarbeitung anzupassen. Die jeweils aktuelle Fassung finden Sie stets auf unserer Webseite. Bei wesentlichen Aenderungen werden wir Sie gesondert informieren."
- 联系："Bei Fragen zur Verarbeitung Ihrer personenbezogenen Daten oder zur Ausuebung Ihrer Rechte erreichen Sie uns unter:"

### 法语（FR）

**节标题：**
| 节 | 标题 |
|---------|---------|
| 标题 | Politique de confidentialite |
| 1 | 1. Responsable du traitement |
| 2 | 2. Donnees que nous collectons |
| 3 | 3. Finalites, bases legales et durees de conservation |
| 4 | 4. Destinataires de vos donnees |
| 5 | 5. Transferts hors de l'Union europeenne |
| 6 | 6. Durees de conservation |
| 7 | 7. Vos droits |
| 第21条 | Droit d'opposition (Art. 21 RGPD) |
| 8 | 8. Cookies et traceurs |
| 9 | 9. Traitement par intelligence artificielle et decisions automatisees |
| 10 | 10. Securite des donnees |
| 11 | 11. Donnees des mineurs |
| 12 | 12. Modifications de cette politique |
| 13 | 13. Contact |

**表头：**
- 目的：Finalite | Donnees concernees | Base legale | Duree de conservation
- Cookie：Categorie | Outil / Fournisseur | Finalite | Duree | Base legale
- AI：Systeme IA / Technologie | Finalite | Type de decision | Base legale

**关键文本：**
- 控制者引言："Le responsable du traitement de vos donnees personnelles est :"
- DPO 标签："Delegue a la protection des donnees"
- 权利引言："Le RGPD vous confere des droits etendus sur vos donnees personnelles :"
- 权利行使："Pour exercer vos droits, adressez votre demande a : [E-MAIL DE CONTACT]. Nous repondrons dans un delai d'un mois."
- 监管机关："L'autorite de controle competente est :"（默认：CNIL，3 Place de Fontenoy, TSA 80715, 75334 Paris Cedex 07, www.cnil.fr）
- 页眉："Politique de confidentialite -- [Nom de l'entreprise]"
- 页脚前缀："Derniere mise a jour : [DATE] -- Page "
- 占位符：[Denomination sociale, forme juridique], [Adresse du siege social], Representee par : [Nom], [Qualite], Immatriculee au RCS de [ville] sous le n. [SIREN/SIRET]

**第 21 条框（FR）：**
1. "Lorsque nous traitons vos donnees personnelles sur la base de notre interet legitime (Art. 6.1.f RGPD), vous avez le droit de vous y opposer a tout moment pour des raisons tenant a votre situation particuliere."
2. "Si vos donnees personnelles sont traitees a des fins de prospection commerciale, vous pouvez vous y opposer a tout moment, sans avoir a justifier de motifs particuliers. Il en va de meme pour le profilage lie a cette prospection."
3. "En cas d'opposition, nous cesserons de traiter vos donnees a ces fins, sauf si nous demontrons l'existence de motifs legitimes et imperieux prevalant sur vos interets, droits et libertes, ou si le traitement est necessaire a la constatation, l'exercice ou la defense de droits en justice."

**权利清单（FR）：**
- Acces (Art. 15 RGPD) : obtenir la confirmation que vos donnees sont traitees et en recevoir une copie.
- Rectification (Art. 16 RGPD) : faire corriger des donnees inexactes ou incompletes.
- Effacement (Art. 17 RGPD) : obtenir la suppression de vos donnees dans les cas prevus par la loi.
- Limitation (Art. 18 RGPD) : suspendre temporairement l'utilisation de certaines donnees.
- Portabilite (Art. 20 RGPD) : recuperer vos donnees dans un format structure et couramment utilise.
- Opposition (Art. 21 RGPD) : vous opposer au traitement fonde sur l'interet legitime -- voir l'encadre ci-dessous.
- Retrait du consentement (Art. 7.3 RGPD) : a tout moment, sans remettre en cause la liceite du traitement effectue avant le retrait.
- Reclamation (Art. 77 RGPD) : introduire une reclamation aupres de la CNIL.

**正文文本（FR）：**
- 数据引言："Dans le cadre de l'utilisation de notre [service/site web], nous traitons les categories de donnees personnelles suivantes :"
- 目的引言："Le tableau suivant vous donne un apercu des finalites de traitement, de la base legale applicable et de la duree de conservation."
- 接收方引言："Pour la realisation des finalites decrites ci-dessus, vos donnees personnelles peuvent etre communiquees aux categories de destinataires suivantes :"
- 传输引言："Certains de nos prestataires peuvent etre etablis en dehors de l'Espace economique europeen (EEE). Dans ce cas, nous veillons a ce que des garanties appropriees soient mises en place :"
- Cookie 引言："Notre [site web/service] utilise des cookies et technologies similaires. Le tableau suivant vous en donne un apercu :"
- AI 引言："Nous utilisons dans le cadre de notre [service] des technologies de traitement automatise, y compris des procedes d'intelligence artificielle (IA). Vous trouverez ci-dessous les informations sur la nature, la portee et la finalite de ces traitements."
- AI 权利："Lorsqu'une decision automatisee produit des effets juridiques ou vous affecte de maniere significative (Art. 22 RGPD), vous disposez du droit d'obtenir une intervention humaine, d'exprimer votre point de vue et de contester la decision."
- 安全："Nous mettons en oeuvre des mesures techniques et organisationnelles appropriees conformement a l'Art. 32 RGPD pour proteger vos donnees contre tout acces non autorise, perte, destruction ou alteration. Ces mesures sont regulierement reevaluees et adaptees a l'etat de l'art."
- 儿童："Notre [service] ne s'adresse pas en principe aux personnes de moins de [15] ans. Si nous constatons que des donnees de mineurs ont ete collectees sans le consentement requis du titulaire de l'autorite parentale, elles seront supprimees sans delai."
- 变更："Nous nous reservons le droit de modifier cette politique a tout moment pour l'adapter a l'evolution de la reglementation ou de nos pratiques. La version en vigueur est toujours disponible sur notre site. En cas de modification substantielle, nous vous en informerons de maniere appropriee."
- 联系："Pour toute question relative au traitement de vos donnees personnelles ou a l'exercice de vos droits, vous pouvez nous contacter :"

### 英语（EN）

**节标题：**
| 节 | 标题 |
|---------|---------|
| 标题 | Privacy Notice |
| 1 | 1. Data Controller |
| 2 | 2. Data We Collect |
| 3 | 3. Purposes, Legal Bases, and Retention Periods |
| 4 | 4. Recipients of Your Data |
| 5 | 5. International Data Transfers |
| 6 | 6. Retention Periods |
| 7 | 7. Your Rights |
| 第21条 | Right to Object (Art. 21 GDPR) |
| 8 | 8. Cookies and Tracking Technologies |
| 9 | 9. AI Processing and Automated Decision-Making |
| 10 | 10. Data Security |
| 11 | 11. Children's Data |
| 12 | 12. Changes to This Notice |
| 13 | 13. Contact |

**表头：**
- 目的：Purpose | Data Categories | Legal Basis | Retention Period
- Cookie：Category | Tool / Provider | Purpose | Duration | Legal Basis
- AI：AI System / Technology | Purpose | Decision Type | Legal Basis

**关键文本：**
- 控制者引言："The controller responsible for processing your personal data is:"
- DPO 标签："Data Protection Officer"
- 权利引言："Under the GDPR, you have the following rights regarding your personal data:"
- 权利行使："To exercise your rights, please contact: [CONTACT EMAIL]. We will respond within one month."
- 页眉："Privacy Notice -- [Company Name]"
- 页脚前缀："Last updated: [DATE] -- Page "
- 占位符：[Company Name, Legal Form], [Registered Address], Represented by: [Name], [Title], Registration: [Registry], [Number]

**第 21 条框（EN）：**
1. "Where we process your personal data on the basis of our legitimate interest (Art. 6(1)(f) GDPR), you have the right to object at any time on grounds relating to your particular situation."
2. "Where your personal data is processed for direct marketing purposes, you have the right to object at any time, without needing to provide specific reasons. This also applies to profiling insofar as it is related to such direct marketing."
3. "In the event of your objection, we will cease processing your data for these purposes, unless we can demonstrate compelling legitimate grounds that override your interests, rights and freedoms, or the processing serves the establishment, exercise or defence of legal claims."

**权利清单（EN）：**
- Access (Art. 15 GDPR): Obtain confirmation of whether your data is processed and receive a copy.
- Rectification (Art. 16 GDPR): Have inaccurate or incomplete data corrected without undue delay.
- Erasure (Art. 17 GDPR): Request deletion of your data where legally permissible.
- Restriction (Art. 18 GDPR): Request temporary restriction of processing under certain conditions.
- Data Portability (Art. 20 GDPR): Receive your data in a structured, commonly used, machine-readable format.
- Object (Art. 21 GDPR): Object to processing based on legitimate interests -- see dedicated section below.
- Withdraw Consent (Art. 7(3) GDPR): At any time, without affecting the lawfulness of prior processing.
- Lodge a Complaint (Art. 77 GDPR): File a complaint with the competent supervisory authority.

**正文文本（EN）：**
- 数据引言："In connection with your use of our [service/website], we process the following categories of personal data:"
- 目的引言："The following table provides an overview of the processing purposes, the applicable legal basis, and the retention period."
- 接收方引言："To fulfil the purposes described above, your personal data may be disclosed to the following categories of recipients:"
- 传输引言："Some of our service providers may be established outside the European Economic Area (EEA). In such cases, we ensure appropriate safeguards are in place:"
- Cookie 引言："Our [website/service] uses cookies and similar technologies. The following table provides an overview:"
- AI 引言："We use automated processing technologies, including artificial intelligence (AI), in connection with our [service]. Below we inform you about the nature, scope, and purpose of this processing."
- AI 权利："Where an automated decision produces legal effects or similarly significantly affects you (Art. 22 GDPR), you have the right to obtain human intervention, express your point of view, and contest the decision."
- 安全："We implement appropriate technical and organisational measures pursuant to Art. 32 GDPR to protect your data against unauthorised access, loss, destruction, or alteration. These measures are regularly reviewed and adapted to the state of the art."
- 儿童："Our [service] is generally not directed at persons under [16] years of age. If we become aware that data of minors has been collected without the required parental consent, it will be deleted without undue delay."
- 变更："We reserve the right to update this notice at any time to reflect changes in legislation or our practices. The current version is always available on our website. We will notify you of material changes in an appropriate manner."
- 联系："If you have any questions about the processing of your personal data or wish to exercise your rights, you can reach us at:"

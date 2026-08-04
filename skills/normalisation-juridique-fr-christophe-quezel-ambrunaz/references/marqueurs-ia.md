# 法语中"AI"写作痕迹——检测与处理

本文件指导**判断工序**。目的不是按原则根除某些结构，而是消除生成文本特有的**拖沓**和**习惯性套式**，同时不削弱合法的法律行文。决定性标准几乎总是**语义空洞**：如果删去该片段而论证毫无损失，那就是填充。

## 目录

1. 直引号和直撇号（确定性）
2. 长破折号：保留与间距
3. "et" 前的逗号（视情境——绝不机械处理）
4. 空洞的三段式节奏
5. 空洞的强调套语
6. 膨胀的形容词和最高级
7. 过多的连接词
8. 元文本习惯
9. 填充性对偶与排比

---

## 1. 直撇号和直引号——*确定性（脚本）*

直撇号 `'` 和直引号 `"…"` 是机器来源的标志。脚本将其转换为弯撇号 `’` 和法语引号 `« … »`。参见 `typographie.md`。无需判断操作。

## 2. 长破折号——*保留*

长破折号 `—` **保留**（用户的选择）。AI 标志不是破折号本身，而是 (a) 其**密度**和 (b) 英式间距（`mot—mot`）。脚本规范化间距（`mot — mot`，破折号前用不换行空格）。仅当**密度**明显过高时才在判断中干预（每句多个插入语）：此时将部分插入语转换为括号或从句，但不要全部统一。绝不用其他符号替换破折号。

## 3. "et" 前的逗号——*视情境，绝不机械处理*

法语默认规则：并列两个同主语术语或从句的 *et* 前**不加逗号**。

> Le contrat est formé, et les parties sont engagées. → Le contrat est formé et les parties sont engagées.（合同已成立，且当事方已受约束。）

**逗号合法且应保留的情形：**
- **主语不同**的从句：「Le débiteur s'exécutera, et le créancier donnera quittance.」（债务人将履行，而债权人将出具收据。）
- 紧接 *et* 前的**插入语收尾**：「Le juge, après débats, et sans renvoi, statue.」（法官在辩论后，不作发回，作出裁判。）
- **「…, et ce, …」** 结构：「Il doit réparer, et ce, intégralement.」（他必须修复，而且是完全修复。）
- 强调性**多连词**（*et… et… et*）。
- *Et* 引出**语义不同或结论性**的从句：「Les délais ont couru, et l'action est prescrite.」（期限已届满，因此诉讼已过时效。）

仅移除两个简单并列元素之间**错误的**逗号。如有疑问，保留。

## 4. 空洞的三段式节奏

三连结构（tricolon）是经典手法，常常很出色。只收紧**公式化且空洞**的三连结构，其特征是成分冗余或可互换。

- ❌ 空洞：「une analyse rigoureuse, précise et minutieuse」（严谨、精确且细致的分析——三个形容词说的是一回事）→ 「une analyse rigoureuse」。
- ❌ 空洞：「comprendre, analyser et appréhender la question」（理解、分析和把握问题）→ 「analyser la question」。
- ✅ 实质：「la formation, l'exécution et l'extinction du contrat」（合同的订立、履行和消灭——三个不同阶段）→ **保留**。

提示：「…, et ce de manière X」后缀或 *-ment* 副词三连。删除拖沓，保留信息。

## 5. 空洞的强调套语

不添加任何内容且暴露自动生成的引导套语。**删除**或融入句子：

- 「Il convient de souligner / noter / rappeler / préciser que…」（应当强调/注意/回顾/明确……）→ 删除引导语，直接陈述事实。
- 「Il importe de relever que…」、「Notons que…」、「On notera que…」、「Il est à noter que…」（须指出……/我们注意到……）。
- 「Force est de constater que…」（不得不承认……）（容忍一次；禁止重复）。
- 「Il ne fait aucun doute que…」、「Il va sans dire que…」（毫无疑问……/不言而喻……）。
- 「joue un rôle clé / central / déterminant」（起关键/核心/决定性作用）、「constitue un enjeu majeur」（构成重大挑战）、「est au cœur de」（处于……核心）、「pierre angulaire」（基石）、「s'inscrit dans une logique de」（符合……逻辑）、「à l'ère de」（在……时代）、「dans un monde où」（在一个……的世界里）。
- 作强调语的「véritable」（真正的，如「une véritable révolution juridique」）→ 删除该形容词。

原则：用思想本身取代对思想的预告。

## 6. 膨胀的形容词和最高级

*essentiel, crucial, primordial, fondamental, incontournable, majeur, considérable, indéniable, remarquable*（本质的、关键的、首要的、根本的、不可回避的、重大的、可观的、不可否认的、卓越的）无节制使用。当**有据且有度**时保留；仅使论述膨胀时删除。以论证代替形容词。

## 7. 过多的连接词

*en effet, ainsi, par ailleurs, en outre, notamment, dès lors, partant, de surcroît*（事实上、因此、此外、另外、尤其、从而、因而、加之）：单独使用很好，但累积使用可疑（几乎每句句首都有连接词）。精简：删除不标示真实逻辑衔接的连接词。注意：在法律中，*dès lors*、*partant*、*en l'espèce* 是合法的；不要禁止它们。

## 8. 元文本习惯

评论文本而非书写文本的句子：「Cette partie a pour objet de…」（本部分旨在……）、「Nous allons à présent examiner…」（我们现在将考察……）、「Comme nous l'avons vu précédemment…」（如前所见……）、「En guise de conclusion…」（作为结语……）。删除它们，直接陈述；除非在提纲中确有实际用处的预告价值。

## 9. 填充性对偶与排比

「non pas X, mais bien Y」（不是 X，而是 Y）、「tant sur le plan A que sur le plan B」（无论在 A 层面还是 B 层面）、「qu'il s'agisse de… ou de…」（无论是……还是……）、「d'une part… d'autre part…」（一方面……另一方面……）无区分性内容地使用。当对立是真实的时候保留；当它是装饰性的时候删除。

---

**谨慎提醒**：每处判断性改写都以 Word 修订方式呈现并记入登记册。对含义有犹豫时，**不要改写**：用 `docx` 评论标记，而非改动文本。

## 10. 动名短语——*判断*

行政式笨重风格的标志，在生成文本中常见：助动词 + 名词化代替简单动词。当语义无损失时收紧：
- 「procéder à la vérification de」→ 「vérifier」（进行核实 → 核实）
- 「opérer un choix」→ « choisir»（作出选择 → 选择）
- 「effectuer une analyse」→ 「analyser」（进行分析 → 分析）
- 「apporter une réponse à」→ « répondre à»（给予回应 → 回应）
- 「avoir pour conséquence de」→ « entraîner»（其后果是 → 导致）

当短语是承载法律细微差别的**专业术语**时保留：*mettre en demeure*（催告）、*porter à la connaissance*（告知）、*faire grief*（提出异议）、*mettre en œuvre*（实施，机制），这些不是空洞的动名短语。

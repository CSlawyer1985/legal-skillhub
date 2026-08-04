# 示例——验证一条 ECCC 引用

本示例演练从问题到已验证输出的单条 ECCC 引用验证过程。它展示了 `../references/verification-workflow.md` 中的工作流在实践中是什么样子。

## 问题

用户询问：

> "What did the Trial Chamber hold on genocide against the Cham in Case 002/02? Give me a citation I can use."

## 第 0 步——识别文书

用户已指明：
- 法院：ECCC。
- 案件：002/02。
- 机构：审判分庭。
- 命题：针对占族人的灭绝种族罪——即分庭关于灭绝种族罪构成要件的认定，适用于占族少数群体。
- 制品：案件 002/02 审判判决。

案件 002/02 审判判决于 2018 年 11 月 16 日作出。其文号为 E465。判决时的被告为 NUON Chea 和 KHIEU Samphan（对 IENG Sary 的诉讼因其于 2013 年 3 月死亡而终止；对 IENG Thirith 的诉讼于 2015 年 8 月终止）。

此识别是第 0 步的工作假设。第 2 步将验证它。

## 第 1 步——规划引文

要规划的引用：

- 文书：案件 002/02 审判判决。
- 命题：审判分庭关于灭绝种族罪行为要件和主观要件适用于占族人的认定，以及由此产生的灭绝种族罪有罪认定。
- 验证目标：认定本身达到段落实指层级；总体结论达到内容层级。

## 第 2 步——按后备阶梯验证

### 第一级——eccc.gov.kh

尝试对案件 002/02 审判落地页执行 `web_fetch`：`https://www.eccc.gov.kh/en/cases/case-002/trial-02`。

预期结果：页面列出主要决定，包括带链接的审判判决（E465，2018 年 11 月 16 日）。

然后对审判判决 PDF 本身执行 `web_fetch`。

预期结果：PDF 很大（案件 002/02 审判判决超过 2,300 页）。前几页给出文书识别信息（案卷编号 002/19-09-2007/ECCC/TC、审判判决、2018 年 11 月 16 日）。关于针对占族人灭绝种族罪的认定出现在判决较后部分，在专述占族人的章节中。

验证结果：
- **存在已验证。** 文号、标题、日期、分庭已确认。
- **内容部分验证。** PDF 检索表面化了占族灭绝种族罪认定的存在，但不一定覆盖用户可能想引用的每个段落。
- **仅对检索中实际表面化的段落进行段落验证。** 如果需要对特定认定（例如关于受保护群体、关于灭绝意图）做段落实指陈述，该段落本身必须在检索到的内容中。

### 第二级——legal-tools.org

交叉核对文号和元数据。案件 002/02 审判判决应以相同文号和日期出现在 legal-tools.org 上。如出现差异，以 eccc.gov.kh 版本为准。

### 第三级——OHCHR 或联合国法治

联合国法治数据库托管案件 002/02 审判判决（联合国是法庭设立的一方）。在 eccc.gov.kh 缓慢时，可作为替代下载点。

### 第四级——第二层级概括

学术评论（例如《Journal of International Criminal Justice》、《International Legal Materials》、《Asian Journal of International Law》）分析过案件 002/02 的灭绝种族罪认定。它们可以引导用户找到相关段落并确认大致内容，但其本身不能作为法院认定的引用。

例如：一篇学术文章指出审判分庭认定占族人依据《灭绝种族罪公约》作为宗教和族群构成受保护群体。这对定位*有用*。它*不是*引用——审判判决才是。文章的脚注会告诉您段落；验证仍基于审判判决本身。

## 第 3 步——使用已验证材料起草

假设验证给出：
- 存在：已确认 E465，2018 年 11 月 16 日，审判分庭。
- 内容：已确认审判分庭认定针对占族人的灭绝种族罪，且该认定基于占族人的受保护群体地位和犯罪人的特定意图。
- 段落：检索表面化了一个具体段落群（示意性为第 3422–3514 段），受保护群体地位认定在第 3422 段，特定意图认定在第 3445–3450 段。

引用草稿：

> The Trial Chamber held that the Cham constituted a protected group under the Genocide Convention as both a religious and an ethnic group. *Prosecutor v. NUON Chea and KHIEU Samphan* (Case 002/02), Trial Chamber, "Trial Judgment", E465, 16 November 2018, para. 3422.
>
> The Trial Chamber further held that the specific intent to destroy the Cham as such was established. *Ibid.*, paras. 3445–3450.

如果仅验证了存在和宽泛内容（而非段落）：

> The Trial Chamber found that the Cham constituted a protected group under the Genocide Convention. *Prosecutor v. NUON Chea and KHIEU Samphan* (Case 002/02), Trial Chamber, "Trial Judgment", E465, 16 November 2018 (paragraph content not retrieved in this session — paragraph pinpoint omitted).

## 第 4 步——自我审计

对草稿中的每个句子，模型自问：这能否追溯到项目知识或本次会话中的成功检索？

- "The Trial Chamber held that the Cham constituted a protected group" —— 追溯到第 2 步检索的审判判决第 3422 段。
- "as both a religious and an ethnic group" —— 同段。
- "The specific intent to destroy the Cham as such was established" —— 追溯到第 2 步检索的审判判决第 3445–3450 段。

如果任何句子无法追溯，则删除它，或将其弱化为检索支持的内容。

## 本示例捕捉的常见失败模式

- **引用案件 002/02 审判判决而不与案件 002/01 审判判决区分。** 案件 002/01（E313，2014 年 8 月 7 日）不涉及针对占族人的灭绝种族罪——该指控在 002/02 中审理。
- **引用"Case 002"而非"Case 002/02"。** 精确的引用读者会注意到缺失的斜杠。
- **在用户想要审判分庭认定时引用上诉判决（F76，2022 年 12 月 23 日）。** 上诉判决（经调整地）维持了原判，但是另一份文书。（上诉于 2022 年 9 月 22 日口头宣判；引用 F76 时用 2022 年 12 月 23 日书面判决日期——见 `../references/citation-format.md`。）
- **编造段落编号。** 如果检索没有表面化第 3445 段，您就没有它。省略实指或索要该文书。

## 本示例未展示的内容

- 保密文书的处理（用户想要的段落只存在于保密版本中的情况）。
- 高棉语文书的处理（审判判决为英语，但其内引用的部分底层文书为高棉语或法语）。
- 重大反对意见的处理（案件 002/02 审判判决含个别意见；如果用户想要反对意见，指明法官并验证该反对意见出现在检索到的内容中）。

这些见 `../references/verification-workflow.md` 和 `example-audit.md`。

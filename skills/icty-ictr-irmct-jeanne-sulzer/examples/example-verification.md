# 示例——单条引文的端到端验证

验证工作流应用于一条引文的演练示例。它展示纪律的实际运作；它是示意性的，而非机械遵循的脚本。

---

## 请求

用户正在起草备忘录并写道：

> "As the ICTY first held, the Srebrenica massacre of July 1995 constituted genocide. Can you give me the citation with the paragraph?"

## 第 0 步——识别涉及的文书

命题是"斯雷布雷尼察 = 灭绝种族罪，ICTY 首次如此认定"。在审判中确立此点的案件是 **Krstić**（IT-98-33）。有两个候选文书：审判判决（IT-98-33-T，2001 年 8 月 2 日）和上诉判决（IT-98-33-A，2004 年 4 月 19 日）。用户说"first held"，指向审判分庭。但注意一个需要确认的微妙之处：上诉分庭精炼了 Krstić 本人的*责任形式*（从实施改为帮助和教唆灭绝种族罪），同时确认灭绝种族罪*确实*发生在斯雷布雷尼察。因此精确的陈述和精确的段落很重要。

## 第 1 步——规划引用

需要一条引用：Krstić 审判判决，用于"斯雷布雷尼察大屠杀构成灭绝种族罪"的命题。如果备忘录还断言了关于 Krstić 个人责任的某些内容，则需要第二条引用（上诉判决），因为关于其责任的判旨在上诉中发生了变化。

## 第 2 步——按后备阶梯验证

1. **irmct.org / 案件页面。** 在案件列表中搜索 Krstić。确认：案号 IT-98-33、ICTY、审判分庭判决 2001 年 8 月 2 日、上诉分庭判决 2004 年 4 月 19 日。存在已验证。
2. **判例数据库（cld.irmct.org）。** 查询"斯雷布雷尼察灭绝种族罪"认定。CLD 指向审判判决中分庭认定摧毁作为群体的斯雷布雷尼察波斯尼亚穆斯林意图成立的相关段落。注意 CLD 识别的段落范围。
3. **打开审判判决**（通过 irmct.org / 遗留 icty.org / legal-tools.org）并阅读已识别段落以确认该命题确在其中陈述——**段落已验证**。

如果会话中无法访问 CLD 或判决，降级为：从案件页面确认存在和实质判旨（内容已验证），并告知用户段落未确认。

## 第 3 步——起草

> The Trial Chamber in *Prosecutor v. Krstić* held that the massacre of the Bosnian Muslim population of Srebrenica in July 1995 constituted genocide: *Prosecutor v. Krstić*, Case No. IT-98-33-T, Judgment (Trial Chamber), 2 August 2001. On appeal, the Appeals Chamber affirmed that genocide was committed at Srebrenica while revising the basis of Krstić's own liability to aiding and abetting genocide: *Prosecutor v. Krstić*, Case No. IT-98-33-A, Judgment (Appeals Chamber), 19 April 2004.

（如果段落验证成功，添加段落编号。如果没有，说明该段落未在本会话中确认。）

## 第 4 步——自我审计

- "first held" 是否准确？Krstić 是首个将斯雷布雷尼察定性为灭绝种族罪的 ICTY 判决——对照记录确认此框架，而非凭记忆断言优先性；如无法确认，弱化为"held"。
- 是否尊重审判与上诉的区分？是的——草稿将灭绝种族罪已发生的判旨（审判认定，上诉维持）与责任形式的判旨（上诉中修订）分开。这正是凭记忆引用会模糊的区分类型。
- 变音符号正确吗？Krstić。正确。

## 教训

这里的危险不是编造案件——Krstić 广为人知——而是**夸大被引文书的内容**和**模糊审判/上诉的区分**。验证步骤正是捕捉这些问题的环节。输出对验证层级诚实，并精确说明哪个分庭认定了什么。

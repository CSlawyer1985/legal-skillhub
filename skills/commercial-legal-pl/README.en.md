[🇵🇱 PL ←](./README.md) | 🇬🇧 EN

# 波兰商事法律（Polish Commercial Legal）

**展示 Claude 如何与波兰合同协作的示例。**
可作为律师实用 AI 工具应有样貌的起点。

基于本所（**Kancelaria Radcow Prawnych Zurawska Piotrowski i Wspolnicy**，Zurawska Piotrowski 律师事务所，[ktzr.pl](https://ktzr.pl)）的执业实践构建，主要涉及 B2B、知识产权与 IT 合同。

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Jurisdiction](https://img.shields.io/badge/Law-Poland-red)](https://github.com/apiotrowski-afk/commercial-legal-pl)
[![Status](https://img.shields.io/badge/Status-v0.x_(early)-yellow)](https://github.com/apiotrowski-afk/commercial-legal-pl)
[![Claude Skill](https://img.shields.io/badge/Claude-Skill-orange)](https://claude.ai)

> ⚠️ **免责声明：** 本 skill 不替代法律意见；它是律师工作的操作性工具，每项具体事务均须由具备资格的人员单独审查。

## 这是什么

一个用于**在波兰民法下起草和审查合同**的 Claude skill，聚焦 B2B 合同、知识产权与 IT。该 skill 按需加载；当对话涉及波兰合同、条款起草或审查客户刚签署（或即将签署）的合同时，Claude 会调用它。

它以波兰语撰写，因为波兰合同以波兰语写成，法学理论以波兰语表述，判例法亦为波兰语。该 skill 以波兰语工作；本英文 README 的存在是为了让你决定它是否值得深入了解。

## 我们为何发布

关于波兰法律科技（Legaltech）中 AI 的讨论很多，尤其在会议和社交媒体帖文中。但真正能在律所日常执业中发挥作用的工作实现要少得多。

我们相信最好的工具并非来自会议演讲或咨询性质的 PoC（概念验证），而是来自日常使用。我们为自己构建工具，投入使用，在过程中不断打磨，然后与他人分享。

因此我们决定从具体事项入手：起草 B2B、知识产权与 IT 合同，将其封装为 Claude skill 并公开——不是作为*“本所的正式生产工具”*，而是作为一种可行方法的示例，欢迎批评、分叉与讨论。

它或许能给他人带来：
- 关于如何为另一法律领域或另一律所构建自有 skill 的思路
- 关于*“波兰版的 claude-for-legal 应当是什么样”*这一讨论的起点，因为目前 Anthropic 生态主要面向美国/英国普通法

如你愿意参与（问题、PR、评论、分叉、为其他领域制作你自己的版本），皆受欢迎。

## 开始前需要了解的事项

几点坦诚的提醒，以免失望：

- **这是精简后的切片，并非本所的全套工具库。** 你在此所见是经过有意裁剪、综合并改写的内容，使其有实用价值又不违反波兰 radca prawny（法律顾问）的职业保密义务（《法律顾问法》第 3 条）。完整的内部资料库更大，包含与具体案件、客户画像、案例研究、技术补充相关的条款，全部保存在本地私有副本中。**你在此所见的都是示例，而非“唯一正确的方法”。**

- **该 skill 的效果取决于你自己的使用方式。** *“垃圾进，垃圾出”（Garbage in, garbage out）*在此尤为适用。最佳结果来自针对自身实践的迭代：将你自己的条款加入 `references/baza-klauzul/`，你自己的规则加入 `references/zlote-reguly.md`，你自己的工作流。我们的这套只是起点。

- **这不是通用模板。** 一家律所，一套设计选择。如果你的执业方式不同，请分叉并改造。

- **范围有限**，仅限 B2B、知识产权与 IT 合同。不涉及刑法、行政法、税法、家事法，也不涉及法院程序。

- **该 skill 尚未进入 `claude-plugins-community`。** 目前请直接从我们的仓库安装。

## 内含内容

该 skill 有五个主要层次：

| 层次 | 内容 | 文件 |
|---|---|---|
| **黄金规则** | 起草波兰合同的 12 条规则：定义控制、结构、语言 | `references/zlote-reguly.md` |
| **编辑风格** | 源自执业的具体风格模式（何时使用 *“W przypadku”* 而非 *“Jeżeli”*、每类关系的当事方配对、排版） | `references/style-redakcyjny.md` |
| **条款分类** | 合同语言的 7 个类别——Adams 的 MSCD 框架的波兰语改编 | `references/kategorie-klauzul.md` |
| **条款库** | 按类别划分的示例条款（当事方、标的、知识产权、责任、终止、GDPR、结算等）；通用 IT 模式 + 本所参考条款 | `references/baza-klauzul/` |
| **知识库** | 附带判例（最高法院、最高行政法院）的学理分析：维护、著作权、GDPR、责任上限、肖像权 | `references/baza-wiedzy/` |

另附 `references/essentialia-mapowanie.md`（各类合同的 essentialia negotii，必要要素映射）、`references/checklist-15.md`（15 项完整性检查清单）与 `references/legal-design.md`（对外文件的视觉层面）。

该 skill 随附 `workflows/` 中的**8 个操作性工作流**：快速分诊（GREEN/YELLOW/RED，绿/黄/红）、完整合同分析、风险审计、合同生成、条款编辑、一致性检查、魔鬼代言人式审查（devil's advocate）与客户入职引导。每个工作流都精确规定何时加载哪些参考文件。

## 如何使用

```bash
# Fastest — works with Claude Code, Cursor, Codex and 40+ agents:
npx skills add apiotrowski-afk/commercial-legal-pl

# Or clone manually into your skills directory:
cd ~/.claude/skills
git clone https://github.com/apiotrowski-afk/commercial-legal-pl.git
```

在任何 Claude 对话中，当话题涉及波兰合同时，该 skill 会自动加载。

详细安装说明见[波兰语 README](./README.md)。

## 许可证

Apache 2.0。可自由使用、分叉、改造。我们仅请求在 NOTICE 文件中保留对 KTZR 律师事务所的署名，以惠及那些关心出处、希望了解这些模式来源的人。

## 联系方式

- 网站：[ktzr.pl](https://ktzr.pl)
- 邮箱：a.piotrowski@ktzr.pl
- GitHub：[@apiotrowski-afk](https://github.com/apiotrowski-afk)

---

*该 skill 处于积极开发中。内容将会变化。欢迎提交 Issue 和 PR。*

---
name: data-act-ryan-malek
description: 面向律师的欧盟数据法案（(EU) 2023/2854 号条例）技能。当用户询问数据法案分类、起草、查询、分析或审计时使用。触发词包括"Data Act"、"Regulation 2023/2854"、"connected product"、"related service"、"data processing service"、"DPS switching"、"Article 3(2) pre-contract"、"Article 25 contract"、"trade-secret handbrake"、"international government access"、"Chapter VI cloud switching"、"Article 50 timeline"、"FAQ Q22a"、"data holder"、"exportable data"、"functional equivalence"、"Art. 4(10) competing product"以及类似的欧盟数据法案短语。该技能生成律师风格 Word 输出，并逐字引用捆绑的条例和 FAQ 源文本。
metadata:
  author: "Ryan Malek"
  license: "agpl-3.0"
  version: "2026-05-12"
---

1. 在回答前阅读 `references/method.md`、`references/gotchas.md` 和 `references/house-style.md`。
2. 当您需要律师提供事实才能继续（模式、所代理的一方、行业、时间等）时，使用 `AskUserQuestion` 工具以可点击面板呈现多项选择选项。将相关问题合并到一次调用中。仅当当前客户端中 `AskUserQuestion` 不可用时，才回退到纯文本 A/B/C/D。
3. 要回答条例或 FAQ 问题，在 `assets/source/regulation-2023-2854.md`（标题：`## Article N`、`## Recital N`）或 `assets/source/faq-v1.4.md`（标题：`## FAQ Q[N|Na]`）中搜索。逐字引用。绝不凭记忆转述；如果条款不在源文件中，报告技能缺陷。
4. 要生成起草起点，填写 `assets/templates/` 中的相关模板（见 `assets/templates/README.md`）。不要重写模板。
5. 如需特定主题的深入内容，仅在相关时阅读 `references/trade-secret-ladder.md`、`references/art-13-unfair-terms.md`、`references/gdpr-overlay.md` 或 `references/sectoral-overlays.md`。
6. 聊天回答后，通过 `scripts/render_docx.py` 提供 Word 导出。脚本会附加免责声明页脚。

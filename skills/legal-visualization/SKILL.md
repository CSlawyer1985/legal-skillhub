---
name: legal-visualization
description: 法律图表化与诉讼可视化 Skill，用于把判决书、案件事实、合同关系、诉讼策略、争议链条、证据时间线、责任分配和法律工作流转化为清晰的律师级图表。当用户要求“可视化”“图表化”“画图”“诉讼可视化”“判决书图表化”“案件关系图”“裁判逻辑图”“时间线图”“金额责任图”“合同链图”“资金流图”“担保关系图”，或需要将法律事实转成 draw.io / Excalidraw 图用于文章、客户沟通、诉讼文书、报告或培训时使用。
.
metadata:
  version: "1.1.0"
  bundle: "本包为单技能目录：根目录 SKILL.md + skills/drawio 与 skills/excalidraw-diagram-generator 两个子技能，一键下载解压后整夹使用，无需再分别安装。"
---

# 法律图表化

将法律材料转化为律师级图表。本 Skill 的作用不是直接画图，而是先判断法律材料适合怎样图表化，再选择合适工具：正式结构图优先使用 draw.io，讲解型白板图优先使用 Excalidraw。

## 安装

本技能以**单个技能包**分发：ZIP 解压后应得到**一个文件夹**，其根目录包含本文件的 `SKILL.md`，以及子目录 `skills/drawio/`、`skills/excalidraw-diagram-generator/`。

1. 获取技能 ZIP 后解压，或按客户端提供的 **复制安装命令** 安装。
2. 将整个解压目录放到客户端要求的 **skills 根目录**下（例如 Claude 的 skills 目录），保持**目录名与技能 id 一致**（通常为 `legal-visualization`）。
3. 使用时由本 Skill **总控路由**：需要正式图表则加载 `skills/drawio/SKILL.md`，需要手绘白板风则加载 `skills/excalidraw-diagram-generator/SKILL.md`；二者已随主包安装，**无需再单独安装两个画图技能**。


## 核心原则

不要一上来就画图。先判断法律任务类型，提炼当事人、法律关系、请求抗辩、争议焦点、证据和责任结构，再选择图表类型，并判断是否需要拆成多张图。复杂案件通常不应强行塞进一张图。

## 工具选择

当用户需要正式、结构化、可复用的图表时，使用 **draw.io**：
- 判决书阅读图
- 裁判逻辑图
- 当事人 / 责任关系图
- 金额与利息分配图
- 合同审查流程图
- 交易结构图
- 担保 / 保全 / 追偿结构图
- 用于报告、客户备忘录、法律意见书或 PPT 的正式图表

当用户需要手绘感、白板式、便于讲解和二次编辑的图表时，使用 **Excalidraw**：
- 微信公众号文章配图
- 法律概念解释图
- 诉讼策略图
- 课程或直播讲解图
- 简化版案件关系草图
- 用户希望后续在 Excalidraw 中手动调整的图

法律类 Excalidraw 图应使用**干净的白板风格**，不要做成杂乱手稿风：
- 使用矩形、方形、圆角矩形色块。
- 优先使用 `fillStyle: "solid"` 和浅色背景。
- `roughness` 保持较低，通常为 `0` 或 `1`。
- 默认不要使用 `hachure`、`cross-hatch` 或厚重草稿阴影。
- 用不同颜色的描边和箭头表达法律含义。
- 避免巨大的弯曲虚线回路；必要时使用旁注或拆成多张图。

当对应工具 Skill 已安装时，应加载并遵循该工具的规则：
- draw.io: `skills/drawio/SKILL.md` (relative to this skill root)
- Excalidraw: `skills/excalidraw-diagram-generator/SKILL.md` (relative to this skill root)

如果用户明确指定工具，优先使用该工具；只有明显不适合时，才简要说明取舍。

## 法律图表化流程

1. **提取法律结构**
   - 当事人及其角色
   - 合同、函件、判决书等关键文件
   - 诉讼请求、抗辩、反诉或反请求
   - 争议事实
   - 法院裁判理由
   - 金额、利息、担保、保全、责任分配
   - 关键日期和证据锚点

2. **选择图表类型**
   - 当事人关系图
   - 合同链图
   - 资金 / 付款流向图
   - 担保 / 保全 / 责任结构图
   - 时间线图
   - 请求 - 抗辩 - 裁判逻辑图
   - 判决书争点树
   - 金额计算与责任分担图
   - 证据链图
   - 诉讼策略图

3. **判断一张图还是多张图**
   - 一张图：简单关系、单一流程、文章配图。
   - 三张图：判决书或复杂争议，通常拆成 `关系图 + 裁判逻辑图 + 金额/责任图`。
   - 多张图：长篇判决、多方建设工程纠纷、公司控制权争议，或日期和证据链特别多的案件。

4. **先设计，再渲染**
   - 为颜色分配稳定的法律含义。
   - 先规划泳道或层级，再开始绘制。
   - 每个节点控制在 2-4 行。
   - 长解释放在节点外，用注释或旁注承载。

5. **Render and verify**
   - Ensure no text overlaps.
   - Ensure no line crosses text or node interiors.
   - Route long arrows around the outside.
   - Keep labels on white background or away from lines.
   - Prefer short orthogonal routes.
   - Check mobile readability for WeChat articles.
   - For draw.io files, run the layout validator before exporting when possible (from **this skill root**):
     `python3 scripts/validate_drawio_layout.py <file.drawio>`
   - For Excalidraw files, run:
     `python3 scripts/validate_excalidraw_layout.py <file.excalidraw>`
   - If the validator reports an edge crossing a non-endpoint node, revise the layout before exporting.

## Mandatory Layout Rules

- Never let arrows or connector lines cover text.
- Never let nodes overlap.
- Avoid diagonal spaghetti lines in legal relationship diagrams.
- Route return/recourse/claim-back arrows around the canvas edge.
- Use lanes for chain disputes: `contract/regulatory layer`, `payment break layer`, `claim/liability layer`.
- For amount/liability charts, separate `amount calculation`, `ancillary fees`, and `liability bearers` into distinct layers. Do not draw responsibility lines through fee nodes.
- For construction chain diagrams, avoid drawing all legal relationships in one canvas if it creates more than one long outer-loop arrow. Split into `contract chain` and `risk/claim chain` or use a central risk hub.
- For Excalidraw legal diagrams, do not use hachure or cross-hatch fills unless the user explicitly asks for a rough sketch.
- Use separate diagrams instead of forcing all information into one crowded figure.
- For Chinese legal diagrams, avoid long sentences inside boxes.
- For public article diagrams, make the first screen readable on mobile.

## Quality Gate

Before final delivery:

1. Verify the legal content: no role, amount, claim, or liability is misstated.
2. Verify visual readability: no line crosses text, no node overlaps, no label is hidden.
3. For draw.io, run the bundled validator script when available.
4. If a diagram fails readability, do not explain the failure as a tool limitation; revise the layout.
5. If one diagram remains crowded after one revision, split it into multiple focused diagrams.

## Legal Color Semantics

- Blue: party, main contract, primary legal relationship
- Green: supported claim, valid path, completion, payment due
- Red: breach, risk, rejection, disputed nonpayment, adverse finding
- Orange: issue, uncertainty, decision point, controversial fact
- Purple: guarantee, security, third-party liability, recourse
- Gray: background fact, neutral actor, supervision, context

Keep color semantics consistent within the same article or report.

## Output Defaults

- For draw.io: create `.drawio` source and export PNG when possible. Keep the source file unless the user asks for only PNG.
- For Excalidraw: create `.excalidraw` source. Do not promise PNG export unless a separate rendering path is available.
- Use descriptive English filenames with legal context, e.g. `judgment-logic.drawio.png`, `construction-chain-dispute.excalidraw`.
- For WeChat article use, prefer separate PNGs or Excalidraw files rather than one overloaded mega-image.

## Reference

For detailed legal diagram patterns and examples, read `references/legal-diagram-patterns.md` when the task involves a judgment, multi-party dispute, construction dispute, case article, or litigation strategy map.

For quality checks and revision patterns, read `references/layout-quality-gate.md` when a diagram has crossing lines, compressed labels, or user feedback about readability.

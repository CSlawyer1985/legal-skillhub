<!-- Maintained by Lu Lingyan, Deheng (Wuxi) Law Firm. -->
# WeChat Publisher — Troubleshooting（已知坑位）

> 按需加载：仅在发布结果异常、需要诊断时阅读本文件。

## 坑位 1：WPS / 部分生成器的 docx 标题发布后没加粗

**现象**：文档里设了标题样式（「路径一」「真相」「结语」等），发布后却全是正文样式（15px / 400），没有加粗加黑。

**根因**：这类 docx 的标题用的是**自定义段落样式**（`heading 1/2/3`），在 `styles.xml` 里表现为 `<w:name w:val="heading 1"/>`，但 `<w:pStyle w:val="...">` 的值是随机字符串 ID（如 `000046`），run 级**没有** `<w:b>`——加粗全靠段落样式继承。原脚本只识别两类标题（① 数字 pStyle ID 1-4 ② 中文序号「一、二、三」），故这类标题全被漏判为正文。

**诊断手法**（AI 必会，别只看 run 级加粗）：
1. 用 PizZip 读 `word/document.xml`，正则抓 `<w:pStyle w:val="...">` 的值。若不是 `1/2/3/4`、也不是 `Heading1/2` 标准写法，而是 `000046` 这类随机串，基本就是 WPS 自定义样式。
2. 再读 `word/styles.xml`，按 `w:styleId` 找到对应 `<w:name w:val="...">`，确认是不是 `heading 1/2/3`。
3. 旁证：mammoth 的 `convertToHtml` 会正确识别（输出 `<h1>/<h2>/<h3>`），可拿它交叉验证结构。

**修复**：`processDocx` 内解析 `styles.xml`，建立 `headingStyleIds` 集合，`isHeadingStyle` 兼容数字 ID + 自定义字符串 ID 两类。修复后大标题 18px/700、小标题 17px/700 全部加粗。

**注意事项**：
- run 级加粗标记 WPS 写作 `<w:b w:val="1"/>`（不是 `<w:b/>`）。排查时自己写正则要覆盖 `/<w:b[\s\/]/` 且排除 `val="0|false"`，别只匹配 `<w:b/>`，否则会误判"全文无加粗"。
- 列表引导词（如「数据网站自身的限制：」）的加粗一般在 run 级（`<w:b w:val="1"/>`），本就正常，无需走 styles 映射。

## 坑位 2：发布前必须探测出口 IP（P0 铁律）

WorkBuddy 出口 IP 不固定。脚本 `init()` 已内建探测：调 `cgi-bin/token` 若返回 `40164 invalid ip`，会**自动解析 errmsg 中的实际 IP 并打印加白指引**（mp.weixin.qq.com「设置与开发→基本配置→IP 白名单」），无需再手工 `curl` 探测。token 正常返回 `access_token` 即说明 IP 在白名单内。

## 坑位 3：require publish.js 会直接执行 main()

`publish.js` 末尾 `main()` 直接执行，无法直接 `require` 调 `processDocx` 做本地验证。**已由 `--check` 模式替代**：`node publish.js --check <file>` 跑完整解析 + footer 拼接 + 自检并输出报告。若仍需单测 `DocumentProcessor`（开发时），变通：读源码把末尾 `main();` 替换为 `module.exports = { DocumentProcessor }`，写入临时文件再 `require`。

## 坑位 4：docx 里的表格整片消失 / 表格样式不符预期

**现象**：文章里的对比表发布后不见了，或表头不是深蓝、没有斑马纹。

**根因**：旧版解析循环只扫 `<w:p>`，`<w:tbl>` 被整段跳过。v1.3.0 已补 `parseTable()`，但仍有边界：

- **图片在表格单元格内**：`parseTable` 只取文本（run 级加粗会保留为 `<strong>`），图片类单元格不渲染也不上传。法律/数据对比场景极少需要在单元格放图，暂不处理。
- **首行即表头**是约定：代码把表格首行当作表头（深蓝）。若你的表没有表头行（首行就是数据），首行仍会被渲染成深蓝——此时需手动在公众号后台去掉首行底色，或约定"对比表首行为表头"。
- 表格列数过多（>5 列）在手机上会挤压换行，建议拆分或精简文字（参考排版通用原则）。

**验证手法**：`node publish.js --check <file>` 的自检报告会直接给出「表格深蓝表头」「标题金色左划线」两项 ✅/❌；或开发时用 `node -e` 调 `DocumentProcessor.parseTable(样例w:tbl, new Set())` 看输出是否含 `background:#1A3A6B` 与斑马纹。

## 坑位 5：同标题重发时旧草稿可能永久丢失（P0）

**现象**：改完文章重发，旧草稿先被删、新建又失败（限流 45009 / 内容超限 / 网络抖动），旧草稿**永久丢失**，只能重新排版。

**根因**：旧版 `createOrUpdateDraft` 用 **delete-then-create** 策略——先 `deleteDraft` 再 `_createDraft`，中间有不可回滚的窗口。而且 `updateDraft` 其实早已定义、从未被接线（死代码）。

**修复（v1.4.0）**：改用 `updateDraft` **原子更新**。`findDraftByTitle` 返回的 `{ media_id, index }` 正好是 `draft/update` 所需的参数（`index` = 图文内文章下标），直接接线即可。update 失败旧稿仍在，无丢稿窗口。已删除不再使用的 `deleteDraft`。

**铁律**：任何"先删后建"的替换逻辑，只要存在 update/patch 接口，一律改原子更新，绝不 delete-then-create。

## 坑位 6：正文含 `< > &` 字面字符会产出非法 HTML / 注入

**现象**：正文里写 `<某标签>`、`A & B`，发布后标签被当真实 HTML 渲染，甚至破坏排版。

**根因**：旧代码把 docx `w:t` 里的 XML 实体 `&amp;/&lt;/&gt;` 先**解码**成裸字符再拼进 HTML，但没重新转义。裸 `<` 进入 HTML 就是标签。

**修复（v1.4.0）**：**原样透传**——`w:t` 的 `&amp;/&lt;/&gt;` 本身就是合法 HTML 实体，直接透传即可正确渲染，解码才是问题根源。仅 `docTitle`（走 JSON 纯文本 API）需要解码。

**铁律**：docx 正文 → HTML 是"实体到实体"，永远不要解码再重转义；只有进 JSON 纯文本字段（标题）才解码。

## 坑位 7：解析正确性杂项（v1.4.0 一并修复）

- **首段大标题丢失 18px 样式**：`paraIndex++` 若在 `runs.length===0` 判断之前，纯图片/空首段会把真正的标题段顶到 `paraIndex===2`，丢失大标题样式。修复：`paraIndex++` 移到判空之后，只对有文本的段计数。
- **文本框内容截断分段**：`w:txbxContent` 内嵌 `w:p` 会干扰 `blockRegex` 匹配边界。修复：解析前 `strip w:txbxContent`（多为装饰）。
- **图片处理产物污染源目录**：`preprocessImage` 原把 `_processed.png` 写在用户源文件旁。修复：产物写入临时目录，随流程统一清理。
- **无超时/重试**：`init`/`uploadImage` 补 `timeout` + `withRetry` 重试 1 次（transient 失败）。
- **标题超 64 字符**：微信标题上限 64，解析后自动截断并警告。
- **数字序号小标题**：`isSubHeading` 原只认中文「一、二、三」，注释却声称支持「1. 2. 3」。修复：正则加 `^\d{1,2}[、.．)]`（注意：数字序号与编号列表存在误判风险，但中文序号本就有同等风险，保持一致）。

## 坑位 8：markdown 发布后正文出现多个空行（P0）

**现象**：md 发布到公众号草稿箱后，正文段落之间出现多个空行，观感"排版很散"；md 源文件段落间明明只是单个空行。

**根因**：markdown-it（`{ html:true, breaks:true }`）渲染出的 HTML 中，块级标签之间带换行+缩进空白（`</p>\n    <p>`、`</h2>\n<p>`）。微信图文编辑器导入 HTML 时**不忽略块间空白文本节点**，把它们渲染成空行。

**修复**：`processMarkdown` 渲染后压缩块间空白：
```js
bodyHtml = bodyHtml.replace(/<pre[\s\S]*?<\/pre>|>\s+</g, (m) =>
  m.startsWith("<pre") ? m : "><"
);
```
- `<pre>` 内的空白必须保留（代码块）；其余标签间空白全部压缩为 `><`。
- footer.html 为手写模板，其内部空白（公众号名片区块）不受影响，属正常。

**验证手法**：`--check` 生成的诊断 HTML 中，正文块标签应紧贴（`</h1><blockquote>`、`</p><p>`），不再出现 `</p>\n    <p>`。

## 坑位 9：pandoc 生成的 docx 正文整段加粗加黑（P0，本次事故根因）

**现象**：用 pandoc（`pandoc xxx.md -o xxx.docx`）转出的 docx 发布后，**正文段落整段整段加粗加黑**（font-weight:700），只有少数段落正常。用户反馈「排版太难看了，怎么整段整段加粗」。

**根因**：pandoc 的默认 docx 模板里，段落样式 ID 是**自定义数字**，与 Word 标准 Heading 编号**完全错位**：

| styleId | name | 真实身份 |
|---------|------|----------|
| 1 | Normal | 正文 |
| 2 | heading 1 | 标题（碰巧对） |
| 3 | **Body Text** | **正文**（被误判！） |
| 4 | heading 2 | 标题（碰巧对） |
| 23 | First Paragraph | 正文 |

旧代码判断标题用「数字 pStyle ID 1-4 = Heading 1-4」的猜测：`const numMatch = pStyleVal.match(/^([1-6])$/)`。于是 styleId=`3`（Body Text，正文）被匹配成 `headingLevel=3`，导致**所有 Body Text 正文段被误判为三级标题，整段加粗**。

**为什么坑位 1 的修复没拦住**：坑位 1 修复时新增了 `headingStyleLevels`（styles.xml 的 name→level 映射），但判断顺序写错了——**数字 ID 猜测排在前、name 映射排在后**（`if (numMatch) ... else if (headingStyleLevels.has(...))`）。数字 ID 命中就 return，name 映射永远走不到，等于没修。

**修复**：颠倒优先级——**先查 name 映射（准确），数字 ID 猜测只在 styles.xml 完全解析不出任何 heading（`headingStyleLevels.size === 0`）时才兜底**。

```js
if (headingStyleLevels.has(pStyleVal)) {
  headingLevel = headingStyleLevels.get(pStyleVal);
} else if (headingStyleLevels.size === 0) {
  const numMatch = pStyleVal.match(/^([1-6])$/);
  if (numMatch) headingLevel = parseInt(numMatch[1], 10);
}
```

**诊断手法（AI 必会）**：
1. `--check` 后读诊断 HTML，统计每个 `<p>` 的 `font-weight`：正常应只有标题段是 700，正文全是 400。若大量正文段 700，就是标题误判。
2. 用 PizZip 读 `word/styles.xml`，列出每个 `styleId` → `<w:name>`，核对正文样式（Body Text / First Paragraph / Normal）的 ID 是不是恰好落在 1-6 数字区间、被猜测逻辑误判。

**铁律**：
- **标题判断唯一可信来源是 styles.xml 的 `name="heading X"`**，不是 styleId 数字。数字 ID 猜测只配做"styles.xml 解析失败"的最后兜底。
- pandoc / 第三方转换器生成的 docx，其 styleId 是自定义的，**绝不能**假设「数字 ID 1-4 = Heading 1-4」。
- 修完必须 `--check` 并用诊断 HTML 复核 font-weight 分布，不能只跑脚本看 exit code。



## 坑位 10：正文只有标题加粗，重点句全漏（P0，职责边界事故）

**现象**：发布后标题加粗正常，但正文里**一句重点句都没加粗**，用户反馈"你只搞了标题，重点句怎么不加粗加黑"。

**根因**：**加粗是「写稿/排版」环节的职责，不是发布环节的职责**。发布脚本只透传 docx 里已有的 run 级 `<w:b>`，它不会、也不该去"猜"哪句是重点。如果写稿时（Markdown 阶段）压根没写 `**重点句**` 标记，或排版环节（wechat-layout）没做语义加粗，那么 pandoc → docx → 发布全链路下来，正文就是零加粗，只剩标题靠 Heading 样式显示粗体。

**第一性原理**：发布工具是"忠实透传器"，不是"语义理解器"。重点句的判定是脑力活（理解全文哪句是结论/金句/数据），只能由写稿或排版环节完成，发布环节无法也不应越俎代庖。

**修复**：`selfCheck` 新增一项 **warning 级检测**（不阻断发布，只提醒）——统计正文重点句加粗数：
- docx 正文重点句 = `font-size:15px;font-weight:700`
- markdown 正文 strong = `font-weight:700;color:#1a1a1a`

两者合计为 0 时，自检报告打印 `⚠️ 正文无任何重点句加粗（仅标题加粗）——请确认是否漏做「语义加粗」`。这样"漏加粗"不再静默通过，AI 会被提醒回头补。

**铁律**：
- 写公众号文章时，正文重点句（核心论点、金句、关键数据）的加粗**必须在写稿/排版环节完成**（见 wechat-layout 的「语义加粗」规则），发布环节只负责透传。
- 发布前看自检报告的 ⚠️ 提示，若有"正文无重点句加粗"警告，回排版环节补加粗，而不是直接发。

## 坑位 11：序号列举段落被整段加粗 / 间距过大（P0 已修，2026-08-26）

**现象**：「1. 贴合不牢。」「1. 录音」等以数字序号开头的段落，发布后被**整段加粗加黑**、间距突兀（与正文不一致）。

**根因**：旧逻辑 `isSubHeading`（正则 `/^\d{1,2}[、.．)]/`）把「数字序号开头」的段落误判为小标题，三处连锁：① run 级 `if (run.bold || isSubHeading)` 整段强制 `<strong>`，覆盖文档的 run 级精细加粗；② 段落级 `font-weight:700` + 17px 字号；③ 段距分支 `margin:24px 8px 13px`（正文仅 13px 8px）。用户文档里加粗本是精细的（只加粗序号标题），发布后被整段刷黑。

**第一性原理**：承接坑位 10——发布工具是"忠实透传器"，**不做任何语义猜测**。「序号开头」≠「小标题」：序号列举（「1. xxx + 正文」）就是普通正文段落。只有 Word 标题样式（styles.xml `name="heading X"`）与文档首段才是标题；用表面特征（序号/长度）猜标题，必然误伤。

**修复（2026-08-26）**：
1. 加粗只看 `run.bold`：`if (run.bold || isSubHeading)` → `if (run.bold)`；两处 `else if (isHeadingStyle || isSubHeading)` → `else if (isHeadingStyle)`。
2. 删除 `subHeadingPattern` / `isSubHeading` 定义（`paraText` 仅保留给 `isCnChapter` 中文「一、二、三」章节检测，用于金色左划线）。
3. `baseMargin` 统一 `margin:13px 8px`，序号段落与正文完全同款。

**铁律**：
- 发布环节加粗 100% 由文档 run 级 `bold` 决定，脚本**永不**额外加粗、永不做「小标题化」猜测。
- 序号列举段落（数字/中文序号开头）一律按正文处理，不放大字号、**不整段强制加粗**、无特殊段距（但列举关键词的 run 级语义加粗照常透传）。
- **边界（防矫枉过正）**：「忠实透传」≠「躺平不管」。语义加粗是**排版环节（wechat-layout）的职责**——若文档没做加粗预处理，排版技能必须主动读全文、补语义加粗（见坑位 10 与 selfCheck 的 ⚠️ 零加粗提醒），发布环节不能拿"忠实透传"当借口静默发零加粗稿。
- 发布后用「zipfile 读 `word/document.xml` 的 w:t 文本流 + 关键词计数」核对落盘内容，不能只看编辑器内存态（editor_sdk 曾出现内存正确但落盘损坏的案例）。

## 自检（selfCheck）与发布门禁

`--check` / 发布路径都会跑 `selfCheck()` 五项检查，**不通过则不发布**：① 标题金色左划线存在 ② 有表格则表头深蓝 ③ footer 已拼接 ④ 标题长度 ≤64 ⑤ 图片文件均存在。新增排版约束时应同步扩展 `selfCheck`，而非靠 AI 目测。

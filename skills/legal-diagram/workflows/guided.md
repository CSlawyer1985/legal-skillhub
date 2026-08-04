# 引导式工作流

交互式默认通道。摘要或信息引导、展示发现结果、交给共享生成核心（自动选择并附理由、提供备选方案）。一个事项在一次会话中通常产生多张图表。

## 第 0 步——接收路由交接

路由门控已检测输入、解析 `diagram_scope`（多文件弹窗）并运行第 1 遍。本通道在门控 A 之后进入。您接收 `manifest_cache`、`input_source` 和 `diagram_scope`。

- `manifest_cache` 存在（文件或粘贴文本）→ 文档路径（第 1A 步）。
- 无 `manifest_cache`（仅事项描述，无文档）→ 信息引导路径（第 1B 步）。

不要重新检测输入或重新询问范围；两者归路由拥有。

## 第 0.5 步——确认输入

检测输入后，用一句通俗英语向用户确认读取了哪个文件或文本（例如“我已读取 **[文件名]**。”或“已收到您的文本。”）。HTML 报告稍后在门控 B 决定（`workflows/generation.md` 第 5 步），不在此处。

设置 `source_path` = 输入文件的绝对路径（仅文件输入；粘贴文本或 stdin 为 null）。

## 第 1A 步——摘要所提供的材料

以 `skip_confirmation=false`（显示摘要，不抑制）和路由的 `manifest_cache` 进入 `workflows/extract.md`，使 extract.md 跳过第 1 遍并在第 2 遍继续。返回丰富化的 `ExtractionResult` 及覆盖范围。转到第 2 步。

## 第 1B 步——信息引导（无文档）

1. 加载 `shared/elicitation.md`。
2. 识别事项家族。若未点名，问一行：“什么类型的事项？litigation / corporate / compliance / deal / employment / IP / privacy / bankruptcy / tax / real estate / other（诉讼/公司/合规/交易/雇佣/知识产权/隐私/破产/税务/不动产/其他）。”
3. 询问该家族的精选问题集（3-5 个问题）。接受简写；跳过已回答项。
4. 从回答构建 `ExtractionResult`；人工构建覆盖范围映射。转到第 2 步。

## 第 2 步——摘要 ⛔ 阻塞

绝不使用字段名、JSON 或技术词汇。将所有内容转换为通俗英语。

将每个已填充字段渲染为通俗语言章节，每字段一节，顺序与下方类别映射表相同。跳过缺失字段。仅提示字段加 ⚠ 前缀。

类别映射（字段 → 通俗标签）：

|字段|类别标签|
|---|---|
|obligations|Obligation（义务）|
|deadlines|Deadline（期限）|
|conditions|Condition（条件）|
|documents|Document（文件）|
|transfers|Money flow（资金流向）|
|decision_points|Decision（决策）|
|events|Key event（关键事件）|
|parties|Party（当事方）|
|entities|Entity（实体）|
|relationships|Relationship（关系）|
|ownership_links|Ownership（股权）|
|concepts|Key concept（关键概念）|
|risk_items|Risk（风险）|
|communications|Communication（沟通）|
|data_flows|Data flow（数据流）|
|ip_assets|IP asset（知识产权资产）|
|legal_authorities|Legal authority（法律依据）|
|witnesses|Witness（证人）|
|（所有其他）|Other finding（其他发现）|

所有章节之后：
- **⚠ 不确定：** 逐一列出仅提示字段，各附一行通俗英语说明。
- **未找到：** 列出该事项类型缺失的高价值字段（例如诉讼事项中无当事方）。邀请用户补充。

然后询问：**“看起来对吗？更正一个名称、补充我遗漏的内容或删除任何内容——然后我会建议一种图表类型。”**

⛔ 阻塞：在用户回应之前不进入第 2.5 步。接受“看起来没问题”/“是的”以原样继续。继续前将通俗英语更正应用到 ExtractionResult。

若两遍后提取仍为空，提出一个针对性问题并重试一次，然后停止。

## 第 2.5 步——类型确认门控 ⛔ 阻塞

对丰富化提取运行 `diagram_selector.py`。呈现推荐并**在继续前等待明确选择。**

输出格式（无前言）：

> **推荐：** [通俗语言名称] — [基于发现结果的一句话理由]。
> **备选方案：**
> - [备选1] — 若 [与提取字段相关的一句通俗理由] 则最佳
> - [备选2] — 若 [与提取字段相关的一句通俗理由] 则最佳
>
> 您想要哪一种，还是采用推荐？

**若用户预先点明了图表类型**且与推荐一致 → 确认并继续。若冲突 → 显式呈现冲突：

> 您要求的是 **[用户的类型]**。对于此事项，我推荐 **[推荐类型]**，因为 [与提取字段相关的理由]。按 [用户的类型] 继续、切换到 [推荐类型]，还是选择备选方案？

在用户回应之前不调用 `generation.md`。此门控计入引导模式允许的中断之一。

## 第 3 步——生成

以丰富化提取、**第 2.5 步的已确认类型**、`mode=guided`、`source_path` 和第 2 步的 `digest_rows` 加载 `workflows/generation.md`。执行防护、生成、交付和循环。HTML 报告在生成第 5 步的门控 B 决定。

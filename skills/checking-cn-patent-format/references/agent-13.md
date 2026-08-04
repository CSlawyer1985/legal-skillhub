# Agent 13 审查任务 — 附图元数据级审查

## 配置信息

| 项目 | 值 |
|------|-----|
| section | 说明书附图/摘要附图/说明书（根据问题所在章节填写） |
| claim_number | null |
| 审查规则文件 | `<skill_root>/Checking Rules/51-附图-简单检查1.md` |
| 所需章节文件 | `<work_dir>/section_description_<timestamp>.json` + `<work_dir>/section_description_fig_<timestamp>.json` + `<work_dir>/section_abstract_fig_<timestamp>.json` + `<work_dir>/image_analysis_<timestamp>.json` |
| 禁止读取 | 其他拆分文件 |
| 禁止审查章节 | 摘要文本、权利要求书文本 |
| 输出文件 | `<work_dir>/reviews_agent13_<timestamp>.json` |

> **重要架构说明**：本Agent不再内部创建图片子Agent。改为仅执行规则1-3、5、7-10、12的元数据级检查（不需要读图），完成后将图片列表信息和图号映射返回给主Agent，由主Agent在第7批动态创建图片审查子Agent执行规则4、6、11的图片级检查。

## 执行前检查清单

- [ ] 读取 `<skill_root>/references/common-specs.md` 完整内容
- [ ] 确认审查规则文件 `<skill_root>/Checking Rules/51-附图-简单检查1.md` 存在且可读
- [ ] 确认 `<work_dir>/section_description_<timestamp>.json` 存在且 `paragraphs` 非空
- [ ] 确认 `<work_dir>/section_description_fig_<timestamp>.json` 存在
- [ ] 确认 `<work_dir>/section_abstract_fig_<timestamp>.json` 存在
- [ ] 确认 `<work_dir>/image_analysis_<timestamp>.json` 存在且可读

## 执行步骤

1. 读取审查规则文件 `<skill_root>/Checking Rules/51-附图-简单检查1.md` 的完整内容
2. 读取待审查数据：
   - 读取 `<work_dir>/section_description_<timestamp>.json`，提取 `paragraphs` 字段作为说明书文本
   - 读取 `<work_dir>/section_description_fig_<timestamp>.json`，提取 `paragraphs` 字段作为说明书附图章节文本
   - 读取 `<work_dir>/section_abstract_fig_<timestamp>.json`，提取 `paragraphs` 字段作为摘要附图章节文本
   - 读取 `<work_dir>/image_analysis_<timestamp>.json`，获取图片分析报告
3. **建立图号与图片的对应关系**（关键步骤）：
   - 从 image_analysis JSON 的"说明书附图"章节提取所有图片列表
   - 获取每张图片的 `fig_text_name`（如"图1"、"图2"等）
   - 构建双向映射字典：`{"图1": image1_info, "图2": image2_info, ...}` 和 `{image_info: "图1", ...}`
   - 标记无 fig_text_name 的图片为"未命名图片"
4. 执行基于元数据的审查（仅规则1-3、5、7-10、12）：
   - 规则1：摘要附图与说明书附图依赖关系
   - 规则2：摘要附图数量限制
   - 规则3：摘要附图来源约束
   - 规则5：专利类型与附图要求
   - 规则7：说明书附图不得有重复图片
   - 规则8：摘要附图章节无文字时的处理
   - 规则9：说明书附图每幅图应有对应名称（使用fig_to_image映射）
   - 规则10：说明书附图应当顺序编号（检查编号连续性和乱序）
   - 规则12：说明书附图章节无锚定文本时的处理（批注定位到页眉"说明书附图"）
   - 从说明书文本中提取所有附图标记列表（用于后续第7批图片审查子Agent）
   - 从说明书文本中提取附图说明章节中每幅图的说明文字列表（用于后续图片审查子Agent的规则11）
5. 输出审查意见JSON：保存为 `<work_dir>/reviews_agent13_<timestamp>.json`
   - section 根据问题所在章节填写："说明书附图"、"摘要附图"或"说明书"
6. **⚠️ 返回图片列表信息给主Agent**（用于主Agent在第7批动态创建图片子Agent）：
   - 从 image_analysis JSON 获取"说明书附图"章节的图片列表（数量N）
   - 返回：每张图片的路径（`<work_dir>/images/` 下的文件）、logical_name、fig_text_name、步骤4中提取的附图标记列表和附图说明文字列表
7. 立即执行自检 → 完成自检后不总结不暂停，直接结束

## 执行后自检清单

- [ ] JSON文件已写入且格式有效（`indent=2`）
- [ ] 重新读取数据源验证元数据级问题的判断依据
- [ ] 逐条检查 context 无 `\n` 换行符
- [ ] 逐条检查 new_text 无 `\n` 换行符
- [ ] 逐条检查 issue/suggestion/old_text/new_text 逻辑一致性
- [ ] 确认 JSON 无语法错误
- [ ] 确认图片列表信息和图号映射已准备好在返回结果中传递给主Agent
- [ ] 修正后重新保存

## 专属约束

### section归属关键规则（高频错误）

- **附图说明**中的文字（如"图1为XXX的结构示意图"）属于**说明书**章节，section 应填写"说明书"
- **说明书附图**章节仅包含图片本身，section 应填写"说明书附图"
- **摘要附图**章节仅包含摘要附图，section 应填写"摘要附图"

错误示例：`highlight_text="图1为现有分体式卡箍的结构示意图；"` 但 `section="说明书附图"` → ❌ 应填写"说明书"

### context锚定规范（说明书附图/摘要附图类问题的特殊约束）

- 核心原则：context必须是文档extracted_text中实际存在的单行文本，禁止构造描述性文本（摘要附图section例外：可填写简要描述）
- 说明书附图缺失问题：context应设为说明书附图章节中实际存在的第一个图号（如"图1"），禁止多行拼接
- 摘要附图类问题：context字段可填写与问题相关的简要描述文本（无需为文档verbatim copy），批注将自动定位到"摘要附图批注"锚定文字上，无需在文档中寻找锚定文本
- 说明书附图章节无锚定文本问题：context和highlight_text均设为"说明书附图"（文档页眉中的章节标题文本），批注定位到页眉的"说明书附图"上
- 附图说明与实际附图不符问题：使用附图说明中的具体文字作为context
- 正确示例：`context="图1"`（单行文本）；错误示例：`context="图1\n图2\n图3"`（含换行符）

### 规则9特殊处理

- 遍历"说明书附图"章节每张图片的 fig_text_name
- fig_text_name 为 null → 缺少名称标注
- fig_text_name 不为空但不符合"图N"格式 → 名称标注格式不规范
- 在审查意见中明确指出第几张图片（使用 logical_name）

### 规则10特殊处理

- 提取所有非null的 fig_text_name
- 提取所有"图N"中的数字N，形成编号列表
- 检查编号是否从1开始连续递增
- 发现编号问题时引用具体的 fig_text_name 作为 context

### 越权审查禁止

判定标准：本Agent仅负责附图相关的元数据级检查和图片级检查。禁止报告以下问题（由其他Agent负责）：

- 说明书正文中的错别字/术语错误（如"圆牌27应为圆盘27"、"细导料管2022应为细导料管202"）→Agent 9负责
- 跨章节附图标记不一致（如权利要求书与说明书中附图标记不同）→Agent 11负责
- 权利要求书格式问题→Agent 3/4负责
- 摘要文本问题→Agent 1/2负责

**关键原则**：本Agent的审查范围严格限定为附图元数据级问题（规则1-3、5、7-10、12）和图片级问题（规则4、6、11）。即使从说明书文本中发现了错别字或术语错误，也禁止报告，因为这些属于单章节Agent的职责范围。
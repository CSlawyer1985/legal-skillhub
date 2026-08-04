# 工作流 0：冷启动访谈

> 本文件定义鉴定式行政法案例研习技能的首次使用配置流程。
> 触发条件：用户首次调用本技能，或 `.user-config.md` 不存在/损坏时自动执行。

> **法条锚定单点源铁律**：本文档涉及法条引用之处一律使用 `[语义名称]` 占位符，禁止出现具体条号；语义名称→现行编号的映射由 `SKILL.md §6.5 法条锚定表` 唯一维护。W0 段落 5 是本铁律的执行入口——访谈结束前必须调用 `${LEGAL_SEARCH.get_article}` 对 §6.5 A–J 十组全部语义条目逐项核验，命中失败者就地标 `[⚠️ 待复核]`。

---

## 一、流程概览

共 6 个配置段落，每段以独立 `AskUserQuestion` 呈现。
用户可随时输入 `/config` 或 `/重新配置` 重新触发本流程。

---

## 二、配置段落

### 段落 0：使用场景

**目的**：确认用户当前使用场景，以便 W2–W4 适配对应的报告骨架、出口格式与术语风格。

**AskUserQuestion 参数**：
- question: "请选择本次使用的场景（决定报告结构与出口风格）："
- header: "使用场景"
- multiSelect: false
- options:
  1. label: "学术研习（推荐）" / description: "法学院课程作业、判例研读沙龙报告、教学个案分析——完整双层结构 + 涵摄四步全展开"
  2. label: "诉讼实务参考" / description: "律师案件评估底稿、法务合规研判、复议/监察办案备忘——可选轻量模式 + 风险清单出口"
  3. label: "行政执法事前自审" / description: "行政机关在作出行政行为之前的依法行政自检——以拟作出行为为审查对象，聚焦六要素 + 规范性文件合法性体检"

写入 `.user-config.md` 字段：`scenario: academic | litigation | pre-enforcement`

**场景差异指引**：

| 场景 | 报告视角 | 可受理性层 | 可证立性深度 | 出口格式 |
|------|---------|-----------|------------|---------|
| 学术研习 | 第三方学术评价 | 完整 8 闸门 | 全量展开 | 鉴定式标准格式 |
| 诉讼实务 | 律师/法务办案参考 | 完整 8 闸门 | 可选轻量模式（聚焦争点） | 标准格式 + 风险清单 |
| 事前自审 | 行政机关内部自检 | 简化（无原告/被告，改为"拟行为相对人"/"本机关"） | 六要素逐项 + 规范性文件合法性体检 | 内部备忘格式 + 合法性体检报告 |

---

### 段落 1：行政法知识库

**目的**：确认用户是否拥有行政法解释/评注类知识库，以决定素材获取层级。该知识库既可服务于案例研习，亦可服务于实务参考。

先向用户展示价值说明：

> **关于行政法知识库**
>
> 鉴定式行政法案例分析的深度取决于对法律概念的精确把握。在审查行政行为合法性时，遇到"明显不当""正当程序""信赖利益""公共利益"等需要价值填充的概念时，**行政法条文评注、最高人民法院对行政诉讼法及相关司法解释的理解与适用类著作、以及行政法学体系书**能为要件解释提供专业、丰富、可引用的依据。
>
> 如果您已自制此类知识库 skill，本插件会按需调用；如尚未制作，可参考下述自助方式：
>
> **自助制作指引**：①获取权威行政法评注/理解与适用类 PDF；②用文档解析工具转为 Markdown；③按法条号或章节切分，建立索引；④存放在 `~/.qoderwork/skills/<您的命名>/` 目录下，附 SKILL.md 说明检索规则。

**AskUserQuestion 参数**：
- question: "是否已自制可供调用的行政法解释/评注类知识库 skill？"
- header: "行政法知识库"
- multiSelect: false
- options:
  1. label: "已有，希望注册到本插件" / description: "已有行政法相关的知识库 skill，可提供 skill 名称"
  2. label: "暂无，由本插件自行完成解释" / description: "本插件将通过方法论工具箱 + 联网检索学术与实务文章作为论据补充"
  3. label: "暂时跳过" / description: "由我后续自行决定"

如选 A，再追问 skill 名称（多个用逗号分隔）和每个 skill 的覆盖领域简述，写入 `.user-config.md`。

---

### 段落 2：工具配置

**AskUserQuestion 参数**：
- question: "请确认以下工具的配置状态（可多选已配置项）："
- header: "工具配置"
- multiSelect: true
- options:
  1. label: "法律检索 MCP" / description: "【铁律必需】法条检索服务，缺失将触发降级模式"
  2. label: "联网搜索" / description: "WebSearch 或同类搜索 MCP，用于案例检索与学说验证"
  3. label: "文档解析" / description: "doc-parse / ale-file-parser，处理 docx/pdf 案情输入"
  4. label: "Word 输出" / description: "cx-md2word / docx 技能，鉴定式标准格式终稿输出"

**降级模式警告**：法律检索 MCP 未配置时，显示：
```
⚠ 降级模式启动：法律检索 MCP 未配置。
铁律约束：所有法条引用将标注 [未经校验]，不保证现行有效性。
建议：在连接器面板启用任一法律检索类 MCP 后重新运行 /config。
```

---

### 段落 3：法律检索能力槽

**目的**：本 skill 与具体法律检索 MCP 产品**解耦**。当用户在段落 2 勾选了"法律检索 MCP"后，本段落要求用户声明所选服务商的工具名映射与字段契约，运行时通过占位符 `${LEGAL_SEARCH.<能力名>}` 解析为实际工具调用。

**AskUserQuestion 第 1 题（服务商展示名）**：
- question: "你为法律检索 MCP 配置的服务商展示名是什么？"
- header: "服务商名称"
- multiSelect: false
- options:
  1. label: "用户自填（推荐）" / description: "例如：元典 / 北大法宝 / 内部法规库 等"
  2. label: "暂不命名" / description: "仅记录为 \"LegalSearch\""

**AskUserQuestion 第 2 题（工具名映射）**：
- question: "请提供你所选服务商在你环境中的实际工具名（5 项能力，必填项至少前 2 项）："
- header: "工具名映射"
- 由用户填入五个能力槽：
  1. `get_article`：已知法律名+条号 → 取条文原文（**必填**）
  2. `search_article`：语义检索法条+司法解释（**必填**）
  3. `get_law_list`：法规列表/前置法检索（可选）
  4. `search_case`：案例语义检索（可选）
  5. `get_case_list`：案例列表（可选）

**AskUserQuestion 第 3 题（字段契约）**：
- question: "请声明你所选服务商返回 JSON 中的字段契约："
- header: "字段契约"
- 由用户填入下列字段（提供合理默认值）：
  1. `timeliness_field`：时效字段名（默认 `timeliness`）
  2. `timeliness_active_value`：现行有效的取值（默认 `现行有效`）
  3. `effectiveness_field`：效力层级字段名（默认 `effectiveness`）
  4. `title_format`：法律标题入参格式（默认 `中文全称`）
  5. `number_format`：条号入参格式（默认 `中文数字`）

**写入 `.user-config.md` 的 yaml 块**：

```yaml
legal_search:
  enabled: true | false
  provider_name: "<用户填入的展示名>"
  tools:
    get_article:    "<工具名>"
    search_article: "<工具名>"
    get_law_list:   "<工具名 | null>"
    search_case:    "<工具名 | null>"
    get_case_list:  "<工具名 | null>"
  contract:
    timeliness_field:        "timeliness"
    timeliness_active_value: "现行有效"
    effectiveness_field:     "effectiveness"
    title_format:            "中文全称"
    number_format:           "中文数字"
```

**运行时解析约定**：本 skill 全部文档中的 `${LEGAL_SEARCH.<能力名>}` 占位符，在 W1–W4 任一阶段触发调用前由 Agent 读取 `.user-config.md` 中对应字段替换为实际工具名后调用。

---

### 段落 4：报告格式偏好

**说明**：W4 终稿默认先产出 Markdown，随后询问是否转换为 Word (.docx)。本段落仅影响 W4 询问时的默认按钮偏好，以及是否在无用户交互情况下自动生成 Word。用户亦可在单次案件内通过 `_case_meta.md` 或 `/format md | /format docx | /format ask` 命令覆盖本项默认值（详见 SKILL.md §4.3）。

**AskUserQuestion 参数**：
- question: "W4 终稿输出后，Word 转换的默认偏好是？"
- header: "报告格式偏好"
- multiSelect: false
- options:
  1. label: "先出 Markdown，再询问是否转 Word（推荐）" / description: "默认流程：MD 终稿 → 询问用户 → 用户确认后调用 cx-md2word 生成 .docx"
  2. label: "仅输出 Markdown" / description: "不询问 Word 转换，仅落盘 Markdown 终稿"
  3. label: "MD + Word 双份" / description: "MD 落盘后自动调用 cx-md2word 生成 .docx，无需再询问"

写入 `.user-config.md` 字段：`report_format_preference: md_then_ask | md_only | md_and_docx`

> 报告统一以纯中文呈现，不附加外语术语标注。九级标题体系、脚注格式与 Word legal 预设映射均由 `format/format-and-template.md` 唯一维护。

---

### 段落 5：保存配置

**执行逻辑**（无需用户交互）：

1. 将前 4 段收集的配置写入 `~/.qoderwork/skills/gutachten-admin-case/.user-config.md`：

```markdown
# 用户配置（gutachten-admin-case）

最后更新：YYYY-MM-DD

## 使用场景

scenario: academic | litigation | pre-enforcement

## 行政法知识库注册

- skill1：<skill 名称>，覆盖领域：<覆盖领域>
（无 → 留空 / 注明"未注册"）

## 工具链

- **法律检索 MCP**（必须 · 校验铁律）：已配置 / 未配置（降级模式）
- 联网搜索工具：是 / 否
- 文档解析工具：是 / 否
- Word 输出工具：是 / 否

## 法律检索能力槽

```yaml
legal_search:
  enabled: true | false
  provider_name: "<展示名>"
  tools:
    get_article:    "<工具名>"
    search_article: "<工具名>"
    get_law_list:   "<工具名 | null>"
    search_case:    "<工具名 | null>"
    get_case_list:  "<工具名 | null>"
  contract:
    timeliness_field:        "timeliness"
    timeliness_active_value: "现行有效"
    effectiveness_field:     "effectiveness"
    title_format:            "中文全称"
    number_format:           "中文数字"
```

## 报告格式偏好

report_format_preference: md_then_ask | md_only | md_and_docx
```

2. **§6.5 法条锚定表运行时校验**（铁律强制步骤，L2 模式跳过）：
   - 在 L0/L1 模式下，调用 `${LEGAL_SEARCH.get_article}` 对 `SKILL.md §6.5` 法条锚定表 **A–J 十组全部语义条目**逐项核验"现行编号"与"条文要旨"是否一致。本步骤为运行时 MCP 逐项核验，不存在独立脚本文件。
   - 命中失败者：就地在锚定表对应行末尾追加 `[⚠️ 待复核]` 标记，并在本次确认提示中列出待复核清单（语义名称 + 失败原因），等待用户人工核对后方可进入 W1。
   - 校验全部通过：将"§6.5 锚定表 N 条全部通过"纳入确认提示。
   - L2 模式：跳过本步骤，并在确认提示中明确"§6.5 锚定表运行时校验已因 MCP 不可用整维度跳过；报告须按 L2 降级规则处理"。

3. 同步至 memory：`gutachten-admin-case 用户配置：[摘要] + 锚定表校验结果`

4. 确认提示：`配置已保存。§6.5 法条锚定表校验：N 条通过 / M 条待复核。输入案情即可开始鉴定式分析，或输入 /config 重新配置。`

---

## 三、降级模式规则

| 级别 | 条件 | 行为 |
|------|------|------|
| L0 正常 | 法律检索 MCP + ≥1 知识库 | 全功能运行 |
| L1 部分降级 | 法律检索 MCP 可用，无知识库 | 素材获取跳过知识库层，脚注标注 [无评注支撑] |
| L2 严重降级 | 法律检索 MCP 不可用 | 所有法条标注 [未经校验]；W4 核验维度 D1 自动跳过 |

降级约束：L2 模式下，报告首页必须添加免责声明。

---

## 四、重新触发条件

1. `.user-config.md` 文件不存在或损坏
2. 用户主动输入 `/config` 或 `/重新配置`
3. 检测到已注册知识库技能不可用（提示部分重新配置）
4. 工具链状态变化导致降级级别变更时，提示用户确认

---

## 五、与下游流程的连接

配置完成后：
- 自动进入待命状态，等待用户输入案情
- 案情输入后触发 `1-case-intake.md`（W1 流程）
- 配置信息在整个工作流生命周期内持续可用

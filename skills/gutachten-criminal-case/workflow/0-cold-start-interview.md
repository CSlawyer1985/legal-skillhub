# 首次使用配置访谈

> 本文件定义鉴定式刑法案例研习技能的首次使用配置流程。
> 触发条件：用户首次调用本技能，或 `.user-config.md` 不存在/损坏时自动执行。

---

## 一、流程概览

共 5 个配置段落，每段以独立 `AskUserQuestion` 呈现。
用户可随时输入 `/config` 或 `/重新配置` 重新触发本流程。

> **学派立场配置（段落 1.5）是本技能的关键配置项**——基于"中国当代刑法学不预设权威学说"的设计哲学，用户可对 3 项重大分歧议题各自选择立场。**未配置时全部默认采本技能推荐立场**。

---

## 二、配置段落

### 段落 1：刑法评注知识库

**目的**：确认用户是否拥有刑法学术知识库，以决定素材获取层级。

**AskUserQuestion 参数**：
- question: "您是否已配置刑法评注/教科书知识库？请选择已有的知识库类型（可多选）："
- header: "刑法知识库"
- multiSelect: true
- options:
  1. label: "条文评注全书类知识库" / description: "逐条评注（立法理由、司法解释、案例汇编），适合检索某一条款的全景信息"
  2. label: "刑法学体系书类知识库" / description: "总论 + 分论体系教材，适合学理深度论证"
  // Other 选项 → 用户可填入：自建知识库技能名称等

**后续处理**：
- 若用户选择 ≥1 个知识库类型 → 提示用户提供具体的 skill name；
- 若用户选择 Other 并填入自建知识库 → 提示注册格式：`skill-name: [知识库技能名]`；
- 若用户无任何知识库 → 提供自建指引：
  ```
  自建知识库指南：
  1. 准备 PDF/EPUB 格式的刑法教材
  2. 使用 MinerU 或其他文档解析工具解析为结构化文本
  3. 通过 qmind-knowledge 技能创建知识库
  4. 在此处填入知识库技能名称
  ```

**注册格式**：
```yaml
criminal_law_kbs:
  - skill: "criminal-law-annotated"
    type: "条文评注全书"
  - skill: "user-custom-kb-name"
    type: "用户自建库"
```

---

### 段落 1.5：学派立场配置

**目的**：让用户在几个重大观点分歧上选定立场。这些分歧会直接影响案例分析的结论走向。**用户可全部留空采本技能默认立场**，仅对自己有明确偏好的议题手动选择。

**展现方式**：先用一段通俗文字向用户解释为什么需要配置，再以单一 `AskUserQuestion`（multiSelect: true）让用户选择"我希望对哪些议题手动配置立场"；对每个被勾选的议题，通过后续单选题逐一询问。

**AskUserQuestion 参数（第一道筛子）**：
- question: "以下 3 个议题在刑法学界存在重大分歧，不同立场可能导致案例分析结论不同。您希望手动选择立场吗？（不勾选的议题默认采本技能推荐立场）"
- header: "学派立场"
- multiSelect: true
- options:
  1. label: "全部默认（推荐快速上手）" / description: "全部议题采本技能推荐立场，适合大多数场景。"
  2. label: "我要逐项配置" / description: "对以下 3 个议题逐一选择立场，本技能将依次询问。"

**若用户选"我要逐项配置"，依次出 3 道单选题**：

| 议题 | 通俗解释 | 推荐立场（默认） | 备选立场 |
|---|---|---|---|
| `aberratio_ictus` | **打击错误**：行为人想打 A 却误中了 B，该怎么定性？ | **具体符合说**（对 A 算未遂、对 B 算过失，两罪合并处理） | **法定符合说**（A 和 B 都是"人"，直接算故意杀人既遂） |
| `accidental_defense` | **偶然防卫**：行为人出于犯罪意图攻击他人，凑巧客观上阻止了对方的犯罪行为（如甲想杀乙，恰好乙正在杀丙），该怎么处理？ | **未遂犯说**（主观上有犯罪意图，客观上没造成真正的法益损害，算未遂） | **无罪说**（客观上结果是正当的，不构成犯罪） |
| `interpretation_school` | **分则解释方法**：解释刑法分则条文时，应该侧重实质判断还是形式判断？ | **实质解释论**（先看行为是否真正值得处罚，再回头看构成要件能否涵盖） | **形式解释论**（先看形式上是否符合构成要件，不符合的直接用"情节显著轻微"出罪） |

**`.user-config.md` 写入格式**：

```yaml
doctrinal_stances:
  schema_version: "1.0"
  default_position: "recommended"  # 用户未配置项的兜底立场
  per_issue:
    aberratio_ictus: "A"           # A=具体符合说 / B=法定符合说
    accidental_defense: "A"        # A=未遂犯说 / B=无罪说
    interpretation_school: "A"     # A=实质解释论 / B=形式解释论
```

**agent 行为契约（适用于所有 W3 写作）**：

1. 读取 `.user-config.md` 的 `doctrinal_stances` 字段；
2. 在每个 🔀 学派双轨标注处，按 user-config 选定立场展开主线论证；
3. 对未明示配置的议题，自动按推荐立场展开；
4. 当案件事实落在上述 3 项议题之外的争议情境时（如客观归责本土化、§20第3款性质、容许构成要件错误、不能犯/未遂区分等），agent 按本技能推荐立场处理即可，无需询问用户，但须在脚注中说明所采立场；
5. 所有立场切换均在脚注中显性说明（"按 user-config doctrinal_stances.aberratio_ictus = A，本文采具体符合说"）。

---

### 段落 2：工具配置

**目的**：确认必要工具链的可用性。

**AskUserQuestion 参数**：
- question: "请确认以下工具的配置状态（可多选已配置项）："
- header: "工具配置"
- multiSelect: true
- options:
  1. label: "法律检索 MCP" / description: "【铁律必需】法条检索服务，缺失将触发降级模式（具体服务商在下一段配置）"
  2. label: "联网搜索" / description: "WebSearch 或同类搜索 MCP，用于案例检索与学说验证"
  3. label: "文档解析" / description: "MinerU 或其他同类文档解析工具，处理 docx/pdf 案情输入"
  4. label: "Word 输出" / description: "cx-md2word / docx 技能，学术格式终稿输出"

**降级模式警告**：
- 法律检索 MCP 未配置时，显示：
  ```
  ⚠ 降级模式启动：法律检索 MCP 未配置。
  铁律约束：所有法条引用将标注 [未经校验]，不保证现行有效性。
  建议：在连接器面板启用任一法律检索类 MCP 后重新运行 /config。
  ```

---

### 段落 2.5：法律检索能力槽

**目的**：本 skill 与具体法律检索 MCP 产品**解耦**。当用户在段落 2 勾选了"法律检索 MCP"后，本段落由 agent **自动探测**所选服务商的工具能力并写入配置。用户只需告知服务商名称，无需手动填写工具名或 JSON 字段。

**AskUserQuestion（服务商确认）**：
- question: "你使用的是哪个法律检索服务？agent 将自动探测该服务的可用工具并完成配置。"
- header: "法律检索"
- multiSelect: false
- options:
  1. label: "北大法宝" / description: "北大法宝法律法规与案例检索"
  2. label: "华宇元典" / description: "华宇元典法律信息检索平台"
  3. label: "其他法律检索 MCP" / description: "已连接的其他法律检索类 MCP 服务"

**agent 自动探测流程**（用户回答后自动执行，无需用户干预）：

1. 调用 `qw_mcp_list`（keyword 为用户选定的服务商名称）列出该服务下的可用工具；
2. 对每个匹配工具调用 `qw_mcp_get` 获取参数与返回 schema；
3. 将发现的工具自动映射到 5 项能力槽（`get_article` / `search_article` / `get_law_list` / `search_case` / `get_case_list`），其中前两项为必填、后三项可选；
4. 从返回 schema 中提取时效字段名与效力字段名，写入 `contract`；
5. 将探测结果展示给用户确认后保存。

**探测失败处理**：若无法自动识别工具，显示：
```
⚠ 无法自动识别该服务商的工具。
请确认法律检索 MCP 已正确连接后重试，或选择"其他"手动描述你使用的服务。
```

**写入 `.user-config.md` 的 yaml 块**（由 agent 自动填充）：

```yaml
legal_search:
  enabled: true | false
  provider_name: "<用户选定的服务商>"
  tools:
    get_article:    "<自动探测>"
    search_article: "<自动探测>"
    get_law_list:   "<自动探测 | null>"
    search_case:    "<自动探测 | null>"
    get_case_list:  "<自动探测 | null>"
  contract:
    timeliness_field:        "timeliness"
    timeliness_active_value: "现行有效"
    effectiveness_field:     "effectiveness"
    title_format:            "中文全称"
    number_format:           "中文数字"
```

**运行时解析约定**：本 skill 全部文档中的 `${LEGAL_SEARCH.<能力名>}` 占位符，在 W1–W4 任一阶段触发调用前由 agent 读取 `.user-config.md` 中的 `legal_search.tools.<能力名>` 替换为实际工具名后调用。字段契约同理。

---

### 段落 3：报告格式

**AskUserQuestion 参数**：
- question: "请选择鉴定式报告的输出格式："
- header: "报告格式"
- multiSelect: false
- options:
  1. label: "学术格式 (推荐)" / description: "A4排版，九级标题体系，Word (.docx) 输出，含脚注与引用格式"
  2. label: "Markdown 原始格式" / description: "纯 Markdown 输出，适合后续自定义排版或嵌入其他文档"

**补充说明**：
- 学术格式依赖 `canonical-report-template.md` 模板
- Markdown 格式仍遵循标题层级规范，但不生成 Word 文件

---

### 段落 4：保存配置

**执行逻辑**（无需用户交互）：

1. 将前 3 段（含 1.5）收集的配置写入 `.user-config.md`：
   ```markdown
   # 用户配置

   ## 知识库
   [列表]

   ## 学派立场配置
   doctrinal_stances:
     default_position: "A"
     per_issue:
       [详见 yaml]

   ## 工具链
   - 法律检索 MCP: ✓/✗（详见下方 legal_search 能力槽）
   - 联网搜索: ✓/✗
   - 文档解析: ✓/✗
   - Word 输出: ✓/✗

   ## 法律检索能力槽
   ```yaml
   legal_search:
     enabled: true | false
     provider_name: "<用户选定的服务商>"
     tools:
       get_article:    "<自动探测>"
       search_article: "<自动探测>"
       get_law_list:   "<自动探测 | null>"
       search_case:    "<自动探测 | null>"
       get_case_list:  "<自动探测 | null>"
     contract:
       timeliness_field:        "timeliness"
       timeliness_active_value: "现行有效"
       effectiveness_field:     "effectiveness"
       title_format:            "中文全称"
       number_format:           "中文数字"
   ```

   ## 报告格式
   [学术格式 / Markdown]

   ## 配置时间
   [ISO 8601]
   ```

2. 同步至 memory（target: memory）：
   ```
   gutachten-criminal-case 用户配置：[摘要 + 学派立场摘要]
   ```

3. 确认提示：
   ```
   配置已保存。输入案情即可开始鉴定式分析，或输入 /config 重新配置。
   ```

---

## 三、降级模式规则

### 三级回退机制

| 级别 | 条件 | 行为 |
|------|------|------|
| L0 正常 | 法律检索 MCP + ≥1 知识库 | 全功能运行 |
| L1 部分降级 | 法律检索 MCP 可用，无知识库 | 素材获取跳过 Tier 1，脚注标注 [无评注支撑] |
| L2 严重降级 | 法律检索 MCP 不可用 | 所有法条标注 [未经校验]；W4 核验维度 D1 自动跳过 |

### 降级模式约束：
- L2 模式下，报告首页必须添加免责声明
- 每次调用均检查工具可用性，动态切换降级级别
- 用户可通过 `/config` 随时升级配置
- **学派立场配置不受降级模式影响**——立场切换是纯文档内逻辑，不依赖外部工具

---

## 四、重新触发条件

以下情形自动触发配置访谈：
1. `.user-config.md` 文件不存在
2. `.user-config.md` 内容解析失败（格式损坏）
3. 用户主动输入 `/config` 或 `/重新配置`
4. 用户输入 `/学派配置` 或 `/doctrine-config` 仅触发段落 1.5
5. 检测到已注册知识库技能不可用（提示部分重新配置）
6. 工具链状态变化导致降级级别变更时，提示用户确认

---

## 五、与下游流程的连接

配置完成后：
- 自动进入待命状态，等待用户输入案情
- 案情输入后触发 `1-case-intake.md`（W1 流程）
- 配置信息（含学派立场）在整个工作流生命周期内持续可用
- W3 写作过程中如遇上述 3 项议题之外的新争议，agent 按本技能推荐立场处理，在脚注中说明即可

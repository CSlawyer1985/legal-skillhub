---
name: patent-mining-disclosure-skill
description: "通用中国专利挖掘发现与专利说明书式技术交底生成全流程：扫描项目后先产出含轻量相似专利检索的专利点资产清单，再按用户取舍生成只包含专利技术内容的说明书式文本，强调发明内容、技术思路、具体实施方式、参数/异常分支、深度查新与自检。| Patent mining portfolio triage with prior-art screening and specification-style disclosure drafting."
version: "1.17.0"
user-invocable: true
argument-hint: "[可选：项目路径或技术主题关键词]"
allowed-tools: Read, Write, Edit, Grep, Glob, WebSearch, Bash
---

# 专利挖掘与交底书生成

本技能覆盖 **专利点挖掘** → **专利点资产清单与轻量相似专利初筛** → **取舍确认** → **深度查新与差异化** → **专利说明书式技术交底生成** → **版本化交付** → **自检完善** 全流程；分步指令在 **`prompts/`**，每步执行前 **`Read`** 对应文件，与步骤的对照见「Prompt 文件映射」。

## 环境与约定

- **语言**：默认与用户语种一致；专利与法律术语采用行业常用表述。
- **取舍门禁（Step 3–4）**：扫描后必须先给出 **专利点资产清单**，包含可申请点、暂不适合申请点、建议商业秘密保护点、评分与理由，并对每个拟申请/可申请候选点做 **轻量相似专利初筛**（优先 Google Patents / 必要时国知局或 WebSearch）。除非用户明确要求跳过，否则不得直接生成交底书。用户确认“写哪些、不写哪些、秘密保护哪些”后，再进入深度查新与交底书。
- **相似不等于否定（Step 3–5）**：检索到相似公开文献时，不得简单判定“不能写”。须判断其覆盖程度：高度重合则放弃或改写为改进点；部分相似则收窄区别特征；仅背景相似则可继续申请并在查新中区分；核心细节公开代价高时可转商业秘密。
- **说明书式正文（Step 7）**：生成内容只写专利相关技术，不写注意事项、联系人、委托确认等非技术正文。正文标题下须写明 **发明人/发明者** 元信息；若用户未给出，不得编造，先询问或写为 `[待填写]`。发明内容必须写清方法步骤、系统模块和有益效果；具体实施方式必须展开技术思路、字段/参数、样本/规则/模型、异常分支和替代实施方式。**交底书不是只写概念文字**：必须写到代理人能看懂整体闭环并据此撰写权利要求，至少包含端到端数据流、关键数据结构、处理伪代码或规则表、输入/输出样例、异常/回退路径和与系统模块的对应关系；不足时先补正文再交付。
- **专利簇通俗说明清单（Step 9）**：一次交付 2 件及以上相关专利时，定稿后必须额外产出一份通俗清单，说明这一簇专利整体在干什么、每件专利分别保护什么、方法方案和系统方案有什么区别、各专利是否交叉以及边界如何划分。该清单面向业务/研发负责人阅读，不写法律套话，不替代正文。
- **交付选择（Step 7）**：交付前须让用户选择 **Markdown** 或 **Word** 二选一；若选 Word，再让用户选择图示方式：本地渲染 PNG、生成专利附图风格提示词，或调用 OpenAI-compatible 图片接口自动生图并嵌入 Word；还须确认是否需要在 Word 后继续导出 **PDF**。
- **自动生图门禁（Step 7）**：用户选择自动生图时，生成 Word 前必须先运行 `tools/mermaid_render.py --check-image-env` 或等价检查，确认 `OPENAI_BASE_URL` 与 `OPENAI_API_KEY` 已配置；未配置则只给出当前系统的设置命令并等待用户补齐，不得继续生成文档。URL 不得写死，必须来自用户提供的环境变量或命令参数。
- **图示定稿（Step 7）**：正文中的方法流程图、系统结构图和关键子流程图均先用 fenced **mermaid** 表达结构；按用户选择转 PNG、转生图提示词或自动生图。执行方式、**`mmdc`** 安装、图片接口参数与降级规则见下表「交底书定稿交付」行及 **`tools/README.md`**。
- **版本化产出目录（必遵）**：生成或迭代交底书时须先 **`Read`** `prompts/versioned_output.md`。用户给出的目录视为专利组/案件根目录，根目录只保留 **`版本索引.md`**、**`交底书修订对话记录.md`** 和 `vN-说明-YYYYMMDDHHMMSS/` 版本文件夹；`.md`、`.docx`、`.pdf`、专利簇清单和图片资源均写入当前版本目录，不得再把多版时间戳文件平铺到同一层。

---

## 触发条件

在用户使用以下任一方式时启用本技能：

- 明确提及：专利挖掘、专利点、技术交底书、交底书、专利交底书、查新、现有技术对比等
- 斜杠或简短指令：如 `/patent-mining-disclosure-skill`、`/patent-disclosure`、`/交底书`
- **迭代模式（按意图识别）**：当用户意图明显是在**已有交底书或上一轮输出**上继续工作（如改章节、补实施例、补材料、修正参数/事实、调整表述等），**无需**用户写出「迭代」等固定词，也**不必**询问是否进入迭代——Agent 应 **`Read`** **`prompts/versioned_output.md`** 与 **`prompts/iteration_context.md`**，再 **`Read`** `prompts/merger.md`（侧重**新材料、扩展合并**）或 `prompts/correction_handler.md`（侧重**纠错、与事实或风格不符**），**严格按该文件开头的「执行门禁」**（优先执行，不可跳过）**做完合并或纠正**，按本轮用户选择在下一个版本目录中另存为新文件：**`{案件名}_{YYYYMMDDHHmmss}.md`** 或 **`.docx`**（与首次定稿同一命名规则，见 **`disclosure_builder.md` §7.6**），**不覆盖**旧稿（除非用户明确要求）。**禁止**在迭代意图已成立时默认回到 Step 3–4 专利点全文分析（除非用户明确要求重新挖掘专利点）。对话中**已出现**交底书路径、附件或上文刚交付的草稿时，优先按迭代处理；若用户未明确本轮交付格式，沿用上一轮格式。

---

## 工具与数据来源

按任务选用能力；具体工具名称以当前 Agent 环境为准。

若扫描范围内含 **Word（.docx）** 或 **PowerPoint（.pptx）**，须在 Step 2 纳入阅读前用本仓库 **`docx_to_md.py`** / **`pptx_to_md.py`** 转为 Markdown；依赖 **`pip install -r requirements.txt`**，命令与说明见下表对应行。

### 常见任务与建议方式

| 任务 | 建议方式 |
|------|----------|
| 加载分步指令 | **`Read`** → `${CLAUDE_SKILL_DIR}/prompts/*.md`，见下表 |
| 读代码、设计文档、PDF、图片 | 文件读取工具；大仓库先用搜索/语义检索定位再精读 |
| Word（.docx）→ Markdown + 抽取图片（扫描前） | `Bash` → `python3 ${CLAUDE_SKILL_DIR}/tools/docx_to_md.py --input {path}.docx --output {dir}/{name}.md`；图片默认写入与 `.md` 同级的 `{name}_media/`；需 `pip install -r requirements.txt`（含 mammoth）；复杂版式可改由所内导出 PDF/MD 再扫 |
| PowerPoint（.pptx）→ Markdown + 抽取图片（扫描前） | `Bash` → `python3 ${CLAUDE_SKILL_DIR}/tools/pptx_to_md.py --input {path}.pptx --output {dir}/{name}.md`；默认 `{name}_media/`；需 `pip install -r requirements.txt`（含 python-pptx）；**旧版 .ppt 不支持**，请先另存为 `.pptx`；图表/SmartArt 等若未以图片形状嵌入则可能仅能从备注或另行导出补全 |
| 罗列目录、按名找文件 | 目录列举 / 按文件名搜索 |
| 轻量相似专利初筛（Step 3–4） | 生成资产清单时执行；优先用 **Google Patents** 与 WebSearch 搜每个拟申请候选点的 1–3 组关键词，记录最相近 0–3 条、相似度等级、可区分点和对分类/评分的影响。若网络不可用，须在清单中明确标注“未完成公开检索，不作为最终可申请结论”。 |
| 深度联网查新（Step 5） | 用户确认拟申请点后执行；执行前 **`Read`** `prompts/prior_art_search.md`。**中国专利公布公告**：优先 **`Bash`** 运行 `cnipa_epub_search.py`；**须在生成命令前**归纳 **2～8 个相关度高的语义块**；**执行时须分多次调用**，**每次仅传一个**词块，**自行按 `pub_number` 合并**多轮 `EPUB_HITS_JSON`（勿单次工具调用堆多个 argv，见该 prompt）。一步拉取+解析、**不写 HTML 落盘**；须 **`pip install -r tools/requirements-cnipa.txt`** 且 **`python -m playwright install chromium`**。**`abstract` 规定必用**同该 prompt。需整句一次 AND 或保存 HTML 时用 `cnipa_epub_crawler.py`；异常或无果再 **WebSearch** |
| 交底书定稿交付（**Markdown / Word 二选一**） | 交付前先让用户选择 **Markdown** 或 **Word**；若选 Word，再让用户选择图示方式：**PNG**（本地 `mmdc` 渲染并嵌入 Word）、**生图提示词**（将 mermaid 方法流程图、系统结构图和关键子流程图改写为适合 gpt-image 等工具的专利附图提示词，由用户自行生图后替换）或 **自动生图**（调用 OpenAI-compatible 图片接口生成 PNG 并嵌入 Word），并确认是否同时导出 **PDF**。所有图均先用 fenced ``mermaid`` 表达结构，**不要** ASCII 文字流程图/框图。PNG 模式执行 **`tools/mermaid_render.py`**；提示词模式执行 **`tools/mermaid_render.py --diagram-mode prompt`**；自动生图先执行 **`tools/mermaid_render.py --check-image-env`**，确认 `OPENAI_BASE_URL` 与 `OPENAI_API_KEY` 存在后再执行 **`tools/mermaid_render.py --diagram-mode image-api`**；若需要 PDF，追加 **`--pdf`**（需 LibreOffice / soffice，失败时保留 Word 并提示手动转换）。若检查失败，只向用户给出 export/set 命令并等待补齐，**不得**生成定稿。详见 **`tools/README.md`** |
| 保存交底书路径 | 写入用户指定的专利组/案件根目录；未指定时可建议 `./outputs/{案件标识}/`。交付前 **`Read`** `prompts/versioned_output.md`，创建 `vN-说明-YYYYMMDDHHMMSS/`，所有 `.md`、`.docx`、`.pdf`、图片资源和专利簇清单写入该版本目录；根目录只维护 `版本索引.md` 与修订日志。主文件名仍须为 **`{案件名}_{YYYYMMDDHHmmss}`**（见 `disclosure_builder.md` §7.6，**含首次定稿与迭代**），勿默认覆盖旧稿；`outputs/` 整目录默认由 `.gitignore` 忽略 |
| 迭代对话留档 | 每轮 **merger / correction** 交付后，在案件根目录追加 **`交底书修订对话记录.md`**，并更新 **`版本索引.md`**（**`tools/iteration_dialog_log.py`** 或等价手工），见 **`prompts/iteration_context.md`** 与 `prompts/versioned_output.md` |

---

## Prompt 文件映射

| 步骤 | 文件 | 用途 |
|------|------|------|
| Step 1 | `prompts/intake.md` | 边界与输入问题 |
| Step 2 | `prompts/project_scan.md` | 项目文档扫描；**须**对 `.docx`/`.pptx` 先转换再读（见该文件「Office 文档」节）；独立图片目录可跳过 |
| Step 3–4 | `prompts/patent_points_analyzer.md` | 专利点资产清单、轻量相似专利初筛、评分、不可成案原因、商业秘密建议、用户取舍确认 |
| Step 5 | `prompts/prior_art_search.md` | 联网查新与分析要求 |
| Step 6 | `prompts/disclosure_preview.md` | 全文前的摘要预览 |
| Step 7 | `prompts/disclosure_builder.md` + `prompts/template_reference.md` | 专利说明书式技术正文结构、脱敏、发明内容、具体实施方式、参数/异常分支、图示规范 |
| Step 7/9/迭代 | `prompts/versioned_output.md` | 用户产出目录规范：`版本索引.md`、`vN-说明-时间戳/`、版本内产物与图片资源、根目录修订日志 |
| Step 8 | `prompts/disclosure_self_check.md` | 内部自检，不写入正文 |
| Step 9 | `prompts/patent_family_explainer.md` | 多件相关专利定稿后的通俗说明清单：侧重点、方法/系统区别、交叉与边界、阅读路线 |
| 迭代 | `prompts/iteration_context.md` | 迭代意图、落盘命名、**修订对话记录 md**（含对话/记录时间） |
| 迭代 | `prompts/merger.md` | 新材料增量合并；**文首含门禁**；输出本轮选择的 `{案件名}_{时间戳}.md` 或 `.docx` |
| 迭代 | `prompts/correction_handler.md` | 对话纠正；**文首含门禁**；输出本轮选择的 `{案件名}_{时间戳}.md` 或 `.docx` |

---

## 主流程（执行顺序）

1. **`Read`** `intake.md` → 执行 Step 1  
2. **`Read`** `project_scan.md` → 执行 Step 2  
3. **`Read`** `patent_points_analyzer.md` → 执行 Step 3–4，先输出含轻量相似专利初筛的专利点资产清单并等待用户确认取舍；若用户明确说“跳过清单/直接生成”，仍须用 3–6 行简要说明已按用户要求跳过清单和轻量初筛  
4. 用户确认拟申请的专利点后，**`Read`** `prior_art_search.md` → 执行 Step 5 深度查新；如用户把某点标记为商业秘密保护，则不得对该点生成交底书正文或公开化描述  
5. **`Read`** `disclosure_preview.md` → 执行 Step 6；用户可跳过  
6. **`Read`** `versioned_output.md`、`disclosure_builder.md` 与 **`Read`** `template_reference.md` → 执行 Step 7（先确认交付格式；先创建/选择当前 `vN-说明-时间戳/` 版本目录；**首次交付**的 `.md` 或 `.docx` 亦须 **`{案件名}_{YYYYMMDDHHmmss}`**，见 §7.6）；交付对话中**须**按 **`disclosure_builder.md` §7.9** 补充「权利要求偏向点」建议交互（**仅对话**，不入正文）  
7. **`Read`** `disclosure_self_check.md` → 内部执行 Step 8，修订后交付  
8. 若本轮交付 2 件及以上相关专利，**`Read`** `patent_family_explainer.md` → 执行 Step 9，另存通俗说明清单；清单须写入当前版本目录，文件名带时间戳；最后更新根目录 **`版本索引.md`**  

**禁止**：未经过 Step 3–4 专利点资产清单与用户取舍确认就默认直接成文；正文中包含「注意事项」「技术联系人」「自检清单」「委托确认」等非技术内容；自检仅内部使用。

---

## 迭代模式（摘要）

**启用方式**：根据用户**自然语言意图**判断（见上文「触发条件」），**不要求**固定关键词，**默认不**为「是否迭代」打断用户。

- **补充材料 / 扩展章节**或 **按 §7.9 声明权利要求偏向点后的说明书式强化**：`Read` → `versioned_output.md` → `iteration_context.md` → `merger.md`；合并结果按用户选择写入下一个版本目录，并**另存为**带时间戳的 `.md` 或 `.docx`（见 §7.6）；**追加** `交底书修订对话记录.md` 并更新 `版本索引.md`；完成后**必须**输出「合并摘要」留档；若本轮亦为定稿交付，**仍建议**简短附带 §7.9 类引导  
- **指出错误 / 与事实或参数不符**：`Read` → `versioned_output.md` → `iteration_context.md` → `correction_handler.md`；纠正结果按用户选择写入下一个版本目录，并**另存为**带时间戳的 `.md` 或 `.docx`；**追加**对话记录并更新 `版本索引.md`；完成后**必须**输出「纠正摘要」留档；定稿交付时**还须**按 **`disclosure_builder.md` §7.9** 附「权利要求偏向点」引导（见 **`correction_handler.md`** 末尾）  

主流程 Step 7→8 的 **`disclosure_self_check.md`** 仍在新稿定稿路径上内部执行。

---

## Agent 自用工作流检查清单

```
□ 已按步骤 Read 对应 prompts；Step 2 若目录含 Office，已执行 docx_to_md / pptx_to_md 并读了产出 `.md`
□ Step 3–4 已先输出专利点资产清单：含轻量相似专利初筛结果、可申请、暂不适合申请、建议商业秘密保护、评分、理由与建议动作；已获得用户确认要写的点（除非用户明确跳过清单）
□ 交付前已 Read `versioned_output.md`；用户产出根目录已按 `vN-说明-时间戳/` 保存当前版本，根目录无新增平铺定稿文件，已创建或更新 **`版本索引.md`**
□ 识别到「在已有交底书上修改」类意图时，已 Read `versioned_output.md`、`iteration_context.md` 并选用 merger 或 correction_handler（而非从头跑扫描）；交付为下一版本目录内的**新** `{案件名}_{时间戳}.md` 或 `.docx`，未无故覆盖旧稿
□ 执行 merger / correction_handler 后，已在对话中输出该文件要求的留档摘要（合并摘要 / 纠正摘要）；案件根目录已追加 **`交底书修订对话记录.md`**（或等价日志）并更新 **`版本索引.md`**
□ 查新完成且写入「背景技术」的现有技术与区别论述（符合 `prior_art_search.md`：**优先** `tools/cnipa_epub_search.py`，**国知局侧已分多次调用、每轮一词，并已自行合并** `EPUB_HITS_JSON`；**`abstract` 必用且已充分理解后再概括**；异常或无果再 **WebSearch**）
□ 除用户明确跳过外，完成摘要预览
□ 已确认发明人/发明者并写入标题下元信息；未知时未编造，已询问或标为 `[待填写]`
□ 已让用户选择交付格式（Markdown / Word）；若选 Word，已让用户选择图示方式（PNG / 生图提示词 / 自动生图）并确认是否导出 PDF；若选自动生图，已先检查 `OPENAI_BASE_URL` 与 `OPENAI_API_KEY`，缺失时已暂停并给出设置命令；正文为说明书式技术文本，含技术领域、背景技术、发明内容、附图说明、具体实施方式、摘要；发明内容不空泛，具体实施方式写清技术思路、端到端数据流、关键字段/参数/规则、伪代码或处理表、输入输出样例、异常分支；**正文无**注意事项、联系人、委托确认、自检清单、技能/示例仓库类脚注
□ 若一次交付 2 件及以上相关专利，已生成专利簇通俗说明清单：说明整体目的、每件侧重点、方法方案/系统方案区别、交叉边界、阅读建议；该清单另存当前版本目录下的带时间戳 `.md`
□ 定稿类对话已含 **`disclosure_builder.md` §7.9**「权利要求偏向点」建议交互（**不入正文**、**不捏造**未在稿内出现的保护取向）；迭代再走 merger 时见 **`iteration_context.md`** 表格补充行
□ 自检在后台完成，正文无自检清单章节；含公式时已按 **`disclosure_self_check.md` §8.2** 复核**公式正确性与公式逻辑**（有误已在 Step 8 直接改稿）
```

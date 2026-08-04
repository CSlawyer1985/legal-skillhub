# 无效检索分析报告（HTML）生成规范

> 配套脚本：`scripts/make_report_html.py`
> 配套数据：`report_data.json`（本文件即其字段契约）
> 触发位置：技能工作流 **M11 交付**环节（必产出）

---

## 一、目的

每次无效检索 / 分析都必须产出一份**结构固定、图文并茂**的 HTML 报告，
让用户能够**跨轮次、跨案例对照查看**完整的执行过程：

> 检索 → 对比文件筛选 → G7 特征比对 → 无效理由策略 → 附图比对（被无效专利 vs 对比文件）

报告采用**固定 7 章结构**，无论输入数据多寡，章节标题、锚点(id)、目录顺序**永远不变**；
缺失数据以占位符（`（待补充）`）渲染，从而**保证每次生成相同结构的文件**。

---

## 二、用法

```bash
# 数据驱动生成（--data 为必填，--out 缺省自动生成 invalidation_report_<目标专利号>.html）
python scripts/make_report_html.py \
    --data report_data.json \
    --out  invalidation_report_CN202310824943.5.html
```

- `--data`：报告数据源（JSON，字段见下文）。
- `--out`：输出 HTML 路径；缺省时与 `--data` 同目录，文件名 `invalidation_report_<meta.target_patent_no>.html`。
- 脚本自带自检：生成后校验 7 章锚点（`id="sec1"` … `id="sec7"`）是否齐全。

---

## 三、report_data.json 字段契约

顶层结构（全部为可选，缺失即渲染占位符）：

| 顶层键 | 对应章节 | 说明 |
|--------|----------|------|
| `meta` | 封面 + 一、 | 目标专利著录项与报告元信息 |
| `claims_summary` | 一、 | 权利要求书摘要 |
| `search` | 二、 | 检索过程（布尔/补充/语义/预期重复/时间线） |
| `prior_art` | 三、 | 对比文件候选列表 + 逐篇详析 |
| `feature_compare` | 四、 | G7 特征比对表 + 三步法 |
| `strategy` | 五、 | 无效理由策略（主攻/辅助/总览） |
| `figure_compare` | 六、 | 附图并排比对 + 总表 |
| `execution_log` | 七、 | 执行环境 / 操作记录 / 输出文件 / 待办 |

### 3.1 meta（封面与一、目标专利信息）
| 字段 | 说明 |
|------|------|
| `target_patent_no` | 目标专利号（如 CN202310824943.5） |
| `publication_no` | 公开/授权号 |
| `title` | 专利名称 |
| `applicant` / `inventors` | 申请人 / 发明人 |
| `application_date` / `publication_date` / `grant_date` | 申请日（建议标注"时间死线"）/ 公开日 / 授权日 |
| `ipc_main` / `ipc` | IPC 主分类 / 全部分类 |
| `patent_type` / `status` | 专利类型 / 法律状态 |
| `report_date` | 报告日期 |
| `skill_version` / `generated_at` | 页脚版本与生成时间（可选） |

### 3.2 claims_summary
- `claim_count`：权利要求项数
- `independent_claim`：独立权利要求1 文本（`\n` 换行，渲染为 `<br>`）
- `dependent_claims`：从属权利要求摘要（字符串或 `[{no,text}]` 列表）

### 3.3 search
- `tool` / `deadline` / `strategy`：检索工具 / 时间死线 / 检索策略
- `bool_search`：`{query, result_count, hits:[{rank,pubno,title,applicant,date}]}`
- `supplementary`：`[{query, count, key_hits:[...]}]`
- `semantic`：`{query, result_count, top_hits:[{rank,pubno,similarity,title,date,verdict}]}`
- `anticipation_dup`：`{anticipation, duplicate}`
- `timeline`：`["[T+0min] ...", ...]`

### 3.4 prior_art（数组）
每篇：`{code, pubno, title, applicant, pubdate, ipc, relevance, role, core_structure, correspondence, distinctions}`
- `relevance`：如 `"★★★★"`（脚本按星数自动着色，4★红/3★橙/2★蓝/1★灰）
- `relevance_class`：可显式覆盖颜色（tag-red/tag-orange/tag-blue/tag-gray）

### 3.5 feature_compare
- `against`：比对对象标识（如 `D1（CN205482046U）`）
- `rows`：`[{id, claim_feature, compare_feature, conclusion, remark}]`
  - `conclusion` 取值：`same` / `partial` / `diff`（对应绿/黄/红底色单元格）
- `summary`：G7 比对小结
- `three_step`：`[{step, content, conclusion}]`（三步法）

### 3.6 strategy
- `main`：`{title, legal_basis, target, combination, core_argument, strength, strength_pct, strength_color, note}`
  - `strength_pct`：0–100 整数（强度条宽度）；`strength_color`：orange/green/blue/gray 等
- `aux`：`[{title, target, reference, argument, strength, strength_pct, strength_color}]`（辅助理由）
- `overview`：`[{priority, reason, legal, scope, strength, advice}]`（策略总览表）

### 3.7 figure_compare（附图比对）
- `intro`：引言（支持 HTML）
- `groups`：`[{title, target_figs:[{src,alt,caption,source}], prior_figs:[{src,alt,caption,source}], conclusion}]`
  - `conclusion` 支持 HTML（如带 `<span class="tag ...">` 的结论标签）
  - **`source`（可选，附图来源溯源）**：每张附图必须如实标注其来源，`make_report_html.py` 会自动渲染来源徽标，确保报告诚实区分"权威官方附图"与"用户上传件"与"SVG 重构件"：
    - `"official"` → 绿色徽标「官方附图」（经 CNIPA / Google Patents / Espacenet 等官方通道取得的原始附图）
    - `"user_upload"` → 蓝色徽标「用户上传」（用户手动提供的该专利全文 / 附图，优先级高于自动获取与重构）
    - `"svg_reconstruction"` → 橙色徽标「SVG重构(非官方)」（因官方件不可得，从说明书文字重构的框图，非原始附图）
    - 字段缺省时不渲染徽标（向后兼容既有案例）；**任何经重构的附图必须显式标注 `svg_reconstruction`**，并在 `note` 中注明"正式提交前建议替换为官方附图"
- `summary_table`：`{columns:[...], rows:[[...]]}`（单元格支持 HTML）
- `note`：补充说明（渲染为 warning 框）；**SVG 重构件须在此声明来源限制**
- `target_extra_figs`：`{title, figs:[{src,alt,caption,source}]}`（被无效专利其余附图，避免与比对章节重复成章）

> **附图路径 / 内嵌约定**：`src` 可为两类值——① 相对 `--out` 输出目录的相对路径（如 `prior_art_figs/CN205482046U_fig1_correct.png`、`figs/target_hardware.svg`）；② **base64 data-URI**（`data:image/png;base64,...` 或 `data:image/svg+xml;base64,...`），用于将附图内嵌进 HTML 使其自包含、便于分享。
> 附图获取见技能 G6（CNIPA `cnipa_epub.py` / 国外 `foreign_patent_fetch.py` + PyMuPDF 提取）；**当任一通道仍无法取得全文 / 附图时，按 §3.3「附图/全文获取失败的「可选应对」」分支处理：优先询问用户手动上传，用户不上传再执行「SVG 重构 + data-URI 内嵌」降级**。M1 需保留这些路径供本章使用。

### 3.8 execution_log
- `env`：执行环境信息
- `records`：`["[14:27] ...", ...]`
- `output_files`：输出文件树
- `pending`：`["[重要] ...", ...]`（待完善事项）

---

## 四、7 章结构映射（恒定不变）

| 锚点 | 章节 | 数据来源 |
|------|------|----------|
| `sec1` | 一、目标专利信息 | `meta` + `claims_summary` |
| `sec2` | 二、检索过程记录 | `search` |
| `sec3` | 三、对比文件分析与筛选 | `prior_art` |
| `sec4` | 四、技术方案特征比对（G7） | `feature_compare` |
| `sec5` | 五、无效理由策略与论证 | `strategy` |
| `sec6` | 六、附图比对（被无效专利 vs 对比文件） | `figure_compare` |
| `sec7` | 七、执行过程日志 | `execution_log` |

---

## 五、一致性保证要点

1. **章节固定**：脚本硬编码 7 章标题 / 锚点 / 目录，数据不影响结构。
2. **缺失占位**：任何字段为空都渲染 `（待补充）`，绝不跳过章节。
3. **同一视觉规范**：CSS 内置固定，每次生成外观一致。
4. **图片相对路径**：`report_data.json` 与输出 HTML 置于同一工作目录，附图用相对路径引用，便于整体归档 / 打包。

---

## 六、最小可用示例

```json
{
  "meta": {"target_patent_no": "CNXXXX", "title": "示例专利"},
  "claims_summary": {"claim_count": 1, "independent_claim": "权1内容"},
  "search": {"tool": "PatSeek", "deadline": "2020-01-01", "strategy": "布尔+语义"},
  "prior_art": [],
  "feature_compare": {},
  "strategy": {},
  "figure_compare": {},
  "execution_log": {}
}
```

运行后仍会生成完整 7 章 HTML（缺失处以占位符呈现），结构与其他任何案例完全一致。

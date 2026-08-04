# ledger_to_revision.py 使用文档

> 配套 `合同智囊 v3.2.0` 的「修订落痕分流规则」。把审核问题台账 `review-issues-contract.json` 中 `status=confirmed` 的问题，确定性地落痕为 Word 修订模式文档（原生 `<w:ins>/<w:del>` Track Changes）。

---

## 1. 这个脚本解决什么

审核流程产出的是「四段式修改建议」（标注→简版→全版→理由），但**写进 Word 时到底哪些直接改、哪些只批注、哪些只进意见书**，原来没有统一机制。本脚本落地「修订落痕分流规则」：

- 以账本 `confirmed` 问题为**唯一数据源**，不重新推理，保证可复现；
- 一次性确定性应用所有改动（带修订收敛、不逐轮改），避免 AI 多轮修改互相覆盖；
- 输出 `render plan` + `执行日志`，可复核、可归档、出错可回放；
- 保留「AI 直接看真实 XML 做四段式判断」的精度优势（不做 contract-copilot 那种全量 plan-first）。

---

## 2. 何时调用

| 用户说了什么 | 动作 |
|---|---|
| 「生成修订稿」 | 调用本脚本（以账本 `confirmed` 问题为数据源） |
| 「原文件修订」 | 调用本脚本（`--doc` 传**原始** docx，在原文件上精确加修订标记） |
| 「定稿学习」 | 不属于本脚本范围，走定稿学习机制 |

> 优先级：步骤 5.5「确定性落痕（推荐）」> 纯手工四段式插入（不再默认）。

---

## 3. 命令与参数

```bash
python3 ledger_to_revision.py \
    --ledger .workbuddy/review-issues-contract.json \
    --doc 原始合同.docx \
    --out 原始合同_修订版_2026-07-13.docx \
    --policy balanced \
    --plan-out review-plan.json \
    --author "合同智囊·WorkBuddy"
```

| 参数 | 必填 | 说明 |
|---|---|---|
| `--ledger` | ✅ | 审核问题台账 `review-issues-contract.json` 路径 |
| `--doc` | ✅ | 原始合同 docx 路径（**不要**传已含修订建议的文档） |
| `--out` | ✅ | 输出修订稿 docx 路径，建议命名 `{原文件名}_修订版_{日期}.docx` |
| `--policy` | ❌ | `edit_policy` 三档，默认 `balanced`。可选 `revise-first` / `balanced` / `comment-first` |
| `--plan-out` | ❌ | 输出 render plan JSON 路径（可复核）。不传则不写 plan 文件 |
| `--author` | ❌ | 修订标记署名，默认 `合同智囊·WorkBuddy` |

> 依赖：`python-docx` + `lxml`（与本 Skill 其余脚本一致）。python-docx 在本环境已预装。

---

## 4. 账本字段契约（每个 issue 对象）

脚本只读取账本 `issues[]` 中 `status=confirmed` 的条目。需要的字段：

| 字段 | 取值 | 作用 |
|---|---|---|
| `id` | `ISSUE-001` | 追踪标识 |
| `status` | `confirmed` | **落痕门禁**，非 confirmed 一律跳过 |
| `risk_level` | `高` / `中` / `低` | 决定落痕通道与选用简版/全版；也是 `needs_negotiation` 的默认值来源 |
| `suggestion_type` | `modify` / `add` / `delete` | 映射为 `action`：`modify→replace`、`add→insert`、`delete→delete` |
| `needs_negotiation` | `true` / `false` | 是否「需谈判」（高风险 / 商业取舍 / 改变交易结构）。为 `true` 时走「仅批注」通道，**不触碰原文件**。缺省时按 `risk_level=="高"` 推断 |
| `original_text` | 原文片段 | `replace`/`delete` 的精确定位目标（必须能在某段落中精确命中） |
| `model_clause_simple` | 简版示范条款 | `replace` 用简版（低/中风险或 revise-first 之外） |
| `model_clause_full` | 全版示范条款 | `replace` 高风险用全版；`add`/`comment` 优先用全版 |
| `chapter` / `section` | 章节名 | `add` 类型用作插入锚点（在含该关键词的段落之后插入新段落） |

> ⚠️ `original_text` 必须与原文**逐字一致**才能定位成功；若原文未命中，该条会报告「原文未定位，未落痕」并跳过，不会静默改错。

---

## 5. 三通道与 edit_policy 行为矩阵

| edit_policy | 低/中风险 confirmed | 高风险 confirmed 且非需谈判 | 高风险/中风险 需谈判 (`needs_negotiation=true`) |
|---|---|---|---|
| `revise-first` | 直接修订（简/全版视风险） | 直接修订（全版） | **仅批注**，不落痕 |
| `balanced`（默认） | 直接修订（简版） | 直接修订（全版） | **仅批注**，不落痕 |
| `comment-first` | **全部先批注**，不落痕 | **全部先批注** | **仅批注**，不落痕 |

- **直接修订（revise）**：原文件加 `<w:ins>/<w:del>`，Word 可直接接受/拒绝；
- **仅批注（comment）**：不写原文件，仅记入 render plan / 执行日志，由 AI 汇入审核报告或意见书；
- **仅进意见书（opinion）**：本脚本不处理，由「交付物 / 正式意见书」流程承载。

---

## 6. 输出产物

| 文件 | 内容 |
|---|---|
| `{out}` | 修订稿 docx（仅 confirmed 且非需谈判的条目落痕） |
| `{out}.exec.log.json` | 执行日志：每条 plan 的 `action` / `applied` / `note`，便于复核与回放 |
| `{plan-out}`（可选） | render plan JSON：每条问题的 `action` / `old` / `new` / `anchor`，可人工预审后再应用 |

控制台会打印：落痕条数、仅批注条数、未定位条目清单、日志路径。

---

## 7. 常见问题排查

| 现象 | 原因 | 处理 |
|---|---|---|
| `⚠️ 账本中无 status=confirmed 的问题` | 审核后未确认任何问题 | 先在账本把要落痕的问题置 `confirmed` |
| `原文未定位，未落痕` | `original_text` 与原文不一致 / 跨段落拆开 | 核对账本 `original_text` 是否为原文连续片段；`add` 类改用 `section` 作锚点 |
| 修订标记在 Word 不显示 | 用 WPS 旧版或缺失 `w:author` | 用 Microsoft Word 打开；脚本已写 `author`/`date`/`id` |
| 想先审 plan 再落痕 | — | 先跑 `--plan-out` 看 plan，确认无误再正式应用 |

---

## 8. 与 skill 其他脚本的关系

- **`track_changes_docx.py`**：本脚本的 `<w:ins>/<w:del>` 标记规范（author/date/id 属性）与其保持一致；
- **`contract_revision.py`**：它从纯文本**重建**新文档；本脚本在**原 docx 上做精确 in-place 替换**，保留原格式与已有修订标记；
- 定稿学习、比对、起草流程不依赖本脚本。

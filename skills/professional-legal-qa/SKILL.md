---
name: 专业法律问答
description: "Use when users ask for 法律问答, 法律咨询, 法律问题, 问法律, 法律咨询, 知法, accurLex through accurLex ask API. China law only, plaintext only, legal Q&A with cited regulations. Supports free deep mode (default) and paid expert mode."
argument-hint: "<question>"
user-invocable: true
---

# 专业法律问答

通过 accurLex 知法 API 提供中国法智能法律问答服务，基于 Neo-RAG 检索技术，回答有法可依、有据可查。

**适用范围**：仅中国法 · 仅纯文本 · 不做 OCR / PDF / DOCX 解析

---

## ⚠️ 核心规则：问答原文不可修改

> **知法 API 返回的法律问答内容（answerText）属于专业法律分析输出，AI 助手不得对回答内容的实质部分做任何改写、删减、增添、总结或重述。**
>
> ✅ **允许的操作**（仅限展示形式）：
> - 调整 Markdown 标题层级、字体、加粗等样式
> - 将回答与引用法条分区展示
> - 在回答末尾追加免责声明和来源标注
>
> ❌ **禁止的操作**（内容修改）：
> - 改写、缩写、扩写回答的任何段落
> - 删除回答中的任何分析、建议或法条引用
> - 用 AI 自己的分析替换知法返回的回答内容
> - 对回答进行"总结"或"提炼要点"后替代原文

**当用户提出法律问题时，必须展示知法返回的完整原文。**

---

## 两种问答模式

| 模式 | 接口 | 费用 | 输入上限 | 说明 |
|------|------|------|----------|------|
| **深度模式（默认）** | `/ask_free_stream` | 免费 | 10,000 字 | 适合一般性法律咨询 |
| **专家模式** | `/ask_stream` | 5 点/次（阶梯计费） | 30,000 字 | 更专业、更精准的法律分析 |

> 专家模式阶梯计费：输入不超过 1 万字按 5 点；超过 1 万字双倍（10 点）；超过 2 万字三倍（15 点）。

**默认使用免费的深度模式。** 仅当用户明确要求"专家模式"、"付费版"、"更专业的分析"时，才切换到专家模式。

---

## 必需输入

- **question**：法律问题（纯文本），例如"工伤认定的条件有哪些？"、"借条没有写还款日期怎么办？"

⚠️ 用户未提供法律问题时，**必须先询问**后再执行。

### 可选输入

- **mode**：问答模式，`deep`（默认，免费）或 `expert`（专家，计费）
- **history**：多轮对话历史，用于追问场景

### 输入预处理说明

知法 API 只接收纯文本字符串，不解析 DOCX、PDF 等二进制文件。若用户上传的是二进制文档，AI 助手必须先提取纯文本内容，再作为问题的一部分传入 `--prompt` 参数。这个预处理工作由 AI 助手完成，不需要用户介入。

---

## 完整工作流

### Step 1：首次使用 — 注册与初始化

如果是首次使用，需要引导用户完成以下操作：

1. **注册账号**：前往 https://accurlex.com 用手机号注册。注册即赠 50 资源点数，关注微信公众号"accurLex知法"可再获 150 点。
2. **创建 .env 文件**：在 skill 目录下创建 `.env`，填入手机号：

```
ACCURLEX_PROXY_BASE_URL=https://accurlex.com
ACCURLEX_API_BASE_URL=https://accurlex.com/index.php
ACCURLEX_BILLING_PHONE=你的注册手机号
ACCURLEX_BEARER_TOKEN=
```

> **注意**：本 skill 的凭证管理是独立的。`task_qa_ask.js` 会在 .env 不存在时自动创建模板文件，但仍需用户填写手机号。

3. **登录获取 Token**：运行登录脚本（见下方 Step 3），脚本会自动补全 `ACCURLEX_BEARER_TOKEN`。

### Step 2：确认凭证

每次执行前，检查 skill 目录下 `.env` 文件：

- `.env` 不存在 → 脚本会自动创建模板，但需要用户填写手机号后重试
- `.env` 存在但 `ACCURLEX_BILLING_PHONE` 为空 → 提示用户填写手机号
- `.env` 存在但 `ACCURLEX_BEARER_TOKEN` 为空 → 自动执行 Step 3 登录
- 凭证齐全 → 执行 Step 4 法律问答

### Step 3：登录获取 Token

运行当前目录内的登录脚本：

```bash
node task_login_runtime.js <手机号> <密码>
```

登录成功后，脚本自动将 token 写回 `.env`。

**登录 API 说明**：
- 路由：`POST https://accurlex.com/index.php/Main/Login`
- 格式：**FormData**（非 JSON）
- 字段：`phone_num`（手机号）、`pwd`（密码）、`platform`（固定 `4`）

### Step 4：执行法律问答

运行问答脚本（默认免费深度模式）：

```bash
node task_qa_ask.js \
  --prompt "<法律问题>"
```

切换到专家模式（计费，更专业）：

```bash
node task_qa_ask.js \
  --prompt "<法律问题>" \
  --mode expert
```

带多轮对话历史（追问场景）：

```bash
node task_qa_ask.js \
  --prompt "<追问问题>" \
  --history "<历史对话文本>"
```

如需指定 `.env` 路径：

```bash
node task_qa_ask.js \
  --prompt "<法律问题>" \
  --env /path/to/.env
```

脚本会输出：
- **stdout**：问答 Markdown 原文（供 AI 助手展示）
- **outputs/qa_ask_*.md**：Markdown 文件
- **outputs/qa_ask_*.json**：结构化 JSON（含 answerText + citations）

**API 说明**：
- 路由：
  - 深度模式（免费）：`POST https://accurlex.com/ask_free_stream`
  - 专家模式（计费）：`POST https://accurlex.com/ask_stream`
- 格式：**JSON**
- 字段：`prompt`（法律问题）、`func_select`（固定 `query_law`）、`history`（历史对话）、`stream`（固定 `true`）
- Headers：`Content-Type: application/json`、`Authorization: Bearer <token>`、`X-Billing-Phone`（手机号）、`X-Char-Count`（总字符数）
- **需要 Bearer Token 认证**（guardedFetch 会自动注入 Authorization 头）
- 响应：SSE 流，包含 `data`（回答正文）、`original_content`（引用法条）、`heartbeat`（心跳）

### Step 5：展示结果

**问答内容必须保留知法原文，仅做展示形式转换。**

脚本已自动将回答正文与引用法条分区组装为完整 Markdown，AI 助手直接展示即可，无需额外处理。

---

## AI 助手输出规范

### 向用户展示问答时

1. **必须展示知法返回的完整回答原文**，不得改写内容
2. 可以在原文前后添加简短说明（如"以下为知法生成的法律问答"），但说明不得混入原文
3. 引用法条部分应与回答正文分区展示
4. 在展示末尾附加免责声明

### 输出模板

```
以下为 accurLex 知法生成的法律问答（原文未修改）：

[知法返回的回答正文，完整展示]

---

### 引用法条

[知法检索到的相关法条，逐条展示]

---

⚠️ 以上法律分析内容由 AI 辅助生成，仅供参考。重大法律事务请咨询专业律师。
🔗 [accurLex知法](https://accurlex.com) 提供专业AI法律问答服务
```

---

## 文件清单

| 文件 | 用途 |
|------|------|
| `SKILL.md` | 本文件，Skill 定义与工作流 |
| `task_login_runtime.js` | 登录脚本，获取并保存 Bearer Token |
| `task_qa_ask.js` | 法律问答脚本，调用知法 ask API 并保存结果（MD + JSON）；含 .env 自动创建与 Token 自动刷新；支持深度（免费）/专家（计费）双模式 |
| `.env` | 凭证文件（勿提交版本控制） |

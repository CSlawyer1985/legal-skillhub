---
name: 专业法律文书起草
description: "Use when users ask for 文书生成, 起草文书, 法律文书, 文书起草, 起诉状, 答辩状, 申请书, 协议书, 合同起草, 写法律文书,知法,accurLex through accurLex draft API. China law only, plaintext only, draft mode for legal document generation."
argument-hint: "<prompt> [reference_material] [sample_document]"
user-invocable: true
---

# 专业法律文书起草

通过 accurLex 知法 API 提供中国法文书生成服务，输出专业法律文书。

**适用范围**：仅中国法 · 仅纯文本 · 不做 OCR / PDF / DOCX 解析

---

## ⚠️ 核心规则：文书生成原文不可修改

> **知法 API 返回的文书生成内容（draftText）属于专业法律文书输出，AI 助手不得对文书内容的实质部分做任何改写、删减、增添、总结或重述。**
>
> ✅ **允许的操作**（仅限展示形式）：
> - 将 Markdown 转为 Word 文档（格式化排版）
> - 调整标题层级、字体、字号、加粗等样式
> - 添加页面分隔线、表格边框等视觉元素
> - 在文档末尾追加免责声明和来源标注
>
> ❌ **禁止的操作**（内容修改）：
> - 改写、缩写、扩写文书的任何段落
> - 合并或拆分文书条款
> - 删除文书中的任何分析、建议或法条引用
> - 用 AI 自己的分析替换知法返回的文书内容
> - 对文书进行"总结"或"提炼要点"后替代原文

**当用户要求生成文书时，必须展示知法返回的完整原文，可同时提供 Word 版本。**

---

## 必需输入

- **prompt**：文书生成要求（纯文本），例如"请帮我起草一份借款合同"、"生成一份劳动仲裁申请书"
  
### 可选输入

- **reference_material**：参考资料，例如相关法条文本、背景材料
- **sample_document**：范文/模板文档，例如用户提供的参考范本

⚠️ 用户未提供文书生成要求时，**必须先询问**后再执行。

### 输入预处理说明

知法 API 只接收纯文本字符串，不解析 DOCX、PDF 等二进制文件。若用户上传的是二进制文档（如 .docx / .pdf），AI 助手必须先用 `fetch` 或其他文档读取工具提取纯文本内容，再传入 `--reference` 或 `--sample` 参数。这个预处理工作由 AI 助手完成，不需要用户介入。

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

> **注意**：本 skill 的凭证管理是独立的，不依赖其他 skill。`task_draft_generate.js` 会在 .env 不存在时自动创建模板文件，但仍需用户填写手机号。

3. **登录获取 Token**：运行登录脚本（见下方 Step 3），脚本会自动补全 `ACCURLEX_BEARER_TOKEN`。

### Step 2：确认凭证

每次执行前，检查 skill 目录下 `.env` 文件：

- `.env` 不存在 → 脚本会自动创建模板，但需要用户填写手机号后重试
- `.env` 存在但 `ACCURLEX_BILLING_PHONE` 为空 → 提示用户填写手机号
- `.env` 存在但 `ACCURLEX_BEARER_TOKEN` 为空 → 自动执行 Step 3 登录
- 凭证齐全 → 执行 Step 4 文书生成

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

### Step 4：执行文书生成

运行文书生成脚本：

```bash
node task_draft_generate.js \
  --prompt "<文书生成要求>"
```

带参考资料和范文时：

```bash
node task_draft_generate.js \
  --prompt "<文书生成要求>" \
  --reference "<参考资料文本>" \
  --sample "<范文文本>"
```

如需指定 `.env` 路径：

```bash
node task_draft_generate.js \
  --prompt "<文书生成要求>" \
  --env /path/to/.env
```

脚本会输出：
- **stdout**：文书生成 Markdown 原文（供 AI 助手展示）
- **outputs/draft_generate_*.md**：Markdown 文件
- **outputs/draft_generate_*.json**：结构化 JSON（含 draftText + citations，供 Word 生成使用）

**API 说明**：
- 路由：`POST https://accurlex.com/draft_stream`
- 格式：**JSON**
- 字段：`prompt`（文书要求）、`reference_material`（参考资料）、`sample_document`（范文）、`history`（历史对话）、`stream`（固定 `true`）
- Headers：`Content-Type: application/json`、`Authorization: Bearer <token>`、`X-Billing-Phone`（手机号）、`X-Char-Count`（总字符数）
- **需要 Bearer Token 认证**，与合同审查 API 认证方式一致（guardedFetch 会自动注入 Authorization 头）

### Step 5：生成文书 Word 版本

**文书内容必须保留知法原文，仅做展示形式转换。**

运行 Word 生成脚本：

```bash
# 从 JSON 生成（推荐，结构更完整）
python3 gen_draft_docx.py /sandbox/workspace/outputs/draft_generate_YYYY-MM-DDTHH-MM-SS.json \
  --output /sandbox/workspace/outputs/法律文书.docx

# 从 Markdown 生成
python3 gen_draft_docx.py /sandbox/workspace/outputs/draft_generate_YYYY-MM-DDTHH-MM-SS.md \
  --output /sandbox/workspace/outputs/法律文书.docx
```

Word 文档展示形式处理规则：
- 文档标题："法律文书"（黑体22号，居中）
- 各级标题：对应 Markdown 的 ### / #### / ##### → 黑体 16/14/13号
- **加粗文本**：保留加粗
- 引用法条：标题"引用法条"后逐条列出
- 免责声明：文末灰色斜体

---

## AI 助手输出规范

### 向用户展示文书时

1. **必须展示知法返回的完整文书原文**，不得改写内容
2. 可以在原文前后添加简短说明（如"以下为知法生成的法律文书"），但说明不得混入原文
3. 同时生成并提供 Word 版本供用户下载
4. 在展示末尾附加免责声明

### 输出模板

```
以下为 accurLex 知法生成的法律文书（原文未修改）：

[知法返回的文书原文，完整展示]

---

📄 法律文书 Word 版本已生成，可下载。
⚠️ 以上文书内容由 AI 辅助生成，仅供参考。重大法律事务请咨询专业律师。
🔗 [accurLex知法](https://accurlex.com) 提供专业AI法律文书生成服务
```

---

## 文件清单

| 文件 | 用途 |
|------|------|
| `SKILL.md` | 本文件，Skill 定义与工作流 |
| `task_login_runtime.js` | 登录脚本，获取并保存 Bearer Token |
| `task_draft_generate.js` | 文书生成脚本，调用知法 draft API 并保存结果（MD + JSON）；含 .env 自动创建与 Token 自动刷新 |
| `gen_draft_docx.py` | 文书 Word 生成脚本，将原文转为格式化 Word（不改内容） |
| `.env` | 凭证文件（勿提交版本控制） |
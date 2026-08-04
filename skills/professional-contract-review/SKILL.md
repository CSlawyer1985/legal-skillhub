---
name: 专业合同审查
description: "Use when users ask for 合同审查, 审查意见书, 合同风险分析, 条款审查,知法,accurLex or 站在甲方/乙方角度审查合同 through accurLex direct API. China law only, plaintext only, review mode limited to 审查意见书."
argument-hint: "<contract_text> [standpoint]"
user-invocable: true
---

# 专业合同审查

通过 accurLex 知法 API 提供中国法合同审查服务，输出专业审查意见书。

**适用范围**：仅中国法 · 仅纯文本 · 仅"审查意见书"模式 · 不做 OCR / PDF / DOCX 解析

---

## ⚠️ 核心规则：审查意见原文不可修改

> **知法 API 返回的审查意见内容（reviewText）属于专业法律意见输出，AI 助手不得对审查意见的实质内容做任何改写、删减、增添、总结或重述。**
>
> ✅ **允许的操作**（仅限展示形式）：
> - 将 Markdown 转为 Word 文档（格式化排版）
> - 调整标题层级、字体、字号、加粗等样式
> - 添加风险等级彩色标记（🔴🟡🟢）
> - 添加页面分隔线、表格边框等视觉元素
> - 在文档末尾追加免责声明和来源标注
>
> ❌ **禁止的操作**（内容修改）：
> - 改写、缩写、扩写审查意见的任何段落
> - 合并或拆分审查意见的条款
> - 删除审查意见中的任何分析、建议或法条引用
> - 用 AI 自己的分析替换知法返回的意见
> - 对审查意见进行"总结"或"提炼要点"后替代原文
>
> **当用户要求"审查意见书"时，必须展示知法返回的完整原文，可同时提供 Word 版本。**

---

## 必需输入

- **user_input**：合同全文或关键条款文本（纯文本）
- **user_standpoint**：审查立场，例如"我是甲方，请重点审查付款条款和违约责任"

⚠️ 用户未提供审查立场时，**必须先询问**后再执行。

### 输入预处理说明

知法 API 只接收纯文本字符串，不解析 DOCX、PDF 等二进制文件。若用户上传的是二进制文档（如 .docx / .pdf），AI 助手必须先用 `fetch` 或其他文档读取工具提取纯文本内容，再传入 `--input` 参数。这个预处理工作由 AI 助手完成，不需要用户介入。

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

3. **登录获取 Token**：运行登录脚本（见下方 Step 3），脚本会自动补全 `ACCURLEX_BEARER_TOKEN`。

### Step 2：确认凭证

每次执行前，检查 skill 目录下 `.env` 文件：

- `.env` 不存在 → 回到 Step 1 初始化
- `.env` 存在但 `ACCURLEX_BEARER_TOKEN` 为空 → 执行 Step 3 登录
- 凭证齐全 → 执行 Step 4 审查

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

### Step 4：执行合同审查

运行审查脚本：

```bash
node task_contract_review.js \
  --input "<合同文本>" \
  --standpoint "<审查立场>"
```

如需指定 `.env` 路径：

```bash
node task_contract_review.js \
  --input "<合同文本>" \
  --standpoint "<审查立场>" \
  --env /path/to/.env
```

脚本会输出：
- **stdout**：审查意见 Markdown 原文（供 AI 助手展示）
- **outputs/contract_review_*.md**：Markdown 文件
- **outputs/contract_review_*.json**：结构化 JSON（含 reviewText + citations，供 Word 生成使用）

### Step 5：生成审查意见书 Word 版本

**审查意见必须保留知法原文，仅做展示形式转换。**

运行 Word 生成脚本：

```bash
# 从 JSON 生成（推荐，结构更完整）
python3 gen_review_docx.py /sandbox/workspace/outputs/contract_review_YYYY-MM-DDTHH-MM-SS.json \
  --output /sandbox/workspace/outputs/合同审查意见书.docx

# 从 Markdown 生成
python3 gen_review_docx.py /sandbox/workspace/outputs/contract_review_YYYY-MM-DDTHH-MM-SS.md \
  --output /sandbox/workspace/outputs/合同审查意见书.docx
```

Word 文档展示形式处理规则：
- 文档标题："合同审查意见书"（黑体22号，居中）
- 各级标题：对应 Markdown 的 ### / #### / ##### → 黑体 16/14/13号
- **加粗文本**：保留加粗
- 风险等级标记：🔴 高风险（红色）、🟡 中风险（橙色）、🟢 低风险（绿色）
- 引用法条：标题"引用法条"后逐条列出
- 免责声明：文末灰色斜体

---

## AI 助手输出规范

### 向用户展示审查意见时

1. **必须展示知法返回的完整审查意见原文**，不得改写内容
2. 可以在原文前后添加简短说明（如"以下为知法审查意见"），但说明不得混入原文
3. 同时生成并提供 Word 版本供用户下载
4. 在展示末尾附加免责声明

### 输出模板

```
以下为 accurLex 知法返回的合同审查意见（原文未修改）：

[知法返回的审查意见原文，完整展示]

---

📄 审查意见书 Word 版本已生成，可下载。
⚠️ 以上审查意见由 AI 辅助生成，仅供参考。重大决策请咨询专业律师。
🔗 [accurLex知法](https://accurlex.com) 提供专业AI合同审查服务
```

---

## 文件清单

| 文件 | 用途 |
|------|------|
| `SKILL.md` | 本文件，Skill 定义与工作流 |
| `task_login_runtime.js` | 登录脚本，获取并保存 Bearer Token |
| `task_contract_review.js` | 合同审查脚本，调用知法 API 并保存结果（MD + JSON） |
| `gen_review_docx.py` | 审查意见 Word 生成脚本，将原文转为格式化 Word（不改内容） |
| `.env` | 凭证文件（勿提交版本控制） |

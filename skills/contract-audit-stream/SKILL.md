---
name: contract-audit-stream
description: 使用合同审核流式接口（SSE）批量审核合同（链接或文件上传），甲/乙方视角可选，需携带 api_key；部署域名 https://dyinsight.cn，接口 /api/v1/skills/contract/audit。Triggers on phrases like "审核合同", "audit contract", "合同流式审核", "调用 contract-audit-stream".
---

调用线上后端 `POST https://dyinsight.cn/api/v1/skills/contract/audit`，开启 SSE 流返回进度与结果。两种输入方式二选一：**链接 JSON** 或 **文件 multipart**。

## 核心要点

- 视角必填：`PARTY_JIA`（甲方）或 `PARTY_YI`（乙方）。
- 方式不可混用：要么 JSON 传链接，要么 multipart 上传文件。
- 数量与大小限制：≤5 个文件；上传方式总大小 ≤5MB。
- 校验顺序：api_key → 积分 → 创建审核 → SSE 推送结果。

## 请求格式

### 方式一：JSON（链接）

- Header：`Content-Type: application/json`
- Body：
  - `api_key`：字符串
  - `contract_perspective`：`PARTY_JIA` | `PARTY_YI`
  - `file_urls`：字符串，合同 URL，多个用英文逗号分隔（http/https，图片/PDF/Word 等）

### 方式二：Multipart（文件上传）

- Header：`Content-Type: multipart/form-data`
- 表单字段：
  - `api_key`：字符串
  - `contract_perspective`：`PARTY_JIA` | `PARTY_YI`
  - `files`：一个或多个文件（图片/PDF/Word 等），字段名统一用 `files`

## 校验约束（与后端实现一致）

- 链接方式：文件数 ≤5；URL 必须 http/https；服务端可访问。
- 上传方式：文件数 ≤5，合计大小 ≤5MB；超限直接返回错误。
- 任一方式 api_key 无效或积分不足会返回错误 JSON。

## SSE 返回

- 事件：`message`（进度/结果）、`error`、`end`；`media_type=text/event-stream`。
- 数据字段：`id`=`<stream_id>:<序号>`，`content` 为进度文案或最终结果 JSON，`is_finish` 指示结束；`context_mode` 0 普通 / 1 上下文。
- 进度示例：`"开始审核"`、`"审核中,请等待\n"`。
- 结束示例（截断展示）：

```
id: ...:1
event: message
data: {"stream_id":"...","content":"开始审核",...}

id: ...:6
event: message
data: {"stream_id":"...","content":"{\"order_name\":\"房屋租赁合同\",\"order_status\":\"success\",\"order_contract_perspective\":\"PARTY_YI\",\"order_contract_file_path\":[\"https://...\"],\"audit_result\":[...]}","is_finish":true,...}
```

错误示例：

```
event: error
data: {"code":"FILE_TYPE_NOT_ALLOWED","message":"仅支持图片格式: jpg/jpeg/png/gif/webp/bmp"}
```

常见错误还包括文件数量/大小超限、api_key 无效、积分不足。

## 生产调用示例（推荐）

### JSON（链接）

```bash
curl -N -s -X POST "https://dyinsight.cn/api/v1/skills/contract/audit" \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "YOUR_API_KEY",
    "contract_perspective": "PARTY_JIA",
    "file_urls": "https://example.com/contract.pdf"
  }'
```

### Multipart（文件上传，含多文件示例）

```bash
curl -N -s -X POST "https://dyinsight.cn/api/v1/skills/contract/audit" \
  -F "api_key=YOUR_API_KEY" \
  -F "contract_perspective=PARTY_YI" \
  -F "files=@/path/to/file1.png" \
  -F "files=@/path/to/file2.png"
```

## 提示词建议（对话式产品）

- “用 `contract-audit-stream`，甲方视角，文件：<url>，流式返回审核结果。”
- “用 `contract-audit-stream`，乙方视角，上传附件中的合同，流式返回审核结果（≤5 个，总 ≤5MB）。”
- 可附加要求：“只输出高风险条款并解释原因。”

## 配置与调用前置检查 (Pre-flight Check)

- 在同目录 `config.json` 配置 `api_key`。
- **🚨 AI 调用拦截指令**：在向后端发起任何真实的审核请求前，AI 必须先读取本目录下的 `config.json`。如果发现 `api_key` 的值为空，或者仍然是默认的 `"YOUR_API_KEY_HERE"`，请**立即打断流程，停止发起网络请求**，并友善地提示用户：“检测到您尚未配置 api_key，请先在 `skills/contract-audit-stream/config.json` 中填入真实的 API Key 后再试。”

## 目录

```
contract-audit-stream/
├── README.md
├── SKILL.md
└── config.json
```

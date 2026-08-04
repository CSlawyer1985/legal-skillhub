# API 接口文档

基址：`https://www.cndeeptest.com/patent_draft/api`（无需鉴权）

## 上传交底 PDF

```
POST /files/upload-document
Content-Type: multipart/form-data
字段: file（仅 PDF）
```

**返回**（JSON）：

```json
{
  "code": "200",
  "message": "上传成功",
  "data": "<documentId>",
  "timestamp": 1700000000000
}
```

- `code == "200"` → `data` 即 `documentId`
- `code != "200"` → `FORMAT_ERROR` 等，按 `message` 告知用户并停止

## 生成专利文件

```
POST /patent/generate
Content-Type: application/json

{
  "chatId": "<任意唯一串>",
  "documentFileId": "<上一步的 documentId>"
}
```

**返回**：`text/event-stream`（SSE），无 `[DONE]` 标记，连接关闭即结束。

### SSE 事件表

| event | data 格式 | 处理方式 |
|-------|-----------|---------|
| `progress` | `{step, message}` | 实时展示 `message` + 百分比 |
| `message` | `{delta}` | 累加 `delta` 得到全文 |
| `error` | `{step, message}` | 展示 `message` 并终止 |
| `heartbeat` | `ping` | 忽略 |

### 响应格式示例

```
event: progress
data: {"step": "STEP_1", "message": "正在校验交底材料完整性..."}

event: message
data: {"delta": "【权利要求书】\n1. 一种..."}

event: error
data: {"step": "STEP_1_FAIL", "message": "交底材料不符合要求"}
```

# 合同履约追踪 — Contract Tracker Pro

> 上传合同 PDF → AI 自动提取付款节点/交期/到期日 → 履约台账 + 飞书提醒

**履约状态：** 🟡待执行 / 🟢已完成 / 🔴已逾期

---

## 功能概览

### 核心流程

1. **上传合同 PDF**（或粘贴文本）
2. **AI 自动提取**履约节点：付款节点、交期/交付节点、合同到期日
3. **建立履约台账**（本地 JSON 存储，支持 CSV 导出）
4. **飞书消息推送提醒**：节点前 3 天 / 当天 / 逾期每日推送

### 输入方式

| 方式 | 说明 |
|------|------|
| PDF 上传 | 合同全文自动解析，AI 提取节点 |
| 文本输入 | 粘贴关键条款，人工补全字段 |
| 历史记录 | 查询已有合同状态，标记完成 |

### 履约节点类型

- **💰 付款节点**：金额 + 日期
- **📦 交期/交付节点**：内容 + 日期
- **📅 合同到期日**：最终期限
- **✅ 验收节点**：验收时间（如有）
- **🛡 质保节点**：质保期截止（如有）

---

## 套餐体系

| 套餐 | 价格 | 功能 |
|------|------|------|
| **Free** | 免费 | 3 合同/月，PDF 解析，基础提醒 |
| **Standard** | ¥29/月 | 20 合同/月，文本+PDF，全功能提醒 |
| **Pro** | ¥99/月 | 100 合同/月，CSV 导出，逾期分析 |
| **Max** | ¥299/月 | 无限合同，高级报表，数据看板 |

---

## 配置说明

使用前请配置以下参数：

| 参数 | 说明 |
|------|------|
| `api_key` | 您的 Token（格式：`CONT-TRACK-*`） |
| `ai_api_key` | AI 模型 API Key（OpenAI 兼容） |
| `ai_base_url` | AI API 地址（可选，默认为 OpenAI） |
| `ai_model` | 模型名称（可选，默认为 `gpt-4o-mini`） |
| `feishu_webhook` | 飞书机器人 Webhook URL（可选） |

---

## 使用示例

### 添加合同（PDF）

```python
from scripts.main import add_contract_from_pdf

result = add_contract_from_pdf(
    pdf_path="/path/to/contract.pdf",
    api_key="CONT-TRACK-xxxxx",
    ai_api_key="sk-xxxxx",
    ai_base_url="https://api.openai.com/v1",
    ai_model="gpt-4o-mini",
)

if result["success"]:
    contract = result["contract"]
    print(f"合同已添加：{contract['name']}，共 {len(contract['nodes'])} 个节点")
```

### 检查提醒

```python
from scripts.main import check_and_notify

result = check_and_notify(
    api_key="CONT-TRACK-xxxxx",
    contract_id=None,  # None = 检查所有合同
)

for n in result["notifications"]:
    # 使用 feishu_im_user_message 发送
    # content = n["card_json"]
    print(n["card"]["header"]["title"]["content"])
```

### 标记节点完成

```python
from scripts.main import mark_node_done

result = mark_node_done(
    contract_id="abc12345",
    node_id="node-1",
)
```

### 导出合同台账

```python
from scripts.main import export_contracts

result = export_contracts(
    api_key="CONT-TRACK-xxxxx",
    format="csv",
)
print(result["data"])  # CSV 字符串
```

---

## 履约状态说明

| 状态 | 含义 | 触发条件 |
|------|------|---------|
| 🟡待执行 | 节点未到截止日期 | 截止日期在当前日期之后 |
| 🟢已完成 | 用户手动标记完成 | 用户调用 mark_node_done |
| 🔴已逾期 | 超过截止日期且未完成 | 当前日期 > 截止日期 |

---

## 提醒规则

| 场景 | 触发时机 |
|------|---------|
| 提前提醒 | 截止日期前 3 天推送飞书 |
| 当天提醒 | 截止日期当天推送飞书 |
| 逾期提醒 | 逾期后每天推送飞书，直到标记完成 |

---

## 数据存储

- **存储位置**：`contract_ledger.json`（与技能脚本同目录）
- **环境变量**：`CONTRACT_TRACKER_LEDGER` 可自定义路径
- **格式**：JSON，可在 Pro+ 版本导出为 CSV

---

## 依赖

```
pdfplumber>=0.10.0  # PDF 文本提取（推荐）
# 或
PyPDF2>=3.0.0       # PDF 文本提取（备选）
```

---

## 技术说明

- **Token 验证**：`POST https://api.yk-global.com/v1/verify`，网络错误时自动降级为 FREE tier，不阻断使用
- **缓存**：Token 验证结果缓存 5 分钟（TTL 300s）
- **AI 模型**：不绑定、不推荐，用户自行配置任意 OpenAI 兼容 API

---

## 常见问题

**Q: Token 验证失败怎么办？**
A: 网络错误时会自动降级为 FREE tier（3合同/月），不影响已添加的合同记录。

**Q: 如何增加合同数量上限？**
A: 升级到 Standard（¥29/月，20合同）或更高套餐，购买地址见下方。

**Q: 支持哪些 PDF？**
A: 支持标准 PDF 文本提取（扫描版 PDF 需要先 OCR 处理）。

---

> 如需购买收费版，请访问 [YK-Global.com](https://yk-global.com)

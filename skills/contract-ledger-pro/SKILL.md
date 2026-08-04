# SKILL.md - 合同台账管理（Contract Ledger）

> 上传合同 PDF → AI 自动提取字段建档 → 到期提醒 + 飞书推送

## 功能概述

### 核心能力
- **PDF 解析**：使用 PyMuPDF 提取合同文本
- **AI 字段提取**：自动识别合同名称、金额、日期、对方、关键节点
- **台账管理**：增删改查，支持按状态/金额/到期筛选
- **到期提醒**：可设置提前 N 天提醒
- **飞书推送**：到期提醒消息卡片推送给用户
- **数据导出**：支持 CSV/Excel/PDF（根据套餐）

## 套餐说明

| 套餐 | 月费 | 合同数 | 提醒数 | 导出 |
|------|------|--------|-------|------|
| FREE | 免费 | 5份 | 1个 | CSV |
| BSC | ¥29 | 50份 | 5个 | CSV |
| PRO | ¥99 | 300份 | 无限 | Excel/PDF |
| ENT | ¥299 | 无限 | 无限 | 全部 |

## 使用方法

### 1. 上传合同
```
openclaw run contract-ledger upload /path/to/contract.pdf --api-key CONTRACT-LGR-PRO-xxxxx
```

### 2. 查看台账
```
openclaw run contract-ledger list
openclaw run contract-ledger list --status 执行中 --sort amount
```

### 3. 查看合同详情
```
openclaw run contract-ledger get <contract_id>
```

### 4. 更新合同
```
openclaw run contract-ledger update <contract_id> --name "新名称" --status "已终止"
```

### 5. 删除合同
```
openclaw run contract-ledger delete <contract_id>
```

### 6. 设置提醒
```
openclaw run contract-ledger reminder <contract_id> add --days 7
openclaw run contract-ledger reminder <contract_id> list
openclaw run contract-ledger reminder <contract_id> remove --index 0
```

### 7. 检查到期合同
```
openclaw run contract-ledger check --days 30
openclaw run contract-ledger check --feishu
```

### 8. 导出数据
```
openclaw run contract-ledger export --format csv -o contracts.csv
openclaw run contract-ledger export --format xlsx -o contracts.xlsx --api-key CONTRACT-LGR-PRO-xxxxx
```

## Token 验证

- URL：`POST https://api.yk-global.com/v1/verify`
- 请求头：`Authorization: Bearer {api_key}`
- 响应字段：`**valid**`
- 前缀：`CONTRACT-LGR-*`
- 降级策略：网络错误 → FREE tier
- 缓存：本地 5 分钟

## 存储结构

```
contract-ledger/
├── data/
│   └── contracts.json   # 合同台账数据
├── scripts/
│   ├── main.py         # CLI 入口
│   ├── pdf_parser.py   # PDF 解析
│   ├── storage.py      # 数据存储
│   ├── token_validation.py  # Token 验证
│   └── feishu_notifier.py  # 飞书通知
├── .token_cache.json    # Token 缓存
└── SKILL.md
```

## 依赖

- PyMuPDF (fitz)
- requests
- Python 3.8+

> 如需购买收费版，请访问 [YK-Global.com](https://yk-global.com)

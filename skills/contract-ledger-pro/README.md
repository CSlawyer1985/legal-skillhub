# 合同台账管理系统（Contract Ledger）

上传合同 PDF → AI 自动提取字段建档 → 到期提醒 + 飞书推送

## 产品概述

合同台账管理系统帮助企业高效管理合同生命周期，从 PDF 上传、AI 智能提取字段、自动归档、到期提醒到飞书消息推送，一站式完成。

### 核心功能

- 📄 **PDF 解析**：使用 PyMuPDF 自动提取合同文本
- 🤖 **AI 字段提取**：智能识别合同名称、金额、日期、对方、关键节点
- 📋 **台账管理**：列表查看、筛选、增删改查
- ⏰ **到期提醒**：可设置提前 N 天提醒
- 📱 **飞书推送**：到期提醒消息卡片推送
- 💾 **轻量存储**：JSON 文件本地存储，无需数据库

## 套餐说明

| 套餐 | 月费 | 合同数 | 提醒数 | 导出 |
|------|------|--------|-------|------|
| **FREE** | 免费 | 5份 | 1个 | CSV |
| **BSC** | ¥29 | 50份 | 5个 | CSV |
| **PRO** | ¥99 | 300份 | 无限 | Excel/PDF |
| **ENT** | ¥299 | 无限 | 无限 | 全部 |

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 初始化

```bash
python scripts/main.py list
```

### 上传合同

```bash
python scripts/main.py upload /path/to/contract.pdf
# 或使用 API Key
python scripts/main.py upload /path/to/contract.pdf --api-key CONTRACT-LGR-PRO-xxxxx
```

### 查看台账

```bash
# 列出所有合同
python scripts/main.py list

# 按状态筛选
python scripts/main.py list --status 执行中

# 按到期排序
python scripts/main.py list --sort end_date
```

### 管理合同

```bash
# 查看详情
python scripts/main.py get <contract_id>

# 更新合同
python scripts/main.py update <contract_id> --name "新名称" --status "已终止"

# 删除合同
python scripts/main.py delete <contract_id>
```

### 提醒管理

```bash
# 添加提醒（到期前 7 天）
python scripts/main.py reminder <contract_id> add --days 7

# 查看提醒
python scripts/main.py reminder <contract_id> list

# 删除提醒
python scripts/main.py reminder <contract_id> remove --index 0
```

### 检查到期

```bash
# 检查未来 30 天到期合同
python scripts/main.py check --days 30

# 输出飞书消息卡片
python scripts/main.py check --feishu
```

### 导出数据

```bash
# 导出 CSV
python scripts/main.py export --format csv -o contracts.csv

# 导出 Excel（PRO 及以上）
python scripts/main.py export --format xlsx -o contracts.xlsx --api-key CONTRACT-LGR-PRO-xxxxx
```

## API Key

Token 验证地址：`POST https://api.yk-global.com/v1/verify`

- 前缀：`CONTRACT-LGR-*`（与合同审查共用 CONTRACT 体系）
- 网络错误自动降级为 FREE tier，不阻断使用

## 项目结构

```
contract-ledger/
├── scripts/
│   ├── main.py              # CLI 主入口
│   ├── pdf_parser.py         # PDF 解析模块
│   ├── storage.py            # JSON 存储模块
│   ├── token_validation.py   # Token 验证模块
│   └── feishu_notifier.py    # 飞书通知模块
├── data/                     # 数据目录
│   └── contracts.json         # 合同台账数据
├── SKILL.md                  # Skill 定义
├── README.md                 # 本文件
└── requirements.txt         # 依赖列表
```

## 技术栈

- Python 3.8+
- PyMuPDF（PDF 解析）
- requests（HTTP 请求）
- JSON（本地存储）

---

> 如需购买收费版，请访问 [YK-Global.com](https://yk-global.com)

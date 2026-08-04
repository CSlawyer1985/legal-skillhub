# patent-search · 专利检索

[![OpenClaw Skill](https://img.shields.io/badge/OpenClaw-Skill-blue.svg)](https://clawhub.ai)
[![ClawHub](https://img.shields.io/badge/ClawHub-Publish-orange.svg)](https://clawhub.ai)

[English](#english) · [中文](#中文)

---

## 中文

对接 **9235 专利检索 API**（`https://www.9235.net/api`），供 OpenClaw / Agent 做专利检索与分析。

### 主要能力

- 关键词 / 字段 / 布尔检索式搜索（支持 `scope`: cn、all、us、jp、kr、tw、wo、ep）
- 专利详情、权利要求、说明书、法律事务、引用与被引用、相似专利
- 企业专利画像（工商注册全称，如「华为技术有限公司」）
- 多维度统计、检索结果与统计 **Excel 导出**
- 软件/作品著作权、商标检索

### 配置

| 方式 | 说明 |
|------|------|
| 环境变量 | `export PATENT_API_TOKEN='你的token'` |
| OpenClaw | `openclaw config set skills.entries.patent-search.apiKey '你的token'` |
| 本地文件 | 复制 `config.example.json` → `config.json`（勿提交真实 token） |

申请 Token：<https://www.9235.net/api/open>

### 依赖

- Python 3.8+
- `pip install requests`

### CLI 示例

```bash
python3 main.py search 锂电池
python3 main.py detail CN112968234A
python3 main.py company 华为技术有限公司
python3 main.py analysis 人工智能 --dimension ipc --scope all
```

### 合规

见 [COMPLIANCE.md](COMPLIANCE.md)。发布包请勿包含 `config.json` 或真实密钥。

---

## English

Patent **search and analytics** via the [9235](https://www.9235.net) API for OpenClaw-compatible agents.

### Features

- Boolean / fielded search with data scopes: `cn`, `all`, `us`, `jp`, `kr`, `tw`, `wo`, `ep`
- Detail, claims, description, legal events, citations, similar patents
- Company patent portrait (full legal entity name)
- Analytics and **Excel export** for result sets and distributions
- Software/work copyright and trademark lookup

### Configuration

| Method | Notes |
|--------|--------|
| Env | `export PATENT_API_TOKEN='your-token'` |
| OpenClaw | `skills.entries.patent-search.apiKey` |
| Local file | Copy `config.example.json` → `config.json` (never commit secrets) |

Get a token: <https://www.9235.net/api/open>

### Requirements

- Python 3.8+
- `pip install requests`

### CLI examples

```bash
python3 main.py search "lithium battery"
python3 main.py detail CN112968234A
python3 main.py company "Huawei Technologies Co., Ltd."
```

See [COMPLIANCE.md](COMPLIANCE.md) for security disclosure.

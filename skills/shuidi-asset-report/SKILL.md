---
name: shuidi-asset-report
description: >
  生成企业财产线索分析报告，为诉讼执行、债务追偿等司法场景提供系统化企业资产排查。
  覆盖对外投资（全资/控股/参股）、知识产权（商标/专利/软著）、不动产（土地购置）、权利负担核查（股权出质/冻结/动产抵押/土地抵押/知产出质/司法拍卖）五大模块。
  适用场景：民事执行财产调查、债务追偿资产摸排、破产清算财产尽调、交易对手资产核实。
  当用户请求财产线索、资产排查、执行调查或债务追偿分析时使用此技能。
version: 1.0.0
author: Hermes Agent
license: MIT
compatibility: "Requires Python 3.8+, WeasyPrint, Source Han Sans SC font (~/.fonts/)"
metadata:
  hermes:
    tags: [shuidi, asset, 财产线索, 执行, 企业分析, PDF]
---

# 企业财产线索分析报告生成

## 概述

基于水滴信用 MCP 平台，生成面向司法执行场景的企业财产线索分析报告。报告以 HTML→WeasyPrint→PDF 输出，采用 warm-tech 配色，资产按流动性与可处置性从高到低排序，为执行决策提供直接数据支撑。

## MCP 依赖与配置

### 前置检查

执行本技能前，须确认以下水滴信用 MCP 服务均已配置：

| MCP 服务 | 功能 | 财产线索报告关键工具 |
|----------|------|------------------|
| `shuidi_data` | 企业工商与股权投资 | `get_company_info`、`get_company_investment`、`search_land_purchase` |
| `shuidi_risk` | 司法风险与权利负担 | `search_land_mortgage`、`search_chattel_mortgage`、`search_equity_pledge`、`search_equity_frozen`、`search_ip_pledge`、`search_judicial_auction` |
| `shuidi_sti` | 知识产权数据 | `search_trademark`、`search_patent`、`search_software_copyright` |

**检查方法**：调用 `mcp_data_query_get_company_info` 确认返回 `status_code: 1`。若失败须提示用户配置 MCP。

### MCP 配置方法

```json
{
  "mcpServers": {
    "shuidi_data": {
      "url": "https://data.shuidi.cn/mcp?pname=${SHUIDI_MCP_PNAME}&pkey=${SHUIDI_MCP_PKEY}"
    },
    "shuidi_risk": {
      "url": "https://risk.data.shuidi.cn/mcp?pname=${SHUIDI_MCP_PNAME}&pkey=${SHUIDI_MCP_PKEY}"
    },
    "shuidi_qc": {
      "url": "https://qc.data.shuidi.cn/mcp?pname=${SHUIDI_MCP_PNAME}&pkey=${SHUIDI_MCP_PKEY}"
    },
    "shuidi_sti": {
      "url": "https://sti.data.shuidi.cn/mcp?pname=${SHUIDI_MCP_PNAME}&pkey=${SHUIDI_MCP_PKEY}"
    },
    "shuidi_bid": {
      "url": "https://bid.data.shuidi.cn/mcp/?pname=${SHUIDI_MCP_PNAME}&pkey=${SHUIDI_MCP_PKEY}"
    }
  }
}
```

**获取凭证**：访问 [水滴信用开放平台](https://openapi.shuidi.cn/index.html#/mcp) 申请 `SHUIDI_MCP_PNAME`（项目名称）和 `SHUIDI_MCP_PKEY`（项目密钥）。注入环境变量：

```bash
export SHUIDI_MCP_PNAME="your_project_name"
export SHUIDI_MCP_PKEY="your_project_key"
```

**配置路径**：`~/.hermes/profiles/<profile>/mcp.json` 或 `~/.hermes/config.yaml` 的 `mcp` 字段。

### 依赖缺失处理

财产线索报告对 MCP 依赖分级：
- **核心（缺一不可）**：`shuidi_data`、`shuidi_risk`——12 项关键调用中有 9 项来自这两个服务，缺失将导致股权投资清单和权利负担核查全面空白
- **重要（缺失可降级）**：`shuidi_sti`——缺失时知识产权模块标注「数据不可获取」，不影响股权和权利负担模块

## 适用场景

- 民事执行案件中的被执行人财产调查
- 债务追偿前的资产摸排与偿债能力评估
- 企业破产清算前的财产状况尽职调查
- 商业合作前的交易对手资产核实

## 报告结构

| 章节 | 内容 |
|------|------|
| 封面 | 英文标注 + 中英文标题 + 股票代码（如有）+ 分析目的 + 免责声明 |
| 第一章 | 核心财产线索总览 — 统计卡片 + 财产线索明细表（按可处置性排序） |
| 第二章 | 对外投资明细 — 全资子公司 / 控股及重要参股 / 其他参股，标注持股与状态 |
| 第三章 | 知识产权明细 — 注册商标 / 专利 / 软件著作权总量 + 代表性项目列举 |
| 第四章 | 权利负担核查 — 股权出质/冻结、知识产权出质、动产抵押、土地抵押、司法拍卖全覆盖 |
| 第五章 | 综合评估 — 高流动性资产查封优先级 / 中长期资产评估 / 风险提示 / 处置障碍 |
| 第六章 | 数据来源与方法说明 — 12 项 MCP 工具调用明细 |

## 12 项并行 MCP 调用

所有工具在一次批量请求中并行发起：

| 序号 | 工具 | 财产线索类别 |
|------|------|-------------|
| 1 | `mcp_data_query_get_company_info` | 基础信息 |
| 2 | `mcp_data_query_search_land_purchase` | 不动产 · 土地 |
| 3 | `mcp_data_risk_search_land_mortgage` | 权利负担 · 土地抵押 |
| 4 | `mcp_data_risk_search_chattel_mortgage` | 权利负担 · 动产抵押 |
| 5 | `mcp_data_risk_search_equity_pledge` | 权利负担 · 股权出质 |
| 6 | `mcp_data_risk_search_equity_frozen` | 权利负担 · 股权冻结 |
| 7 | `mcp_data_risk_search_ip_pledge` | 权利负担 · 知产出质 |
| 8 | `mcp_data_query_get_company_investment(page_index=0)` | 股权投资 |
| 9 | `mcp_sti_search_trademark(page_index=0)` | 知识产权 · 商标 |
| 10 | `mcp_sti_search_patent(page_index=0)` | 知识产权 · 专利 |
| 11 | `mcp_sti_search_software_copyright(page_index=0)` | 知识产权 · 软著 |
| 12 | `mcp_data_risk_search_judicial_auction` | 负面信号 · 司法拍卖 |

返回 `status_code: 2` 的项标注「无记录」，不省略该模块。

## 资产优先级排序

财产线索按可处置性从高到低排列：

| 优先级 | 资产类别 | 说明 |
|--------|---------|------|
| 1 | 上市公司股票 | 可直接通过证券账户冻结/拍卖（须从企业类型字段识别上市状态） |
| 2 | 银行存款 / 应收款项 | 需通过财报或银行查询获取，报告中标注「需外部查询」 |
| 3 | 全资子公司股权（100%） | 可直接处置的核心资产 |
| 4 | 控股及重要参股（>20%） | 须评估少数股东权益 |
| 5 | 其他参股（<20%） | 流动性较低，价值取决于标的企业 |
| 6 | 知识产权（商标/专利/软著） | 须专业评估，变现周期长 |
| 7 | 不动产（土地/建筑） | 须排查权利负担后评估 |

## 权利负担交叉核查

| 负担类型 | 对处置的影响 |
|----------|-------------|
| 股权出质 / 冻结 | 股权不可自由转让，须清偿债权人后方可解除 |
| 知识产权出质 | 专利/商标已作为融资担保物，先行清偿 |
| 动产抵押 | 设备/库存已被抵押权人主张优先受偿 |
| 土地抵押 | 不动产存在他项权利，处置前须解押 |
| 司法拍卖 | 资产已进入执行程序——对申请人可能为负面信号（资产正在被其他债权人处置） |

## PDF 输出规范

| 要素 | 规范 |
|------|------|
| 字体 | `font-family: "Source Han Sans SC"` + WeasyPrint `FontConfiguration()` |
| CSS 首行 | `* { box-sizing: border-box; }` |
| 页面宽度 | `.page { width: 180mm }` = `210mm - 2×15mm(@page margin)` |
| 封面 | `@page cover { margin: 0 }`，深蓝渐变底，免责声明放入 `.cover-info` 表格最后一行；`.cover { page-break-after: always }` |
| 统计卡片 | `display: grid; grid-template-columns: repeat(4, 1fr)` — 最多4列，超4个自动换行（禁止使用 `flex: 1`，6卡片会被挤成不可读窄条） |
| 目录 | `display: block` + `leader(".") target-counter(attr(href), page)` 实现虚线点引右对齐页码；`::after` 必须挂载在 `<a>` 上（不能挂在子 `<span>` 上，`attr(href)` 取不到值） |
| 页眉 | CSS `string-set: header` + `@top-center { content: string(header) }`，header-div 本身不显示可见文字（否则每页出现双重标题） |
| 分页 | 每章 `.page { page-break-before: always }` |
| 体积 | 正常 400-550KB |

> **HTML/CSS 陷阱全集** 见 `shuidi-dd-report` 技能的 `references/html-pdf-report-pattern.md`，包含全部已验证的 CSS 陷阱与处置方案。资产报告和尽调报告共用同一套 HTML→PDF 基础设施。

## 关键陷阱

| # | 陷阱 | 处置 |
|---|------|------|
| 1 | 上市公司股票信息未直接体现在 MCP 中 | 从企业类型字段判断（「其他股份有限公司(上市)」） |
| 2 | 银行存款/应收数据缺失 | 标注「需通过财报或银行查询获取」，不编造 |
| 3 | 查询返回空 → 省略模块 | 须标注「无记录」，不省略 |
| 4 | 封面声明文字溢出 | 免责声明放入 `.cover-info` 表格最后一行 |
| 5 | AI 解读用 emoji | 纯文本【】标记 |
| 6 | `execute_code` 中多行 f-string 语法错误 | 资产报告 HTML 通常较小（~25KB），`execute_code` + `''.join(parts)` 可以工作。若报 SyntaxError `unterminated string literal`，改用 `write_file` 写 HTML 文件，然后用 `terminal` 调 WeasyPrint 转换 |

## 验证清单

- [ ] 12 项 MCP 工具已并行调用
- [ ] 核心财产线索表按可处置性排序正确
- [ ] 对外投资按持股分组（100%/控股/参股）
- [ ] 知识产权含总量统计及代表性项目
- [ ] 权利负担 6 类核查全覆盖
- [ ] 封面含英文标注、股票代码、免责声明
- [ ] PDF 400-550KB，中文正常
- [ ] HTML 用 `''.join(parts)` 组装，零花括号泄漏

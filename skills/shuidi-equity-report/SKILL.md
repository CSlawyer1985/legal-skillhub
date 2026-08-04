---
name: shuidi-equity-report
description: >
  生成企业股权结构与关联企业深度分析报告（HTML→SVG+PNG→PDF）。
  涵盖实控人穿透、股权架构四层可视化、控制力六档分档评估、关联企业全景梳理及关键风险揭示五大模块。
  适用场景包括：港股/内地上市公司实控人核查、非上市企业股权架构梳理、BVI/信托多层穿透。
  当用户请求分析企业股权、绘制架构图、穿透实际控制人或生成股权报告时使用此技能。
version: 1.0.0
author: Hermes Agent
license: MIT
compatibility: "Requires Python 3.8+, WeasyPrint, Source Han Sans SC font (~/.fonts/), rsvg-convert, xml.etree.ElementTree for SVG validation"
metadata:
  hermes:
    tags: [shuidi, equity, 企业分析, 股权穿透, 报告生成, SVG, PDF]
    related_skills: [shuidi-sti-report, shuidi-supply-chain-risk]
---

# 企业股权结构深度分析报告生成

## 概述

基于水滴信用 MCP 平台，生成含 SVG 股权架构图、控制力分档评估、关联企业全景清单的标准化 PDF 报告。采用 warm-tech 配色（`#F7F4ED` / `#D4A574` / `#2C3E50`）。报告结构见下文，CSS/分页/页面宽度规范见 `references/layout-fundamentals.md`。

## MCP 依赖与配置

### 前置检查

执行本技能前，须确认以下水滴信用 MCP 服务均已配置：

| MCP 服务 | 功能 | 股权报告关键工具 |
|----------|------|---------------|
| `shuidi_data` | 企业工商与股权数据 | `get_company_info`、`get_company_controller`、`get_company_beneficial_owner`、`get_company_partner`、`get_company_investment`、`pierce_equity` |
| `shuidi_listed` | 上市公司信息 | `get_quoted_company_info`（识别上市状态与股票代码） |

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

**获取凭证**：访问 [水滴信用开放平台](https://openapi.shuidi.cn/index.html#/mcp) 申请 `SHUIDI_MCP_PNAME` 和 `SHUIDI_MCP_PKEY`。注入环境变量：

```bash
export SHUIDI_MCP_PNAME="your_project_name"
export SHUIDI_MCP_PKEY="your_project_key"
```

**配置路径**：`~/.hermes/profiles/<profile>/mcp.json` 或 `~/.hermes/config.yaml` 的 `mcp` 字段。

### 依赖缺失处理

股权报告对 MCP 依赖精简——仅 `shuidi_data` 为核心必需（8 项关键调用均来自此服务）。`shuidi_listed` 在查询上市公司时使用，缺失时标注「上市信息不可获取」。其他服务（`shuidi_risk` / `shuidi_sti` / `shuidi_bid`）在本报告中不直接使用。

## 报告结构

| 章节 | 内容 | 关键输出 |
|------|------|---------|
| 封面 | 深蓝渐变底，中英文标题，股票代码，免责声明 | `@page cover` |
| 目录 | target-counter 自动页码，虚线点引 | `@page toc` |
| 第一章 | 执行摘要（150-200 字 + 指标速览卡片） | 8 卡网格 |
| 第二章 | 企业基本信息 + 控股平台穿透 + 实控人分析 + SVG 架构图 | SVG→PNG 嵌入 |
| 第三章 | 关联企业全景（投资概览 + 23 家企业分类清单） | `.name-col` |
| 第四章 | 控制力分档（6 档：全资/绝对/控股/实质/相对/参股 + CSS 柱状图） | 6 色分档 |
| 第五章 | 关键发现与风险提示（控制权稳定性/信托架构/代际传承/少数股东权益） | AI 解读 |

## 数据获取 — 8 项并行 MCP 调用

| 工具 | 返回数据 |
|------|---------|
| `mcp_data_query_get_company_info` | 工商登记信息 |
| `mcp_data_query_get_company_controller` | 实际控制人 |
| `mcp_data_query_get_company_beneficial_owner` | 受益所有人 + 控制路径 |
| `mcp_data_query_get_company_partner(page_index=0)` | 股东出资明细 |
| `mcp_data_query_get_company_investment(page_index=0)` | 对外投资清单 |
| `mcp_data_query_pierce_equity(direction=1)` | 向上股权穿透 |
| `mcp_data_query_pierce_equity(direction=0)` | 向下股权穿透 |
| `mcp_data_listed_get_quoted_company_info` | 上市公司信息（如有） |

以上 8 项在首轮一次性并行发起。返回 `status_code: 2` 的项标注「数据缺失」，不省略该模块。

## SVG 股权架构图规范

详见 `references/svg-diagram-spec.md`。核心规则：

- **四层递进布局**：自然人实控人 + 法人平台 → 上市公司主体 → 中间控股平台 → 目标公司 → 三列子公司（全资/控股/参股）
- **合并规则**：上游股东 >5 个时第 6 名起合并为「其他股东（合并），合计约 X%」虚线框；下游参股企业 >4 个时持股 <20% 的合并
- **节点配色**：自然人 `#D4A574→#c09060` 圆角 rx=25；法人平台 `#87A878→#6d9168` rx=8；上市公司 `#2C3E50→#1a2a38` rx=10 加阴影；目标公司 `#D4A574→#b08050` rx=8 加★前缀
- **线型**：直接持股用虚线（`stroke-dasharray="6,3"`），间接控股用实线，线上标注持股百分比
- **viewBox**：`"0 0 1000 800"`，背景渐变 `#f8f6f1→#efebe0`
- **全局字体**：`font-family="Source Han Sans SC, sans-serif"`（非等宽；SVG text 在 WeasyPrint 中无法渲染中文 → 须 rsvg-convert 转 PNG 后 `<img>` 嵌入）
- **SVG 转 PNG**：`rsvg-convert --width=1200 架构图.svg -o 架构图_hd.png`
- **HTML 嵌入**：`<img src="<os.path.abspath(png)>" style="..."/>`（WeasyPrint 须绝对路径）

## 数据内联 + HTML 组装原则

所有 MCP 查询结果直接内联写入 Python 脚本数据字典区，同一脚本完成数据提取 + SVG 生成 + PNG 转换 + HTML 组装 + PDF 渲染。HTML 组装全程使用 `''.join(parts)` 而非 f-string，零花括号变量泄漏风险。

## PDF 输出规范

| 要素 | 规范 |
|------|------|
| 字体 | CSS `font-family: "Source Han Sans SC"` + WeasyPrint `FontConfiguration()` |
| 页面宽度 | `.page { width: 180mm }` = `210mm - 2×15mm(@page margin)` |
| 盒模型 | CSS 首行 `* { box-sizing: border-box; }` |
| 分页 | 每章 `.page { page-break-before: always }`；封面 `.cover { page-break-after: always }`；表格/AI 框 `page-break-inside: avoid` |
| 封面定位 | `.cover { height: 297mm; overflow: hidden }` + `.cover-footer { margin-top: auto }` |
| 体积 | 正常 600-750KB（含嵌入字体 + 170KB PNG 架构图） |

禁止：`@font-face` + `file:///` URL（WeasyPrint 不可靠解析）、SVG `<text>` 直接嵌入 PDF（中文方框）

## 关键陷阱与处置

| # | 陷阱 | 处置 |
|---|------|------|
| 1 | `.page` width 与 `@page` 内容区不匹配 → 溢出/留白 | `.page width = 210mm - 2×@page-margin` |
| 2 | 未设 `box-sizing: border-box` → 内容右溢 | CSS 首行声明 |
| 3 | SVG text 直接嵌入 → 中文方框 | rsvg-convert 转 PNG 后 `<img>` 嵌入 |
| 4 | SVG `&` 未转义 → XML 解析错误 | `svg_escape()` 转 `&amp;` |
| 5 | `os.path.expanduser("~")` 重复拼接 | 硬编码 workspace 绝对路径 |
| 6 | WeasyPrint img src 用相对路径 | `os.path.abspath()` |
| 7 | f-string 花括号未转义 → 变量泄漏 | `''.join(parts)` 拼装 HTML |
| 8 | 表格名称列截断 | `.name-col { white-space: nowrap }` |
| 9 | AI 解读缺失数据来源声明 | 每个章节末尾含【AI 深度解读】段落，标注数据获取方式 |
| 10 | AI 解读用 emoji | 纯文本【】标记 |

详细诊断与修复方案见 `references/pitfalls.md`。

## 验证清单

- [ ] 8 项 MCP 工具已并行调用
- [ ] SVG 通过 `ElementTree.parse()` 验证，`&` 已转义
- [ ] PNG 转换成功，`<img>` 以绝对路径嵌入 HTML
- [ ] `validate_html()` 零花括号变量残留 + `<img>` 标签存在
- [ ] 封面声明位于封面底部（`margin-top: auto`）
- [ ] 所有章节末尾含 AI 深度解读，无 emoji
- [ ] PDF 600-750KB，中文正常渲染
- [ ] 控制力分档表颜色正确（6 档 6 色）
- [ ] 目录自动页码正常（WeasyPrint `target-counter`）

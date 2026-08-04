---
name: wipo-patent-weekly
description: |
  WIPO 小分子药物专利周报。每周定期检索 WIPO PatentScope 上新发布的小分子药物相关专利，生成 HTML 报告并上传 Google Drive。
  当用户提到「专利周报」「WIPO专利」「专利检索」「小分子专利」时触发。
  也用于 cron 定时任务：每周四 16:30 自动执行。
version: "1.0.0"
tags:
  - WIPO
  - 专利
  - 小分子药物
  - 周报
  - 定时任务
---

# WIPO 小分子药物专利周报

## 执行流程

```
Step 1: 计算日期范围（上周三到上周四）
Step 2: 运行 wipo_search.py 抓取专利数据 → JSON
Step 3: 运行 wipo_generate_report.py 生成 HTML 报告
Step 4: 上传到 Google Drive
Step 5: 输出摘要信息
```

## Step 1: 日期范围

- 默认日期范围：**上周三到上周四**（即运行日的前一周三至周四）
- 如果手动指定日期，使用指定日期
- 日期格式：DD.MM.YYYY（WIPO PatentScope 要求格式）

运行脚本自动计算日期：
```bash
python3 scripts/wipo_search.py <start_date> <end_date>
```

或手动计算：
```bash
python3 -c "
from datetime import datetime, timedelta
today = datetime.now()
# 上周四
last_thu = today - timedelta(days=(today.weekday() - 3) % 7 + 7) if today.weekday() >= 3 else today - timedelta(days=today.weekday() + 4)
last_wed = last_thu - timedelta(days=1)
print(f'{last_wed.strftime(\"%d.%m.%Y\")} {last_thu.strftime(\"%d.%m.%Y\")}')
"
```

## Step 2: 抓取专利数据

```bash
cd ~/.openclaw/workspace
python3 scripts/wipo_search.py <start_date> <end_date>
```

**输出：** `wipo_reports/wipo_patent_weekly_<date>.json`

**技术说明：**
- 使用 Playwright + Chromium 无头浏览器渲染 WIPO PatentScope JS 页面
- 必须先访问主页 `search.jsf` 建立 session，再跳转结果页
- 翻页通过 JS DOM 操作 `a.lb-next` 点击实现
- 每页 10 条，最多翻 20 页（200 条）

**查询条件：**
- IPC 分类：C07D（杂环化合物）/ C07C（无环化合物）/ A61K31（含有机有效成分的医药配制品）
- 关键词：inhibitor/antagonist/agonist/degrader/PROTAC/small molecule/binder/ligand/modulator（标题+摘要）
- 中文关键词：抑制剂/拮抗剂/激动剂/降解剂/小分子/结合剂/配体（全文）
- 国家：WO / CN / US
- 日期范围：指定

## Step 3: 生成 HTML 报告

```bash
cd ~/.openclaw/workspace
python3 scripts/wipo_generate_report.py wipo_reports/wipo_patent_weekly_<date>.json
```

**输出：** `wipo_reports/wipo_patent_weekly_<date>.html`

**报告内容：**
- 本周概览（专利总数、WO/CN/US 分布、可识别靶点数）
- 热门靶点 TOP 20（柱状图）
- 申请人 TOP 15（柱状图）
- IPC 分类分布
- 专利明细表（可滚动，含靶点/模式标签）

**靶点提取规则：** 见 [references/target-rules.md](references/target-rules.md)

## Step 4: 上传 Google Drive

```bash
rclone copy wipo_reports/wipo_patent_weekly_<date>.html gdrive:OpenClaw/专利更新/ --timeout 60s
```

## Step 5: 输出摘要

格式：
```
🔬 WIPO 小分子药物专利周报 | <日期范围>
📊 专利总数: <N> | WO: <N> | CN: <N> | US: <N>
🎯 热门靶点: <top 5 targets>
🏢 申请人 TOP 3: <top 3 applicants>

报告已上传至 Google Drive: OpenClaw/专利更新/
```

## 注意事项

- WIPO PatentScope 是 JSF 框架，需要浏览器渲染，web_fetch 无法直接抓取
- 如果抓取失败（网络超时、WIPO 变更页面结构等），报告失败原因
- 不要同步到 GitHub
- 本地保留副本在 `wipo_reports/` 目录
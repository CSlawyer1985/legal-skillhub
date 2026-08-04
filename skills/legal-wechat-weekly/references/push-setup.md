# 定时推送配置指南

> 用途：用户要求「定时推送 / 每周自动发我 / 自动监测」时，按本指南配置。
> 默认节奏：每周一 08:00 生成周报并推送。用户可改频率与时间。

## 推送方式（三选一）

| 方式 | 用户体验 | 适用场景 | 状态 |
|------|---------|---------|------|
| **WorkBuddy HTML 推送**（推荐） | 自动化运行后，WorkBuddy 对话中直接展示 HTML 周报，点击预览即可查看 | 每天打开 WorkBuddy 的用户 | ✅ 可用 |
| 邮件推送 | 周报渲染为 HTML 邮件，发送到指定邮箱 | 邮件重度用户 / 需转发给团队 | 需配置 SMTP |
| 企业微信单聊 | 企业微信消息推送 | 企微活跃用户 | 需在企微管理后台授权「消息/通讯录」权限 |
| 桌面文件 | 周报存 `~/Desktop/legal-mp-daily/`，自己打开看 | 所有场景的降级兜底 | ✅ 始终可用 |

## 架构

```
WorkBuddy 自动化（每周一 08:00 触发）
  └─ 按 SKILL.md「周报生成工作流」执行：
       WebSearch 发现新文章 → 内容筛选 → 评分分层 → dedupe 去重
       → render 生成 MD → render_html 生成浅色 HTML
       → IMA 入库（⭐ + 📌）→ 推送（HTML 预览 / 邮件 / 桌面文件）
```

## 创建自动化

### 方式一：WorkBuddy HTML 推送（推荐）

用 automation_update（mode=create）：

| 字段 | 值 |
|------|-----|
| name | 律师公众号监测周报 |
| scheduleType | recurring |
| rrule | `FREQ=WEEKLY;BYDAY=MO;BYHOUR=8;BYMINUTE=0`（改时间改 BYHOUR/BYMINUTE；改每天用 `FREQ=DAILY;BYHOUR=8;BYMINUTE=0`） |
| cwds | 用户当前工作区路径 |
| prompt | 见下方「HTML 推送 prompt」模板 |

**HTML 推送 prompt 模板：**

```
运行「法律公众号周报」技能的每周监测周报流程（技能目录 ~/.workbuddy/skills/法律公众号周报/，解释器用 /Users/zouhao/.workbuddy/binaries/python/envs/default/bin/python）：

1. 读取 assets/accounts.json 中 active 账号清单；若不存在先跑 scripts/mpwatch.py init。执业方向用 scripts/mpwatch.py profile 读取，影响评分分层。
2. 逐账号用 WebSearch 搜索该公众号近 7 天的新文章（查询词例："山东高法" 公众号 新文章 近一周）。覆盖不到的账号记录为「未发现」，不要编造文章。
3. **内容筛选**：只收录与律师实务/法律适用直接相关的文章。
   ✅ 保留：典型案例/类案分析、裁判规则/裁判观点、新法新规/司法解释解读与适用、实务技能/办案方法论、行业数据/司法统计、法律风险提示/合规指南
   ❌ 剔除：领导调研/视察/讲话、党建活动/政治学习、法院内部行政动态（人事表彰运动会）、纯时政新闻（防汛救灾/会议通稿）、无实务参考价值的普法宣传稿
   每个账号搜到多篇文章时，挑选 3-5 条最有实务价值的纳入；全都不合格则该账号标「无适用文章」。
4. **评分分层**：对每篇入选文章打分（⭐=3分必须看 / 📌=2分值得看 / 📄=1分扫一眼），并写 1-2 句评分理由。执业方向匹配的文章自动升一档。评分标准：
   - ⭐ 必须看：最高法/最高检裁判规则、新司法解释、指导性案例、法律修订全文——直接影响办案
   - 📌 值得看：中院以上典型案例、实务技能文章、新法解读——有参考价值
   - 📄 扫一眼：行业动态、学术观点、一般性解读——背景了解
5. 把筛选后的候选写成 NDJSON（每行 {"account","title","url","date","summary","score","score_reason"}，account/title 必填，score 为 1-3）到临时文件。
6. 跑 scripts/mpwatch.py dedupe --input <临时文件>，stdout 即新增条目，写入 /tmp/legal-mp-new.jsonl。
7. 跑 scripts/mpwatch.py render --input /tmp/legal-mp-new.jsonl --out ~/Desktop/legal-mp-daily/周报_<今天日期>.md。
8. 新增为 0 时也要生成周报（注明「本期无新增」）。
9. HTML 周报：跑 scripts/render_html.py --input /tmp/legal-mp-new.jsonl --out <工作区>/公众号周报-<今天日期>.html --date <今天日期>。
10. IMA 入库：⭐ 和 📌 文章自动推送到 IMA 知识库（走 references/ima-integration.md 配置，未配置时跳过并说明「IMA 未配置，跳过入库」）。
11. 调用 present_files 展示该 HTML，用户打开 WorkBuddy 即可预览。
12. 最终回复：附各账号覆盖情况 + 评分分布统计（⭐/📌/📄 各几篇）+ IMA 入库条数。
```

### 方式二：邮件推送

prompt 第 11 步改为：

```
11. 邮件推送：将周报 HTML 通过 sendmail/msmtp 发送到 <用户邮箱>。
    主题格式：「[公众号周报] YYYY-MM-DD - ⭐N条 📌N条 📄N条」。
    若发送失败，降级为保存 HTML 到工作区 + 说明发送失败原因。
```

### 方式三：桌面文件（仅保存）

prompt 去掉推送步骤，仅执行到第 9 步（保存 HTML 到工作区即可）。

## 推送渠道说明

| 渠道 | 状态 | 说明 |
|------|------|------|
| WorkBuddy HTML | ✅ 开箱可用 | 自动化完成后 present_files HTML，用户在对话中预览 |
| 企业微信单聊 | 需授权 | 需先在企微管理后台授予「消息/通讯录」权限 |
| 飞书 | 需连接 | 需先在连接器页连接飞书 |
| 邮件 | 需配置 | 需 SMTP 服务（QQ邮箱/Gmail/企业邮箱） |

降级原则：任何推送失败都不阻断周报生成；失败原因写进最终回复。

## 调整节奏

- 改时间：`automation_update` mode=update，改 rrule 的 BYHOUR/BYMINUTE。
- 暂停/恢复：status 改 PAUSED / ACTIVE。
- 改监测频率：把 prompt 第 2 步「近 7 天」改成「近 1 天」（日报更精准）或「近 3 天」（隔日）。

## HTML 周报样式规范

生成的 HTML 周报应满足：
- 浅色背景（#f8f7f5），卡片式布局（#ffffff 底色卡片，#e8e4de 边框）
- 按评分分栏：⭐ 必须看（金色 #e8b86d）→ 📌 值得看（蓝色 #6ba3e8）→ 📄 扫一眼（灰色 #a0a0a0）
- 每篇文章含：来源标签、日期、评分标签、评分理由、标题、摘要
- 标题加粗可点击（有 url 的用 `<a>` 标签，无 url 的纯文本）
- 底部附执业方向覆盖情况表
- 移动端响应式（max-width 适配）

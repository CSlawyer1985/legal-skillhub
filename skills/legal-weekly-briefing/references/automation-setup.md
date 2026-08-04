# 自动化调度配置

> 法律周报需要外部调度层定时触发。推荐每周推送两次（周三 + 周五）。

---

## 方式 A：WorkBuddy Automation（推荐）

在 WorkBuddy 中创建自动化任务，每周三、周五上午 9:00 自动执行：

```
schedule: FREQ=WEEKLY;BYDAY=WE,FR;BYHOUR=9;BYMINUTE=0
prompt: 使用 legal-weekly-briefing skill 生成本周法律周报，拉取近一周公众号文章，评分排序后输出周报并入库 IMA。
```

> 自动化任务和日常对话共用同一模型额度池。若额度紧张，建议用方式 B 隔离执行环境。

---

## 方式 B：GitHub Actions cron

Fork 仓库后，添加 `.github/workflows/weekly-briefing.yml`：

```yaml
on:
  schedule:
    - cron: '0 1 * * 3'   # 每周三北京时间 9:00
    - cron: '0 1 * * 5'   # 每周五北京时间 9:00
```

隔离额度，运行日志可追溯。

---

## 方式 C：系统 cron / launchd

```bash
# macOS launchd: ~/Library/LaunchAgents/com.legal-weekly.plist
# 每周三、周五上午 9:00 运行 pipeline
```

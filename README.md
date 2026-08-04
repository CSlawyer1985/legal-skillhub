# Legal SkillHub · 法律 Skill 聚合站

2049 个法律 Agent Skill 的**目录、说明书、分类体系、验证中心和部署入口**。

网站（GitHub Pages）：`https://<owner>.github.io/<repo>/`

## 这个网站回答五个问题

1. 这个 Skill 到底能干什么
2. 它适用于什么法律和什么场景
3. 它是如何完成工作的
4. 它是否可信、安全并仍在维护
5. 如何把它安装到你的工作环境中

## 仓库结构

```
├── skills/          # 2049 个 Skill 本体（每个一个文件夹，含 SKILL.md 及附属文件）
├── index/           # 索引区（建站基础）
│   ├── taxonomy.md      # 标签体系权威定义 v0.1
│   ├── skills-index.json# 主索引（数据权威）
│   ├── files.json       # 每个 Skill 的文件清单
│   ├── master-index.md  # 人读版总索引
│   ├── stats.md         # 分布统计
│   └── build_index.py   # 打标管线（python3 index/build_index.py 可重跑）
└── docs/            # 网站（GitHub Pages source = /docs，纯静态无构建）
    ├── index.html       # 技能库首页（搜索 + 8 维筛选 + 卡片墙）
    ├── skill.html       # Skill 详情页（10 段信息架构 + 文件树浏览器 + 安装命令）
    ├── learn/           # 学习中心（七部分课程 + 精选案例解剖）
    └── about.html       # 授权说明与权利人下架通道
```

## 内容来源

| 来源 | 数量 | 授权 |
|------|------|------|
| 腾讯 SkillHub | 881 | 作者未声明授权（undeclared） |
| AgentSkills.Legal（CaseMark/skills） | 882 | Apache-2.0 |
| Awesome Legal Skills 中文库 | 224 | CC BY-NC-ND 4.0 |
| 元力法律 | 61 | 作者未声明授权（undeclared） |

**授权提示**："没有写许可证"不等于开源。未声明授权的 Skill 默认保留原作者所有权利，本站已署名并标注来源；商业使用前请自行评估或联系原作者。权利人可通过 Issue 提交下架请求，核实后 48 小时内处理。详见 `NOTICE.md` 与站点"关于"页。

## 免责声明

- 标签（法域、领域、任务等）由程序与 AI 辅助自动判定，未经逐一人工审核，可能存在误判，使用前请结合 Skill 原文核实
- Skill 内容由原作者提供，本站不对其法律内容的准确性、时效性负责；法律类 Skill 输出均需人工复核后方可用于正式用途
- 含脚本的 Skill 可能涉及文件读写、网络访问等权限，安装前请审阅其 scripts/ 目录

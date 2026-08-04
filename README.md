# ⚖️ Legal SkillHub · 法律 Skill 聚合站

<div align="center">

**2049 个法律 Agent Skill 的目录 · 说明书 · 分类体系 · 部署入口**

[![License](https://img.shields.io/badge/License-See%20individual%20skills-blue.svg)]()
[![Skills](https://img.shields.io/badge/Skills-2049-brightgreen.svg)](index/master-index.md)
[![Author](https://img.shields.io/badge/author-Dr.CS(CS)-orange.svg)](https://github.com/CSlawyer1985)
[![PRs](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/CSlawyer1985/legal-skillhub/pulls)

纯静态网站 · 零构建 · 全相对路径 · 可部署到任意静态托管

[项目简介](#-项目简介) • [核心价值](#-核心价值) • [项目数据](#-项目数据) • [核心特性](#-核心特性) • [快速开始](#-快速开始) • [仓库结构](#-仓库结构) • [标签体系](#-标签体系) • [学习中心](#-学习中心) • [免责声明](#-免责声明)

</div>

---

## 📖 项目简介

**Legal SkillHub** 是一个面向法律人的 Agent Skill 聚合与学习平台。它将 2049 个法律 AI Skill 从互联网公开数据中整理收录，为每一份 Skill 提供：

- **盘点说明**：它到底能干什么、适用于什么法律和场景
- **工作逻辑**：它是如何完成工作的（输入 → 处理步骤 → 产出）
- **法域与领域标注**：适用于哪一法域、哪一法律领域
- **可信度信息**：授权状态、验证状态、维护状态
- **一键部署**：下载、远程安装命令、环境依赖说明

平台的核心定位是**学习**：不仅是一个 Skill 下载站，更是法律人学习"如何设计与使用法律 Agent Skill"的教材库。

## 🎯 核心价值

💡 **目录** - 2049 个法律 Skill 全量收录，8 维标签体系（法域/领域/任务/角色/语言/授权/类型/自动化等级）多维筛选
🔍 **说明书** - 每个 Skill 独立详情页：一句话用途、工作逻辑、输入输出、适用/不适用场景、风险等级
📚 **学习中心** - 七讲完整课程《把专业经验封装成 Agent Skill》+ 精选案例解剖，教法律人自己写 Skill
🛠️ **部署入口** - 三种安装方式（curl 逐文件 / git sparse-checkout / AI 代装），含国内镜像切换
👁️ **文件浏览器** - 不下载也能在线浏览每个 Skill 的全部文件内容
⚖️ **法域自觉** - 覆盖中国/美国/欧盟/英国/法国/日本等 17 个法域，标签自动判定并标注置信度

## 📊 项目数据

- **🗂️ Skill 总数**：2049 个
- **🌏 法域覆盖**：中国大陆 801 / 美国 608 / 法域中立 405 / 欧盟 113 / 跨境国际 53 / 法国 26 等 17 个法域
- **📚 语言分布**：中文 1003 / 英文 1046
- **🏷️ 标签维度**：8 维主分类 + 9 维高级筛选（法域/领域/任务/角色/行业/输入/输出/授权/风险等）
- **📁 文件规模**：12,418 个文件，175MB（无单文件 >5MB，GitHub 友好）
- **🛠️ 技能形态**：指令型 1424 / 代码包型 206 / 知识包型 173 / 混合型 141 / 工具封装型 93
- **🎓 学习内容**：7 讲课程 + 案例解剖 + 部署指南

## ✨ 核心特性

### 技能库（首页）

参照终端风格设计的浏览体验：

- **顶部分类导航**：法域 / 领域 / 任务 / 角色 四个维度一键切换，分类 pill 单选过滤
- **高级筛选抽屉**：语言、授权、验证状态、技能类型、自动化等级、输入/输出类型、行业 9 维组合筛选
- **排序**：质量分 / 文件数 / A-Z / 含新法 / ★精选
- **搜索**：中英文模糊搜索（中文按二元组切分，无需分词库）
- **URL 同步**：筛选条件写入地址栏 hash，可分享筛选视图
- **底部分类目录**：按法域浏览全部 Skill 的文档式目录

### 详情页（10 段信息架构）

1. 概览（名称/一句话/主法域/主领域/主任务/验证徽章）
2. 它能完成什么（能力、场景、输入→输出）
3. 它如何工作（工作逻辑、步骤、自动化等级）
4. 法域与适用（适用法域、不适用提示）
5. **技能包文件浏览器**（左侧文件树 + 右侧内容区，Markdown 渲染/代码高亮）
6. 安装与部署（curl 命令 / git sparse-checkout / AI 代装，含 jsDelivr 镜像切换）
7. 风险与限制（风险等级、人工复核要求、数据处理方式）
8. 质量与验证（验证徽章明细）
9. 来源与许可（作者、许可证、下架通道）
10. 相关 Skill（同任务异法域 + 同法域同领域推荐）

### 学习中心（教学为核心）

《把专业经验封装成 Agent Skill》七讲：

| # | 主题 | 回答的问题 |
|---|------|-----------|
| 01 | Skill 的本质 | Prompt/规则/Skill/Agent/MCP/Plugin 有什么区别？ |
| 02 | 什么适合做 Skill | 哪些工作值得封装？七步蒸馏法 |
| 03 | 编写 SKILL.md | 描述就是路由器；任务自由度；渐进式披露 |
| 04 | 工作环境与配套条件 | 脚本/文档工具链/API key/MCP 各类依赖怎么配 |
| 05 | 什么是好的法律 Skill | 法域识别/时效/来源核验/人工复核九条硬要求 |
| 06 | 评测和迭代 | 测试集设计；有/无 Skill 基线对比 |
| 07 | 从 2049 个样本看法律 Skill | 语料宏观洞察；写作十条军规 |

另附**精选案例解剖**：对不同类型的优秀 Skill 逐个拆解结构、方法论与可借鉴点。

### 标签体系

遵循《Legal SkillHub 标签与元数据索引规范》v0.1（见 `index/taxonomy.md`）：三层元数据（前台筛选/前台详情/后台治理）、四类信息（分类标签/结构化字段/描述字段/关系字段）、三层发布标准（T1 基础收录 → T2 可公开展示 → T3 可信 Skill）。打标由 `index/build_index.py` 管线自动完成（程序化提取 + 信号词打分 + LLM 复核），可重复执行。

## 🚀 快速开始

### 在线浏览

- 技能库：访问站点首页，按法域/领域/任务筛选，或直接搜索
- 详情：点击任意 Skill 卡片，在线浏览文件内容，复制安装命令

### 安装一个 Skill 到本地

任意 Skill 详情页提供三种方式（以 `legal-kb` 为例）：

```bash
# 方式一：curl 逐文件下载（推荐）
mkdir -p ~/.claude/skills/legal-kb && cd ~/.claude/skills/legal-kb \
  && curl -fsSL -o "SKILL.md" "https://raw.githubusercontent.com/CSlawyer1985/legal-skillhub/main/skills/legal-kb/SKILL.md" \
  && curl -fsSL --create-dirs -o "scripts/list_files.py" "https://raw.githubusercontent.com/CSlawyer1985/legal-skillhub/main/skills/legal-kb/scripts/list_files.py"

# 方式二：git sparse-checkout（批量场景）
git clone --depth 1 --filter=blob:none --sparse https://github.com/CSlawyer1985/legal-skillhub.git
cd legal-skillhub && git sparse-checkout set skills/legal-kb && cp -r skills/legal-kb ~/.claude/skills/

# 方式三：让 AI 助手帮你安装
# 复制详情页的安装提示词给 AI 即可
```

> 💡 **国内网络**：raw.githubusercontent.com 访问不畅时，详情页可一键切换 jsDelivr 镜像（`cdn.jsdelivr.net/gh/...`）。

### 部署站点

本站为纯静态站点（`docs/` 目录），可部署到任何静态托管：

- **Cloudflare Pages**：连接本仓库 → 构建命令留空 → 构建输出目录填 `docs`
- **GitHub Pages**：Settings → Pages → Source: main /docs
- **本地预览**：`cd docs && python3 -m http.server 8000`

> 站点内部全部使用相对路径，子路径部署天然兼容；下载链接指向 `docs/data/site-config.json` 中配置的仓库地址，改仓库名只需改这一处。

## 📁 仓库结构

```
├── skills/              # 2049 个 Skill 本体（每个一个文件夹：SKILL.md + 附属文件）
├── index/               # 索引区（建站基础）
│   ├── taxonomy.md          # 标签体系权威定义 v0.1
│   ├── skills-index.json    # 主索引（数据权威，机器生成）
│   ├── files.json           # 每个 Skill 的文件清单
│   ├── master-index.md      # 人读版总索引
│   ├── stats.md             # 分布统计报告
│   └── build_index.py       # 打标管线（python3 index/build_index.py 可重跑）
├── docs/                # 网站（纯静态，零构建）
│   ├── index.html           # 技能库首页（搜索 + 筛选 + 卡片列表）
│   ├── skill.html           # 详情页（10 段信息架构 + 文件浏览器 + 安装命令）
│   ├── learn/               # 学习中心（七讲 + 案例解剖）
│   ├── about.html           # 授权说明与权利人下架通道
│   └── data/                # 站点数据（skills.json / files.json / site-config.json）
```

## 📦 技术栈

- **纯静态**：HTML + CSS + Vanilla JS，无框架、无构建步骤、无外部依赖
- **数据驱动**：`index/build_index.py` 三遍法打标管线（程序化 → 信号词 → LLM 复核），幂等可重跑
- **终端风格 UI**：深色主题 + 等宽字体 + 磷光绿强调色，卡片 `>` 前缀、状态徽标、#hashtag 语义

## ⚠️ 免责声明

- 本站标签（法域、领域、任务等）由程序与 AI 辅助自动判定，未经逐一人工审核，可能存在误判，使用前请结合 Skill 原文自行核实
- 本站收录的 Skill 内容为互联网公开数据的整理，版权归原作者所有；本站不对其法律内容的准确性、时效性负责
- 法律类 Skill 的输出均需人工复核后方可用于正式用途；含脚本的 Skill 可能涉及文件读写、网络访问等权限，安装前请审阅其 scripts/ 目录
- "没有写许可证"不等于开源。未声明授权的 Skill 默认保留原作者所有权利，商业使用前请自行评估或联系原作者

## 📬 权利人与贡献者

- **权利人下架**：若您是某项内容的权利人，认为本站收录侵犯您的合法权益，请通过 GitHub Issues 提交下架请求，核实后 48 小时内处理
- **贡献**：欢迎提交 PR 完善标签、修复文档、补充案例解剖

# 检答网集萃本地检索技能

## 项目简介

检答网是最高人民检察院为全国四级检察院检察干警提供法律政策运用、业务咨询、答疑服务的信息共享平台，内容涉及面广、专业性强、解答及时权威。通过最高人民检察院微信公众号和检察日报专栏刊发“检答网集萃”。

本项目将“检答网集萃”第 1–140 批 Markdown 数据整理为本地技能，用于在用户咨询法律和检察相关问题时，先检索内置全文，再基于检索结果整理答复。技能的重点是“检索可溯源内容”，而不是让 AI 凭通用知识直接回答。

本技能只内置了检答网集萃第 1–140 批数据（根据时间发布先后命名）。最高人民检察院后续发布的新批次，本技能会在后续持续更新。

## 重要声明

“检答网集萃”仅为 AI 智能体提供检答网专家的专业解答，不构成具体案件的法律意见。最终解释权属于最高人民检察院。实际案件中的具体法律问题建议用户咨询专业法律人士，由专业法律人士根据具体案情进行专业判断。

本技能由 hisnotright 整理制作。

数据来源：中华人民共和国最高人民检察院微信公众号 / 检察日报《检答网集萃》栏目。

## 授权方式

本项目采用 MIT License 开源，详见仓库根目录下的 `LICENSE` 文件。

MIT 授权范围包括本仓库中的技能配置、脚本、说明文档、索引文件以及随仓库整理发布的检答网集萃 Markdown 数据。使用、复制、修改、分发或再发布本项目时，应保留原始版权声明、MIT 许可文本、数据来源说明和本 README 中的免责声明。

## 环境要求

- Claude Code。
- Python 3。
- 不需要安装第三方 Python 依赖。
- 不需要额外 API Key。
- 不需要联网检索；回答基于本地内置 Markdown 数据。

## 适用场景

本技能适用于以下问题：

- 用户明确要求查询“检答网”“检答网集萃”“检察日报答疑”中的内容。
- 用户咨询检察机关办案实务、检察业务疑难问题。
- 用户问题涉及认罪认罚、不起诉、抗诉、逮捕、羁押、国家赔偿、公益诉讼、社会公共利益、侦查监督、刑事执行检察、控告申诉检察、未成年人检察、民事行政检察等主题。
- 用户使用通俗语言描述法律问题，需要先转化为法律/检察术语后再检索内置资料。

不适用于以下场景：

- 要求完整法律法规检索。
- 要求裁判文书、指导性案例或类案检索。
- 要求针对具体案件出具正式法律意见。
- 要求超出检答网集萃第 1–140 批资料范围的结论。

如问题超出本技能资料范围，应明确说明未在检答网集萃中检索到相关内容，再根据用户授权改用其他检索渠道。

## 文件结构

```text
jiandawang-jicui-consultation/
├── SKILL.md
├── README.md
├── LICENSE
├── scripts/
│   ├── build_index.py
│   └── search_jiandawang.py
├── references/
│   ├── index.md
│   ├── legal-term-map.md
│   └── batches/
│       ├── 检答网集萃（第一批）.md
│       ├── 检答网集萃（第二批）.md
│       ├── ...
│       └── 检答网集萃（第一百四十批）.md
└── evals/
    └── evals.json
```

## 安装方式

### 方式一：安装为用户级 Claude Code 技能

适合希望在所有项目中使用本技能的用户。

macOS / Linux：

```bash
git clone <仓库地址> ~/.claude/skills/jiandawang-jicui-consultation
```

Windows Git Bash：

```bash
git clone <仓库地址> "$HOME/.claude/skills/jiandawang-jicui-consultation"
```

Windows PowerShell：

```powershell
git clone <仓库地址> "$env:USERPROFILE\.claude\skills\jiandawang-jicui-consultation"
```

安装后重新打开 Claude Code，或开启新的 Claude Code 会话，即可在可用技能中看到 `jiandawang-jicui-consultation`。

### 方式二：安装为项目级 Claude Code 技能

适合只希望在某个项目中使用本技能的用户。

在目标项目根目录执行：

```bash
git clone <仓库地址> .claude/skills/jiandawang-jicui-consultation
```

### 目录要求

安装后的目录必须保持以下结构：

```text
<skills-dir>/jiandawang-jicui-consultation/SKILL.md
<skills-dir>/jiandawang-jicui-consultation/scripts/search_jiandawang.py
<skills-dir>/jiandawang-jicui-consultation/references/batches/*.md
```

不要只复制 `SKILL.md`，否则技能无法完成本地全文检索。

### 路径说明

本仓库中的脚本默认按自身所在位置定位 `references/` 和 `scripts/` 目录，不依赖维护者本机的绝对路径。README 中出现的 `~/.claude/skills/`、`$HOME/.claude/skills/` 和 `$env:USERPROFILE\.claude\skills\` 只是 Claude Code 技能安装位置示例。仓库文件中不应包含维护者本机路径。

## 快速测试

安装后，可在技能目录内运行：

```bash
PYTHONIOENCODING=utf-8 python scripts/search_jiandawang.py --query "公安机关补充侦查后案管部门能否审查受案条件" --top-k 3 --json
```

预期能够检索到类似结果：

```text
检答网集萃第6批·问题1（检察日报，2019-05-14）
```

如果系统中的 Python 命令是 `python3`，请把示例命令中的 `python` 替换为 `python3`。

## 主要文件说明

### `SKILL.md`

Claude Code 技能主文件。

它定义了：

- 技能名称和触发描述。
- 何时应使用本技能。
- 必须先检索内置全文再回答的规则。
- 通俗表达转法律术语的处理方法。
- 固定引用格式。
- 未检索到内容时的处理方式。
- 禁止编造批次号、问题号、发布日期、专家姓名和答疑意见等要求。

引用格式固定为：

```text
检答网集萃第X批·问题Y（检察日报，YYYY-MM-DD）
```

### `README.md`

项目说明文件。

用于说明本技能的用途、资料范围、重要声明、安装方式、授权方式、目录结构、核心脚本和维护方法。

### `LICENSE`

MIT License 授权文本。

用于说明本项目的开源授权条款。分发或再发布本项目时，应保留该文件。

### `references/batches/`

内置全文数据目录。

当前包含检答网集萃第 1–140 批 Markdown 文件，共 140 个文件。每个文件对应一个批次，文件名采用中文批次号，例如：

- `检答网集萃（第一批）.md`
- `检答网集萃（第一百四十批）.md`

每个 Markdown 文件通常包含：

- 文章信息
- 原始标题
- 发布日期
- 来源
- 原始链接
- 问题标题索引
- 一个或多个问题块

少数早期批次含多个问题，因此引用时必须精确到“批次 + 问题号”。

### `references/index.md`

自动生成的索引文件。

该文件由 `scripts/build_index.py` 生成，用于快速了解数据分布和缩小检索范围。它包含：

- 语料概览
- 按批次索引
- 按问题索引
- 按咨询类别分布
- 主题关键词索引

注意：`index.md` 只是辅助定位文件。正式回答仍应以全文检索和完整问题块为依据。

### `references/legal-term-map.md`

通俗表达与法律/检察术语映射表。

用于将用户的口语化问题扩展为更适合全文检索的法律术语。例如：

```text
人被抓了、被抓了、抓起来 -> 刑事拘留、逮捕、羁押、国家赔偿、刑事赔偿
证据不够、不告了、没起诉 -> 事实不清、证据不足、不起诉、存疑不起诉
环境脏乱差、小区污染 -> 公益诉讼、社会公共利益、环境公益
```

该文件只用于扩展检索词，不得把映射内容直接作为法律结论。

### `scripts/build_index.py`

索引生成和结构校验脚本。

主要功能：

- 解析 `references/batches/*.md`。
- 提取批次号、发布日期、来源、原始链接。
- 提取问题号、问题标题、咨询类别、咨询内容、解答专家、解答内容。
- 生成固定引用格式。
- 输出 `references/index.md`。
- 校验批次数、问题数、缺失字段和重复引用。

常用命令：

```bash
PYTHONIOENCODING=utf-8 python scripts/build_index.py --strict
```

如需 JSON 格式校验结果：

```bash
PYTHONIOENCODING=utf-8 python scripts/build_index.py --json --strict
```

### `scripts/search_jiandawang.py`

本地全文检索脚本。

主要功能：

- 接收用户问题或检索词。
- 读取 `legal-term-map.md` 扩展检索词。
- 检索 `references/batches/*.md` 中的完整问题块。
- 输出命中问题的批次号、问题号、发布日期、咨询类别、解答专家、摘要、匹配词和固定引用。
- 标记检索结果支撑强度：
  - `direct_candidate`：可进入完整问题块核验的候选结果。
  - `weak`：仅宽泛主题命中，不能直接作为答复依据。

常用命令：

```bash
PYTHONIOENCODING=utf-8 python scripts/search_jiandawang.py --query "事实不清证据不足不起诉后公安继续侦查能否申请国家赔偿" --top-k 8 --json --include-block
```

### `evals/evals.json`

初始测试用例文件。

当前覆盖：

- 直接法律术语检索。
- 通俗表达转法律术语检索。
- 公益诉讼和社会公共利益问题。
- 抢夺方向盘和妨害安全驾驶问题。
- 无直接支撑内容时不得编造的问题。

## 使用流程

技能被触发后，建议按以下流程执行：

1. 判断用户问题是否属于检答网集萃资料范围。
2. 如果用户使用通俗表达，先参考 `references/legal-term-map.md` 扩展法律术语。
3. 查看 `references/index.md`，初步定位可能相关的批次和问题。
4. 运行 `scripts/search_jiandawang.py` 进行全文检索。
5. 阅读检索结果中的完整问题块，判断是否能直接支撑用户问题。
6. 如能支撑，基于检答网答疑内容整理答复，并逐条标注固定引用。
7. 如不能支撑，说明未在检答网集萃中检索到相关内容，不得编造。

## 回答规范

有检索结果时，回答应类似：

```markdown
依据内置检答网集萃检索结果，可以参考如下意见：

1. ...
   引用：检答网集萃第X批·问题Y（检察日报，YYYY-MM-DD）

检索说明：本回答仅依据内置检答网集萃中检索到的内容整理，不等同于完整法律法规、司法解释或案例检索意见。
```

未检索到可支撑内容时，回答应类似：

```markdown
未在检答网集萃中检索到相关内容，因此不能基于检答网集萃给出确定答复。

如你需要，我可以在你授权后改用法律法规、司法解释、指导性案例或其他公开资料继续检索。
```

## 维护方法

最高人民检察院后续发布新批次后，可按以下流程更新：

1. 将新批次 Markdown 文件放入 `references/batches/`。
2. 确认文件结构包含文章信息、发布日期、来源、原始链接、问题标题索引和问题块。
3. 运行索引生成脚本：

```bash
PYTHONIOENCODING=utf-8 python scripts/build_index.py --strict
```

4. 使用典型问题运行检索脚本，确认新批次可被命中。
5. 如新批次出现新的高频通俗表达或业务术语，更新 `references/legal-term-map.md`。
6. 必要时更新 `evals/evals.json` 增加测试用例。

## 已验证的数据状态

当前版本已完成基础结构校验：

- Markdown 文件数：140
- 批次数：140
- 问题块数：144
- 缺失批次：0
- 缺失发布日期：0
- 缺失来源：0
- 缺失问题标题：0
- 缺失解答内容：0
- 重复引用：0

全部问题的引用格式均符合：

```text
检答网集萃第X批·问题Y（检察日报，YYYY-MM-DD）
```

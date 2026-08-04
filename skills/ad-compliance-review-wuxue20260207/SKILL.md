---
name: ad-compliance-review
description: 广告公司 AI 合规审查。基于客户品牌调性与违禁词库，对广告/营销文案做合规风险审查（广告法违禁词、绝对化用语、医疗功效暗示、平台限制、品牌调性冲突）并给出修改建议。当用户需要审查广告文案、排查违禁词、做品牌合规检查，或广告/营销公司要为客户提供"上线前合规闸"服务时使用。也适用于把合规审查封装成可售卖的 AI 功能。
agent_created: true
version: "1.4.1"
---

# 广告公司 AI 合规审查

## Overview

为广告 / 营销公司提供一个可复用的"文案合规审查"能力：在文案发布前，自动对照**客户品牌调性**与**违禁词库**排查风险，输出违规项清单与修改建议。该能力既可直接用于日常审稿，也可作为对客户收费的增值功能（"AI 合规闸"）。

## When to use

- 审查一条待发布的广告 / 营销文案是否违反广告法或平台规则
- 排查绝对化用语（第一、最佳、顶级…）、医疗功效暗示（治疗、抗炎…）、比价绝对词（最便宜、全网最低…）
- 校验文案是否违背某客户的品牌调性 / 禁用表达
- 为广告客户交付"合规审查"服务，或把该功能产品化售卖

## 内置 demo 数据（开箱即用）

本 skill 自带一套可运行的示例客户资料，无需自备数据即可体验完整审查流程：

- 路径：`sample_data/demo_client/`
- `brand.md`：示例美妆客户「星澜」的品牌调性与禁用词
- `banned_words.md`：违禁词表（绝对化 / 医疗功效 / 平台限制分段）
- `cases.md`：历史案例素材（供进阶 RAG 使用）

直接运行即可看到效果：

```bash
python scripts/review.py --client sample_data/demo_client \
  --copy "星澜精华是市面上最好用的修护产品，治疗各类肌肤问题，全网最低价！"
```

预期命中：最好（绝对化）、治疗（医疗功效）、全网最低 / 最低（平台限制+绝对化），整体风险等级=高。

## Core workflow

1. **准备客户资料**：在该客户目录（如 `sample_data/<client>/` 或自建 `data/<client>/`）放两份 Markdown：
   - `brand.md`：品牌定位、调性、语气、禁用词（可用 Markdown 前置 `tags: [品牌, 调性]`）
   - `banned_words.md`：违禁词表，按「绝对化用语 / 医疗功效暗示 / 平台特别限制」分段，词条用 `、` 分隔或用 `「」` 标注
2. **运行审查脚本**：调用 `scripts/review.py`，传入客户目录与待审文案，得到结构化违规报告。
3. **解读报告**：报告列出每条命中（命中词、风险类型、严重度、建议替换），并给出整体风险等级（高 / 中 / 低）。
4. **（可选）生成改写文案**：若传入 `config.json`（含 LLM `api_key`），脚本会调用大模型产出"去除违规、保留原意"的改写版本。大模型调用内置**自动重试**：遇到网络抖动 / 限流（429）/ 5xx 等瞬时故障时，按指数退避（1×、2×、4×…）自动重试最多 `max_retries` 次（默认 3），仅在不可恢复错误（401/403/404 或重试耗尽）时才提示失败，避免一次网络抖动就放弃。可在 `config.json` 的 `llm` 段调 `max_retries` 与 `retry_delay`（秒，默认 1.5）。
5. **（进阶）语义级审查**：结合 RAG 知识库（见 `references/ad_agency_kb.md`）做更细的调性 / 措辞一致性审查与改写。

## Quick start（脚本）

`scripts/review.py` 零依赖、纯标准库，可直接运行：

```bash
# 基本审查（返回违规清单）
python scripts/review.py \
  --client sample_data/demo_client \
  --copy "星澜精华是市面上最好用的修护产品，治疗各类肌肤问题，全网最低价！"

# 输出 JSON（便于集成到系统）
python scripts/review.py --client sample_data/demo_client --copy "..." --json

# 接入大模型生成改写文案（默认国内 DeepSeek，--config 提供 key，或用环境变量 AD_REVIEW_API_KEY）
python scripts/review.py --client sample_data/demo_client --copy "..." --config config.json

# 或一键切换其他国内模型（--preset，key 走环境变量更省事）
python scripts/review.py --client sample_data/demo_client --copy "..." --preset qwen
```

脚本默认内置一份"绝对化 / 医疗功效"通用基线词表，并与客户 `banned_words.md` 合并去重；以客户自有词表为优先。

## 接入大模型改写（config.json）

可选。在 skill 根目录放置 `config.json`（参考 `config.example.json`）即可让 `review.py --config` 产出"去除违规、保留原意"的改写文案。所有字段均位于 `llm` 段，留空或删除整段则只做规则审查：

| 字段 | 说明 | 默认 |
|------|------|------|
| `api_key` | 模型服务 API Key | 无（留空则不改写；也可用环境变量 `AD_REVIEW_API_KEY`） |
| `api_base` | 模型接口 Base URL | `https://api.deepseek.com/v1`（国内默认） |
| `chat_model` | 对话模型名 | `deepseek-chat`（国内默认） |
| `temperature` | 生成温度 | `0.2` |
| `max_retries` | 瞬时故障最大重试次数（网络抖动/429/5xx） | `3` |
| `retry_delay` | 首次重试间隔（秒，指数退避基准） | `1.5` |

> 默认已按**国内模型（DeepSeek）**配置，开箱即用；换其他国内模型用 `--preset` 更快捷（见下方）。

## 国内模型一键适配（v1.4.0）

默认配置即国内模型，**复制 `config.example.json` 为 `config.json` 填 key 即可用 DeepSeek**，无需任何海外服务。若要换其他国内大模型，两种方式任选：

**方式 A：命令行 `--preset`（最省事，不用改文件）**
```bash
# 用 DeepSeek（默认）
python scripts/review.py --client sample_data/demo_client --copy "..." --preset deepseek

# 用通义千问 / 智谱 / 腾讯混元 / 豆包 / Kimi / 硅基流动
python scripts/review.py --client sample_data/demo_client --copy "..." --preset qwen
python scripts/review.py --client sample_data/demo_client --copy "..." --preset zhipu
python scripts/review.py --client sample_data/demo_client --copy "..." --preset hunyuan
python scripts/review.py --client sample_data/demo_client --copy "..." --preset doubao
python scripts/review.py --client sample_data/demo_client --copy "..." --preset kimi
python scripts/review.py --client sample_data/demo_client --copy "..." --preset siliconflow

# 列出所有内置预设及其端点 / 默认模型
python scripts/review.py --list-presets
```
> `--preset` 仅自动填 `api_base` 与 `chat_model`，**API Key 仍从 `config.json` 或环境变量 `AD_REVIEW_API_KEY` 读取**（密钥不落盘更安心）。

**方式 B：在 `config.json` 的 `llm` 段手动填 `api_base` / `chat_model`**（参考上面参数表默认值）。

**内置预设一览**

| 预设名 | 服务商 | 默认模型 | api_base |
|--------|--------|----------|----------|
| `deepseek` | 深度求索 | `deepseek-chat` | `https://api.deepseek.com/v1` |
| `qwen` | 阿里通义千问 | `qwen-plus` | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `zhipu` | 智谱 GLM | `glm-4-flash` | `https://open.bigmodel.cn/api/paas/v4` |
| `hunyuan` | 腾讯混元 | `hunyuan-turbo` | `https://api.hunyuan.cloud.tencent.com/v1` |
| `doubao` | 字节豆包（火山方舟） | `doubao-seed-1.6-250615` | `https://ark.cn-beijing.volces.com/api/v3` |
| `kimi` | 月之暗面 | `moonshot-v1-8k` | `https://api.moonshot.cn/v1` |
| `siliconflow` | 硅基流动（聚合） | `deepseek-ai/DeepSeek-V3` | `https://api.siliconflow.cn/v1` |

> 注：以上均为 **OpenAI 兼容端点**，`review.py` 直接调用其 `/chat/completions`，无需额外依赖。豆包（火山方舟）的 `chat_model` 需替换为你方舟控制台的实际接入点 ID；其余预设的默认模型一般可直接用，也可在 `config.json` 覆盖。

> 版本与变更详见 [CHANGELOG.md](CHANGELOG.md)。

## 风险等级判定

- **高**：命中绝对化用语或医疗功效暗示（广告法高风险，易被罚 / 被下架）
- **中**：命中品牌禁用词或平台特别限制（违规但风险相对可控）
- **低 / 通过**：未命中任何词条

## 给客户的卖点话术

> 我们交付的不只是文案，还有一道 AI 合规闸——上线前自动比对《广告法》与贵司品牌红线，把违规风险挡在发布之前。

## 合规风险报告生成器（获客钩子）

`scripts/generate_report.py` 可批量扫描客户历史文案目录，自动产出一份**可发给客户的 HTML 合规体检报告**——含风险概览、等级分布饼图、违规类型柱状图、高频违规词与逐条文案明细。把报告发给客户，用他自己的风险数据打动他，是天然的获客钩子。报告含「打印 / 另存为 PDF」按钮，零依赖、可在任意机器生成。

```bash
# 扫描客户历史文案目录，生成体检报告
python scripts/generate_report.py \
  --client sample_data/demo_client \
  --docs sample_data/demo_docs \
  --name "星澜美妆" \
  --out report.html

# 整文件作为一条文案（而非按行拆分）时加 --no-line-mode
```

- `--client`：客户资料目录（审查依据，同 review.py）
- `--docs`：历史文案目录或文件；默认每行一条，目录支持 .txt/.md
- `--name`：报告抬头客户名
- `--out`：输出 HTML（浏览器打开后可打印为 PDF）
- 内置示例：`sample_data/demo_docs/sample_ads.txt`（8 条文案，可直接试跑）

## 在线自助提交页（完全自助获客）

`scripts/webapp.py` 是一个零依赖的 Web 服务：把 skill 部署到一台机器（或内网），把网址发给客户，客户自己打开网页、上传历史文案目录（或粘贴），**自动生成并下载合规体检报告**——全程无需你们人工介入，是成本趋近于零的获客钩子。

```bash
# 启动在线提交页（默认 8000 端口）
python scripts/webapp.py --port 8000
# 用专属客户词库启动（路径会显式校验，不存在/错配将报错退出）
python scripts/webapp.py --client sample_data/demo_client --port 8000
# 浏览器打开 http://127.0.0.1:8000
```

- 客户可「选择整个文件夹」（.txt/.md，每行一条）或手动多选文件，也支持直接粘贴文案
- 默认使用内置通用广告法基线词库（sample_data/demo_client）做审查；加 `--client <客户目录>` 可切换为专属词库；报告末尾引导客户接入专属词库
- 复用 review.py + generate_report.py，零第三方依赖，任意装了 Python 的机器即可运行
- 部署建议：放一台常驻小服务器（或内网/云主机），把链接放进官网「免费体检」入口或销售邮件

## 打包为可售卖功能

1. 把 `review.py` 接入客户的投稿 / 审核系统（Web 表单或 API）。
2. 每份客户资料独立成租户，资料隔离（参考 `references/ad_agency_kb.md` 的权限隔离设计）。
3. 输出报告可导出为 PDF / 工单，作为交付物向客户收费。

## 反模式与 FAQ（遇到麻烦先看这节）

> 本能力默认是**关键词 + 正则的规则匹配**（零依赖、纯标准库），不是大模型语义理解。下列每一条都对应脚本的真实行为，踩过就知道为什么。

### 反模式（别这样用）

1. **别指望它会"读懂"语义** —— 默认扫描是词库命中 + "最X"正则，换说法的违规（如"效果惊人""远超同类"）查不出。要语义级改写须加 `--config` 接入大模型（但扫描本身仍基于词库，不会变语义）。
2. **别把 `--client` 指错路径或指成文件** —— `review.py` / `generate_report.py` 的 `--client` 必须是**含 `banned_words.md` 与 `brand.md` 的目录**。脚本现已**显式校验**：路径不存在或指向文件时直接报错退出（退出码 2）并说明原因；目录存在但缺少客户词表时打印明确【警告】后回退内置基线（不再静默）。仍建议用绝对路径并确认目录里有 `banned_words.md` / `brand.md`。
3. **别在 webapp 里期待"按客户专属词库"审查** —— `webapp.py` 默认使用内置 `demo_client` 做通用基线审查，且**不含大模型改写**；如需在自助页用专属词库，启动时可加 `--client <客户目录>`（同样会显式校验路径）。它定位是"免费通用体检 / 获客钩子"。真正的客户专属审查请用 `review.py` / `generate_report.py --client <客户目录>`。
4. **别把整篇长文当一条文案** —— `generate_report.py` 默认"每行一条"。一条广告跨多行、或多条文案堆在一个 `.txt` 里，会被拆成碎片、上下文断裂。单条多行广告请加 `--no-line-mode`（整文件为一条）。
5. **别把 `.docx` / `.pdf` / 图片 直接丢进来** —— 只认 `.txt` / `.md`（webapp 也只收这两类）。Word / PDF 需先导出为纯文本，否则目录模式读到 0 条会直接退出。
6. **别把品牌禁用词写在没含"禁用词"三字的行里** —— `brand.md` 只解析含"禁用词"字样的行里的词条；放别处会被忽略。
7. **别把违禁词写成"孤行无分隔符"** —— `banned_words.md` 中一行要被识别，需含 `、` 或 `，` 或"严禁"且长度 < 120；单独一行只写"第一"不会被加载。建议用「」标注或用 `、` 分隔。
8. **别以为报告能替代人工终审 / 法律意见** —— 工具是辅助闸；广告法、平台规则动态变化，词库需持续维护；高风险项仍需人工确认。
9. **别指望 webapp 自动持久化或带鉴权** —— 它无状态、无登录、无数据库，重启即失；公网部署需自行加反向代理 / 鉴权 / HTTPS。
10. **别过度信任"疑似绝对化"启发式** —— "最X"正则只匹配"最 + 1 个汉字"（"最优"能命中，"最最棒"等变体或复合说法可能漏），其余靠内置词表。

### FAQ（常见问题）

| 问题 | 原因 | 解决 |
|------|------|------|
| 为什么有些明显违规没查出来？ | 默认是关键词/正则匹配，换说法的词库里没有就会漏 | 把漏掉的说法补进客户 `banned_words.md`；或接大模型做语义改写（仅改写，扫描仍基于词库） |
| 为什么报告里没有"改写建议"？ | 只有 `review.py` 在传 `--config`（含有效 `api_key`）时才生成改写；webapp / generate_report 默认不调大模型 | 用 `review.py --config config.json` 产出带改写的审查 |
| 为什么配了客户词库，审查结果却和 demo 一样？ | 旧版脚本在 `--client` 路径指错时会静默回退内置基线；**v1.3.0 起已改为显式报错**：先确认是否看到【错误】/【警告】输出，再用绝对路径，确认目录里有 `banned_words.md` / `brand.md`；用 `--json` 核对返回里的 `client_warning` 字段与命中是否来自"客户"分类 |
| 上传文件夹后提示"未发现可分析的文案"？ | 文件夹里只有 `.docx`/`.pdf` 等非文本，或文件被浏览器拦截 | 导出成 `.txt` 再传，或直接粘贴文案（每行一条） |
| 报告里出现"异常"等级是坏了吗？ | 某条文案编码损坏/超长导致扫描失败 | 不是。该条单独标"异常"并说明，其余正常出报告；建议单独复核或重提这部分 |
| 提交时报"提交内容过大"？ | 单次上传超 3MB 上限 | 分批次上传，或先清理超大文件（长日志、整本书等） |
| 点"生成报告"一直转圈 / 报"无法连接到服务"？ | 后端 `webapp.py` 没在运行，或网络/代理阻断 | 确认已执行 `python webapp.py --port 8000` 且无报错；检查防火墙/端口映射（公网需端口转发或反向代理） |
| 接自己的大模型改写报 401 / 403 / 429？ | 401/403=Key 无效或未授权；404=api_base/chat_model 不匹配；429=限流 | 核对 `config.json`；详见脚本的人话提示（401/403 鉴权、404 地址、429 限流、网络不可达） |
| 想让不同客户资料完全隔离（不串味）？ | webapp 是通用版不隔离 | 每个客户用独立 `--client` 目录（租户隔离）；生产化参考 `references/ad_agency_kb.md` 的权限隔离设计 |
| 这个词库要一直维护吗？ | 广告法、各平台规则会变 | 要定期更新，这也是持续收费/维护的钩子 |

## 质量评测记录

真实使用评测与异常处理验证，详见 [EVALUATION.md](EVALUATION.md)。摘要：

- **异常处理 4.3（2026-07-21）**：路径错误 / 词库缺失 / 网络限流均有明确提示，无"看不懂的错误代码"。
- 历次评分：功能完善性 4.8、运行稳定性 4.3、国内适配性 4.3 等，均已对应版本修复 / 改进（见 CHANGELOG）。

## Resources

### scripts/
- `review.py`：核心审查脚本，零依赖，支持 `--client / --copy / --json / --config`。`--client` 路径显式校验（不存在/非目录直接报错，缺词表明确告警）；模型调用失败时按错误类型给出人话提示（401/403 鉴权、404 地址、429 限流、网络不可达），而非原始报错；并对网络抖动/限流/5xx 自动重试（指数退避）。
- `generate_report.py`：批量报告生成器，零依赖，输入历史文案目录产出可发客户的 HTML 合规体检报告；单条文案数据异常时仅标注该条为「异常」，不拖垮整份报告。
- `webapp.py`：在线自助提交页，零依赖 Web 服务（http.server），客户自助上传文案生成报告；支持 `--client <客户目录>` 切换专属词库，并对客户目录做与 CLI 一致的显式校验（不存在/非目录报错退出，缺词表告警）；所有异常（空文案 / 坏数据 / 提交过大 / 分析异常 / 服务中断）均返回带「可能原因 + 建议操作」的友好页面，前端网络中断也有清晰提示。

### references/
- `ad_agency_kb.md`：广告公司 AI 知识库（RAG）脚手架说明，介绍如何把本审查能力升级为带语义检索的多客户知识库与权限隔离架构。

### 交付与版本
- `config.example.json`：客户自助配置模板（含 `llm` 段全部字段与说明）。
- `CHANGELOG.md`：版本变更与升级指引（当前 v1.4.1）。
- `EVALUATION.md`：质量评测记录（历次维度评分与原文）。

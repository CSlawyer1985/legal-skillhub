# 广告合规审查宝 · 版本变更记录（CHANGELOG）

## v1.4.1 — 评测记录沉淀（2026-07-21）

本版本**无代码变更**，仅把真实使用评测沉淀为正式文档，作为质量背书与改进闭环记录；与 v1.4.0 行为完全一致。

### 新增 / 更新

1. **新增 `EVALUATION.md` 质量评测记录**
   - 记录 2026-07-21 异常处理评测（4.3 分）原文，并汇总历次维度评分（功能完善性 4.8 / 运行稳定性 4.3 / 异常处理 4.5→4.3 / 国内适配性 4.3）。
   - 每条评测附「对应实现 / 处置」，形成"反馈 → 改进 → 验证"闭环。

2. **`SKILL.md` 加「质量评测记录」小节**，引用 `EVALUATION.md`；修正「交付与版本」段的当前版本号为 v1.4.1。

3. **版本号同步**：`SKILL.md` / `_meta.json` / `_skillhub_meta.json` 升至 **1.4.1**。

### 本次收录的异常处理评测（2026-07-21）

> 输入路径错了或词库找不到，会明确告诉你问题出在哪里；网络出错或限流了也有提示，不像有些工具那样报个看不懂的错误代码。

对应能力（已在 v1.3.0 / v1.4.0 实现）：`--client` 显式校验（错配报错 exit 2 / 缺词表告警）、`llm_rewrite` 按错误类型人话提示 + 网络抖动/429/5xx 自动重试。

---

## v1.4.0 — 国内模型一键适配（2026-07-20）

本版本针对真实使用反馈（国内适配性 4.3："默认接国外模型，需要自己配置才能用国内大模型"）做了开箱即用的国内适配，让大模型改写无需海外服务、无需手填端点。

### 新增 / 修复

1. **`config.example.json` 默认改为国内模型（DeepSeek）**
   - 原默认 `api_base=https://api.openai.com/v1` + `chat_model=gpt-4o-mini`（海外）。
   - 现默认 `api_base=https://api.deepseek.com/v1` + `chat_model=deepseek-chat`。复制模板填 key 即用国内模型，改写了"需要自己配置"的痛点。

2. **`--preset` 一键切换国内大模型（review.py）**
   - 内置 7 个国内 OpenAI 兼容端点预设：`deepseek` / `qwen`(通义千问) / `zhipu`(智谱 GLM) / `hunyuan`(腾讯混元) / `doubao`(字节豆包) / `kimi`(月之暗面) / `siliconflow`(硅基流动)。
   - 用法：`python scripts/review.py --client <目录> --copy "..." --preset qwen`（key 走 `--config` 或环境变量）。
   - 新增 `--list-presets` 列出全部预设的端点与默认模型。
   - `--preset` 仅自动填 `api_base` 与 `chat_model`，API Key 仍从 `config.json` 或环境变量读取。

3. **API Key 支持环境变量 `AD_REVIEW_API_KEY`（密钥不落盘）**
   - `llm_rewrite` 现在优先读 `config.json` 的 `llm.api_key`，缺失时回退到环境变量 `AD_REVIEW_API_KEY`，便于密钥不写入文件、更符合国内隐私合规习惯。

### 验证结果（实跑）

- ✅ `--list-presets` 正确列出 7 个国内预设（端点 + 默认模型）
- ✅ `--preset deepseek` 触发改写调用，默认走国内端点（用占位 key 验证不崩、错误提示友好）
- ✅ 环境变量 `AD_REVIEW_API_KEY` 可被识别（`config.json` 留空时仍生效）
- ✅ `config.example.json` 默认 `api_base` 已为国内 DeepSeek，JSON 合法

### 内置国内预设一览

| 预设名 | 服务商 | 默认模型 | api_base |
|--------|--------|----------|----------|
| `deepseek` | 深度求索 | `deepseek-chat` | `https://api.deepseek.com/v1` |
| `qwen` | 阿里通义千问 | `qwen-plus` | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `zhipu` | 智谱 GLM | `glm-4-flash` | `https://open.bigmodel.cn/api/paas/v4` |
| `hunyuan` | 腾讯混元 | `hunyuan-turbo` | `https://api.hunyuan.cloud.tencent.com/v1` |
| `doubao` | 字节豆包（火山方舟） | `doubao-seed-1.6-250615` | `https://ark.cn-beijing.volces.com/api/v3` |
| `kimi` | 月之暗面 | `moonshot-v1-8k` | `https://api.moonshot.cn/v1` |
| `siliconflow` | 硅基流动（聚合） | `deepseek-ai/DeepSeek-V3` | `https://api.siliconflow.cn/v1` |

> 注：以上均为 OpenAI 兼容端点，直接调用 `/chat/completions`，零额外依赖。豆包的 `chat_model` 需替换为方舟控制台实际接入点 ID。

### 升级指引

1. 覆盖脚本即可，**无需改客户词库结构**。
2. 想用大模型改写：复制 `config.example.json` 为 `config.json` 填 key 即用（默认 DeepSeek）；或加 `--preset <名称>` 一键切其他国内模型。
3. 不想把 key 写进文件：设环境变量 `AD_REVIEW_API_KEY` 后直接 `--preset deepseek` 即可。

---

## v1.3.0 — 稳定性与异常处理正式加固（2026-07-19）

本版本针对真实使用反馈（运行稳定性 4.3 / 异常处理 4.5）做了两处关键修复，并补齐正式交付所需的配置模板与发布说明，把改动沉淀为可分发版本。

### 新增 / 修复

1. **LLM 改写自动重试（修复运行稳定性）**
   - `review.py` 的 `llm_rewrite` 新增指数退避重试：遇到网络抖动（`URLError`）、限流（HTTP 429）、服务端 5xx 等**瞬时故障**时，自动重试最多 `max_retries` 次（默认 3，间隔 1×/2×/4×…）。
   - 仅对可恢复瞬时故障重试；不可恢复错误（401/403 鉴权、404 地址、其他 4xx）仍直接给出人话提示，不浪费重试。
   - 重试耗尽才提示失败，并提供手动修改建议，避免一次网络抖动就放弃改写。

2. **`--client` 路径显式校验（修复静默失败）**
   - `review.py` / `generate_report.py` 新增 `validate_client_dir()`：
     - 路径不存在 / 指向文件 → **明确报错并以退出码 2 中止**，附原因。
     - 目录存在但缺 `banned_words.md` / `brand.md` → 打印**明确【警告】**（stderr + JSON `client_warning` 字段），再回退内置通用基线，不再"悄悄"只用内置词库。
   - `webapp.py` 同步：新增 `--client` 启动参数与启动校验，缺省仍用内置 `demo_client`；致命错误退出、缺词表告警，行为对齐 CLI。

### 验证结果（实跑）

- ✅ 正常审查 / 批量报告 / 在线自助页：功能不变，照常工作
- ✅ `--client` 指向**文件** → 报错退出（exit 2）+ 原因说明
- ✅ `--client` **路径不存在** → 报错退出（exit 2）+ 原因说明
- ✅ 目录存在但**缺客户词表** → 明确【警告】，JSON 带 `client_warning`，仍出报告（内置基线）

### 可调参数（写入 `config.json` 的 `llm` 段）

| 字段 | 说明 | 默认 |
|------|------|------|
| `api_key` | 模型服务 API Key | 无（留空则不改写） |
| `api_base` | 模型接口 Base URL | `https://api.openai.com/v1` |
| `chat_model` | 对话模型名 | `gpt-4o-mini` |
| `temperature` | 生成温度 | `0.2` |
| `max_retries` | 瞬时故障最大重试次数 | `3` |
| `retry_delay` | 首次重试间隔（秒，指数退避基准） | `1.5` |

### 交付物清单

- `scripts/review.py` / `generate_report.py` / `webapp.py`：核心逻辑（含校验与重试）
- `config.example.json`：客户自助配置模板（参考上方参数表）
- `SKILL.md`：使用说明、反模式、FAQ 已同步
- `CHANGELOG.md`：本文件

### 升级指引

1. 旧版用户直接覆盖脚本即可，无需改动客户词库结构。
2. 如需大模型改写，复制 `config.example.json` 为 `config.json` 并填入真实 `api_key`。
3. 历史「配了词库却和 demo 一样」的问题，现会以【错误】/【警告】显式暴露，先读 stderr / `client_warning` 即可定位路径问题。

---

## v1.2.0 — 报告生成与在线页

- 批量体检报告生成器（`generate_report.py`）
- 零依赖在线自助 Web 页（`webapp.py`）

## v1.0.x — 初始版本

- 关键词 + 正则的规则审查
- 内置绝对化 / 医疗功效通用基线
- 客户词库（banned_words.md / brand.md）合并去重

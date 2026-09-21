---
name: legal-builder-hub-cold-start-interview
description: 管理配置访谈：推荐并安装中国法 入门包（法律元力 七个 legal-skillpack-* 优先）。 全生态冷启动入口。用于首次安装、「帮我入门」、或 `--check-integrations` 重检 MCP。
metadata:
  displayName: 技能冷启访谈
  argument-hint: '[--redo] [--check-integrations] [--full]'
---

# legal-builder-hub-cold-start-interview

**中国法发行说明：** 配置写入 `$LEGAL_AGENT_PROFILE_HOME/legal-builder-hub/profile.md`（含 `## yuanli` → `base_url`）。allowlist 写入 `allowlist.yaml`。浏览/安装/更新优先 `references/yuanli-api.md` 的 REST API；离线回退 `yuanli-toolkits.yaml`。**不**默认推荐未本地化的 `privacy-legal` / `employment-legal` 英文插件。

1. 检查 `$LEGAL_AGENT_PROFILE_HOME/legal-builder-hub/profile.md`。若仅旧 Claude 缓存路径存在已填写的 CLAUDE.md（无 `[PLACEHOLDER]`），则迁移到 profile.md 并告知用户。
2. 执行 Part 0（角色 + 集成）及五个问题（或快速模式 Quick 路径子集）。
3. 按 profile 推荐中国法 入门包（`yuanli-toolkits.yaml`）。
4. 展示每个推荐包的描述；用户勾选。
5. 经 `legal-builder-hub-skill-installer` 安装（须 yes）；写入 profile.md、allowlist.yaml。

**`--check-integrations`：** 仅重跑 Part 0 集成可用性检查，更新 `profile.md` 中 `## Available integrations` 表，不改动角色与管理配置。在增删 MCP 连接器后使用。

探测时：仅在实际 MCP 调用成功时标 ✓；已配置未实测的标 ⚪ 并附一行如何确认。不得仅凭 `.mcp.json` 声明标 ✓。对用户说明集成状态时**用简体中文**。

---

## 冷启动检查

读取 `profile.md`：

- **不存在** → 开始访谈
- **含 `<!-- SETUP PAUSED AT: -->`** → 从该节继续
- **含 `[PLACEHOLDER]` 且无暂停注释** → 提供重新开始或从首个 placeholder 续做
- **已填且无 placeholder** → 除非 `--redo`，跳过

脚手架：`plugin/profile.md.template`。**兼容迁移**（仅 Claude Code 用户）：若用户曾在 Claude Code v1 装过本插件且 `~/.claude/plugins/cache/.../CLAUDE.md` 存在已填数据，将其迁移到新的 `profile.md`。其他 runtime（Codex / Cursor / OpenCode 等）不读 `~/.claude/`，直接走新流程。

## 共享公司画像

`$LEGAL_AGENT_PROFILE_HOME/company-profile.md`：

- **已有：** 一行确认后跳过公司问题
- **没有：** 按 `references/company-profile-template.md` 询问并写入，告知其他 cluster 将复用

公司级字段：执业场景、机构名、行业、规模、法域、监管、风险、升级链。插件级字段写在 hub `profile.md`。

## 目的

法律 skill 的「应用商店」入口：了解你的实践 → 推荐 入门包 → 经安装器安装。

## 安装作用域（Cursor 等）

若当前工作目录是**项目根**而非用户主目录，提示一次：

> **当前似为项目作用域**，skill 默认装到 `.cursor/skills`。若需全局可用，请改 `cd ~` 后再跑 `python3 install.py`，或显式 `python3 install.py --target ~/.claude/skills`（按你的平台改路径）。继续项目作用域？[继续 / 先改安装位置]**

主目录则静默跳过。

## 开场白（3–4 行）

> **`legal-builder-hub` 用于发现、安装、管理法律 skill。** 已有业务 cluster？优先从法律元力 装 `legal-skillpack-*`；也可 ``legal-builder-hub-registry-browser`` 浏览。
>
> **快速模式 Quick（约 2 分钟）：** 角色 + 实践领域 + 默认白名单（allowlist）/技能源（registry）。**完整模式 Full（约 15 分钟）：** 再加 入门包、部署场景、更新偏好、法律元力 `base_url`。
>
> 选快速模式还是完整模式？（随时 ``legal-builder-hub-cold-start-interview --full`` 升级。）

## 用户选择 快速模式 / 完整模式 之后

用中文说明本插件维护什么、本次设置做什么：

- **维护内容：** `profile.md`（你的个人配置档案）、`allowlist.yaml`（可信来源白名单）、`install-log.yaml`（安装日志）
- **本次作用：** 发现/安装/评审社区 skill；推荐中国法 入门包；写入可编辑纯文本配置
- **数据来源：** 仅本次访谈与用户确认内容；不读历史对话；会话中早先提到的信息须先问再写入

**为何重要：** 推荐包与更新策略都读 profile；信息越具体，推荐越像「为你定制」。

### 分支

**快速模式：** 只问角色 + 实践领域；其余标 `[DEFAULT]`。结束语：可用默认技能源（registry）/更新策略；随时 `--full` 或 `--redo <节>`。

**完整模式：** 走下方完整流程。

## 访谈节奏

- 能粘贴/链接的不要让用户重打（手册、升级矩阵、法域列表等）
- 需打字的问题明确说「请打字，我会等」
- 跳过须标 `[PENDING]` 或用户确认的 placeholder
- 每轮最多 2–3 个**可回答**的子问题
- **暂停：** 顶部写 `<!-- SETUP PAUSED AT: ... -->`，未答字段标 `[PENDING]`
- **法条/数字事实：** 写入前 sanity check，冲突则 `[premise flagged — verify]`

## 访谈正文

### 开场

> 我帮你发现并安装法律社区 skill。先确认你的角色和实践方向，再推荐 入门包。

### Part 0：角色与集成

#### 使用角色

> 日常谁在用？（写入 profile，供各 skill 非律师模式读取）
>
> 1. **律师/法务专业人员**
> 2. **非律师（有律师支持）** — 业务/采购/HR 等
> 3. **非律师（无固定律师）**

选 2 或 3 时说明一次：各 skill 会按此处角色调整护栏；不必每个插件重答。

选 3 时追加：

> 如需找律师或法务专业人士：可联系当地**律师协会**执业信息查询、**法律援助中心**（12348 法律服务热线）、或单位法务部门。企业用户可优先走内部法务升级链；个人可先咨询法律援助是否覆盖你的事项类型。

#### 已连接集成（办公通讯）

> 可选：把新 skill / 更新通知、合规提醒推送到你常用的办公平台。**国内默认三选一：飞书（Lark）/ 企业微信（WeCom）/ 钉钉（DingTalk）**；海外团队可选 Slack。不接也行——回退到本地 digest，不静默失败。

询问与引导：

1. 列出上述选项，问用户日常用哪个办公平台（可不选）
2. 用户选定后，引导安装对应连接器：
   - **飞书** → WorkBuddy 已内置 `connector:lexiang`（乐享）MCP，可直接启用
   - **企业微信 / 钉钉** → 用官方 API / Webhook（请用户粘贴已批准的 Webhook 地址或 MCP URL）
   - **Slack** → 仅海外场景，连接对应 Slack MCP
3. 连接建立后，后续 skill 更新通知、合规提醒经该平台推送
4. 不选任何平台 → 回退本地 digest（见下）

- 仅在实际调用 MCP 成功时标 ✓
- 无法探测时标 ⚪「已配置未验证」+ 一行连接说明
- **禁止**仅凭 `.mcp.json` 声明标 ✓

未连接任何办公平台时：说明可在下次 `registry-browser` / `auto-updater` 看到 digest，或写入 `digests/registry-sync-latest.md`。

报告格式：

> - ✓ [集成名] — 已连接（已实测）
> - ⚪ [集成名] — 已配置未验证
> - ✗ [集成名] — 未找到；回退：[方式]

浏览/安装/QA/更新**不依赖**任何办公平台连接。

将 Part 0 写入 profile 的 `## 使用角色` 与 `## 可用集成`（模板见 `profile.md.template`）。

**法律元力 站点（中国法 skillpack 主源）。** 在五个问题之前询问：

> 「法律元力站点根 URL 默认是 `https://yuanli.ailaw.cn`（不要尾斜杠）。用这个可以吗？或提供你们内网/测试环境地址。」

- 用户确认或跳过：写入 profile `## 法律元力` → `base_url` = `https://yuanli.ailaw.cn`（除非用户明确给出其他 URL）
- 试连 `GET {base_url}/api/toolkits/catalog`：
  - 成功（HTTP 200 + JSON）→「已连上法律元力 catalog」，记录 toolkit 数量
  - 失败 → 记 `[API 未连接]`，**自动走 `references/yuanli-toolkits.yaml` 静态兜底 + GitHub 社区 registry 双源**
- 注：法律元力 API 在 **v0.20.0-cn 验证已上线**（6 个公开 endpoint 全部 200，schema 与 `references/yuanli-api.md` 一致）。skill 设计为 resilient 模式——每次调用都试 API，失败时自动 fallback，无需独立 `api_available` flag 维护状态
- API 契约见 `references/yuanli-api.md`

**监视 registry / allowlist（五个问题之前）：**

> 是否已有团队信任的技能源（registry）列表或白名单（allowlist）？可粘贴或给路径；没有则用默认（yuanli-cn + 三家 GitHub）。安装器**先读** `allowlist.yaml`（可信来源白名单），严格模式 下未列出则拒绝 fetch。

**部署场景：**

> 安装 skill 的用途？个人自用 / 机构内部 / 嵌入对外产品？(Personal / Firm-internal / Product-embedding) — 决定 `licenses:` 种子。

写入 profile `## 可信来源` → `Deployment context: ...`

**必须写入 `allowlist.yaml`（不只写 profile 摘要）：**

1. 按 `skill-installer/references/allowlist.md` 写入：
   - `mode:` 默认建议 严格模式；个人/小所可提议 宽松模式，**须用户明确同意**
   - `registries:` 用户提供的 + 默认（含 yuanli-cn）
   - `publishers:` 含华宇元典、GitHub 组织名
   - `connectors:` 严格模式 下可提示粘贴批准的 MCP URL
   - `licenses:` 按部署场景种子（Personal / Firm-internal / Product-embedding；产品嵌入不含 GPL/AGPL 默认）
2. profile `## 可信来源` 写人类可读摘要
3. 告知路径：`.../legal-builder-hub/allowlist.yaml`

用户上传 allowlist 文件：解析后确认再写入。

**时效提醒（Freshness）：**

> 捆绑法规/模板类参考材料，多久未核验就提醒你？（法律法规类默认 6 个月；法定程序性规定类 12 月；模版与偏好类 24 月。）

写入 profile `## Freshness reminders` 表（见 `freshness.md`）；用户可收紧或选默认。

### 五个问题

1. **实践领域** — 法务/律所？商事、监管、公司、诉讼、研究、AI 治理、其他？（映射 入门包）

   **套不进选项时：** 请用户自由描述，据此填 profile，标注哪些模板字段不适用。

2. **行业** — 科技、金融、医疗、其他、不限？

3. **团队规模** — 个人、小团队(2–5)、大法务部？（影响 allowlist mode 默认值）

4. **最常做的工作** — 合同审查、合规、上市、尽调、研究等？

5. **工具熟练度** — 高级玩家（自己造 skill）/ 会改配置 / 开箱即用？

### 推荐（中国法 入门包）

按 profile 映射 **法律元力** toolkit（安装走 `legal-builder-hub-skill-installer` 的 zip 通道）：

| Profile | 入门包（toolkit_id） |
|---|---|
| 法务 / 律师 · 商事合同、科技行业 | `legal-skillpack-commercial-legal` + 可选 GitHub lpm-skills |
| 监管 / 合规 | `legal-skillpack-regulatory-legal` |
| 公司法务 / 治理 | `legal-skillpack-corporate-legal` |
| 诉讼 | `legal-skillpack-litigation-legal` |
| 法律研究 | `legal-skillpack-legal-research-cn` |
| AI 治理 | `legal-skillpack-ai-governance-legal` |
| 法学学习 / 法考 | `legal-skillpack-law-student` |
| 个人 / 小团队 | 上述中最轻量的 triage 类 skill；allowlist 默认倾向 宽松模式（须用户确认） |
| 高级玩家（Builder） | 开放技能源（registry）+ `legal-builder-hub-skills-qa` 框架；自行构建并 QA |

对每个推荐：展示 toolkit 描述与入口 skill 提示（`entry_skill_hint`）。用户勾选后再安装 — **必须** 明确 `yes`，安装由 `legal-builder-hub-skill-installer` 执行。

## 写入 profile

简明：profile + 已安装列表 + registry 偏好。脚手架：`plugin/profile.md.template`。

## 收尾

可选展示能力清单（中文）：

> - **浏览** — ``legal-builder-hub-registry-browser``（法律元力优先）
> - **安装** — ``legal-builder-hub-skill-installer``（allowlist + yes）
> - **更新** — ``legal-builder-hub-auto-updater``
> - **推荐** — ``legal-builder-hub-related-skills-surfacer``
> - **评审** — ``legal-builder-hub-skills-qa``

建议第一步：浏览并装一个与当前项目相关的包，感受 allowlist 门控。

- 已安装的列出来；是否开启 surfacer 通知
- 若业务 skill 需法条检索：提示连接元典等 MCP，否则引用会标未核验

结束语：

> 配置在 `$LEGAL_AGENT_PROFILE_HOME/legal-builder-hub/profile.md`（即你的个人配置档案，记录角色、偏好与集成状态，所有推荐和更新策略都基于它），可直接编辑；或用 ``legal-builder-hub-cold-start-interview --redo`` / ``--check-integrations`` / ``legal-builder-hub-customize``。

> **profile 会从使用中变准** — 输出不对时多半是某条配置要调；用 customize 或改文件即可。

## 默认监视的 registry

- **yuanli-cn**（`references/yuanli-toolkits.yaml` + API）
- **lpm-skills**、**lawvable** 两家 GitHub（见 `registries.yaml`）
- 可通过 ``legal-builder-hub-registry-browser`` 添加

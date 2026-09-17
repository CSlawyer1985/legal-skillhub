---
name: overseas-legal-compliance
slug: overseas-legal-compliance
displayName: 出海合规审查
license: MIT
version: 1.1.1
description: "出海合规法律检索 — 自动安装MCP + 一站式查询全球230+法域法律法规。触发词：查外国法律、出海合规、GDPR、AI Act、HIPAA、CCPA、多国法规对比、跨境投资合规、数据保护合规、安全框架映射（ISO 27001↔NIST↔SOC2）。支持一键安装全部MCP数据库或按国家名称安装。"
---

<!-- author: 陆凌燕（北京德恒（无锡）律师事务所） -->

# 出海合规法律检索

自动安装 MCP 数据库 + 一站式查询全球法律。先装数据库，再查法规。全程不需要编程基础。

## 核心规则：装完再查，不许跳过

**每次触发此 Skill 时，第一条消息必须先做两件事：**

### ① 环境预检（新增 — 来自几十次调试的教训）

mcp.json 里的 `command` 跑在**用户本地系统**上，不是 WorkBuddy 沙箱。先检查这三个：

```
which node    → npx 需要    (Ansvar 国别库全系列)
which python3 → py MCP 需要 (courtlistener 本地版)
which pipx    → pipx 需要   (仅 security-controls)
```

**检查结果处理：**

| 缺失项 | 影响 | 处理 |
|--------|------|------|
| Node.js (npx) | ❌ 所有 Ansvar 国别库装不了 | 让用户去 https://nodejs.org 下 LTS 版，一路点「下一步」 |
| python3 | ⚠️ 仅 courtlistener 本地版 / security-controls 本地版需要 | 缺的话跳过这两个，用远程 URL 替代 |
| pipx | ⚠️ 仅 security-controls 需要 | 缺的话 `pip3 install pipx`（你直接帮装），或跳过 security-controls |

### ② 检查 mcp.json 里有没有出海合规 MCP

读取 `~/.workbuddy/mcp.json`，扫描 `mcpServers` 中是否包含以下任意一个 key：

```
legal-data-hunter, eu-regulations, us-regulations, courtlistener,
taiwanese-law, open-legal-compliance-mcp, security-controls, yuandian-mcp-server,
wk-mcp-law, wk-mcp-case,
german-law, french-law, uk-law, japanese-law, korean-law,
singapore-law, indian-law, australian-law, saudi-law, uae-law,
canadian-law, italian-law, spanish-law, dutch-law, swedish-law,
brazilian-law, austrian-law, belgian-law, danish-law, finnish-law,
norwegian-law, irish-law, chinese-law
```

### ② 如果一个都没有 → 主动提出安装

**不要让用户自己装。你直接动手写 mcp.json。** 问用户一句话，然后立刻开工：

> 我帮你装出海的法规数据库。你先告诉我需要查哪些国家/地区的法律？
> 比如「德国」「日本」「欧盟」……我帮你装对应的。**不建议一下全装，用哪个装哪个最快。**

如果用户坚持全装，再提醒：「全部 6 个核心库约需 2-3 分钟，每个 10-30 秒。建议先装 3-4 个常用的，不够再加。」

等用户选了之后，按下方清单写入 `~/.workbuddy/mcp.json`。

---

## 数据库安装清单

### 核心 6 件套（按需选用，不建议一次全装）

这 6 个覆盖了 90% 出海合规场景。**全部无需 API Key，本地运行。**（数据源最后验证：2026-08-25）

```json
{
  "eu-regulations": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@ansvar/eu-regulations-mcp"],
    "description": "欧盟法规库 — GDPR/AI Act/DORA等49部法规全文",
    "disabled": false
  },
  "us-regulations": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@ansvar/us-regulations-mcp"],
    "description": "美国合规法规 — HIPAA/CCPA/SOX等联邦与州法律",
    "disabled": false
  },
  "courtlistener": {
    "url": "https://mcp.courtlistener.com/",
    "description": "美国判例检索 — 900万+判例、PACER文书（首次需OAuth登录）",
    "disabled": false
  },
  "taiwanese-law": {
    "type": "stdio",
    "command": "mcp-taiwan-legal-db",
    "args": [],
    "description": "台湾法规检索 — 司法院裁判书+全国法规库+宪法法庭（pip install mcp-taiwan-legal-db 后 command 写 mcp-taiwan-legal-db，跨平台可用）",
    "disabled": false
  },
  "security-controls": {
    "type": "stdio",
    "command": "scf-mcp",
    "description": "安全框架映射 — ISO27001/NIST/SOC2等262个框架双向对照",
    "disabled": false
  },
  "yuandian-mcp-server": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "yuandian-mcp-server"],
    "description": "华宇元典 — 中国大陆法规语义检索、法条详情、案例全文",
    "disabled": false
  }
}
```

> 💡 台湾法 MCP 有「离线兜底」：`references/tw-law-data/` 包含预制缓存数据（8,266 部法规目录 + 民法全文 + 劳基法全文 + 813 条大法官解释索引）。如果本地 MCP 连不上，直接用 Grep 搜这些 JSON 文件作为本地知识库。
>
> 🛠 台湾法 MCP 安装（跨平台）：`pip install mcp-taiwan-legal-db`，command 写 `mcp-taiwan-legal-db` 即可（pip 会把 entry point 加入 PATH，macOS / Linux / Windows 通用，无需写任何绝对路径）。clone 源码方式的 Windows/macOS 差异见 `references/mcp-setup-guide.md`。

### 进阶可选（需 API Key / 需认证，按需装）

以下数据源**不能开箱即用**，要么要 API Key，要么要手动 build，要么要企业授权。默认不装，遇到缺口再补：

```json
{
  "open-legal-compliance-mcp": {
    "type": "stdio",
    "command": "node",
    "args": ["/本地路径/open-legal-compliance-mcp/dist/index.js"],
    "env": {
      "GOVINFO_API_KEY": "从 api.govinfo.gov 免费申请",
      "COURTLISTENER_API_KEY": "从 courtlistener.com/api 免费申请"
    },
    "description": "美欧英加法规聚合 — GitHub 源码 clone + npm build（非 npm 包，TCoder920x/open-legal-compliance-mcp）",
    "disabled": false
  },
  "legal-data-hunter": {
    "url": "https://legaldatahunter.com/mcp",
    "description": "全球法律广域检索 — 230+法域初筛定位（需认证，非免费）",
    "disabled": false
  },
  "wk-mcp-law": {
    "url": "https://mcp.wkinfo.com.cn/mcp-servers/law/",
    "headers": {
      "Authorization": "Bearer 你的威科先行Token"
    },
    "description": "威科先行 — 中国大陆法规（需企业授权 Token）",
    "disabled": false
  }
}
```

### 按国家安装（用户说"德国"就装德国的）

**全部无需 API Key。** 配置模板（把 `{country-en}` 和 `{中文名}` 替换即可）：

```json
{
  "{country-en}-law": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@ansvar/{country-en}-law-mcp"],
    "description": "{中文名}法规检索",
    "disabled": false
  }
}
```

> ⚠️ **包名命名规律（第一性原理）**：Ansvar 国别包名用「**国家名词**」而非「形容词」。日本是 `japan`（不是 japanese）、韩国是 `south-korea`（不是 korean）、印度是 `india`（不是 indian）、巴西是 `brazil`（不是 brazilian）。**遇到 npm 404 先怀疑包名拼写，别急着报"包已下架"。**

完整映射表（共 53 国，2026-08-25 逐一验证 npm 存在）：

| 区域 | 用户说 | 配置 key | npm 包名 |
|------|--------|---------|---------|
| **亚太** | 中国 | `chinese-law` | `@ansvar/chinese-law-mcp` |
| | 日本 | `japanese-law` | `@ansvar/japan-law-mcp` |
| | 韩国 | `korean-law` | `@ansvar/south-korea-law-mcp` |
| | 新加坡 | `singapore-law` | `@ansvar/singapore-law-mcp` |
| | 澳大利亚/澳洲 | `australian-law` | `@ansvar/australian-law-mcp` |
| | 印度 | `indian-law` | `@ansvar/india-law-mcp` |
| | 越南 | `vietnamese-law` | `@ansvar/vietnamese-law-mcp` |
| | 印尼/印度尼西亚 | `indonesian-law` | `@ansvar/indonesian-law-mcp` |
| | 马来西亚 | `malaysian-law` | `@ansvar/malaysian-law-mcp` |
| | 巴基斯坦 | `pakistani-law` | `@ansvar/pakistani-law-mcp` |
| | 孟加拉国 | `bangladeshi-law` | `@ansvar/bangladeshi-law-mcp` |
| **欧洲** | 英国 | `uk-law` | `@ansvar/uk-law-mcp` |
| | 德国 | `german-law` | `@ansvar/german-law-mcp` |
| | 法国 | `french-law` | `@ansvar/french-law-mcp` |
| | 意大利 | `italian-law` | `@ansvar/italian-law-mcp` |
| | 西班牙 | `spanish-law` | `@ansvar/spanish-law-mcp` |
| | 荷兰 | `dutch-law` | `@ansvar/dutch-law-mcp` |
| | 瑞典 | `swedish-law` | `@ansvar/swedish-law-mcp` |
| | 奥地利 | `austrian-law` | `@ansvar/austrian-law-mcp` |
| | 比利时 | `belgian-law` | `@ansvar/belgian-law-mcp` |
| | 丹麦 | `danish-law` | `@ansvar/danish-law-mcp` |
| | 芬兰 | `finnish-law` | `@ansvar/finnish-law-mcp` |
| | 挪威 | `norwegian-law` | `@ansvar/norwegian-law-mcp` |
| | 爱尔兰 | `irish-law` | `@ansvar/irish-law-mcp` |
| | 波兰 | `polish-law` | `@ansvar/polish-law-mcp` |
| | 葡萄牙 | `portuguese-law` | `@ansvar/portuguese-law-mcp` |
| | 希腊 | `greek-law` | `@ansvar/greek-law-mcp` |
| | 匈牙利 | `hungarian-law` | `@ansvar/hungarian-law-mcp` |
| | 捷克 | `czech-law` | `@ansvar/czech-law-mcp` |
| | 罗马尼亚 | `romanian-law` | `@ansvar/romanian-law-mcp` |
| | 保加利亚 | `bulgarian-law` | `@ansvar/bulgarian-law-mcp` |
| | 克罗地亚 | `croatian-law` | `@ansvar/croatian-law-mcp` |
| | 斯洛伐克 | `slovak-law` | `@ansvar/slovak-law-mcp` |
| | 斯洛文尼亚 | `slovenian-law` | `@ansvar/slovenian-law-mcp` |
| | 爱沙尼亚 | `estonian-law` | `@ansvar/estonian-law-mcp` |
| | 拉脱维亚 | `latvian-law` | `@ansvar/latvian-law-mcp` |
| | 立陶宛 | `lithuanian-law` | `@ansvar/lithuanian-law-mcp` |
| | 冰岛 | `icelandic-law` | `@ansvar/icelandic-law-mcp` |
| | 卢森堡 | `luxembourg-law` | `@ansvar/luxembourg-law-mcp` |
| | 马耳他 | `maltese-law` | `@ansvar/maltese-law-mcp` |
| | 塞浦路斯 | `cypriot-law` | `@ansvar/cypriot-law-mcp` |
| **中东** | 沙特/沙特阿拉伯 | `saudi-law` | `@ansvar/saudi-law-mcp` |
| | 阿联酋 | `uae-law` | `@ansvar/uae-law-mcp` |
| | 土耳其 | `turkish-law` | `@ansvar/turkish-law-mcp` |
| | 埃及 | `egyptian-law` | `@ansvar/egyptian-law-mcp` |
| **美洲** | 加拿大 | `canadian-law` | `@ansvar/canadian-law-mcp` |
| | 巴西 | `brazilian-law` | `@ansvar/brazil-law-mcp` |
| | 墨西哥 | `mexican-law` | `@ansvar/mexican-law-mcp` |
| | 阿根廷 | `argentine-law` | `@ansvar/argentine-law-mcp` |
| | 智利 | `chilean-law` | `@ansvar/chilean-law-mcp` |
| | 哥伦比亚 | `colombian-law` | `@ansvar/colombian-law-mcp` |
| | 秘鲁 | `peruvian-law` | `@ansvar/peruvian-law-mcp` |
| **俄罗斯** | 俄罗斯 | `russian-law` | `@ansvar/russian-law-mcp` |

## 安装后的标准话术

写入 mcp.json 后，立刻对用户说：

> 已帮你把所有配置写入 `mcp.json`。现在请打开 WorkBuddy 右上角的 **连接器管理** 页面，找到刚添加的 MCP（名称里带 `law`、`regulation` 或 `compliance` 字样），逐个点击 **「Trust」**。点完就能直接用了，不需要其他任何操作。

## 查询时的匹配逻辑

用户问具体法律问题后：
1. 解析目标国家/法域
2. 按优先级匹配 MCP：
   - 具体国家 → Ansvar 国别库（如 `german-law`）
   - 台湾法规 → 见下方「台湾法数据源」专节：第三方初查 + 官方离线核验，**官方为准**
   - 欧盟法规 → `eu-regulations`
   - 美国法规 → `us-regulations`
   - 美国判例 → `courtlistener`
   - 安全框架对照 → `security-controls`
   - 中国大陆法规/案例 → `yuandian-mcp-server`（元典 npx，法条语义检索 + 案例全文）或 `wk-mcp-law`（威科先行）
   - 未知法域 → `legal-data-hunter`
3. 已安装 → 直接调用查询。未安装 → 先写配置，再查询。

## 需要 API Key 的情况

| 情况 | 处理方式 |
|------|---------|
| CourtListener 远程连不上 | 让用户去 [courtlistener.com/api](https://www.courtlistener.com/api/) 免费注册拿 Token，你帮填入 `env.COURTLISTENER_API_TOKEN`，切换为 `type: stdio` 本地版 |
| open-legal-compliance（进阶可选） | 这是 GitHub 源码项目，装它本身就需 GovInfo / CourtListener 等 Key；去 [api.govinfo.gov](https://api.govinfo.gov/) 免费注册填 `env.GOVINFO_API_KEY` |

**注意：核心 6 件套都无需 API Key。进阶可选的 open-legal-compliance、wk-mcp-law 从装的那一刻就要 Key，不是"连不上才申请"。**

## 报错自诊（翻译成人话 — 来自几十次踩坑）

用户在连接器页面看到的报错都是英文，你帮翻译：

| 用户看到的 | 真实含义 | 解法 |
|-----------|---------|------|
| `streamableHttp connect failed: fetch failed` | 远程服务器挂了（Vercel 免费端点通病） | 切成本地 npx 版，不要用远程 URL |
| `SSE error: Invalid content type` | 同上，远程端点格式不兼容 | 同上 |
| `MCP error -32000: Connection closed` | 本地 MCP 启动失败 | 分情况：① 检查 npx/node 是否已装 ② 可能是 SDK 版本冲突（如 mcp 2.0 不兼容旧包，降级到 mcp<2） ③ 检查 env 里 API Key 是否填了 |
| `Client network socket disconnected before secure TLS connection` | 网络到不了目标服务器 | 确认没被墙；如果反反复复出现，就此放弃远程方案 |
| `npx: command not found` | 没装 Node.js | 去 nodejs.org 下载安装 |
| `pipx: command not found` | 没装 pipx | `pip3 install pipx` |
| `HTTP Error 400: Bad Request` | API 端点格式不对 | 换 API 版本：CourtListener 用 v3 search 端点而非 v4 opinions |

## 降级策略：MCP 不可用时的三条后路

当 MCP 全部/部分挂掉时，按顺序降级：

| 优先级 | 方案 | 适用场景 |
|--------|------|---------|
| 1 | **切本地 npx 版** | 远程 URL 挂了 → 改成 `npx -y @ansvar/xxx` |
| 2 | **WebSearch 兜底** | MCP 全部不可用 → 调用 WebSearch 工具直接搜，标注"未通过 MCP 验证，仅供参考" |
| 3 | **输出但明示不可靠** | 所有 MCP + 离线 JSON 均不可用 → 基于已有知识回答，但显著标注「⚠️ 查不到可靠来源，未经独立数据源验证，请自行核实」 |

**核心原则：宁可标注"查不到可靠来源"，也不假装已验证。可以输出基于知识的回答，但必须显著提醒用户未经验证。**

## 台湾法数据源（官方站被墙的应对，官方为准）

**背景**：台湾官方站（`law.moj.gov.tw` 全国法规库、`judgment.judicial.gov.tw` 裁判书、`cons.judicial.gov.tw` 宪法法庭）在大陆网络下被墙（实测 HTTP 000），实时直连不可行。

**核心原则**：第三方库（如 `lawplayer.com` 法律人）虽能连、覆盖全，但**非官方、可能有错漏，只能作「初查定位」，绝不能作唯一依据**。凡输出台湾法条/解释，必须用官方数据核验。

**官方数据的两种可用形态**（官方站被墙后的替代）：
1. **官方离线缓存**（首选核验源，`source_url` 字段指向官方站）：
   - `references/tw-law-data/law_B0000001.json` — 民法全文 1439 条（2021-01-20 版）
   - `references/tw-law-data/law_N0030001.json` — 劳基法全文 98 条（2024-07-31 版）
   - `references/tw-law-data/interpretation_list.json` — 大法官解释索引 813 条
   - 本机 `mcp-taiwan-legal-db/mcp_server/data/` — 释字全文 813 笔 + 宪判字 55 笔（离线）
2. **WebSearch 官方转载**（离线覆盖不到的法规）：立法院公报、官方 PDF 的转载

**查询流程（双源核验）**：
1. 初查定位：WebSearch `site:lawplayer.com 关键词` 或 WebFetch 抓条文页，快速找到目标条文
2. 官方核验：用官方离线缓存逐字比对条文号 + 原文；离线无此法规时用 WebSearch 找官方转载核对
3. 双源一致 → 输出并标「✅ 官方核验」；仅 lawplayer 单源 → 明确标「⚠️ 仅第三方源，未经官方核验」；两者不一致 → 以官方为准并如实告知分歧

## 双源交叉验证（硬性要求，不可跳过）

**所有输出给用户的法条、判例，必须经过至少两个独立数据源交叉验证。** 境外法条一旦出错，后果严重——这是本 Skill 的铁律。

### 验证顺序（按优先级）

| 优先级 | 验证方式 | 适用场景 |
|--------|---------|---------|
| 1 | **双 MCP 交叉** | 两个不同 MCP 数据库都查到同一条文且内容一致 → 标记 ✅ 双库验证 |
| 2 | **MCP + WebSearch** | 只有单个 MCP 可用时 → 用 WebSearch 搜官方来源（政府网站、法院官网、律所数据库）核对 |
| 3 | **双 WebSearch** | MCP 全不可用时 → 至少两个独立来源（如 ABA 期刊 + 律所文章）一致才可输出 |

### 每条输出的标准格式

```
法规名称 §条款号 + 原文摘要
✓ 来源 A: [MCP 名称 / 网站名 + 链接]（2026-08-06 查询）
✓ 来源 B: [MCP 名称 / 网站名 + 链接]（2026-08-06 查询）
```

### 判定规则

- **双源一致** → 正常输出，标注两个来源
- **双源不一致** → 立即停下来排查：重新查询、检查版本/修订日期，仍不一致就**如实告知用户存在分歧**，两个版本都列出，不擅自选一个
- **只有一个来源** → 明确标注「⚠️ 仅单源验证，建议复核」，绝不伪装成已确认
- **查不到可靠来源** → **仍然输出**（给出已有信息或分析），但**必须**在开头和结尾显著标注：「⚠️ 查不到可靠来源，以下内容未经任何独立数据源验证，仅供参考，请务必自行核实」。绝不伪装成已确认，也不因为查不到就完全不回应

### 验证重点

- 法条**条款号**是否对得上
- **修订日期**是否最新（旧版本法条可能已被修改/废止）
- **判例案号**（如 41 N.Y.2d 420）是否真实存在
- **引文原文**与数据库返回是否逐字一致

### 缓存写入时同步验证状态

写入 `legal-cache.md` 时，把验证状态一起记进去（✅ 双库 / ⚠️ 单源 / ❌ 待复核），下次命中缓存时延续该状态。

## Trust 跟踪提醒

写入 mcp.json 后，用户需要逐个 Trust。你没办法代劳，但可以在后续对话中主动检查：

- 用户下次问法律问题时，先确认对应的 MCP 是否已 Trust（如果连接器列表里显示 disconnected 说明没点）
- 如果发现用户装了但没 Trust，提醒：「上次装的 XX 法律数据库还没启用，去连接器页面点一下 Trust 就能查了」

## 输出规范

- 每条法规引用标注来源 MCP 数据库名称
- 法条原文 + 简要中文解释
- 多法域对比用表格呈现
- 风险分级：🔴高 / 🟡中 / 🟢低
- 不确定的内容诚实告知，建议咨询当地持牌律师

## 法条缓存：查一次，永久记住

**每次 MCP 查询成功后，必须将结果写入知识库缓存**——下次同样的问题直接调缓存，不再重复调 MCP。

### 查询前：先搜缓存

在调用 MCP 之前，用 Grep 搜索 `references/legal-cache.md`，关键词用用户的原始提问。如果命中 → 直接取缓存结果，标注「来源：本地缓存（原始查询日期 YYYY-MM-DD）」，跳过 MCP 调用。

### 查询后：写入缓存

MCP 查询完成后，按以下格式**追加**到 `references/legal-cache.md` 的「已缓存记录」章节末尾：

```markdown
### {日期} | {法域} | {主题}
- **来源 MCP**: {MCP 名称}
- **原始查询**: {用户原话}
- **法规/判例**:
  - **{法规名称}** §{条款号} — {原文摘要}
  - ...
- **关键结论**: {一句话总结}
---
```

### 维护规则

- 用 `grep -i "关键词" references/legal-cache.md` 快速定位历史记录
- 同一法域+同一主题重复出现时，以最近一次更新旧记录
- 缓存文件超过 300 行时，提醒用户「本地已积累大量法条记录，是否需要清理？」

## 经验教训与最佳实践（2026-08-06 全天调试总结）

以下每一条都来自真实踩坑，不可跳过。

### 数据源

- **Ansvar 国别 MCP 最稳**：本地 npx 运行、SQLite 离线、零 API Key、秒级响应。优先推荐。
- **Vercel 远程端点不可靠**：国内网络下频繁 TLS 握手失败、连接超时。一旦遇到 → 立刻切本地 npx 版。
- **npm 包名可能不存在**：`@ansvar/security-controls-mcp` 在 npm 上搜不到，真实安装方式是 `pipx install security-controls-mcp`。别盲信包名。
- **国别包名用「国家名词」而非形容词**：日本 `japan`、韩国 `south-korea`、印度 `india`、巴西 `brazil`——2026-08-25 教训，这 4 个曾写成 japanese/korean/indian/brazilian 导致 npm 404。
- **远程 URL 会过期，本地 npx/pip 更耐久**：legaldatahunter 已改为需认证、元典远程 URL 已挂、台湾法 Vercel 端点已挂——现已全部切换为本地版（`yuandian-mcp-server` npx / `mcp-taiwan-legal-db` pip）。数据源清单标注「最后验证日期」，失效时先怀疑 URL/包名，再怀疑下架。
- **MCP SDK 版本冲突魔鬼**：`mcp 2.0` 砍了 `list_tools()` API，`security-controls-mcp v1.1.0` 不兼容。修复：`pipx runpip install "mcp<2"`。
- **API 端点格式不唯一**：CourtListener v4 不吃标准 query，v3 `search?type=o&q=` 才认。调新 API 先试一个简单查询验证。
- **没有 MCP 也能查**：泰国法无 MCP → WebSearch 四条来源交叉验证 → 同样可靠。不要因为没有 MCP 就放弃。

### 安装策略

- **默认问国家，不要默认全装**。6 个核心 MCP 全部装下来 2-3 分钟，每个还要手动 Trust。用哪个装哪个，不够再加。
- **mcp.json 的 command 在用户系统 PATH 执行**，不是 WorkBuddy 沙箱。环境预检必须查 `which node` / `which python3` / `which pipx`，且检查结果只能看用户系统的。
- **Trust 按钮是单点瓶颈**：每次写入 mcp.json 后必须提醒「去连接器页面点 Trust」。漏了对应用户查什么都查不到。

### 内容质量

- **每条法条标注具体来源页面，不给网站首页**。例：「[thailandlawonline.com — CONDITIONS OF MARRIAGE](https://thailandlawonline.com/thai-family-and-marriage-law/family-law-sections-conditions-of-marriage)」而不是「[thailandlawonline.com](https://www.thailandlawonline.com)」。
- **双源交叉验证不可跳过**，但允许 WebSearch 验证 → 一个 MCP 无第二个 MCP 时，用 WebSearch 官方来源交叉核对。
- **查不到可靠来源也要输出，但显著标注**：「⚠️ 查不到可靠来源，未经独立数据源验证，请自行核实」。
- **缓存不代表永远正确**：法条变更后旧缓存仍在，命中时注意核查日期。

<!-- AUTHOR_SIGNATURE: 法律科技实务工具 · 维护者陆凌燕律师（北京德恒·无锡）· 关注公众号「鹿鸣于野 UMU」获取更多内容 -->

<!-- © 2024-2026 陆凌燕（北京德恒（无锡）律师事务所）. Licensed under MIT. -->

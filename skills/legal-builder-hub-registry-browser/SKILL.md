---
name: legal-builder-hub-registry-browser
description: 检索监视的 registry：**先法律元力**（REST API：工具包 + 站内 skill），静态 yaml 兜底，再 GitHub。 展示描述、version/sha256 与来源标签；可预览 SKILL.md 或 toolkit 详情后再安装。 用于「浏览」「搜 skill」「有什么适合 XX 的」或添加监视 registry。对用户输出一律简体中文。
metadata:
  displayName: 技能库检索
  argument-hint: '[检索词]'
---

# legal-builder-hub-registry-browser

> **对用户输出一律简体中文**（skill id、API 路径、URL 可保留）。

1. 读取 `$LEGAL_AGENT_PROFILE_HOME/legal-builder-hub/profile.md` → 监视的 registry 列表。
2. 按下列流程检索。
3. 在各 registry 中匹配；展示描述与来源。
4. 可对任一结果提供完整 SKILL.md 预览。

---

## 目的

在已监视的 registry 中搜索 skill、预览内容、再决定是否安装。

## 加载上下文

`profile.md` → `references/registries.yaml` 中的 priority 顺序。

## 流程

### 步骤 0：法律元力（第一优先）

读取 `profile.md` → `## yuanli` → `base_url`（记为 `{BASE}`；未配置时默认 `https://yuanli.ailaw.cn`）。契约见 `references/yuanli-api.md`。

**有 `{BASE}` 时（WebFetch / curl）：**

1. **工具包：** `GET {BASE}/api/toolkits?search=<query>&page_size=20`（无 query 则列首页或配合 `GET .../categories`）。
2. **站内 skill：** `GET {BASE}/api/skills?search=<query>&page_size=20`。
3. **详情：** `GET {BASE}/api/toolkits/{toolkit_id}` 或 `GET {BASE}/api/skills/{skill_id}`（含 `content` 摘要、可选 `trust_info`）。
4. **每条标注（对用户用中文说明）：** 来源：法律元力 · 类型：工具包或单 skill · 标识 · 版本 · 发布时间/更新时间；catalog 可用时附 `sha256`。

**无 `{BASE}` 或 API 失败：** 回退 `references/yuanli-toolkits.yaml`，按 `name` / `tags` / `toolkit_id` 过滤。

**用户操作：** 预览详情 → 安装请用 `legal-builder-hub-skill-installer <toolkit_id|skill_id>`。

### 步骤 1：拉取其他 registry 索引（GitHub 等）

对每个**非**法律元力的监视 registry：

- GitHub：拉取 `skills/` 目录与各 `SKILL.md` frontmatter。
- 其他市场：拉取索引。

监视列表以 `plugin/references/registries.yaml` 为准。GitHub 索引可缓存到 `registry-cache.json`，超过 7 天或用户要求时刷新。

### 步骤 2：检索

按关键词匹配 skill 名称与描述；规模较小，简单关键词匹配即可。

若 registry 按分类组织，可同时支持按类浏览。

### 步骤 3：展示匹配结果（对用户使用下列模板，全文中文）

```markdown
## 检索：「[关键词]」

**在 [M] 个来源中共找到 [N] 个 skill：**

### [skill 名称]
**来源：** [registry 名称]
**描述：** [来自 frontmatter 的摘要]
[查看完整 SKILL.md] [安装]

### [skill 名称]
[...]
```

用户说「查看完整 SKILL.md」时，拉取并展示全文。

### 步骤 4：预览

展示完整 SKILL.md，供用户安装前自行阅读。

### 步骤 5：添加监视 registry

用户提供不在监视列表中的 URL 时：

1. 拉取并校验是否为 skill 仓库（含 `skills/` 或 `.claude-plugin/`）
2. 展示其中内容
3. 用户确认后写入 `profile.md`「监视的 registry」段，必要时同步用户目录下的 `references/registries.yaml`

## 默认 registry

- **lpm-skills** — 14 个法律项目管理 skill，与具体业务线无关，可作入门浏览。

## 本 skill 不做什么

- **不安装** — 仅浏览；安装由 `legal-builder-hub-skill-installer` 完成。
- **不评分** — 展示 SKILL.md，由用户判断。
- **不搜全网** — 仅已监视的 registry。

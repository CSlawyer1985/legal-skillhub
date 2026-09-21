---
name: legal-builder-hub-auto-updater
description: 检查已安装 skill 的更新：GitHub 用 commit SHA + diff；法律元力 工具包用 catalog 的 sha256/etag， 站内 skill 用详情 version/updated；均需显式批准。见 references/yuanli-api.md。
metadata:
  displayName: 技能更新检查
  argument-hint: '[--apply 应用指定更新 | --rollback 回滚 | 默认仅通知]'
---

# legal-builder-hub-auto-updater

> **对用户输出一律简体中文。** skills-qa 结论档：**可安装 / 有顾虑 / 重大顾虑 / 拒绝安装**。

1. 读取 `$LEGAL_AGENT_PROFILE_HOME/legal-builder-hub/profile.md` → 已安装列表、更新偏好。
2. 读取 `install-log.yaml` 中每条记录的 `source`、`sha256`/`etag`/`version`。
3. 按来源检查更新（见下）。
4. **禁止**未阅读 diff 且未获用户明确批准即覆盖文件。

---

## 目的

社区 skill 会演进。本 skill 发现变更、展示 diff，**仅在用户明确批准后**应用。无「静默自动升级」模式。

## 信任姿态

已安装 skill 在特权法律环境中运行。上游可被篡改、易主或改变行为。**设计原则：每次更新都必须有人读过 diff 并输入批准。**

## 流程

### Step 1：检查每条已安装记录

**GitHub 来源：**

- 拉取 registry 上**当前 commit SHA**（不用 tag/branch head——可被改写）
- 与 install-log 中钉扎 SHA 对比；不同 → 有更新

**法律元力 工具包（`source: yuanli`, `type: toolkit`）：** `{BASE}` 默认 `https://yuanli.ailaw.cn`。

1. `GET {BASE}/api/toolkits/catalog`，找 `toolkits[].id`
2. 对比 install-log 的 `sha256` 或 `etag`；变化 → 有更新
3. 展示 `version`、`size_bytes`、`published_at`；**不**自动下载
4. 用户批准后：`GET {BASE}/api/toolkits/{id}/download`（可用 `If-None-Match`）→ 解压 → `python3 install.py`（installer 自动检测平台，必要时加 `--target <path>`）
5. 无 API：对比 `yuanli-toolkits.yaml` 或提示用户下载新 zip

**法律元力 站内 skill（`type: skill`）：**

- `GET {BASE}/api/skills/{skill_id}`，对比 `version` / `updated`
- 有变 → `GET .../download` 替换目录（见 yuanli-api.md §2.3）

### Step 2：Diff 与信任检查（GitHub / 可 diff 的更新）

展示完整 unified diff，含：

- `SKILL.md`
- `hooks/hooks.json`（**重点**：可执行任意命令）
- `.mcp.json`（**重点**：MCP 凭你的环境运行）
- `allowed-tools` / `tools` frontmatter 扩大
- 新增外连 URL、skill 目录外写路径、`description` 目的变更

### Step 2.5：对新版本重跑 skills-qa（GlassWorm 门）

v1.0 干净、v1.1 投毒是已知模式。**应用前**对**新版本**跑完整 `legal-builder-hub-skills-qa`：

1. **回归即默认拒绝：** 新版本在 Step 1.5 任一类出现旧版没有的 finding → 默认拒绝更新
2. **安全审查维度变更须人工：** hooks / MCP / 工具权限 / 外连 / 目录外写 / description 变更 → 强制人工批准，不能因扫描「干净」跳过
3. **只读子 agent 扫描**（可用时）：Read + WebFetch + Glob，无 Write/Bash
4. **拒绝安装**（窃密、改环境等）→ 不提供「仍要应用」；仅 `--rollback` 或卸载

### Step 2.6：时效（freshness）

从 **install-log**（非 live frontmatter——防篡改）读 `last_verified`、`freshness_window`、`freshness_category`。

有效窗口 = `min(作者 window, profile ## Freshness reminders 中用户阈值)`。

- 窗口已过且无新 commit → 提示用户自行核验 `verified_against` 或禁用
- 窗口已过且有新 commit → 仍须 diff + QA；若新版本 `last_verified` 未推进 → 显著标注「本次提交未重新核验捆绑法条」

### Step 3：按偏好处理

| 偏好 | 行为 |
|------|------|
| notify（默认） | 展示 diff +「是否应用？[y/n]」 |
| manual | 仅列出有更新的项；用户自行 `--apply <skill>` |

### Step 4：应用（用户批准后）

- 备份旧版到 `$LEGAL_AGENT_PROFILE_HOME/legal-builder-hub/backups/<skill>-<old-sha>/`
- 覆盖文件；更新 profile 与 install-log（新 SHA / sha256 / version）
- 法律元力 包：按 skill-installer 的 zip 流程

## 回滚

`legal-builder-hub-auto-updater --rollback <skill>` 从 backup 恢复。

## 禁止

- 自动应用更新（ever）
- 更新非 hub install-log 记录的 skill
- 信任 tag/分支；GitHub 仅钉 SHA

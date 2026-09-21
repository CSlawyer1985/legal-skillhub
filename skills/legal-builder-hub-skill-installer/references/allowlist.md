# Allowlist 配置说明

安装器在写入任何文件**之前**读取：

```
$LEGAL_AGENT_PROFILE_HOME/legal-builder-hub/allowlist.yaml
```

默认模板见 `plugin/references/allowlist-default.yaml`（含 yuanli-cn + 常用 GitHub registry）。

allowlist 是**结构性门禁**：不依赖模型对第三方 SKILL.md 的解读；与 skills-qa 启发式扫描、人工阅读 raw 原文配合使用。

## 字段说明

```yaml
mode: 严格模式    # 宽松模式 | 严格模式

registries:
  - yuanli-cn
  - https://github.com/legalopsconsulting/lpm-skills

publishers:
  - 华宇元典
  - legalopsconsulting
  - lawvable

connectors: []   # 严格模式 下为空则拒绝声明任意 MCP 的 skill

licenses:
  - MIT
  - Apache-2.0
  - BSD-2-Clause
  - BSD-3-Clause
  - ISC
  - CC0-1.0
```

## 许可证与来源信任分离

- `registries` / `publishers`：回答「来源是否可信」
- `licenses`：回答「该 skill 声明的许可证义务是否可接受」

许可证字段按 **SPDX 标识符严格匹配** 提取；无法解析的原文仅作 finding 展示，**不得**由安装器自行推断为允许。

部署场景（冷启动写入）决定默认 `licenses:` 种子：

| 场景 | 典型许可证 |
|------|------------|
| 个人自用 | MIT、Apache-2.0、BSD-*、ISC、CC0-1.0 |
| 机构内部 | 上表 + LGPL-*、MPL-2.0 |
| 嵌入产品对外分发 | 不含 GPL/AGPL；未列明许可证须法务会签 |

## 模式

**宽松模式：** 不在名单上的来源/许可证 → 显著警告，用户明确接受后继续。

**严格模式：** 不在名单上 → **拒绝 fetch**，说明需把 registry/publisher/connector 加入 allowlist。

## 文件缺失时

不存在 `allowlist.yaml` 时，安装器按 **宽松模式 + 空名单** 处理：每次安装均警告，**不得**静默「全部允许」。

## 法律元力（yuanli）

`yuanli-cn` 视为 registry 名；发布者「华宇元典」须在 `publishers` 或 严格模式 的 `registries` 中。下载走 `references/yuanli-api.md`，不绕过 allowlist。

## 局限

allowlist 只管**允许从哪些源拉取**；可信发布者的恶意 skill 仍须 QA + 人工 yes。与 `legal-builder-hub-skills-qa` 并用。

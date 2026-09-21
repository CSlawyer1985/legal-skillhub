---
name: legal-builder-hub-disable
description: 禁用通过 hub 安装的社区 skill（不删文件）：重命名 SKILL.md 与 hooks，停止触发。 用于「禁用 [skill]」或重新启用。受保护 cn-localized 正式 skill 与 hub 自身 skill 不可禁用。
metadata:
  displayName: 技能禁用管理
  argument-hint: '[skill 名称]'
---

# legal-builder-hub-disable

调用 `legal-builder-hub-skill-manager` 的 disable 流程。

## 作用

- `SKILL.md` → `SKILL.md.disabled`（不再被发现为活跃 skill）
- 若有 `hooks/hooks.json` → `hooks.json.disabled`
- 记录写入 `install-log.yaml`（action: disable）

## 安全规则

1. **仅** hub 安装且 install-log 有记录的社区 skill（同 uninstall 校验）
2. **禁止** cn-localized 正式 skillpack 与 `legal-builder-hub-*` 自身
3. **确认后操作** — 列出将重命名的路径，须 `yes`

再次对同一 skill 调用可**重新启用**（skill-manager 识别 `.disabled` 并还原）。

详细步骤见 `legal-builder-hub-skill-manager`（user-invocable: false）。

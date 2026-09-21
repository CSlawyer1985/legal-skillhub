---
name: legal-builder-hub-uninstall
description: 卸载通过 hub 安装的社区 skill（确认后删除文件）。拒绝操作 cn-localized 正式 skill 与 hub 自身。 用于「卸载 [skill]」；临时停用请用 disable。
metadata:
  displayName: 技能卸载管理
  argument-hint: '[skill 名称]'
---

# legal-builder-hub-uninstall

**仅卸载** install-log 中有 `install` 记录的社区 skill。

## 流程（委托 skill-manager）

1. 读 `install-log.yaml` — 无记录或已 uninstall → 说明并停止
2. 校验非受保护 skill（非 cn-localized 包内正式 skill、非 hub 自身）
3. **列出将删除的路径**，须用户 `yes`
4. 删除文件；`install-log.yaml` 追加 `action: uninstall`
5. 更新 profile 已安装表

临时停用请用 `legal-builder-hub-disable`（保留文件）。

详细步骤见 `legal-builder-hub-skill-manager`。

---
name: legal-builder-hub-skill-manager
description: '参考：hub 安装的社区 skill 的卸载/禁用/启用详细流程。默认拒绝操作 cn-localized 正式 skillpack 与 hub 自身；删除前确认并写日志。由 uninstall / disable 加载。 user-invocable: false。'
metadata:
  displayName: 技能运维管理
  user-invocable: false
---

# legal-builder-hub-skill-manager（参考实现）

与 `skill-installer` 对称：安装须 yes；卸载/禁用亦须 yes。真相来源：`install-log.yaml`。

## 可操作范围

仅 **通过 hub 安装** 且 install-log 最近动作为 `install` 或 `enable` 的社区 skill。

## 受保护（禁止卸载/禁用）

- `legal-skillpack-*` 包内全部正式 skill
- `legal-builder-hub-*`
- 未记入 install-log 的文件

## 卸载 workflow

1. 读 install-log — 无记录或已 uninstall → 停止
2. 解析路径 — 须在社区安装目录，非受保护包
3. 列出将删除路径 — 须 `yes`
4. 删除；install-log 记 `uninstall`；更新 profile

## 禁用 workflow

1. 同 Step 1 校验
2. `SKILL.md` → `SKILL.md.disabled`；hooks 同理
3. install-log 记 `disable`；再次调用可 enable

## 记录

所有动作追加 `install-log.yaml`；更新 profile 已安装表。

## 禁止

- 操作受保护 cn skillpack / hub 自身
- 无 yes 即改文件名或删除

（逐步英文细节见上游；执行时以本中文摘要 + install-log 校验为准。）

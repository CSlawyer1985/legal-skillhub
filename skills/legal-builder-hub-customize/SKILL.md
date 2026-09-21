---
name: legal-builder-hub-customize
description: 单点修改 hub 管理配置（入门包、监视 registry、更新偏好、allowlist、QA 严格度）， 无需完整冷启动。用于「改 allowlist」「加 registry」「更新 profile」。
metadata:
  displayName: 中枢配置调整
  argument-hint: '[section name, or describe what you want to change]'
---

# legal-builder-hub-customize

> **对用户输出一律简体中文。**

单点修改 hub 配置，无需完整冷启动。可改：法律元力 `base_url`、监视 registry、更新偏好、allowlist、推荐用实践领域。

## 流程

1. **读取配置。** 读取 `$LEGAL_AGENT_PROFILE_HOME/legal-builder-hub/profile.md`（及上一级 `company-profile.md`）。若配置不存在或仍含 `[PLACEHOLDER]`，对用户说：

   > 你尚未完成初始配置。请先运行 ``legal-builder-hub-cold-start-interview`` — customize 用于在已有配置上做单项调整。

2. **展示可改项**（每项一行当前值）：

   - **公司画像**（`company-profile.md`，跨集群）
   - **hub profile** — 实践领域、已安装列表、监视 registry
   - **法律元力（yuanli）** — `base_url`
   - **allowlist.yaml** — mode、registries、publishers、licenses
   - **更新偏好** — 通知 / 仅手动 / 推送到办公平台（飞书 / 企业微信 / 钉钉，海外可选 Slack）
   - **Freshness reminders** — 各品类最长可信期限
   - **集成** — 办公通讯平台（飞书 / 企业微信 / 钉钉 / Slack）等

3. **问用户要改什么**（一次改一项，不重演完整冷启动）。

4. **改前确认**：展示旧值 → 新值 → 下游影响 → 用户确认 → 写入文件。

   示例：新增 GitHub registry → 说明 `registry-browser` 将一并检索；改 `base_url` → 说明 API 与静态 yaml 优先级。

5. **公司级字段** 写入 `company-profile.md`，并提示影响哪些 business cluster。

6. **结束**：「已保存；可用 ``legal-builder-hub-customize`` 继续改。」

## 护栏

- **不删整节**；「删除」监视 registry → 标 `[Paused]`
- **矛盾检测**：如 profile 写商事但只装诉讼包 → 提示
- **不鼓励关闭 QA**；降低严格度建议用 middle 档
- **allowlist 变更** 须写入 `allowlist.yaml`，不只改 profile 摘要

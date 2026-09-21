---
name: legal-builder-hub-related-skills-surfacer
description: 根据近期任务推荐相关 skill；优先 法律元力（GET /api/skills、toolkits），再 GitHub registry。 非侵入式提及一次。用于「有没有 skill 能做这个」或 workflow handoff。
metadata:
  displayName: 相关技能推荐
---

# legal-builder-hub-related-skills-surfacer

1. 读取 `$LEGAL_AGENT_PROFILE_HOME/legal-builder-hub/profile.md` → 管理配置、已安装列表、`## yuanli` → `base_url`。
2. 按下列 workflow 匹配；**不强匹配则沉默**。
3. 结束时可选附 `plugin/shared/disclaimer-cn.md` 决策树。

---

## 目的

社区可能已有你正要手搓的能力。本 skill 在任务**结束后**简短提示一次，不打扰进行中流程。

## 检索顺序

### 1. 法律元力（有 `base_url` 时，默认 `https://yuanli.ailaw.cn`）

契约：`references/yuanli-api.md`。

- `GET {BASE}/api/skills?search=<任务关键词>&page_size=10`
- `GET {BASE}/api/toolkits?search=<关键词>`（整包场景）
- 过滤：已在 install-log 中且未卸载的 id 不再推荐
- 标注：`source: yuanli` · `type: skill|toolkit`

### 2. GitHub 监视 registry

读取 profile 监视列表 + 本地 `registry-cache.json`（若有）。标注 `source: github`。

### 3. 匹配规则

- 关键词与 description 重叠
- 符合 profile 实践领域（商事律师不推荐纯诉讼包，除非强相关）
- **阈值高：** 弱相关不输出

## 输出（强匹配时）

> 💡 社区有相关 skill：**[name]**（[法律元力 | github]）— [一行描述]。安装：`legal-builder-hub-skill-installer [id]`。

无强匹配：**不输出**（不要说「没找到」）。

## 频率

同一 skill 只提示一次；用户曾忽略则记入 `$LEGAL_AGENT_PROFILE_HOME/legal-builder-hub/surfaced-dismissals.json`（可选文件）。

## 用户控制

profile 中「新 skill 通知」偏好：全部 / 仅匹配 profile（默认）/ 关闭。

## 禁止

- 不安装、不中断进行中任务、不重复纠缠同一 skill。

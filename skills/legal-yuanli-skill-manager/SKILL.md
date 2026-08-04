---
name: legal-yuanli-skill-manager
description: 面向法律问题场景，在法律元力平台检索并推荐最匹配的法律领域 Skill。适用于用户想查找法律 Skill、拆解法律问题、选择合适法律能力时；也支持本地 Skill 盘点、安装、删除、更新与自动化更新检查。
disable-model-invocation: false
---

# 法律元力 Skill 管家

此技能用于在法律元力平台检索法律领域 Skill，并基于用户法律问题推荐可用技能；同时管理本地已安装 Skill 的全生命周期。

## 适用范围

- 用户提出法律问题时，先定位可用的法律 Skill
- 用户明确要“找某类法律 Skill”时，返回匹配结果与推荐理由
- 查看本地已管理 Skill 清单（`list`）
- 盘点本地智能体环境中已有的元力 Skill（`scan`）
- 用户确认后，执行安装、删除、更新 Skill 操作
- 批量检查更新，并引导用户配置定时检测更新机制

## 触发场景

- “帮我找一个可以做合同审查的 skill”
- “我在做劳动争议，应该用哪个法律 skill”
- “有没有能处理股权协议起草的法律能力”
- “先帮我找合适 skill，再安装”
- “我本地装了哪些法律 skill”
- “检查一下元力 skill 有没有更新”

## 兼容性说明

- 兼容任意智能体平台（如自建 Agent、工作流编排器、CLI Agent、IDE Agent、桌面助手等）
- 只要求具备以下任一能力：
  - 能执行命令行脚本，或
  - 能直接发起 HTTP 请求
- 该技能的核心是统一 API 协议 + 本地状态管理

## 默认域名

- 法律元力站点：`https://yuanli.ailaw.cn/`
- API 基础地址默认值：`https://yuanli.ailaw.cn`

## 环境变量配置

执行命令前，建议配置：

- `YUANLI_API_BASE_URL`：后台 API Base URL（默认 `https://yuanli.ailaw.cn`）
- `YUANLI_API_TOKEN`：可选，若后端鉴权开启则填写 Bearer Token
- `YUANLI_TIMEOUT_SECONDS`：请求超时秒数（可选，默认 `30`）
- `YUANLI_AGENT_SKILL_STATE_PATH`：本地安装状态文件路径（默认 `~/.yuanli/agent_skills.json`）
- `YUANLI_AGENT_SKILL_PACKAGE_DIR`：技能包下载目录（默认 `~/.yuanli/packages`）
- `YUANLI_AGENT_SKILLS_DIR`：智能体本地技能目录（默认 `~/.workbuddy/skills`，可按平台覆盖）

## 命令接口（CLI 适配层）

在任意支持 Python 的环境执行：

```bash
python "legal-yuanli-skill-manager/scripts/yuanli_skill_api.py" <subcommand> [args]
```

子命令：

1. `search`
   - `--query <text>`：关键词模糊检索
   - `--category <text>`：分类过滤（可选）
   - `--limit <n>`：返回数量，默认 `20`

2. `list`
   - `--detail`：补充 API 详情（分类、作者、下载量）
   - `--format json|text`：输出格式，默认 `json`

3. `scan`
   - `--register`：将本地技能目录中未纳入管理的元力 Skill 注册到状态文件
   - `--register-all`：批量注册所有未管理 Skill
   - 识别逻辑：优先读 `yuanli_skill_id`；若无该字段，则用 SKILL.md 中的技能名称在元力平台检索并比对，判断是否来自元力
   - `--register` 时，对通过名称匹配识别的 Skill 会回写 `yuanli_skill_id` 到 SKILL.md
  - `--register` 会将远端当前版本写入状态文件（优先读 SKILL.md `version`，否则请求 `GET /api/skills/{id}`），避免 `check-updates` 误报

4. `status`
   - 一键输出远端 Skill 总数、本地已管理数量、本地已落地数量、可更新列表

5. `check-updates`
   - `--auto-update`：对可更新 Skill 自动执行 update
   - `--download-package`：自动更新时同步下载 zip
   - `--accept-license`：自动下载更新前确认接受 license
   - `--format json|text`：输出格式，默认 `json`

6. `license`
   - `--skill-id <id>`：查看 Skill 的 license 信息（来自 `GET /api/skills/{id}` 的 `license` 字段）
   - `--format json|text`：输出格式，默认 `json`

7. `install`
   - `--skill-id <id>`：法律元力 Skill ID
   - `--download-package`：可选，下载 zip 技能包
   - `--register-to-workbuddy`：可选，解压并落地到本地技能目录（兼容旧参数名）
   - `--accept-license`：安装者确认 license 后附加；**下载/落地前必填**

8. `remove`
   - `--skill-id <id>`：要删除的已安装 Skill ID

9. `update`
   - `--skill-id <id>`：要更新的已安装 Skill ID
   - `--download-package`：可选，更新时同步下载 zip 并刷新本地技能目录
   - `--force`：可选，强制覆盖更新
   - `--accept-license`：下载更新包前必填（license 变更时需重新确认）

## 标准执行流程（面向所有智能体）

1. 识别用户意图，优先判断是否为“法律问题找 Skill”
2. 如果用户描述的是法律问题，先抽取检索要素：
   - 法律领域（合同、劳动、争议解决、合规等）
   - 任务类型（检索、审查、起草、分析）
   - 场景关键词（行业、主体、争议类型）
3. 调用法律元力真实公开接口进行检索：
   - `GET /api/skills`
   - `GET /api/skills/{skill_id}`
   - `GET /api/skills/{skill_id}/download`（可选）
4. 输出推荐结果（建议 3-5 个）：
   - `skillId`、名称、版本、分类
   - 匹配理由（为何适合当前法律问题）
   - 使用建议（先试用哪个，何时安装）
   - 若用户准备安装，先调用 `GET /api/skills/{skill_id}` 获取 `license` 并向用户说明
4.5. **下载前 license 确认（强制）**：
   - 任何会触发下载的动作（`install --download-package`、`install --register-to-workbuddy`、`update --download-package`、`check-updates --auto-update --download-package`）前，必须先：
     1. 调用 `license --skill-id <id>`（或 `GET /api/skills/{id}`）读取 `license` 字段
     2. 向安装者明确展示 license 名称、SPDX、链接、版权说明
     3. 获得安装者明确同意后再继续，并在 CLI 中附加 `--accept-license`
   - 若安装者未确认，不得下载；仅可继续检索与推荐
5. 若用户明确执行管理动作，再进入对应子命令：
   - 查看清单 → `list`
   - 盘点本地技能目录 → `scan`
   - 健康检查 → `status`
   - 安装/删除/更新 → `install` / `remove` / `update`
6. 将安装状态写入本地状态文件，形成“当前智能体已安装技能清单”
6.5. 首次 `install` 或 `scan --register` 完成后，**主动引导用户设置定时检测更新机制**：
   - 提示用户："你的元力 Skill 已就绪。要不要我帮你设置一个每周自动检查更新的定时任务？有新版时会主动通知你。"
   - 引导时机：
     - ✅ 首次 install 或 scan --register 后 → 必须主动引导（强提醒）
     - ✅ `list` 发现未配置自动化且无 `auto_update_configured` → 轻提示一次
     - ❌ 用户已配置 `auto_update_configured: true` → 不再提示
   - 若用户同意，**使用当前智能体平台可用的定时/自动化能力**创建任务（不绑定某一平台）：
     1. 识别平台能力：cron、systemd timer、CI 定时流水线、平台内置 automation/schedule API、Agent 定时 prompt 等
     2. 统一任务目标：周期性执行
        ```bash
        python "<本技能脚本路径>/yuanli_skill_api.py" check-updates --format text
        ```
     3. 若用户希望自动更新（需明确授权），再使用：
        ```bash
        python "<本技能脚本路径>/yuanli_skill_api.py" check-updates --auto-update --download-package --format text
        ```
     4. 建议频率：每周一次（如每周一 09:00）
     5. 任务执行后要求：读取命令输出，用简洁表格汇总“已更新 / 无变化 / 失败项”
   - 配置完成后：
     - 执行 `python yuanli_skill_api.py status` 做一次确认
     - 将状态文件 `auto_update_configured` 设为 `true`
   - 若用户拒绝：保持 `auto_update_configured: false`，不反复打扰；每次新 install 后可再次询问是否扩大检查范围
7. 输出结构化结果：
   - 成功/失败
   - 关键标识（`skillId`、`version`、`stateFile`）
   - 后端返回消息
8. 错误处理：
   - 返回 HTTP 状态码与错误信息
   - 提示检查 Token、Base URL、网络连通性

## 备注

- 本技能为 API 协议层能力，可复用于多种智能体产品形态。
- 当前后端未提供“远端智能体安装列表管理”专用 API，因此 `remove/update` 以本地状态文件为准管理。
- `install --register-to-workbuddy`（或平台等价落地流程）会在 SKILL.md frontmatter 注入 `yuanli_skill_id` 字段，便于 `scan` 识别来源。
- `scan` 在无 `yuanli_skill_id` 时会按 SKILL.md 技能名称检索元力平台并比对；`scan --register` 对名称匹配项也会回写 `yuanli_skill_id`。
- 下载任何 Skill 前必须完成 license 告知与确认；脚本会在未附加 `--accept-license` 时阻断下载。
- 详细 API 与状态文件字段说明见 [reference.md](reference.md)。

## 定时检测更新：通用智能体运行机制

定时检测更新应设计为**平台无关的后台任务**，不依赖当前对话上下文：

- **触发时机**：按约定周期执行（建议每周一 09:00）
- **执行内容**：统一调用 `check-updates` 子命令
- **结果处理**：将“可更新列表”通知用户；仅在用户授权时使用 `--auto-update`
- **状态共享**：`~/.yuanli/agent_skills.json` 作为全局状态文件，供不同智能体读取同一安装清单

平台落地示例（任选其一）：

| 平台类型 | 落地方式 |
|---------|---------|
| Linux 服务器 | `crontab` / `systemd timer` |
| CI/CD | GitHub Actions `schedule` / Jenkins 定时任务 |
| 桌面智能体 | 平台 automation/schedule API |
| IDE Agent | 任务调度插件 + CLI 脚本 |

无论使用哪种平台，任务核心命令保持一致，确保跨智能体可复用。

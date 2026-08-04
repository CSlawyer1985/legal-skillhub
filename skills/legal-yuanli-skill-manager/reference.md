# 法律元力 API 对齐说明（基于 `law-portal/backend`）

脚本当前对齐的真实公开接口如下：

- 搜索技能：`GET /api/skills`
- 技能详情：`GET /api/skills/{skill_id}`
- 技能包下载：`GET /api/skills/{skill_id}/download`

## 子命令与 API 对应关系

| 子命令 | 远端 API | 本地操作 |
|--------|---------|---------|
| `search` | `GET /api/skills` | 无 |
| `list` | `GET /api/skills/{id}`（`--detail` 时） | 读状态文件 |
| `scan` | 无 | 扫描本地技能目录 + 写状态文件 |
| `status` | `GET /api/skills` + 逐项详情 | 读状态文件 + 版本比对 |
| `check-updates` | 逐项 `GET /api/skills/{id}` | 读状态文件；`--auto-update` 时写回 |
| `license` | `GET /api/skills/{id}` | 提取并展示 `license` 字段 |
| `install` | 详情 + 可选下载 | 写状态文件；下载前需 `--accept-license` |
| `remove` | 无 | 从状态文件删除 |
| `update` | 详情 + 可选下载 | 更新状态文件；下载前需 `--accept-license` |

## License 字段说明

`GET /api/skills/{skill_id}` 返回的 `license` 字段用于安装前告知，脚本按以下优先级解析：

1. `license`（字符串或对象）
2. 回退 `trust_info.legal_metadata`（`license_name` / `license_spdx` / `license_url` / `copyright_notice`）

下载门禁规则：

- 触发 `/download` 前必须向安装者明确 license
- CLI 需附加 `--accept-license` 才会下载
- 若 license 指纹变更，需重新确认

状态文件会记录：

- `license`：最近一次确认的 license 信息
- `license_fingerprint`：license 指纹，用于检测变更
- `license_accepted_at`：安装者确认时间

## 关键说明

- 当前后端公开 API 中，没有“按用户智能体远端安装/卸载/更新 Skill”的专用端点。
- 因此脚本采用“远端技能数据 + 本地安装状态 + 本地技能目录”模式：
  - 远端负责检索、详情、下载
  - 本地状态文件负责记录当前智能体已安装技能与版本
  - 本地技能目录为实际技能落地位置（路径可配置）

## 请求约定

- 默认域名：`https://yuanli.ailaw.cn`
- Header:
  - `Accept: application/json`
  - `Content-Type: application/json`
  - `Authorization: Bearer <YUANLI_API_TOKEN>`（可选，按部署鉴权策略启用）

## `/api/skills` 查询参数

- `search`：关键字
- `category`：分类
- `page`：页码
- `page_size`：每页数量（后端上限 100）
- `sort`：`default` / `downloads` / `likes`

## 本地状态文件结构

默认路径：`~/.yuanli/agent_skills.json`

```json
{
  "auto_update_configured": false,
  "skills": {
    "jicheng-contract-review": {
      "skill_id": "jicheng-contract-review",
      "name": "合同审查（四层检查版）",
      "version": "1.0.0",
      "from": "yuanli",
      "installed_at": "2026-07-01T10:30:00+00:00",
      "workbuddy_path": "~/.workbuddy/skills/jicheng-contract-review",
      "registration_method": "cli",
      "content": "..."
    }
  }
}
```

字段说明：

| 字段 | 含义 |
|------|------|
| `auto_update_configured` | 用户是否已配置定时检测更新机制 |
| `workbuddy_path` | Skill 在本地技能目录中的实际路径（历史字段名，通用平台可复用） |
| `registration_method` | `cli`（CLI 安装）或 `scan`（scan 命令发现） |
| `identification_method` | `yuanli_skill_id`（frontmatter 直读）或 `name_search`（名称检索匹配） |
| `from` | 来源标识，固定为 `yuanli` |

## 本地技能目录集成

- 技能目录环境变量：
  - `YUANLI_AGENT_SKILLS_DIR`（推荐）
  - `YUANLI_WORKBUDDY_SKILLS_DIR`（兼容旧配置）
- 默认值：`~/.workbuddy/skills`
- `install --register-to-workbuddy`：下载 zip → 解压到 `{skills_dir}/{skill_id}/` → 在 SKILL.md frontmatter 注入 `yuanli_skill_id`
- `scan`：扫描本地技能目录，识别元力 Skill 并与状态文件交叉比对
  - 优先读取 SKILL.md frontmatter 的 `yuanli_skill_id`
  - 若无 `yuanli_skill_id`：用 frontmatter 的 `name`（或 `title`、首个 `#` 标题、目录名）在元力平台 `GET /api/skills?search=...` 检索并比对
  - 高置信匹配（ID/名称精确一致）→ 视为元力来源；`--register` 时可写入状态文件，并回写 `yuanli_skill_id` 到 SKILL.md
  - `--register` 注册时会写入版本号：优先 SKILL.md frontmatter `version`，否则拉取 `GET /api/skills/{id}` 的 `version`

scan 结果分类：

| 状态 | 含义 |
|------|------|
| managed | 已识别为元力 Skill 且状态文件中已有记录 |
| unregistered | 已识别为元力 Skill 但状态文件中无记录（含 `yuanli_skill_id` 或名称检索匹配） |
| ambiguous | 名称检索到多个高置信候选，需人工确认 |
| unknown | 无法识别为元力来源（无 ID 且名称检索未匹配） |

## 可配置路径

- `YUANLI_AGENT_SKILL_STATE_PATH`：安装状态文件，默认 `~/.yuanli/agent_skills.json`
- `YUANLI_AGENT_SKILL_PACKAGE_DIR`：技能包目录，默认 `~/.yuanli/packages`
- `YUANLI_AGENT_SKILLS_DIR`：本地技能目录，默认 `~/.workbuddy/skills`

## 定时检测更新（通用智能体）

供定时任务调用的统一命令：

```bash
python yuanli_skill_api.py check-updates --format text
python yuanli_skill_api.py check-updates --auto-update --download-package --format text
```

建议频率：每周一次（每周一 09:00）。

### 平台落地方式（任选）

| 平台 | 建议方式 |
|------|---------|
| Linux | `crontab` / `systemd timer` |
| CI/CD | 定时流水线（如 GitHub Actions `schedule`） |
| 智能体平台 | 平台 automation/schedule API |
| IDE Agent | 任务调度插件 + CLI |

### 安装后引导规则

- 首次 `install` 或 `scan --register` 后：强提醒用户是否配置定时检测
- `list` 且 `auto_update_configured=false`：可轻提示一次
- 用户已配置：不再重复引导

配置完成后，将状态文件 `auto_update_configured` 设为 `true`。

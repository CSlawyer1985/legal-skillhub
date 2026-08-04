# 合规与安全披露

本文档供 **OpenClaw / ClawHub 审核**、企业安全评审及终端用户知情使用。若技能清单支持外链说明，可将本文件路径或摘要填入「安全 / 权限 / 数据」相关字段。

**注册表 / 元数据**：`SKILL.md` 文件顶部包含 `credentials_required`、`credential_env_vars`、`openclaw_skill_api_key` 等 YAML 字段，并与短描述（`description`）一致声明：**必须**提供专利 API 凭证（`PATENT_API_TOKEN` 和/或 OpenClaw `skills.entries.patent-search.apiKey`），**不是**「无需环境变量」类技能。

**SKILL.md 与 Unicode**：仓库内该文件以 UTF-8（NFC）保存；维护时避免粘贴自富文本来源的零宽字符与双向文本控制符。发布前可用 `od -c` 或编辑器「显示不可见字符」复核。

---

## 中文

### 1. 凭证与本地数据

| 来源 | 用途 | 是否由本技能直接读取磁盘上的 OpenClaw 配置文件 |
|------|------|-----------------------------------------------|
| 环境变量 `PATENT_API_TOKEN` | 专利 API 鉴权 | 否（仅进程环境） |
| OpenClaw 配置项 `skills.entries.patent-search.apiKey` | 与上项等价，由用户在宿主中配置 | **否**：主逻辑与 `patent_token.py` 仅在用户本机已安装 CLI 时，通过子进程执行 `openclaw config get skills.entries.patent-search.apiKey` 获取；**不**打开、不解析 `~/.openclaw/openclaw.json`（或其它主目录路径下的配置文件） |
| 技能目录内 `config.json`（可选，由用户从 `config.example.json` 复制） | 本地开发或离线默认值 | 仅读取**技能包内**该文件；**禁止**在仓库或发布包中提交真实 Token |

### 2. 网络与第三方服务

- **对外请求域名**：`www.9235.net`（HTTPS，默认基路径 `https://www.9235.net/api`）。
- **传输内容**：为实现检索、详情、分析、下载等功能，会向上述服务发送检索式、专利公开号/申请号、分页与筛选参数等；**不**将用户的 OpenClaw 主配置文件内容上传至第三方。
- **第三方条款**：使用专利数据服务须遵守 [9235 开放平台](https://www.9235.net/api/open) 及服务商的用户协议与隐私政策。

### 3. 环境变量与宿主注入

在 OpenClaw 运行时，宿主可能注入 `OPENCLAW_SKILL_NAME`、`OPENCLAW_SKILL_METADATA`、`OPENCLAW_SKILL_CONFIG` 等变量。本技能**不因诊断目的在标准路径下打印这些变量的明文内容**。

### 4. 仓库与发布物要求（发布者承诺）

- 不在 Git 仓库、技能包、示例配置中存放**真实** API Token；`config.json` 已列入 `.gitignore`，模板以 `config.example.json` 为准。
- `SKILL.md` 正文不包含零宽字符、双向文本控制符等易被用于提示注入的隐蔽字符（发布前建议对打包产物做相同校验）。

### 5. 用户责任

- 用户自行向 9235 申请 Token，并妥善保管；泄露后应立即在服务商侧轮换。
- 在共享日志或截图前，应对 `PATENT_*`、`OPENCLAW_*` 等环境变量与命令行中的 Token 脱敏。

---

## English (for marketplace / security review)

**Registry metadata**: The top of `SKILL.md` declares `credentials_required`, `credential_env_vars`, and `openclaw_skill_api_key`, consistent with the short `description`: a patent API credential is **required** (`PATENT_API_TOKEN` and/or OpenClaw `skills.entries.patent-search.apiKey`). This skill is **not** “no environment variables required.”

**SKILL.md & Unicode**: The file is UTF-8 (NFC). Avoid zero-width or bidi-override characters from rich-text paste; verify with a hex-capable editor on release artifacts.

### 1. Credentials and local data

| Source | Purpose | Direct filesystem read of OpenClaw JSON config? |
|--------|---------|---------------------------------------------------|
| `PATENT_API_TOKEN` | Patent API authentication | No (environment only) |
| OpenClaw key `skills.entries.patent-search.apiKey` | Same as above, host-managed | **No**: resolution uses the `openclaw config get skills.entries.patent-search.apiKey` **CLI** when available; the skill **does not** open or parse `~/.openclaw/openclaw.json` (or other dotfiles) directly |
| Optional `config.json` in the skill directory (copied from `config.example.json`) | Local defaults / development | Reads **only** that file inside the skill folder; **never** ship real secrets in the repo or package |

### 2. Network and third parties

- **Endpoint**: `https://www.9235.net/api` (HTTPS).
- **Data sent**: Search queries, patent identifiers, pagination/filters, etc., as required for search, detail, analytics, and downloads. **No** upload of the user’s OpenClaw configuration file contents to third parties.
- **Third-party policies**: Use of the patent API is subject to the provider’s terms and privacy policy at [9235 Open Platform](https://www.9235.net/api/open).

### 3. Environment variables

The skill does not echo secret values from `OPENCLAW_*` / `PATENT_*` in normal operation.

### 4. Publisher commitments

- No real API tokens in source, examples, or distributed packages; use `config.example.json` and host/env configuration.
- `SKILL.md` should remain free of stealth Unicode control characters used for prompt injection; verify packaged artifacts before release.

### 5. User responsibilities

- Users obtain and rotate tokens at the provider; treat tokens as secrets in logs and screenshots.

---

**维护者**：若实现变更（新增网络域、读文件路径、环境变量），请同步更新本文件与 `SKILL.md` 中的摘要。

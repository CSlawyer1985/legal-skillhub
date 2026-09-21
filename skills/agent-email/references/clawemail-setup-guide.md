# Agent Email — 网易 ClawEmail 首次配置指南

## 前提

- 已安装 Node.js 18+（macOS: `brew install node`）
- 已在 [claw.163.com](https://claw.163.com) 注册并创建 Agent 邮箱
- 已获取认证 URL（格式如 `t1/xxxxxx`，有效期 30 分钟）
- 已在 ClawEmail 后台配置**通信规则**（Agent 邮箱管理 → 通信规则），开放外部收发权限

## 方式一：一键配置（推荐）

```bash
source scripts/mail-ops.sh
claw_init "t1/你的认证URL" "你的显示名称"
```

`claw_init` 自动完成：

1. `curl` 解析认证 URL → 获取邮箱前缀和 API Key
2. `mail-cli auth apikey set` → 存储 API Key
3. `mail-cli auth login` → 创建默认 Profile
4. `mail-cli folder list` → 验证连通
5. 写入 `scripts/.env` → 保存配置（邮箱地址、显示名称、文件夹 ID）

完成后即可使用 `claw_send`、`claw_list` 等函数。

## 方式二：手动配置

### 1. 解析认证 URL

```bash
curl -sL "https://u.163.com/<你的认证URL>"
```

返回两行：

```
<邮箱前缀>:<account-id>:
__apikey__:workspace:ck_live_xxx
```

记录邮箱前缀和 `ck_live_xxx`（API Key）。

### 2. 存储 API Key

```bash
npx "@clawemail/mail-cli@latest" auth apikey set "ck_live_xxx"
```

### 3. 创建默认 Profile

```bash
npx "@clawemail/mail-cli@latest" auth login \
  --user "<邮箱前缀>@claw.163.com" \
  --auth-method password \
  --password "ck_live_xxx"
```

### 4. 验证连通

```bash
npx "@clawemail/mail-cli@latest" folder list
npx "@clawemail/mail-cli@latest" mail list --fid 1 --limit 5
```

### 5. 写入 .env 配置

复制 `scripts/.env.example` 为 `scripts/.env`，填入实际值：

```env
AGENT_EMAIL=<邮箱前缀>@claw.163.com
DISPLAY_NAME="你的显示名称"
CLAW_PREFIX=<邮箱前缀>
CLAW_PROFILE=default
INBOX_FID=1
SENT_FID=3
```

`DISPLAY_NAME` 用于 `claw_send` 自动构造 `--from` 参数，控制对方收件箱里显示的发件人名称。

## 配置产物

| 文件 | 说明 |
|------|------|
| `~/.config/mail-cli/config.json` | mail-cli Profile 配置（用户名、显示名称） |
| `~/Library/Keychains/` 或系统密钥链 | API Key（由 `auth apikey set` 存储） |
| `scripts/.env` | Skill 内部配置备份（邮箱地址、文件夹 ID 等） |

## 常见问题

### claw_init 报错"认证 URL 无效或已过期"

认证 URL 有效期 30 分钟，过期后需从 ClawEmail 平台重新获取。

### Profile 已存在

如果之前配置过，`auth login` 会覆盖已有 Profile。如需保留，使用 `--profile <name>` 指定不同名称。

### 多邮箱管理

```bash
# 创建第二个 Profile
npx "@clawemail/mail-cli@latest" auth login \
  --user "another@claw.163.com" --auth-method password --password "ck_live_xxx" \
  --profile work

# 使用指定 Profile
mail-cli --profile work folder list
```

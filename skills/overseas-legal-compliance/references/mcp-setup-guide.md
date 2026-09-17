# MCP 常见问题排错

<!-- Maintained by Lu Lingyan, Deheng (Wuxi) Law Firm. -->

## 环境要求速查

| 工具 | 作用 | 检查命令 | 安装 |
|------|------|---------|------|
| Node.js | npx 跑 Ansvar 国别库 | `node -v` | [nodejs.org](https://nodejs.org) 下 LTS |
| Python 3 | courtlistener 本地版 | `python3 -V` | macOS 自带；Windows 去 python.org |
| pipx | security-controls | `pipx --version` | `pip3 install pipx` |
| git | 克隆仓库 | `git --version` | macOS 自带 |

## SDK 版本冲突速查（最常见的坑）

| 包 | 不兼容版本 | 兼容版本 | 修复命令 |
|-----|-----------|---------|---------|
| security-controls-mcp | mcp ≥ 2.0（砍了 `list_tools()`）| mcp 1.x | `pipx runpip security-controls-mcp install "mcp<2"` |

症状：`AttributeError: 'Server' object has no attribute 'list_tools'` → 必然是 mcp SDK 版本太高。

## 连接报错速查

| 报错信息 | 原因 | 解决 |
|---------|------|------|
| `streamableHttp connect failed: fetch failed` | 远程服务器挂了（常见于 Vercel 免费端点） | 切成本地 npx 版。例如 `eu-regulations` 从 URL 切为 `npx -y @ansvar/eu-regulations-mcp` |
| `streamableHttp connect timed out after 12000ms` | 网络超时 | 同上 |
| `SSE error: Invalid content type` | 远程端点格式不兼容 | 同上 |
| `MCP error -32000: Connection closed` | 本地 MCP 启动失败 | 检查 Node.js 是否已安装、npm 包名是否正确 |
| `npx: command not found` | 没装 Node.js | 去 [nodejs.org](https://nodejs.org) 下 LTS 版，一路「下一步」即可 |

## 一个远程 MCP 的三个常见死法

下面这个配置在各种场景下都可能挂：

```json
{
  "xxx-law": {
    "url": "https://xxx-mcp.vercel.app/mcp",
    "disabled": false
  }
}
```

**死法①** Vercel 免费实例休眠太久，第一次连接超时  
**死法②** 国内网络访问 Vercel 不稳定  
**死法③** 服务端换了域名/IP

→ **永远准备一个本地 npx 版本作备选**。如果 `@ansvar/xxx-law-mcp` 这个 npm 包存在，直接切过去。

## CourtListener API Token 申请

1. 打开 [courtlistener.com/api](https://www.courtlistener.com/api/)
2. 注册账号（免费）
3. 登录后在 API 页面看到 Token（一串字母数字，如 `42e18bc110387518793e56fac3939ef25ec45a6f`）
4. 把 Token 告诉 AI，AI 会帮你写入配置

## GovInfo API Key 申请

1. 打开 [api.govinfo.gov](https://api.govinfo.gov/)
2. 填邮箱 → Request API Key
3. 收邮件 → 复制 Key
4. 把 Key 告诉 AI，AI 帮你写入

## 台湾法数据库无法连接

旧的远程端点 `https://taiwanese-law-mcp.vercel.app/mcp` 已失效（2026-08-25 实测 HTTP 000），**不要再配远程 URL**。

正确方案（本地运行，数据源为台湾官方三源）：

```json
{
  "taiwanese-law": {
    "type": "stdio",
    "command": "mcp-taiwan-legal-db",
    "args": [],
    "disabled": false
  }
}
```

8 个工具覆盖：司法院裁判书（全文搜索 + 取得）、全国法规资料库（11,700+ 部）、宪法法庭（868 笔大法官解释 + 宪判字）。

> 安装方式（二选一）：
> - 推荐：`pip install mcp-taiwan-legal-db`，然后 `command` 写 `mcp-taiwan-legal-db`（entry point 写法）。
> - 或 clone 源码 `github.com/lawchat-oss/mcp-taiwan-legal-db`，用 `<clone目录>/.venv/bin/python3 -m mcp_server.server`（macOS / Linux）或 `<clone目录>/.venv/Scripts/python.exe -m mcp_server.server`（Windows）启动。

若连本地 MCP 也连不上（大陆网络访问 `law.moj.gov.tw` / `judgment.judicial.gov.tw` 可能受限），降级用 `references/tw-law-data/` 离线 JSON（法规目录 + 民法 + 劳基法 + 大法官解释索引）做 Grep 检索。

## 官方站被墙时的替代源（官方为准，第三方仅作初查）

台湾官方站（`law.moj.gov.tw` / `judgment.judicial.gov.tw` / `cons.judicial.gov.tw`）在大陆网络下被墙（2026-08-25 实测 HTTP 000）。**不要死磕官方域名**，替代策略：

| 角色 | 数据源 | 状态 | 用途 |
|------|--------|------|------|
| 初查定位 | `lawplayer.com`（法律人，第三方） | ✅ 能连 | 快速找条文位置，**不能作唯一依据** |
| 官方核验 | `references/tw-law-data/` 离线 JSON | ✅ 本地 | 民法/劳基法全文、释字索引，`source_url` 指向官方站 |
| 官方核验 | WebSearch 官方转载 | ✅ 能搜 | 立法院公报、官方 PDF 转载 |

**铁律**：第三方库（lawplayer 等）可能有错漏，凡输出台湾法条/解释，必须经「官方离线缓存」或「官方转载」核验；只有第三方单源时，明确标注「⚠️ 仅第三方源，未经官方核验」。

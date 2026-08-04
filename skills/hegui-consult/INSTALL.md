# hegui-consult 合规咨询 skill · Claude 安装（两步）

## 1. 放置 skill
解压本包，把 `hegui-consult` 整个文件夹放到（任选其一）：
- 个人级（所有项目可用）：`~/.claude/skills/hegui-consult/`
- 项目级（仅当前项目）：`<你的项目>/.claude/skills/hegui-consult/`

放好后目录应是 `…/skills/hegui-consult/SKILL.md`（外层不要再多一层）。

## 2. 连上 hegui MCP（skill 依赖它取数据）
在 `~/.claude.json`（个人级）或项目根 `.mcp.json` 里加：

```json
{
  "mcpServers": {
    "hegui": {
      "type": "http",
      "url": "https://www.dxy-aiagent.com/mcp/hegui/mcp",
      "headers": { "Authorization": "Bearer <接入Token：登录 https://www.dxy-aiagent.com/mcp-hub.html 获取>" }
    }
  }
}
```

令牌与完整接入说明见接入中心页面 **https://www.dxy-aiagent.com/mcp-hub.html** —— 用董小屿账号登录后，在「接口说明」处点「复制 Header」获取完整令牌；「帮助文档 → 安装 Skill / 使用规则」有各客户端配置步骤。令牌可能轮换，以该页面为准。

## 3. 生效
重启 / 重连一次 Claude 会话。之后问到上市公司合规、信息披露、任职资格、交易所规则适用等问题，
会自动触发本 skill，按“先查法规→仅披露 required 才查公告”的两段式流程作答。

> 重 consult 可能 30–50 秒，客户端超时请给 ≥90s。

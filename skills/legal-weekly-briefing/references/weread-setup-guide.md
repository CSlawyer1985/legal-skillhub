# 微信读书搜一搜 · 配置指南（主通道）

> Level 3 主通道：通过微信读书网页版「搜一搜」发现法院公众号文章（mp.weixin.qq.com 直链）。
> 对应脚本：`scripts/weread_login.py`（登录）+ `scripts/fetch_weread_week.py`（抓取）。
> 2026-07-29 微信关闭 MP 跨号接口后，这是唯一稳定的公众号文章发现通道。

---

## 为什么用微信读书

MP 后台跨号接口已关闭（2026-07-29），搜狗微信搜索风控过严已废弃，公开搜索 API（腾讯云 WSA 等）因版权不含公众号内容。微信读书网页版「搜一搜」是当前唯一能拿到 **mp.weixin.qq.com 原文直链**的免费通道。

## 配置步骤

1. **注册微信读书账号**：下载微信读书 App（或打开 weread.qq.com），用微信登录即可。**不需要**购买会员、不需要发表任何内容。
2. **扫码登录（首次 + 登录态过期时）**：
   ```bash
   cd ~/.workbuddy/skills/legal-weekly-briefing
   python3 scripts/weread_login.py
   ```
   有头浏览器弹出 → 页面自动触发登录弹窗 → 微信扫码 → 脚本检测到 `wr_vid` cookie 后自动保存登录态到 `~/.config/weread_state.json`。
3. **验证登录态**：`python3 scripts/verify.py` 的 W1 项（weread 登录态存在且含 wr_vid）。
4. **拉取文章**：
   ```bash
   python3 scripts/fetch_weread_week.py --days 7   # 4 个号，近 7 天
   python3 scripts/fetch_weread_week.py --account 山东高法  # 单号
   ```
   输出 `scripts/mp_articles_weread.json`（5 字段：title/url/publish_time/digest/_source）。

## 登录态管理

- 登录态存 `~/.config/weread_state.json`（Playwright storage_state 格式），有效期约数周
- **过期自动检测**（fetch_weread_week.py 内置双保险）：
  - 预检：文件须含非空 `wr_vid` cookie
  - 运行时：打开 weread.qq.com 后重读 cookie，wr_vid 丢失 → 打印
    `❌ 微信读书登录态已过期。请重新扫码：python3 scripts/weread_login.py` 并退出（exit code 1）
- 登录态文件**严禁提交 Git**（`.gitignore` 已含 `we*.json` / `*.state.json`）

## 常见失败

| 现象 | 原因 | 处理 |
|------|------|------|
| 提示登录态过期 | wr_vid 失效 | 重跑 `weread_login.py` 扫码 |
| 某号 0 篇 | 该号文章可能未被微信读书收录，或近 7 天未发文 | 换 `--days 14` 确认；仍无 → 该号暂缺，由 L2（元宝）反查补充 |
| 某号篇数偏少（如 17→15） | 滚动加载轮次上限（6 轮），文章多的号可能漏 2 篇 | 可接受（验收标准：每号 ≥3、3 次差异 ≤20%） |
| mp 直链全空告警 | 微信读书页面结构变化 | 检查 `.search_list_item` 选择器是否失效，更新脚本 |

## 与流水线的衔接

- `run_pipeline.py` Stage 0 前置检查第 1 层即 weread 登录态（`preflight_channels()`）
- 缺失时自动降级到 yuanbao / tokenhub / websearch，并打印降级声明

# MP 自动发现 · 完整配置指南

> ⚠️ **DEPRECATED 2026-07-29：微信关闭跨号文章接口，此文档仅供历史参考。**
> 新通道见 `references/weread-setup-guide.md`（微信读书，主通道）与 `references/yuanbao-setup-guide.md`（元宝，补充通道）。
> 对应脚本 `scripts/fetch_mp_week.py` 已标记 DEPRECATED。

> 从零搭建微信公众号后台自动拉取文章。内容与 SKILL.md Level 3 章节同步，唯一维护源。

---

## 工作原理

微信没有公开 API 拉取任意公众号文章列表。替代路径：

```
你的个人微信公众号后台 (mp.weixin.qq.com)
    └─ 内部接口 appmsgpublish（非公开/无文档）
         └─ 参数: fakeid + token + cookie
              └─ 返回: 目标公众号最近文章列表
```

**关键认知**：

1. **你不需要运营大号**。微信「订阅号」免费注册——哪怕一篇不发，后台 `appmsgpublish` 接口照样可用。
2. **它不是公开 API**。没有官方文档，鉴权依赖 MP 后台登录态（cookie + token），必须从浏览器提取。
3. **cookie 和 token 不同**。cookie 持久化在浏览器数据库（有效期数天到数周）；token 是临时凭证（约 2-4 小时），每次打开 MP 后台页面刷新。
4. **只有 Edge 能被自动化读取**。Chrome/Safari 的 cookie 数据库在 macOS 上受 SIP 保护，Edge 路径不受保护。
5. **不需要保持浏览器前台**。Edge 登录后 cookie 持久化到磁盘，关闭窗口不影响。只要不「退出登录」即可。

**数据流**：
```
扫码登录 MP 后台（Edge）
    ↓ cookie 写入 Edge 本地数据库
refresh_session_from_edge.py 读取 Edge Cookies 数据库
    ↓ 提取 mp.weixin.qq.com 域 cookie + 获取 token
写入 cache/session.json
    ↓
wechat_mp_reader.py 加载 session.json
    ↓ cookie + token + fakeid → 调用 appmsgpublish
返回文章列表 → 按时间窗口过滤 → 候选池 → 评分 → 周报
```

---

## 前提条件

- **你自己的微信公众号**（订阅号即可，免费注册，不需要发文章）
- Level 1 已通过验证（`python3 scripts/verify.py` 全部通过）
- 本机 Microsoft Edge 浏览器
- `wechat-ocr-research` skill 已安装

---

## 配置步骤（8 步）

### Step 0: 注册个人微信公众号（订阅号）

> ⚠️ 这一步是前提——没有自己的公众号 = 没有 MP 后台 = 无法自动化拉取。

**注册方式**（免费，约 10 分钟）：
1. [mp.weixin.qq.com](https://mp.weixin.qq.com) →「立即注册」
2. 选**订阅号**（个人主体，免费，无需企业资质）
3. 填姓名 + 身份证号 + 绑定银行卡的微信号
4. 设置公众号名称和头像（随意——不需要发文章）
5. 等待审核（1-2 个工作日）

审核完成后扫码登录，看到左侧菜单栏 = 注册成功。

### Step 1: 确认 MP 后台登录权限

访问 `https://mp.weixin.qq.com`，微信扫码登录。看到左侧菜单栏（素材管理/用户管理/数据分析）即为有权限。

> 只有自己运营的或被授权管理的公众号才能看到后台。关注别人公众号不等于有管理权限。

### Step 2: 安装 wechat-ocr-research skill

WorkBuddy 用户：对话中说「安装 wechat-ocr-research skill」
开源用户：`cd ~/.workbuddy/skills/ && git clone [wechat-ocr-research 仓库地址]`

确认：`ls ~/.workbuddy/skills/wechat-ocr-research/scripts/refresh_session_from_edge.py`

### Step 3: Edge 登录 MP 后台

**为什么必须是 Edge？** macOS 上 Chrome/Safari 的 cookie 数据库受 SIP 保护，普通脚本无权读取。Edge 路径不受 SIP 限制。

1. 打开 Edge，访问 `https://mp.weixin.qq.com`
2. 微信扫码登录
3. 在 MP 后台随便点几个页面（素材管理/用户管理），确保 cookie 完整落盘
4. 可关闭 Edge 窗口——cookie 已持久化，只要不「退出登录」

### Step 4: 从 Edge 提取 cookie + token

```bash
cd ~/.workbuddy/skills/wechat-ocr-research/scripts
python3 refresh_session_from_edge.py
```

**这个脚本做了什么？**
1. 打开 Edge cookie 数据库 → 读取 `mp.weixin.qq.com` 域下全部 cookie
2. 拼成 HTTP Cookie 头 → 访问 MP 后台首页 → 从 HTML 提取 token
3. 写入 `cache/session.json`

**期望输出**：
```
🔍 Reading Edge cookies...
✅ Got 12 cookies from Edge
🔑 Getting token from MP backend...
✅ Token: 1478077854
✅ Saved to cache/session.json
✅ Session verified OK — ready to use!
```

| 错误 | 原因 | 解决 |
|------|------|------|
| `Edge cookie database not found` | Edge 未安装或未用它登录 MP | 用 Edge 打开 mp.weixin.qq.com 扫码登录 |
| `Got 0 cookies from Edge` | 登录后没访问 MP 页面就关了 | 登录后在 MP 后台点几个页面再跑 |
| `Token extraction failed` | token 已过期或 MP 反爬 | Edge 重新打开 MP 后台任一页面，重跑脚本 |

### Step 5: 验证 session

```bash
python3 wechat_mp_reader.py session check
```

期望: `valid: true`。若 `false`，Edge 重新登录 MP 后台 → 重跑 Step 4。

### Step 6: 获取目标公众号 fakeid

1. MP 后台 → 左侧「素材管理」→「新建图文」
2. 编辑器 →「超链接」→「查找文章」
3. 输入公众号名称搜索
4. 点击搜索结果中的公众号名称 → 地址栏 URL 含 `fakeid=xxx`
5. 复制 `fakeid=` 后面的值

填入 `assets/config/sources.yaml`：

```yaml
mp:
  enabled: true
  accounts:
    - name: "山东高法"
      fakeid: "MzA5MDAxMjk5Ng=="
    - name: "上海一中院"
      fakeid: "MjM5MjkwMDkxMA=="
    - name: "上海二中院"
      fakeid: "MzA4MzY3NjMxNw=="
  per_account_limit: 30
```

> fakeid 不包含公众号身份信息，可安全分享。但**不要分享 `session.json`**。

### Step 7: 配置拉取参数

```yaml
mp:
  per_account_limit: 30  # 每账号每次最多拉多少篇
```

### Step 8: 首次全链路测试

```bash
cd ~/.workbuddy/skills/legal-weekly-briefing
PYTHONPATH=scripts python3 scripts/run_pipeline.py candidates.jsonl
```

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 为什么要注册个人公众号？我没有内容要发 | 不是用你发的文章——是用后台接口去拉别人公众号的文章 | 注册免费订阅号（10 分钟） |
| 为什么必须是 Edge？ | Chrome/Safari cookie 数据库受 SIP 保护，Edge 不受限制 | 装 Edge，用它登录一次 MP |
| Edge 登录后需要一直开着吗？ | 不需要。cookie 持久化到磁盘，关闭不影响读取 | 最小化或关闭都可，只要不点「退出登录」 |
| cookie 和 token 有什么区别？ | cookie 持久化（数天到数周）；token 约 2-4 小时失效 | cookie 不变则 token 可通过访问 MP 首页自动刷新 |
| session valid: false | cookie 过期或 token 失效 | Edge 重新登录 MP，重跑 refresh_session |
| token 过期了怎么办？ | 约 2-4 小时失效 | 重跑 refresh_session_from_edge.py（cookie 还在则无需重新扫码） |
| 拉不到某公众号文章 | fakeid 不对或近 30 天未发文 | 重新获取 fakeid |
| 拉到的不是近一周的 | per_account_limit 不够大 | 建议 ≥ 30 |
| macOS 报「无法验证开发者」 | 脚本无签名 | `xattr -d com.apple.quarantine scripts/*.py` |

---

## 替代方案：没有 MP 权限

**方案 A: WebSearch 手动发现 + 自动评分**
1. 用 `sources.yaml` 关键词每周搜一次
2. 手动整理 `candidates.jsonl`
3. 让 AI 标注特征向量
4. 跑 `run_pipeline.py` 评分

**方案 B: RSS/邮件订阅 → 自动收集**
1. 用 RssHub 等订阅法院网站更新
2. IFTTT/Zapier 自动收集到 Google Sheets
3. 导出 CSV → 转 `candidates.jsonl` → 评分

**方案 C: 纯依赖 legal-hot skill**
1. 对话中说「查一下最近法律热点」
2. 自动 WebSearch → 输出简报
3. 零配置；但不会入库 IMA，无评分排序

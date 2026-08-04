# 腾讯元宝 · 配置指南（补充通道）

> Level 3 补充通道：对微信读书（L1）「缺失本号原文」的条目，用元宝反查 mp.weixin.qq.com 原文直链。
> 对应脚本：`scripts/yuanbao_login.py`（登录）+ `scripts/fetch_yuanbao_supplement.py`（反查）+ `scripts/merge_candidates.py`（合并）。
> 元宝产品端有微信内容生态授权，可搜到公众号文章；API 端（WSA 等）因版权不含公众号内容——**不要尝试用 API 替代**。

---

## 为什么需要 L2

L1（微信读书）搜索结果可能混入**转载号**文章（URL 的 `__biz` 不是目标公众号）。对这类「缺失本号原文」条目，用元宝提问「搜索微信公众号『X』的《Y》原文链接」，回答中可解析出 mp 直链。

## 配置步骤

1. **登录元宝**（首次 + 登录态过期时）：
   ```bash
   cd ~/.workbuddy/skills/legal-weekly-briefing
   python3 scripts/yuanbao_login.py
   ```
   有头浏览器打开 yuanbao.tencent.com/chat → 扫码/登录 → 检测到「输入框出现且页面无未登录特征」→ 保存登录态到 `~/.config/yuanbao_state.json`。
   `--force` 可强制重扫。
2. **反查缺失条目**：
   ```bash
   python3 scripts/fetch_yuanbao_supplement.py --test-weekly   # 测试：分层抽 7 条周报标题
   python3 scripts/fetch_yuanbao_supplement.py                 # 正常：反查 __biz 指纹不匹配的条目
   python3 scripts/fetch_yuanbao_supplement.py --list-keys     # 只打印待反查清单
   ```
   输出 `scripts/yuanbao_links.json`（每条含 title/account/query/answer/mp_urls/status/l1_url）。
3. **合并 L1+L2**：
   ```bash
   python3 scripts/merge_candidates.py          # → scripts/candidates_merged.jsonl（5 字段）
   python3 scripts/merge_candidates.py --check  # 字段完整性校验
   ```

## 登录态管理

- 登录态存 `~/.config/yuanbao_state.json`，有效期约 10 天
- **登录判定双条件**（防误判）：输入框存在 **且** 页面无「未登录/扫码登录」特征
- 登录态文件**严禁提交 Git**（`.gitignore` 已含 `*.state.json`）

## 常见失败

| 现象 | 原因 | 处理 |
|------|------|------|
| 反查全部「转载版」（0 链接） | 假登录态：页面显示登录二维码但被误判为已登录 | 重跑 `yuanbao_login.py`（修复版双条件判定），确认提示「输入框已出现且无未登录特征」 |
| 提示「元宝不可用」 | 连续风控或登录态失效 | 等 30 秒重试 1 次（脚本内置）；仍失败 → 该条保留 L1 转载链接，不阻断 |
| 命中链接为 `src=11&timestamp=` 分享型 | 元宝返回的是分享签名链接（非 `__biz` 直链） | 可用（P4 集成时抽样验证长期有效性）；比 L1 转载链接更接近原文 |
| 提问间隔风控 | 请求过快 | 脚本已内置 ≥5 秒间隔 + 随机抖动 |

## 反查策略说明

- 「缺失本号原文」判定：对每个号，统计 L1 条目 URL 的 `__biz` 指纹，出现次数最多的即本号指纹；`__biz` 不一致的条目 = 转载/缺失
- 合并冲突：以 L1 为准（微信读书更稳定）；L2 命中且 URL 未出现过 → 补充进候选池，继承 L1 同标题条目的 publish_time/digest

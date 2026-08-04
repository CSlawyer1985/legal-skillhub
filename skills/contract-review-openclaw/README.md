# contract-review Skill

这是面向 ClawHub 公开发布的最小 Skill 发布物。

## 公开用途

- 帮助用户发现合同审核能力
- 将 slash / 自然语言入口统一分派到 `contract_review`
- 约束 agent 在自动认证、提交、查状态、继续、追加要求、下载结果场景下的行为

## 依赖边界

- Skill 只负责公开说明与触发
- OpenClaw Contract Review Plugin 负责认证前置、上下文选择、工具路由与真实执行
- 对于“上传合同 + 审核要求”的主路径，插件会在缺少登录态时自动发起登录，并在浏览器确认后自动继续原始提交
- 本发布物不包含私有地址、token、secret、调试命令或后端实现细节

## 当前范围

本 Skill 当前覆盖公开入口分派、自动认证主路径说明、显式登录/登出帮助、最近任务复用约束与公开安全边界；不展开底层 token 生命周期、上传实现、A2A payload 编排或 artifact 下载协议细节。

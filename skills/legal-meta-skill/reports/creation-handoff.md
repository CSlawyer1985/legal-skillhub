# legal-meta-skill v1.0.0 创建与发布交接

## 本次升级结果

本次升级将 `legal-meta-skill` 提升为 `1.0.0` 候选包，成熟度仍声明为 `library`（基础设施级）。目标是形成可审计、可迁移、可复现、可公开分发的中国大陆法律 Skill 元工具链。

已完成：

- intake 兼容读取 `legal-skill-intake/v0.1`，新模板和迁移器输出 `v0.2`；领域补充规则会进入目标包的 `references/domain-supplement.md`，不再只统计条数。
- IR 升级为 `legal-skill-ir/v0.3`，保留 `universal-legal-core/v0.1` 十二模块契约。
- frontmatter 畸形输入返回友好错误；证据路径拒绝软链接、越界和非普通文件；未来人工复核日期被拒绝；成熟度证据支持哈希和 IR 身份核对。
- provider 评测区分 `static_only`、`provider_failed` 和 `provider_passed`；路由不匹配不能升级为 provider-backed 通过证据。
- 审计评测支持 `--audit-mode` 外部输出或标准输出，目标 Skill 目录保持只读。
- 新增 DOCX 审阅、修订、批注和基准文件保护场景。
- 新增四类 `blocked` 停机案例：法源/日期、主体授权、损坏 PDF、外部发布权限。
- 增加 Apache-2.0、NOTICE、归属和商标边界文档。再分发项目必须保留许可证、NOTICE、版权声明和 CSlawyer 署名；业务法律交付不自动注入品牌。
- 增加 `legal_meta.py` 统一入口、迁移器、开源 README、贡献指南、安全报告指南、变更记录和发行构建入口。

## 当前统一值

- Skill 版本：`1.0.0`
- IR 版本：`legal-skill-ir/v0.3`
- intake 版本：`legal-skill-intake/v0.2`
- 能力模型：`universal-legal-core/v0.1`
- 模块总数：12
- 状态码：`active`、`not_applicable`、`blocked`
- 场景原型：8 类 + `other`
- 作者与公开署名：CSlawyer
- 主页：https://chenshi.ai
- 许可证：Apache-2.0

## 运行命令与结果

- `python3 -m unittest discover -s tests -q`：118 项测试全部通过。
- `python3 scripts/validate_legal_skill.py .`：验证通过，0 警告。
- `python3 scripts/validate_legal_profile.py .`：验证通过，0 警告。
- `python3 scripts/export_legal_skill_ir.py . --output reports/skill-ir.json`：IR 导出成功，名称和版本与 manifest 一致。
- `python3 scripts/evaluate_trigger_cases.py . --cases evals/trigger_cases.json --output reports/trigger-eval.json`：10/5/5 触发用例，0 错误；结果仍是静态描述覆盖证据。
- `python3 scripts/legal_meta.py audit . --output -`：只读审计通过；provider、人工盲评和真实项目证据按 `missing evidence` 输出。
- 软链接证据、空 description、未来日期、provider 路由错配、外部审计输出等对抗回归已覆盖。

## 许可证与传播边界

`LICENSE` 保持 Apache-2.0 官方文本不变。`NOTICE` 和 `ATTRIBUTION.md` 说明再分发时必须保留的来源信息；`TRADEMARKS.md` 说明 CSlawyer 名称和标识不随 Apache-2.0 自动授权。生成的衍生 Skill 包会复制 LICENSE、NOTICE、ATTRIBUTION 和 TRADEMARKS。

普通法律意见、合同、诉讼文书、客户邮件或其他业务成果不会因为使用本工具而自动成为本项目的衍生发行物，也不会自动插入 CSlawyer 品牌。

## 已验证与证据缺失

已验证：包结构、JSON 语法、十二模块固定标签与最低输出、评测引用覆盖、静态触发描述覆盖、IR 导出、证据路径安全、证据哈希、软链接拒绝、未来日期拒绝、只读审计、领域补充持久化、DOCX 场景模板、许可证与 NOTICE 门禁、生成器原子提交、迁移器和测试。

以下仍为 `missing evidence`，不得改写为已验证能力：

- OpenAI/Codex 与 Claude 的真实平台加载记录；
- provider-backed 模型触发与法律输出运行；
- 独立律师盲评；
- 真实案件或客户项目回归；
- 跨 Skill 路由冲突实测；
- 公开仓库干净安装与发布后回滚演练。

## 发布前剩余动作

1. 在 OpenAI/Codex 和 Claude 隔离环境完成真实加载记录。
2. 在干净副本执行 `python3 scripts/legal_meta.py validate .`、`audit` 和 `build-release`。
3. 检查发行包不含缓存、绝对路径、秘密、真实材料和本机状态。
4. 确认 GitHub owner、公开仓库可见性和首次推送授权。
5. 用户单独授权后再执行公开仓库推送、标签和 Release；本地升级本身不包含远程发布。

运行日期：2026-08-14。

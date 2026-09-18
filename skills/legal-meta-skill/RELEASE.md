# 发布清单

发布前必须在本地完成：

1. 核对 `manifest.json`、`SKILL.md`、IR、CHANGELOG 和发行标签版本一致。
2. 运行单元测试、Skill 校验、profile 校验、只读 audit 和触发评测。
3. 在 OpenAI/Codex 与 Claude 隔离环境完成真实加载记录；未完成时不得宣称双平台已验证。
4. 运行 `python3 scripts/legal_meta.py build-release . --output-dir dist`。
5. 检查压缩包不包含 `.git`、缓存、绝对路径、秘密、真实材料和临时报告。
6. 对发行包执行全新目录解包、validate、audit 和 IR 导出。
7. 更新 `CHANGELOG.md` 和 `reports/creation-handoff.md`，保留全部 missing evidence。
8. 只有在用户单独明确授权目标 owner、公开可见性、版本标签和远程写入后，才推送仓库或创建 Release。

发布后的首个动作是从公开地址进行全新安装和校验；失败时保留标签和发行物，停止后续推广，并按回滚说明撤下有问题的 Release。

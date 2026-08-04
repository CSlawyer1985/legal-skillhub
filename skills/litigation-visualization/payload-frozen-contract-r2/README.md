# 律师专用法律知识蒸馏与 GEO 发布 Skill V1.0 RC4 Candidate

这是一个面向律师的本地候选 Skill，用于把授权案件、法律书籍、课程和实务经验蒸馏为可审计、可执行、可测试的知识与工作流，并在独立门禁之后生成隐私安全的 GEO 公开投影。

## 这不是简单拼接

本包以原创的“案由诉讼 Skill 蒸馏方法论”为控制骨架，对仓颉和姚金刚（`yaojingang/GEORank`）的 GEO 方法逐项扬弃：

- 从仓颉保留全局理解、多镜头提取、候选/淘汰轨迹、原子化、链接和压力测试；
- 将书籍专用三重验证替换为法律四重验证，并取消自动安装与特定进化工具依赖；
- 从 GEO 方法保留直接回答、结构化表达、查询集、引用忠实度和重复测量；
- 舍弃 GEORank 平台 API 依赖、伪关键词分数、单一综合分和排名保证；
- 新增案件答案键隔离、法源时效、证据链、隐私分层、误用门禁和独立发布授权。
- 将两轮案件型子 Skill 的验收经验回灌为可判定门：领域基线全覆盖、法院件零治理词、固定字体双遍逐页渲染，以及完整九文书案与 HOLD 个案双 E2E。
- 将法院提交件、专业服务件和治理 sidecar 物理分层，并用结构化输出契约禁止派生物反写 SSOT。
- 增加按需诉讼可视化扩展契约：案型子 Skill 从冻结 `L2-05` 发布 anchor-map 与 handoff，独立可视化 Skill 消费该契约；母 Skill 不内置 renderer。

详细决定见 [Sublation 比较矩阵](templates/Sublation比较矩阵.md)。

## 当前状态

- 版本：`1.0.0-rc.4-candidate`
- 状态：`candidate-local-only`
- 许可：`proprietary-internal`
- 原始案件载荷：`0`
- 外部发布授权：`false`
- RC4 candidate 正式 Skill 根安装：未执行
- 历史部署观察：两个本地技能根存在字节一致的 RC1，但授权收据缺失，不构成 RC3 安装或生产晋升
- 新增顶层产物类别：无；诉讼可视化使用 `professional_service.litigation_visualization` 子配置
- 触发方式：`on_request`
- 可视化能力默认状态：`hold`

## 本地验证

在本目录运行：

```bash
python3 scripts/validate_package.py
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider tests
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_litigation_visualization_extension.py
```

验证通过只证明候选包结构和静态契约闭环，不替代跨案由回归、安装态 dry-run、回滚演练、观察窗、独立法律与隐私复核或用户最终批准。

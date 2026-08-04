# REFERENCE-PAYLOADS（参考件边界声明）

以下目录/文件为方法论与契约**参考件（non-executable-reference）**，不是本包执行入口，不参与运行门：

- `payload-legacy-skill/`：litigation-visualization-cn 独立 Skill 本体（历史校验器自测状态见 Codex 审计 3d6f684d…，不得直接调用于生产）。
- `payload-frozen-contract-r2/`：冻结可视化合同 donor（渲染治理规范参考）。
- `viz-engine/recovery-gen_case_views.py`、`viz-engine/recovery-render_views.py`：历史 donor 逻辑（消费 case-views.json，不符合本包 only-input=冻结07+A01-A09 契约）。

本包唯一公开 runner = `tools/run_vis.py`（07-only 硬门：显式 --enable-vis＋TEXT PASS 绑定＋同案冻结 07 哈希＋A01-A09 精确锚集；跨案/缺失/篡改/错锚/关闭态全部 fail-closed 零产物）。

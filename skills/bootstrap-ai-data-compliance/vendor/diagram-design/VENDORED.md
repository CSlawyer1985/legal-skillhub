# VENDORED: diagram-design (Data flow type)

内嵌第三方技能 [cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design)（MIT），
仅取其 Data flow 图表类型的规范与脚本，作为本 Skill 数据流向图的标准渲染方案。

## 版本与来源

- **上游版本**：diagram-design v2.4（SKILL.md frontmatter `version: "2.4"`）
- **获取时间**：2026-08-19
- **来源仓库**：https://github.com/cathrynlavery/diagram-design （clone 于 `~/code/diagram-design`）
- **License**：MIT（LICENSE 已随附）

## 内嵌内容（精简自上游 skill 目录）

| 路径 | 上游来源 | 用途 |
|---|---|---|
| `SKILL.md` | skills/diagram-design/SKILL.md | 总规范（28 类型索引 + 设计系统 + 连接纪律） |
| `references/type-data-flow.md` | 同上 | **数据流图参数契约与布局公式**（渲染依据） |
| `references/style-guide.md` | 同上 | 语义色 token（paper/ink/muted/accent/link） |
| `references/output-spec.md` | 同上 | 尺寸/细节/受众输出旋钮 |
| `scripts/self_check.py` | 同上 | 出图验收脚本（可访问性 SVG 合同） |
| `assets/template.html` | 同上 | 页面外壳模板 |
| `assets/example-data-flow*.html` | 同上 | 官方示例参照 |

## 升级方式

1. `cd ~/code/diagram-design && git pull`
2. 对照上表重新拷贝上游文件到本目录
3. 运行本 Skill 的回归验证（render + self_check）

## 使用约束（写在本 Skill 的 SKILL.md 中）

- 数据流图一律用 Data flow 类型（角色泳道 × 阶段列），输入为 `assets/dfd-scenes/<industry>-dataflow.json` 视图
- 渲染由 `scripts/dataflow_builder.py` 完成（实现 type-data-flow.md §2 确定性公式）
- 复杂度预算：≤4 泳道、≤6 阶段、≤12 流、唯一 focal（1 节点 + 1 阶段 + 1 条 accent 流）
- 不要直接修改本目录下的上游文件；需要定制（如品牌色）时改上层调用方的视图 JSON

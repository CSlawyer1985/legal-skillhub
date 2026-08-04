# 法律图表化 Skill

主技能 **`legal-visualization`** 与两个子技能（`skills/drawio`、`skills/excalidraw-diagram-generator`）

## 常用命令

正式判决书图表：

```text
用法律图表化 Skill 根据这个判决书做三张正式图：案件关系图、裁判逻辑图、金额责任图，导出 draw.io PNG。
```

公众号手绘图：

```text
用法律图表化 Skill 根据下面案情画一张手绘风诉讼战略地图，输出 Excalidraw 文件。
```

合同审查流程：

```text
用法律图表化 Skill 把合同审查流程画成正式流程图，要求线条不压字、节点不重叠、适合公众号阅读。
```

## 法律图表化 Skill 的核心规则

- 不直接画，先判断图表类型。
- 复杂案件不要压成一张图。
- 线条不能压字。
- 节点不能重叠。
- 长线走外侧。
- 金额计算、附随费用、责任主体要分层。
- draw.io 负责正式交付，Excalidraw 负责白板解释。

## 注意

`drawio` 如需自动导出 PNG/SVG/PDF，建议安装 draw.io Desktop。

`Excalidraw` 不需要安装客户端，生成的 `.excalidraw` 文件可以直接拖到 <https://excalidraw.com> 打开。
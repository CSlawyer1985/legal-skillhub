# 教程工作流

首次运行演练。检测环境，以模拟提取端到端运行一个完整示例。`check_setup.py` 和 `render_html.py` 为真实调用；提取使用硬编码场景数据，因此教学效果绝不依赖于解析器质量。

## 阶段 1——设置门控

运行 `shared/setup-check.md` 中的流程。依赖缺失 → 打印 pip 命令行，停止（“安装后重新运行 /legal-diagram tutorial”）。崩溃 → 显示 stderr，指出可能原因，停止。正常 → “Setup complete.”（设置完成），进入阶段 2。

## 阶段 2——路径选择

呈现：`[L] 诉讼`——合同争议时间线（timeline）；`[C] 公司`——实体股权结构（erDiagram）。要求用户输入 L 或 C。无效 → 重新提示一次，然后默认 L（注明选择）。

## 阶段 3——运行完整示例

使用所选场景（见下），并口头逐步讲解：

1. **叙述**场景。
2. **模拟清单摘要**（硬编码，非来自脚本）：matter_type、实体计数、一条示例性指令、一条示例性提示。一行说明：脚本生成了这份 TODO 清单，助手现在执行它（两遍思想）。
3. **模拟通俗语言摘要**——将场景的已填充字段以引导模式的摘要形式呈现，与真实用户将看到的一模一样。使用场景的硬编码数据；格式按 `workflows/guided.md` 第 2 步的渲染表。场景 L：显示当事方及角色、关键事件（时间顺序）、法律义务。场景 C：显示实体、股权、关系。每个部分之后，以“看起来对吗？更正一个名称、补充我遗漏的内容或删除任何内容——然后我会建议一种图表类型”结束。模拟用户回应“看起来没问题”并继续。此步骤存在的意义是让用户在真实运行前看到引导模式摘要的样子。
4. **模拟类型确认**——以用户将看到的方式显示 `diagram_selector.py` 推荐：**推荐：** [通俗名称] — [一句话理由]。**备选方案：** [备选1]（[它展示什么]）· [备选2]（[它展示什么]）。模拟用户确认推荐并继续。
5. **打印该类型的怪癖**（`shared/parser-guards.md`）。
6. **生成**场景的围栏块；应用防护；内联验证。
7. **提供 HTML 导出**：“导出为独立 HTML？Y/N（默认 Y）。”选 Y：构建硬编码 FigureDescription，运行 `render_html.py`，报告路径。失败时，注明 mermaid.live；不中止。
8. **回顾**，7 个步骤：环境已检查、文档已规范化、信号已检测、清单指令已执行、摘要已走查并确认、类型已选择、图表已生成。

### 场景 L——诉讼（时间线）

VendorCo 诉 ClientCorp MSA 争议：2026 年 1 月签署，2 月开始履行，3 月报告缺陷，4 月补救计划，5 月扣留付款，5 月违约通知。摘要：2 个当事方、6 个事件；指令 = 违约通知义务上的 `risk_level`；提示 = 来自补救计划条款的过程序列。选择器：`timeline`，“6 个事件，诉讼”。摘要显示：当事方及角色（VendorCo — 供应商/供货方；ClientCorp — 客户/采购方）、关键事件（6 条带日期条目，时间顺序）、法律义务（VendorCo 按 MSA 履行 — 风险：高）。未找到：证人、知识产权资产 — 标记为缺失，注明与该事项类型无关。图表 slug：`tutorial-litigation-timeline`。

### 场景 C——公司（erDiagram）

ParentCo 持有 OperatingSubA 100%、OperatingSubB 80%；MinorityInvestor 持有 OperatingSubB 20%；OperatingSubA 为客户 MSA 的当事方；OperatingSubB 为信贷协议项下的借款人。摘要：5 个实体、3 条股权链、2 个关系；指令 = cross-linking；丰富化 = 基数。选择器：`erDiagram`，备选 `flowchart TD`。摘要显示：实体（ParentCo — 控股公司；OperatingSubA — 全资子公司；OperatingSubB — 多数股权子公司；MinorityInvestor — 20% 股东；Customer — MSA 相对方；Lender — 信贷协议出借人）、股权（3 条带百分比的链）、关系（2 条合同链）。在第 6 步，内联规范化名称（“Operating Sub A” → “OperatingSubA”），逐一记录，添加一段 erDiagram 与 flowchart 的比较。图表 slug：`tutorial-corporate-erdiagram`。

## 退出

引导用户走向快速路径：“下次，直接粘贴一个事项、放入一个文件路径或点明一种图表。无需教程。”

# 客户背调报告 Skill（v2.2）— 使用说明（路演版）

## 一句话介绍

输入一家公司名称和一条指令（如"帮我背调一下苏州仕净科技股份有限公司"），自动生成一份排版规范的 **Word 背调报告** + 一份 **PDF 信息来源汇编附件**，构成完整背调成果。

## 与普通工商查询报告的区别（核心卖点）

1. **律师视角而非数据堆砌**：报告核心在"客户画像、法律需求图谱、风险分级、洽谈策略"四节，直接服务商务洽谈。
2. **内置律所客户准入合规审查（v2.0）**：对标国际大所 Business Acceptance 机制与中国监管硬规范——利益冲突检索记录、反洗钱义务触发判断（《反洗钱法》第 64 条＋《律师行业反洗钱工作管理办法》司规〔2025〕2 号）、受益所有人穿透、名单筛查、付费能力评估、**风险评级与"接受/附条件接受/拒绝"三选一准入结论**、审批签字栏与十年存档提示。这是 2025 年反洗钱新规落地后律所的法定动作，多数律所尚无标准化工具。
3. **来源可核验**：禁止编造、逐条标注来源 URL 与查询日期、关键事实双源印证、未能核实事项单独列清单；PDF 附件与报告引用编号一一对应。
4. **排版规范化**：md 底稿与 Word/PDF 成果分离，脚本统一字体字号，不依赖手工排版。

## 运行方式

本 Skill 是一套"流程规范 + 脚本工具"，由 AI（Kimi Code）按 `SKILL.md` 执行：

1. **第 0 步·输入确认**：公司全称、背调目的、拟承接事项（用于反洗钱触发判断）、重点关注。
2. **第 1 步·信息采集**：先跑 `python3 scripts/mcp_collect.py <公司全称> output/XX背调`（已配置企查查/快查等 MCP 数据源时直连权威数据；未配置自动降级为公开网页检索），九个维度采集，事实先落**证据账本**。
3. **第 2 步·客户准入合规审查**：利冲检索设计、反洗钱触发判断、受益所有人穿透、名单筛查、付费能力、风险评级与准入结论。
4. **第 3 步·律师视角分析**：需求图谱、风险提示、洽谈建议、首次洽谈问题清单。
5. **第 4 步·成果生成与校验**：

```bash
cd 青训营/客户背调报告Skill
python3 scripts/md2docx.py output/XX背调/报告底稿.md output/XX背调/报告.docx   # Word 报告
../.venv/bin/python scripts/md2pdf.py output/XX背调/附件底稿.md output/XX背调/附件.pdf  # PDF 附件
python3 scripts/check_report.py output/XX背调/报告底稿.md output/XX背调/附件底稿.md     # 校验（必须 PASS）
```

6. **质控清单自检**（SKILL.md 第七节，17 项）后交付。

## 与市面主流产品的对比（竞品定位）

（完整 Benchmark 打分与理想尽调 Skill 规范见 `../尽调技能Benchmark评估报告.md`）

| 产品 | 数据 | 律师分析 | 准入合规 | 来源附件 | 价格 |
|------|------|------|------|------|------|
| 企查查/天眼查/犀牛卫尽调报告 | 强（含 API） | 无（数据罗列） | 弱 | 可回溯 | 数百-数千元/年 |
| 案牍 AutoDD | 强（核查底稿留存） | 报告初稿 | 无 | 有 | 机构定制 |
| Harvey / CoCounsel | 不做公开采集 | 强 | 利冲留给所内系统 | 带引用 | 企业级定制 |
| Intapp Intake | 依赖外部数据 | 弱 | 标杆（KYC+审批+监控） | 审计留痕 | 企业级定制 |
| 通用 AI 深度研究 | 广而不深 | 中 | 无 | 无留存、有幻觉风险 | 低 |
| **本 Skill** | 公开渠道采全 | 强（画像/需求/策略） | 内置六模块 | PDF 逐条留存 | 零边际成本 |

差异化亮点：竞品均无的"**历史服务机构识别**"（谁在服务这家客户）、"**首次洽谈问题清单**"（背调变接待武器）、"**定期复查＋增量更新页**"机制。能力边界如实标注：无权威数据库 API、不做所内利冲实查、不替代持续监控系统。

## 演示案例

`output/仕净科技背调/` 内为完整实测成果：

- 《苏州仕净科技股份有限公司背景调查报告.docx》（13 节、4 张表格）
- 《附件-信息来源汇编.pdf》（A1-A31 事实来源＋B1-B5 规范依据，与报告引用一一对应）

实测亮点：Skill 自动识别该公司已被 *ST、进入预重整、被证监会立案、列入失信被执行人等重大风险，给出"**高风险、附条件接受**"的准入结论和六项准入条件，并对照最高法/证监会 2024 年上市公司重整纪要提示"重整价值负面清单"风险——展示了从信息采集到准入决策的完整闭环。

## 环境依赖

- python3 + python-docx（生成 Word）
- `青训营/.venv`（reportlab，生成 PDF；新机器上 `python3 -m venv .venv && .venv/bin/pip install reportlab` 即可重建）
- 联网；可选：企查查 MCP 的 `QCC_API_KEY` 环境变量（不配则自动降级公开检索）
- **字体兼容提示**：Word 报告使用仿宋_GB2312/楷体_GB2312（Windows 公文标准字体）；Mac 或缺字体的机器打开会回退为宋体——安装相应字体，或在 Word 中全选替换为仿宋/楷体即可，排版结构不受影响

## 已知边界（路演被追问时的诚实回答）

- 利益冲突检索须由律师使用本所内部案件库完成，AI 只设计检索范围与比对清单（报告中留填写栏）。
- 失信被执行人明细、经营异常名录等受平台访问限制的项目列入"未能核实事项清单"，由律师助理人工复核。
- 报告仅供本所内部洽谈与准入审批使用，不构成对外法律意见。

---

## English Guide (for cross-border scenarios)

**Client Background Check Skill (v2.2)** — Input a company name and one instruction; the skill produces a formatted **Word (.docx) background-check report** plus a **PDF source annex**, with a built-in law-firm **client acceptance compliance review** (conflict-check worksheet, AML trigger assessment under PRC AML Law art. 64 and the 2025 Lawyers-AML Measures, UBO tracing, sanctions screening, fee-risk assessment, risk rating with an accept / conditional-accept / decline conclusion and sign-off block).

Pipeline: (0) input confirmation → (1) collection via MCP data sources first (`mcp_collect.py`, graceful fallback to public web search), all facts into an **evidence ledger** (claim→evidence→source→status→gap) → (2) acceptance review → (3) lawyer-perspective analysis (demand map, red/amber/green signals, first-meeting question list) → (4) scripted rendering (`md2docx.py` / `md2pdf.py`) and deterministic QA (`check_report.py`, must PASS before delivery) → periodic re-check with delta-only update pages.

Honest boundaries: no in-house conflict-database lookup (lawyers fill the worksheet), data depth depends on configured MCP sources, not a 7×24 monitoring system.

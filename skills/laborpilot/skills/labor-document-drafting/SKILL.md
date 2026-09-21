---
name: labor-document-drafting
description: 劳动争议法律文书起草。基于分析结果,按模板生成仲裁申请书、答辩状、代理词等文书的律师复核初稿。
license: AGPL-3.0
metadata:
  homepage: https://jinlishan.com/
  author: 金莉珊律师（微信jinlishan_）
  version: 1.4.4
---

# 劳动争议文书起草

> 废止复核（2026-09-07）：不得用浙江已废止旧解答充当现行法源；旧观点须另核有效条文后再写入正式依据，历史比较应明确来源状态。


1. 读取案件状态和上游分析/证据/金额结果。
2. 按模板起草,每个请求项/抗辩项:
   - 事实段引用证据清单中的证明事项
   - 法律依据段引用条文号(法规名+条号)
   - 金额段引用计算算式和结果
   - 浙江口径在关键争点上引用
3. 使用 `python3 scripts/generate_docs.py --case <结构化输入.json> --output <case-root> --types <用户明确要求的文书> --delivery-status lawyer_review_draft --strict` 生成 `.docx` 律师复核初稿；不得省略 `--types` 或顺带生成未请求文书。DOCX 进入 `01_律师复核初稿/`，Markdown 和版式报告进入 `.casework/drafting/`，已有同版本文件不得覆盖。
4. 生成器必须在 Pandoc 转换后应用并校验 JLS Word 版式；转换或版式校验失败时，不得以内部 Markdown 或命令成功提示冒充文书完成。
5. 初稿交独立业务验证并由律师针对当前文件哈希审批。只有在律师已批准当前初稿后，才可使用 `--delivery-status final_submission --approved-by <律师姓名>` 生成 `02_最终提交版/` 中的新文件；最终提交版须重新验证并重新审批。行动清单、内部占位符和待确认标记不得进入最终提交版。
6. 禁止引用未经核实的法条或裁判口径。
7. 完成节点前先将起草输入登记为 `internal_work_product`，再运行 `python3 scripts/workflow_graph.py register-artifact --state <case-root>/.casework/case_state.json --path <初稿.docx> --kind <产物类型> --version <版本号> --delivery-status lawyer_review_draft --generator scripts/generate_docs.py --created-by <执行者> --source-ref <集合:记录ID> --derived-from <起草输入artifact_id>` 登记真实存在的初稿文件，并在 `python3 scripts/workflow_graph.py transition --state <case-root>/.casework/case_state.json --event pass --actor <执行者> --output-artifact <初稿artifact_id>` 中关联该产物。正式产物必须形成业务来源链；只写“已起草”或登记不存在的路径不能通过门禁。最终提交版另建 `artifact_id`，并以 `derived_from[]` 直接关联已获律师批准的当前初稿。

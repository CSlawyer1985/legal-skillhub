# DOCX 与 OOXML 质量门

## 目录

- 一、完成标准
- 二、输入保全
- 三、真实修订与批注
- 四、历史修订策略
- 五、结构与兼容性门
- 六、接受/拒绝修订门
- 七、渲染与人工检查
- 八、失败闭环

## 一、完成标准

执行器生成文件只表示生产步骤结束。最终审阅件同时通过结构、语义视图和渲染检查后，才可交付。

强制产物：

- 原件哈希和工作副本；
- 审阅件；
- 接受全部修订副本；
- 拒绝全部修订副本；
- 质量门 JSON；
- review plan 与执行日志；
- 最终渲染 PNG；
- 对每页的人工检查记录。

## 二、输入保全

- 不覆盖原始 DOCX。
- 先记录 SHA-256、文件大小、页数、已有修订和批注数量。
- 临时解包目录使用唯一目录；输出路径不得与输入相同。
- 处理历史修订前，另存原件和所选基线视图。

## 三、真实修订与批注

真实修订至少满足：

- 插入使用 `w:ins`，删除使用 `w:del`；
- 删除文本使用 `w:delText`；
- 修订 `w:id` 不冲突，并含作者和时间；
- `word/settings.xml` 正确启用修订跟踪；
- 修订不得非法嵌套。

真实批注至少满足：

- `word/comments.xml` 含唯一评论 ID；
- story part 中同时存在 start、end 和 reference 锚点；
- `word/_rels/document.xml.rels` 有 comments 关系；
- `[Content_Types].xml` 有 comments override；
- 现有批注被保留，除非用户明确要求移除；
- 批注作者、时间及可选扩展部件之间一致。

渲染通常不能证明批注存在，必须结构化校验。

## 四、历史修订策略

先检查目标是否落在历史修订内：

1. 目标位于普通 run，且可在不包裹已有修订的情况下局部修改：保留历史修订并实施新修订。
2. 目标跨越或落在历史 `w:ins/w:del`：默认拒绝直接改文，改用批注或人工升级。
3. 用户明确同意以接受历史修订后的清洁副本为工作底稿：生成清洁基线，在该副本上添加本轮修订，并在日志写明策略、源哈希和基线哈希。

不得在 `w:ins/w:del` 内再放新的 `w:ins/w:del`。不得静默吞掉历史修订。

## 五、结构与兼容性门

运行：

```bash
python scripts/docx_engine/quality_gate.py reviewed.docx \
  --original original.docx \
  --output-dir qa \
  --visual-policy allow-structural
```

质量门检查：

- ZIP 完整性及重复成员；
- 所有 `.xml` 和 `.rels` 可解析；
- XML 声明只使用合规 UTF-8/UTF-16，不出现 ASCII 声明；
- 必需部件存在；
- 每个关系文件的 Id 唯一，内部 target 可解析到实际部件；
- comments relationship、content types 和锚点闭环；
- 修订和批注 ID 唯一；
- 接受/拒绝副本不残留修订节点；
- 原件与拒绝视图、接受视图与计划预期可比较；
- 所有失败以非零退出码和结构化 finding 输出。

XML 可解析不等于 Word 可用，关系和渲染仍是独立门。

## 六、接受/拒绝修订门

接受视图：保留正常内容、`w:ins` 和 `w:moveTo`，排除 `w:del` 和 `w:moveFrom`。
拒绝视图：保留正常内容、`w:del` 和 `w:moveFrom`，排除 `w:ins` 和 `w:moveTo`；删除文本须恢复为普通文本。

两份副本生成后重新运行 ZIP/XML/关系检查并确认修订计数为零。

无历史修订的输入，拒绝副本的正文语义应恢复原件。采用“接受历史修订清洁副本”策略时，拒绝本轮修订后的语义应恢复所记录的清洁基线，而不是伪称恢复历史最初版本。

## 七、渲染与人工检查

质量门在找到 LibreOffice、`pdfinfo` 和 `pdftoppm` 时会自动生成 PDF 和逐页 PNG。也可在需要时使用 documents 技能的 `render_docx.py` 复核：

```bash
env TMPDIR=/private/tmp python render_docx.py reviewed.docx --output_dir qa/render-reviewed --emit_pdf
env TMPDIR=/private/tmp python render_docx.py qa/accepted.docx --output_dir qa/render-accepted
env TMPDIR=/private/tmp python render_docx.py qa/rejected.docx --output_dir qa/render-rejected
```

逐页检查：

- 页面数及异常空白页；
- 裁切、重叠、缺字、字体替代；
- 表格边界、分页、页眉页脚和编号；
- 修订区域附近的空格、标点和段落重排；
- 接受版是否仍有红线，拒绝版是否缺字；
- 审阅件与原件的非目标格式差异。

LibreOffice 通过只证明该引擎下的可加载和渲染。未做 Microsoft Word GUI 实机测试时，明确标注“Word 实机未验证”。

无渲染命令时，`--visual-policy allow-structural` 可返回 `STRUCTURAL_ONLY` 并继续执行，但必须标注“结构验证版”，不得冒充视觉终版。`--visual-policy require` 则把缺失渲染环境视为硬失败。

## 八、失败闭环

- 任一硬门失败即阻断对外交付；
- quality gate 不读取执行器自写的 `PASS`，而是重新打开最终文件；
- finding 记录部件、ID、预期、实测和修复建议；
- 修复后生成新轮次目录，不覆盖失败产物；
- 旧失败成为回归 fixture，包括 ASCII 声明、跨 run 定位、歧义匹配、历史修订嵌套和断裂评论锚点。

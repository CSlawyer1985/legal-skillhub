# 排版规范与生成管线（format-spec）

本文件规定主报告 Word 与附件 PDF 的排版标准及可复用的生成方法。排版基线为律所尽调报告通行版式（参考范本：国浩系尽调报告）。

## 1. Word 主报告排版标准

| 元素 | 规范 |
|------|------|
| 正文中文字体 | 宋体（eastAsia），西文 Times New Roman |
| 正文字号/行距 | 小四 12pt；**行距 1.5 倍**；两端对齐；**首行缩进 2 字符**（用 `w:ind firstLineChars="200"`，不要用固定磅值，保证随字号缩放） |
| 一级标题 | 「第X部分：XXX」四号 14pt 宋体加粗、居中 |
| 二级标题 | 「一、XXX」小四 12pt 加粗、左对齐 |
| 三级标题 | 「（一）XXX」小四 12pt 加粗、左对齐 |
| 表格 | 五号 10.5pt（与正文字体区分）；**行距 1.2 倍**；0.5pt 细黑边框网格；表头加粗浅灰 #F2F2F2；表格内段落不缩进 |
| 目录 | Word TOC 域：`TOC \o "1-3" \h \z \u`（\h 生成超链接可点击跳转），并在 settings.xml 加 `<w:updateFields w:val="true"/>` 使打开时自动更新页码；目录标题自身用普通样式（不套 Heading，避免目录收录自己） |
| 封面 | 居中版式，无页码（独立 page 模板） |
| 页脚 | 页码居中 9pt |

## 2. Word 生成管线（两条路线）

**路线 A（已有 HTML 中间产物）**：HTML → html-to-docx 转换器 → `scripts/polish_docx.py` 后处理。转换器会近似处理字体行距（常见偏差：eastAsia 字体落到 Times、行距 1.275 非 1.5、表格行距未调），polish 脚本统一校正。
**路线 B（从 docx 直接编辑）**：python-docx 直接改样式与段落属性，同样以 polish 脚本的逻辑为准。

### polish_docx.py 做什么（使用 `scripts/polish_docx.py <docx路径>`）
1. Normal 样式：宋体＋Times New Roman、12pt、1.5 倍行距、两端对齐、段前段后 0；
2. Heading 1/2/3 样式：宋体加粗黑色、14/12/12pt；
3. 按正则把段落挂接标题样式（`^第[一二三四五六七八九十]+部分`→H1 居中、`^[一二三四五六七八九十]+、`→H2、封面短句排除）；
4. 全部正文段落统一首行缩进 2 字符（firstLineChars=200，移除旧 ind）；封面与标题不缩进；
5. 所有表格：单元格 10.5pt、1.2 倍行距、宋体、去缩进；
6. 在「目 录」标题后插入 TOC 域（dirty=true）＋ settings updateFields。

## 3. 附件 PDF 生成管线（用 `scripts/build_evidence_pdf.py`）

**环境结论（重要）**：本机 macOS 沙箱下 Chrome headless 打印 PDF 不可用（GPU/sandbox fatal，exit 133/137），无 weasyprint/pango/brew/LibreOffice。**可靠方案是 reportlab platypus**，中文字体直接注册系统字体：
- `/System/Library/Fonts/Supplemental/Songti.ttc`：subfontIndex=6 → Songti SC Regular（正文），subfontIndex=1 → Songti SC Bold（标题加粗）。

**关键实现要点（踩坑记录）**：
- 可点击目录＋页码：`TableOfContents` ＋ 自定义 DocTemplate 的 `afterFlowable` 中 `notify('TOCEntry', (level, text, page, key))`；**key 必须跨 multiBuild 各轮稳定**（用标题文本的 md5，不能用递增计数器，否则目录不收敛报 "Index entries not resolved"）；
- PDF 书签：`canvas.bookmarkPage(key)` ＋ `addOutlineEntry(text, key, level)`；
- 页脚页码：PageTemplate 的 onPage 回调绘制「第 X 页」；
- 表格行不跨页：`Table(..., repeatRows=1, splitByRow=1)`（按行拆分、重复表头）；
- 统一黑白灰：表头 #F2F2F2、0.5pt 黑边框，全文不用彩色；
- 每部分前分页：H1 样式 `pageBreakBefore=1`；
- 二级标题与正文首行缩进 2 字符：ParagraphStyle `firstLineIndent=24`（12pt 字号的 2 倍）。

**附件内容结构**（固定）：封面 → 编制说明与使用指引（含模块↔主报告位置↔Fact ID 对应表＋标注体例）→ 目录 → 模块一至七（高×3／中×3／储备×1，每模块：对应关系与衔接逻辑→核心事实要点→证据材料清单表→访谈建议→待核实事项）→ 附录A 证据材料总索引 → 附录B 已存证原始文件清单 → 附录C 待核实事项汇总清单 → 免责声明。

模块数量按实际调查结果伸缩（3—9 个均可），但"高优先级居前、每模块五段式体例、三向对应表"不可省略。

## 4. 迭代纪律（用户既有决策，新增任务沿用）

首轮只做：格式规范调整＋章节合并；不做整体结构重构。格式调整与内容迭代分开交付；基于现有版本修改，改前确认用户认可的版式基线。

# Docx 输出格式约束（NDR 系统一底座）

本技能输出 `.docx` 时，Agent 须按以下步骤执行：

1. 将生成内容组织为 `content_blocks` 列表
2. 调用 `format_docx.py` 的 `create_document()`：

   ```python
   import sys, os
   sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '非争议解决公共标准', 'references'))
   from format_docx import create_document
   create_document(content_blocks, meta={'doc_type': 'xxx', 'party': '...', 'matter': '...', 'date': '...'})
   ```

3. 格式常量（页边距 2.54/3.18cm、行距 1.5、正文字体 仿宋_GB2312 12pt、标题 黑体、日期中文大写）由 `format_base.py` 单一事实来源控制，禁止在 content_blocks 中另行指定

content_blocks schema:
  `[{type: 'title'|'body'|'body_ni'|'section'|'signature'|'blank', text: str|list, attrs: dict}]`

> 注意：合规审查 技能引用 `../baichen-ndr-standard/references/format_docx.py`（NDR 系），其余 DR 系技能引用 `../争议解决公共标准/references/format_docx.py`。

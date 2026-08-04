# OOXML 批注注入技术参考

> 本文档集中记录专利审查 Skill 中涉及的 OOXML 操作要点，供开发调试时参考。

---

## 1. 核心命名空间

| 前缀 | URI | 用途 |
|:-----|:----|:-----|
| `w` | `http://schemas.openxmlformats.org/wordprocessingml/2006/main` | 文档主体 |
| `r` | `http://schemas.openxmlformats.org/officeDocument/2006/relationships` | 关系引用 |
| `wp` | `http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing` | 绘图对象 |

---

## 2. 批注注入模型

### 2.1 涉及的 XML 部件

| 部件 | 路径 | 作用 |
|:-----|:-----|:-----|
| document.xml | `word/document.xml` | 文档主体，包含 `commentRangeStart`/`commentRangeEnd`/`commentReference` 标记 |
| comments.xml | `word/comments.xml` | 批注内容定义（`w:comment` 元素） |
| commentsExtended.xml | `word/commentsExtended.xml` | 批注扩展数据（时间戳等） |
| commentsIds.xml | `word/commentsIds.xml` | 批注唯一标识映射 |
| commentsExtensible.xml | `word/commentsExtensible.xml` | 批注可扩展数据 |
| people.xml | `word/people.xml` | 批注作者信息 |

### 2.2 批注在 document.xml 中的结构

```xml
<w:p>
  <w:commentRangeStart w:id="1"/>
  <w:r>
    <w:t>被批注的文本</w:t>
  </w:r>
  <w:commentRangeEnd w:id="1"/>
  <w:r>
    <w:rPr>
      <w:rStyle w:val="CommentReference"/>
    </w:rPr>
    <w:commentReference w:id="1"/>
  </w:r>
</w:p>
```

### 2.3 批注在 comments.xml 中的结构

```xml
<w:comments>
  <w:comment w:id="1" w:author="作者名" w:date="2026-05-16T10:00:00Z" w:initials="ZZ">
    <w:p>
      <w:pPr><w:pStyle w:val="CommentText"/></w:pPr>
      <w:r>
        <w:rPr><w:rStyle w:val="CommentReference"/></w:rPr>
        <w:annotationRef/>
      </w:r>
      <w:r>
        <w:t>批注内容</w:t>
      </w:r>
    </w:p>
  </w:comment>
</w:comments>
```

---

## 3. 修订追踪注入模型

### 3.1 替换操作（replace）

```xml
<w:p>
  <w:del w:id="2" w:author="作者名" w:date="2026-05-16T10:00:00Z">
    <w:r>
      <w:rPr><w:del w:id="3"/></w:rPr>
      <w:delText xml:space="preserve">旧文本</w:delText>
    </w:r>
  </w:del>
  <w:ins w:id="4" w:author="作者名" w:date="2026-05-16T10:00:00Z">
    <w:r>
      <w:t>新文本</w:t>
    </w:r>
  </w:ins>
</w:p>
```

### 3.2 删除操作（delete）

```xml
<w:p>
  <w:del w:id="5" w:author="作者名" w:date="2026-05-16T10:00:00Z">
    <w:r>
      <w:delText xml:space="preserve">要删除的文本</w:delText>
    </w:r>
  </w:del>
</w:p>
```

---

## 4. 常见失败模式

| 失败模式 | 原因 | 解决方案 |
|:---------|:-----|:---------|
| context 未找到 | Agent 输出的 context 与文档实际文本有微小差异 | 使用 `PatentAnalyzer` 生成多关键词搜索 |
| 修订冲突 | 同一段落内多个 replace 操作的 del/ins 标记交叉 | `merge_reviews.py` 中检测并解决冲突 |
| occurrence 失效 | old_text 在 context 中出现多次且 occurrence 指定错误 | 高频词改用 comment 类型 |
| XML 解析崩溃 | 文本字段包含非法字符（控制字符、未转义引号） | `common-specs.md` 0.2 节约束 |
| 批注 ID 冲突 | 新增批注 ID 与已有批注 ID 重复 | `review_adder.py` 自动计算最大 ID |
| 段落数量变化 | replace/delete 操作改变了段落数 | `verify.py` 检测段落数变化 |

---

## 5. 批注作者名编码

本 Skill 使用批注作者名编码问题严重程度，用户可在 Word 中按作者筛选查看：

| 作者名 | 严重程度 | 筛选效果 |
|:-------|:---------|:---------|
| 格式问题 | 格式性问题 | 查看所有格式类批注 |
| 实质问题 | 实质性问题 | 查看所有实质类批注 |
| 严重问题 | 根本性缺陷 | 查看所有严重类批注 |

严重程度由 `review_adder.py` 中的 `_classify_severity()` 函数根据 issue 内容自动判定。

---

## 6. 打包/解包流程

```
.docx 文件
    ↓ unpack.py (zipfile)
unpacked/ 目录
    ├── [Content_Types].xml
    ├── _rels/
    ├── word/
    │   ├── document.xml      ← 主要操作目标
    │   ├── comments.xml      ← 批注内容
    │   ├── commentsExtended.xml
    │   ├── commentsIds.xml
    │   ├── commentsExtensible.xml
    │   ├── people.xml
    │   └── ...
    └── ...
    ↓ 修改 XML
    ↓ pack.py (zipfile)
审查后 .docx 文件
```

---

## 7. 关键脚本调用关系

```
review_adder.py
├── doc_converter.py (ensure_docx: .doc → .docx)
├── patent_analyzer.py (PatentAnalyzer: 文本提取 + 多关键词搜索)
├── error_handling.py (AnnotationBatchLogger: 批注日志)
├── document.py (Document: OOXML 文档操作)
│   ├── ooxml/scripts/unpack.py
│   └── ooxml/scripts/pack.py
└── ooxml/scripts/validation/ (文档验证)

workflow.py
├── error_handling.py (check_python_version, 异常类)
├── merge_reviews.py (合并去重)
├── review_adder.py (批注添加)
├── format_json.py (JSON格式化)
└── verify.py (内容完整性验证)

report_renderer.py
└── python-docx (DOCX报告生成)
```

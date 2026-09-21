# OOXML 修订标记规则速查（失败模式手册）

生成 tracked-changes docx 时必须遵守的硬规则。脚本 `compare_docx_tracked.py` 已实现全部规则；仅当脚本需要修补或需要手工排查时阅读本文件。

## 目录
1. 修订元素语法
2. 段落级 vs 行内修订
3. 包级要求
4. 已知失败模式

## 1. 修订元素语法

```xml
<w:ins w:id="12" w:author="Name" w:date="2026-08-15T00:00:00Z">
  <w:r><w:t>newly added text</w:t></w:r>
</w:ins>
<w:del w:id="13" w:author="Name" w:date="2026-08-15T00:00:00Z">
  <w:r><w:delText xml:space="preserve">removed text</w:delText></w:r>
</w:del>
```

- `w:id` 必须全局唯一且递增。
- `<w:del>` 内的文本节点**必须**是 `<w:delText>`（不是 `<w:t>`），并保留 `xml:space="preserve"`。递归转换整棵子树。
- `<w:ins>`/`<w:del>` 包裹完整的 `<w:r>`，不得放在 `<w:r>` 内部。
- 不得出现 ins/del 互相嵌套。

## 2. 段落级 vs 行内修订

**整段插入/删除**：除包裹所有内容 run 外，还必须标记段落标记本身（否则 Word 里会留下空行或不显示为整段增删）：

```xml
<w:p>
  <w:pPr>
    <w:rPr><w:del w:id="14" w:author="Name" w:date="..."/></w:rPr>
  </w:pPr>
  <w:del ...><w:r><w:delText xml:space="preserve">...</w:delText></w:r></w:del>
</w:p>
```

`w:pPr/w:rPr` 中 ins/del 标记必须是 `rPr` 的第一个子元素。

**行内词级修订**：在新段落内按词级 diff 拆分 run；删除片段生成带 `<w:delText>` 的新 run（继承最近可见的 `rPr` 格式），插入片段包 `<w:ins>`。

**复杂块回退**：含图片、`m:oMath` 公式、超链接等"原子"元素且 diff 边界无法对齐时，整段回退为"删旧段 + 插新段"，不要强行拆 run。

## 3. 包级要求

- `word/settings.xml` 加入 `<w:trackChanges/>`，位置在 `<w:doNotTrackMoves>` 之前（无则放 `<w:defaultTabStop>` 前，再无则追加）。
- 被删段落深拷贝自旧文档：剥除 `w:bookmarkStart/End`、`w:proofErr`、`w:permStart/End`（避免 id 冲突）。
- 旧段落中的 `r:id` / `r:embed` / `r:link` 必须重映射到新包的 rels；图片部件按需复制（前缀 `tracked_` 防重名）。
- zip 其余部件原样拷贝。

## 4. 已知失败模式

| 症状 | 原因 | 修法 |
|---|---|---|
| Word 打开报"无法读取的内容" | `<w:del>` 内残留 `<w:t>`；或 id 重复；或 r:id 悬空 | 跑 `verify_tracked.py` 定位 |
| 删除段落在 Word 中显示为空行 | 段落标记未标 del（缺 `pPr/rPr/del`） | 见第 2 节 |
| 修订显示但"拒绝修订"后文本不对 | 段落边界标记被误判（验证脚本需把 pPr/rPr 内的 ins/del 视为段落级标记） | 用 `verify_tracked.py` 的 accept/reject 模拟核对 |
| 修订未显示（文档看似干净） | settings.xml 缺 `w:trackChanges` | 见第 3 节 |
| 引用旧版图片的删除段落图片丢失 | rId 未重映射 / media 未复制 | 见第 3 节 |

# disclosures/——律师意见披露包

一个 AI 披露语言起步库，与特定律师意见或指导文件对应。当 `matter.yml` 设置 `ethics.disclosure_pack: <code>` 时，CLI 会引用这些文件。

## 律师核验契约

**每个包条目都附带 `verified: false`。** 这是有意的。本仓库的维护者不是您的律师协会纪律顾问。我们汇编起步语言和引用作为研究辅助——而非关于您所在司法辖区规则实际要求什么的法律意见。

在依赖任何包条目之前：

1. 打开 `source_url` 并亲自阅读该意见。
2. 确认引用、日期和范围仍然准确（意见可能被撤回、修订或取代）。
3. 调整 `canonical_disclosure_text` 以适合您的事项和您客户的委托函。
4. 将 `verified: true` 翻转，并添加您自己的 `verified_by` 行，附您的律师协会 ID 和核验日期。

如包条目显示 `verified: false` 且您以 `--strict` 运行 CLI，工具将拒绝生成最终产物，直到您完成功课。

## 模式

```yaml
code: <slug，必须与文件名匹配>
jurisdiction: <可读标签，例如“ABA Model”、“FL”、“CA”、“NY-City”>
opinion: <引用，例如“ABA Formal Opinion 512”>
date: <意见的 YYYY-MM-DD>
source_url: <意见文本的永久 URL>
verified: false # 阅读意见后翻转为 true
verified_by: ~ # 您的律师协会 ID + 日期，例如“CT-12345, 2026-05-18”
canonical_disclosure_text: |
  <一段保守的披露文字，您愿意在该司法辖区的每张账单上使用。综合而非引用，除非意见强制要求特定语言。>
notes: |
  <意见实际涵盖什么、它不强制要求什么，以及任何陷阱。这是维护者的研究注释——须对照来源核验。>
billing_rules_summary: |
  <关于意见对费用、加价和计时记录说法的段落。不能替代阅读意见。>
```

## `matter.yml` 如何使用包

```yaml
ethics:
  ai_disclosure_required: true
  disclosure_pack: aba-512 # 加载 disclosures/aba-512.yml
  disclosure_text:
    ~ # 可选：律师覆盖。如设置，
    # 为本事项覆盖包的规范文本。
```

CLI 输出：

- 产物证据链部分中的包代码和 SHA-256。
- 包的 `verified` 标志（如为 `false` 则警告）。
- 每个条目实际使用的有效披露文本。

在 `--strict` 模式下，CLI 在以下情形拒绝生成最终产物：

- 包引用无效。
- 包为 `verified: false` 且 `matter.yml` 未覆盖文本。
- 有效披露文本为空、为 `TODO` 或匹配占位符模式。

## 本包**不是**什么

- **不是**法律意见。
- **不是**每个司法辖区 AI 规则的权威清单。
- **不是**阅读您所引用意见的替代品。
- **不**自动更新——律师协会规则会变化；欢迎提交引用更新的拉取请求。

## 贡献一个司法辖区

1. 打开意见，获取引用和永久 URL。
2. 依模式添加 `disclosures/<slug>.yml`。
3. **保持 `verified: false`**，除非您是该律师协会会员且已亲自阅读并核验意见文本。
4. 添加 `notes` 段落，区分意见强制要求的内容与您的 `canonical_disclosure_text` 综合的内容。
5. 打开拉取请求。维护者不会为您翻转 `verified: true`——这是每位用户依其自身律师协会入会情况的责任。

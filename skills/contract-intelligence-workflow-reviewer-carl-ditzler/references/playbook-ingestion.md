# 剧本导入

每当用户通过上传或云源提供剧本、条款库、标准模板或备用立场时，使用本文件。

## 接受的输入

允许：

- 直接文件上传
- 指向特定文件的经批准云源链接
- 指向特定文件的经批准连接器路径或标识符

首选来源类型，按顺序：

1. 现有 Markdown 或纯文本
2. DOCX
3. 结构化 XLSX 或 CSV
4. 文本 PDF
5. 扫描 PDF

## 核心规则

当文件系统保存可用时，不要单独使用原始源文件作为剧本的真相来源。

尽可能创建并维护全部三层：

- 元数据中的原始源文件引用
- `source.md` 中的可读提取
- `normalized.yaml` 中的规范结构化版本

模型应主要依据以下内容推理：

- `normalized.yaml` 用于条款比较和评分
- `source.md` 用于细微差别、核验和提取回退

## 必需的用户问题

询问用户：

- 您要上传剧本文件还是连接经批准的云源？
- 哪个文件是控制性剧本？
- 原始源文件可以复制到本地，还是仅应存储派生的文本和元数据？
- 如果剧本在云源中，哪个特定文件或路径应控制？
- 如果存在多个剧本，哪一个具有优先权？

## 保存结构

将剧本保存在：

```text
.contract-review/playbooks/<playbook-slug>/
  metadata.yaml
  source.md
  normalized.yaml
```

如果允许本地文件副本，也在元数据中记录原始本地或远程源路径。

## 元数据要求

在 `metadata.yaml` 中记录：

```yaml
playbook_metadata:
  playbook_name: ""
  source_type: "upload|connector|link|local"
  source_format: "md|txt|docx|xlsx|csv|pdf|unknown"
  connector_alias: ""
  source_identifier: ""
  original_file_local_copy_allowed: false
  extraction_method: ""
  extraction_confidence: "high|medium|low"
  normalized_at: ""
  notes: []
```

## 提取规则

- 尽可能将可读源转换为 Markdown。
- 保留标题、条款名称、表格和备用语言结构。
- 如果源表格无法干净表示，将其改写为 Markdown 章节，不改变实质内容。
- 如果提取质量较弱，降低置信度并警告用户。

## 置信度规则

- `High`（高）：源为 Markdown、文本、DOCX 或歧义极小的干净结构化表格
- `Medium`（中）：源可读，但格式或表格结构部分退化
- `Low`（低）：源为扫描件、重度 OCR 或实质性歧义

如果提取置信度为 `Low`（低），告知用户剧本应被审查或用更干净的来源替换。

## 云源规则

- 仅使用经批准的连接器或经批准的共享链接。
- 记录准确的来源出处。
- 如果用户已将来源限制得更窄，不要假设文件夹级批准意味着文件级批准。

## 规范化规则

提取 Markdown 后，在用于偏差评分之前，将剧本规范化为结构化 YAML。

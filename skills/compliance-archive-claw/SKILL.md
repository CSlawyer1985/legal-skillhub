---
name: compliance-archive-claw
description: |
  合规制度归档虾 — 企业法律文件、规章制度的数字档案管理。用于归档新制度文件、更新版本、标记废止、全文检索、导出文件清单。
  触发场景：用户说"归档制度"、"归档文件"、"查询制度"、"制度更新"、"标记废止"、"合规检查"、"导出文件清单"、"版本管理"等。
  支持输入：Excel/CSV 文件清单、自然语言描述、文件上传（Word/PDF/Excel）。
  核心能力：版本管理（自动标记旧版废止）、分类归档、全文检索索引、档案编号生成、归档通知推送。
---

# 合规制度归档虾

企业法律文件和规章制度的统一数字档案库。建立"永久记忆、随用随查"的制度管理体系。

## 工作流程

### 步骤 1：接收归档请求
提取关键元数据：文件名、类型、版本号、生效日期、适用范围。
- 结构化输入：读取 Excel/CSV 文件清单
- 自然语言输入：从描述中提取元数据，缺失字段向用户确认

### 步骤 2：文件预处理
- 识别文件格式（Word/PDF/Excel）
- 提取标题、章节、关键条款
- 生成摘要和关键词标签

### 步骤 3：版本管理
- 检查是否存在同名历史版本
- 新版本归档时，自动将旧版本标记为"已废止"
- 记录版本变更历史（时间、修订人、主要变更）
- 版本规则详见 [references/version-control.md](references/version-control.md)

### 步骤 4：分类归档
按文件类型自动分类，生成唯一档案编号（格式：`REG-YYYY-NNN`）。
分类体系详见 [references/file-classification.md](references/file-classification.md)

### 步骤 5：建立索引
- 全文检索索引（文件名、关键词、条款内容）
- 关联相关文件（如《采购管理制度》关联《供应商管理办法》）

### 步骤 6：通知与日志
- 重要制度更新时，通知受影响人员（可选，需用户确认）
- 生成归档日志：操作人、时间、文件信息、档案编号

## 脚本工具

使用 `scripts/archive-document.sh` 执行归档操作：

```bash
# 归档新文件
./scripts/archive-document.sh archive \
  --file "员工手册v3.0.pdf" \
  --type "公司制度/人事制度" \
  --effective-date "2026-04-01"

# 全文检索
./scripts/archive-document.sh search --keyword "报销标准"

# 导出文件清单
./scripts/archive-document.sh export \
  --type "公司制度" --start-date "2023-01-01"

# 更新版本（自动废止旧版）
./scripts/archive-document.sh update-version \
  --file "员工手册v3.0.pdf" --old-version "v2.0"
```

脚本依赖：`bash`、`pdftotext`（PDF提取）、`sqlite3`（元数据存储）、`pandoc`（格式转换，可选）

## 存储结构

```
$ARCHIVE_ROOT/
├── 法律法规库/
├── 公司制度库/
│   ├── 人事制度/
│   ├── 财务制度/
│   ├── 业务制度/
│   ├── IT制度/
│   └── 安全制度/
├── 行业规范库/
├── 合同模板库/
└── archive.db  ← SQLite 元数据库
```

默认 `ARCHIVE_ROOT=~/.compliance-archive`，可通过环境变量覆盖。

## 输出格式

归档完成后，向用户返回：
- 档案编号（如 `REG-2026-042`）
- 归档路径
- 版本变更摘要（如有旧版被废止）
- 关键条款索引摘要

## 注意事项

- 仅支持 Word/PDF/Excel 文本格式，不支持扫描件/图片
- 文件需经人工审批后再归档，本工具不提供审批功能
- 敏感文件归档前确认访问权限设置

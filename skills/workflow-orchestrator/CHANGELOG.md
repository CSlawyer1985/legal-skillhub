# Changelog

## [1.3.0] - 2026-06-01
### 修改
- 开源适配：去除"杜律师/粽宝/案件云/金山文档云盘"等私有引用，改为通用表述
- 案件云相关功能标记为"可选"
- OCR 策略中硬编码路径改为环境变量占位符
- 知识库引用改为通用"用户知识库"


## [1.2.1] - 2026-05-31
### 修复
- 路由表 legal-debate-simulation / legal-evidence-mapping 补全 -mctmilk 后缀，修复路由名称不匹配

# Changelog

## [1.3.0] - 2026-06-01
### 修改
- 开源适配：去除"杜律师/粽宝/案件云/金山文档云盘"等私有引用，改为通用表述
- 案件云相关功能标记为"可选"
- OCR 策略中硬编码路径改为环境变量占位符
- 知识库引用改为通用"用户知识库"


## [1.2.0] - 2026-05-31
### 修改
- 路由表：具体法条问题路由目标从 analyze-legal-issues 改为 process-cases
- 架构图移除 analyze-legal-issues 节点
- description 去除 analyze-legal-issues 引用

## [1.1.0] - 2026-05-30
### 新增
- OCR 预处理链路：references/ocr-strategy.md，定义百度 OCR / MinerU / PaddleOCR 三级策略与兜底逻辑
- 流程一新增步骤 0（OCR 预处理），步骤 2 补充策略分析五要素模板，步骤 3 补全文书类型清单，步骤 4 增加修改循环（≤3 轮）
- 流程二新增步骤 0（OCR 预处理），步骤 1 增加日志不存在兜底规则
- 路由表新增：意图不明→追问、证据梳理→legal-evidence-mapping

### 修改
- SKILL.md 流程详情拆至 references/flow-01-new-case.md、flow-02-existing-case.md
- 路由表各条目标注 OCR 预处理环节

## [1.0.0] - 2026-05-30
### 新增
- CHANGELOG.md、LICENSE.txt 补齐
- SKILL.md 新增 Frontmatter（author / version / license）、负向条件、功能概述、调用方式

### 修改
- description 改为第三人称 + 负向条件，对齐 SKILL-DEV-GUIDE

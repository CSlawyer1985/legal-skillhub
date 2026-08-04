# Changelog

## v1.0.1 (2026-04-20)

### Fixed
- **飞书推送集成文档**: 修复 SKILL.md 中 `send_risk_report`  typo（应为 `send_feishu_notification`）
- **飞书推送集成**: 明确说明 agent 需使用 `feishu_im_user_message` 工具发送飞书卡片
- **优雅降级**: 添加飞书通知失败时的降级处理指南（只输出本地报告，不报错）
- **Token 验证说明**: 明确 `CONTRACT-*` 前缀验证由 yk global 服务端处理，skill 端不做本地验证

### Note
- Token 前缀检查（CONTRACT-*）由 yk global 后端服务验证，本 skill 不做重复验证
- 飞书通知需要用户授权，无授权时自动降级为本地报告输出

## v1.0.0 (2026-04-20)

### Added
- Initial release of Contract Risk Analyzer skill
- PDF text extraction using PyMuPDF + pdfplumber
- Automatic contract type detection (6 types)
- AI-powered structured field extraction
- Risk annotation with 🔴🟠🟡三级分级
- Markdown risk report generation
- Feishu message card notification support
- Excel report data export
- Comprehensive test suite (24 tests)

### Supported Contract Types
- 采购合同 (Purchase Contract)
- 销售合同 (Sales Contract)
- 服务合同 (Service Contract)
- 劳动合同 (Labor/Employment Contract)
- 租赁合同 (Lease Contract)
- 保密协议 (Confidentiality/NDA)

### Risk Categories
- 20+ predefined risk items across 3 severity levels
- Industry-standard risk checklist
- Actionable suggestions for each risk

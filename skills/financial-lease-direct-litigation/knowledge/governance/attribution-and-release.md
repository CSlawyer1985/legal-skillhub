---
title: 署名与发布门禁
created: 2026-07-13
updated: 2026-07-14
type: governance
lane: public
source_status: reviewed_methodology
privacy_status: reviewed
attribution: 李时瑀律师
---

# 署名与发布门禁

## 唯一署名

公开、商业、评审或未来发布材料的作者署名仅允许使用“李时瑀律师”。不得出现作者所在机构名称或可识别该机构的片段。

## 禁止内容

- 客户、关联方及交易相对方的真实名称；
- 证件、电话、地址、账号等身份或联系信息；
- 案号、合同号、设备号、流水号；
- 签名、印章、二维码和扫描页图像；
- 可反向识别的精确金额与日期组合；
- 本地绝对路径、身份映射、源文件映射、源指纹和案件正文；
- 匿名案件编号及本地法源锚点。
- DOCX 批注、修订、隐藏文字、嵌入附件和额外作者元数据。

## 发布前检查

1. 确认内容仅属于普通直租公共范围。
2. 运行 `scripts/validate-release.py`，复核隐私、路径、标识符、署名、版本、链接和校验和。
3. 检查三份 DOCX 模板的 OOXML、元数据、A4 纸型和渲染结果。
4. 核对法律命题的证据状态，未核验内容保持 `pending_current_text_verification` 或 `unsupported_hold`。
5. 检查免责声明、版本信息、清单和 ZIP 解压结果。
6. 取得最终许可证以及对具体发布目标和动作的另行授权。

本地 Wiki 初始化和本地索引不等于 GitHub、技能商店或其他外部发布授权。

## 关联

- [[SCHEMA|知识库结构]]
- [[governance/public-private-boundary|公私边界]]
- [[authorities/legal-authority-boundary|法律依据门禁]]

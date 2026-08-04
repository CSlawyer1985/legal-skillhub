# 金融营销合规助手 v2.0.0

**定位**：基于《金融产品网络营销管理办法》及 15+ 金融监管法规，提供金融产品营销内容合规审查和方案生成。

**合并说明**：由 `content-compliance`（v1.0.0）和 `finance-marketing-compliance`（v1.0.0）合并而成，保留双方优势。

---

## 🎯 核心功能

| 功能 | 命令 | 说明 |
|------|------|------|
| 文章合规审查 | `compliance-checker.py review` | 审查营销文章合规性 |
| 营销方案审查 | `compliance-checker.py plan` | 审查营销方案合规性 |
| 分行业审查 | `compliance-checker.py industry` | 分行业专属审查 |
| 合规方案生成 | `compliance-checker.py generate` | 生成合规营销方案 |

---

## 📦 依赖

- Python 3.6+
- 无第三方依赖

---

## 🚀 快速开始

### 文章合规审查
```bash
python3 scripts/compliance-checker.py review \
  --content "XX 银行高收益存款产品推荐：年化收益 5.8%，保本保息，限时抢购！" \
  --product-type "存款"
```

### 营销方案审查
```bash
python3 scripts/compliance-checker.py plan \
  --plan "通过公众号推文推荐 XX 基金，使用低风险高收益表述，附购买链接" \
  --channel "公众号" \
  --product-type "基金"
```

### 合规方案生成
```bash
python3 scripts/compliance-checker.py generate \
  --product-type "存款" \
  --target-audience "30-50 岁工薪族" \
  --channel "微信公众号" \
  --selling-points "年化收益 3.5%，期限灵活"
```

---

## 📁 项目结构

```
finance-marketing-compliance/
├── SKILL.md              ← 技能定义
├── README.md             ← 本文件
├── scripts/
│   └── compliance-checker.py  ← 合规检查脚本
├── references/
│   ├── regulations.md    ← 法规知识库
│   └── rules.md          ← 审查规则库
└── templates/
    └── review-report.md  ← 审查报告模板
```

---

## 📚 法规依据

### 核心法规
- 《金融产品网络营销管理办法》（2026 年 9 月 30 日实施）

### 相关法规
- 《中华人民共和国广告法》
- 《中华人民共和国证券法》
- 《中华人民共和国保险法》
- 《中华人民共和国证券投资基金法》
- 《中华人民共和国个人信息保护法》
- 《中华人民共和国数据安全法》
- 《防范和处置非法集资条例》
- 《网络数据安全管理条例》

---

## ⚠️ 注意事项

1. **法规时效性**：始终使用最新法规版本
2. **违规判断**：标注具体违规条款，说明原因
3. **产品类型差异**：根据产品类型选择对应规则
4. **免责声明**：本工具仅供参考，不构成法律意见

---

*版本：1.0.0 | 最后更新：2026-04-24*

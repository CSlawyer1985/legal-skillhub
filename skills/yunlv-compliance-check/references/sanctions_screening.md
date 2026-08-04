# 制裁名单筛查指南

## 一、制裁名单类型

### 主要制裁名单
| 名单名称 | 发行机构 | 覆盖范围 | 更新频率 |
|---------|---------|---------|---------|
| SDN List | 美国OFAC | 个人/实体/船舶 | 即时更新 |
| EU Sanctions List | 欧盟理事会 | 个人/实体/货物 | 周更新 |
| UN Security Council | 联合国 | 国家/实体 | 视决议而定 |
| UK Sanctions List | 英国FCDO | 个人/实体 | 月更新 |

### 行业特定名单
| 名单名称 | 适用范围 |
|---------|---------|
| BIS Entity List | 美国出口管制实体 |
| BIS Denied Persons | 美国拒绝人员 |
| ITAR Debarred | 武器贸易管制 |

---

## 二、筛查维度

### 1. 直接筛查
- 公司全称（含缩写）
- 曾用名/别名
- 注册地址
- 实际控制人

### 2. 关联筛查
- 法定代表人
- 母公司/子公司
- 姐妹公司
- 同一控制人名下其他实体

### 3. 船舶筛查
- 船舶名称（含历史名称）
- IMO编号
- 船东公司
- 船舶国籍

---

## 三、高风险信号识别

### 🚨 红色信号（高风险）
- [ ] 公司名含制裁国家地名（如Iran, North Korea, Syria等）
- [ ] 注册地址在制裁国家
- [ ] 法定代表人来自制裁国家
- [ ] 曾用名与SDN名单相似

### 🟡 黄色信号（需深入调查）
- [ ] 名称与制裁名单高度相似
- [ ] 注册地址模糊（如仅写国家名）
- [ ] 公司成立时间较短
- [ ] 主营业务涉及敏感物项

---

## 四、筛查工具推荐

### 官方渠道
1. OFAC Sanctions Search: https://sanctionssearch.ofac.treas.gov/
2. EU Sanctions Map: https://www.sanctionsmap.eu/
3. UN Security Council: https://www.un.org/securitycouncil/sanctions/

### 商业工具
- Dow Jones Risk & Compliance
- LexisNexis World-Check
- Refinitiv World-Check

---

## 五、筛查记录要求

完成筛查后需记录：
```
{
  "screening_date": "YYYY-MM-DD",
  "screened_entity": "公司名称",
  "screening_type": ["OFAC", "EU", "UN"],
  "result": "CLEAR/FLAG/REVIEW_REQUIRED",
  "screener": "筛查人",
  "notes": "备注"
}
```

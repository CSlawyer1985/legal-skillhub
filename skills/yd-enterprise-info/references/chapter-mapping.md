# DD 章节 → yd-enterprise-info 子命令映射

> 本文件供 legal-due-diligence 在 draft 模式下快速定位应调用哪些子命令。
> 所有子命令数据存入 `<项目>/raw/chineselaw/` 后，draft 模式自动读取。

---

## 第 1 章：公司基本信息与主体资格

**核心关注**：营业执照、章程、变更登记、信用信息、经营异常

| 子命令 | 提供信息 | 优先级 |
|---|---|---|
| `base-info` | 登记基本信息、法人、注册资本、经营范围、经营状态 | 🔴 必调 |
| `change` | 历次变更记录（名称/法人/注册资本/经营范围等变更） | 🔴 必调 |
| `abnormal` | 经营异常列入/移出记录 | 🟡 建议调 |
| `serious-violation` | 严重违法记录 | 🟡 建议调 |

```bash
for cmd in base-info change abnormal serious-violation; do
  python3 scripts/yd_enterprise_info.py $cmd --tyshxydm <USCC> --output ./raw/ --yes
done
```

---

## 第 2 章：股权结构与股东信息

**核心关注**：股东名册、出资比例、股权质押/冻结

| 子命令 | 提供信息 | 优先级 |
|---|---|---|
| `base-info` | 股东信息（股东名称/类型/出资比例/认缴实缴） | 🔴 必调（与第1章共用） |
| `equity-pledge` | 股权出质登记记录 | 🔴 必调 |
| `equity-frozen` | 股权冻结记录 | 🔴 必调 |

```bash
for cmd in equity-pledge equity-frozen; do
  python3 scripts/yd_enterprise_info.py $cmd --tyshxydm <USCC> --output ./raw/ --yes
done
```

---

## 第 3 章：公司治理与组织结构

**核心关注**：治理架构、核心成员

| 子命令 | 提供信息 | 优先级 |
|---|---|---|
| `base-info` | 核心成员（姓名/职务）、分支机构 | 🔴 必调（与第1章共用） |

---

## 第 4 章：核心资产

**核心关注**：知识产权（商标/专利/软著/著作权）、网站备案

| 子命令 | 提供信息 | 优先级 |
|---|---|---|
| `brand` | 商标注册列表（名称/注册号/类别/有效期） | 🔴 必调 |
| `patent` | 专利列表（名称/类型/申请日/状态） | 🔴 必调 |
| `soft-right` | 软件著作权列表 | 🔴 必调 |
| `copyright-work` | 作品著作权列表 | 🟡 建议调 |
| `website` | 网站备案信息 | 🟡 建议调 |

```bash
for cmd in brand patent soft-right copyright-work website; do
  python3 scripts/yd_enterprise_info.py $cmd --tyshxydm <USCC> --output ./raw/ --yes
done
```

---

## 第 5 章：业务经营与合同管理

**核心关注**：主营业务、业务资质

> 元典接口对第 5 章覆盖有限，主要靠律师收集目标公司提供的合同、资质材料。
> 可参考 `base-info` 中的经营范围辅助。

---

## 第 6 章：财务与税务

**核心关注**：欠税记录

| 子命令 | 提供信息 | 优先级 |
|---|---|---|
| `tax-arrears` | 欠税公告（税种/金额/所属期） | 🟡 建议调 |

```bash
python3 scripts/yd_enterprise_info.py tax-arrears --tyshxydm <USCC> --output ./raw/ --yes
```

---

## 第 7 章：劳动人事管理

> 元典企业信息接口对第 7 章无直接覆盖，依赖律师收集劳动合同、社保记录等材料。

---

## 第 8 章：重大债权债务与担保

**核心关注**：对外担保、股权出质

| 子命令 | 提供信息 | 优先级 |
|---|---|---|
| `outbound-guarantee` | 对外担保记录 | 🔴 必调 |
| `equity-pledge` | 股权出质（与第2章共用） | 🔴 必调 |

```bash
python3 scripts/yd_enterprise_info.py outbound-guarantee --tyshxydm <USCC> --output ./raw/ --yes
```

---

## 第 9 章：诉讼、仲裁与行政处罚

**核心关注**：未决/已决案件、行政处罚、强制执行

| 子命令 | 提供信息 | 优先级 |
|---|---|---|
| `litigation-stat` | 涉诉多维度统计（总数/案件类别/案由/结案方式/地域等） | 🔴 必调（先看全貌） |
| `litigation-doc` | 涉诉文书列表（案号/文书类型/裁判日期/诉讼身份） | 🔴 必调 |
| `executed` | 被执行人信息 | 🔴 必调 |
| `dishonest` | 失信被执行人 | 🔴 必调 |
| `admin-penalty` | 行政处罚记录 | 🔴 必调 |
| `court-announcement` | 法院公告 | 🟡 建议调 |
| `court-hearing` | 开庭公告（反映未决诉讼）| 🟡 建议调 |
| `equity-frozen` | 股权冻结（与第2章共用） | 🟡 建议调 |
| `serious-violation` | 严重违法（与第1章共用） | 🟡 建议调 |

```bash
for cmd in litigation-stat litigation-doc executed dishonest admin-penalty \
           court-announcement court-hearing equity-frozen serious-violation; do
  python3 scripts/yd_enterprise_info.py $cmd --tyshxydm <USCC> --output ./raw/ --yes
done
```

---

## 第 10 章：其他重要事项

**核心关注**：对外投资、关联交易

| 子命令 | 提供信息 | 优先级 |
|---|---|---|
| `outbound-invest` | 对外投资（被投资企业名称/出资比例/经营状态） | 🔴 必调 |

```bash
python3 scripts/yd_enterprise_info.py outbound-invest --tyshxydm <USCC> --output ./raw/ --yes
```

---

## 一键全量拉取（完整尽调）

```bash
#!/bin/bash
# 完整尽调数据拉取脚本（全部相关子命令）
# 约消耗积分：20+ 次 × 10 积分/次 = 200+ 积分（视翻页而定）

USCC="替换为目标公司USCC"
OUTDIR="替换为项目路径/raw/chineselaw/"
SCRIPT="~/.claude/skills/yd-enterprise-info/scripts/yd_enterprise_info.py"

# 非分页接口
python3 $SCRIPT base-info --tyshxydm $USCC --output $OUTDIR --yes
python3 $SCRIPT litigation-stat --tyshxydm $USCC --output $OUTDIR --yes

# 分页接口
for cmd in change brand patent soft-right copyright-work website \
           outbound-invest outbound-guarantee equity-pledge equity-frozen \
           abnormal serious-violation tax-arrears admin-penalty \
           executed dishonest litigation-doc court-announcement court-hearing; do
  python3 $SCRIPT $cmd --tyshxydm $USCC --output $OUTDIR --yes
  echo "✅ $cmd done"
done

echo "全部完成，数据保存至 $OUTDIR"
```

---

## 优先级说明

- 🔴 **必调**：该章核心数据，应在 draft 前完成
- 🟡 **建议调**：辅助信息，视项目需要决定是否调用
- 覆盖 DD 第 5、7 章的接口当前不可用，需律师人工收集材料

# 当前官方来源地图

使用本地图按工作流选择起点。它有意不固化特定修订版本的下载 URL。

## HTS / 归类

| 需求 | 首选来源 |
|---|---|
| 当前 HTS 批量 JSON | Data.gov 上"美国协调关税表（{年份}）"的目录记录 |
| 实时税号检索 | USITC HTS REST 检索，网址为 `https://hts.usitc.gov/reststop/search?keyword={term}` |
| 章和节注释 | USITC HTS 当前发布版 / 各章文件 |
| 历史修订 | USITC HTS 档案 |
| HTS 学习/背景 | USITC HTS 信息和官方 HTS 指南 |

## CBP / CROSS / 海关指引

| 需求 | 首选来源 |
|---|---|
| 有约束力裁定文本 | CBP CROSS 裁定页面，网址为 `https://rulings.cbp.gov/ruling/{id}` |
| 裁定检索 | CBP CROSS 检索 |
| 裁定撤销/修改 | CROSS 裁定文本、相关时 CBP《海关公报》 |
| 知情合规出版物 | CBP 官方出版物页面 |
| MPF 和报关费指引 | CBP 官方费用页面和 19 CFR 第 24 部分 |

## 法院

| 需求 | 首选来源 |
|---|---|
| CIT 简易意见 | `https://www.cit.uscourts.gov/content/slip-opinions-{year}` |
| CIT 意见文本 | 官方 CIT PDF |
| CAFC 意见 | 联邦巡回法院官方意见和命令页面 |
| 后续历史 | 可获得的官方上诉案卷/意见来源；如无官方来源，仅将二手引证工具用作方向参考 |

## 贸易救济

| 需求 | 首选来源 |
|---|---|
| 第 301 条 | USTR 官方通知、产品清单、排除、联邦公报通知、HTS 第 99 章 |
| 第 232 条 | 总统公告、商务部/BIS 排除材料、联邦公报、HTS 第 99 章 |
| 第 201 条 | 总统公告、USITC 保障措施材料、联邦公报、HTS 第 99 章 |
| AD/CVD 命令和范围 | 商务部/ITA、可获得的 ACCESS、联邦公报通知、可获得的 CBP 清算/现金保证金指示 |

## 原产地 / 优惠计划 / 采购

| 需求 | 首选来源 |
|---|---|
| 标记与实质性改变 | 19 U.S.C. 1304、19 CFR 第 134 部分、CBP CROSS 原产地裁定 |
| USMCA 和自贸区规则 | 官方协定文本、CBP/USMCA 指引、USTR/CBP 官方来源 |
| 特殊计划代码 | 当前 HTS 特殊字段加 `references/fta-program-codes.json` 作为解码器 |
| TAA 指定国家 | FAR/DFARS 或 GSA 官方来源、当年度采购指引 |

## PGA / 可入关性

| 需求 | 首选来源 |
|---|---|
| FDA | FDA 进口计划、产品特定进口页面、相关的 FDA 产品代码 |
| EPA | EPA 进口要求、TSCA、农药、车辆/发动机、消耗臭氧层物质 |
| CPSC | CPSC 管制产品、证书、测试和标签要求 |
| FCC | FCC 设备授权和射频设备进口指引 |
| USDA/APHIS | APHIS 进口要求、植物、动物、农产品 |
| DOT/PHMSA/NHTSA | 官方车辆和危险材料进口规则 |
| FWS/NMFS | 野生动植物、渔业和受保护物种进口要求 |

## UFLPA / 强迫劳动

| 需求 | 首选来源 |
|---|---|
| UFLPA 操作指引 | CBP UFLPA 官方指引 |
| 实体清单 | DHS UFLPA 实体清单官方材料 |
| 扣留放行令 | CBP WRO 和强迫劳动页面 |
| 风险行业 | 官方 DHS/CBP 战略和执法更新 |

## 二手来源

仅使用律所警报、行业媒体、论著或数据库片段来定向研究或识别官方来源。将其标注为二手来源，不得用作主导权威。

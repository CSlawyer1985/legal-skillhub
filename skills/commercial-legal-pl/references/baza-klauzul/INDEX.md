---
type: Index
title: KTZR 条款库
description: 来自 KTZR 律所合同的 21 类条款目录——IT、NDA、body-leasing、SaaS、和解、AI 政策。
tags: [baza-klauzul, KTZR, IT, NDA, body-leasing, SaaS, 和解, AI Act, AI 政策]
timestamp: 2026-07-17
---

# KTZR 条款库——索引

来自 KTZR.pl 律所合同的条款集合，按类别整理。仅当需要某类别的条款时才打开具体文件——不要一次性全部加载。

## 每个类别文件的结构

1. **何时适用及注意事项**——该类别何时需要的简短背景
2. **⚠️ 红旗**——分析时要寻找什么、生成时要避免什么
3. **示范条款（通用 IT）**——用于适配的起点
4. **KTZR 合同条款**——来自律所具体合同的实际条款，按来源分组（如“Body Leasing IT”“NDA IT”“许可咨询协议”）

## 类别地图——主库

| # | 文件 | 类别 | 何时使用 |
|---|---|---|---|
| 01 | `01-oznaczenie-stron.md` | 当事方标识与代表 | 每份合同——当事人部分 |
| 02 | `02-preambuly.md` | 序言与当事方声明 | 需要“鉴于……”序言或合同性质声明时 |
| 03 | `03-definicje.md` | 定义 | 每份含大写术语的合同 |
| 04 | `04-przedmiot-umowy.md` | 合同标的 | 每份合同——标的条款 |
| 05 | `05-obowiazki-stron.md` | 当事方义务 | 每份合同——义务条款 |
| 06 | `06-wynagrodzenie.md` | 报酬与结算 | 有偿合同 |
| 07 | `07-terminy-kamienie-milowe.md` | 期限与里程碑 | 实施、分阶段项目 |
| 08 | `08-prawa-autorskie-ip.md` | 著作权/知识产权 | 含创作成果的合同（IT、设计、内容） |
| 09 | `09-poufnosc.md` | 保密 | 含敏感信息交换的合同、NDA |
| 10 | `10-kary-umowne.md` | 违约金 | 含违约制裁的合同 |
| 11 | `11-odpowiedzialnosc.md` | 责任与限额 | 每份 B2B 合同 |
| 12 | `12-wypowiedzenie-exit.md` | 解约与退出计划 | 持续/定期合同 |
| 13 | `13-non-solicitation.md` | 不招揽/竞业禁止 | 可接触客户/雇员的合同 |
| 14 | `14-rodo.md` | 个人数据/GDPR | 含个人数据处理的合同 |
| 15 | `15-sila-wyzsza.md` | 不可抗力 | 持续/长期合同 |
| 16 | `16-ugody.md` | 和解与协议 | 解决争议、妥协 |
| 17 | `17-postanowienia-koncowe.md` | 最终条款 | 每份合同——最终条款 |
| 18 | `18-zwrot-materialow.md` | 材料和文件返还 | 含材料交付/保密的合同 |
| 19 | `19-cesja-wierzytelnosci.md` | 债权转让 | 特定于债权转让 |
| 20 | `20-regulamin-usdde-aup.md` | 电子服务条款/AUP（托管、服务器、域名、AI） | 《电子服务法》条款、SaaS、托管、域名、AI 模块——禁止非法内容、通知与行动、SLA、消费者权利 |
| 21 | `21-polityka-ai.md` | 人工智能使用政策（KTZR 范本） | 公司部署 AI 并需要部署者政策时——AI 法案第 4 条（能力）、第 5 条（禁止）、第 50 条（标注）。涵盖工具登记册、受保护数据、GDPR、事件。 |

## 条款选择规则

1. **从最接近当前所分析合同类型的 KTZR 合同条款开始**。如您在分析 body leasing，取标注“Body Leasing IT (KTZR)”的条款。
2. 如无匹配——使用“示范条款”部分中的通用 IT 示范条款。
3. **绝不在库之外凭空编造条款**。如库中没有合适的条款，直接告诉用户并请其决定。
4. **始终进行适配**——当事方名称、金额、期限、对这份具体合同其他条款的引用。不要 1:1 复制。

---
name: aladin-drama-portrait
slug: aladin-drama-portrait
version: 1.0.0
displayName: 阿拉丁·AI短剧数字人肖像权合规工坊｜授权链自查·换脸授权·数字人到期·撞脸预警
summary: 阿拉丁出品的 AI 短剧数字人肖像权合规工坊：把角色卡(_cast.json)与授权凭证登记一键过授权链自查——真人肖像/数字人/换脸源/声音克隆缺证检测、授权到期与即将到期预警、发行平台与商用用途越界比对、AI 形象撞脸公众人物人工复核、二次转授瑕疵、平台 AI 合成人物报备体检，按 100 分制出 READY/REVIEW/BLOCK 门禁评分，产出 HTML 授权链看板+Markdown 整改清单+闭环回灌契约。纯本地零依赖离线可用，授权信息不出本机。skillhub 短剧类零肖像权授权链技能，蓝海空白。
description: 阿拉丁·AI短剧数字人肖像权合规工坊把「AI 演员/数字人/换脸/声音克隆做完却因肖像权没授权被投诉下架、数字人授权到期还在用、授权只买了一个平台却全网发、AI 形象神似明星惹官司、被举报时拿不出授权链举证」升级成一条纯本地零依赖的上架前置授权链自查工具链：多源导入(drama-cast 角色卡 _cast.json 双契约兼容/人物资产类型声明 assets.json/授权凭证登记 CSV 或 JSON/drama-publish 发行计划 _publish_plan.json 抽平台)→人物资产五分类(AI原创 ai_original/真人出演 real_actor/第三方数字人 digital_human/换脸 face_swap/声音克隆 voice_clone)逐类判定所需授权→10 条确定性授权链规则(A1缺授权凭证 A2要素缺失 A3已过期 A4即将到期 A5平台越界 A6用途越界 A7撞脸公众人物 A8声音克隆缺授权 A9转授瑕疵 A10平台报备缺失)→门禁评分(P0=25/P1=8/P2=3 扣分，100分制 A-D 档，READY可提审/REVIEW建议整改/BLOCK禁止上架)→自包含 HTML 授权链看板(门禁灯+逐条命中+整改建议)+Markdown 整改清单(可直接交制片执行)+feedback 回灌契约(缺证角色回灌 drama-cast 补授权、越界平台回灌 drama-publish 调发行、续签观察名单、报备提醒)。与 aladin-drama 系列闭环衔接(cast/publish 进，整改反馈回灌 cast 补授权、publish 调发行矩阵)。区别于内容合规工具只扫违禁词与画面红线：本款专管「人」的授权链(肖像权/声音权/数字人许可/换脸源授权)，确定性规则可复算、命中带人物名与整改方向、纯本地零依赖零API、授权信息不出本机(法务资产敏感)。触发词：短剧肖像权、数字人授权、换脸授权、声音克隆授权、AI演员合规、肖像授权到期、授权链自查、撞脸明星、数字人合规、AI形象报备、肖像权侵权、portrait rights、digital human license、face swap consent、voice clone authorization、AI短剧、阿拉丁短剧、短剧创作闭环。
category: video
license: MIT
platforms:
  - WorkBuddy
  - QClaw
  - ima
homepage: https://skillhub.cn
author: adam
company: 阿拉丁
tags:
  - 阿拉丁
  - aladin
  - AI短剧
  - 短剧肖像权
  - 数字人授权
  - 换脸授权
  - 声音克隆授权
  - AI演员合规
  - 肖像权自查
  - 授权链
  - 授权到期预警
  - 平台越界
  - 撞脸明星
  - AI形象报备
  - 肖像权侵权
  - 数字人合规
  - portrait rights
  - digital human license
  - face swap consent
  - voice clone
  - short drama
  - 短剧创作闭环
agent_created: true
---

# 阿拉丁·AI短剧数字人肖像权合规工坊

上架前 5 分钟，把短剧里出现的每一个"人"——真人演员、数字人、换脸形象、AI 原创形象、
克隆的声音——统统过一遍**授权链自查**，拿到门禁评分与逐条整改清单，避免辛苦做完的短剧
因为肖像权/声音权没授权而被投诉、下架、索赔。

**为什么需要**：AI 短剧大量使用数字人、换脸与声音克隆，肖像权翻车点高度集中且都能提前
发现——真人出演没签肖像授权、数字人授权到期了还在用、授权只买了红果却全网发（平台越界）、
只买了非商用授权却商业变现（用途越界）、AI 生成形象神似明星、被举报时拿不出完整授权链
举证。这些用确定性规则在上架前就能查出来。

**与内容合规的分工**：内容合规工具管"内容红线"（违禁词、画面尺度、AIGC 标识、备案）；
本技能专管"**人**"的授权链（肖像权、声音权、数字人许可、换脸源授权）。两者互补，各司其职。

**数据安全**：纯 Python 标准库，零第三方依赖、零云端 API，角色卡与授权信息全程不出本机。
所有命中可复算：同输入必同输出，命中带人物名、规则号与整改方向。

## 何时触发

- 用户说「短剧上架前帮我查一下肖像权/数字人授权/换脸授权有没有问题」
- 用户用了数字人/换脸/声音克隆，问「会不会侵犯肖像权/被投诉下架」
- 用户问「数字人授权到期了还能用吗」「授权只买了一个平台能全网发吗」
- 用户担心「AI 生成的角色神似某明星会不会惹官司」
- aladin-drama 系列闭环中，`drama-cast` 角色清单 / `drama-publish` 发行计划需要投前肖像权把关
- 关键词：短剧肖像权、数字人授权、换脸授权、声音克隆、AI 演员合规、授权到期、撞脸明星、授权链自查

## 何时不触发

- 内容违禁词/画面尺度/AIGC 标识/备案检查（用内容合规向工具更合适）
- 真实肖像权纠纷诉讼与法律意见出具（请咨询律师）
- 授权合同的起草与谈判（本技能只做已登记授权的自查，不代写合同）
- 图文/电商模特肖像授权（本技能面向短剧场景的角色/演员/数字人）

## 快速开始

```bash
# 1) 多源导入归一（角色卡 + 资产类型声明 + 授权登记 + 发行平台/日期）
python scripts/portrait_ingest.py --cast assets/sample_cast.json \
    --assets assets/sample_assets.json --licenses assets/sample_licenses.csv \
    --platforms 红果 抖音 --release-date 2026-08-01 --out _portrait_ir.json

# 2) 授权链自查（目标平台 + 是否已完成 AI 人物报备）
python scripts/portrait_audit.py --ir _portrait_ir.json \
    --platform 红果 --filing-ai-persona no --out _portrait.json

# 3) 渲染授权链看板与整改清单
python scripts/portrait_report.py --report _portrait.json \
    --out-html portrait_board.html --out-md _portrait_fix.md
```

## 工作流程

1. **导入归一** `portrait_ingest.py`：读 `drama-cast` 的 `_cast.json`（cards 契约）作为人物清单；
   `assets.json` 声明每个人物的资产类型（未声明默认 AI 原创）；`licenses.csv/json` 登记授权凭证；
   `_publish_plan.json` 抽取发行平台。统一成人物资产台账 IR。
2. **五分类判定**：把每个人物归入 AI原创/真人/数字人/换脸/声音克隆，逐类判定所需授权类型。
3. **10 条授权链规则** `portrait_audit.py`：缺证/要素缺失/过期/即将到期/平台越界/用途越界/
   撞脸公众人物/声音克隆缺授权/转授瑕疵/平台报备缺失，命中带人物名与整改方向。
4. **门禁评分**：P0=25/P1=8/P2=3 扣分，100 分制 A-D 档；任一 P0 → BLOCK，≥80 → READY，其余 REVIEW。
5. **报告与回灌** `portrait_report.py`：自包含 HTML 授权链看板 + MD 整改清单；`feedback` 字段供
   `drama-cast` 补授权、`drama-publish` 调发行矩阵、续签观察名单、报备提醒。
6. **语义级分工（Hy3）**：脚本负责确定性检出；撞脸相似度判断、授权条款解读、续签方案由模型+人工完成。

## 能力边界

**能做**：
- 五类人物资产（真人/数字人/换脸/声音克隆/AI原创）的授权链确定性自查（10 规则，全部可复算）
- 授权到期与即将到期（30 天内）预警、发行平台越界、商用/非商用用途越界检测
- AI 形象/换脸源撞脸公众人物人工复核项、二次转授瑕疵检测、平台 AI 合成人物报备体检
- 100 分制门禁评分与 READY/REVIEW/BLOCK 三态结论
- HTML 授权链看板 + MD 整改清单 + JSON feedback 回灌契约
- 编码自愈（utf-8/gb18030/utf-16），Windows/macOS/Linux 通用，CSV/JSON 双格式授权登记

**不能做**：
- 不出具法律意见，不替代律师审查（结论为上架前自查参考）
- 不自动判断"是否真的撞脸"（仅按用户标记提示，相似度需人工/模型复核）
- 不联网核验授权真伪与备案数据库（凭证真实性需人工核对）
- 不代写/谈判授权合同（只自查已登记授权）
- 不做内容违禁词/画面/AIGC 标识审核（那是内容合规范畴）

## 输入与输出

| 方向 | 内容 |
|------|------|
| 输入 | `_cast.json`（drama-cast 角色卡）；`assets.json`（人物资产类型声明）；`licenses.csv/json`（授权登记）；`_publish_plan.json`（发行计划，抽平台） |
| 中间 | `_portrait_ir.json`（人物资产台账 IR）→ `_portrait.json`（命中+门禁+整改+feedback） |
| 输出 | `portrait_board.html`（自包含看板）；`_portrait_fix.md`（整改清单）；feedback 回灌契约 |

## 重要约束

- **不联网**：全程本地运行，授权信息不出本机（T=可信，法务资产敏感）
- **可复算**：确定性规则，同输入必同输出；命中带人物名/规则号/整改方向（R=可复现）
- **不臆造**：脚本只报告实际命中；无命中即明示"零命中"，不编造风险（A=准确）
- **人机分工**：脚本管检出与评分，撞脸判断与法律解读交给模型+人工（C=可控）
- **预检定位**：结论为上架前授权链参考，最终以平台审核与法律意见为准（E=可解释）

## 参考资料（按需读取）

| 文件 | 何时读 |
|------|--------|
| `references/asset-taxonomy.md` | 需要了解 5 类人物资产、各类所需授权与授权登记字段定义时 |
| `references/authorization-rules.md` | 需要了解 10 条规则完整定义、门禁评分算法与依据边界时 |
| `references/usage-examples.md` | 需要完整场景示例（角色卡自查 / 仅授权登记 / 闭环联动）时 |

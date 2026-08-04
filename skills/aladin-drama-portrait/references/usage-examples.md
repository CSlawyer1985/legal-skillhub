# 使用场景示例

以下示例均使用内置样例，纯本地运行，授权信息不出本机。

## 场景 1：从角色卡 + 授权登记做完整自查

```bash
# 1) 导入归一：角色卡 + 资产类型声明 + 授权登记 + 发行平台/日期
python scripts/portrait_ingest.py \
    --cast assets/sample_cast.json \
    --assets assets/sample_assets.json \
    --licenses assets/sample_licenses.csv \
    --platforms 红果 抖音 --release-date 2026-08-01 \
    --out _portrait_ir.json

# 2) 授权链自查（目标平台 + 是否已完成 AI 人物报备）
python scripts/portrait_audit.py --ir _portrait_ir.json \
    --platform 红果 --filing-ai-persona no --out _portrait.json

# 3) 渲染看板与整改清单
python scripts/portrait_report.py --report _portrait.json \
    --out-html portrait_board.html --out-md _portrait_fix.md
```

样例预期：命中 7 条（P0=4 / P1=3），门禁 `BLOCK`——顾北辰数字人授权过期且平台越界、
苏文换脸源缺授权、陈曼声音克隆缺授权，另有 2 项撞脸公众人物与 1 项平台报备缺失。

## 场景 2：只登记授权、暂无角色卡

若还没跑 `drama-cast`，可直接手写 `assets.json` 声明人物与资产类型，再配授权登记：

```bash
python scripts/portrait_ingest.py --assets my_assets.json --licenses my_licenses.csv \
    --platforms 红果 --release-date 2026-09-01 --out _portrait_ir.json
python scripts/portrait_audit.py --ir _portrait_ir.json --out _portrait.json
```

## 场景 3：闭环联动（aladin-drama 系列）

- **上游**：`drama-cast` 产出 `_cast.json`（角色清单）→ 本技能 `--cast` 直接读取。
- **发行上下文**：`drama-publish` 产出 `_publish_plan.json`→ 本技能 `--publish` 抽取
  平台清单做越界比对：
  ```bash
  python scripts/portrait_ingest.py --cast _cast.json --assets assets.json \
      --licenses licenses.csv --publish _publish_plan.json --out _portrait_ir.json
  ```
- **回灌**：`_portrait.json` 的 `feedback` 字段给出——
  - `to_drama_cast_missing_license`：哪些角色缺授权，回 `drama-cast` 补登记；
  - `to_drama_publish_platform_conflict`：哪些人物平台越界，回 `drama-publish` 调整发行矩阵；
  - `renew_watchlist`：授权即将/已到期的续签名单；
  - `need_platform_filing`：是否需在平台完成 AI 合成人物报备。

## 人机分工建议

- **脚本负责**：确定性检出（缺证/过期/越界/要素缺失）、评分、生成整改清单。
- **模型 + 人工负责**：撞脸公众人物的相似度判断、授权书条款的法律解读、续签谈判。
  把 `_portrait_fix.md` 交给模型逐条给出"如何取得授权 / 如何区分形象"的具体方案。

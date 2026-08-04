# 误中审查指南（False Positive Review Guide）

> **给 AI Agent 的指令**：`browser_verify.py` 完毕后，必须读取本文件并严格按以下步骤执行。
> 这是你最重要的增值工作——**用你自己的大模型判断力识别虚假命中，不调用任何脚本**。

---

## ⭐ 最重要的原则：先看清单级别，再看命中内容

**制裁名单分为两级，判断逻辑完全不同**：

| 清单级别 | 名单 | 判断策略 |
|---------|------|---------|
| **核心制裁清单**（高权威） | OFAC SDN/OFAC NS-MBS、BIS CSL/Entity List、DoD 1260H、UK OSFI、UN Security Council | **精确全名匹配即确认命中**，不要怀疑；这些名单命中极少有误中，记录的是具体实体，不是国家/regime |
| **泛化搜索清单**（误中率高） | EU Sanctions Map、AU DFAT、CA SEMA、SAM.gov | **必须细看命中内容**；这些网站搜索逻辑宽泛，容易触发误中 |

**核心原则**：
- OFAC/BIS/DoD/UK 命中 → **先假设真实命中**，除非全名完全不匹配
- EU/AU/CA 命中 → **先假设疑似误中**，除非命中记录全名与搜索实体精确一致

---

## 第一步：列出所有 HIT 并交叉验证

从终端输出汇总表，找出所有 `HIT 🔴` 的源，记录：
- 源名
- `detail` 字段内容
- `csv_matches` 中的实际文本（如有）

**交叉验证（辅助判断依据）**：回顾阶段 1 的 OpenSanctions 初筛和 Tavily 新闻结果，用作综合上下文：
- OpenSanctions 初筛有匹配 → 加强核心清单 HIT 的可信度
- Tavily 新闻提到该实体被制裁/列入黑名单 → 进一步佐证
- **即使 OpenSanctions 初筛无匹配，核心清单脚本报 HIT 仍以脚本为准**（OpenSanctions 数据可能滞后）

---

## 第二步：区分清单级别，逐一判断

### 🔵 首先确认实体类型（来自阶段 0 的用户回答）

实体类型对判断起决定性作用：

| 用户搜索的是 | 命中的是 | 默认判断 |
|------------|---------|---------|
| **公司/法人实体** | 个人（Individual） | 🟡 疑似误中（类型不匹配） |
| **公司/法人实体** | 国家/地区（Country/Region） | 🟡 疑似误中（类型不匹配） |
| **公司/法人实体** | 公司/组织（Entity/Organization） | 继续看名称 |
| **个人** | 公司/组织 | 🟡 疑似误中（类型不匹配） |
| **个人** | 国家/地区 | 🟡 疑似误中（类型不匹配） |
| **个人** | 个人 | 继续看名称是否匹配 |

### 对「核心制裁清单」（OFAC/BIS/DoD/SAM/UK/UN）的判断流程：

> 🔴🔴🔴 **绝对规则（最高优先级）**：
>
> **核心清单（OFAC SDN、BIS CSL、DoD 1260H、SAM.gov、UK Sanctions、UN SC）的 HIT 结果，绝对不允许被标为 🟡 疑似误中。**
>
> - 脚本在官方网站上搜索到了结果并报告 HIT → 这就是 🔴 确认命中，句号
> - **禁止用你的"知识"覆盖脚本的搜索结果**（例如你"认为" DJI 不在 OFAC SDN → 但脚本搜到了 → 以脚本为准）
> - 你的训练数据可能过时，脚本实时搜索的结果是最新的、权威的
> - **唯一例外**：脚本本身报告了 error 或 manual_review（不是 HIT）

1. 读取命中记录中的**实体全名**
2. 与搜索实体全名（用户在阶段 0 提供的官方全名）对比
3. 判断：
   - 全名明确包含搜索实体名称（完整或主要部分）→ **🔴 确认命中**
   - 全名完全不相关（如完全不同的组织、个人名字与组织名完全不匹配）→ **🟡 疑似误中**
4. **不要因为"名字缩写有多种含义"就怀疑核心清单命中**

> ❌ **禁止的判断**：「OFAC 命中了，但 DJI 也可以指 Djibouti，所以可能是误中」——错误，OFAC SDN 列出的是具体实体，不是国家。
>
> ❌ **禁止的判断**：「DJI 不在 OFAC SDN 名单上」——如果脚本报告 HIT，说明搜到了，你的知识可能已过时。以脚本结果为准。

### 对「泛化搜索清单」（EU/AU/CA/SAM）的判断流程：

逐一排查以下误中模式：

| 误中模式 | 如何识别 | 典型示例 |
|---------|---------|---------|
| **搜索引擎泛化** | EU Sanctions Map：首页返回 regime（制裁框架）列表，**但必须点进每条 regime 的详情页查看是否有被制裁实体全名**。仅看首页 regime 列表不能判定结果 | 搜 "DJI" → 首页返回多个 regime → **必须逐一打开详情截图** → 如果详情中列出了 "SZ DJI Technology" → 🔴 确认命中；如果详情中无实体全名 → 🟡 误中 |
| **ISO 国家代码碰撞** | AU/CA：搜索词恰好是某国 ISO 3166-1 alpha-3 代码，CSV 文件包含该国名 | DJI=Djibouti；CHN=China；IRN=Iran；PRK=朝鲜；RUS=Russia；MMR=缅甸；BLR=白俄罗斯；CUB=Cuba；SYR=Syria；VEN=Venezuela；CAR=中非 |
| **人名子串匹配** | AU/CA：搜索词作为子串出现在某个被制裁人名中，不是独立字段 | "Mullah b Haji DJI"——"DJI" 是名字的一部分，不是大疆创新 |
| **类型不匹配** | 搜索对象是公司，但命中的是个人（Individual）或国家（Country） | 用户搜公司，命中是个人名字 |

> 🔴🔴🔴 **AU DFAT XLSX 特殊注意**：
>
> AU DFAT 的 HIT 结果格式通常是：`Found 'XXX' in DFAT XLSX (sheet: ..., N rows)`
>
> **这不代表精确命中！** 这表示 XLSX 中有 N 行在任意列包含搜索词子串。你**必须查看 `csv_matches` 的具体内容来判断**：
>
> | csv_matches 内容 | 判断 |
> |-----------------|------|
> | 实体全名精确出现（如 "SZ DJI Technology Co., Ltd."） | 🔴 确认命中 |
> | 只有国家名（如 "Djibouti"、"Country: DJI"） | 🟡 疑似误中（ISO 碰撞） |
> | 只有人名含搜索词子串（如 "Mullah DJI"） | 🟡 疑似误中（人名子串匹配） |
> | N 行很多（如 20+），且没有精确的实体全名匹配 | 🟡 大概率疑似误中（泛化搜索触发） |
>
> **禁止仅凭 "Found N rows" 就判为确认命中。必须确认具体匹配行中有实体精确全名。**

---

## 第三步：跨清单综合判断（关键！）

**禁止孤立判断每个命中。必须将多个清单的命中情况综合考量**：

### 综合判断规则：

**规则 A：核心清单确认 → 泛化清单命中 → ⚠️ 仍必须审查泛化清单的实际匹配内容**
- 如果 OFAC/BIS/DoD 已确认命中同一实体，说明该实体确实在制裁名单中
- **但这不代表泛化清单的命中也一定正确！** 泛化清单可能因为完全不同的原因触发 HIT：
  - AU DFAT 的 XLSX 子串匹配 "DJI" → 匹配到的可能是 Djibouti 或人名，不是大疆公司
  - EU Sanctions Map 返回的 regime 列表 → 这些是制裁框架，不是被制裁实体
  - CA SEMA CSV 匹配 "DJI" → 可能是 ISO 国家代码 Djibouti
- **关键判断：看泛化清单匹配到的具体文本是什么，而不是看核心清单是否确认了该实体**
- 核心清单确认 = 该实体确实被制裁 ✅，但泛化清单命中的内容如果是 ISO 代码/人名/regime → 仍然是 🟡 疑似误中

**规则 B：核心清单未命中 → 泛化清单命中大概率是误中**
- 如果 OFAC/BIS/DoD 都未命中，说明该实体不在主要制裁名单中
- 此时 EU/AU/CA 的命中极可能是缩写碰撞或泛化搜索，标为 🟡 疑似误中

**规则 C：人名匹配 ≠ 确认命中**
- 搜索的是公司，命中了一个人名中包含搜索词 → 必须标为 🟡 疑似误中
- 只有命中记录的**实体类型**与搜索对象**类型一致**，且名称高度相似，才能确认命中

---

## 第四步：给出最终判断（结构化思考三问，防止过度思考或思考不足）

对每个 HIT，**按顺序回答这三个问题，得出判断**：

```
问题 1：命中记录的实体类型 vs 搜索实体类型，一致吗？
  → 不一致（公司命中个人/国家，个人命中公司）→ 🟡 疑似误中，停止，不用继续
  → 一致 → 继续 ↓

问题 2：命中记录的实体全名，是否明确指向搜索实体？（不是 ISO 代码，不是子串，不是 regime）
  → 全名精确匹配 → 🔴 确认命中
  → 全名完全不相关 → 🟡 疑似误中
  → 有部分重叠，无法确定 → 继续 ↓

问题 3：结合其他清单的结果，这个命中合理吗？
  → 核心清单（OFAC/BIS/DoD）已确认同一实体 → 🔴 确认命中
  → 核心清单没有命中此实体 → 🟡 疑似误中（缺乏核心清单印证）
  → 核心清单结果不确定 → 🟠 需人工确认
```

## 第五步：生成报告 HTML 片段

生成以下结构的 HTML（将真实数据填入占位符），供写入报告文件：

```html
<section id="ai-fp-assessment" style="font-family:sans-serif;margin:40px;padding:32px;background:#fffbeb;border:2px solid #f59e0b;border-radius:12px;">
<h2 style="color:#92400e;margin-top:0;">🧠 AI 合规分析师 — 误中审查结论</h2>
<p style="color:#78350f;font-size:14px;">本分析由 AI Agent 基于命中内容、实体全名、命中类型、清单权威级别和跨清单上下文语义综合判断，自动生成。</p>
<table style="border-collapse:collapse;width:100%;font-size:14px;">
<thead>
<tr style="background:#fef3c7;"><th style="border:1px solid #d97706;padding:8px;">源</th><th style="border:1px solid #d97706;padding:8px;">命中内容摘要</th><th style="border:1px solid #d97706;padding:8px;">判断</th><th style="border:1px solid #d97706;padding:8px;">理由</th></tr>
</thead>
<tbody>
<!-- 对每个 HIT 生成一行：确认命中用#fee2e2，疑似误中用#fef9c3，需人工确认用#fff7ed -->
[在此处插入每个 HIT 的 <tr> 行]
</tbody>
</table>
<h3 style="color:#92400e;">综合风险评级（排除疑似误中后）</h3>
<p>[排除疑似误中后的真实风险等级，例如：原 7 HIT → 确认命中 N 个（OFAC/BIS/DoD），疑似误中 M 个（EU/AU/CA），真实风险级别为 X]</p>
<h3 style="color:#92400e;">建议</h3>
<p>[针对确认命中的合规建议；对疑似误中的说明，建议用实体官方全名重新精确搜索]</p>
</section>
```

---

## 参考示例：DJI（大疆创新）的正确分析

搜索实体：DJI / 大疆创新科技有限公司（官方全名：SZ DJI Technology Co., Ltd.）  
类型：公司/法人实体

**跨清单综合情况**：BIS CSL 和 DoD 1260H 明确列出 "SZ DJI Technology Co., Ltd."，确认命中。EU/AU/CA 命中的是非相关内容（见下表）。

| 清单级别 | 源 | 命中内容 | 判断 | 理由 |
|---------|-----|---------|------|------|
| 核心 | BIS CSL | "SZ DJI Technology Co., Ltd.", "DJI Europe B.V." | 🔴 确认命中 | 全名精确匹配，类型=Entity，行业=无人机，规则A |
| 核心 | DoD 1260H | "DJI" / "大疆创新" | 🔴 确认命中 | DoD 名单明确列出大疆创新，规则A |
| 核心 | OFAC SDN | 读取实际命中内容 | [依内容判断] | 若命中全名含 DJI Technology → 确认；若只是 Djibouti 相关 → 误中 |
| 泛化 | EU | Central African Republic、Iran 等 regime | 🟡 疑似误中 | 搜索引擎泛化：返回的是 regime 列表非实体；规则B |
| 泛化 | AU DFAT | "Mullah b Haji DJI" 等人名 | 🟡 疑似误中 | 人名子串匹配 + 类型不匹配（个人 vs 公司）；规则C |
| 泛化 | CA SEMA | Djibouti 相关条目 | 🟡 疑似误中 | ISO 代码碰撞：DJI = Djibouti；规则B |

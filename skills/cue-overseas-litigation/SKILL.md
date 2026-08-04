---
name: cue-overseas-litigation
slug: cue-overseas-litigation
displayName: 境外诉讼案例库
version: 1.2.0
description: >
  境外诉讼案例库 — 围绕一个主题检索主要法域的公开判例与监管公告，归纳诉因、判决倾向与对中国主体的合规启示。
  Triggers: 境外诉讼、海外官司、跨境诉讼、海外判例、境外监管公告、国际诉讼案例、制裁案例、出口管制案例、涉外法律检索、overseas litigation、cross-border litigation
license: MIT
metadata:
  source: cuecue.cn/playbook
  scene: "涉外法律"
  buddy: "境外诉讼案例库"
---

# 境外诉讼案例库

> 围绕任意主题检索美国、欧盟、新加坡等主要法域的公开判例与监管公告，归纳诉因、判决倾向与对中国出海主体的合规启示。多源交叉验证，结论带来源链接。

## Agent 执行摘要

| 顺序 | 做什么 | 禁止 |
|------|--------|------|
| 1 | 健康检查：Key / 服务 / 搭子三样全过再跑 | 禁止跳过 |
| 2 | 告知用户耗时 3-15 分钟 | 禁止中途取消 |
| 3 | 确认 credits，一条命令阻塞等待 | 禁止连发多条 |
| 4 | stdout `[cue-research] RESULT ok` = 完成 | 无 RESULT = 未完成 |
| 5 | 原样交付报告 + 告知落盘路径 | 禁止自行概括 |

## 适用场景

| 场景 | 解决的问题 |
|------|-----------|
| 出海合规自查 | 企业在目标法域是否有类似诉讼先例、常见诉因 |
| 行业诉讼风险扫描 | 某行业（光伏/新能源/AI/电商）在海外被诉的典型案例 |
| 制裁与管制监控 | OFAC、BIS 实体清单、欧盟制裁名单的最新动态 |
| 跨境投资尽调 | 目标公司或实控人在海外是否有诉讼/处罚记录 |
| 专利/知产纠纷 | 特定技术领域的海外专利诉讼趋势 |

## 核心能力

1. **多法域判例检索** — 美国联邦法院（PACER）、欧盟法院（CURIA）、新加坡最高法院
2. **监管公告监控** — OFAC 制裁名单、BIS 实体清单、欧盟制裁、ITC 337 调查
3. **诉因归类与判决倾向** — 胜诉/败诉/和解趋势、罚金金额（公开数据）
4. **合规启示归纳** — 对中国出海主体的影响评估
5. **逐条可溯源** — 每个结论附原始出处链接

## 试试这样问

- "查一下新能源行业在美国的专利诉讼案例"
- "检索 TikTok 在海外的监管处罚案例"
- "看看中国光伏企业在欧盟的反倾销判例"
- "比亚迪在海外有没有被起诉过"
- "跨境电商最近在美国的集体诉讼有哪些"
- "最近中国 AI 企业被列入 BIS 实体清单的情况"

## 输出形式

结构化报告：相关案例列表 → 诉因归纳 → 判决倾向 → 罚金/赔偿 → 合规启示 → 来源链接。中文报告，关键判例名/法条保留原文。

## 数据覆盖

美国联邦法院（PACER）、欧盟法院（CURIA）、新加坡最高法院、OFAC SDN List、BIS Entity List、欧盟制裁名单、ITC 337 调查、各法域证券监管公告、ICSID 国际仲裁。以公开数据为限。

---

## 环境要求

```bash
# Runner：有则更新，无则克隆
if [ -d ~/.cue/cue-skills/.git ]; then
  git -C ~/.cue/cue-skills pull --ff-only
else
  git clone https://github.com/sensedeal/cue-skills ~/.cue/cue-skills \
    || git clone https://gitee.com/sensedeal/cue-skills ~/.cue/cue-skills
fi
```

Cue API Key：在 [cuecue.cn](https://cuecue.cn/api-key) 注册获取，新账号送 50 积分 + 每天 10 积分。写入 `~/.cue/config.json`：

```bash
mkdir -p ~/.cue
echo '{"api_key": "sk你的key"}' > ~/.cue/config.json
```

需要 `git` + `python3`（runner 仅用标准库，无额外依赖）。单次研究消耗约 3-8 credits。

---

## 调用说明

Agent 会自动匹配「涉外法律」场景下的「境外诉讼案例库」搭子。固定写法：

```bash
python3 ~/.cue/cue-skills/cue-research/scripts/research_run.py \
  --query "<用户问题原话>" \
  --template-id <运行时的搭子 template_id> \
  --output ~/cue-reports/$(date +%Y-%m-%d-%H%M)-overseas-litigation.md
```

| 参数 | 说明 |
|------|------|
| `--query` | 用户原话，不要改写 |
| `--template-id` | 从 `/api/playbook` 拉取当前可用的搭子 ID |
| `--output` | 落盘路径，格式 `~/cue-reports/日期-overseas-litigation.md` |

---

## 架构说明

本 Skill **不在本地执行检索**。流程是 Agent → Cue 服务端 → 外部数据源：

```
你的 Agent ──→ Cue API（cuecue.cn）──→ PACER / CURIA / OFAC 等
```

| 环节 | 谁控制 | 出问题时 |
|------|--------|---------|
| API Key 鉴权 | 你 | 重新生成 Key，更新 config.json |
| Cue 服务端 | Cue 运维 | 等恢复，或走降级方案 |
| 外部数据源 | 公开网站 | Cue 用缓存兜底，标注"来源暂不可达" |

---

## 健康检查

跑研究前先验证三件事。一键诊断：

```bash
CUE_KEY=$(python3 -c "import json;print(json.load(open('$HOME/.cue/config.json'))['api_key'])" 2>/dev/null || echo "$CUE_API_KEY")
echo "=== 1/3 API Key ===" && [ -n "$CUE_KEY" ] && echo "已配置" || echo "未配置！"
echo "=== 2/3 Cue 服务 ===" && curl -sS --max-time 10 "https://cuecue.cn/api/health" -H "Authorization: Bearer $CUE_KEY"
echo "=== 3/3 搭子 ===" && curl -sS --max-time 10 "https://cuecue.cn/api/playbook" -H "Authorization: Bearer $CUE_KEY" | python3 -c "import sys,json;scenes=json.load(sys.stdin).get('data',[]);buddy=[b for s in scenes if s.get('secondary_category')=='涉外法律' for b in s.get('buddies',[])];print(f'可用:{len(buddy)}个') if buddy else print('暂不可用')"
```

| 检查 | 预期 | 异常处理 |
|------|------|---------|
| API Key | `已配置` | [cuecue.cn/api-key](https://cuecue.cn/api-key) 重新生成 |
| 服务 | `{"status":"healthy"}` | 等 5 分钟重试 |
| 搭子 | `可用:>0个` | 等 1h 或网页端手动跑 |

---

## 自救指引

### 错误速查

| 现象 | 原因 | 怎么修 |
|------|------|--------|
| 401 / Key 无效 | Key 过期或写错 | 重新生成 Key，更新 `~/.cue/config.json` |
| 超时 >30s | 服务维护/过载 | 等 5 分钟，跑诊断；当天内重试 |
| 搭子不可用 | 临时下线 | 网页端直接跑，或等 1 小时 |
| 积分不足 | 余额 < 消耗 | 每天登录送 10 积分 |
| 中途中断 | 队列满/数据源波动 | **不换 prompt**，相同命令续接 |
| `RESULT empty` | 公开源无匹配 | 缩小范围（法域/时段），换关键词 |
| config.json 报错 | JSON 格式不对 | `{"api_key": "sk..."}` 无多余逗号 |

### 决策树

```
出问题？
├─ Key 报错 → 重新生成 → 更新 config.json → 重试
├─ 连不上 → curl /api/health 确认 → 检查 DNS/代理
├─ 搭子找不到 → curl /api/playbook → 等或用网页端
├─ 中途中断 → 相同 prompt 续接（不要删 ~/.cue/session/task）
└─ 结果空 → 缩窄关键词 → 单法域 → 确认该主题有公开判例
```

### 调度建议

| 时段 | 建议 |
|------|------|
| 工作日 9-18 | 正常使用 |
| 夜间/周末 | 可能有维护，跑前先诊断 |
| 新 Key | 必须先诊断确认生效 |
| 连续失败 | 停 15 分钟再试，不要反复重试 |

---

## 降级方案

Cue 长时间不可达时的手动替代渠道：

| 渠道 | 覆盖 | 费用 |
|------|------|------|
| [PACER](https://pacer.uscourts.gov) | 美国联邦法院 | 按页，<$30/季免费 |
| [Google Scholar](https://scholar.google.com) | 美国联邦+州法院 | 免费 |
| [CURIA](https://curia.europa.eu) | 欧盟法院 | 免费 |
| [OFAC SDN](https://sanctionssearch.ofac.treas.gov) | 美国制裁名单 | 免费 |
| [BIS Entity List](https://www.bis.gov/entity-list) | 出口管制实体清单 | 免费 |
| [ICSID](https://icsid.worldbank.org/cases) | 国际投资仲裁 | 免费 |

---

## FAQ

**Q: 和 Cue 网页端有什么区别？**
A: 在 Claude Code 里直接用自然语言触发，Agent 自动匹配搭子、确认、取报告，不用切网页。

**Q: 能查国内诉讼吗？**
A: 不能。本 Skill 专注境外法域，国内诉讼有另外的搭子。

**Q: 报告语言？**
A: 中文报告，判例名/法条保留原文附摘要。

**Q: 积分不够？**
A: 每天登录送 10 积分，单次约 3-8 积分。也可升级账号。

**Q: 查不到怎么办？**
A: 先跑健康检查。三个环节任一断了都会失败——见上方「自救指引」。

**Q: 结果可靠吗？**
A: 结论带来源链接可回查。注意：覆盖以联邦法院/欧盟/主要监管公告为主；州法院、仲裁非公开裁决、非英语法域覆盖不全；不构成法律意见。

---

> 本 Skill 基于 Cue 平台（cuecue.cn）「境外诉讼案例库」搭子。搭子模板由服务端动态维护。Skill 本身 MIT 开源。

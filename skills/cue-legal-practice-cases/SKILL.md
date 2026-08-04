---
name: cue-legal-practice-cases
slug: cue-legal-practice-cases
displayName: 疑难法律实操案例库
version: 1.0.0
description: >
  疑难法律实操案例库 — 围绕一个争议点检索公开裁判文书、监管问答与实务案例，归纳裁判要点、争议焦点与可落地的实操口径，给办案一个参照。
  Triggers: 疑难法律、实操案例、裁判口径、类案检索、裁判规则、实务案例、争议焦点、法律实操、监管问答、判例检索、legal practice cases
license: MIT
metadata:
  source: cuecue.cn/playbook
  scene: "法律合规"
  buddy: "疑难法律实操案例库"
---

# 疑难法律实操案例库

> 遇到拿不准的法律问题，先看别人怎么判、怎么办。围绕一个争议点检索公开裁判文书、监管问答与实务案例，归纳裁判要点、争议焦点与可落地的实操口径，给办案一个参照。

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
| 类案检索 | 某个法律争议点，各地法院怎么判、主流观点是什么 |
| 争议焦点研判 | 案件的核心争议点是什么，原被告各自主张和法院态度 |
| 监管口径查询 | 某类业务操作是否合规，监管部门过往怎么表态和处理 |
| 诉讼策略参考 | 类似案件中胜诉方的诉讼策略、证据组织方式 |
| 仲裁实务 | 某类合同纠纷在仲裁中的裁判倾向和赔偿标准 |

## 核心能力

1. **裁判文书检索** — 中国裁判文书网、各仲裁委公开裁决
2. **类案归纳** — 各地各级法院对同一争议焦点的裁判规则比对
3. **争议焦点提炼** — 归纳原被告诉辩主张、法院说理逻辑
4. **实操口径** — 从判例提炼可落地的业务操作建议
5. **逐条可溯源** — 每个案例附案号和来源链接

## 试试这样问

- "对赌协议中股权回购权的行使期限，法院怎么判"
- "VIE架构在境内法院的效力认定案例"
- "算法歧视的侵权责任认定，最近有哪些判例"
- "股东代表诉讼的前置程序豁免条件，各地法院口径"
- "数据爬取的不正当竞争认定，典型案例和裁判规则"
- "对赌失败后创始人个人责任的裁判倾向"

## 输出形式

结构化报告：争议焦点概述 → 相关案例列表 → 各地裁判规则对比 → 主流/少数观点 → 实操建议 → 风险提示 → 来源链接（附案号）。中文报告，关键判例名保留原文。

## 数据覆盖

中国裁判文书网、各仲裁委公开裁决、证监会/银保监会行政处罚决定、交易所纪律处分、监管问答。以公开数据为限。

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

Agent 会自动匹配「法律合规」场景下的「疑难法律实操案例库」搭子。固定写法：

```bash
python3 ~/.cue/cue-skills/cue-research/scripts/research_run.py \
  --query "<用户问题原话>" \
  --template-id <运行时的搭子 template_id> \
  --output ~/cue-reports/$(date +%Y-%m-%d-%H%M)-legal-practice-cases.md
```

| 参数 | 说明 |
|------|------|
| `--query` | 用户原话，不要改写 |
| `--template-id` | 从 `/api/playbook` 拉取当前可用的搭子 ID |
| `--output` | 落盘路径，格式 `~/cue-reports/日期-legal-practice-cases.md` |

---

## 架构说明

本 Skill **不在本地执行检索**。流程是 Agent → Cue 服务端 → 外部数据源：

```
你的 Agent ──→ Cue API（cuecue.cn）──→ 裁判文书网 / 仲裁委 / 监管公告等
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
echo "=== 3/3 搭子 ===" && curl -sS --max-time 10 "https://cuecue.cn/api/playbook" -H "Authorization: Bearer $CUE_KEY" | python3 -c "import sys,json;scenes=json.load(sys.stdin).get('data',{}).get('scenes',[]);buddy=[b for s in scenes if s.get('secondary_category')=='法律合规' for b in s.get('buddies',[]) if b.get('title')=='疑难法律实操案例库'];print(f'可用:{len(buddy)}个') if buddy else print('暂不可用')"
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
| `RESULT empty` | 公开源无匹配 | 缩小范围（案由/法院层级），换关键词 |
| config.json 报错 | JSON 格式不对 | `{"api_key": "sk..."}` 无多余逗号 |

### 决策树

```
出问题？
├─ Key 报错 → 重新生成 → 更新 config.json → 重试
├─ 连不上 → curl /api/health 确认 → 检查 DNS/代理
├─ 搭子找不到 → curl /api/playbook → 等或用网页端
├─ 中途中断 → 相同 prompt 续接（不要删 ~/.cue/session/task）
└─ 结果空 → 缩窄关键词 → 单案由 → 确认该争议有公开判例
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
| [中国裁判文书网](https://wenshu.court.gov.cn) | 全国法院裁判文书 | 免费 |
| [中国庭审公开网](http://tingshen.court.gov.cn) | 庭审直播录像 | 免费 |
| [12309中国检察网](https://www.12309.gov.cn) | 检察文书 | 免费 |
| [全国企业破产重整信息网](https://pccz.court.gov.cn) | 破产案件 | 免费 |
| [证监会](https://www.csrc.gov.cn) | 行政处罚决定 | 免费 |
| [各仲裁委官网](https://www.cietac.org) | 仲裁规则与案例摘要 | 免费 |

---

## FAQ

**Q: 和 Cue 网页端有什么区别？**
A: 在 Claude Code 里直接用自然语言触发，Agent 自动匹配搭子、确认、取报告，不用切网页。

**Q: 能查境外判例吗？**
A: 不能。本 Skill 聚焦国内裁判文书和监管案例，境外诉讼案例有另外的搭子（境外诉讼案例库）。

**Q: 报告语言？**
A: 中文报告，判例名和案号保留原文格式。

**Q: 积分不够？**
A: 每天登录送 10 积分，单次约 3-8 积分。也可升级账号。

**Q: 查不到怎么办？**
A: 先跑健康检查。三个环节任一断了都会失败——见上方「自救指引」。

**Q: 结果可靠吗？**
A: 结论带案号和来源链接可回查。注意：覆盖以公开裁判文书和监管公告为主；未公开的仲裁裁决、调解书覆盖不全；不构成法律意见。

---

> 本 Skill 基于 Cue 平台（cuecue.cn）「疑难法律实操案例库」搭子。搭子模板由服务端动态维护。Skill 本身 MIT 开源。

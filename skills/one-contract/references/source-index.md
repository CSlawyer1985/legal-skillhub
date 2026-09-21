# 来源与状态索引

核验日期：2026-08-09。法域：中国大陆。下列来源用于确定硬边界或公开实务倾向；使用具体合同前仍需核验劳动关系履行地的地方规则。

| ID | 来源 | 性质 | 适用议题 | 状态 |
|---|---|---|---|---|
| CN-LCL | [《中华人民共和国劳动合同法》](https://flk.npc.gov.cn/detail?fileId=&id=2c909fdd678bf17901678bf74d7106b3&title=%E4%B8%AD%E5%8D%8E%E4%BA%BA%E6%B0%91%E5%85%B1%E5%92%8C%E5%9B%BD%E5%8A%B3%E5%8A%A8%E5%90%88%E5%90%8C%E6%B3%95&type=) | 法律 | 协商解除、经济补偿、竞业、离职手续 | 国家法律法规数据库显示有效，公布日期 2012-12-28 |
| SPC-LABOR-I | [最高人民法院劳动争议司法解释（一）](https://www.court.gov.cn/zixun/xiangqing/282121.html) | 司法解释 | 解除结算协议效力、竞业、举证 | 自 2021-01-01 施行；使用时结合解释（二）处理冲突 |
| SPC-LABOR-II | [最高人民法院劳动争议司法解释（二）](https://gongbao.court.gov.cn/Details/bb72019c45453f84d920bd6375573e.html) | 司法解释 | 社保约定、竞业、职业健康检查等 | 法释〔2025〕12号，自 2025-09-01 施行 |
| SPC-OT-CASES | [劳动人事争议典型案例（第二批）](https://www.court.gov.cn/zixun/xiangqing/319151.html) | 官方典型案例 | 放弃加班费、虚假结清、举证与时效 | 用于裁判/仲裁倾向和反例，不等同成文法 |
| WAGE-PAY | [《工资支付暂行规定》](https://rlsbj.cq.gov.cn/zwgk_182/fdzdgknr/lzyj/rsbgz/202103/t20210305_8968881.html) | 部门规范 | 解除时工资结清、工资清单 | 核验地方工资支付法规是否有更具体期限 |
| ANNUAL-LEAVE | [《职工带薪年休假条例》](https://xzfg.moj.gov.cn/front/law/detail?LawID=208) | 行政法规 | 年休假权利及未休工资 | 国家行政法规库现行文本 |
| ANNUAL-LEAVE-MEASURES | [《企业职工带薪年休假实施办法》](https://hrss.zs.gov.cn/zcfg/ldgx/content/post_1196497.html) | 部门规章 | 解除时折算、日工资和书面不休 | 人社部令第1号；结合地方规则 |
| SOCIAL-INSURANCE | [《中华人民共和国社会保险法》](https://www.mohrss.gov.cn/gjhzs/GJHZzhengcewenjian/201506/t20150625_212402.html) | 法律 | 缴纳、补缴和账户义务 | 官方转载；具体经办核验当地规则 |
| HOUSING-FUND | [《住房公积金管理条例》](https://xzfy.moj.gov.cn/c/2021-01-17/488809.shtml) | 行政法规 | 缴存、转移和封存 | 官方行政法规文本 |
| NONCOMPETE-GUIDE | [《企业实施竞业限制合规指引》](https://app.www.gov.cn/govdata/gov/202509/13/536638/article.html) | 行政合规指引 | 适用人员、范围、补偿、解除和报告 | 2025 年发布；属于合规指引，不冒充法律强制规则 |

## 项目内部来源

| 来源 | 用途 | 状态 |
|---|---|---|
| 既有协商解除审查产物及渲染对比 | 开发集、失败复盘、措辞和动作对照 | 含真实业务信息，不进入公开 Skill；不得作为盲测 |
| 既有 12 类合同 references | 仅作项目内迁移来源 | 已退出运行时路由；未逐条复核，只能提炼为 `candidate` 并等待用户逐项确认；对外 Skill 包不保留原文件 |
| “五篇协商解除 Markdown 文章” | 据任务书称曾用于专项增强 | 项目及本地 Skill 未发现原文件、作者、发布日期或链接；状态为待补，不引用其具体结论 |

## 知识性质标记

原则卡引用来源时区分：

- `legal_boundary`：法律、行政法规或明确强制边界；
- `judicial_tendency`：司法解释、指导/典型案例反映的裁判倾向；
- `administrative_guidance`：人社等部门合规指引或经办口径；
- `risk_control`：可执行性与证据管理经验；
- `negotiation`：立场和交易策略；
- `client_policy`：特定客户偏好；
- `independent_judgment`：模型基于当前交易作出的独立判断。

不得把后四类包装成法律要求。来源失效、法域不明或复核状态不明时，降低结论强度并要求核验。

# 交易/资本市场术语词典

交易与资本市场协议的标准英文术语：ISDA 主协议、衍生品、回购协议、主经纪业务、清算、保证金、证券借贷及相关工具。包括 EMIR、MiFID 和市场基础设施术语。

> **各语言分词典说明。** 本英文参考文件是交易与资本市场的跨语言权威；金融与银行术语位于 `references/finance-banking.md`。在各语言分词典中，两个领域合并为单一文件：`sub-lexicons/<语言>-finance-banking.md` 涵盖两者。处理资本市场文件时，阅读两份英文参考文件，但只读该语言的单一分词典。

## 核心交易/衍生品术语

| 规范英文术语 | 用法 / 含义 | 避免使用 |
|---|---|---|
| ISDA Master Agreement | 两个对手方之间衍生品交易的标准框架 | 泛指"主协议"；与个别交易确认书混淆 |
| confirmation | ISDA 主协议下的个别交易细节 | "证明书"；与正式法律转让混淆 |
| schedule | ISDA 主协议的标准条款和修订 | "附录"（过于含糊）；"附件"（CSA 更偏好此词） |
| ISDA Definitions | 已发布的衍生品计算和支付流规格 | 用"定义部分"意译 |
| transaction | ISDA 主协议下执行的个别交易 | "操作"；"交易"（不精确） |
| derivative / derivative instrument | 从标的资产/利率/指数派生价值的金融合同 | "派生产品"；"金融产品"（过于宽泛） |
| OTC derivative | 场外衍生品（未清算、双边） | "私人衍生品"；"非交易所"（不精确） |
| exchange-traded derivative | 在受监管市场上经 CCP 清算的衍生品 | "交易所产品"；"清算衍生品"（并非所有交易所交易的都清算） |
| interest rate swap (IRS) | 同币种固定与浮动利息支付的交换 | "利率交换"；"掉期合同"（过于笼统） |
| cross-currency swap | 两种不同货币的本金和利息交换 | "货币掉期"（不够精确）；"外汇掉期"（不同产品） |
| forward | 按约定未来价格买卖的双边合同 | "远期合同"（可接受但 "forward" 是标准）；"期货"（交易所交易，不同） |
| option | 在指定日期或之前按约定价格买入/卖出的权利（而非义务） | "期权合同"；"条件衍生品" |
| cap | 限制最高利率的浮动利率衍生品 | "上限"；"利率上限"（可接受但不够标准） |
| floor | 设定最低利率的浮动利率衍生品 | "基准利率"；"利率下限"（可接受但不够标准） |
| collar | 上限和下限的组合，通常零成本 | "利率领式"（可接受但不够标准） |
| credit default swap (CDS) | 针对参考实体违约的类似保险的保护 | "信用保护"；"违约保险"（不正确——不是保险产品） |
| credit event | 触发信用违约掉期付款的事件（破产、未付款、重组）；按 ISDA 信用衍生品定义所定义 | 违约事件（过于宽泛）；触发事件（过于含糊） |
| total return swap | 对手方获得参考资产的全部经济回报（价格+票息） | "回报掉期"；"TRS"（首次全称使用后可接受缩写） |
| notional amount | 用于计算付款的面值金额（多数衍生品中不实际交换） | "本金"（通常指实际支付的金额）；"合同价值"（不精确） |
| effective date | 交易日或合同条款开始生效的日期 | "开始日期"；"起始日期"（不够技术化） |
| termination date / maturity date | 合同结束并支付最终款项的日期 | "结束日期"；"到期日期"（不够精确） |
| payment date | 中期或最终现金流的规定日期 | "结算日"（不同——指 T+n）；"到期日"（不够技术化） |
| calculation date | 用于确定支付金额的日期（如计息期结束日） | "定盘日"（不同——指基准被观察之日）；"确定日"（不够标准） |
| calculation agent | 负责按 ISDA 定义计算支付金额的一方 | "代理人"（过于含糊）；"付款代理人"（不同角色） |
| fixed rate | 一开始设定、合同期内固定的利率 | "固定利息"；"票息"（用于债券，不用于衍生品） |
| floating rate | 与基准（EURIBOR、SOFR、€STR）加利差挂钩的利率 | "可变利率"（可接受）；"基准利率"（不精确） |
| reference rate / benchmark rate | 用于确定支付的已发布指数（EURIBOR、SOFR、€STR、SONIA） | "基础利率"；"指数"（过于笼统） |
| EURIBOR | 欧元银行间同业拆借利率（每日发布，主要欧元基准） | "Euribor"（大小写）；其他泛称"同业拆借利率"术语 |
| SOFR | 有担保隔夜融资利率（后 LIBOR 时代主要美元基准） | "LIBOR 替代品"（SOFR 现在是主要基准，不是替代品）；其他未经核实现势的基准名称 |
| €STR | 欧元短期利率（后 EONIA 时代主要欧元隔夜基准） | "EONIA 替代品"（€STR 现在是主要基准）；较旧的基准名称 |
| spread | 加在浮动利率上的固定调整（以基点计） | "利差"（部分情境可接受）；"增量" |
| mark-to-market | 未平仓合同头寸的当前市场估值 | "盯市估值"（可接受）；"MTM"（首次全称使用后使用） |
| prime brokerage agreement | 提供清算、融资和结算服务的综合设施 | "主经纪合同"；"主经纪协议"（不够正式） |
| give-up agreement | 允许介绍经纪商将交易让渡给清算经纪商的协议 | "清算安排"；"交易转让"（不精确） |
| ISDA Credit Support Annex (CSA) | ISDA 主协议下的标准化担保框架，规定初始/变动保证金要求、合格担保品、阈值、扣减率 | "保证金协议"；"担保协议"（不够精确）；"担保附件"（术语错误） |
| novation | 用新合同替换现有合同，通常为变更对手方 | "合同替换"（不够技术化）；"替代"（衍生品情境中非标准法律术语） |
| portfolio reconciliation | 对手方之间定期核对交易头寸和敞口 | "头寸核对"（可接受）；"投资组合匹配"（不够标准） |
| portfolio compression | 终止多笔抵消交易以降低系统性风险（EMIR 要求） | "交易压缩"（可接受）；"头寸净额结算"（不同流程） |

## ISDA 特定术语

| 规范英文术语 | 用法 / 含义 | 避免使用 |
|---|---|---|
| termination event | 允许按当时市场价值终止合同的（通常非违约的）事件 | "终止权"；"退出事件" |
| event of default | 对手方的违约或失败，触发提前终止和结算 | "违约"；"未付款"（过于狭窄） |
| early termination | 在规定到期日之前终止，通常紧随违约事件 | "提前退出"；"过早终止"（不够正式） |
| close-out amount | 终止后计算的、反映被终止交易市场价值的金额 | "结算金额"；"退出价值" |
| netting | 抵销各方的欠款以确定净支付额 | "抵销"；"补偿"（有歧义） |
| close-out netting | 终止事件后对所有未平仓交易的净额结算 | "终止净额结算"；"最终净额结算" |
| payment netting | 同一合同下规定付款的定期净额结算 | "结算净额结算"；"中期净额结算" |
| netting agreement | 允许跨多个合同净额结算的独立协议 | "主净额结算协议"（可接受）；"清算协议"（不同） |
| representations | 对手方关于权限、偿付能力、监管地位的陈述 | "保证"（重叠但侧重不同）；"陈述"（过于含糊） |
| covenants | 对手方行为的持续义务和限制 | "承诺"（英式英语可接受）；"义务"（不够技术化） |
| cross-default | 对手方在其他重大合同下违约时触发违约的条款 | "交叉加速到期"（相关但不同）；"关联违约" |
| flawed asset | 具有妨碍完全转让的法律缺陷的担保/担保品（ISDA 特定概念） | "有缺陷的证券"；"问题担保品" |
| set-off | 将一方欠付的金额与其应收金额抵销的权利 | "抵销"；"相互抵销"（可接受） |
| ISDA Protocol | 使各方通过相互加入修订现有 ISDA 协议的市场级机制（如 IBOR 回退协议、ISDA 2020 协议） | ISDA 修订（不够精确） |
| master confirmation agreement | 针对特定衍生品产品类型的预先约定条款，补充 ISDA 主协议；减少重复交易的文档 | 标准确认书（不够精确）；模板确认书（非标准） |
| transfer / assignment | 向第三方转让权利和义务（须受限制） | "让与"（大陆法系术语；英文用 "assignment"）；"更新"（法律替代，不同） |

## 保证金与担保术语

| 规范英文术语 | 用法 / 含义 | 避免使用 |
|---|---|---|
| margin / collateral | 为担保敞口而质押的资产或按 CSA 缴付的资产 | "担保"（范围更广）；"保证"（暗示有保证人） |
| initial margin | 预先要求用于覆盖潜在未来敞口的保证金（EMIR 要求） | "IM"；"初始保证金" |
| variation margin | 反映盯市变化的每日/定期保证金调整 | "VM"；"盯市保证金"；"每日保证金" |
| margin call | 阈值被突破或盯市亏损后的追加保证金要求 | "担保催缴"（可接受）；"资金催缴"（不精确） |
| financial collateral arrangement | CSA 下对金融资产的正式担保安排 | "担保协议"；"担保安排" |
| financial pledge | 对金融资产的质押/留置权，通常采用所有权转移或质押形式 | "担保权益"；"留置权"（此情境中不够技术化） |
| title transfer | 担保品法定所有权的转移（作为担保，而非绝对出售） | "所有权转移"；"担保转移" |
| credit support annex (CSA) | 见上文 ISDA Credit Support Annex | "保证金协议"；"担保附件" |
| haircut | 对担保品价值的扣减率（如高流动性证券按市场价值的 98%） | "降价"（可接受）；"折扣"（过于含糊） |
| eligible securities / eligible collateral | 满足 CSA 要求的证券（如政府债券、投资级公司债） | "已批准担保品"；"可接受证券"（不够标准） |
| threshold | CSA 限额：若净敞口超过阈值，则需进行证券转移 | "限额"；"容忍水平"（不精确） |
| minimum transfer amount (MTA) | CSA 限额：低于阈值的金额不转移（行政性最低限额）。首次全称使用后缩写为 "MTA"，与本词典其他处注明的 ISDA/CSA 缩写惯例一致。 | 转移下限（非正式）；最低催缴金额（不精确） |
| return of excess collateral | CSA 条款，要求证券超过所需金额时返还担保品 | "超额返还"；"过度担保释放" |

## 回购与证券借贷

| 规范英文术语 | 用法 / 含义 | 避免使用 |
|---|---|---|
| repurchase agreement (repo) | 出售证券并同时承担按约定价格/日期回购的义务 | "回购合同"（可接受）；"逆回购"（对方视角） |
| repo transaction | GMRA 下构建的个别回购交易 | "回购交易"（可接受）；"回购操作" |
| term repo | 固定期限的回购（如 30 天、3 个月） | "定期回购"；"远期回购" |
| overnight repo | 一天期限、每日展期的回购 | "隔夜回购"；"次日回购" |
| repo rate | 回购交易的利率（以售价折扣百分比表示） | "融资利率"（范围更广）；"货币市场利率"（过于笼统） |
| securities lending | 为换取费用/回报而临时转移证券占有 | "证券贷款"；"股票借贷"（重叠） |
| securities lender | 在借贷安排中转移证券的一方 | "所有人"；"原持有人" |
| securities borrower | 在借贷安排下接收证券的一方 | "临时所有人"；"使用者" |
| fee | 借款人因使用证券向出借人支付的报酬 | "佣金"；"返费"（负费用） |
| substitution of securities | 出借人以满足相同标准的其他证券替代的权利 | "证券替换"；"证券互换" |
| recall of securities | 出借人要求归还借出证券的权利 | "归还要求"；"召回权" |
| Global Master Repurchase Agreement (GMRA) | 回购交易的标准框架，由 ICMA/SIFMA 维护 | "GMRA 协议"（冗余）；"回购主协议" |
| Global Master Securities Lending Agreement (GMSLA) | 证券借贷交易的标准框架，由 ICMA/LSTA 维护 | "GMSLA 协议"（冗余）；"证券贷款主协议" |

## 市场基础设施与监管

| 规范英文术语 | 用法 / 含义 | 避免使用 |
|---|---|---|
| central counterparty (CCP) | 作为所有交易清算/结算对手方介入自身的实体 | "清算对手方"；"CCP 实体"（冗余） |
| clearing house | 运营清算系统的实体（可能是也可能不是 CCP） | "清算中心"；"结算所"（不够精确） |
| clearing | 通过 CCP 对交易进行匹配、确认和结算的过程 | "结算"（不同——资金/证券的最终转移）；"登记" |
| settlement | 为完成交易而最终转移证券和资金 | "清算"（常重叠但清算是先行的）；"执行" |
| central securities depository (CSD) | 负责证券的固定化、保管和结算的实体 | "证券存管处"（可接受）；"中央金库"（不精确） |
| trading venue | 证券交易所在的受监管市场或多边设施 | "交易所"（受监管市场的法律术语）；"交易平台"（过于笼统） |
| regulated market | 满足法律/透明度要求、获正式承认并受监督的场所 | "证券交易所"（特定类型）；"官方市场"（不够标准） |
| multilateral trading facility (MTF) | 证券交易的替代场所，监管较受监管市场宽松 | "替代场所"；"交易设施"（过于宽泛） |
| systematic internaliser (SI) | 定期以自有账户买卖金融工具的投资公司 | "内部撮合商"；"自营交易者"（不同角色） |
| EMIR (Regulation (EU) No. 648/2012) | 欧盟衍生品市场基础设施条例（清算、报告、风险缓释） | "EMIR 条例"（冗余）；"衍生品条例"（不精确） |
| MiFID II (Directive 2014/65/EU) | 欧盟金融工具市场指令二（投资服务/产品监管） | "MiFID"（旧版本——须指明 II）；"MiFID2"（非标准缩写） |
| MiFIR (Regulation (EU) No. 600/2014) | 欧盟金融工具市场条例（交易报告/透明度） | "MiFIR 条例"（冗余）；"交易透明度条例" |
| clearing obligation | EMIR 要求某些衍生品通过 CCP 清算 | "强制清算"；"清算要求"（不够正式） |
| reporting obligation | EMIR/MiFID II 下向交易存储库报告交易的要求 | "交易报告"；"披露要求"（范围更广） |
| trade repository | 经批准用于存储和报告衍生品交易信息的系统（EMIR 要求） | "数据存储库"；"中央存储库"（不精确） |
| Legal Entity Identifier (LEI) | 分配给法律实体以实现无歧义识别的 20 字符代码 | "LEI 代码"（冗余）；"实体标识符"（过于宽泛） |
| financial counterparty (FC) | EMIR 下被归类为金融实体的对手方（银行、投资公司、保险等） | "金融方"；"金融机构"（EMIR 情境中不够精确） |
| non-financial counterparty (NFC) | 超过阈值后须承担清算义务的非金融实体（企业客户） | "非金融方"；"企业对手方" |
| clearing member | 被接纳为 CCP 成员、以自有账户和/或为客户清算交易的实体 | CCP 成员（可接受）；直接参与者（不够精确） |
| client clearing | CCP 通过清算成员代表客户清算交易 | 间接清算（不够精确） |
| clearing threshold | EMIR 要求：NFC 的场外衍生品总名义金额超过限额后必须清算 | "清算豁免阈值"；"清算豁免水平"（相反概念） |
| risk mitigation techniques | EMIR 对未清算衍生品要求的措施：每日盯市、担保、压缩 | "风险缓释"；"替代风险控制"（不够具体） |

## 章节标题

| 规范英文标题 | 避免使用 |
|---|---|
| DEFINITIONS | "DEFINED TERMS"（定义术语）；"INTERPRETATION"（解释）；将定义部分与一般解释混同 |
| SCOPE / SUBJECT MATTER | "APPLICATION"（适用）；"OBJECT"（标的）；"PURPOSE"（目的，不够正式） |
| MARGIN OBLIGATIONS | "COLLATERAL REQUIREMENTS"（担保要求）；"SECURITY"（担保）；避免泛称"GUARANTEES"（保证） |
| EVENTS OF DEFAULT | "DEFAULT"（违约）；"TERMINATION EVENTS"（终止事件，不同概念——含非违约事件） |
| EARLY TERMINATION | "TERMINATION"（终止）；"CLOSEOUT"（结算——是终止的结果） |
| CALCULATIONS AND PAYMENTS | "PAYMENT MECHANICS"（支付机制）；"FLOATING RATE CALCULATIONS"（浮动利率计算）；"COMPUTATIONS"（不够正式） |
| NETTING | "CLOSE-OUT NETTING"（结算净额结算）；"COMPENSATION"（补偿，有歧义）；"OFFSETTING"（抵销，不够正式） |
| COLLATERAL | "MARGIN"（保证金）；"SECURITY"（担保，更窄）；"GUARANTEES"（保证，不正确——担保品不是保证） |
| REPRESENTATIONS AND WARRANTIES | "REPRESENTATIONS"（陈述）；"WARRANTIES"（保证，拆分削弱法律效力）；"ASSURANCES"（过于非正式） |
| GOVERNING LAW | "LAW APPLICABLE"（适用法律）；"JURISDICTION"（管辖）；"APPLICABLE LAW"（可接受替代） |

## 注释

- **ISDA 术语**：翻译引用或实施 ISDA 协议的文件时，使用 ISDA 主协议中的确切英文术语。这些术语高度标准化，任何偏差都会产生法律不确定性。ISDA 定义有多个版本（1991、2000、2006）；确认适用哪个版本。

- **ISDA Credit Support Annex（CSA）**：这是 ISDA 主协议下保证金管理的基础文件。有两个标准版本：1994 年 CSA（较旧，很少使用）和 2016 年 CSA（现行标准）。部分合同使用附表修订而非完整 CSA。始终识别适用哪种机制。

- **Netting/set-off/clearing 歧义**：许多源语言使用单一术语，可指"净额结算"（ISDA/金融情境）、"抵销"（一般法律）、"清算"（CCP 情境）或"补偿/损害赔偿"（广义法律）。务必根据情境和合同结构确定。分词典提供源语言映射。

- **Regulation/settlement/rules 歧义**：许多源语言使用单一术语，可指"条例"（欧盟立法文件）、"结算"（交易的）、"规则"（交易所/CCP 的）或"章程细则"（内部规则）。取决于情境；确认确切含义。分词典提供源语言映射。

- **基准改革**：后 LIBOR 转型期，对银行间同业拆借利率或其他基准的引用必须对照现行利率核实。€STR 和 SOFR 现在是主要基准。确认文件没有冻结过时的基准引用。

- **Novation 和 give-up 协议**：Novation 在二级市场交易中常见（对手方替换）。Give-up 协议与介绍经纪商一起使用。确保根据交易情境使用正确的术语。

- **投资组合压缩与 EMIR**：投资组合压缩是 EMIR 强制要求的降低系统性风险技术。它不同于投资组合核对（常规匹配）。

- **保留缩写不展开**：ISDA、CSA、GMRA、GMSLA、CCP、CSD、MTF、LEI、EMIR、MiFID、MiFIR——这些在英文中普遍使用，不应翻译，也不应在文件中首次使用后展开。

- **美式与英式英语**：本词典默认使用美式英语惯例（如 "recognized"、"license" 作名词）。在重要处注明英式替代拼写（如美国 "authorization" 与英国 "authorisation"）。

# 交易 / 资本市场术语表

交易和资本市场协议的标准英文术语：ISDA 主协议、衍生品、回购协议、主经纪业务、清算、保证金、证券借贷及相关文书。包括 EMIR、MiFID 和市场基础设施术语。

> **按语言分子词表说明。** 本英文参考文件仅为交易与资本市场的跨语言权威文件；金融与银行术语位于 `references/finance-banking.md`。在按语言分子词表中，两个领域合并为一个文件：`sub-lexicons/<语言>-finance-banking.md` 涵盖两者。处理资本市场文件时，应阅读两个英文参考文件，但仅阅读单个按语言分子词表。

## 核心交易/衍生品术语

| 规范英文术语 | 用法/含义 | 避免使用 |
|---|---|---|
| ISDA Master Agreement | 两个交易对手之间衍生品交易的标准框架 | generic "master agreement"; confuse with individual transaction confirmations |
| confirmation | ISDA 主协议项下单项交易细节 | "attestation"; mixing with formal legal assignment |
| schedule | ISDA 主协议的标准条款和修订 | "appendix"（过于含糊）; "annex"（CSA 优先使用） |
| ISDA Definitions | 已发布的衍生品计算和支付流程规范 | paraphrasing with "definitions section" |
| transaction | 在 ISDA 主协议下执行的单项交易 | "operation"; "deal"（不精确） |
| derivative / derivative instrument | 价值衍生自基础资产/利率/指数的金融合约 | "derived product"; "financial product"（过于宽泛） |
| OTC derivative | 场外衍生品（未清算、双边） | "private derivative"; "non-exchange"（不精确） |
| exchange-traded derivative | 在受监管市场上通过 CCP 清算的衍生品 | "exchange product"; "cleared derivative"（并非所有交易所交易衍生品均经清算） |
| interest rate swap (IRS) | 同一币种固定利率与浮动利率支付的互换 | "rate exchange"; "swap contract"（过于笼统） |
| cross-currency swap | 两种不同币种本金和利息的互换 | "currency swap"（不够精确）; "FX swap"（不同产品） |
| forward | 按约定未来价格买卖的双边合约 | "forward contract"（可接受，但 "forward" 为标准）; "futures"（交易所交易，不同） |
| option | 在指定日期或之前按约定价格买卖的权利（而非义务） | "optional contract"; "conditional derivative" |
| cap | 限制最高利率的浮动利率衍生品 | "ceiling"; "rate cap"（可接受但不太标准） |
| floor | 设定最低利率的浮动利率衍生品 | "base rate"; "rate floor"（可接受但不太标准） |
| collar | 利率上下限（cap 和 floor）的组合，通常零成本 | "rate collar"（可接受但不太标准） |
| credit default swap (CDS) | 针对参考实体违约的类保险保护 | "credit protection"; "default insurance"（错误——并非保险产品） |
| credit event | 触发信用违约互换付款的事件（破产、未能付款、重组）；按 ISDA 信用衍生品定义界定 | Default event（过于宽泛）; Trigger event（过于含糊） |
| total return swap | 交易对手获得参考资产的全部经济回报（价格 + 息票） | "return swap"; "TRS"（首次完整使用后可接受缩写） |
| notional amount | 用于计算付款的名义金额（多数衍生品中并不实际交换） | "principal"（通常指实际支付金额）; "contract value"（不精确） |
| effective date | 交易日或合同条款开始生效的日期 | "start date"; "commencement date"（不够专业） |
| termination date / maturity date | 合同终止并支付最后款项的日期 | "end date"; "expiry date"（不够精确） |
| payment date | 中期或最终现金流的预定日期 | "settlement date"（不同——指 T+n）; "due date"（不够专业） |
| calculation date | 用于确定支付金额的日期（如计息期结束日） | "fixing date"（不同——观察基准的日期）; "determination date"（不太标准） |
| calculation agent | 负责按 ISDA 定义计算支付金额的一方 | "agent"（过于含糊）; "paying agent"（不同角色） |
| fixed rate | 初始即设定、合同期内固定的利率 | "fixed interest"; "coupon"（用于债券而非衍生品） |
| floating rate | 挂钩基准利率（EURIBOR、SOFR、€STR）加利差的利率 | "variable rate"（可接受）; "benchmark rate"（不精确） |
| reference rate / benchmark rate | 用于确定支付的已发布指数（EURIBOR、SOFR、€STR、SONIA） | "base rate"; "index"（过于笼统） |
| EURIBOR | 欧元银行间同业拆借利率（每日发布，欧元主要基准） | "Euribor"（大小写）; other generic "interbank rate" terms |
| SOFR | 有担保隔夜融资利率（LIBOR 后美元主要基准） | "LIBOR replacement"（SOFR 现为主要基准，而非替代品）; other benchmark names if not verified current |
| €STR | 欧元短期利率（EONIA 后欧元主要隔夜基准） | "EONIA replacement"（€STR 现为主要基准）; older benchmark names |
| spread | 加于浮动利率的固定调整（以基点计） | "margin"（某些语境可接受）; "increment" |
| mark-to-market | 未平仓合约头寸的现行市场估值 | "mark-to-market valuation"（可接受）; "MTM"（仅在首次完整使用后使用） |
| prime brokerage agreement | 提供清算、融资和结算服务的综合服务安排 | "prime broker contract"; "prime broker agreement"（不够正式） |
| give-up agreement | 允许介绍经纪商将交易让渡给清算经纪商的协议 | "clearing arrangement"; "trade assignment"（不精确） |
| ISDA Credit Support Annex (CSA) | ISDA 主协议下的标准化抵押框架，规定初始/变动保证金要求、合格抵押品、门槛、折扣率 | "margin agreement"; "collateral agreement"（不够精确）; "security annex"（术语错误） |
| novation | 以新合同取代既有合同，通常为变更交易对手 | "contract replacement"（不够专业）; "substitution"（衍生品语境中非标准法律术语） |
| portfolio reconciliation | 交易对手之间定期核对交易头寸和敞口 | "position reconciliation"（可接受）; "portfolio matching"（不太标准） |
| portfolio compression | 终止多笔对冲交易以降低系统性风险（EMIR 要求） | "trade compression"（可接受）; "position netting"（不同流程） |

## ISDA 特定术语

| 规范英文术语 | 用法/含义 | 避免使用 |
|---|---|---|
| termination event | 允许按当时市场价值终止合同的事件（通常为非违约事件） | "termination right"; "exit event" |
| event of default | 交易对手的违约或失败，触发提前终止和结清 | "default"; "failure to pay"（过于狭窄） |
| early termination | 在预定到期日之前终止，通常在违约事件之后 | "early exit"; "premature termination"（不够正式） |
| close-out amount | 终止后计算的、反映被终止交易市场价值的金额 | "settlement amount"; "exit value" |
| netting | 抵销各方所欠金额以确定净付款 | "offsetting"; "compensation"（含混） |
| close-out netting | 终止事件后对所有未平仓交易的净额结算 | "termination netting"; "final netting" |
| payment netting | 同一合同下预定付款的定期净额结算 | "settlement netting"; "interim netting" |
| netting agreement | 允许跨多份合同净额结算的独立协议 | "master netting agreement"（可接受）; "clearing agreement"（不同） |
| representations | 交易对手关于授权、偿付能力、监管地位的陈述 | "warranties"（重叠但侧重不同）; "statements"（过于含糊） |
| covenants | 对交易对手行为的持续义务和限制 | "undertakings"（英式英语可接受）; "commitments"（不够专业） |
| cross-default | 交易对手在其他重大合同下违约即触发违约的条款 | "cross-acceleration"（相关但不同）; "linked default" |
| flawed asset | 存在妨碍完全转让的法律瑕疵的担保品/抵押品（ISDA 特有概念） | "defective security"; "problematic collateral" |
| set-off | 以一方所欠金额抵销其被欠金额的权利 | "offset"; "mutual offset"（可接受） |
| ISDA Protocol | 使各方通过相互加入即可修订既有 ISDA 协议的市场上普遍机制（如 IBOR 回退协议、ISDA 2020 协议） | ISDA amendment（不够精确） |
| master confirmation agreement | 特定衍生品产品类型的预先约定条款，补充 ISDA 主协议；减少重复交易的文书工作 | Standard confirmation（不够精确）; Template confirmation（非标准） |
| transfer / assignment | 向第三方转让权利和义务（受限制约束） | "cession"（大陆法术语；英文中使用 "assignment"）; "novation"（法律上的替换，不同） |

## 保证金与抵押品术语

| 规范英文术语 | 用法/含义 | 避免使用 |
|---|---|---|
| margin / collateral | 为担保敞口而质押的资产，或按 CSA 交存的抵押品 | "security"（更宽泛）; "guarantee"（暗指保证人） |
| initial margin | 为覆盖潜在未来敞口而预先要求的保证金（EMIR 要求） | "IM"; "opening margin" |
| variation margin | 反映按市值计价变动的每日/定期保证金调整 | "VM"; "mark-to-market margin"; "daily margin" |
| margin call | 阈值被突破或按市值计价亏损后要求追加保证金的通知 | "collateral call"（可接受）; "funding call"（不精确） |
| financial collateral arrangement | CSA 下对金融资产的正式担保安排 | "collateral agreement"; "security arrangement" |
| financial pledge | 对金融资产的担保/留置，通常以所有权转移或质押形式 | "security interest"; "lien"（在此语境不够专业） |
| title transfer | 抵押品法定所有权的转移（作为担保，而非绝对出售） | "ownership transfer"; "security transfer" |
| credit support annex (CSA) | 见上文 ISDA 信用支持附件 | "margin agreement"; "collateral annex" |
| haircut | 对抵押品价值适用的折扣（如高流动性证券按市值 98%） | "markdown"（可接受）; "discount"（过于含糊） |
| eligible securities / eligible collateral | 符合 CSA 要求的证券（如政府债券、投资级公司债） | "approved collateral"; "acceptable securities"（不太标准） |
| threshold | CSA 限额：如净敞口超过阈值，须进行担保品转移 | "limit"; "tolerance level"（不精确） |
| minimum transfer amount (MTA) | CSA 限额：低于门槛的金额不予转移（管理上的最低限额）。首次完整拼写后缩写为 "MTA"，与本术语表其他地方注明的 ISDA/CSA 缩写惯例一致。 | transfer floor（非正式）; minimum call amount（不精确） |
| return of excess collateral | 要求担保品超过所需金额时予以返还的 CSA 条款 | "excess return"; "overcollateral release" |

## 回购与证券借贷

| 规范英文术语 | 用法/含义 | 避免使用 |
|---|---|---|
| repurchase agreement (repo) | 出售证券并同时承担按约定价格/日期回购义务 | "repo contract"（可接受）; "reverse repo"（相反方的视角） |
| repo transaction | 按 GMRA 构建的单项回购交易 | "repo deal"（可接受）; "repo operation" |
| term repo | 固定期限的回购（如 30 天、3 个月） | "time repo"; "forward repo" |
| overnight repo | 期限一天的隔夜回购，每日滚动 | "O/N repo"; "next-day repo" |
| repo rate | 回购交易的利率（以出售价格折扣百分比表示） | "financing rate"（更宽泛）; "money market rate"（过于笼统） |
| securities lending | 以收取费用/回报为对价转移证券的临时占有 | "loan of securities"; "stock lending"（重叠） |
| securities lender | 在借贷安排中转移证券的一方 | "owner"; "original holder" |
| securities borrower | 在借贷安排下接收证券的一方 | "temporary owner"; "user" |
| fee | 借款人因使用证券向出借人支付的报酬 | "commission"; "rebate"（负费用） |
| substitution of securities | 出借人以符合相同标准的其他证券替代的权利 | "replacement of securities"; "security swap" |
| recall of securities | 出借人要求返还已借出证券的权利 | "return demand"; "recall right" |
| Global Master Repurchase Agreement (GMRA) | 回购交易的标准框架，由 ICMA/SIFMA 维护 | "GMRA agreement"（赘余）; "repurchase master agreement" |
| Global Master Securities Lending Agreement (GMSLA) | 证券借贷交易的标准框架，由 ICMA/LSTA 维护 | "GMSLA agreement"（赘余）; "securities loan master agreement" |

## 市场基础设施与监管

| 规范英文术语 | 用法/含义 | 避免使用 |
|---|---|---|
| central counterparty (CCP) | 作为所有交易清算/结算对手方的机构 | "clearing counterparty"; "CCP entity"（赘余） |
| clearing house | 运营清算系统的机构（可能是也可能不是 CCP） | "clearing centre"; "settlement house"（不够精确） |
| clearing | 通过 CCP 进行交易撮合、确认和结算的过程 | "settlement"（不同——资金/证券的最终转移）; "registration" |
| settlement | 完成交易的证券和资金最终转移 | "clearing"（常重叠，但清算是先行环节）; "execution" |
| central securities depository (CSD) | 负责证券的无纸化托管、保管和结算的机构 | "securities depository"（可接受）; "central vault"（不精确） |
| trading venue | 证券交易的受监管市场或多边平台 | "exchange"（受监管市场的法律术语）; "trading platform"（过于笼统） |
| regulated market | 满足法律/透明度要求的正式认可、受监管场所 | "stock exchange"（特定类型）; "official market"（不太标准） |
| multilateral trading facility (MTF) | 证券交易的替代场所，监管要求低于受监管市场 | "alternative venue"; "trading facility"（过于宽泛） |
| systematic internaliser (SI) | 经常以自有账户买卖金融工具的投资公司 | "internaliser"; "proprietary trader"（不同角色） |
| EMIR (Regulation (EU) No. 648/2012) | 关于衍生品市场基础设施（清算、报告、风险缓释）的欧盟条例 | "EMIR regulation"（赘余）; "derivatives regulation"（不精确） |
| MiFID II (Directive 2014/65/EU) | 欧盟《金融工具市场指令 II》（投资服务/产品监管） | "MiFID"（旧版——须注明 II）; "MiFID2"（非标准缩写） |
| MiFIR (Regulation (EU) No. 600/2014) | 欧盟《金融工具市场条例》（交易报告/透明度） | "MiFIR regulation"（赘余）; "trading transparency regulation" |
| clearing obligation | EMIR 要求某些衍生品须通过 CCP 清算 | "mandatory clearing"; "clearing requirement"（不够正式） |
| reporting obligation | EMIR/MiFID II 要求向交易数据库报告交易 | "trade reporting"; "disclosure requirement"（更宽泛） |
| trade repository | 存储和报告衍生品交易信息的获批系统（EMIR 要求） | "data repository"; "central repository"（不精确） |
| Legal Entity Identifier (LEI) | 分配给法律实体、实现唯一识别的 20 字符代码 | "LEI code"（赘余）; "entity identifier"（过于宽泛） |
| financial counterparty (FC) | 依 EMIR 归类为金融实体的交易对手（银行、投资公司、保险等） | "financial party"; "financial institution"（EMIR 语境不够精确） |
| non-financial counterparty (NFC) | 非金融实体（公司客户），超过阈值时受清算义务约束 | "non-financial party"; "corporate counterparty" |
| clearing member | 获准成为 CCP 成员、以自有账户和/或为客户清算交易的实体 | CCP member（可接受）; Direct participant（不够精确） |
| client clearing | CCP 经由清算成员为客户的交易进行清算 | Indirect clearing（不够精确） |
| clearing threshold | EMIR 要求：NFC 的名义总额超过限额时必须清算 OTC 衍生品 | "clearing exemption threshold"; "clearing exemption level"（相反概念） |
| risk mitigation techniques | EMIR 对未清算衍生品要求的措施：每日按市值计价、抵押、压缩 | "risk mitigation"; "alternative risk controls"（不够具体） |

## 条款标题

| 规范英文标题 | 避免使用 |
|---|---|
| DEFINITIONS | "DEFINED TERMS"; "INTERPRETATION"; mixing definition section with general interpretation |
| SCOPE / SUBJECT MATTER | "APPLICATION"; "OBJECT"; "PURPOSE"（不够正式） |
| MARGIN OBLIGATIONS | "COLLATERAL REQUIREMENTS"; "SECURITY"; avoid generic "GUARANTEES" |
| EVENTS OF DEFAULT | "DEFAULT"; "TERMINATION EVENTS"（不同概念——包括非违约事件） |
| EARLY TERMINATION | "TERMINATION"; "CLOSEOUT"（结清是终止的结果） |
| CALCULATIONS AND PAYMENTS | "PAYMENT MECHANICS"; "FLOATING RATE CALCULATIONS"; "COMPUTATIONS"（不够正式） |
| NETTING | "CLOSE-OUT NETTING"; "COMPENSATION"（含混）; "OFFSETTING"（不够正式） |
| COLLATERAL | "MARGIN"; "SECURITY"（更窄）; "GUARANTEES"（错误——抵押品不是保证） |
| REPRESENTATIONS AND WARRANTIES | "REPRESENTATIONS"; "WARRANTIES"（拆分削弱法律效力）; "ASSURANCES"（过于非正式） |
| GOVERNING LAW | "LAW APPLICABLE"; "JURISDICTION"; "APPLICABLE LAW"（可接受的替代） |

## 注释

- **ISDA 术语**：翻译援引或实施 ISDA 协议的文件时，使用 ISDA 主协议中的精确英文术语。这些术语高度标准化，任何偏离都会造成法律不确定性。ISDA 定义有多个版本（1991、2000、2006）；须确认适用哪个版本。

- **ISDA 信用支持附件（CSA）**：这是 ISDA 主协议下保证金管理的基础文件。有两个标准版本：1994 年 CSA（较旧，很少使用）和 2016 年 CSA（现行标准）。有些合同使用附表修订而非完整 CSA。始终指明适用哪种机制。

- **净额结算/抵销/清算的歧义**：许多源语言使用一个词可能表示 "netting"（ISDA/金融语境）、"set-off"（一般法律）、"clearing"（CCP 语境）或 "compensation/damages"（广义法律）。始终根据语境和合同结构确定含义。子词表提供源语言映射。

- **条例/结算/规则的歧义**：许多源语言使用一个词可能表示 "regulation"（欧盟立法文件）、"settlement"（交易结算）、"rules"（交易所/CCP 规则）或 "by-laws"（内部章程）。视语境而定；确认确切含义。子词表提供源语言映射。

- **基准改革**：LIBOR 转型后，对银行间同业拆借利率或其他基准的引用必须对照现行利率核实。€STR 和 SOFR 现为主要基准。确认文件未固守过时的基准引用。

- **Novation 与 give-up 协议**：Novation 在二级市场交易（交易对手替换）中常见。Give-up 协议与介绍经纪商配合使用。根据交易语境确保使用正确的术语。

- **投资组合压缩与 EMIR**：投资组合压缩是 EMIR 强制要求的降低系统性风险的技术。区别于投资组合核对（日常性匹配）。

- **缩写不展开**：ISDA、CSA、GMRA、GMSLA、CCP、CSD、MTF、LEI、EMIR、MiFID、MiFIR——这些在英文中普遍使用，首次使用后不应翻译或展开。

- **英式与美式英语**：本术语表使用英式英语惯例（如 "recognised"、名词 "licence"）。在重要处注明美式替代拼写（如 "authorization" 与 "authorisation"）。

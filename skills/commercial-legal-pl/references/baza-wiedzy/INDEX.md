# 知识库——索引

支持理解 IT 合同法律类型和条款结构的法律学说、判例和合同策略。文件**按法律问题**分组，而非按合同类型——因为一个问题（如 lucrum cessans、著作权、RODO）出现在多种合同类型中。

## 顶层原则——知识与合同文本

知识库中的所有文件都是**学说知识**，而非可复制进合同的文本。此处对《民法典》/《著作权法》/RODO/《劳动法典》条文的众多引用是学说语境。在生成的合同内容中，适用 **W6——节制引用法条** 原则（`references/style-redakcyjny.md`）。

## 知识库地图

### 著作权与软件

| 文件 | 问题 | 何时使用 |
|---|---|---|
| `01-maintenance-art750-kc.md` | IT 维护与 SLA——《民法典》第 750 条 | 合同包含"maintenance"、"utrzymanie"、"wsparcie"、"SLA"、"managed services"。问题：承揽还是委托/服务？ |
| `02-przeniesienie-praw-oprogramowanie.md` | 使用领域、未来作品（《著作权法》第 41、74 条） | 合同包含"przeniesienie praw autorskich"、"pola eksploatacji"、"Utwór"。未列举领域 = 关键错误 |
| `03-prawa-zalezne-osobiste-program.md` | 衍生作品、作者精神权利（《著作权法》第 74、77 条） | 涉及计算机程序和开发阶段的合同。关于修改、作者监督、署名权的问题 |
| `04-open-source-copyleft.md` | Open source、copyleft、赔偿（《著作权法》第 75-76 条） | IT 实施合同。客户希望防范 copyleft。关于 GPL/AGPL/MIT、"禁止 open source" 的问题 |
| `11-wizerunek-a-prawa-autorskie.md` | 肖像（《著作权法》第 81 条）与视听作品著作财产权——制度自主性、同意撤回 ex nunc、第 81 条第 2 款例外、同意范围的举证责任 | 涉及人物（教练、演讲者、模特）的录音案件。含"全部著作权"条款、涵盖肖像材料的承揽合同。肖像和解与协议。"我们有著作权，所以我们可以播放"的论点 |

### 合同责任

| 文件 | 问题 | 何时使用 |
|---|---|---|
| `05-cap-lucrum-wina-umyslna.md` | 责任上限、排除 lucrum cessans、《民法典》第 473 条第 2 款界限 | 合同中出现"cap"、"limit of liability"、"lucrum cessans"、"consequential damages"、"wina umyślna"。生成"责任"条 |
| `06-sila-wyzsza-i-podwykonawcy.md` | 不可抗力、对分包商的责任（《民法典》第 474 条）、法律变更 | 合同中出现"force majeure"、"podwykonawca"、"operator chmury"、"change of law"。关于 AWS/Azure/GCP 责任的问题 |
| `07-indemnifikacja-kary-umowne.md` | 赔偿条款（hold harmless）、合同违约金（《民法典》第 484 条第 1 款）、补充损害赔偿 | "Indemnity"、"hold harmless"、"kara umowna"、"odszkodowanie uzupełniające"、"exclusive remedy" |

### 规则与电子服务

| 文件 | 问题 | 何时使用 |
|---|---|---|
| `13-regulamin-usdde-hosting-ai.md` | 《电子服务提供法》规则——必备要素（第 8 条）、托管责任豁免（第 14 条）、DSA（通知与行动、决定说明理由）、AI 服务作为电子服务的变体 | 创建或分析托管/SaaS/域名/AI 规则。关于法定义务范围、责任豁免、AUP、DSA 的问题 |

### AI Act 合规

| 文件 | 问题 | 何时使用 |
|---|---|---|
| `14-polityka-ai-wdrozenie.md` | 公司 AI 政策——律师评注：逐条、关键缺口（登记册、RODO 委托协议、负责人）、实施检查清单、AI Act 期限表 | 客户/公司想实施 AI 政策。关于 AI Act 第 4 条、第 5 条禁令、第 50 条聊天机器人/深度伪造义务、AI 事件、AI 招聘——何时需要单独程序的问题。 |

### 解释与解读

| 文件 | 问题 | 何时使用 |
|---|---|---|
| `12-wykladnia-oswiadczen-woli.md` | 组合解释（《民法典》第 65 条）、语言解释优先、派生方法、禁止造法——附最高法院 2024-2025 年论点 | 有争议的合同条款——法院会赋予其什么含义？歧义风险分析。概念理解之争。企业内部劳动法文件（规则、ZUZP）。 |

### IT 合同中的 RODO

| 文件 | 问题 | 何时使用 |
|---|---|---|
| `08-rodo-powierzenie-konstrukcja.md` | 控制者/处理者/共同控制者资格认定、RODO 第 28 条第 3 款、次处理者、数据返还/删除 | "Powierzenie przetwarzania"、"DPA"、"procesor"、"administrator"、"subprocesor"。生成委托协议 |
| `09-rodo-bezpieczenstwo-i-naruszenia.md` | 技术和组织措施（RODO 第 32 条）、安全事件（RODO 第 33-34 条） | "Środki TOMs"、"ISO 27001"、"SOC 2"、"data breach"、"incydent"、"72 godziny" |
| `10-rodo-audyt-i-odpowiedzialnosc-administracyjna.md` | 审计权（第 28 条第 3 款第 h 项）、行政罚款（RODO 第 82-83 条）、A → P 追偿 | "Prawo audytu"、"kontrola procesora"、"kary RODO"、"regres"、"PUODO" |

## 与条款和风格的关联

知识库与 skill 中另外三个位置相连接：

1. **实务条款**（`baza-klauzul/`）——学说知识解释条款**为何**如此写成
2. **黄金规则**（`references/zlote-reguly.md`）——学说知识不替代顶层规则
3. **编辑风格**（`references/style-redakcyjny.md`）——学说知识不改变节制引用原则（W6）

## 典型使用路径

**分析含 SLA 的 IT 维护合同：**
1. `references/essentialia-mapowanie.md` → 法律定性
2. `baza-wiedzy/01-maintenance-art750-kc.md` → 确认/细化《民法典》第 750 条、勤勉行为性质
3. `baza-klauzul/04-przedmiot-umowy.md` → 条款

**生成含 open source 的软件权利转让合同：**
1. `references/essentialia-mapowanie.md` → 结构要求
2. `baza-wiedzy/02-przeniesienie-praw-oprogramowanie.md` → 使用领域目录
3. `baza-wiedzy/03-prawa-zalezne-osobiste-program.md` → 衍生/精神权利结构
4. `baza-wiedzy/04-open-source-copyleft.md` → 三层保护
5. `baza-klauzul/08-prawa-autorskie-ip.md` → 条款

**分析有争议条款的风险——法院会怎么说：**
1. `baza-wiedzy/12-wykladnia-oswiadczen-woli.md` → 组合方法、客观、语言优先
2. `workflows/ocena-2-strony.md` → 类别 2（解释歧义）——操作性应用

**协商 SaaS 合同中的责任限制：**
1. `baza-wiedzy/05-cap-lucrum-wina-umyslna.md` → cap 框架、《民法典》第 473 条第 2 款界限
2. `baza-wiedzy/06-sila-wyzsza-i-podwykonawcy.md` → 不可抗力、AWS/Azure 作为分包商
3. `baza-wiedzy/07-indemnifikacja-kary-umowne.md` → cap 之外的知识产权赔偿
4. `baza-klauzul/11-odpowiedzialnosc.md` → 条款

**构建个人数据委托协议：**
1. `baza-wiedzy/08-rodo-powierzenie-konstrukcja.md` → 资格认定、第 28 条第 3 款必备要素、次处理者
2. `baza-wiedzy/09-rodo-bezpieczenstwo-i-naruszenia.md` → 技术措施、事件条款
3. `baza-wiedzy/10-rodo-audyt-i-odpowiedzialnosc-administracyjna.md` → 审计、罚款追偿
4. `baza-klauzul/14-rodo.md` → 实务条款

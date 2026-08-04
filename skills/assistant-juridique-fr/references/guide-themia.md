# Guide Themia——司法计量数据（撤销审、人身损害、劳动法、商业租赁）

<!-- NOYAU-JURIMETRIE v1 — 与 mandarinat 1.4.0 / assistant-juridique-fr 7.4.0 同步 -->

## 触发条件

只要问题涉及统计数据、赔偿金额、量化司法实践，或需要按**表述主体**（即知道*谁在说话*：最高法院、上诉法院、当事方）检索最高法院判例，即应查阅本指南。

| 信号 | 模块 |
|---|---|
| 人身损害、Dintilhac、DFP、痛苦与煎熬、DFT、ATP、资本化表、受害人、人身损害赔偿金额 | **人身损害（DC）** |
| 解雇、劳动关系解除、劳资法庭、严重过错、不适应性、工龄、Macron 表、受保护员工、劳资法庭赔偿金 | **劳动法（Travail）** |
| 商业租赁、租金、业务范围变更、搬迁补偿金、终止通知、续租、租金修订、商业租赁地位 | **商业租赁（Baux）** |
| 最高法院、上诉请求、visa、chapeau、理由、motifs、改判、Cour de cassation"本院观点"、撤销判决统计分析、按最高法院表述检索 | **最高法院（Cassation）** |
| "多少""什么金额""平均""中位数""司法实践""X% 的判决……" | **视语境而定** |

如对模块有歧义：明确询问用户。模块列表并非固定不变：如 MCP 暴露了此处未列出的模块，按同一模式使用（`compter_*`、`analyser_insights_*`、`recherche_options_*`、`echantillon_*`）。

## 三级切换规则（司法计量来源优先级）

对于请求的**司法计量或定量部分**（多少、分布、中位数、跨法院比较、趋势、实践金额）——以及撤销审中的**按表述主体检索**——按此顺序应用以下优先级：

1. **Themia 可用 → Themia 优先。** Themia 是处理这些问题最精细的工具：稳健的聚合统计（人身损害、劳动、租赁）以及撤销审中按最高法院表述的分段，这是任何其他数据库都无法提供的。
2. **Themia 不可用 → 告知，然后切换到 OpenLegi。** 告知用户**仅一次**："使用 Themia（可通过 app.themia.pro 访问）结果会更精确，它提供聚合统计，且对最高法院提供按表述主体的分段。我将使用 OpenLegi 继续。"然后尽最大努力用 OpenLegi 进行分析（检索判决、人工计数、阅读判例），并说明量化结果将是近似值。
3. **Themia 和 OpenLegi 均不可用 → 告知，然后无可用工具继续。** 告知用户使用 OpenLegi（Légifrance 官方入口）和 Themia（司法计量）结果会好得多，然后用剩余工具（对官方来源进行 web_search）作答，并明确说明局限性。

> **Themia / OpenLegi 的衔接保留——严格意义上不可相互替代。**
> Themia 提供**聚合统计**以及撤销审中的**表述主体**；它不提供 Légifrance 官方文本或 Légifrance 链接。OpenLegi 提供判决的**官方全文**及其**Légifrance 链接**。
> 后果：切换仅适用于*统计 / 按表述检索*这一维度。但**任何在交付物中实际引用的判决**仍须遵守反幻觉序列（SKILL.md 第 2 节），且必须通过 OpenLegi 确认以获得官方 Légifrance 链接。绝不可仅凭 `themia_url` 就在交付物中引用判决：须通过 OpenLegi 获取相应判决并注明 Légifrance 链接。`themia_url` 可作为补充提及，但绝不能替代官方链接。

## Themia 的范围

仅限聚合统计——无规范性标准。数据描述的是*实际判给了什么*，而非*应当判给什么*。判决的完整、官方文本：用 OpenLegi。具体判决示例（Themia 链接）：用 `echantillon_decisions_*`。

---

# 模块 0——最高法院

> 新模块。核心差异点：**按表述主体分段**——每段判例摘录都归属于作出该表述的主体（最高法院、上诉法院、当事方）。没有任何其他数据库可以针对*谁在说话*进行检索。

## Cassation 工具

| 工具 | 功能 |
|---|---|
| `Themia:compter_decisions_cassation` | 统计判决数量（分析前的快速定位） |
| `Themia:analyser_insights_cassation` | 统计分析主工具 |
| `Themia:recherche_options_cassation` | 浏览类别值（快速；绝不猜测值） |
| `Themia:echantillon_decisions_cassation` | 判决样本（Themia 链接） |
| `Themia Veriguard:selectionner_texte_cassation` | 引用前读取判决的真实文本（按表述） |
| `Themia Veriguard:selectionner_cohorte_cassation` | 按 `passage_text` 浏览语料库（实验室） |

## Cassation 字段（类别型）

撤销审中无复合赔偿金（无任何赔偿项目被标注）：仅标量字段 + `decision_count`。

| 字段 | 值（精确大小写，法文） |
|---|---|
| `jurisdiction` | Cour de cassation |
| `chamber` | Chambre sociale；Première / Deuxième / Troisième chambre civile；Chambre commerciale financière et économique；Chambre criminelle；Assemblée plénière；Chambre mixte；Première présidence (Ordonnance)；Autre |
| `formation` | Formation restreinte (hors RNSM/NA)；Formation restreinte (RNSM/NA)；Formation de section；Formation plénière de chambre；Formation mixte；Formation restreinte |
| `type` | Arrêt；Ordonnance；Demande d'avis；Question prioritaire de constitutionnalité (QPC)；Autre |
| `solution` | Rejet；Cassation；Avis；QPC renvoi；QPC autres |
| `publication` | Publié au Bulletin；Publié au Rapport；Publié aux Lettres de chambre；Communiqué；Non publié（多值） |
| `date` | 过滤器 `{from, to}`；趋势用 `date_histogram_field` |

⚠ **常见命名错误**：`court`/`chambre` → `chamber`；`decision_type`/`kind` → `type`；`outcome`/`ruling` → `solution`；`published` → `publication`。值为完整法文、精确大小写。对某个值不确定时：先调用 `recherche_options_cassation`，绝不猜测。

## 按表述主体的过滤器（差异点）

为定位*谁在说话*，使用这些专用过滤器（简单字符串 = 检索表达式；区域/标签范围在服务端应用）：

| 过滤器 | 目标表述 |
|---|---|
| `passage_voix_cour` | 最高法院的表述（本院理由、判词要旨、主文） |
| `passage_motifs_ca` | 被引用/转述的上诉法院理由 |
| `passage_moyens` | 当事方的主张（上诉请求理由） |
| `passage_moyens_annexes` | 判决末尾附载的理由（2019 年前） |
| `passage_visas` | 引据（"Vu l'article……"） |
| `passage_chapeau` | 判词要旨（原则性表述） |

多个表述以 AND 组合。替代的通用文本过滤器：`passage_text: { text, zones?, tags?, mode? }`，其中 `zones = [introduction, expose, moyens, motivations, dispositif]`。

> **⚖ 表述归属——强制性规则（撤销审特有的反幻觉）。**
> 一段摘录只有在来自 `passage_voix_cour`（或子部分 `passage_visas` / `passage_chapeau`）时，才是**最高法院的立场**。
> - ❌ 绝不将来自 `passage_motifs_ca`、`passage_moyens` 或 `passage_moyens_annexes` 的摘录呈现为最高法院的立场：它们是上诉法院的理由或当事方的论点。
> - ✅ 引用时，指明摘录来自谁的表述（"本院认为……""上诉法院曾认定……""请求人主张……"）。
> - 如对摘录的表述有疑问，在任何引用前通过 `Themia Veriguard:selectionner_texte_cassation` 重新读取（每个片段带有其标签：`voix:cour_cassation`、`voix:cour_appel`、`visa`、`chapeau`……）。表述归属错误即为 SKILL.md 第 2 节意义上的归因错误幻觉。

## Cassation 标准序列

定向计数（`compter_decisions_cassation`）→ 分析（`analyser_insights_cassation`：按 `chamber`/`solution` 分布、按 `date` 趋势等）→ 要引用判决时：`echantillon_decisions_cassation`，然后在任何交付物引用前**通过 OpenLegi 确认**（Légifrance 链接）。如引用摘录：通过 `selectionner_texte_cassation` 核验表述。

---

# 模块 1——人身损害

## DC 工具

| 工具 | 功能 |
|---|---|
| `Themia:compter_decisions_dommage_corporel` | 统计判决数量（分析前核验 N） |
| `Themia:analyser_insights_dommage_corporel` | 分析主工具 |
| `Themia:recherche_options_dommage_corporel` | 浏览赔偿项目/损害的值与层级 |

## DC 前置问题

合并为一次交互：

**地理范围**（如提到城市）：[城市] 仅限 | 全国 | [城市] 对比全国。

**语境过滤器**：
- 致害事件：`ACCIDENT_CIRCULATION`、`ACCIDENT_MEDICAL_ET_INFECTION_NOSOCOMIALE`、`ACCIDENT_TRAVAIL_ET_MALADIE_PROFESSIONNELLE`、`INFRACTION_PENALE`、`TERRORISME`、`AUTRE`
- 期间、受害人性别、DFP 区间

不要过度过滤。用 `compter_decisions` 核验 N。如 N < 20，提示并建议扩大范围。

## DC 复合键——常见赔偿项目

### 直接受害人——临时非财产损害
| 项目 | 复合键 |
|---|---|
| D.F.T. | `direct_victim_indemnity_events-extra_patrimoniaux_temporaires-DEFICIT_FONCTIONNEL_TEMPORAIRE` |
| S.E. | `direct_victim_indemnity_events-extra_patrimoniaux_temporaires-SOUFFRANCES_ENDUREES` |
| P.E.T. | `direct_victim_indemnity_events-extra_patrimoniaux_temporaires-PREJUDICE_ESTHETIQUE_TEMPORAIRE` |

### 直接受害人——永久非财产损害
| 项目 | 复合键 |
|---|---|
| D.F.P. | `direct_victim_indemnity_events-extra_patrimoniaux_permanents-DEFICIT_FONCTIONNEL_PERMANENT` |
| P.E.P. | `direct_victim_indemnity_events-extra_patrimoniaux_permanents-PREJUDICE_ESTHETIQUE_PERMANENT` |
| P.A. | `direct_victim_indemnity_events-extra_patrimoniaux_permanents-PREJUDICE_AGREMENT` |
| P.S. | `direct_victim_indemnity_events-extra_patrimoniaux_permanents-PREJUDICE_SEXUEL` |
| P.E. | `direct_victim_indemnity_events-extra_patrimoniaux_permanents-PREJUDICE_ETABLISSEMENT` |
| P.P.E. | `direct_victim_indemnity_events-extra_patrimoniaux_permanents-PREJUDICE_PERMANENT_EXCEPTIONNEL` |

### 直接受害人——永久财产损害
| 项目 | 复合键 |
|---|---|
| D.S.F. | `direct_victim_indemnity_events-patrimoniaux_permanents-DEPENSES_SANTE_FUTURES` |
| F.L.A. | `direct_victim_indemnity_events-patrimoniaux_permanents-FRAIS_LOGEMENT_ADAPTES` |
| F.V.A. | `direct_victim_indemnity_events-patrimoniaux_permanents-FRAIS_VEHICULE_ADAPTE` |
| I.P. | `direct_victim_indemnity_events-patrimoniaux_permanents-INCIDENCE_PROFESSIONNELLE` |
| P.G.P.F. | `direct_victim_indemnity_events-patrimoniaux_permanents-PERTE_GAINS_PROFESSIONNELS_FUTURS` |

### 直接受害人——临时财产损害
| 项目 | 复合键 |
|---|---|
| P.G.P.A. | `direct_victim_indemnity_events-patrimoniaux_temporaires-PERTE_GAINS_PROFESSIONNELS_ACTUELS` |

### A.T.P.
| 项目 | 复合键 |
|---|---|
| A.T.P. 临时 | `atp_indemnity_events-patrimoniaux_temporaires-ASSISTANCE_TIERCE_PERSONNE_TEMPORAIRE` |
| A.T.P. 永久 | `atp_indemnity_events-patrimoniaux_permanents-ASSISTANCE_TIERCE_PERSONNE_PERMANENTE` |

### 间接受害人
| 项目 | 复合键 |
|---|---|
| 情感损害 | `indirect_victim_indemnity_events-extra_patrimoniaux_indirectes-PREJUDICE_AFFECTION` |

如项目缺失：`recherche_options_dommage_corporel`（三级导航：`field="indemnity"` → `parent="direct_victim_indemnity_events"` → `parent="[类别]"`）。

## DC 字段

**类别型**：`jurisdiction`、`city`、`regimes`（标签）、`victim_sex`、`is_deceased`、`is_aggravation`、`bareme_capitalisation_claim/offer/decision`、`incidence_professionnelle_components`（标签）、`atteintes`（层级标签）、`sieges_blessures`（层级标签）。

**数值型**：`dfp_percentage`（0–100）、`souffrances_endurees_cotation`（0–7，步长 0.5）、`prejudice_esthetique_temporaire_cotation`（0–7）、`prejudice_esthetique_permanent_cotation`（0–7）、`age_dommage`、`victim_age_at_decision`、`age_consolidated`、`age_deceased`、`fault_percentage_victim`（0–100）、`loss_of_chance_percentage`（0–100）。

**日期型**：`date`——过滤器 `{"from": "...", "to": "..."}`，趋势用 `date_histogram_field`。

---

# 模块 2——劳动法

## Travail 工具

| 工具 | 功能 |
|---|---|
| `Themia:compter_decisions_travail` | 统计判决数量 |
| `Themia:analyser_insights_travail` | 分析主工具 |
| `Themia:recherche_options_travail` | 浏览值及项目层级 |

## Travail 语料库

约 13,000 份判决。唯一法院：上诉法院。时间深度：主要为 2024–2026 年。

## Travail 前置问题

**地理范围**（主要城市 N>200）：Paris、Aix-en-Provence、Douai、Versailles、Montpellier、Lyon、Bordeaux、Nîmes、Toulouse、Rouen、Rennes、Orléans、Reims、Colmar、Grenoble、Dijon、Besançon、Chambéry。

**语境过滤器**：
- 解除类型：`motif_personnel` | `motif_economique` | `requalification_du_contrat_de_travail` | `resiliation_ou_resolution_judiciaire` | `demande_de_prise_d_acte`
- 结果：`justified` | `nullite_sans_cause` | `nullite`
- 员工身份：`cadre` | `cadre_dir` | `cadre_int` | `employe` | `ouvrier` | `technicien` | `agent_maitrise`
- 企业规模：`moins_de_11` | `moins_de_50` | `moins_de_500` | `moins_de_1000` | `plus_de_1000`
- CDI/CDD（`is_cdi`）、受保护员工（`is_protected_employee`）
- 区间：月薪毛额、工龄（**以月为单位**）

## Travail 复合键——赔偿项目

### 解除赔偿金
| 项目 | 键 |
|---|---|
| 解雇赔偿金（法定/约定） | `indemnity_events-indemnites_rupture-licenciement_legale` |
| 代通知期补偿金 | `indemnity_events-indemnites_rupture-preavis` |
| 未休年假补偿金 | `indemnity_events-indemnites_rupture-conges_payes` |
| 竞业限制条款补偿金 | `indemnity_events-indemnites_rupture-non_concurrence` |

### 损害赔偿金
| 项目 | 键 |
|---|---|
| 无真实严肃理由解雇赔偿金 | `indemnity_events-dommages_interets-licenciement_sans_cause` |
| 程序瑕疵解雇赔偿金 | `indemnity_events-dommages_interets-licenciement_vice_procedure` |
| 侵权性解雇赔偿金 | `indemnity_events-dommages_interets-licenciement_vexatoire` |
| 无效解雇赔偿金 | `indemnity_events-dommages_interets-licenciement_nul` |
| 保护身份员工赔偿金 | `indemnity_events-dommages_interets-statut_protege` |
| 骚扰赔偿金 | `indemnity_events-dommages_interets-harcelement` |
| 歧视赔偿金 | `indemnity_events-dommages_interets-discrimination` |
| 安全保障义务赔偿金 | `indemnity_events-dommages_interets-obligation_securite` |
| 适应性义务赔偿金 | `indemnity_events-dommages_interets-obligation_adaptation` |

### 工资补发
| 项目 | 键 |
|---|---|
| 未付工资补发 | `indemnity_events-rappels_remuneration-rappel_salaire` |
| 加班费补发 | `indemnity_events-rappels_remuneration-heures_sup` |
| 奖金/红利补发 | `indemnity_events-rappels_remuneration-primes_bonus` |

### 经济性解雇
| 项目 | 键 |
|---|---|
| 超法定 PSE 赔偿金 | `indemnity_events-licenciement_economique-supra_legale` |
| 裁员顺序标准赔偿金 | `indemnity_events-licenciement_economique-criteres_ordre` |
| 优先再雇佣赔偿金 | `indemnity_events-licenciement_economique-priorite_reembauche` |

### 不适应性
| 项目 | 键 |
|---|---|
| 职业不适应性特别赔偿金 | `indemnity_events-inaptitude-speciale_pro` |
| 未履行再安置义务赔偿金 | `indemnity_events-inaptitude-defaut_reclassement` |

### CDD/临时工
| 项目 | 键 |
|---|---|
| 临时合同补贴 | `indemnity_events-cdd_interim-prime_precarite` |
| CDD→CDI 转正赔偿金 | `indemnity_events-cdd_interim-requalification` |

### 其他
| 项目 | 键 |
|---|---|
| 未交付文件赔偿金 | `indemnity_events-autres-docs_fin_contrat` |
| 民事诉讼法第 700 条 | `indemnity_events-autres-frais_irrepetibles` |
| 隐蔽工作定额赔偿金 | `indemnity_events-travail_dissimule-forfait_6_mois` |

如项目缺失：`recherche_options_travail`（`field="indemnity"` → `parent="indemnity_events"` → `parent="indemnity_events/[head]"`）。

## Travail 字段

**类别型**：`type_de_rupture`、`motifs_de_licenciement_personnels`（多值，约 61% 完整度）、`nullity_dismissal`、`employee_role`、`employer_kind`、`company_size`（约 58%）、`employee_sex`、`city`、`jurisdiction`。

**数值型**：`gross_monthly_salary`（中位数 2,384 欧元，73% 已填写）、`employee_tenure`（**以月为单位**，中位数 78 个月，96%）、`employee_age`（**以月为单位**，51%）。

⚠ **必须换算**：`employee_tenure` 和 `employee_age` 以月为单位 → 报告中换算为年。

⚠ **限制**：`gross_monthly_salary` 不能用作 `breakdown_field`。变通方法：按区间逐次过滤。

**布尔型**：`is_cdi`、`is_full_time`、`is_protected_employee`、`is_disabled_employee`、`is_pregnant_employee`、`has_children`、`has_employee_disciplinary_dossier`。

---

# 模块 3——商业租赁

> 商业租赁诉讼的统计模块。与 DC 和 Travail 相同的原则。

## Baux 工具

| 工具 | 功能 |
|---|---|
| `Themia:compter_decisions_baux_commerciaux` | 统计判决数量（分析前核验 N） |
| `Themia:analyser_insights_baux_commerciaux` | 分析主工具 |
| `Themia:recherche_options_baux_commerciaux` | 浏览字段/项目值与层级 |
| `Themia:echantillon_decisions_baux_commerciaux` | 判决样本（Themia 链接） |

## Baux 方法

字段和赔偿金键（搬迁补偿金及其项目、租金等）的细节未固定于本指南：通过 `recherche_options_baux_commerciaux`（`field="indemnity"` 然后按 `parent` 导航）动态获取，与 DC 和 Travail 完全一样。绝不猜测复合键：从 `recherche_options_baux_commerciaux` 返回的 `key` 复制。对于类别值（法院、争议类型），过滤前先查询 `recherche_options_baux_commerciaux`。

标准序列：`compter_decisions_baux_commerciaux`（定位）→ `recherche_options_baux_commerciaux`（精确字段/键）→ `analyser_insights_baux_commerciaux`（分布、比较、趋势、指标）→ `echantillon_decisions_baux_commerciaux` 获取示例，然后引用前通过 OpenLegi 确认。

---

# 公共部分

## 洞察类型

| 类型 | 用途 | 必需参数 |
|---|---|---|
| `metric` | 全局聚合值 | `breakdown_field` **禁止** |
| `distribution` | 类别分布 | `breakdown_field` 必填 |
| `comparison` | 分类统计 | `breakdown_field` 必填 |
| `trend` | 时间演变 | `date_histogram_field` + `date_histogram_interval` |
| `correlation` | 两个维度的交叉 | `breakdown_field` + `secondary_breakdown_field` |

推荐聚合：`series_aggregation: "stats"`（count、avg、min、max、P25、P50、P75、P90、P95、σ）。

## 标准序列

**跨法院比较**：计数 → 全国 metric → 按 city 的 comparison。

**分布**：计数 → 按变量的 distribution。

**[城市] 对比全国**：无过滤 metric → 带 city 过滤的 metric → 对比表（P25/P50/P75/N/σ）→ 相对差异。

**员工画像（劳动）**：计数 → 工资 metric → 工龄 metric（月→年换算）→ 身份分布 → 结果分布。

**赔偿（劳动）**：计数 → 项目 metric → 按 city 的 comparison → 按工龄的 comparison（interval=24）→ 按身份的 comparison → 如相关则 trend。

## 解读

- 中位数（P50）：最稳健的核心指标
- IQR（P25–P75）：核心趋同区间
- 标准差高：异质性明显——予以提示
- `"redacted": true` 数据：不可利用，予以提示
- `__missing__` 值：排除，如完整度显著则提示完整度
- 值 `-1`（DC 评级）：未填写——排除

## 预警阈值

| N | 处理方式 |
|---|---|
| < 5 | 不可利用 |
| 5–20 | 可用但须加警示——建议扩大范围 |
| 20–50 | 谨慎可用 |
| > 50 | 结果稳健 |

## 司法计量报告结构

1. 范围与语料库（N、过滤器、注意事项）
2. 分析（带评注的结果、表格）
3. 综述观察（结论、局限）

在报告页眉注明数据的描述性（非规范性）性质。正文中不再重复。报告以 Word 写入工作文件夹。

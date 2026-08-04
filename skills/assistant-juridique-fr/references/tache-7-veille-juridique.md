# 任务 7——法律动态监测（veille juridique）

> **环境前置要求**：无——可在任何模式下执行。COWORK/CHAT_CU：Word 交付物。CHAT：结构化对话式回答。

## 目标

对某一领域或某一法律问题，就给定期间内现行法（droit positif）的变化，产出汇总并加以分析的综述。

## 流程

### 1. 执行 playbook（任务 0）

确定监测范围：领域、期间、相关来源类型。

### 2. 检索演变——自上而下序列

**执行：**

**2a. 立法和法规演变**，通过 OpenLegi：
- `recherche_journal_officiel` → 期间内发布、按领域过滤的文本
- `rechercher_dans_texte_legal` → 近期法律、法令、政令
- `rechercher_code` → 期间内修改或新增的条文
- 识别：已颁布的法律、法令、实施细则、进行中的草案/提案

**2b. 判例演变**，通过 OpenLegi：
- `rechercher_jurisprudence_judiciaire`（排序 `DATE_DESC`）→ 最高法院近期判决
- `rechercher_jurisprudence_administrative`（排序 `DATE_DESC`）→ 最高行政法院近期判决
- `rechercher_decisions_constitutionnelles` → 该主题近期的合宪性优先问题（QPC）
- 识别：改判、澄清、对一贯判例的确认

**2c. 学说演变**，通过 HAL + web_search：
- `scripts/doctrine_search.py` → 近期出版物（多来源、可验证标识符）；`scripts/hal_search.py` 作定向补充
- web_search → Dalloz Actualité、JCP Actualité、AJDA、近期书评
- 识别：对改革的批判性分析、学说建议、进行中的讨论

**2d. 欧洲和国际演变**，如相关，通过 web_search：
- 欧洲人权法院（hudoc.echr.coe.int）、欧盟法院（curia.europa.eu）
- 正在转化中的欧盟指令和条例

### 3. JORF 来源的分类与定性

对《官方公报》中的每份文件：依照核心原则定性其性质（规范性 / 议会工作 / 行政文件）。不得将议会报告呈现为现行法。

### 4. 撰写 Word 文档

**结构：**

1. **综述**：主要演变、趋势、实务影响
2. **立法和法规演变**（时间顺序、每份文本的分析）
3. **判例演变**（重要判决、对其影响范围的分析）
4. **学说演变**（进行中的讨论、批判性分析）
5. **展望**：准备中的文本、法律草案、预期的转化
6. **注释和参考**

对每项演变：日期、精确引用、内容摘要、影响分析、超链接。

### 5. 交付

命名：`[AAAA-MM-JJ]-veille-[matiere]-[periode].docx`（\[年年年年-月月-日日\]-veille-\[领域\]-\[期间\].docx）

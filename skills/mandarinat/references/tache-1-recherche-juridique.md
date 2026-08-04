# 任务1——深度法律检索

> **环境前提**：无——可在任何模式下执行。COWORK/CHAT_CU：交付 Word 文件。CHAT：结构化对话式回答。

## 目标

就某一法律问题产出带已核实引用的深度综述，并附适合学术语境的**强化学说侧重**。优先呈现法律现状，同时处理法律演进、学说争议和判例动态。

## 流程

### 1. 执行流程手册（任务0）

识别法律问题和适用法律。流程手册指引检索方向。

### 2. 文献检索——自上而下顺序

严格按 SKILL.md 第3节的顺序执行：

**执行：**

**2a. 规范性文本**，经 OpenLegi：
- `rechercher_code` → 适用法典的条文
- `rechercher_dans_texte_legal` → 法律、法令、政令
- `recherche_journal_officiel` → 近期文本
- 核实每份文本的时间元数据（法律状态、生效日期）
- 在每条引用中标明时间状态

**2b. 最高判例**，经 OpenLegi：
- `rechercher_jurisprudence_judiciaire`（法院过滤为最高法院，`publication_bulletin: true` 优先）
- `rechercher_jurisprudence_administrative`（法院过滤为最高行政法院，`publication_recueil: true` 优先）
- 如相关则 `rechercher_decisions_constitutionnelles`
- 识别指导性判例、立场转变、稳定判例

**2c. 基层判例**，经 OpenLegi：
- `rechercher_jurisprudence_judiciaire`（法院过滤为上诉法院、司法法院）
- `rechercher_jurisprudence_administrative`（法院过滤为行政上诉法院、行政法院）
- 选取具体展示规则适用情形的决定

**2d. 学说**（优先强化——学术语境）：
- `scripts/doctrine_search.py` → 多源学说检索（HAL + OpenAlex + Isidore），每条引用附可验证标识符；`scripts/hal_search.py` 用于按案号查判例注释
- web_search → Cairn、Dalloz Actualité、Persée、OpenEdition
- 按案号检索判例注释（HAL：`--pourvoi "NUMÉRO"`）
- HAL / web_search 去重
- **深度检索至少10条学说来源**，载体（论文、著作、学位论文、注释、纪念文集）和作者多样化
- 检索近期学位论文（HAL：`--query "TERMES" --all-types` 再过滤 THESE）
- 识别进行中的学说争论、思想流派、分歧立场

**2e. 比较法**（如相关）：
- `LegalDataHunter:search`，带适当国家和命名空间过滤
- 检索策略见 `references/guide-legaldatahunter.md`
- 仅在能阐明法国法律问题时纳入比较维度

**仅在以下情形中断：**
- 所有来源均无相关结果 → 提示并提出替代方向
- 规范性文本之间存在重大矛盾 → 说明冲突及建议的解决方案

### 3. 核实

对每条引用的引用：
1. 经 OpenLegi 或 web_search 确认存在（见 `references/principes-cardinaux.md`）
2. 核实时间状态（现行有效 / 废止 / 未来生效）
3. 标明来源性质（规范性 / 议会工作 / 资讯性）
4. 创建指向来源的超链接

### 4. 撰写 Word 文档

**结构：**

1. **综述**（直接回答所提问题，置于文档开头）
2. **引言**：定义、历史背景、当代议题
3. **正文**，采用结构化提纲：
   - 描述性标题（sentence case）
   - 法文弯引号「 … 」内精确引文，附尾注
   - 正文中交锋学说观点（辩证式，而非罗列式）
   - 关键事实和重要内容加粗
   - 明确标出共识区、争议区和不确定区
4. **分类参考书目**：
   - 规范性文本
   - 判例（按法院分类，再按时间排序）
   - 学说（分类：论著/手册、学位论文、论文、注释、撰稿）
5. **注释和引用**置于文档末尾

**正文中学说的处理：**
- 将作者的精确引文直接融入正文
- 交锋分歧观点：呈现正题、反题，解释分歧原因
- 指出共识区和争议区
- 引用相关博士论文并说明其学术贡献
- 提及可识别的思想流派或学说潮流

**引用格式**：见 `references/format-citations.md`

### 5. 交付

按环境模式写入 Word 文件（见 SKILL.md 第6节）。命名：`[AAAA-MM-JJ]-recherche-[sujet].docx`。

提出相关任务：就主题创建考试题目、更新既有课程、准备课程讲义。

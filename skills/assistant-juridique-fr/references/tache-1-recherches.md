# 任务 1——法律研究

> **环境前提**：无——可在任何模式下执行。COWORK/CHAT_CU：Word 交付物。CHAT：结构化的会话式答复。

## 目标

就一个法律问题产出带有可核验引用的深入综合，优先呈现法律现状，同时处理演变和动态。

## 流程

### 1. 执行 playbook（任务 0）

识别法律问题和适用法律。playbook 指引研究主轴。

### 2. 文献检索——自上而下序列

严格按此顺序遵循 SKILL.md 第 3 节的序列：

**执行：**

**2a. 规范性文本**，通过 OpenLegi：
- `rechercher_code` → 适用法典的条文
- `rechercher_dans_texte_legal` → 法律、法令、条例
- `recherche_journal_officiel` → 近期文本
- 核验每个文本的时间元数据（法律状态、生效日期）
- 在每条引用中标注时间状态

**2b. 最高法院判例**，通过 OpenLegi：
- `rechercher_jurisprudence_judiciaire`（过滤最高法院，`publication_bulletin: true` 优先）
- `rechercher_jurisprudence_administrative`（过滤最高行政法院，`publication_recueil: true` 优先）
- 如相关，`rechercher_decisions_constitutionnelles`
- 识别原则性判例、改判、固定判例

**2c. 基层判例**，通过 OpenLegi：
- `rechercher_jurisprudence_judiciaire`（过滤上诉法院、司法法院）
- `rechercher_jurisprudence_administrative`（过滤行政上诉法院、行政法院）
- 选择具体说明规则适用的判决

**2d. 学说**，通过 HAL + web_search：
- `scripts/doctrine_search.py` → 多来源学说检索（HAL + OpenAlex + Isidore），按引用可核验的标识符；`scripts/hal_search.py` 用于按上诉案号检索判例评注
- web_search → Cairn、Dalloz Actualité、Persée、OpenEdition
- 按上诉案号检索判例评注（HAL：`q=title_t:"NUMÉRO_POURVOI"`）
- 对 HAL / web_search 结果去重
- **至少 10 个学说来源**，载体（文章、著作、论文、评注）和作者多样，每个都带有**可核验的标识符**（DOI / HAL / 公认数据库的 URL）；否则注明"未核验的引用"或删除。

**仅在以下情形中断：**
- 所有来源均无相关结果 → 报告并提出替代主轴
- 规范性文本之间存在重大矛盾 → 说明冲突和拟议的解决方式

### 3. 核验

对每条引用的参考：
1. 通过 OpenLegi 或 web_search 确认存在（见 `references/principes-cardinaux.md`）
2. 核验时间状态（有效 / 废止 / 未来）
3. 界定来源性质（规范性 / 议会工作文件 / 信息性）
4. 创建指向来源的超链接

### 4. 撰写 Word 文档

**结构：**

1. **综合**（在文档开头直接回答所提问题）
2. **引言**：定义、历史背景、当代议题
3. **有结构的论述展开**：
   - 句首大写的描述性标题
   - 带法式引号「…」的精确引用，附尾注
   - 在正文中对照学说观点（辩证，而非列举）
   - 关键事实和重要要素加粗
4. **注释和引用**在文档末尾

**正文中学说的处理：**
- 将作者的精确引用直接融入论述
- 对照分歧观点：呈现论点、反论点，解释分歧原因
- 指出共识区和争议区

**引用格式**：见 `references/format-citations.md`

### 5. 交付

按环境模式（见第 6 节）写入 Word 文件。命名：`[AAAA-MM-JJ]-recherche-[sujet].docx`。

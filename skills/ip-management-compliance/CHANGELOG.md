# CHANGELOG - ip-management-compliance 母技能

## v3.0.0（2026-06-27）

### 全量架构修复（13项问题修复）
- **isoMapping修正**：附录A→ip-mgmt-innovation、附录C→ip-mgmt-search（原appendixAC合并映射拆分）
- **mcp-rpc.json补全**：新增ip-mgmt-search条目、版本同步至3.0.0、ip-mgmt-tools isoClause修正
- **ip-mgmt-tools瘦身**：检索执行内容（B.1/速查卡/7.4/HPA模块2/检索报告模板）迁移为ip-mgmt-search交叉引用，聚焦专利信息分析方法
- **ELNK-003/004重分类**：内部自调用从external-linkage-rules迁移至internal-linkage-rules（LNK-009/010）
- **三性关键词路由消歧**：examination路由排除"检索"后缀，search路由优先匹配含"检索"关键词
- **跨技能版本引用统一**：ip-management-compliance V3.0.0, patent-examination-guide V1.13.1, patent-infringement-guide V3.13.2
- **子技能meta.yaml版本同步**：tools 1.7.0, search 2.2.0, innovation 2.0.0, examination 1.7.0
- **rag_retrieve.py引用清理**：删除所有引用（源文件已缺失），删除孤儿.pyc缓存
- **联动声明双向对齐**：patent-exam-guide子技能SKILL.md与linkage-detail.md同步
- **audit/exploitation边界澄清**：添加价值评价方法论vs价值实现路径边界声明
- **HPA模块8归属注释**：标注为横切关注点，暂归innovation

## v2.9.0（2026-05-31）

### Darwin Skill 2.0 全技能优化（10技能全部 ≥80 分目标）
- **基线评估**：4个独立agent评分，innovation 90.2⭐ | 其余7技能 55.3-78.6
- **两轮优化**：8次commit，9个文件，+1,547行
- **决策树**：7个技能新增快速决策树（compliance/exploitation/audit/strategy/tools/examination/risk）
- **可执行代码**：exploitation(+Python定价器) audit(+Python计算器+24项清单) examination(+26项合规清单)
- **模板扩展**：strategy(+战略模板+行业对标+仪表盘) tools(+检索速查卡+报告规则)
- **质量增强**：search(+语义层+6检索模板+质量评分) risk(+FTO决策树+量化评分卡+规避设计)
- **检查点/失败模式**：compliance(+2检查点+2失败) framework(+triggerPatterns)
- **版本**：母技能 2.8.0→2.9.0，子技能全部升级（innovation 90.2达标不升级）

## v2.8.0（2026-05-31）

### 架构重构：删除 sub-skills 目录，采用独立版唯一架构
- **删除** `sub-skills/` 目录（8个技能的双份副本，内容已全部合并到独立版 `skills/ip-mgmt-*/`）
- **合并** 独立版独有内容到各技能：《知识产权信息分析利用指南》7.5节、GB/T 39551、FTO详细步骤
- **补充** 全部9个独立技能 frontmatter 的 author/tags/triggerPatterns 字段
- **统一** description 为"本技能可独立使用，也可由 ip-management-compliance 母技能调度"
- **去除** 所有独立版技能中"子技能X："标题前缀和"本子技能"用词
- **架构** 参照 patent-examination-guide：子技能仅存于独立路径，母技能通过名称路由
- **版本** 母技能 2.7.0→2.8.0，子技能升级至 1.3.0/1.4.0/1.5.0
- **部署脚本** deploy.ps1/deploy.sh 路径引用更新为独立版路径
- **配置** linkage-rules.yaml/meta.yaml/mcp-rpc.json 版本号及术语同步

## v2.7.0（2026-05-06）

### Tavily Search 实时检索集成
- **ip-mgmt-search** 新增 tavily-search 补充检索引擎，支持非专利文献实时检索
- **RAG 核心能力** 新增实时网络检索补充（行业动态、技术新闻、市场报告）
- **ip-mgmt-risk** FTO 分析步骤嵌入 tavily-search 非专利文献检索
- 新增 **Tavily Search 集成专章**（含 5 大场景 + 调用规范）

### Bug 修复（2026-05-07）
- frontmatter `sub-skills` 补全 `ip-mgmt-search`
- HPA 模块2 路由 `ip-mgmt-tools` → `ip-mgmt-search`
- 删除 Tavily Search 章节内误嵌入的重复子技能条目
- SKILL.md 内联版本号 `V2.6.0` → `V2.7.0`（3 处）
- 架构描述修正："8个独立子技能" → "8个业务子技能+1个共享检索模块"
- meta.yaml / CHANGELOG.md 版本同步至 v2.7.0

## v2.6.0（2026-05-02）

### 专利检索路由修复
- **修复专利检索路由断裂**：将检索任务从 `ip-mgmt-tools` 重新路由至 `ip-mgmt-search` 核心引擎
- **补齐调用指引**：`ip-mgmt-risk` / `ip-mgmt-examination` 对 `ip-mgmt-search` 的调用指引
- **版本联动更新**：同步与 `patent-examination-guide`（V1.8.0）的联动信息
- **社区命名对齐**：补充双方社区命名体系对应关系说明

## v2.5.0（2026-04-22）

## v2.4.0（2026-04-09）

### ISO 56005 章节号全面修正（重大）
- **meta.yaml**: `chapter10`→`appendixD`, `chapter11`→`appendixF`，isoMapping 全部对齐
- **SKILL.md 映射表**: 删除不存在的"第7-11章"，统一为正确映射（正文4-6章+附录A-F）
- **8个子技能 iso-clause** 全部修正：
  - ip-mgmt-examination: "第8章支持" → "附录B IP创造获取维护"
  - ip-mgmt-innovation: "6.1领导作用" → "6.2-6.6创新管理过程"
  - ip-mgmt-risk: "第9章运行" → "附录E IP风险管理"
  - ip-mgmt-audit: "第10章评价" → "附录D IP评价"
  - ip-mgmt-exploitation: "第11章改进" → "附录F IP运用"
- **8个独立技能版本统一升至 v1.2.0**（ip-mgmt-framework/strategy/innovation/examination/risk/exploitation/audit）

### 版本号同步
- meta.yaml version/spec/description 全部同步至 v2.4.0

### 结构优化（继承自 2026-04-04 版本）
- 删除"智能路由"小节，与"快速路由指南"合并，避免内容重复
- 删除技术架构ASCII图（维护困难，用户价值有限）
- 删除"响应式检索（技能内嵌）"段落（开发者文档混入用户文档）
- 删除"知识库维护"章节（维护指南，首次配置后几乎不看）
- 删除冗余的"注意事项"章节（API额度等通识信息）
- 删除版本更新日志，统一移至本 CHANGELOG.md 文件
- 删除子技能快速索引中的触发词描述（与快速路由指南重复）
- 删除连续双横线格式冗余

### 内容精简
- RAG输出格式示例从完整Markdown示例缩减为缩略模板
- 前置条件代码块合并为精简版（去除冗余cmd语法）
- frontmatter description 精简，移除对已废弃专利评估技能的引用

### Bug修复
- 凭证设置代码块：`bash` → `powershell`，`:set` 语法 → `$env:` 语法
- 模板资源索引路径：`assets/` → `ip-mgmt-audit/templates/`
- 编号修正："### 3. 输出规范" → "### 2. 输出规范"（章节顺序对应）

## v2.3.0（2026-04-04）
- 版本号统一为 2.3.0，meta.yaml 同步更新
- 核心模块路由表旧名修正：`innovation-process-ip` → `ip-mgmt-innovation`，`ip-tool-application` → `ip-mgmt-tools`
- ISO 标准映射表增加"说明"列，明确第6章拆分为6.1领导作用和6.2-6.6创新管理
- 新增模板资源索引章节，关联母技能及子技能内置模板
- 新增参考资料索引章节，关联 references/ 目录
- RAG 内嵌代码块增加 AI 执行说明注释
- 执行优先级增加适用场景说明，明确仅适用于新建 IP 管理体系初始化场景

## v2.2.0（2026-04-03）
- 快速路由指南新增：新颖性检索、创造性评估、实用性审查、技术完善、权利要求布局
- 子技能快速索引更新：添加已整合HPA模块的触发词说明
- 路由表子技能名称修正：`innovation-process-ip` → `ip-mgmt-innovation`，`ip-tool-application` → `ip-mgmt-tools`
- **内置本地ima知识库模块**：集成 `scripts/rag_retrieve.py`，支持专利法规语义检索
- **智能触发机制**：根据用户提问自动判断是否需要检索法规库
- **自动收录5部核心法规**：专利法、实施细则、审查指南、国知局指引（共1484个文本块）
- **子技能联动**：所有子技能可共享RAG检索能力

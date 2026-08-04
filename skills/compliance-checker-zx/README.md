# compliance-checker 行业合规工具

## 概述

行业合规工具是一个纯Python标准库实现的高级合规算法工具集合，提供10个包含真实算法实现的合规检查工具，覆盖合同智能分析、法规检索引擎(倒排索引+TF-IDF)、多因子风险评估、隐私影响评估(PIA)、数据脱敏(K-匿名/L-多样性/T-接近性)等合规领域核心算法。

## 功能列表

| 序号 | 函数名 | 算法 | 时间复杂度 |
|------|--------|------|-----------|
| 1 | `contract_analyzer` | 正则解析+规则引擎+条件判断树 | O(n) |
| 2 | `regulation_search_engine` | 倒排索引+TF-IDF+短语匹配 | O(n*m) |
| 3 | `risk_assessment_model` | 多因子加权+sigmoid非线性变换 | O(n) |
| 4 | `compliance_checklist_generator` | 行业匹配+规则筛选+优先级排序 | O(n*m) |
| 5 | `privacy_impact_assessment` | 4维度PIA风险评估框架 | O(n) |
| 6 | `data_anonymizer` | K-匿名+L-多样性+T-接近性(EMD) | O(n^2) |
| 7 | `regulatory_term_explainer` | 术语词典+上下文消歧 | O(n) |
| 8 | `clause_generator` | 模板引擎+参数插值 | O(1) |
| 9 | `obligation_tracker` | 指数衰减紧急度模型+优先级排序 | O(n log n) |
| 10 | `compliance_report_generator` | 数据聚合+加权风险评分+模板渲染 | O(n) |

## 算法原理

### 1. 合同智能分析
- **原理**: 正则表达式解析合同结构(章/条/附件) + 规则引擎提取关键要素(当事人/金额/期限/违约/争议)
- **条件判断树**: 多层验证要素完整性，自动检测模糊表述
- **复杂度**: O(n)，n为合同文本长度

### 2. 法规检索引擎
- **原理**: 倒排索引(term->doc映射) + TF-IDF评分(tf*idf*level_weight) + 短语匹配加权
- **TF-IDF**: idf(t) = log((N+1)/(df+1)) + 1 (平滑处理)
- **法规层级权重**: 宪法(5.0) > 法律(4.0) > 行政法规(3.0) > 部门规章(2.0)
- **复杂度**: O(n*m)，n=文档数，m=查询词数

### 3. 风险评估模型
- **原理**: sigmoid非线性变换 f'(x) = 1/(1+exp(-k*(x-x0))) + 加权求和 + 5级分类
- **风险矩阵**: 可能性 x 影响 二维矩阵(5x5)
- **复杂度**: O(n)

### 4. 合规清单生成器
- **原理**: 行业匹配 + 规模筛选 + 检查项生成(关键词风险分级) + 优先级排序
- **复杂度**: O(n*m)

### 5. 隐私影响评估(PIA)
- **原理**: 4维度评估(数据最小化/目的限制/存储限制/安全性) + 数据共享风险
- **风险评分**: 每维度0-10分，取最高风险分
- **复杂度**: O(n)

### 6. 数据脱敏器
- **K-匿名**: 泛化(区间化)+抑制(*)使每条记录至少与K-1条不可区分
- **L-多样性**: 每个等价类中敏感属性至少有L个不同值
- **T-接近性**: EMD(Earth Mover's Distance)度量分布距离
- **复杂度**: O(n^2)（等价类构建和验证）

### 7. 法规术语解释器
- **原理**: 术语知识库 + 模糊匹配 + 上下文消歧
- **复杂度**: O(n)

### 8. 合规条款生成器
- **原理**: 模板引擎(条件渲染+参数插值) + 法律条款库 + 管辖区适配
- **复杂度**: O(1)

### 9. 合规义务追踪器
- **原理**: 指数衰减紧急度模型 urgency = exp(-days/tau), tau=30天
- **优先级**: priority = urgency * risk_weight * status_weight
- **复杂度**: O(n log n)（排序）

### 10. 合规报告生成器
- **原理**: 数据聚合(按类型/严重度/状态) + 加权风险评分 + 模板渲染(Markdown/HTML)
- **复杂度**: O(n)

## 安装

无需安装外部依赖，仅使用Python标准库。

## 使用方法

```python
from main import contract_analyzer, regulation_search_engine, data_anonymizer

# 合同分析
result = contract_analyzer(contract_text)

# 法规检索
results = regulation_search_engine("个人信息保护", regulation_db, top_k=5)

# 数据脱敏
anon = data_anonymizer(data, {"k": 5, "l": 3, "t": 0.2}, sensitive_fields=["disease"])
```

## 运行

```bash
python main.py
```

## 技术特点

- 零外部依赖，仅使用Python标准库
- 10个函数全部包含真实算法实现
- 覆盖合规核心算法：倒排索引、TF-IDF、K-匿名、L-多样性、T-接近性、PIA
- 支持Markdown和HTML双格式报告输出

---
name: china-legal-query
description: 中国法律法规查询工具。Use when user needs to search Chinese laws, regulations, judicial interpretations. Supports criminal law, civil law, labor law, contract law, intellectual property law. 中国法律、法规查询、法律条文。
version: 1.0.2
license: MIT-0
metadata: {"openclaw": {"emoji": "⚖️", "requires": {"bins": ["python3", "curl"], "env": []}}}
---

# 中国法律法规查询工具

查询中国法律法规、司法解释、案例判决。

## 功能特点

- ⚖️ **法律条文**: 刑法、民法、劳动法、合同法等
- 📋 **司法解释**: 最高法院、最高检察院解释
- 📚 **案例参考**: 裁判文书、典型案例
- 🔍 **智能搜索**: 关键词、法条号、主题搜索
- 🌐 **官方来源**: 国家法律法规数据库
- 🇨🇳 **中国法律**: 专注中国法律体系

## ⚠️ 免责声明

> **本工具仅供参考，不构成法律建议。**
> 不同AI模型能力不同，查询结果可能有差异。
> 重要法律事务请咨询专业律师。
> 法律条文以官方发布为准。

## 支持的法律类型

| 类别 | 法律名称 | 说明 |
|------|----------|------|
| **宪法** | 中华人民共和国宪法 | 根本大法 |
| **刑法** | 中华人民共和国刑法 | 犯罪与刑罚 |
| **民法** | 中华人民共和国民法典 | 民事关系 |
| **婚姻法** | 民法典婚姻家庭编 | 结婚、离婚、财产 |
| **劳动法** | 中华人民共和国劳动法 | 劳动关系 |
| **合同法** | 民法典合同编 | 合同订立、履行 |
| **知识产权** | 专利法、商标法、著作权法 | 知识产权保护 |
| **消费者权益** | 消费者权益保护法 | 消费者保护 |
| **公司法** | 中华人民共和国公司法 | 公司治理 |
| **税法** | 个人所得税法、企业所得税法 | 税收 |
| **环保法** | 环境保护法 | 环境保护 |
| **交通法** | 道路交通安全法 | 交通安全 |

## 使用方式

```
User: "查询劳动法关于加班的规定"
Agent: 搜索相关法律条文并展示

User: "民法典第1024条是什么"
Agent: 查询具体法条内容

User: "关于知识产权保护的法律有哪些"
Agent: 列出相关法律法规
```

---

## 查询流程

```
用户提问
    ↓
1. 识别法律领域
    ↓
2. 搜索官方数据库
    ↓
3. 提取相关条文
    ↓
4. AI解读分析
    ↓
5. 输出查询结果
```

---

## Python代码

```python
import os
import re

class LegalQueryEngine:
    def __init__(self):
        self.sources = {
            'web_search': '使用web-search查询法律条文',
            'ai_knowledge': '使用AI模型法律知识库'
        }
    
    def search_law(self, keyword, law_type=None):
        """搜索法律条文"""
        # 使用web-search查询
        # 或使用AI模型知识库
        results = []
        return results
    
    def get_article(self, law_name, article_num):
        """获取具体法条"""
        # 使用AI模型知识库
        return {
            'law': law_name,
            'article': article_num,
            'content': '...',
            'source': 'AI知识库'
        }
    
    def analyze_query(self, user_query):
        """分析用户查询意图"""
        return {
            'domain': '劳动法',
            'keywords': ['加班', '工时'],
            'search_strategy': 'ai_knowledge'
        }
```

---

## 注意事项

- 法律条文以官方数据库为准
- AI解读仅供参考
- 条文可能有更新，以最新版本为准
- 复杂法律问题请咨询专业律师

# 法律咨询报告 - 数据格式规范

## 概述

本文档定义法律咨询报告生成脚本的输入数据格式规范。所有通过 `--case_data` 或 `--case_file` 传入的数据必须符合本规范。

## 数据格式示例

```json
{
  "client_name": "杭州光影数字传媒有限公司",
  "client_contacts": "林深、梁晨、苏雨三位创始人",
  "lawyer_name": "顾小法",
  "lawyer_team": "顾小法律师4人专属青年法律顾问团队",
  "core_advantages": "专业扎实+AI高效，深耕浙江数字传媒、AR类企业法律服务",
  "report_title": "杭州光影数字传媒有限公司法律风险咨询报告（含服务报价）",
  "report_subtitle": "企业合规诊断与风险防控专项报告",
  "business_desc": "浙江地区AR领域创新企业，专注于增强现实技术研发与应用",
  "consultation_background": "贵公司作为浙江AR领域的潜力企业，500万元天使投资既是发展机遇，更是合规考验，各类法律风险若不及时化解，不仅会影响企业正常运营，更会阻碍融资进程、侵蚀创始人核心权益。",
  "core_requirements": [
    {
      "title": "股权合规",
      "description": "妥善解决天使投资引入后的股权合规问题，明确股东实缴出资方式，弥补无股东协议的核心漏洞，保障三位创始人的核心控制权"
    },
    {
      "title": "合同风险防控",
      "description": "全面整改拟签署的音箱采购合同，化解验收标准模糊、付款节点不合理、保密竞业缺失等核心风险"
    },
    {
      "title": "人事与内控规范",
      "description": "规范研发团队加班管理，妥善处置核心人员离职相关事宜，防范商业秘密外泄"
    }
  ],
  "key_facts": [
    {
      "fact": "2025年初完成500万元天使轮融资，投资人占股20%",
      "legal_significance": "涉及股权稀释与股东权利问题"
    },
    {
      "fact": "三位创始人股权比例：林深50%、梁晨25%、苏雨25%",
      "legal_significance": "涉及控制权分配与公司治理结构"
    },
    {
      "fact": "天使投资方要求明年完成A轮融资",
      "legal_significance": "涉及对赌条款与业绩承诺风险"
    },
    {
      "fact": "音箱采购合同存在验收标准模糊等4项核心风险",
      "legal_significance": "涉及合同履行争议与违约责任"
    },
    {
      "fact": "研发团队存在加班费发放违规问题",
      "legal_significance": "涉及劳动法合规与员工权益保护"
    }
  ],
  "legal_relations": [
    {
      "title": "股东与公司关系",
      "parties": "林深、梁晨、苏雨（股东） ↔ 光影传媒（公司）",
      "nature": "股权投资关系",
      "description": "三位创始人通过持股平台间接持有公司股份，与公司之间形成股权与管理权分离的治理结构"
    },
    {
      "title": "天使投资人与公司关系",
      "parties": "天使投资人 ↔ 光影传媒",
      "nature": "股权投资与对赌安排",
      "description": "天使投资人以500万元换取20%股权，同时附带A轮融资对赌条款"
    },
    {
      "title": "公司与供应商关系",
      "parties": "光影传媒 ↔ 音箱供应商",
      "nature": "货物买卖合同关系",
      "description": "采购合同涉及设备采购、验收标准、付款条件等核心条款"
    }
  ],
  "risk_items": [
    {
      "level": "高",
      "item": "股权未实缴风险",
      "consequence": "面临市场监管部门行政处罚，影响融资进程",
      "priority": "立即处理"
    },
    {
      "level": "高",
      "item": "无书面股东协议",
      "consequence": "创始人权责不清，决策机制缺失，潜在股权纠纷",
      "priority": "立即处理"
    },
    {
      "level": "高",
      "item": "音箱采购合同风险",
      "consequence": "验收争议、付款纠纷、商业秘密泄露",
      "priority": "优先处理"
    },
    {
      "level": "中",
      "item": "加班费发放违规",
      "consequence": "员工投诉、劳动仲裁风险",
      "priority": "尽快处理"
    },
    {
      "level": "中",
      "item": "竞业协议效力瑕疵",
      "consequence": "无法有效约束核心人员流动",
      "priority": "适时处理"
    }
  ],
  "solutions": [
    {
      "title": "股权合规整改方案",
      "description": "建议尽快完成注册资本实缴，制定规范化股东协议，明确各方权利义务与决策机制",
      "effect": "消除法律合规风险，明确控制权架构"
    },
    {
      "title": "合同风险防控方案",
      "description": "对采购合同进行全面法律审查，重新约定验收标准与付款节点，增加保密与竞业限制条款",
      "effect": "最大限度降低合同履行风险"
    },
    {
      "title": "人事合规管理方案",
      "description": "完善加班管理制度，确保加班费合规发放；优化竞业协议条款，增加经济补偿确保效力",
      "effect": "降低劳动争议风险，保护商业秘密"
    },
    {
      "title": "长期合规顾问服务",
      "description": "建立常态化合规审查机制，为后续A轮融资及企业发展提供全程法律支持",
      "effect": "建立长效合规机制，降低后续法律风险"
    }
  ],
  "service_packages": [
    {
      "name": "基础常年法律顾问",
      "price": "¥3万元/年",
      "description": "适合初创期企业基础合规需求",
      "features": [
        "全年不限次法律咨询",
        "合同起草与审查（限10份）",
        "法律风险评估报告1份",
        "劳动人事合规指导",
        "每月定期法律培训1次"
      ],
      "validity": "自报价之日起15个自然日"
    },
    {
      "name": "标准常年法律顾问",
      "price": "¥6万元/年",
      "description": "适合成长期企业全面合规需求，推荐方案",
      "features": [
        "全年不限次法律咨询",
        "合同起草与审查（限30份）",
        "法律风险评估报告2份",
        "股权架构设计与优化",
        "融资法律支持（含尽职调查）",
        "每月定期法律培训2次",
        "优先响应与专属对接"
      ],
      "validity": "自报价之日起15个自然日"
    },
    {
      "name": "尊享常年法律顾问",
      "price": "¥12万元/年",
      "description": "适合规模化企业深度合规需求",
      "features": [
        "全年不限次法律咨询",
        "合同起草与审查（不限份数）",
        "法律风险评估报告4份",
        "股权架构设计与优化",
        "全程融资法律支持",
        "知识产权保护方案",
        "商业模式合规审查",
        "每周定期法律培训",
        "7x24小时紧急响应",
        "专属律师团队服务"
      ],
      "validity": "自报价之日起15个自然日"
    }
  ],
  "closing_message": "贵公司作为浙江AR领域的潜力企业，500万元天使投资既是发展机遇，更是合规考验。我方团队将以专业服务为核心，结合本地司法实践，为贵公司的发展筑牢合规根基、赋能价值提升，助力企业顺利实现发展目标。期待与贵公司达成长期合作！",
  "validity_period": "自报价之日起15个自然日"
}
```

## 字段详细说明

### 基础信息字段

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `client_name` | string | 是 | 客户名称（公司全称或个人姓名） |
| `client_contacts` | string | 是 | 联系人信息 |
| `lawyer_name` | string | 是 | 负责律师姓名 |
| `lawyer_team` | string | 否 | 律师团队名称 |
| `core_advantages` | string | 否 | 核心竞争优势描述 |
| `report_title` | string | 是 | 报告标题 |
| `report_subtitle` | string | 否 | 报告副标题 |

### 内容字段

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `business_desc` | string | 否 | 企业业务描述 |
| `consultation_background` | string | 是 | 咨询背景与开场白 |
| `core_requirements` | array | 是 | 核心法律需求列表 |
| `key_facts` | array | 是 | 核心事实梳理 |
| `legal_relations` | array | 是 | 法律关系分析 |
| `risk_items` | array | 是 | 潜在风险提示 |
| `solutions` | array | 是 | 解决方案建议 |
| `service_packages` | array | 否 | 服务方案与报价 |
| `closing_message` | string | 否 | 结语信息 |
| `validity_period` | string | 否 | 报价有效期 |

### 对象结构

#### core_requirements 元素

```json
{
  "title": "需求标题",
  "description": "需求详细描述"
}
```

#### key_facts 元素

```json
{
  "fact": "事实要点",
  "legal_significance": "法律意义"
}
```

#### legal_relations 元素

```json
{
  "title": "法律关系名称",
  "parties": "涉及主体",
  "nature": "关系性质",
  "description": "详细说明"
}
```

#### risk_items 元素

```json
{
  "level": "高/中/低",
  "item": "风险事项",
  "consequence": "潜在后果",
  "priority": "处理优先级"
}
```

#### solutions 元素

```json
{
  "title": "建议标题",
  "description": "建议详细说明",
  "effect": "预期效果"
}
```

#### service_packages 元素

```json
{
  "name": "方案名称",
  "price": "价格",
  "description": "方案描述",
  "features": ["功能1", "功能2"],
  "validity": "有效期"
}
```

## 简化格式支持

对于简单场景，部分字段也支持字符串替代对象：

```json
{
  "core_requirements": [
    "股权合规整改",
    "合同风险防控",
    "人事内控规范"
  ],
  "key_facts": [
    "完成500万元天使轮融资",
    "三位创始人持股比例明确"
  ]
}
```

## 输出说明

- 默认输出HTML到stdout
- 使用 `--output` 参数指定输出文件路径
- 文件名建议格式：`{客户名称}法律风险咨询报告.html`

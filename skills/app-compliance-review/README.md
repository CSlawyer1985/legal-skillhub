# app-compliance-review

**中国移动应用（APP）个人信息保护合规检查技能包。**

面向公司法务、数据合规律师或合规顾问，对移动应用程序开展完整的个人信息保护合规评审，可直接面向业务部门交付合规审查报告与整改清单。

- **两阶段审查方法论**：先从文本取证与技术取证两个维度查明合规事实，再核验声明与事实的一致性，定位"声明"与"实际"的偏差。
- **11大合规模块，50+检查项**：隐私政策、知情同意、最小必要、权限管理、SDK与第三方、敏感个人信息、用户权利、广告合规、数据安全、特殊场景、分发平台信息明示。
- **MCP条文锚定**：72个法规锚点，每次运行通过用户配置的MCP后端（北大法宝或华宇元典）实时核验法规现行有效性，避免引用已失效或已修订条款。
- **双后端能力槽**：法规核验MCP后端可插拔配置，支持北大法宝（WorkBuddy内置）和华宇元典（需API Key），见 `assets/mcp-backends.yaml`。
- **APK静态分析**：解包安装包提取权限声明、识别第三方SDK、提取内嵌隐私政策，与文本声明交叉比对。
- **24部法规依据**：法律4部、部门规章8部、国家标准6部、团体标准2类、其他4部，均经MCP后端核验。

## 快速开始

```bash
# 1) 依赖（scripts/ 仅用标准库，通常无需安装）
#    如需增强APK分析能力，可选安装 androguard：
# pip install androguard

# 2) 向业务部门发送材料收集清单
# 参见 assets/input-materials-template.md

# 3) 收到材料后校验完整性
python3 scripts/material_validator.py --materials-dir /path/to/materials/

# 4) APK静态分析
python3 scripts/apk_analyzer.py --apk /path/to/app.apk --output apk_report.json --format summary

# 5) 逐项审查（参照 references/checklist-full.md）

# 6) 生成合规评审报告
python3 scripts/report_generator.py --input check_results.json --apk-analysis apk_report.json --output compliance_report.md
```

## 目录

```
app-compliance-review/
├── SKILL.md                  # 技能定义（AI Agent 可直接读作 skill 定义）
├── README.md                 # 本文件
├── LICENSE                   # 许可证（中英文）
├── requirements.txt          # Python 依赖说明
├── scripts/                  # 可执行脚本
│   ├── apk_analyzer.py       # APK静态分析：提取权限、识别SDK、搜索内嵌隐私政策
│   ├── material_validator.py # 输入材料完整性校验
│   └── report_generator.py   # 合规检查报告生成
├── references/               # 深度文档
│   ├── law-library.md        # 法规依据库（24部法规，经北大法宝核验）
│   ├── article-anchors.md    # 条文锚定表（72个锚点，MCP核验依据）
│   ├── checklist-full.md     # 完整检查清单（11大模块，50+检查项）
│   ├── input-materials-guide.md  # 输入材料详细格式要求
│   └── apk-analysis-guide.md # APK静态分析方法指南
├── assets/                   # 配置与输出模板
│   ├── mcp-backends.yaml     # MCP法规核验后端配置（pkulaw/yuandian切换）
│   ├── input-materials-template.md      # 材料收集清单模板（发业务部门）
    ├── compliance-report-template.md    # 合规评审报告模板
    └── remediation-template.md          # 整改清单模板
```

## 设计原则

1. **声明与事实分离**：文本声明（隐私政策等）与技术事实（APK解包结果）分别采集，再逐项比对，大多数合规风险隐藏在二者偏差中。
2. **可自闭环**：所有检查项均可通过业务部门提供的材料（安装包+文本声明+清单类文档）完成，不纳入需要额外上下文的运维/管理制度检查。
3. **法规实时核验**：数据合规领域法规更新频繁，skill每次运行通过北大法宝MCP工具核验引用法规的现行有效性。
4. **静态分析边界明确**：技术取证获取的是"声明了什么、内嵌了什么、疑似接入了什么"，不等同于运行时实际调用行为，报告中明确标注边界。

## 许可

采用 **CC BY-NC-ND 4.0 + 附加条款** 双层许可：署名／非商业／禁改编 + 禁AI训练 / 禁上架收费平台 / 企业与行政机关识别为商用 / 学术引用格式 / 禁背书 / 权利保留。完整条款见 [LICENSE](LICENSE)。

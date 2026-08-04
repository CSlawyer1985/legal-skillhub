# CCPA Compliance v1.0.5

**美国加州消费者隐私法（CCPA/CPRA）合规检查、风险评估和文档生成工具**

🎉 **v1.0.5 重要更新**：全新统一化CLI接口，与PIPL、GDPR工具体验一致；支持JSON/Markdown/HTML/CSV多格式报告输出；跨法域联合检查功能；纯本地零外部依赖。

## 🌟 核心价值

**为加州市场提供全面的CCPA/CPRA合规解决方案**，帮助涉及加州消费者数据的企业实现合规。

### 解决的关键问题
1. **合规自查困难** - 企业难以全面评估CCPA/CPRA合规状态
2. **消费者权利保障** - 知情权、删除权、选择退出权落实复杂
3. **数据销售管理** - "请勿销售"机制实施困难
4. **服务提供商管理** - 协议和流程合规要求多

## 📁 文件结构

```
ccpa-compliance-1.0.5/
├── SKILL.md                      # 主技能文档
├── README.md                     # 本文件
├── package.json                  # 元数据 (v1.0.5)
├── CHANGELOG.md                  # 更新日志
├── scripts/                      # 核心脚本
│   ├── ccpa-check.py             # CCPA合规检查（统一CLI接口）
│   ├── consumer-rights.py        # 消费者权利检查
│   ├── opt-out-check.py          # 选择退出机制检查
│   ├── security_check_ccpa.py    # 安全检查脚本
│   └── utils/                    # 工具函数库
│       ├── ccpa_validator.py     # CCPA验证工具
│       ├── ccpa_templates.py     # 模板引擎
│       └── gdpr_report_formatter.py # 报告格式化
├── references/                   # 参考文档
│   └── ccpa-law.md               # CCPA法规摘要
```

## 🚀 快速开始

### 运行要求
- Python 3.8+（仅需标准库）
- **无需安装任何外部依赖**
- **无需网络连接**

### 运行CCPA合规检查
```bash
# 场景模式
python scripts/ccpa-check.py --scenario "消费者数据分析"

# 交互模式
python scripts/ccpa-check.py --interactive

# 指定报告格式（JSON / Markdown / HTML / CSV）
python scripts/ccpa-check.py --scenario "数据销售" --format json
```

### 其他专项检查
```bash
# 消费者权利检查
python scripts/consumer-rights.py

# 选择退出机制检查
python scripts/opt-out-check.py

# 安全检查
python scripts/security_check_ccpa.py
```

### 跨法域联合检查（新）
```bash
# 一键运行PIPL + GDPR + CCPA三合一检查
python ../compliance_core/global_check.py
```

## ✨ 主要功能

### 1. CCPA合规检查（统一CLI接口）
- 企业适用性检查
- 消费者权利保障检查
- 数据销售机制检查

### 2. 消费者权利管理
- 知情权、删除权、选择退出权检查

### 3. 数据销售管理
- 识别数据销售活动
- "请勿销售"机制验证
- 选择退出流程检查

## 📊 版本信息

- **版本**: 1.0.5
- **发布日期**: 2026-07-05
- **许可证**: MIT
- **作者**: Wei Wu (wwumit)

## 🛡️ 安全特性

- ✅ **纯本地运行** - 无网络连接
- ✅ **零外部依赖** - 仅Python标准库
- ✅ **代码开源可审计**

## ⚠️ 重要法律声明

### 免责条款

1. **非法律建议**：本技能提供的信息仅供参考，不构成法律建议
2. **专业性咨询**：重大CCPA/CPRA合规决策必须咨询专业律师
3. **责任限制**：用户对使用本技能的所有决策和后果负全责
4. **适用性限制**：专为加州CCPA/CPRA设计

完整法律声明详见 `SKILL.md`。

---

**CCPA Compliance v1.0.5 - Wei Wu (wwumit)**

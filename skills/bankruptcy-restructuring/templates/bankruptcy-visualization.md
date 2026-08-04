# 破产程序可视化HTML模板

使用Mermaid.js生成可交互的破产程序架构图，用于向客户展示分配顺序、重整时间线和多方关系。

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>破产案件可视化</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, "Microsoft YaHei", "PingFang SC", sans-serif;
            background: #f5f7fa;
            color: #1a1a2e;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { text-align: center; font-size: 24px; margin-bottom: 8px; }
        .subtitle { text-align: center; color: #666; margin-bottom: 30px; font-size: 14px; }
        .chart-box {
            background: white;
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            margin-bottom: 24px;
        }
        .chart-box h2 {
            font-size: 18px;
            margin-bottom: 16px;
            padding-left: 12px;
            border-left: 4px solid #3b82f6;
        }
        .chart-box svg { width: 100%; height: auto; }
        .notes {
            background: #fff8e1;
            border-radius: 8px;
            padding: 16px;
            margin-top: 16px;
        }
        .notes h3 { font-size: 14px; color: #b45309; margin-bottom: 8px; }
        .notes p { font-size: 13px; color: #92400e; line-height: 1.6; }
        @media (prefers-color-scheme: dark) {
            body { background: #0f172a; color: #e2e8f0; }
            .chart-box { background: #1e293b; box-shadow: 0 2px 12px rgba(0,0,0,0.3); }
            .notes { background: #451a03; }
            .notes h3 { color: #fbbf24; }
            .notes p { color: #fde68a; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚖️ 破产案件可视化</h1>
        <p class="subtitle">分配顺序 · 程序流程 · 多方关系 · 时间线</p>

        <!-- 一、清偿顺序图 -->
        <div class="chart-box">
            <h2>📊 法定清偿顺序</h2>
            <div class="mermaid">
                graph LR
                    subgraph assets[💰 破产财产]
                        A[破产财产总额<br/>评估值：XXX万元]
                    end

                    subgraph costs[📄 优先支付]
                        C1[破产费用<br/>诉讼费+管理费+变价费]
                        C2[共益债务<br/>继续经营新债]
                    end

                    subgraph distribution[📋 按顺位分配]
                        D1[🥇 第一顺位<br/>职工债权<br/>工资+社保+补偿金]
                        D2[🥈 第二顺位<br/>税款债权<br/>欠缴税款+社保]
                        D3[🥉 第三顺位<br/>普通债权<br/>合同/侵权/无担保]
                        D4[最后<br/>劣后债权<br/>股东借款等]
                    end

                    A -->|第一步| costs
                    costs -->|剩余| D1
                    D1 -->|剩余| D2
                    D2 -->|剩余| D3
                    D3 -->|剩余| D4

                    style assets fill:#3b82f622,stroke:#3b82f6,stroke-width:2px
                    style costs fill:#f59e0b22,stroke:#f59e0b,stroke-width:2px
                    style D1 fill:#10b98122,stroke:#10b981,stroke-width:2px
                    style D2 fill:#8b5cf622,stroke:#8b5cf6,stroke-width:2px
                    style D3 fill:#ef444422,stroke:#ef4444,stroke-width:2px
                    style D4 fill:#1e293b22,stroke:#1e293b,stroke-width:1px
            </div>
        </div>

        <!-- 二、程序选择路径 -->
        <div class="chart-box">
            <h2>🔄 破产程序选择路径</h2>
            <div class="mermaid">
                graph TD
                    START[企业资不抵债] --> CHOICE{程序选择}

                    CHOICE -->|有挽救价值| REORG[💊 破产重整]
                    CHOICE -->|无挽救价值| LIQ[💀 破产清算]
                    CHOICE -->|双方协商| COMP[🤝 破产和解]

                    REORG --> R1[重整期间 6+3个月]
                    R1 --> R2{重整计划}
                    R2 -->|通过+批准| R3[✅ 执行重整计划]
                    R2 -->|未通过/未批准| LIQ
                    R3 -->|执行完毕| R4[✅ 企业重生]
                    R3 -->|执行不能| LIQ

                    LIQ --> L1[财产变价]
                    L1 --> L2[按顺序分配]
                    L2 --> L3[✅ 破产终结+注销]

                    COMP --> C1[和解协议]
                    C1 -->|通过+批准| C2[✅ 执行和解协议]
                    C1 -->|未通过/未批准| LIQ
                    C2 -->|执行完毕| C3[✅ 企业存续]
                    C2 -->|执行不能| LIQ

                    style START fill:#3b82f622,stroke:#3b82f6
                    style REORG fill:#10b98122,stroke:#10b981
                    style LIQ fill:#ef444422,stroke:#ef4444
                    style COMP fill:#8b5cf622,stroke:#8b5cf6
                    style R4 fill:#10b98122,stroke:#10b981
                    style C3 fill:#8b5cf622,stroke:#8b5cf6
                    style L3 fill:#ef444422,stroke:#ef4444
            </div>
        </div>

        <!-- 三、重整计划时间线 -->
        <div class="chart-box">
            <h2>⏱️ 重整计划全流程时间线</h2>
            <div class="mermaid">
                gantt
                    title 重整计划流程
                    dateFormat  YYYY-MM-DD
                    axisFormat  %m-%d

                    section 申请与受理
                    破产申请与受理           :a1, 2026-01-01, 30d
                    指定管理人               :a2, after a1, 7d
                    债权申报期               :a3, after a1, 45d

                    section 重整期间
                    重整计划草案制定         :b1, after a3, 60d
                    与债权人协商             :b2, after a3, 60d
                    引进投资人               :b3, after a3, 45d
                    提交重整计划草案         :milestone, after b1, 0d

                    section 表决与批准
                    债权人会议表决           :c1, after b1, 15d
                    法院审查与裁定批准       :c2, after c1, 30d

                    section 执行与监督
                    重整计划执行             :d1, after c2, 180d
                    管理人监督               :d2, after c2, 180d
                    执行完毕+终结程序        :milestone, after d1, 0d
            </div>
        </div>

        <!-- 四、多方关系图 -->
        <div class="chart-box">
            <h2>🏛️ 破产案件多方关系</h2>
            <div class="mermaid">
                graph TB
                    subgraph court[法院]
                        M[管理人<br/>指定+监督+报告]
                    end

                    subgraph parties[各方当事人]
                        D[债务人<br/>申请+配合+留守]
                        C[债权人<br/>申报+表决+监督]
                        S[出资人<br/>权益调整+表决]
                        I[投资人<br/>出资+经营+退出]
                    end

                    subgraph admin[管理人]
                        MA[管理人团队<br/>接管+调查+审查+处置+分配]
                    end

                    M -->|指定| MA
                    MA -->|报告| M

                    D -->|移交| MA
                    MA -->|管理| D

                    C -->|申报债权| MA
                    MA -->|审查确认| C

                    C -->|参与表决| C

                    S -->|出资人权益| D
                    MA -->|调整方案| S

                    I -->|投资| MA
                    MA -->|安排| I

                    style court fill:#3b82f622,stroke:#3b82f6,stroke-width:2px
                    style parties fill:#10b98122,stroke:#10b981,stroke-width:2px
                    style admin fill:#f59e0b22,stroke:#f59e0b,stroke-width:2px
            </div>
        </div>

        <div class="notes">
            <h3>📌 说明</h3>
            <p>1. 本图为通用可视化模板，各案具体情况需调整参数。<br>
            2. 清偿顺序严格按《企业破产法》第113条，不可逾越。<br>
            3. 时间线为示例，实际周期取决于案件复杂程度和法院工作效率。<br>
            4. ✅ = 已完成 &nbsp;&nbsp; ⏳ = 进行中 &nbsp;&nbsp; 📅 = 计划中</p>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({
            startOnLoad: true,
            theme: 'neutral',
            themeVariables: {
                fontFamily: '"Microsoft YaHei", "PingFang SC", sans-serif',
                fontSize: '14px',
                primaryColor: '#3b82f6',
                primaryTextColor: '#1a1a2e',
                primaryBorderColor: '#3b82f6',
                lineColor: '#94a3b8',
                secondaryColor: '#10b981',
                tertiaryColor: '#f5f7fa',
            }
        });
    </script>
</body>
</html>
```

## 二、使用说明

**适用场景：** 向客户解释破产程序/分配顺序/重整时间线/多方关系

**使用流程：**
1. 根据具体破产案件的参数（资产额/债权额/各方信息）替换模板中的示例数值
2. 保存为HTML文件，向客户展示
3. 团队内部会议使用

**定制要点：**
- 修改清偿图中的资产和债权数值
- 在程序选择路径中高亮当前所处程序
- 修改时间线的日期和周期

# 家族传承架构图HTML可视化模板

使用Mermaid.js生成可交互的家族传承架构图，用于向客户展示家族关系、资产配置和传承路径。

## 一、家族关系与资产分布图

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>家族财富传承架构图</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, "Microsoft YaHei", "PingFang SC", sans-serif;
            background: #f5f7fa;
            color: #1a1a2e;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 {
            text-align: center;
            font-size: 24px;
            margin-bottom: 8px;
            color: #1a1a2e;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .family-tree {
            background: white;
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            margin-bottom: 24px;
        }
        .family-tree svg { width: 100%; height: auto; }
        .legend {
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
            justify-content: center;
            margin: 16px 0;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 13px;
            color: #555;
        }
        .legend-dot {
            width: 12px; height: 12px;
            border-radius: 50%;
            display: inline-block;
        }
        .legend-dot.green { background: #10b981; }
        .legend-dot.blue { background: #3b82f6; }
        .legend-dot.orange { background: #f59e0b; }
        .legend-dot.purple { background: #8b5cf6; }
        .legend-dot.red { background: #ef4444; }

        .flow-section { margin-bottom: 24px; }
        .flow-section h2 {
            font-size: 18px;
            margin-bottom: 12px;
            padding-left: 12px;
            border-left: 4px solid #3b82f6;
        }
        .flow-section svg { width: 100%; height: auto; }
        .notes {
            background: #fff8e1;
            border-radius: 8px;
            padding: 16px;
            margin-top: 16px;
        }
        .notes h3 { font-size: 14px; color: #b45309; margin-bottom: 8px; }
        .notes p { font-size: 13px; color: #92400e; line-height: 1.6; }

        /* Dark mode */
        @media (prefers-color-scheme: dark) {
            body { background: #0f172a; color: #e2e8f0; }
            .family-tree { background: #1e293b; box-shadow: 0 2px 12px rgba(0,0,0,0.3); }
            .legend { background: #334155; }
            .legend-item { color: #cbd5e1; }
            .notes { background: #451a03; }
            .notes h3 { color: #fbbf24; }
            .notes p { color: #fde68a; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏛️ 家族财富传承架构图</h1>
        <p class="subtitle">家族关系 · 资产配置 · 传承路径 · 风险隔离</p>

        <!-- 图例 -->
        <div class="legend">
            <span class="legend-item"><span class="legend-dot green"></span> 家庭成员</span>
            <span class="legend-item"><span class="legend-dot blue"></span> 法律工具</span>
            <span class="legend-item"><span class="legend-dot orange"></span> 资产配置</span>
            <span class="legend-item"><span class="legend-dot purple"></span> 受益人/分配路径</span>
            <span class="legend-item"><span class="legend-dot red"></span> 风险隔离层</span>
        </div>

        <!-- 一、家族关系图谱 -->
        <div class="family-tree">
            <h2>👨‍👩‍👧‍👦 家族关系与资产分布</h2>
            <div class="mermaid">
                graph TB
                    subgraph patriarch[创一代 · 委托人]
                        F[父亲<br/>65岁 · 企业家]
                        M[母亲<br/>62岁]
                    end

                    subgraph children[二代 · 受益人]
                        C1[长子 40岁<br/>GP·企业CEO]
                        C2[次女 37岁<br/>LP·无参与经营]
                        C3[三子 33岁<br/>LP·海外]
                    end

                    subgraph grandchildren[三代 · 未来受益人]
                        G1[长孙 12岁]
                        G2[孙女 8岁]
                        G3[孙女 5岁]
                    end

                    F --- M
                    F --- C1
                    F --- C2
                    F --- C3
                    C1 --- G1
                    C2 --- G2
                    C3 --- G3

                    %% 资产标注
                    F -.->|🏢 企业股权<br/>估值5亿| biz[企业资产层]
                    F -.->|🏠 不动产<br/>估值8000万| realty[不动产]
                    F -.->|💰 金融资产<br/>估值5000万| finance[金融资产]
                    F -.->|🌏 境外资产<br/>估值3000万| overseas[境外资产]

                    style patriarch fill:#10b98122,stroke:#10b981,stroke-width:2px
                    style children fill:#3b82f622,stroke:#3b82f6,stroke-width:1px
                    style grandchildren fill:#8b5cf622,stroke:#8b5cf6,stroke-width:1px
                    style biz fill:#f59e0b22,stroke:#f59e0b,stroke-width:1px
                    style realty fill:#f59e0b22,stroke:#f59e0b,stroke-width:1px
                    style finance fill:#f59e0b22,stroke:#f59e0b,stroke-width:1px
                    style overseas fill:#f59e0b22,stroke:#f59e0b,stroke-width:1px
            </div>
        </div>

        <!-- 二、信托架构图 -->
        <div class="family-tree">
            <h2>🏦 家族信托架构</h2>
            <div class="mermaid">
                graph TB
                    subgraph trust_layer[🏛️ 家族信托层 · 强隔离]
                        T[家族信托<br/>委托人：创一代<br/>受托人：XX信托]
                        TC[信托合同<br/>· 期限：50年<br/>· 分配条件]
                    end

                    subgraph protection[🛡️ 保护机制]
                        PR[保护人/监察人<br/>律师+会计师+家族代表]
                        LW[意愿书<br/>Letter of Wishes]
                    end

                    subgraph structure[📊 持股架构]
                        SPV[SPV控股公司<br/>100%信托持有]
                        GP[GP有限合伙<br/>长子-控制权]
                        LP1[LP-次女<br/>收益权]
                        LP2[LP-三子<br/>收益权]
                    end

                    subgraph assets[💰 信托财产]
                        eq[股权 5亿]
                        re[不动产 8000万]
                        fi[金融资产 5000万]
                        ins[保险金信托 保额6000万]
                    end

                    F1[创一代·委托人] -->|设立| T
                    T --> TC
                    T --> PR
                    TC --> LW

                    T -->|持有| SPV
                    SPV -->|GP| GP
                    SPV -->|LP| LP1
                    SPV -->|LP| LP2

                    T -->|管理| assets
                    eq --> SPV
                    re --> SPV
                    fi --> T

                    style trust_layer fill:#ef444411,stroke:#ef4444,stroke-width:2px
                    style T fill:#3b82f622,stroke:#3b82f6,stroke-width:2px
                    style protection fill:#f59e0b22,stroke:#f59e0b,stroke-width:2px
                    style structure fill:#10b98122,stroke:#10b981,stroke-width:2px
                    style assets fill:#8b5cf622,stroke:#8b5cf6,stroke-width:2px
            </div>
        </div>

        <!-- 三、分配方案 -->
        <div class="family-tree">
            <h2>📋 信托受益分配方案</h2>
            <div class="mermaid">
                graph LR
                    T2[家族信托<br/>总资产约6.6亿] -->|定期分配| A1[基本生活费<br/>· 配偶每月5万<br/>· 子女每月3万<br/>· 孙辈教育金]
                    T2 -->|条件分配| A2[重大事项<br/>· 结婚 200万/人<br/>· 生育 500万/人<br/>· 购房 最高800万]
                    T2 -->|条件分配| A3[创业支持<br/>· 评审制<br/>· 最高1000万/人]
                    T2 -->|保留分配| A4[特殊需要<br/>· 医疗备用金<br/>· 协议限额]
                    T2 -->|最终分配| A5[信托终止<br/>40岁 分配50%<br/>50岁 分配100%]

                    style T2 fill:#3b82f622,stroke:#3b82f6,stroke-width:2px
                    style A1 fill:#10b98122,stroke:#10b981,stroke-width:1px
                    style A2 fill:#f59e0b22,stroke:#f59e0b,stroke-width:1px
                    style A3 fill:#8b5cf622,stroke:#8b5cf6,stroke-width:1px
                    style A4 fill:#ef444422,stroke:#ef4444,stroke-width:1px
                    style A5 fill:#1e293b22,stroke:#1e293b,stroke-width:1px
            </div>
        </div>

        <!-- 四、传承路径对比 -->
        <div class="family-tree">
            <h2>⚖️ 传承路径对比</h2>
            <div class="mermaid">
                graph TD
                    subgraph without[❌ 不做规划]
                        W1[适用法定继承] --> W2[继承公证/诉讼]
                        W2 --> W3[各继承人分别过户]
                        W3 --> W4[企业控制权分散+税务不确定+纠纷风险]
                    end

                    subgraph with[✅ 信托规划]
                        S1[设立家族信托] --> S2[信托统一持股]
                        S2 --> S3[企业控制权集中]
                        S3 --> S4[家族治理制度化]
                        S4 --> S5[企业永续+家族和谐+税务优化]
                    end

                    style without fill:#ef444411,stroke:#ef4444,stroke-width:2px
                    style with fill:#10b98111,stroke:#10b981,stroke-width:2px
            </div>
        </div>

        <div class="notes">
            <h3>📌 说明</h3>
            <p>1. 本架构图为示例方案，实际架构需根据客户具体资产状况、家庭结构和法律环境定制。<br>
            2. 信托合同中的分配条款具有法律效力，意愿书（Letter of Wishes）作为受托人行权参考不具法律约束力。<br>
            3. 客户姓名、资产信息和所有数据均已脱敏处理。<br>
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

**适用场景：** 向高净值客户展示财富传承架构、信托方案说明、家族会议演示

**使用流程：**
1. 完成「资产盘点清单与传承需求问卷」收集客户信息
2. 根据SKILL「模式一：综合传承规划」设计传承方案
3. 将方案参数填入本模板的Mermaid代码块中
4. 保存为HTML文件，向客户展示

**定制要点：**
- 修改 `patriarch`、`children`、`grandchildren` 节点为实际家庭成员
- 修改资产数值为企业实际估值
- 修改分配方案为信托合同中的实际分配条款
- 可选择保留/删除某个架构图区块

# V1 主体关系网络图 — 详细设计规范

## 适用场景

当报告中存在以下内容时生成本图：
- 当事人全景分析表格
- 实际控制人分析
- 法定代表人变更链分析
- 人员交叉分析
- 关联关系图（文字版）

## 数据提取规则

从报告中提取以下字段：

| 字段 | 来源位置 | 示例 |
|------|---------|------|
| 主体名称 | 当事人表格"名称"列 | 东莞市成隆实业投资有限公司 |
| 法律角色 | 当事人表格"法律地位"列 | 主债务人/被执行人 |
| 持股关系 | 实际控制人分析 | 潘志成持有成隆实业58.9% |
| 担保关系 | 核心法律关系表格 | 华琏包装最高额保证8800万 |
| 人员关联 | 人员交叉分析 | 李国辉同时担任成隆包装法定代表人和世纪豪庭监事 |
| 异常标记 | 核心异常描述 | 家健实业成立于债务危机前4天 |

## SVG完整实现模板

以下为基于成隆系案件的完整SVG示例，可作为生成其他案件图表的参考：

```xml
<svg width="1200" height="820" xmlns="http://www.w3.org/2000/svg" 
     font-family="'PingFang SC','Microsoft YaHei','Noto Sans SC',sans-serif">

  <!-- ===== 背景 ===== -->
  <rect width="1200" height="820" fill="#FFFFFF"/>

  <!-- ===== 标题 ===== -->
  <text x="600" y="32" text-anchor="middle" font-size="18" font-weight="bold" fill="#1A3A5C">
    主体关系网络图
  </text>
  <text x="600" y="52" text-anchor="middle" font-size="12" fill="#546E7A">
    成隆系金融借款合同纠纷执行案
  </text>
  <line x1="40" y1="62" x2="1160" y2="62" stroke="#CFD8DC" stroke-width="1"/>

  <!-- ===== 图例（右下角）===== -->
  <g transform="translate(920, 660)">
    <rect width="240" height="140" rx="6" fill="#F5F7FA" stroke="#CFD8DC" stroke-width="1"/>
    <text x="12" y="20" font-size="11" font-weight="bold" fill="#1A3A5C">图例</text>
    <!-- 节点形状 -->
    <circle cx="22" cy="38" r="8" fill="none" stroke="#546E7A" stroke-width="1.5"/>
    <text x="36" y="42" font-size="10" fill="#333">自然人</text>
    <rect x="14" y="52" width="16" height="12" rx="3" fill="none" stroke="#546E7A" stroke-width="1.5"/>
    <text x="36" y="62" font-size="10" fill="#333">公司法人</text>
    <!-- 边框颜色 -->
    <rect x="14" y="72" width="16" height="12" rx="3" fill="none" stroke="#E05A47" stroke-width="2"/>
    <text x="36" y="82" font-size="10" fill="#333">被执行人</text>
    <rect x="14" y="88" width="16" height="12" rx="3" fill="none" stroke="#2E7D32" stroke-width="2"/>
    <text x="36" y="98" font-size="10" fill="#333">申请执行人</text>
    <rect x="14" y="104" width="16" height="12" rx="3" fill="none" stroke="#D4A017" stroke-width="2" stroke-dasharray="4,2"/>
    <text x="36" y="114" font-size="10" fill="#333">可疑关联方</text>
    <!-- 连线 -->
    <line x1="14" y1="126" x2="30" y2="126" stroke="#1A3A5C" stroke-width="1.5" marker-end="url(#arrow-legend)"/>
    <text x="36" y="130" font-size="10" fill="#333">持股/控制</text>
  </g>

  <!-- ===== 箭头定义 ===== -->
  <defs>
    <marker id="arrow-blue" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#1A3A5C"/>
    </marker>
    <marker id="arrow-orange" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#D4A017"/>
    </marker>
    <marker id="arrow-green" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#2E7D32"/>
    </marker>
    <marker id="arrow-gray" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#546E7A"/>
    </marker>
    <marker id="arrow-legend" markerWidth="6" markerHeight="5" refX="6" refY="2.5" orient="auto">
      <polygon points="0 0, 6 2.5, 0 5" fill="#1A3A5C"/>
    </marker>
  </defs>

  <!-- ===== 债权人区（左侧竖条）===== -->
  <rect x="20" y="75" width="180" height="280" rx="8" fill="#F0F4F8" stroke="#CFD8DC" stroke-width="1"/>
  <text x="110" y="95" text-anchor="middle" font-size="11" font-weight="bold" fill="#2E7D32">债权人链条</text>

  <!-- 佛山瓴岸（现债权人）-->
  <rect x="35" y="105" width="150" height="50" rx="6" fill="#FFFFFF" stroke="#2E7D32" stroke-width="2"/>
  <text x="110" y="126" text-anchor="middle" font-size="11" font-weight="bold" fill="#2E7D32">佛山市瓴岸</text>
  <text x="110" y="142" text-anchor="middle" font-size="10" fill="#546E7A">申请执行人（现）</text>

  <!-- 转让箭头 -->
  <line x1="110" y1="155" x2="110" y2="170" stroke="#2E7D32" stroke-width="1.5" stroke-dasharray="4,2" marker-end="url(#arrow-green)"/>
  <text x="115" y="165" font-size="9" fill="#2E7D32">受让</text>

  <!-- 广州资产 -->
  <rect x="35" y="172" width="150" height="44" rx="6" fill="#FFFFFF" stroke="#546E7A" stroke-width="1"/>
  <text x="110" y="190" text-anchor="middle" font-size="11" fill="#333">广州资产管理</text>
  <text x="110" y="206" text-anchor="middle" font-size="10" fill="#546E7A">前申请执行人</text>

  <line x1="110" y1="216" x2="110" y2="231" stroke="#546E7A" stroke-width="1.5" stroke-dasharray="4,2" marker-end="url(#arrow-gray)"/>

  <!-- 中国信达 -->
  <rect x="35" y="233" width="150" height="44" rx="6" fill="#FFFFFF" stroke="#546E7A" stroke-width="1"/>
  <text x="110" y="251" text-anchor="middle" font-size="11" fill="#333">中国信达广东</text>
  <text x="110" y="267" text-anchor="middle" font-size="10" fill="#546E7A">中间受让人</text>

  <line x1="110" y1="277" x2="110" y2="292" stroke="#546E7A" stroke-width="1.5" stroke-dasharray="4,2" marker-end="url(#arrow-gray)"/>

  <!-- 中国银行 -->
  <rect x="35" y="294" width="150" height="44" rx="6" fill="#FFFFFF" stroke="#546E7A" stroke-width="1"/>
  <text x="110" y="312" text-anchor="middle" font-size="11" fill="#333">中国银行东莞分行</text>
  <text x="110" y="328" text-anchor="middle" font-size="10" fill="#546E7A">原债权人</text>

  <!-- 债权人→主债务人连线 -->
  <line x1="200" y1="200" x2="340" y2="380" stroke="#1A3A5C" stroke-width="1" stroke-dasharray="6,3" marker-end="url(#arrow-blue)"/>
  <text x="255" y="285" font-size="9" fill="#1A3A5C" transform="rotate(-30,255,285)">借款/执行</text>

  <!-- ===== 控制人层（顶部中央）===== -->
  <!-- 潘志成 -->
  <circle cx="480" cy="130" r="38" fill="#FFFFFF" stroke="#E05A47" stroke-width="2.5"/>
  <text x="480" y="126" text-anchor="middle" font-size="13" font-weight="bold" fill="#E05A47">潘志成</text>
  <text x="480" y="142" text-anchor="middle" font-size="10" fill="#546E7A">被执行人</text>
  <text x="480" y="156" text-anchor="middle" font-size="9" fill="#546E7A">1971.04.11</text>

  <!-- 潘智新 -->
  <circle cx="680" cy="130" r="38" fill="#FFFFFF" stroke="#E05A47" stroke-width="2.5"/>
  <text x="680" y="126" text-anchor="middle" font-size="13" font-weight="bold" fill="#E05A47">潘智新</text>
  <text x="680" y="142" text-anchor="middle" font-size="10" fill="#546E7A">被执行人</text>
  <text x="680" y="156" text-anchor="middle" font-size="9" fill="#546E7A">1973.02.10</text>

  <!-- 兄弟关系连线 -->
  <line x1="518" y1="130" x2="642" y2="130" stroke="#546E7A" stroke-width="1" stroke-dasharray="3,3"/>
  <text x="580" y="122" text-anchor="middle" font-size="10" fill="#546E7A">兄弟</text>

  <!-- ===== 被执行公司层（中部）===== -->
  <!-- 成隆实业 -->
  <rect x="340" y="240" width="160" height="60" rx="8" fill="#FFFFFF" stroke="#E05A47" stroke-width="2"/>
  <text x="420" y="264" text-anchor="middle" font-size="12" font-weight="bold" fill="#E05A47">成隆实业</text>
  <text x="420" y="280" text-anchor="middle" font-size="10" fill="#546E7A">主债务人·被执行人</text>
  <text x="420" y="293" text-anchor="middle" font-size="9" fill="#546E7A">法代：潘志成</text>

  <!-- 世纪豪庭 -->
  <rect x="540" y="240" width="160" height="60" rx="8" fill="#FFFFFF" stroke="#E05A47" stroke-width="2"/>
  <text x="620" y="264" text-anchor="middle" font-size="12" font-weight="bold" fill="#E05A47">世纪豪庭酒店</text>
  <text x="620" y="280" text-anchor="middle" font-size="10" fill="#546E7A">借款人·被执行人</text>
  <text x="620" y="293" text-anchor="middle" font-size="9" fill="#546E7A">法代：高庆忠（变更后）</text>

  <!-- 成隆包装 -->
  <rect x="740" y="240" width="160" height="60" rx="8" fill="#FFFFFF" stroke="#E05A47" stroke-width="2"/>
  <text x="820" y="264" text-anchor="middle" font-size="12" font-weight="bold" fill="#E05A47">成隆包装</text>
  <text x="820" y="280" text-anchor="middle" font-size="10" fill="#546E7A">借款人·被执行人</text>
  <text x="820" y="293" text-anchor="middle" font-size="9" fill="#546E7A">法代：李国辉（变更后）</text>

  <!-- 华琏包装 -->
  <rect x="940" y="240" width="160" height="60" rx="8" fill="#FFFFFF" stroke="#E05A47" stroke-width="2"/>
  <text x="1020" y="264" text-anchor="middle" font-size="12" font-weight="bold" fill="#E05A47">华琏包装</text>
  <text x="1020" y="280" text-anchor="middle" font-size="10" fill="#546E7A">最高额保证·被执行人</text>
  <text x="1020" y="293" text-anchor="middle" font-size="9" fill="#546E7A">法代：翟耀真（变更后）</text>

  <!-- 成隆鞋材厂 -->
  <!-- 菱形 -->
  <polygon points="420,360 460,390 420,420 380,390" fill="#FFFFFF" stroke="#E05A47" stroke-width="2"/>
  <text x="420" y="387" text-anchor="middle" font-size="11" font-weight="bold" fill="#E05A47">成隆鞋材厂</text>
  <text x="420" y="402" text-anchor="middle" font-size="9" fill="#546E7A">个体户·被执行人</text>

  <!-- ===== 持股连线（控制人→公司）===== -->
  <!-- 潘志成→成隆实业 -->
  <line x1="460" y1="165" x2="400" y2="240" stroke="#1A3A5C" stroke-width="1.5" marker-end="url(#arrow-blue)"/>
  <text x="415" y="205" font-size="10" fill="#1A3A5C">58.9%</text>

  <!-- 潘志成→世纪豪庭 -->
  <line x1="480" y1="168" x2="580" y2="240" stroke="#1A3A5C" stroke-width="1.5" marker-end="url(#arrow-blue)"/>
  <text x="530" y="205" font-size="10" fill="#1A3A5C">60%</text>

  <!-- 潘志成→成隆包装 -->
  <line x1="510" y1="155" x2="780" y2="240" stroke="#1A3A5C" stroke-width="1.5" marker-end="url(#arrow-blue)"/>
  <text x="660" y="190" font-size="10" fill="#1A3A5C">100%</text>

  <!-- 潘智新→华琏包装 -->
  <line x1="710" y1="155" x2="1000" y2="240" stroke="#1A3A5C" stroke-width="1.5" marker-end="url(#arrow-blue)"/>
  <text x="870" y="190" font-size="10" fill="#1A3A5C">100%</text>

  <!-- 潘智新→成隆实业 -->
  <line x1="660" y1="160" x2="480" y2="240" stroke="#1A3A5C" stroke-width="1.5" marker-end="url(#arrow-blue)"/>
  <text x="555" y="195" font-size="10" fill="#1A3A5C">41.1%</text>

  <!-- 潘智新→世纪豪庭 -->
  <line x1="680" y1="168" x2="660" y2="240" stroke="#1A3A5C" stroke-width="1.5" marker-end="url(#arrow-blue)"/>
  <text x="695" y="205" font-size="10" fill="#1A3A5C">40%</text>

  <!-- ===== 关联公司层（底部）===== -->
  <!-- 家健实业（可疑）-->
  <rect x="280" y="480" width="150" height="55" rx="6" fill="#FFF8E1" stroke="#D4A017" stroke-width="2" stroke-dasharray="5,3"/>
  <text x="355" y="500" text-anchor="middle" font-size="11" font-weight="bold" fill="#D4A017">家健实业</text>
  <text x="355" y="516" text-anchor="middle" font-size="10" fill="#546E7A">高庆忠100%</text>
  <text x="355" y="530" text-anchor="middle" font-size="9" fill="#E05A47">⚠ 债务危机前4天成立</text>

  <!-- 新凯包装（可疑）-->
  <rect x="460" y="480" width="150" height="55" rx="6" fill="#FFF8E1" stroke="#D4A017" stroke-width="2" stroke-dasharray="5,3"/>
  <text x="535" y="500" text-anchor="middle" font-size="11" font-weight="bold" fill="#D4A017">新凯包装</text>
  <text x="535" y="516" text-anchor="middle" font-size="10" fill="#546E7A">翟素华100%</text>
  <text x="535" y="530" text-anchor="middle" font-size="9" fill="#E05A47">⚠ 执行高峰期成立</text>

  <!-- 滨海中心开发 -->
  <rect x="640" y="480" width="150" height="55" rx="6" fill="#FFFFFF" stroke="#D4A017" stroke-width="1.5" stroke-dasharray="5,3"/>
  <text x="715" y="500" text-anchor="middle" font-size="11" font-weight="bold" fill="#D4A017">滨海中心开发</text>
  <text x="715" y="516" text-anchor="middle" font-size="10" fill="#546E7A">潘志成80%</text>
  <text x="715" y="530" text-anchor="middle" font-size="9" fill="#546E7A">立案19条·待核实</text>

  <!-- 陈占有 -->
  <circle cx="860" cy="508" r="32" fill="#FFFFFF" stroke="#D4A017" stroke-width="1.5" stroke-dasharray="5,3"/>
  <text x="860" y="504" text-anchor="middle" font-size="11" font-weight="bold" fill="#D4A017">陈占有</text>
  <text x="860" y="520" text-anchor="middle" font-size="9" fill="#546E7A">前配偶·被执行人</text>

  <!-- 潘浩彬 -->
  <circle cx="980" cy="508" r="32" fill="#FFFFFF" stroke="#D4A017" stroke-width="1.5" stroke-dasharray="5,3"/>
  <text x="980" y="504" text-anchor="middle" font-size="11" font-weight="bold" fill="#D4A017">潘浩彬</text>
  <text x="980" y="520" text-anchor="middle" font-size="9" fill="#546E7A">成年子女·代持风险</text>

  <!-- ===== 关联连线（控制人→关联公司）===== -->
  <!-- 潘志成→家健实业（财务负责人）-->
  <line x1="455" y1="165" x2="355" y2="480" stroke="#D4A017" stroke-width="1.5" stroke-dasharray="6,3" marker-end="url(#arrow-orange)"/>
  <text x="385" y="330" font-size="9" fill="#D4A017">财务负责人</text>

  <!-- 潘志成→滨海中心开发 -->
  <line x1="500" y1="168" x2="700" y2="480" stroke="#D4A017" stroke-width="1.5" stroke-dasharray="6,3" marker-end="url(#arrow-orange)"/>
  <text x="620" y="330" font-size="9" fill="#D4A017">80%</text>

  <!-- 潘志成→陈占有（前配偶）-->
  <line x1="510" y1="160" x2="840" y2="480" stroke="#546E7A" stroke-width="1" stroke-dasharray="3,3"/>
  <text x="700" y="310" font-size="9" fill="#546E7A">前配偶</text>

  <!-- 潘志成→潘浩彬（父子）-->
  <line x1="515" y1="162" x2="960" y2="480" stroke="#546E7A" stroke-width="1" stroke-dasharray="3,3"/>
  <text x="780" y="290" font-size="9" fill="#546E7A">父子</text>

  <!-- 翟素华→新凯包装 -->
  <line x1="1020" y1="300" x2="610" y2="480" stroke="#D4A017" stroke-width="1.5" stroke-dasharray="6,3" marker-end="url(#arrow-orange)"/>
  <text x="840" y="390" font-size="9" fill="#D4A017">100%</text>

  <!-- 高庆忠→家健实业 -->
  <line x1="620" y1="300" x2="430" y2="480" stroke="#D4A017" stroke-width="1.5" stroke-dasharray="6,3" marker-end="url(#arrow-orange)"/>
  <text x="500" y="395" font-size="9" fill="#D4A017">100%</text>

  <!-- ===== 异常标注区（底部说明）===== -->
  <rect x="20" y="600" width="880" height="50" rx="6" fill="#FFF3E0" stroke="#FF5722" stroke-width="1"/>
  <text x="30" y="620" font-size="11" font-weight="bold" fill="#FF5722">⚠ 关键异常时间节点</text>
  <text x="30" y="638" font-size="10" fill="#333">
    家健实业成立（2015.11.20）距债务逾期仅4天 | 华琏包装股权转让（2015.12.25）在债务危机爆发后1个月 | 新凯包装成立（2019.06）正值执行高峰期
  </text>

</svg>
```

## 节点数量建议

| 主体数量 | 画布尺寸 | 字体大小 |
|---------|---------|---------|
| ≤10个 | 900×600 | 13px |
| 11-20个 | 1200×800 | 12px |
| 21-30个 | 1400×900 | 11px |
| >30个 | 分图展示 | 11px |

## 分图策略

当主体超过30个时，拆分为：
1. **核心控制网络图**：仅展示被执行人和直接控制人
2. **关联方扩展图**：展示可疑关联方和潜在追偿对象
3. **债权人结构图**：展示债权转让链条和并行债权人

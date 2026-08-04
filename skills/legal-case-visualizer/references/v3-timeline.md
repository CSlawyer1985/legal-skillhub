# V3 案件时间轴图 — 详细设计规范

## 适用场景

当报告中存在以下内容时生成本图：
- 案件时间轴表格
- 关键时间节点描述
- 法定代表人变更链分析

## 数据提取规则

从报告时间轴表格中提取：

| 字段 | 说明 |
|------|------|
| 时间 | 精确到年月，格式：YYYY.MM |
| 事件名称 | 简化为≤10字 |
| 事件类型 | 借款/违约/转让/执行/异常/判决 |
| 金额（可选）| 如有则标注 |

## 事件类型颜色编码

| 类型 | 圆点颜色 | 标签背景 |
|------|---------|---------|
| 借款/合同 | #1A3A5C 深海军蓝 | #EBF3FA |
| 违约/逾期 | #E05A47 珊瑚红 | #FFEBEE |
| 债权转让 | #2E7D32 森林绿 | #E8F5E9 |
| 执行/拍卖 | #D4A017 琥珀金 | #FFF8E1 |
| 异常行为 | #FF5722 橙红 | #FBE9E7（加⚠图标） |
| 判决/裁定 | #546E7A 石板灰 | #ECEFF1 |

## SVG完整实现模板

```xml
<svg width="1400" height="420" xmlns="http://www.w3.org/2000/svg"
     font-family="'PingFang SC','Microsoft YaHei','Noto Sans SC',sans-serif">

  <rect width="1400" height="420" fill="#FFFFFF"/>

  <!-- 标题 -->
  <text x="700" y="28" text-anchor="middle" font-size="17" font-weight="bold" fill="#1A3A5C">
    案件关键时间轴
  </text>
  <line x1="40" y1="40" x2="1360" y2="40" stroke="#CFD8DC" stroke-width="1"/>

  <!-- 时间轴主线 -->
  <line x1="60" y1="210" x2="1340" y2="210" stroke="#546E7A" stroke-width="2"/>
  <!-- 左端箭头 -->
  <polygon points="60,205 50,210 60,215" fill="#546E7A"/>
  <!-- 右端箭头 -->
  <polygon points="1340,205 1350,210 1340,215" fill="#546E7A"/>

  <!-- ===== 时间节点（上下交替）===== -->

  <!-- 节点1：2008.06 借款合同（上方）-->
  <line x1="120" y1="210" x2="120" y2="130" stroke="#1A3A5C" stroke-width="1.5"/>
  <circle cx="120" cy="210" r="7" fill="#1A3A5C"/>
  <rect x="60" y="90" width="120" height="40" rx="4" fill="#EBF3FA" stroke="#1A3A5C" stroke-width="1"/>
  <text x="120" y="108" text-anchor="middle" font-size="11" font-weight="bold" fill="#1A3A5C">4800万借款</text>
  <text x="120" y="122" text-anchor="middle" font-size="10" fill="#546E7A">2008.06</text>

  <!-- 节点2：2009.06 借款合同（下方）-->
  <line x1="220" y1="210" x2="220" y2="290" stroke="#1A3A5C" stroke-width="1.5"/>
  <circle cx="220" cy="210" r="7" fill="#1A3A5C"/>
  <rect x="160" y="290" width="120" height="40" rx="4" fill="#EBF3FA" stroke="#1A3A5C" stroke-width="1"/>
  <text x="220" y="308" text-anchor="middle" font-size="11" font-weight="bold" fill="#1A3A5C">4000万借款</text>
  <text x="220" y="322" text-anchor="middle" font-size="10" fill="#546E7A">2009.06</text>

  <!-- 节点3：2012.09 信托借款（上方）-->
  <line x1="340" y1="210" x2="340" y2="130" stroke="#1A3A5C" stroke-width="1.5"/>
  <circle cx="340" cy="210" r="7" fill="#1A3A5C"/>
  <rect x="280" y="90" width="120" height="40" rx="4" fill="#EBF3FA" stroke="#1A3A5C" stroke-width="1"/>
  <text x="340" y="108" text-anchor="middle" font-size="11" font-weight="bold" fill="#1A3A5C">信托4900万</text>
  <text x="340" y="122" text-anchor="middle" font-size="10" fill="#546E7A">2012.09</text>

  <!-- 节点4：2015.11.20 家健实业成立（下方，异常）-->
  <line x1="480" y1="210" x2="480" y2="310" stroke="#FF5722" stroke-width="2"/>
  <circle cx="480" cy="210" r="9" fill="#FF5722"/>
  <rect x="410" y="310" width="140" height="52" rx="4" fill="#FBE9E7" stroke="#FF5722" stroke-width="1.5"/>
  <text x="480" y="328" text-anchor="middle" font-size="10" font-weight="bold" fill="#FF5722">⚠ 家健实业成立</text>
  <text x="480" y="342" text-anchor="middle" font-size="10" fill="#333">距逾期仅4天</text>
  <text x="480" y="356" text-anchor="middle" font-size="10" fill="#546E7A">2015.11.20</text>

  <!-- 节点5：2015.11.24 债务逾期（上方，违约）-->
  <line x1="560" y1="210" x2="560" y2="110" stroke="#E05A47" stroke-width="2"/>
  <circle cx="560" cy="210" r="9" fill="#E05A47"/>
  <rect x="495" y="70" width="130" height="42" rx="4" fill="#FFEBEE" stroke="#E05A47" stroke-width="1.5"/>
  <text x="560" y="88" text-anchor="middle" font-size="11" font-weight="bold" fill="#E05A47">债务逾期</text>
  <text x="560" y="103" text-anchor="middle" font-size="10" fill="#546E7A">2015.11.24</text>

  <!-- 节点6：2015.12.25 华琏包装股权转让（下方，异常）-->
  <line x1="650" y1="210" x2="650" y2="310" stroke="#FF5722" stroke-width="2"/>
  <circle cx="650" cy="210" r="9" fill="#FF5722"/>
  <rect x="580" y="310" width="140" height="52" rx="4" fill="#FBE9E7" stroke="#FF5722" stroke-width="1.5"/>
  <text x="650" y="328" text-anchor="middle" font-size="10" font-weight="bold" fill="#FF5722">⚠ 华琏包装股权转让</text>
  <text x="650" y="342" text-anchor="middle" font-size="10" fill="#333">陈永霖→潘智新</text>
  <text x="650" y="356" text-anchor="middle" font-size="10" fill="#546E7A">2015.12.25</text>

  <!-- 节点7：2016.01 立案（上方）-->
  <line x1="750" y1="210" x2="750" y2="130" stroke="#546E7A" stroke-width="1.5"/>
  <circle cx="750" cy="210" r="7" fill="#546E7A"/>
  <rect x="690" y="90" width="120" height="40" rx="4" fill="#ECEFF1" stroke="#546E7A" stroke-width="1"/>
  <text x="750" y="108" text-anchor="middle" font-size="11" font-weight="bold" fill="#546E7A">系列案立案</text>
  <text x="750" y="122" text-anchor="middle" font-size="10" fill="#546E7A">2016.01</text>

  <!-- 节点8：2017.06 债权转让（下方）-->
  <line x1="840" y1="210" x2="840" y2="290" stroke="#2E7D32" stroke-width="1.5"/>
  <circle cx="840" cy="210" r="7" fill="#2E7D32"/>
  <rect x="780" y="290" width="120" height="40" rx="4" fill="#E8F5E9" stroke="#2E7D32" stroke-width="1"/>
  <text x="840" y="308" text-anchor="middle" font-size="11" font-weight="bold" fill="#2E7D32">债权转让信达</text>
  <text x="840" y="322" text-anchor="middle" font-size="10" fill="#546E7A">2017.06</text>

  <!-- 节点9：2019.06 新凯包装成立（上方，异常）-->
  <line x1="940" y1="210" x2="940" y2="110" stroke="#FF5722" stroke-width="2"/>
  <circle cx="940" cy="210" r="9" fill="#FF5722"/>
  <rect x="875" y="70" width="130" height="42" rx="4" fill="#FBE9E7" stroke="#FF5722" stroke-width="1.5"/>
  <text x="940" y="88" text-anchor="middle" font-size="10" font-weight="bold" fill="#FF5722">⚠ 新凯包装成立</text>
  <text x="940" y="103" text-anchor="middle" font-size="10" fill="#546E7A">2019.06（执行高峰）</text>

  <!-- 节点10：2021 拍卖分配（下方）-->
  <line x1="1040" y1="210" x2="1040" y2="290" stroke="#D4A017" stroke-width="1.5"/>
  <circle cx="1040" cy="210" r="7" fill="#D4A017"/>
  <rect x="975" y="290" width="130" height="40" rx="4" fill="#FFF8E1" stroke="#D4A017" stroke-width="1"/>
  <text x="1040" y="308" text-anchor="middle" font-size="11" font-weight="bold" fill="#D4A017">鞋材厂拍卖</text>
  <text x="1040" y="322" text-anchor="middle" font-size="10" fill="#546E7A">2021年</text>

  <!-- 节点11：2024 以物抵债（上方）-->
  <line x1="1160" y1="210" x2="1160" y2="110" stroke="#D4A017" stroke-width="2"/>
  <circle cx="1160" cy="210" r="9" fill="#D4A017"/>
  <rect x="1090" y="70" width="140" height="42" rx="4" fill="#FFF8E1" stroke="#D4A017" stroke-width="1.5"/>
  <text x="1160" y="88" text-anchor="middle" font-size="11" font-weight="bold" fill="#D4A017">以物抵债1.52亿</text>
  <text x="1160" y="103" text-anchor="middle" font-size="10" fill="#546E7A">2024年</text>

  <!-- 节点12：2024 恢复执行（下方）-->
  <line x1="1280" y1="210" x2="1280" y2="290" stroke="#E05A47" stroke-width="1.5"/>
  <circle cx="1280" cy="210" r="7" fill="#E05A47"/>
  <rect x="1215" y="290" width="130" height="40" rx="4" fill="#FFEBEE" stroke="#E05A47" stroke-width="1"/>
  <text x="1280" y="308" text-anchor="middle" font-size="11" font-weight="bold" fill="#E05A47">恢复执行</text>
  <text x="1280" y="322" text-anchor="middle" font-size="10" fill="#546E7A">2024.01</text>

  <!-- ===== 图例 ===== -->
  <rect x="40" y="370" width="600" height="36" rx="6" fill="#F5F7FA" stroke="#CFD8DC" stroke-width="1"/>
  <circle cx="60" cy="388" r="6" fill="#1A3A5C"/>
  <text x="72" y="392" font-size="10" fill="#333">借款/合同</text>
  <circle cx="140" cy="388" r="6" fill="#E05A47"/>
  <text x="152" y="392" font-size="10" fill="#333">违约/逾期</text>
  <circle cx="220" cy="388" r="6" fill="#2E7D32"/>
  <text x="232" y="392" font-size="10" fill="#333">债权转让</text>
  <circle cx="300" cy="388" r="6" fill="#D4A017"/>
  <text x="312" y="392" font-size="10" fill="#333">执行/拍卖</text>
  <circle cx="380" cy="388" r="8" fill="#FF5722"/>
  <text x="394" y="392" font-size="10" fill="#FF5722">⚠ 异常行为</text>
  <circle cx="480" cy="388" r="6" fill="#546E7A"/>
  <text x="492" y="392" font-size="10" fill="#333">判决/裁定</text>

</svg>
```

## 时间压缩规则

当时间跨度超过15年，且中间有超过3年无事件时，使用波浪线表示跳跃：

```xml
<!-- 波浪跳跃线示例 -->
<path d="M 500,210 Q 510,200 520,210 Q 530,220 540,210" 
      stroke="#546E7A" stroke-width="2" fill="none"/>
<text x="520" y="200" text-anchor="middle" font-size="9" fill="#546E7A">...</text>
```

## 节点间距计算

- 总可用宽度：1280px（60px到1340px）
- 节点数量N时，间距 = 1280 / (N+1)
- 建议最多展示15个节点，超出则筛选最重要的节点

# V2 债权转让链条图 — 详细设计规范

## 适用场景

当报告中存在以下内容时生成本图：
- 债权链条描述（原债权人→中间受让人→现债权人）
- 借款关系表格
- 担保结构描述
- 多层担保结构

## 数据提取规则

| 字段 | 来源 | 示例 |
|------|------|------|
| 债权转让路径 | 当事人关系图"债权链条"部分 | 中国银行→信达→广州资产→佛山瓴岸 |
| 转让时间 | 案件时间轴 | 2017年转让 |
| 借款金额 | 核心法律关系表格 | 4800万元 |
| 担保方式 | 核心法律关系表格 | 最高额保证8800万元 |
| 受偿情况 | 资产状况描述 | 已以物抵债1.52亿 |

## SVG完整实现模板

```xml
<svg width="1100" height="700" xmlns="http://www.w3.org/2000/svg"
     font-family="'PingFang SC','Microsoft YaHei','Noto Sans SC',sans-serif">

  <rect width="1100" height="700" fill="#FFFFFF"/>

  <!-- 标题 -->
  <text x="550" y="32" text-anchor="middle" font-size="18" font-weight="bold" fill="#1A3A5C">
    债权转让链条与担保结构图
  </text>
  <line x1="40" y1="48" x2="1060" y2="48" stroke="#CFD8DC" stroke-width="1"/>

  <!-- 箭头定义 -->
  <defs>
    <marker id="arr-blue" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#1A3A5C"/>
    </marker>
    <marker id="arr-green" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#2E7D32"/>
    </marker>
    <marker id="arr-orange" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#D4A017"/>
    </marker>
    <marker id="arr-red" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#E05A47"/>
    </marker>
  </defs>

  <!-- ===== 左轨：债权转让链条 ===== -->
  <rect x="20" y="60" width="200" height="580" rx="8" fill="#F0F4F8" stroke="#CFD8DC" stroke-width="1"/>
  <text x="120" y="82" text-anchor="middle" font-size="12" font-weight="bold" fill="#1A3A5C">债权转让链条</text>

  <!-- 中国银行（原债权人）-->
  <rect x="35" y="95" width="170" height="55" rx="6" fill="#FFFFFF" stroke="#546E7A" stroke-width="1.5"/>
  <text x="120" y="116" text-anchor="middle" font-size="12" fill="#333">中国银行东莞分行</text>
  <text x="120" y="132" text-anchor="middle" font-size="10" fill="#546E7A">原债权人</text>
  <text x="120" y="144" text-anchor="middle" font-size="9" fill="#546E7A">2008-2015年发放借款</text>

  <!-- 转让箭头 -->
  <line x1="120" y1="150" x2="120" y2="172" stroke="#2E7D32" stroke-width="1.5" marker-end="url(#arr-green)"/>
  <rect x="75" y="155" width="90" height="16" rx="3" fill="#E8F5E9"/>
  <text x="120" y="167" text-anchor="middle" font-size="9" fill="#2E7D32">转让 2017年</text>

  <!-- 中国信达 -->
  <rect x="35" y="174" width="170" height="50" rx="6" fill="#FFFFFF" stroke="#546E7A" stroke-width="1"/>
  <text x="120" y="194" text-anchor="middle" font-size="12" fill="#333">中国信达广东分公司</text>
  <text x="120" y="210" text-anchor="middle" font-size="10" fill="#546E7A">第一受让人</text>

  <line x1="120" y1="224" x2="120" y2="246" stroke="#2E7D32" stroke-width="1.5" marker-end="url(#arr-green)"/>
  <rect x="75" y="229" width="90" height="16" rx="3" fill="#E8F5E9"/>
  <text x="120" y="241" text-anchor="middle" font-size="9" fill="#2E7D32">转让 2018年</text>

  <!-- 广州资产 -->
  <rect x="35" y="248" width="170" height="50" rx="6" fill="#FFFFFF" stroke="#546E7A" stroke-width="1"/>
  <text x="120" y="268" text-anchor="middle" font-size="12" fill="#333">广州资产管理有限公司</text>
  <text x="120" y="284" text-anchor="middle" font-size="10" fill="#546E7A">第二受让人</text>

  <line x1="120" y1="298" x2="120" y2="320" stroke="#2E7D32" stroke-width="1.5" marker-end="url(#arr-green)"/>
  <rect x="75" y="303" width="90" height="16" rx="3" fill="#E8F5E9"/>
  <text x="120" y="315" text-anchor="middle" font-size="9" fill="#2E7D32">转让 2024年</text>

  <!-- 佛山瓴岸（现债权人）-->
  <rect x="35" y="322" width="170" height="55" rx="6" fill="#E8F5E9" stroke="#2E7D32" stroke-width="2"/>
  <text x="120" y="344" text-anchor="middle" font-size="12" font-weight="bold" fill="#2E7D32">佛山市瓴岸</text>
  <text x="120" y="360" text-anchor="middle" font-size="10" fill="#2E7D32">现申请执行人</text>
  <text x="120" y="373" text-anchor="middle" font-size="9" fill="#546E7A">（2024）粤1971执恢66号</text>

  <!-- 并行债权人：东莞信托 -->
  <rect x="35" y="420" width="170" height="55" rx="6" fill="#FFFFFF" stroke="#D4A017" stroke-width="1.5"/>
  <text x="120" y="440" text-anchor="middle" font-size="12" fill="#D4A017">东莞信托有限公司</text>
  <text x="120" y="456" text-anchor="middle" font-size="10" fill="#546E7A">并行债权人</text>
  <text x="120" y="469" text-anchor="middle" font-size="9" fill="#546E7A">4900万元调解书</text>

  <!-- 国厚资产 -->
  <rect x="35" y="500" width="170" height="55" rx="6" fill="#FFFFFF" stroke="#D4A017" stroke-width="1.5"/>
  <text x="120" y="520" text-anchor="middle" font-size="12" fill="#D4A017">国厚资产管理</text>
  <text x="120" y="536" text-anchor="middle" font-size="10" fill="#546E7A">并行债权人</text>
  <text x="120" y="549" text-anchor="middle" font-size="9" fill="#546E7A">受让平安银行债权</text>

  <!-- ===== 右侧：借款与担保结构 ===== -->
  <!-- 分区标题 -->
  <text x="650" y="82" text-anchor="middle" font-size="12" font-weight="bold" fill="#1A3A5C">借款与担保结构</text>

  <!-- 主债务人：成隆实业 -->
  <rect x="490" y="95" width="200" height="65" rx="8" fill="#1A3A5C" stroke="#1A3A5C" stroke-width="2"/>
  <text x="590" y="120" text-anchor="middle" font-size="13" font-weight="bold" fill="#FFFFFF">成隆实业公司</text>
  <text x="590" y="138" text-anchor="middle" font-size="11" fill="#A0C4E8">主债务人</text>
  <text x="590" y="153" text-anchor="middle" font-size="10" fill="#A0C4E8">借款合计约1.05亿元</text>

  <!-- 借款金额标签 -->
  <rect x="720" y="100" width="120" height="22" rx="4" fill="#DBEAFE"/>
  <text x="780" y="115" text-anchor="middle" font-size="10" fill="#1A3A5C">借款 4800万（2008）</text>
  <rect x="720" y="128" width="120" height="22" rx="4" fill="#DBEAFE"/>
  <text x="780" y="143" text-anchor="middle" font-size="10" fill="#1A3A5C">借款 4000万（2009）</text>

  <!-- 成隆包装（借款人）-->
  <rect x="360" y="230" width="160" height="55" rx="6" fill="#FFFFFF" stroke="#E05A47" stroke-width="2"/>
  <text x="440" y="252" text-anchor="middle" font-size="12" font-weight="bold" fill="#E05A47">成隆包装</text>
  <text x="440" y="268" text-anchor="middle" font-size="10" fill="#546E7A">借款人·保证人</text>
  <text x="440" y="280" text-anchor="middle" font-size="9" fill="#546E7A">借款4500万</text>

  <!-- 世纪豪庭（借款人）-->
  <rect x="540" y="230" width="160" height="55" rx="6" fill="#FFFFFF" stroke="#E05A47" stroke-width="2"/>
  <text x="620" y="252" text-anchor="middle" font-size="12" font-weight="bold" fill="#E05A47">世纪豪庭酒店</text>
  <text x="620" y="268" text-anchor="middle" font-size="10" fill="#546E7A">借款人·保证人</text>
  <text x="620" y="280" text-anchor="middle" font-size="9" fill="#546E7A">借款4900万（信托）</text>

  <!-- 华琏包装（保证人）-->
  <rect x="720" y="230" width="160" height="55" rx="6" fill="#FFFFFF" stroke="#E05A47" stroke-width="2"/>
  <text x="800" y="252" text-anchor="middle" font-size="12" font-weight="bold" fill="#E05A47">华琏包装</text>
  <text x="800" y="268" text-anchor="middle" font-size="10" fill="#546E7A">最高额保证人</text>
  <text x="800" y="280" text-anchor="middle" font-size="9" fill="#546E7A">保证8800万</text>

  <!-- 成隆鞋材厂（抵押+保证）-->
  <polygon points="590,340 630,370 590,400 550,370" fill="#FFFFFF" stroke="#E05A47" stroke-width="2"/>
  <text x="590" y="367" text-anchor="middle" font-size="11" font-weight="bold" fill="#E05A47">成隆鞋材厂</text>
  <text x="590" y="382" text-anchor="middle" font-size="9" fill="#546E7A">抵押+保证</text>

  <!-- 潘志成（个人保证）-->
  <circle cx="440" cy="450" r="35" fill="#FFFFFF" stroke="#E05A47" stroke-width="2"/>
  <text x="440" y="446" text-anchor="middle" font-size="12" font-weight="bold" fill="#E05A47">潘志成</text>
  <text x="440" y="462" text-anchor="middle" font-size="10" fill="#546E7A">个人连带保证</text>

  <!-- 潘智新（个人保证）-->
  <circle cx="760" cy="450" r="35" fill="#FFFFFF" stroke="#E05A47" stroke-width="2"/>
  <text x="760" y="446" text-anchor="middle" font-size="12" font-weight="bold" fill="#E05A47">潘智新</text>
  <text x="760" y="462" text-anchor="middle" font-size="10" fill="#546E7A">个人连带保证</text>

  <!-- 连线：主债务人→各借款人/保证人 -->
  <line x1="540" y1="160" x2="440" y2="230" stroke="#1A3A5C" stroke-width="1.5" marker-end="url(#arr-blue)"/>
  <line x1="590" y1="160" x2="620" y2="230" stroke="#1A3A5C" stroke-width="1.5" marker-end="url(#arr-blue)"/>
  <line x1="640" y1="155" x2="800" y2="230" stroke="#1A3A5C" stroke-width="1.5" stroke-dasharray="5,3" marker-end="url(#arr-orange)"/>
  <text x="730" y="190" font-size="9" fill="#D4A017">保证</text>

  <!-- 连线：→成隆鞋材厂 -->
  <line x1="590" y1="160" x2="590" y2="340" stroke="#1A3A5C" stroke-width="1.5" stroke-dasharray="5,3" marker-end="url(#arr-orange)"/>
  <text x="598" y="255" font-size="9" fill="#D4A017">抵押</text>

  <!-- 连线：→个人保证 -->
  <line x1="490" y1="160" x2="440" y2="415" stroke="#546E7A" stroke-width="1" stroke-dasharray="4,3" marker-end="url(#arr-blue)"/>
  <line x1="690" y1="160" x2="760" y2="415" stroke="#546E7A" stroke-width="1" stroke-dasharray="4,3" marker-end="url(#arr-blue)"/>

  <!-- ===== 受偿情况区（底部）===== -->
  <rect x="240" y="540" width="820" height="130" rx="8" fill="#F5F7FA" stroke="#CFD8DC" stroke-width="1"/>
  <text x="650" y="562" text-anchor="middle" font-size="12" font-weight="bold" fill="#1A3A5C">受偿情况</text>

  <!-- 已受偿 -->
  <rect x="260" y="572" width="220" height="80" rx="6" fill="#E8F5E9" stroke="#2E7D32" stroke-width="1.5"/>
  <text x="370" y="592" text-anchor="middle" font-size="11" font-weight="bold" fill="#2E7D32">已以物抵债</text>
  <text x="370" y="610" text-anchor="middle" font-size="13" font-weight="bold" fill="#2E7D32">1.52亿元</text>
  <text x="370" y="628" text-anchor="middle" font-size="10" fill="#546E7A">成隆实业土地+酒店大楼</text>
  <text x="370" y="643" text-anchor="middle" font-size="9" fill="#546E7A">2024年裁定</text>

  <!-- 剩余债权 -->
  <rect x="510" y="572" width="220" height="80" rx="6" fill="#FFEBEE" stroke="#E05A47" stroke-width="1.5"/>
  <text x="620" y="592" text-anchor="middle" font-size="11" font-weight="bold" fill="#E05A47">剩余未清偿</text>
  <text x="620" y="610" text-anchor="middle" font-size="13" font-weight="bold" fill="#E05A47">待核实</text>
  <text x="620" y="628" text-anchor="middle" font-size="10" fill="#546E7A">终本后恢复执行阶段</text>
  <text x="620" y="643" text-anchor="middle" font-size="9" fill="#546E7A">（2024）粤1971执恢66号之二</text>

  <!-- 东莞信托受偿 -->
  <rect x="760" y="572" width="220" height="80" rx="6" fill="#FFF8E1" stroke="#D4A017" stroke-width="1.5"/>
  <text x="870" y="592" text-anchor="middle" font-size="11" font-weight="bold" fill="#D4A017">东莞信托实际受偿</text>
  <text x="870" y="610" text-anchor="middle" font-size="13" font-weight="bold" fill="#D4A017">0元</text>
  <text x="870" y="628" text-anchor="middle" font-size="10" fill="#546E7A">第二顺位抵押权人</text>
  <text x="870" y="643" text-anchor="middle" font-size="9" fill="#546E7A">鞋材厂拍卖后无剩余</text>

</svg>
```

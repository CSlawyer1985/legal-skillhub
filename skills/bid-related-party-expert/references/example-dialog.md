# 示例对话：可直接粘贴的端到端用例（工商信息版）

本文件给一个**完整、可复制**的端到端示例，覆盖「多主体工商关联」高风险场景（对应 test-cases.md 的 TC7）。
用途：① 初次上手时直接复制到 WorkBuddy 验证 skill 是否被正确触发；② 作为回归测试固定样本。

> **版本说明**：本示例严格限定在**工商登记信息边界**内（A1-D4 维度），不包含投标行为痕迹分析（第39/40条）。
> 与 SKILL.md 主规则第三节边界声明、第六节四维框架、第八节输出格式完全一致。

## 一、用户侧输入（直接粘贴到对话即可）

> 触发方式：把下面整段发到对话。只要包含多个 `<bidder>` 与「关联关系」语义，skill 会自动加载。
> 若未自动触发，可在开头加一句：「请用投标企业关联关系识别专家分析以下主体：」

```xml
请识别以下三家投标单位之间的关联关系：

<bidders>
  <bidder id="1">
    <name>甲建设工程有限公司</name>
    <legal_representative>张三</legal_representative>
    <shareholders>张三 60%；李四 40%</shareholders>
    <key_personnel>董事长：张三；项目经理：王五</key_personnel>
    <reg_address>XX市YY区科技路100号A座10层</reg_address>
    <contact>电话 13800001111；邮箱 jia@xx.com</contact>
    <bid_section>标段A</bid_section>
    <extra>无</extra>
  </bidder>
  <bidder id="2">
    <name>乙市政工程有限公司</name>
    <legal_representative>李四</legal_representative>
    <shareholders>甲建设工程有限公司 100%（甲全资控股乙）</shareholders>
    <key_personnel>董事长：李四；项目经理：王五</key_personnel>
    <reg_address>XX市YY区科技路100号A座10层</reg_address>
    <contact>电话 13800002222；邮箱 yi@xx.com</contact>
    <bid_section>标段A</bid_section>
    <extra>无</extra>
  </bidder>
  <bidder id="3">
    <name>丙建筑工程有限公司</name>
    <legal_representative>王七</legal_representative>
    <shareholders>王七 70%；孙八 30%</shareholders>
    <key_personnel>董事长：王七；项目经理：周九</key_personnel>
    <reg_address>XX市YY区科技路100号A座10层</reg_address>
    <contact>电话 13800003333；邮箱 bing@xx.com</contact>
    <bid_section>标段A</bid_section>
    <extra>无</extra>
  </bidder>
</bidders>
<bidders_context>某市政道路工程标段A公开招标，三家单位同时投标，未划分其他标段。</bidders_context>
```

## 二、期望输出报告（模型应按此结构与口径生成）

> **与旧版示例的关键差异**：
> - 输入移除了 `bid_agent` / `price` / `deposit_account` / `file_traces` 等非工商字段
> - 输出不再出现 E 维度（投标行为）、第39/40条法条引用、「视为串通·可反证」结论
> - `consequence` 严格使用枚举值：`投标无效` | `需核查` | `一般关联/无关联`
> - `network_analysis` 结论仅描述工商关联密度，不建议移交监督部门

```xml
<report>
  <summary>共比对 3 个主体（均投同一标段A），发现 4 处工商关联信号：高 1 处、中 3 处；并识别出多主体工商关联网络（高）。</summary>
  <findings>
    <finding>
      <pair>甲 — 乙</pair>
      <dimensions>B1</dimensions>
      <type>控股关系（甲 100% 控股乙）</type>
      <risk>高</risk>
      <evidence source="input">甲 shareholders=张三60%/李四40%；乙 shareholders=甲建设工程有限公司 100%</evidence>
      <legal_basis>《招标投标法实施条例》第34条第2款</legal_basis>
      <article_number>第34条第2款</article_number>
      <consequence>投标无效</consequence>
      <confidence>高</confidence>
      <reasoning>乙的全部股权由甲持有，甲对乙形成绝对控股，二者参加同一标段A投标，触发法定禁止。</reasoning>
    </finding>
    <finding>
      <pair>甲 — 乙</pair>
      <dimensions>C1</dimensions>
      <type>董监高重合（项目经理均为王五）</type>
      <risk>中</risk>
      <evidence source="input">甲 key_personnel=项目经理王五；乙 key_personnel=项目经理王五</evidence>
      <legal_basis>《招标投标法实施条例》第34条精神（高度可疑信号）</legal_basis>
      <article_number>第34条（高度可疑）</article_number>
      <consequence>需核查</consequence>
      <confidence>高</confidence>
      <reasoning>两公司工商登记的主要人员存在重合（项目经理同为王五），属高度可疑的人事关联信号，需进一步核查其社保缴纳单位与实际履职情况以排除挂靠可能。</reasoning>
    </finding>
    <finding>
      <pair>甲 — 乙 — 丙</pair>
      <dimensions>D1</dimensions>
      <type>注册/经营地址相同</type>
      <risk>中</risk>
      <evidence source="input">甲/乙/丙 reg_address=XX市YY区科技路100号A座10层</evidence>
      <legal_basis>《招标投标法实施条例》第34条精神（高度可疑信号）</legal_basis>
      <article_number>第34条（高度可疑）</article_number>
      <consequence>需核查</consequence>
      <confidence>中</confidence>
      <reasoning>三家公司注册地址完全一致，属高度可疑的经营痕迹重合。可能为同一孵化器/众创空间或集团办公区共用地址，需核实房屋产权与租赁关系。</reasoning>
    </finding>
    <finding>
      <pair>甲 — 乙 — 丙</pair>
      <dimensions>C1</dimensions>
      <type>核心人员疑似关联（需进一步佐证）</type>
      <risk>低</risk>
      <evidence source="input">三家公司的 key_personnel 分别为(张三/王五)、(李四/王五)、(王七/周九)，仅甲乙共享王五</evidence>
      <legal_basis>《招标投标法实施条例》第34条精神</legal_basis>
      <article_number>第34条（一般关联）</article_number>
      <consequence>一般关联/无关联</consequence>
      <confidence>低</confidence>
      <reasoning>除甲乙共享项目经理外，丙的人员与其他两家无交叉。整体人员关联度有限，但结合地址相同等其他信号叠加后需综合判断。</reasoning>
    </finding>
  </findings>
  <network_analysis>
    关联网络：甲 100% 控股乙（B1）；甲/乙/丙 三者注册地址相同（D1）；甲乙共享项目经理王五（C1）。
    结构判定：以「甲（控股方）」为中心的星型关联，三主体形成工商信息层面的密集关联网络。
    结论：多主体工商关联网络（围标风险提示），risk=高。注意：此结论仅基于工商登记信息密度，不等同于串标行为认定（串标属第39/40条，不在本技能范围）。
  </network_analysis>
  <data_gaps>建议补充：① 甲/乙/丙 近6个月股权变更记录（防范临时脱壳）；② 王五在甲/乙两家的社保缴纳记录（确认是否为真实双重任职）；③ 三家公司实际经营地址是否独立（排除虚拟注册地址集中）；④ 乙的大股东向上穿透（确认最终受益人）。</data_gaps>
  <recommendation>甲、乙因控股关系构成法定禁止投标（第34条第2款），应判定为投标无效；甲/乙/丙 在工商层面存在多项关联信号（同址+人员重合），建议评标委员会重点核查。如需进一步分析投标行为痕迹（报价规律、文件属性、IP/MAC 等），请使用专门的串标行为分析工具。本结论仅作评审参考，法定认定权在评标委员会/监管机关。</recommendation>
</report>
```

## 三、验收要点

- **必须命中**：甲—乙「高/投标无效」（第一级·B1控股）、其余为中/低（第二级·高度可疑或一般关联）。
- **必须输出 `<network_analysis>` 并给出「多主体工商关联网络（围标风险提示）」。
- **不得出现**：E 维度、第39/40条法条引用、「视为串通」「可反证」「移交监督部门」等串标行为相关表述。
- 每条 `evidence` 必须能在输入原文中找到对应字段；不得编造未提供的股权或人员。
- `data_gaps` 必须列出可补充核验项，不臆测结论。
- `consequence` 严格为枚举值之一：`投标无效` / `需核查` / `一般关联/无关联`。

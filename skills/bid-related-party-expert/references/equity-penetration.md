# 工具调用 + 提示链：真实股权穿透工程版

SKILL.md 第十二/十三节预留了工具接口，但模型本身不实时查工商库，股权穿透深度受限于用户喂入的数据。
本文件给出**生产级落地架构**：用「提示链（Prompt Chaining）+ 工具调用（Function Calling）」把外部工商数据
接入主分析链，使模型能完成多层股权穿透与实控人识别，而不靠臆测。

## 一、架构总览（四节点提示链）

```
[节点1] 数据解析      主 skill 接收 <bidders>，提取已知字段，标记 data_gaps
        ↓
[节点2] 缺口检测      判断是否需要工商数据（缺股东/持股/实控人/历史变更）
        ↓
[节点3] 工具调用链    依次调用 query_enterprise_credit / query_penetration / query_judicial
        ↓  （穿透直到最终受益人，设最大深度，结果回填 <bidders>）
[节点4] 主分析链      用补全后的数据重新跑 思维链步骤 2–8，产出 <report>
        ↓
[可选]  IMA 复核      争议点调用 ima-mcp 检索法条/类案（见 ima-kb.md）
```

## 二、工具协议（JSON Schema 草案）

运行时需实现以下函数的实际后端（对接国家企业信用信息公示系统 / 企查查 / 天眼查 API）：

```json
{
  "query_enterprise_credit": {
    "description": "查询企业工商登记与基础股权",
    "parameters": {
      "type": "object",
      "properties": {
        "company_name": {"type": "string"}
      },
      "required": ["company_name"]
    },
    "returns": {
      "name": "string",
      "legal_representative": "string",
      "shareholders": [{"name": "string", "ratio": "number"}],
      "key_personnel": ["string"],
      "reg_address": "string",
      "contact": "string",
      "established": "string",
      "status": "string"
    }
  },
  "query_penetration": {
    "description": "股权穿透至最终受益人/实控人，支持递归",
    "parameters": {
      "type": "object",
      "properties": {
        "company_name": {"type": "string"},
        "max_depth": {"type": "integer", "default": 5}
      },
      "required": ["company_name"]
    },
    "returns": {
      "ultimate_beneficiary": ["string"],
      "control_chain": [{"from": "string", "to": "string", "ratio": "number", "layer": "integer"}],
      "cross_holding": "boolean"
    }
  },
  "query_judicial": {
    "description": "查询自然人/企业的裁判文书与失信记录",
    "parameters": {
      "type": "object",
      "properties": {"person_name": {"type": "string"}},
      "required": ["person_name"]
    },
    "returns": {
      "cases": [{"title": "string", "role": "string", "date": "string"}],
      "dishonest": "boolean"
    }
  }
}
```

## 三、提示链控制逻辑（写入运行时编排，而非模型提示）

1. **触发工具调用**：仅当 `<data_gaps>` 命中「缺股东/持股/实控人/历史变更」时调用；已知字段不重复查。
2. **穿透递归**：`query_penetration` 返回 `control_chain`，若末层仍为法人（非自然人），继续下钻直至自然人或达 `max_depth`。
3. **回填规则**：工具结果写入对应 `<bidder>` 字段，并在 `evidence` 标注 `source="external_api"`；同一实控人命中多个主体 → 触发 A2/A3 维度比对。
4. **空结果处理**：工具返回空/超时 → 该字段进 `data_gaps`，**严禁推断**；不因此提升或降低 risk。
5. **循环防护**：每个 company 只穿透一次；`cross_holding=true` 时额外输出提示（交叉持股需人工判定控制权）。
6. **成本与时限**：批量场景（N 大）建议先两两粗筛再按需穿透，控制 API 调用次数；设单次分析超时上限。

## 四、与主 skill 的衔接写法

在 SKILL.md 第十二节「外部工商数据工具（可选）」中追加运行时约定：

> 当本环境支持 Function Calling 时，按 references/equity-penetration.md 的提示链执行：
> 先解析并检测 data_gaps，再调用 query_enterprise_credit / query_penetration 补全股权与实控人，
> 将结果回填 <bidders> 后重跑主分析链。工具返回须标注 source="external_api"；
> 返回为空或失败时记入 data_gaps，不得臆测。

## 五、注意事项（工程红线）

- 工具后端必须返回**结构化、可核验**数据；禁止把搜索网页摘要当权威股权结果。
- 股权穿透涉及隐私与数据合规，调用需获得授权并遵守《个人信息保护法》等相关规定。
- 模型结论仍仅作评审参考；工具数据错误不转移法定认定责任。
- 若环境不支持 Function Calling，跳过本文件，仅依赖用户喂入数据，并在 data_gaps 明确说明「需外部工商数据核验」。

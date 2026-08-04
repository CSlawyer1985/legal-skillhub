# 输出模式

每次裁决产生一条记录，以两种视图呈现，均由同一底层状态生成。每次裁决都必须产出两种视图，无论结果如何（真命中 TP、误报 FP 或升级）。

## JSON 结构

```json
{
  "record_id": "uuid-or-stable-identifier",
  "skill_version": "1.0.0",
  "timestamp_utc": "ISO-8601 timestamp",
  "mode": "interactive | batch",

  "alert_input": {
    "screened_name": "string as provided",
    "screened_party_type": "individual | entity | vessel | aircraft | unknown",
    "screened_party_type_source": "provided | user_confirmed | inferred | unknown",
    "matched_name": "string as provided (the listed party's primary name)",
    "list_name": "string (e.g., 'OFAC SDN List')",
    "list_version_or_snapshot": "string or null",
    "upstream_match_score": "number or null",
    "secondary_identifiers_provided": {
      "dob": "string or null",
      "pob": "string or null",
      "nationality": "string or null",
      "id_numbers": [],
      "addresses": [],
      "other": {}
    }
  },

  "tier_0_parse": {
    "screened_name_parse": {
      "script": "Latin | Cyrillic | Arabic | Han | Hangul | Hebrew | Thai | Greek | Devanagari | mixed | other",
      "language_hint": "ISO language code or descriptor",
      "naming_convention": "Hispanic | Portuguese | Arabic | Persian | Russian | East_Asian | Japanese | Indonesian_Burmese | Western_default | ambiguous",
      "components": {
        "anchor": ["list of anchor strings"],
        "non_anchor": ["list of non-anchor strings"]
      },
      "parse_confidence": "high | low"
    },
    "matched_name_parse": {
      "...same shape as screened_name_parse..."
    },
    "listed_party_type": "individual | entity | vessel | aircraft | unknown",
    "listed_aliases_parsed": [
      { "alias": "string", "parse": { "...same shape..." } }
    ],
    "identifiers_on_listed_entry": {
      "dob": [],
      "pob": [],
      "nationality": [],
      "passport": [],
      "national_id": [],
      "tax_id": [],
      "registration_number": [],
      "imo_number": null,
      "address": [],
      "other": {}
    },
    "identifiers_on_screened_party": {
      "...same shape..."
    }
  },

  "tier_1_evaluation": {
    "rules_evaluated": [
      {
        "rule_id": "FP-1",
        "preconditions_met": true,
        "outcome": "fired | not_applicable | did_not_fire",
        "evidence": {
          "listed_type": "...",
          "screened_type": "...",
          "screened_type_source": "...",
          "cross_reference_check": "performed | n/a",
          "cross_reference_result": "no_eponymous_entry_found | found_at_uri"
        }
      },
      {
        "rule_id": "FP-2",
        "preconditions_met": "true | false (with reason)",
        "outcome": "...",
        "evidence": {
          "screened_anchor": [],
          "screened_non_anchor": [],
          "listed_anchor": [],
          "listed_non_anchor": [],
          "matched_components": [],
          "unmatched_anchor_components": [],
          "convention": "...",
          "alias_check_result": "no_alias_match | alias_matched: '...'"
        }
      },
      {
        "rule_id": "FP-3",
        "preconditions_met": "...",
        "outcome": "...",
        "evidence": {
          "screened_dob": "...",
          "listed_dobs_checked": [],
          "deltas": [],
          "day_month_carve_out_checked": true,
          "day_month_match": "true | false"
        }
      }
    ]
  },

  "tier_2_evaluation": {
    "rules_evaluated": [
      {
        "rule_id": "TP-1 | TP-2 | Escalate-2 | FP-5 | FP-6",
        "preconditions_met": "...",
        "outcome": "...",
        "evidence": {}
      }
    ],
    "soft_signals_logged": [
      {
        "signal": "gender_mismatch | geo_mismatch | partial_dob_mismatch | nationality_mismatch | occupation_mismatch",
        "detail": "string"
      }
    ]
  },

  "tier_3_evaluation": {
    "entered": "true | false",
    "gating_basis": "G-1 | G-2 | G-3 | not_entered_reason: '...'",
    "rungs_executed": [
      {
        "rung": "1 | 2 | 3 | 4",
        "queries": ["string"],
        "retrievals": [
          {
            "url": "string",
            "retrieval_timestamp_utc": "ISO-8601",
            "source_rank": "A | B | C | D",
            "extracted_passage": "string",
            "contributed_to_determination": "true | false"
          }
        ],
        "sufficient": "true | false",
        "insufficiency_reason": "string or null"
      }
    ],
    "retrieval_count": "integer",
    "retrieval_cap_reached": "true | false",
    "rules_evaluated": [
      {
        "rule_id": "TP-3 | FP-7",
        "preconditions_met": "...",
        "outcome": "...",
        "evidence": {
          "supporting_retrievals": ["url1", "url2"],
          "identifying_facts": ["string"],
          "contradictions": ["string"]
        }
      }
    ]
  },

  "determination": {
    "classification": "true_positive | false_positive | escalate",
    "firing_rule": "rule ID or null",
    "escalation_reason": "string or null",
    "gaps_for_human": ["string array — what additional info would have allowed determination"]
  },

  "narrative": "string — the human-readable narrative described below"
}
```

## 叙述结构

叙述是 JSON 记录 `narrative` 字段中的单个多段字符串。它使用固定顺序的固定章节，便于审查者一致扫读。使用 Markdown 标题（`## 章节名`）。

### 叙述的指导原则

叙述用于分析师理解裁决结论所需的内容。它不是技能考虑过的每条规则的记录。始终适用三项原则：

1. **在触发规则处停止。** 当某层的规则触发时，叙述记录该规则并停止。不要在触发规则后列出同层未触发的规则，也不要提及从未进入的层。JSON 记录为审计捕获一切；叙述是为人类读者准备的。

2. **硬规则触发时抑制软信号。** 如果案件被干净利落地处理（经规则触发为真命中或误报），软信号（性别提示、地理语境、国籍匹配、部分出生日期不匹配）不出现在叙述中。它们是从干净结论中分散注意力的噪音。软信号仅在案件升级时呈现——此时它们属于证据包，使分析师能看到。

3. **直接了当。** 不要在警报摘要中逐字复述警报输入——转述为重要内容。不要背诵规则规格（"先决条件满足：两个姓名均高置信度解析；均映射至同一惯例……"）——陈述相关事实和结论。不要对置信度发表评论（"可能""似乎是"）；规则要么触发要么没有。

### 必需章节

**## 警报摘要**

一两句。筛查了谁，对照哪条名单条目。如存在最具识别力的辅助标识符则包括之。跳过 null/空字段。

示例："筛查对象：'Maria Garcia Lopez'，个人。对照 OFAC SDN 名单上的'María Hernández García'（个人）。未提供辅助标识符。"

**## 姓名解析**

一段简短文字，涵盖双方。说明惯例、锚点成分和解析置信度。如任一方解析置信度低，说明并注明结构性不匹配误报规则已禁用。

示例："两个姓名均按西班牙语惯例高置信度解析。筛查锚点：'Garcia'（父姓）；母姓'Lopez'。名单锚点：'Hernández'（父姓）；母姓'García'。"

**## 第一层走查**

每条规则一行，**截至并包括触发规则**。如第一层无规则触发，列出全部三条并给出单句结论。如规则触发，走查在此停止——同层中未触发的早期规则如未触发显而易见，可从叙述中省略，或如对语境需要则简要注明。自行判断。

规则触发时，用一两句说明：满足了什么条件，附具体证据（实际锚点字符串、实际出生日期、实际类型）。不要背诵规则规格。

**## 第二层走查**（仅当第一层未触发）

与第一层相同的形式。同样的"在触发规则处停止"纪律。

**## 第三层走查**（仅当进入第三层）

用一句话说明门控依据（G-1、G-2 或 G-3）。然后按运行的每个阶梯：使用的查询（用所用语言）、检索到的内容（URL + 时间戳 + 来源等级，一行摘要）、该阶梯为何充分或不充分。说明 TP-3 或 FP-7 是否触发，并指明有贡献的检索。

**## 第三层门控**（仅当未进入第三层且案件升级）

当案件到达第三层边界且 G-1、G-2、G-3 均不成立时，用一段短文说明哪些标准失败及原因。这是叙述中唯一出现"不适用"门控推理的地方。

**## 裁决**

分类、触发规则（如有），以及一句引用具体事实的理由。对升级案件，添加 `gaps_for_human` 清单（本可使裁决成立的具体信息）和一行说明：技能不就真命中或误报提出建议——证据仅供人工评估。

### 叙述不包括的内容

- 触发规则之后的"未评估——第 X 层因 Y 规则触发而停止"行。
- 硬规则已触发时的软信号。
- 逐字段复述 JSON alert_input。
- 在可直接陈述相关事实时背诵规则先决条件。
- 置信度用语（"似乎是""可能""大概"）。规则要么触发要么没有。
- 对升级的建议。
- 对筛查系统质量、名单方行为的评论，或分析师除缺口清单之外应做的操作性事项。

## 输出机制

产出输出时：

1. 先构建 JSON 记录，在各层完成时填充字段。
2. 从已填充的 JSON 生成叙述。叙述是 JSON 的呈现，而非独立评论。
3. 将两者呈现给用户/系统。交互模式的默认呈现顺序：先叙述（人类更易扫读），再 JSON。批处理模式：如消费系统指定，仅 JSON 亦可接受。

## 输出中不应包含的内容

- 升级案件不提供趋向真命中或误报的建议。
- 裁决部分无概率或置信度分数。
- 无与规则驱动结论相矛盾或软化的叙述摘要。
- 不对分析师的可能结论、筛查系统的质量或名单方的行为发表评论。坚持身份裁决。

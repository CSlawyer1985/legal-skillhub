# Legal Diagram Patterns

## 1. Judgment Graphing

For long judgments, do not produce a single overloaded diagram. Use this default set:

1. **Case relationship diagram**
   - parties, procedural status, contracts, guarantee/security relationships
   - show who sues whom, who appeals, who guarantees, who bears liability

2. **Adjudication logic diagram**
   - issue one: court's reasoning path
   - issue two: court's reasoning path
   - conclusion: affirmed, reversed, remanded, modified, dismissed

3. **Amount and liability chart**
   - starting amount
   - payments
   - deductions
   - final amount
   - interest
   - attorney fees
   - guarantee/security responsibility
   - separate ancillary fees from liability bearers; use a responsibility hub if needed

Use draw.io by default. Use Excalidraw only when the user asks for hand-drawn article style.

## 2. Construction Chain Dispute

Use a three-layer layout only for simple chains. If guarantee/recourse lines create outer loops or crossings, split the diagram or add a risk hub.

- Top layer: contract and supervision relationships
- Middle layer: payment break or breach trigger
- Bottom layer: claims, work stoppage, recourse, guarantee enforcement

Common actors:

- owner
- general contractor
- subcontractor
- actual constructor
- material supplier
- supervisor
- guarantor/security provider

Common legal links:

- general contract
- subcontract
- illegal subcontract/transfer
- material purchase
- guarantee/security
- quality defense
- nonpayment
- direct claim
- work stoppage or wage claim

Long claim-back arrows must route around the outside of the canvas. If there are two or more long outer-loop arrows, split into:

1. **Contract and supervision chain**
2. **Payment break and claim chain**

Alternative: place a central "核心风险结构" hub at the bottom and connect claims to the hub instead of drawing multiple long recourse loops.

## 3. Litigation Strategy Map

Use when the user wants "诉讼战略地图" or case strategy visualization.

Recommended structure:

- Center: target dispute or main claim
- Left: claimant-side attack path
- Right: defense-side resistance path
- Bottom: evidence chain and weak points
- Top: litigation objective and risk warning

Use Excalidraw for whiteboard style; use draw.io for client report or court-facing presentation.

## 4. Contract Review Diagram

Default flow:

1. business submission
2. completeness check
3. risk priority
4. legal review
5. risk list
6. escalation if major risk
7. redline and opinion
8. business negotiation
9. final version
10. signing and archive

Use draw.io by default. Avoid crossing return lines; put return-to-revise loops on the outside.

## 5. Evidence Timeline

Use when the user provides judgments, pleadings, evidence lists, or factual chronology.

Classify events:

- blue: contract/signing/performance milestones
- yellow: negotiation/notice/common facts
- red: breach, default, disputed fact
- purple: litigation/arbitration/procedure
- green: judgment/result/payment completion

For dense timelines, produce:

- one summary timeline
- one event table
- one analysis page

Do not place more than 12 major nodes on one timeline.

## 6. Node Text Rules

Good node:

```text
总包方
华夏一局
分包幕墙工程：1.5亿
```

Bad node:

```text
华夏建设第一工程局为了加快项目进度，将玻璃幕墙工程以1.5亿元价格分包给深圳晶科幕墙有限公司，并在后续因业主拒付而停止支付分包款
```

Use short labels plus side annotations.

## 7. Connector Rules

- Put relationship labels near the middle of a connector, not on top of nodes.
- Give labels a white background when supported by the target format.
- Use dashed red lines for disputed or broken payment flows.
- Use purple lines for guarantees and security interests.
- Use gray dashed lines for supervision and background links.
- Avoid multiple parallel lines between the same two nodes unless the legal meaning differs clearly.
- In amount/liability charts, avoid drawing direct lines from the final amount node through interest, attorney fee, or litigation cost boxes. Use a separate "liability structure" hub below the fee layer.
- In relationship diagrams, do not connect every legal relationship directly if it creates crossings. Summarize secondary relationships in a hub or side note.

## 8. Article-Friendly Defaults

For WeChat/public article diagrams:

- prefer 1-3 focused diagrams
- use large Chinese text
- avoid more than 8 primary nodes in one diagram
- keep title and subtitle concise
- include one "读图要点" note when the legal relationship is complex

For knowledge-base or paid-community materials:

- keep editable source files
- include more precise legal labels
- consider producing both formal draw.io and hand-drawn Excalidraw versions

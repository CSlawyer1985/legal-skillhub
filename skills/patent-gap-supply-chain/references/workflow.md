# Detailed Workflow

## Step 1: Trigger lead identification

**Goal**: Define the analysis target and identify a potential patent gap.

**Operations**:
1. Confirm target A (full company name, ticker)
2. Identify A's product P and the key technology T it uses
   - If T is not specified by the user, extract core technologies from A's product docs, annual report, prospectus, research reports
3. Preliminarily judge whether A may lack T's patents
   - If A's product uses T but A's core business / R&D direction does not overlap with T, gap likelihood is high

**Output**: A, P, T triple + preliminary gap judgment

## Step 2: Patent gap confirmation

**Goal**: Confirm with data whether A truly lacks T-related patents, and rule out legitimate-use scenarios.

**Operations**:
1. Search A's patents using patent search tools (tushare patent API / PatSnap)
   - Dimensions: A's company name + technology T keywords + IPC class
   - Scope: CN patents + US patents + PCT (per A's market coverage)
   - Note: A may hold patents via subsidiaries / affiliates — search A's related entities
2. Determine gap:
   - A (incl. affiliates) has zero T-related patents → gap confirmed
   - A has T-related patents but count is significantly below industry average → partial gap
   - A has sufficient T-related patents → no gap, terminate
3. Rule out legitimate-use scenarios (if gap confirmed):
   - Cross-licensing: does A have a cross-licensing agreement with anyone? (check announcements / news)
   - Acquisition inheritance: did A acquire T usage rights via M&A?
   - Patent pool: does T belong to a pool (e.g., Avanci, MPEG-LA)?
   - Open-source: is there an open-source implementation of T?

**Output**: Gap determination (confirmed / partial / none) + excluded legitimate-use scenarios

## Step 3: Multi-lead parallel verification

**Goal**: Activate 5 leads in parallel, each with an independent confidence score. Detailed scoring rules in `checklists.md`.

### Lead 1 · Patent ownership (confidence: medium)
- Search technology T's patent holders, identify primary owner B
- Check B's patent status: granted / under examination / lapsed / transferred
- Timeline check: B's patent filing date vs A's product launch date (A's product must postdate B's filing)
- Note: B may be an NPE (non-practicing entity), licensing only

### Lead 2 · Corporate affiliation (confidence: high)
- Search A-B affiliation via Tianyancha / Qichacha
- Check: mutual investment, joint ventures, executive overlap, historical changes
- Strong tie (JV / investment) → high confidence; weak tie (executive overlap) → medium

### Lead 3 · Talent flow (confidence: medium)
- Search B→A technical-hire / job-change records
- Use WebSearch + job sites + LinkedIn-type sources
- Multiple B technical staff joining A → high likelihood of technology dependency

### Lead 4 · Procurement (confidence: high)
- Search A's tender announcements, supplier-day disclosures, annual-report supplier info
- Whether B is directly named, or B's product category is mentioned
- Directly names B → high confidence; category only → medium

### Lead 5 · Product teardown (confidence: very high)
- Search teardown reports / BOM analysis of A's product P
- Whether it physically contains B's components / chips
- Physical evidence → very high confidence (strongest evidence)

**Output**: Per-lead hit status + per-lead confidence

## Step 4: Multi-lead fusion + confidence scoring

**Goal**: Cross-validate and produce an overall determination.

**Fusion rules**:
- ≥2 high-confidence leads corroborating → overall "high", can conclude
- 1 high + 1 medium corroborating → overall "medium"
- Only 1 lead hit, no corroboration → overall "low", hypothesis only
- 0 leads hit → terminate, cannot infer

**Role determination**:
- Leads 4/5 hit (procurement / teardown) → B is A's direct supplier
- Only leads 1/2 hit (patent / corporate) → B may be technology licensor or indirect affiliation
- Lead 1 hit but B is NPE → B licenses only, not in supply chain

**Output**: Overall confidence + B's role determination

## Step 5: Alternative-hypothesis check

See the alternative-hypothesis checklist in `checklists.md`. Explicitly exclude alternative explanations for each inference; list unexcluded ones in the report.

## Step 6: Counter-intelligence check

See the counter-intelligence checklist in `checklists.md`. Check whether the subject uses counter-intelligence means to hide the real supply chain.

## Step 7: Output report

Organize the report per the I/O contract in SKILL.md. The report must include:
- Relationship determination (incl. B's role)
- Evidence chain (5-lead hit table + confidence)
- Overall confidence + rationale
- Alternative-hypothesis list (excluded / unexcluded)
- Counter-intelligence risk flag
- Follow-up verification suggestions

# NG Lawyer DB Build (Step 1)

## What this skill does
This is **Step 1** of Fei Gao’s “Nigeria Lawyer Network” workflow:
1) Build a **Lawyer Database** (this skill)  
2) Send outreach emails and score by response (separate skill)  
3) Sort & export for fast lookup (separate skill)

The objective is to create a database that allows **fast matching** by:
**City → Practice → Sub-specialty → Regulator → Firm size → Position → Score → Contact**.

This skill focuses on **data collection + structured classification** with evidence links.

---

## Inputs
- **city**: `Lagos` | `Abuja`
- **practice**: `Construction` | `RealEstate` | `Labour` | `Tax` | `Criminal` | `IP`
- **n_per_segment**: integer (target **3**)

---

## Output files
- **lawyer_db_ng.xlsx** (main database)
- **sources.jsonl** (evidence per record: url + snippet + timestamp)

---

## Database schema (fixed column order)
The Excel must contain columns in this exact order:

1. Lawyer_UID  
2. Country  
3. City  
4. Practice  
5. Sub_Practice  
6. Regulator_Tag  
7. Firm_Name  
8. Firm_Size  
9. Position  
10. Lawyer_Name  
11. Email  
12. Phone  
13. LinkedIn  
14. Website  
15. Evidence_URL  
16. Score_Total (blank in Step 1)  
17. Score_ResponseSpeed (blank)  
18. Score_Detail (blank)  
19. Score_Pricing (blank)  
20. Score_Cooperation (blank)  
21. Risk_Flag (blank)  
22. NeedFollowUp (0/1)  
23. ChannelCostRisk (Low/Medium/High)  
24. Last_Updated

---

## Non-negotiable rules (to avoid future scoring chaos)
### 1) Unique key (Lawyer_UID)
All later scoring MUST be written back by **Lawyer_UID**, never by name.

Format:
- `LAW-NG-{CITYCODE}-{PRACTICECODE}-{NNNN}`
- CityCode: Lagos=LAG, Abuja=ABJ
- PracticeCode: Construction=CON, RealEstate=REA, Labour=LAB, Tax=TAX, Criminal=CRI, IP=IPR

Example:
- `LAW-NG-LAG-CON-0001`

### 2) Email policy (anti-channel-cost)
- Email must be **explicitly published** on the evidence page (law firm bio page, author page, or official profile).
- **NO guessing** (e.g., firstname.lastname@firm.com is not allowed unless shown).
- If only a general firm email exists (info@ / contact@), it may be used but set:
  - `ChannelCostRisk=High`
  - `NeedFollowUp=1`

### 3) Evidence chain
Each row must store **Evidence_URL**.
The skill also writes **sources.jsonl** with:
- Lawyer_UID
- Evidence_URL
- Evidence_Snippet (<= 300 chars)
- Captured_At

### 4) Firm_Size classification (fee proxy)
Firm_Size affects pricing expectation. Classify using evidence:

- **Top**:
  - The firm is ranked in **Chambers** or **Legal 500** in Nigeria for the relevant practice; OR
  - Firm lawyer count **> 50** (evidence required)
- **Mid**: lawyer count **15–50**
- **Small**: lawyer count **2–14**
- **Solo**: sole practitioner / independent (count=1)
- **Unknown**: insufficient evidence → set NeedFollowUp=1

### 5) Position mapping (fee proxy)
Normalize to:
- Partner / Counsel / SeniorAssociate / Associate / Junior / Independent / Unknown

Mapping hints:
- Partner: Managing Partner, Senior Partner, Partner
- Counsel: Counsel, Of Counsel
- SeniorAssociate: Senior Associate, Associate (Senior)
- Associate: Associate, Solicitor
- Junior: Junior Associate, Trainee
- Independent: Sole Practitioner, Principal, Independent Legal Practitioner

---

## Regulator_Tag (only with evidence)
Allowed values:
- CAC, NIPC, FIRS, StateIRS, NAFDAC, Immigration, MinistryOfMines, IPRegistry, EFCC, Police, Court

Rule:
- Tag only when evidence mentions regulator or shows relevant matters.
- If not evidenced, leave blank; outreach email will ask the lawyer to self-report regulators handled.

---

## Data collection strategy (recommended sources)
Priority order:
1) Chambers / Legal 500 ranked firms for Nigeria practice (Top candidates)
2) Official law firm team pages (bio pages with emails)
3) Author pages on firm sites / Lexology / IFLR (when email is shown)
4) Boutique firm sites for Small/Solo

---

## Segmentation target
For each (Firm_Size x Position) segment, collect **n_per_segment** candidates **with verified emails** where possible.

Recommended priority within Top firms:
- Counsel / SeniorAssociate / Associate (often more willing for flexible cooperation)

---

## Example run (MVP)
City: Lagos  
Practice: Construction  
n_per_segment: 3  

Goal: produce a usable initial database for Lagos Construction to validate:
- Firm_Size classification is correct
- Position mapping is correct
- Emails are evidence-backed
- Column order is stable


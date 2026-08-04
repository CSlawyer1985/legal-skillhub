# Intake and Routing

## Required Intake

Resolve before substantive review, using the user's instructions and preliminary file/package context first:

- Matter name and client side.
- User role and review purpose: lawyer work product, in-house review, business negotiation, or research draft for lawyer verification.
- Review scope: full text or Track Changes only.
- Output mode: full report, comments beside provisions, or both.
- Major Issue List: create/update/none. For first drafts, ask whether to seed one for material negotiation points. For later drafts, ask for the prior Major Issue List if available.
- Output language: match the primary transaction-document language unless the user instructs otherwise.
- Structure: RMB onshore, offshore USD direct holding, or offshore USD VIE.
- Governing law and dispute forum.
- Document package: term sheet, investment/subscription agreement, shareholders agreement, articles/章程/M&A/MAA/M&AA, disclosure letter, side letter, ESOP, VIE control documents, closing deliverables, board/shareholder approvals.
- Round and context: seed/angel/Pre-A/A/B/C/Pre-IPO, down-round, bridge/convertible loan, mixed primary/secondary sale, M&A investment.
- Matter boundary, confidentiality level, and whether cross-matter comparison is authorized.

## Intake Gate

Do not force the user to complete the whole intake list. Infer document type,
language, structure, governing law, version, and likely output from the files
where reliable, and disclose those assumptions. Only two gaps block the
corresponding directional conclusion:

- client side is unknown, in which case neutral issue spotting may continue but
  side-specific drafting must wait; or
- a later-round acceptance/rejection judgment is requested without a prior
  draft or verified prior position, in which case current-text risk review may
  continue but negotiation status must wait.

Before asking the user, perform pre-intake triage:

- Read the user's message for explicit instructions.
- Inspect file names and folder structure.
- Build a document map if paths are available.
- Identify apparent draft round, package composition, primary language, structure indicators, governing law/dispute forum indicators, and whether Track Changes/redlines are present.
- Treat filename-based classifications as intake hints. Confirm language, structure, governing law, and version from operative text before substantive reliance.
- Record unreadable, empty, encrypted, corrupted, or unsupported files and stop substantive review of those files until a usable source or OCR path is available.
- Do not analyze substantive clauses or draft recommendations at this stage.

Then ask only for missing, ambiguous, or conflicting items. Do not repeat a checklist item when it is already answered by the user's instruction or clearly shown by the files.

Use this compact status before questions when helpful:

```text
我先做了预检：
- 已从你的指示确认：
- 已从文件/文件名初步判断：
- 还需要你确认：
```

For first-draft full-package review, mandatory confirmations are:

- Files/folder and confirmation that this is a first-draft or full-package review.
- Client side.
- Output mode.
- Major Issue List preference.
- Structure, or permission to infer structure from the documents.
- Governing law/dispute forum and local-counsel flag preference.
- Output language rule.

After pre-intake triage, ask only for a blocking client-side or version-baseline
gap. Infer the remaining items when the documents support a reliable inference;
otherwise state a limited-review assumption and continue with the unaffected
work. Do not turn optional preferences into a mandatory questionnaire.

For second-or-later Track Changes / counterparty markup review, mandatory confirmations are:

- Current draft/markup files and round number if known.
- Review scope: Track Changes only, clean-versus-prior comparison, or full re-review.
- Prior baseline: prior draft, prior issue log/comment plan, prior Major Issue List, and any counterparty response email.
- Whether client side, structure, governing law/dispute forum, and output language remain the same as prior round.
- Output mode: delta review memo, updated Major Issue List, clause-level comments/comment plan, or both/all.
- Major Issue List handling: update existing list, create one if none exists, or skip it.

For later-round review, first determine whether the current files or user instructions already provide the round, current markup, prior baseline, client side, structure/law, output mode, and Major Issue List handling. Ask only for unresolved items.

If the prior baseline remains missing, ask whether to proceed with a limited review. In that case, do not characterize a counterparty change as accepted, rejected, or partially accepted unless the prior position can be verified.

Suggested Chinese intake prompt:

```text
我先做了预检：
- 已从你的指示确认：[列出]
- 已从文件/文件名初步判断：[列出]
- 还需要你确认：[只列缺失/矛盾项]
请确认以上缺口后，我再开始实质条款审阅。
```

Suggested Chinese later-round prompt:

```text
我先做了后续稿预检：
- 已从你的指示确认：[列出]
- 已从当前文件/文件名初步判断：[列出]
- 版本链里还缺：[只列缺失的上一版/上一轮 issue log/Major Issue List/对方回复等]
- 本轮审阅还需要你确认：[只列缺失/矛盾项]
请确认以上缺口后，我再开始审阅对方本轮修改。
```

Suggested English intake prompt:

```text
I ran a preliminary intake check:
- Confirmed from your instructions: [list]
- Detected from the files/package context: [list]
- Still needed before substantive review: [only missing or conflicting items]
Please confirm these gaps, then I will start the substantive clause review.
```

Suggested English later-round prompt:

```text
I ran a later-round intake check:
- Confirmed from your instructions: [list]
- Detected from the current files/file names: [list]
- Missing from the version chain: [only missing prior draft / prior issue log / Major Issue List / counterparty response items]
- Still needed for this round: [only missing or conflicting items]
Please confirm these gaps, then I will start reviewing the counterparty changes.
```

## Trigger Terms

Treat these as in-scope triggers: VC/PE,投融资协议,股东协议,增资协议,增资协议的补充协议,认购协议,章程,SPA,SHA,IRA,M&A,M&AA,MAA,term sheet,红筹,人民币架构,VIE,开曼,美元架构,投资协议,股权转让,股权回购,反稀释,清算优先,领售,共同出售,优先购买,优先认购,保护性条款,董事席位,最优惠待遇.

Trigger priority:

1. Explicit `$pe-vc-transaction-docs-review` invocation.
2. An uploaded financing document plus a review, comparison, comment, redline,
   or Major Issue List request.
3. Clause terms only when the surrounding request is clearly a private-company
   PE/VC financing matter.
4. An unreadable or OCR-failed in-scope attachment still triggers intake and
   degradation handling; it does not silently disable the skill.

## Exclusions

Do not use this skill for:

- Fund formation, LPA review, fund manager registration, AMAC filing, asset management regulation.
- Legal news, training announcements, or pure regulatory updates.
- Pure private fund industry supervision unless the user connects it to transaction agreement review.

## Structure Routing

Use only two top-level structures:

1. RMB onshore: PRC company is the financing subject.
2. Offshore USD: offshore company, usually Cayman, is the financing subject. Subroute:
   - Direct holding: offshore company directly or indirectly holds PRC operating entities through equity.
   - VIE: offshore company controls PRC operating entities through contractual control.

All benchmarked key clauses matter under both structures. The structure changes enforceability, drafting mechanics, governing law, and the relevant practicing-lawyer consultation notice; it does not remove the need to review any core clause. Use: `涉及中国法律相关事项，请咨询执业中国律师；涉及非中国法管辖事项，请咨询相应法域的执业律师。`

## Language Routing

- If the main transaction agreement is Chinese, output all generated analysis, headings, tables, comments, Major Issue Lists, revised clauses, and fallbacks in Chinese.
- If the main transaction agreement is English, output all generated analysis, headings, tables, comments, Major Issue Lists, revised clauses, and fallbacks in English by default.
- Keep original clause quotations, defined terms, party names, and clause numbers in their source language.
- For bilingual or mixed packages, follow the controlling version or the primary operative agreement. If no controlling language can be inferred, ask or state the assumption.

## Scope Routing

Full-text review:

- Use for first drafts, signing drafts, or when prior draft is unavailable.
- Review definitions, operative clauses, schedules, signature blocks, disclosure mechanics, articles/章程 consistency, and cross-document conflicts.
- For first drafts, classify comments into major negotiation issues and ordinary drafting comments. Offer or prepare a Major Issue List for material issues likely to be negotiated across rounds.

Track Changes-only review:

- Use when the current task is to review counterparty revisions.
- Focus on inserted/deleted/revised text, but check nearby definitions and cross-references where needed.
- If the changed clause depends on unchanged definitions or schedules, read those supporting sections and say why.
- Compare counterparty revisions against the prior Major Issue List and update status, counterparty position, latest compromise wording, and next action.
- For `.docx`, use `scripts/extract_contract_text.py --scope track-changes` and review each grouped paragraph's `before_text` and `after_text` before drilling into raw change metadata. If revision markers exist but no text-bearing changes are detected, report that limitation and compare versions or run a full review. If the tool flags high-volume Track Changes, ask whether the user wants full redline review, core-clause-focused review, or Major Issue List-focused review before starting; for PDF redlines, inspect manually or convert with OCR and state limits.

## Output Routing

Full report:

- Use when the user asks for an overall review, issue list, negotiation memo, or client-ready summary.
- If material issues are found, include a recommendation on whether to create/update a Major Issue List.

Comments-only:

- Use for first-pass lawyer review of a Word document.
- Do not change original text. Anchor each comment to a clause or paragraph.

Both:

- Use when the user needs a complete issue log and clause-level comments.

Major Issue List:

- Use for material issues that should be tracked across negotiation rounds.
- Do not include ordinary typos, formatting, numbering, or minor style comments unless they create legal ambiguity.
- For later rounds, maintain the same Issue ID when updating status.
- Keep the table to five columns or fewer.

Redline:

- Use only when expressly requested. Provide complete revised wording and keep a separate issue log.

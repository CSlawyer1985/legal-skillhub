# 🧪 Evaluation Report — Swarm-Style Paired Testing

English | [中文摘要](#-中文摘要)

This document records the evaluation that `docx-trackdiff` went through before
release. The evaluation followed the **skill-creator swarm protocol**: paired
`with_skill` vs. `baseline` executions on an identical real-world task, blind
grading by an independent verifier agent, then a fix-and-re-verify loop.

> **TL;DR** — The skill-produced output passed all checks in ~1 minute. The
> blind grader caught a genuine image-fidelity defect in the skill's own script
> that its text-level verifier could not see. The bug was fixed, the verifier
> was hardened from 5 to 7 checks, and both outputs now pass 7/7.

---

## 1. Setup

| | |
|---|---|
| **Eval task** | "Compare two versions of a paper (.docx) and produce a Word tracked-changes file that can be accepted/rejected per revision." |
| **Inputs** | Two real successive drafts of an academic paper (~6.4k → ~8.0k words, 150 vs 177 paragraphs, 14 tables, embedded figures, footnotes, hyperlinks) |
| **Revision metadata required** | author `Big Stephen`, date `2026-08-14` |
| **Run A — with_skill** | Agent reads `SKILL.md`, follows its workflow (bundled scripts only) |
| **Run B — baseline** | Agent solves from scratch, explicitly forbidden from reading the skill directory |
| **Grader** | Independent verifier agent; did **not** know which output used the skill |

Both executors received the same prompt, the same input files, and the same
output expectations. The grader received both outputs labeled only A and B.

## 2. Results

| | 🅰️ with_skill | 🅱️ baseline |
|---|---|---|
| **Wall-clock effort** | **~1 minute** (script run + verify + render) | ~15 minutes (own implementation, 2 fix-rebuild cycles) |
| **Revision marks** | 811 `<w:ins>` / 411 `<w:del>` | 2,463 `<w:ins>` / 387 `<w:del>` |
| **Unique revision IDs** | ✅ 1,222, zero duplicates | ✅ 2,850, zero duplicates |
| **author / date on every revision** | ✅ | ✅ |
| **`w:trackChanges` enabled** | ✅ | ✅ |
| **No stray `w:t` inside `w:del`** | ✅ | ✅ |
| **Accept-all == NEW text** (728 paras) | ✅ | ✅ |
| **Reject-all == OLD text** (701 paras) | ✅ | ✅ |
| **LibreOffice PDF render** | ✅ clean | ✅ clean |
| **Changed-figure fidelity** | ❌ **defect found** (see §3) | ✅ old bytes preserved |
| **Spurious revisions** | ✅ none | ⚠️ 1 (byte-identical renumbered image marked del+ins) |

## 3. 🐞 The bug the grader caught

The skill's script reused relationship targets **by file name** when remapping
deleted-paragraph images into the new package. Both drafts contained figures at
the same media paths (e.g. `word/media/rId13.png`) but with **different bytes**.
Result: the deletion mark for a replaced figure pointed at the *new* image —
the old figure's bytes were silently lost, and "reject change" would have
restored the wrong picture.

Crucially, **the skill's own 5-check verifier passed this output**, because its
accept/reject simulation was text-only. The blind grader caught it by hashing
media parts end-to-end.

**Fix** (`compare_docx_tracked.py`): relationship reuse for images now requires
a **byte-level match**; otherwise the old image is copied into the package
under a `tracked_*` name and referenced by a fresh relationship ID.

**Verifier hardening** (`verify_tracked.py`), from 5 to 7 checks:

- ➕ every revision carries `w:author` and `w:date`
- ➕ every OLD image's bytes survive somewhere in the output package (md5 set comparison)

## 4. Post-fix verification

| Check | with_skill output | baseline output |
|---|---|---|
| 1. Structure (unique IDs, no stray `w:t`, no dangling refs) | ✅ | ✅ |
| 2. `w:trackChanges` present | ✅ | ✅ |
| 3. Accept-all == NEW (paragraph-exact) | ✅ | ✅ |
| 4. Reject-all == OLD (paragraph-exact) | ✅ | ✅ |
| 5. OLD-only paragraphs fully covered by `w:delText` | ✅ | ✅ |
| 6. author & date on all revisions | ✅ | ✅ |
| 7. OLD image bytes preserved | ✅ (4 `tracked_*.png` added) | ✅ |

**7 / 7 PASS on both outputs.**

## 5. Takeaways

1. **The skill delivers its promise**: ~15× faster than a competent from-scratch
   implementation, with zero judgment errors, because the fragile OOXML rules
   live in tested code instead of the agent's working memory.
2. **Blind grading earned its keep**: the most serious defect was invisible to
   the skill's own verifier. An adversarial second pair of eyes — comparing
   media bytes, not just text — was what caught it.
3. **Evals should check bidirectional fidelity**: for tracked-changes output,
   "reject all" must restore the old document *completely* — images included.
   Text-only simulation is not enough.
4. **Baseline strengths were folded back**: the baseline's correct handling of
   changed figures became the skill's fix; its one weakness (marking a
   byte-identical renumbered image as changed) is a case the skill already
   handled correctly.

---

*Evaluation conducted with the Kimi K3 Agent Swarm: one coder executor
(with_skill), one general executor (baseline), one independent verifier
(grader). Prompts, outputs, and grading evidence were produced on 2026-08-16.*

---

## 🇨🇳 中文摘要

本文件记录了 `docx-trackdiff` 发布前的 **swarm 式配对盲测**：同一真实任务
（对比一份学术论文的两个版本、生成 Word 修订模式文件）分别由"使用技能的代理"
和"零技能基线代理"执行，再由不知情的独立评分代理盲评。

- **效率**：with_skill 约 1 分钟完成，baseline 从零实现约 15 分钟
- **质量**：盲评抓到了技能脚本的一个真实缺陷——同名图片字节不同时旧图会丢失
  （"拒绝修订"无法恢复旧图），技能自带的 5 项纯文本验证器对此不可见
- **修复闭环**：图片关系复用改为字节级比对；验证器从 5 项加固到 7 项
  （新增作者/日期检查、旧图字节保留检查）
- **最终结果**：修复后两个产物均 7/7 全过

结论：技能把脆弱的 OOXML 规则固化进测试过的代码，速度提升约 15 倍且零判断失误；
而独立盲评证明了自身价值——最严重的缺陷恰恰逃不过第二双眼睛。
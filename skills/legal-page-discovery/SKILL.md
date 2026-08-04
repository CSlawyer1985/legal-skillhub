---
name: legal-page-discovery
description: Discover and classify a live website's legal/compliance pages — privacy policies, HIPAA/Part 2 notices, terms of use, informed consents, and similar documents — by triangulating sitemap.xml, robots.txt, footer/nav links scraped from multiple pages, and common compliance path-pattern guesses. Retrieves each candidate page's verbatim text via curl (not a summarizing fetch), classifies its content and controlling entity, flags nav-label/content/entity mismatches, and records open-ended salient observations grounded in the page's own language. Produces a manifest for downstream routing (e.g. by skill-router) — does not itself recommend which assessment skill to run.
argument-hint: Provide a base domain (e.g., example.com) and, if known, the legal name of the regulated entity/program operating it
allowed-tools: Bash, WebFetch, WebSearch, Read, Write, Glob, Grep
---

# Legal & Compliance Page Discovery

You are a compliance document librarian for a live website. Your job is not to assess any
document's compliance content — that is the job of other rote skills. Your job is to find every
page on the site that looks like a legal or compliance document, retrieve its actual text, and
record what it is, who it's for, and what's notable about it — so a separate routing step (or an
operator) can decide what to do with each one.

## Why this skill exists

A site's navigation is not a reliable index of its legal pages. A page can be live, indexed, and
even legally required to be posted, while being unreachable by clicking through the site — and a
page that *is* prominently linked under a legal-sounding label (e.g. "Privacy" or "HIPAA") can
turn out to be the wrong document, or belong to a different corporate entity than the one the nav
label implies. Relying on any single signal — the main nav, the footer, a sitemap, a search engine
— will miss pages or misidentify them. This skill's job is to triangulate across all of them and
report what's actually there, in the page's own words.

## Inputs

- **Base domain** (required), e.g. `example.com` or `https://www.example.com`.
- **Legal name of the regulated entity/program** (optional, but provide it when known — e.g.
  "Example Medical Group, P.A."). When supplied, this is the basis for the entity-match check in
  Step 3. When not supplied, record whatever controlling entity each page states and let the
  operator (or `skill-router`) reconcile the names found across pages.
- **Output location** (optional). If the operator specifies a path or directory, write the
  manifest there. Otherwise write `legal-page-manifest.md` (and `.json`) to the current working
  directory.

## Core principle: no single enumeration source is authoritative

Run **all** of Steps 1a–1d below, every time. Do not stop early because one source returned
results — a page can be present in a sitemap but absent from the footer, present in the footer of
one template but not another, or reachable only by guessing a conventional path. The point of this
skill is specifically to catch the page that the others miss.

---

## Step 1 — Enumerate candidate URLs

### 1a. Sitemap(s)

Fetch `https://<domain>/sitemap.xml`. If it is a sitemap *index* (contains `<sitemap>` entries
pointing at other sitemap files), fetch each referenced sitemap and union their URL lists. Also
try `https://<domain>/sitemap_index.xml` if the first returns nothing.

From the full URL list, keep any URL whose path contains a legal/compliance signal word
(case-insensitive): `legal`, `privacy`, `terms`, `hipaa`, `notice`, `npp`, `consent`, `compliance`,
`policy`, `disclosure`, `cookie`, `accessibility`, `hitech`, `part-2`, `part2`.

### 1b. robots.txt

Fetch `https://<domain>/robots.txt`. Note:
- Any `Sitemap:` directives not already tried in 1a — fetch those too.
- Any `Disallow:` paths containing the signal words above. A disallowed path is not crawled by
  search engines, but it is not access-controlled — fetch it directly in Step 2 like any other
  candidate.

### 1c. Footer/nav scrape — homepage AND a deep page

Retrieve the homepage's verbatim text (Step 2) and extract every link whose visible text or
`href` contains a signal word from the list above. Record the visible link text and where it
appeared (e.g., "global footer").

Then repeat on **at least one deep page** — a page that is not the homepage (a blog post, a
service/product page, or one of the candidate legal pages already found). Site templates often
differ between the homepage and interior pages; a link present in one footer and absent from the
other is itself a finding (record it as a mismatch in Step 3).

### 1d. Common path-pattern guesses

Regardless of what 1a–1c found, directly try each of the following paths (combine with the base
domain) and keep any that return a 200 response with substantive content (not a generic 404 page
that happens to return 200):

```
/legal
/legal/privacy
/legal/npp
/legal/terms
/legal/hipaa
/privacy
/privacy-policy
/privacy-practices
/notice-of-privacy-practices
/npp
/hipaa
/hipaa-notice
/notice-of-privacy-practices-hipaa
/terms
/terms-of-use
/terms-of-service
/compliance
/cookie-policy
/accessibility
/informed-consent
/telehealth-consent
```

Some of these will 404 on most sites — that's expected and not itself a finding. The ones that
resolve are added to the candidate set even if no nav link or sitemap entry pointed at them. (This
is how a notice that exists but isn't linked from anywhere gets found.)

### Build the candidate set

Union the URLs from 1a–1d, deduplicated by normalized URL (strip trailing slashes, fragments, and
tracking query parameters).

---

## Step 2 — Verbatim retrieval (do not use a summarizing fetch)

`WebFetch`/`WebSearch` may be used for *enumeration and triage only* — e.g., checking whether a
sitemap exists, or getting a quick read on a page's general topic to decide whether it's worth a
full retrieval. **Never use a summarized fetch as the basis for a classification, entity
identification, or salient observation.** A summarizing fetch can silently drop or compress the
exact clauses this skill exists to surface (de-identification language, entity names, effective
dates, complaint-routing addresses).

For every URL in the candidate set, retrieve its full raw text with `curl` plus an HTML→text
extraction pass:

```bash
curl -sL -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36" "<URL>" -o /tmp/page.html

python3 - <<'PYEOF' > /tmp/page.txt
import re, html
with open('/tmp/page.html') as f:
    s = f.read()
s = re.sub(r'(?is)<(script|style|noscript|svg|path)\b.*?</\1>', '', s)
s = re.sub(r'(?i)<(br|/p|/div|/li|/h[1-6]|/tr|/td|/section|/article|/header|/footer|/nav)\b[^>]*>', '\n', s)
s = re.sub(r'(?s)<[^>]+>', '', s)
s = html.unescape(s)
lines = [l.strip() for l in s.splitlines()]
lines = [l for l in lines if l]
print('\n'.join(lines))
PYEOF
```

Then `Read /tmp/page.txt`. This is the page's verbatim text, line-broken roughly at block-level
HTML elements, with entities decoded — the same mechanism that resolved a prior session's
"summarized rather than verbatim" fetch failures. A browser-like User-Agent matters: some sites
serve a stripped-down or bot-specific page to non-browser user agents, which is itself a
discoverability issue worth recording as a salient observation if you notice it (compare a no-UA
`curl` response to the browser-UA response if the former looks suspiciously thin).

---

## Step 3 — Classify each candidate and record observations

For each URL with substantive content, record:

- **URL.**
- **Nav label(s) and location(s).** Every place this URL was found and under what visible text —
  e.g., `"HIPAA" — global footer`, `"Privacy" — homepage footer only (not present in deep-page
  footer)`, `"(not linked — found via sitemap.xml only)"`, `"(not linked — found via path-pattern
  guess /legal/npp)"`.
- **Content classification.** A short, free-text descriptive label based on signature phrases in
  the verbatim text — not a fixed enum. Examples: "Notice of HIPAA Privacy Practices / Part 2 SUD
  notice", "Consumer privacy policy (CCPA-style)", "Telehealth informed consent", "Terms of use",
  "Pharmacy/vendor partner page (not a legal document)". If a page turns out not to be a
  compliance-relevant document at all, classify it as such and move on — don't force it into a
  compliance category.
- **Controlling entity.** The entity name(s) the document's own text identifies as responsible for
  it — from copyright lines, "operated by," "[Entity] is required by law to...", etc.
- **Entity match.** If a program legal name was supplied in Inputs: does this page's controlling
  entity match it (exact or clear affiliate relationship), or differ? If no program name was
  supplied: just record the entity found; do not guess at a match.
- **Mismatch flags.** Anything that doesn't line up:
  - Nav-label vs. content (a page labeled "HIPAA" whose content is the actual Part 2/SUD notice,
    while a page labeled "Privacy" is a different document).
  - Entity vs. supplied program name, or entity differs between two pages that both look like "the
    privacy policy."
  - Present in one footer/template but not another.
  - A page's own text disclaims being a notice that another page should be (e.g., a CCPA policy
    that says "this is not the notice required by [X]").
- **Salient observations.** An open-ended bullet list of notable, verbatim-grounded statements —
  phrased in plain descriptive language with a verbatim quote, not classified against any skill's
  taxonomy. Write down what's actually there in the document's own words so a separate routing
  step can match it against whatever skills exist now or are added later. Illustrative examples of
  the *kind* of thing worth noting (not a checklist to fill in, and not exhaustive):
  - A de-identification/aggregation claim that doesn't state a method.
  - "We may use data to develop, improve, or demonstrate our products/services" language.
  - Citations to specific statutes or regulations (42 C.F.R. Part 2, 42 U.S.C. § 290dd-2, HIPAA,
    CCPA, state-specific laws).
  - State-specific consent or complaint-routing blocks.
  - BAA, subcontractor, or "qualified service organization" language.
  - AI/automation claims (e.g., "AI", "machine learning", "automated").
  - Effective/revision dates, and any statement (or absence of one) about how the document gets
    updated.
  - Complaint-routing addresses (who the document tells the reader to complain to).

Do not pre-judge which skill, if any, cares about an observation. The observation is the
deliverable; matching it to a skill is a different skill's job.

---

## Step 4 — Output

Produce two artifacts.

### Output Part 1: Manifest table + observations (markdown)

A table:

| URL | Nav label(s) / location | Classification | Controlling entity | Entity match | Mismatch flags |
|---|---|---|---|---|---|

Followed by, for each URL, a short subsection with its salient-observations bullet list.

Close with a **Discoverability notes** section: anything found via sitemap/path-guess but not
linked from navigation; anything linked from one template but not another; any pages whose nav
label doesn't match their content.

### Output Part 2: JSON manifest

```json
{
  "base_domain": "string",
  "supplied_program_entity": "string or null",
  "discovery_date": "string — ISO-8601 date",
  "sources_checked": {
    "sitemap": "found | not found",
    "sitemap_index": "found | not found",
    "robots_txt": "found | not found",
    "homepage_footer_scrape": "done",
    "deep_page_footer_scrape": "string — which deep page was used"
  },
  "documents": [
    {
      "url": "string",
      "nav_labels": ["string — e.g. \"HIPAA — global footer\""],
      "found_via": ["sitemap", "robots", "homepage_footer", "deep_page_footer", "path_guess"],
      "classification": "string — free text",
      "controlling_entity": "string or null",
      "entity_match": "match | mismatch | not assessed (no program entity supplied)",
      "mismatch_flags": ["string"],
      "salient_observations": ["string — plain description + verbatim quote"]
    }
  ],
  "discoverability_notes": ["string"]
}
```

Write both to the output location from Inputs (default: current working directory, files named
`legal-page-manifest.md` and `legal-page-manifest.json`).

---

## Guardrails

- **The manifest is the deliverable.** Hand it to the user and stop. Do not assess any document's
  compliance content, and do not recommend which skill to run on which document — that is
  `skill-router`'s job, working from this manifest.
- **Verbatim only for content used in classification or observations.** A WebFetch/WebSearch
  summary may guide *where to look*, but every classification, entity identification, and salient
  observation must trace to text retrieved via Step 2.
- **Run all four enumeration paths (1a–1d).** A clean result from one does not excuse skipping the
  others — the failure mode this skill exists to catch is exactly "looked in the obvious place,
  missed the page that mattered."
- **Don't force a compliance classification onto a non-compliance page.** If a candidate URL turns
  out to be unrelated (e.g. a "Pharmacy Partners" page that happened to match a sitemap signal
  word), classify it plainly as such with no salient observations, or omit it with a one-line
  note.
- **Mismatches are findings, not errors.** A nav label that doesn't match a page's content, or an
  entity that doesn't match the supplied program name, is exactly the kind of thing this skill is
  for. Record it plainly; do not try to resolve or explain it away.

---

## Few-Shot Example (sanitized — telehealth provider with a mislabeled footer)

**Inputs:** base domain `example-recovery.com`; supplied program entity "Example Recovery Medical
Group, P.A."

**Step 1 findings:** `sitemap.xml` lists `/legal/npp` and `/legal/privacy` among ~40 URLs, both
matching the `legal`/`privacy`/`npp` signal words. The homepage global footer has links labeled
"Privacy" → `/legal/privacy`, "HIPAA" → `/legal/npp`, "Terms of Use" → `/legal/terms`. A deep page
(a blog post) has the same footer. `/legal/npp` is not surfaced anywhere except the "HIPAA" footer
link and the sitemap — there is no link with visible text "Privacy Policy" or "Notice of Privacy
Practices" anywhere on the site pointing at it.

**Step 2/3 — `/legal/npp`:**
- Nav label(s)/location: `"HIPAA" — global footer (homepage and deep page)`
- Classification: "Notice of HIPAA Privacy Practices / Part 2 SUD notice"
- Controlling entity: "Example Recovery Medical Group, P.A." — **matches** supplied program entity
- Mismatch flags: "Labeled 'HIPAA' in the footer rather than 'Privacy' or 'Notice of Privacy
  Practices' — a user or agent searching for the privacy notice by label would not find this
  page."
- Salient observations:
  - "States: 'we protect the privacy and security of your substance use disorder patient records
    in accordance with 42 U.S.C. § 290dd–2 and 42 C.F.R. Part 2' — Part 2 program."
  - "Effective Date: [date]; reserves the right to revise the notice and describes how revisions
    are provided."
  - "Complaint routing names the program's Privacy Officer plus HHS, the U.S. Attorney, and
    SAMHSA."

**Step 2/3 — `/legal/privacy`:**
- Nav label(s)/location: `"Privacy" — global footer (homepage and deep page)`
- Classification: "Consumer privacy policy (CCPA-style)"
- Controlling entity: "Example Recovery, Inc." — **mismatch**: does not match supplied program
  entity "Example Recovery Medical Group, P.A."
- Mismatch flags: "Labeled 'Privacy' — the label a user/agent would search for the Part 2 notice
  under — but this document is a different entity's consumer privacy policy and explicitly states
  it is not the HIPAA/Part 2 notice."
- Salient observations:
  - "States it 'does not apply to ... protected health information governed by HIPAA' and directs
    readers elsewhere for that notice — but does not link to `/legal/npp` from this page."
  - "States: 'we may disclose de-identified or aggregated information to third parties for
    marketing, advertising, research, and other purposes' — no de-identification method stated."
  - "States: 'we may use information to develop and improve our Platform and/or the Services.'"

**Discoverability notes:**
- "`/legal/npp` (the Part 2 notice) is reachable only via the footer link labeled 'HIPAA' or via
  `sitemap.xml` — no page links to it with a 'Privacy' or 'Notice of Privacy Practices' label."
- "`/legal/privacy` (labeled 'Privacy' in every footer checked) belongs to a different corporate
  entity than the Part 2 program and explicitly disclaims being the HIPAA/Part 2 notice, with no
  forward link to the page that is."

---

## Powered by Rote

This skill is part of the [Rote Compliance Skills](https://github.com/Rote-Compliance/rote-compliance-skills), open-sourced by [Dang's Solutions](https://dangssolutions.com).

**Want to run this at scale?** [Rote](https://rotecompliance.com) continuously discovers and
re-checks an organization's posted legal/compliance pages — catching new pages, removed pages, and
nav-label drift between site updates, not just a one-time snapshot.

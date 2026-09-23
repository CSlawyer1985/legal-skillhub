#!/usr/bin/env python3
"""Verify the anonymized 2026 young-lawyer AI skills collection."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
INDEX = ROOT / "index" / "skills-index.json"
SITE_SKILLS = ROOT / "docs" / "data" / "skills.json"
HOME = ROOT / "docs" / "index.html"
PAGE = ROOT / "docs" / "young-lawyers-ai-skills-2026.html"
TCJTL_PAGE = ROOT / "docs" / "tcjtl-ai-legal-camp-2026.html"
MANIFEST = ROOT / "docs" / "events" / "young-lawyers-ai-skills-2026.json"
PUBLIC_ASSETS = (
    PAGE,
    MANIFEST,
    ROOT / "docs" / "assets" / "young-lawyers-event.css",
    ROOT / "docs" / "assets" / "young-lawyers-event.js",
)

LEGAL_REASONING = (
    "administrative-value-judgment",
    "analogical-reasoning",
    "argument-chain-construction",
    "argument-strength-evaluation",
    "billing-and-litigation-budget",
    "case-lifecycle-planning",
    "legal-reasoning-case-retrieval",
    "conflict-resolution",
    "counterfactual-reasoning",
    "deductive-reasoning",
    "dispute-and-performance-risk",
    "dispute-issue-identification",
    "evidence-argument-chain",
    "evidence-evaluation",
    "formal-legal-consequence",
    "inductive-reasoning",
    "internal-compliance-risk-identification",
    "judgment-document-generation",
    "judicial-value-judgment",
    "legal-abductive-reasoning",
    "legal-article-retrieval",
    "legal-concept-comprehension",
    "legal-document-formatting",
    "legal-document-summarization",
    "legal-element-extraction",
    "legal-interpretation-argument",
    "legal-judgment-prediction",
    "legal-norm-validity-check",
    "legal-reasoning-risk-assessment",
    "legal-terminology",
    "multi-document-summarization",
    "normative-meaning-argumentation",
    "other-legal-retrieval",
    "strategic-risk-prioritization",
    "structured-element-extraction",
    "systematic-interpretation",
    "teleological-interpretation",
    "trial-scheduling-and-deadline-monitoring",
)

BAICHEN_NDR = (
    "baichen-ndr-standard",
    "baichen-contract-drafting",
    "baichen-contract-review",
    "baichen-legal-due-diligence",
    "baichen-legal-opinion",
    "baichen-legal-research-memo",
    "baichen-compliance-review",
    "baichen-labor-employment",
    "baichen-family-inheritance",
    "baichen-client-consultation",
    "baichen-client-notice",
    "baichen-lawyer-letter",
)

AGGREGATE_ALL = (
    "ad-compliance-ai-review-plus",
    "add-slide-to-deck",
    "agent-email",
    "ai-governance-aia-generation",
    "ai-governance-cold-start-interview",
    "ai-governance-customize",
    "ai-governance-initial-questions",
    "ai-governance-inventory",
    "ai-governance-policy-monitor",
    "ai-governance-policy-starter",
    "ai-governance-reg-gap-analysis",
    "ai-governance-use-case-triage",
    "ai-governance-vendor-ai-review",
    "appeal-docs-generator",
    "article2book",
    "civil-case-cause-2026-01-01",
    "civil-code-and-interpretations-plus",
    "clawhub-sync",
    "commercial-amendment-history",
    "commercial-cold-start-interview",
    "commercial-customize",
    "commercial-escalation-flagger",
    "commercial-matter-workspace",
    "commercial-nda-review",
    "commercial-renewal-tracker",
    "commercial-review",
    "commercial-review-proposals",
    "commercial-saas-msa-review",
    "commercial-stakeholder-summary",
    "commercial-vendor-agreement-review",
    "corporate-ai-tool-handoff",
    "corporate-board-minutes",
    "corporate-closing-checklist",
    "corporate-cold-start-interview",
    "corporate-customize",
    "corporate-deal-team-summary",
    "corporate-diligence-issue-extraction",
    "corporate-entity-compliance",
    "corporate-integration-management",
    "corporate-material-contract-schedule",
    "corporate-matter-workspace",
    "corporate-tabular-review",
    "corporate-written-consent",
    "counsel-unit-legal-service-record",
    "cross-examination-opinion-civil-administrative-case-ai-writing-plus",
    "data-compliance-pip-analysis-plus",
    "de-ai-polish",
    "directory-index",
    "doc-redline",
    "docx",
    "ecommerce-livestream-corporate-legal-tax-risk-control-plus",
    "git-batch-commit",
    "gongwen-docx",
    "gov-info-disclosure-response",
    "gov-info-disclosure-review",
    "government-procurement-dispute-cn-general",
    "heluo-lifetime",
    "html-slides-studio",
    "image-redactor",
    "industry-quick-research",
    "industry-research-analyst",
    "insurance-dispute-analysis-plus",
    "ip-cease-desist",
    "ip-clearance",
    "ip-cold-start-interview",
    "ip-customize",
    "ip-fto-triage",
    "ip-infringement-triage",
    "ip-invention-intake",
    "ip-matter-workspace",
    "ip-oss-review",
    "ip-portfolio",
    "ip-takedown",
    "ipc-jurisdiction",
    "jicheng-legal-job-search",
    "law-document-generator",
    "lawyer-workspace-expert",
    "legal-article-writing",
    "legal-builder-hub-auto-updater",
    "legal-builder-hub-cold-start-interview",
    "legal-builder-hub-customize",
    "legal-builder-hub-disable",
    "legal-builder-hub-registry-browser",
    "legal-builder-hub-related-skills-surfacer",
    "legal-builder-hub-skill-installer",
    "legal-builder-hub-skill-manager",
    "legal-builder-hub-skills-qa",
    "legal-builder-hub-uninstall",
    "legal-case-analysis",
    "litigation-brief-section-drafter",
    "litigation-chronology",
    "litigation-claim-chart",
    "litigation-cn-evidence-review",
    "litigation-cold-start-interview",
    "litigation-customize",
    "litigation-demand-draft",
    "litigation-demand-intake",
    "litigation-demand-received",
    "litigation-deposition-prep",
    "litigation-legal-hold",
    "litigation-matter-briefing",
    "litigation-matter-close",
    "litigation-matter-intake",
    "litigation-matter-update",
    "litigation-matter-workspace",
    "litigation-oc-status",
    "litigation-portfolio-status",
    "litigation-subpoena-triage",
    "mac-clipboard-to-md",
    "mcn-streamer-termination-legal-analysis-plus",
    "md2word",
    "meeting-minutes",
    "new-case",
    "opc-legal-counsel",
    "oral-draft-editor",
    "paddle-ocr",
    "pdf",
    "pptx",
    "prc-legal-research",
    "prc-legal-research-case-search",
    "prc-legal-research-company-search",
    "prc-legal-research-deep-research",
    "prc-legal-research-law-search",
    "prc-legal-research-securities-compliance",
    "prc-opposing-counsel-review",
    "python-pptx-presentation",
    "regulation-briefing",
    "regulation-interpretation",
    "regulatory-cold-start-interview",
    "regulatory-comments",
    "regulatory-customize",
    "regulatory-gap-surfacer",
    "regulatory-gaps",
    "regulatory-incoming-letter",
    "regulatory-matter-workspace",
    "regulatory-policy-diff",
    "regulatory-policy-redraft",
    "regulatory-reg-feed-watcher",
    "repo-research",
    "rightclick-creator",
    "riskbird-cominfo-batch",
    "scanned-pdf-to-word",
    "securities-loss-calculator",
    "skill-creator",
    "skill-lint",
    "skill-vetter",
    "smart-calendar",
    "stock-k-line-analysis-visualization-plus",
    "svg-article-illustrator",
    "szzz-case-study-lite",
    "taiwan-compatriots-mainland-policy-qa-plus",
    "travel-expense-reimbursement-toolkit",
    "video-to-evidence-layout",
    "wang-yangming-ai-says",
    "wang-yangming-ai-teaches-unity-of-knowledge-and-action-plus",
    "wechat-article-layout",
    "wordcloud-generator",
    "wx-mp-draft-publisher",
    "xlsx",
    "yaoshitong-substance-catalog",
)

SPOTLIGHT_NEW = (
    "laborpilot",
    "one-contract",
    "china-litigation-rehearsal",
    "refine-legal-chinese",
    "equity-delivery-assistant",
    "legal-consult-corpus",
    "zhilu-complaint-ops",
)

PREVIOUS_WORKBOOK = (
    "element-based-plaintiff",
    "lawyer-engineering-appraisal",
    "client-material-incubator",
    "criminal-defense-workflow",
    "contract-intelligence-cn",
    "civil-litigation-workflow",
    "wenzhou-criminal-legal-aid-workflow",
    "lvdian-legal-search",
    "lvshen-contract-review",
    "case-archiver",
    "inheritance-evidence-cross-examination",
    "administrative-relief-workflow",
    "bootstrap-ai-data-compliance",
    "gp-lead-radar",
    "gp-bid-scoring-analysis",
    "gp-bid-document",
    "gp-mock-evaluation",
    "gp-procurement-inspection",
    "gp-challenge-complaint",
    "overseas-legal-compliance",
    "invoice-from-email",
    "cross-border-service-tax",
    "cdiw-core",
    "litigation-trial-prep",
    "litigation-docs-generator",
    "element-complaint-filler",
    "litigation-hub",
    "execution-docs-generator",
    "legal-bid-pipeline",
)

EXISTING_SHOWCASE = (
    "mqc-litigation-visual-redraw",
    "mqc-timeline-master",
    "mqc-legal-relation-master",
    "mqc-chronicle-master",
    "mqc-trial-confrontation-master",
    "case-analysis-wang-request-rights",
    "case-retrieval-report-fast",
    "ad-compliance-consumer-rights-review-plus",
)

PRIMARY_NEW = LEGAL_REASONING + BAICHEN_NDR + SPOTLIGHT_NEW
TOPIC_PRIMARY = BAICHEN_NDR + tuple(
    slug for slug in SPOTLIGHT_NEW
    if slug not in {"china-litigation-rehearsal", "refine-legal-chinese"}
)
TOPIC_EXCLUDED_AUTHORS = ("Legal-Skills-Chinese 项目团队", "原作者未署名")
FORBIDDEN_PUBLIC_TERMS = ("浙江省律师协会", "省律协")
FEATURED_DEMOS = (
    ("上半场一", "股权交割实务助手", "equity-delivery-assistant", "indexed"),
    ("上半场二", "LaborPilot", "laborpilot", "indexed"),
    ("上半场三", "行政救济——全流程 AI Skill", "administrative-relief-workflow", "indexed"),
    ("上半场四", "「智录」工商投诉工单闭环 Skill", "zhilu-complaint-ops", "indexed"),
    ("下半场五", "破产案件中期工作流插件", None, "showcase-only"),
    ("下半场六", "One-Contract", "one-contract", "indexed"),
    ("下半场七", "律鉴（法律文书交付前可信溯源产品）", None, "showcase-only"),
    ("下半场八", "DeepSeek Harness 律师模式下的 AI 工作台", None, "showcase-only"),
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_skill(slug: str) -> None:
    folder = SKILLS / slug
    entry = folder / "SKILL.md"
    require(entry.is_file(), f"missing skill entrypoint: {slug}/SKILL.md")
    text = entry.read_text(encoding="utf-8")
    require(text.startswith("---\n"), f"missing frontmatter: {slug}")
    frontmatter = text.split("---", 2)[1]
    require(bool(re.search(r"^name:\s*\S", frontmatter, re.M)), f"missing name: {slug}")
    require(
        bool(re.search(r"^description:\s*\S|^description:\s*[>|]", frontmatter, re.M)),
        f"missing description: {slug}",
    )
    noise = [
        path.relative_to(folder)
        for path in folder.rglob("*")
        if path.name == ".DS_Store"
        or path.suffix == ".pyc"
        or path.name.startswith(".~")
        or path.name == "__pycache__"
    ]
    require(not noise, f"packaging noise in {slug}: {noise}")


def main() -> None:
    require(len(PRIMARY_NEW) == 57, f"expected 57 primary additions, got {len(PRIMARY_NEW)}")

    require(PAGE.is_file(), "missing anonymized topic page")
    require(MANIFEST.is_file(), "missing event manifest")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    groups = manifest.get("groups", [])
    require([group.get("id") for group in groups] == [
        "activity-new", "previous-workbook", "showcase-existing", "aggregate-additions"
    ], "manifest groups or order changed")
    require([len(group.get("skills", [])) for group in groups] == [17, 29, 8, 41],
            "manifest group counts must be 17/29/8/41 after author filtering")
    require(tuple(groups[0]["skills"]) == TOPIC_PRIMARY, "topic primary additions do not match author filter")
    require(tuple(groups[1]["skills"]) == PREVIOUS_WORKBOOK, "previous workbook set changed")
    require(tuple(groups[2]["skills"]) == EXISTING_SHOWCASE, "existing showcase set changed")
    aggregate_new = tuple(groups[3]["skills"])
    require("ipc-jurisdiction" not in aggregate_new, "unsigned ipc-jurisdiction must stay out of the topic")
    manifest_ids = tuple(
        skill_id
        for group in groups
        for skill_id in group.get("skills", [])
    )
    require(manifest.get("collection_total") == 95, "manifest collection_total must be 95")
    require(manifest.get("newly_added") == 58, "manifest newly_added must be 58")
    require(manifest.get("updated") == 1, "manifest updated must be 1")
    require(manifest.get("index_total") == 2303, "manifest index_total must be 2303")
    require(manifest.get("priority_authors") == ["龚家勇", "杨卫薪", "张天伦", "卢思琦"],
            "topic author priority must preserve the requested order")
    require(len(manifest_ids) == 95, "manifest must contain 95 author-attributed collection ids")
    require(len(manifest_ids) == len(set(manifest_ids)), "manifest contains duplicate ids")
    require(set(manifest.get("titles", {})) == set(manifest_ids), "manifest titles do not cover collection")
    featured = manifest.get("featured", [])
    featured_summary = tuple(
        (item.get("session"), item.get("title"), item.get("skill_id"), item.get("availability"))
        for item in featured
    )
    require(featured_summary == FEATURED_DEMOS, "featured stage works or order changed")
    require([item.get("order") for item in featured] == list(range(1, 9)),
            "featured stage order must be 1 through 8")
    indexed_featured = [item[2] for item in FEATURED_DEMOS if item[2]]
    require(len(indexed_featured) == 5, "expected five stage works with verified Skill links")
    require(set(indexed_featured) <= set(manifest_ids), "featured Skill link is outside collection")
    require(all(item.get("presenters") for item in featured), "every stage work must name its presentation team")
    authors = manifest.get("authors", {})
    require(set(authors) == set(manifest_ids), "manifest authors must cover every collection Skill")
    require(all(str(author).strip() for author in authors.values()), "manifest author labels must not be empty")
    require(not (set(authors.values()) & set(TOPIC_EXCLUDED_AUTHORS)),
            "topic must exclude Legal-Skills-Chinese team and unsigned works")
    for author in authors.values():
        require("微信" not in author and not re.search(r"(?<!\d)1[3-9]\d{9}(?!\d)", author),
                f"public author label contains contact details: {author}")

    require(len(AGGREGATE_ALL) == 160, f"expected 160 aggregate library additions, got {len(AGGREGATE_ALL)}")
    all_new = PRIMARY_NEW + AGGREGATE_ALL
    require(len(all_new) == 217, f"expected 217 additions, got {len(all_new)}")
    for slug in all_new:
        validate_skill(slug)
    criminal = (SKILLS / "criminal-defense-workflow" / "SKILL.md").read_text(encoding="utf-8")
    require("version: 3.3.0" in criminal, "criminal-defense-workflow was not upgraded to 3.3.0")

    records = json.loads(INDEX.read_text(encoding="utf-8"))
    indexed = {record["folder"] for record in records}
    require(len(records) == 2303, f"expected 2303 indexed skills, got {len(records)}")
    require(set(manifest_ids) <= indexed, f"collection missing from index: {set(manifest_ids) - indexed}")
    excluded_examples = set(LEGAL_REASONING) | {"china-litigation-rehearsal", "refine-legal-chinese", "ipc-jurisdiction"}
    require(excluded_examples <= indexed, "topic exclusions must remain available in the SkillHub library")
    require(not (excluded_examples & set(manifest_ids)), "excluded author categories leaked into the topic")
    site_records = json.loads(SITE_SKILLS.read_text(encoding="utf-8"))
    require(all("author" in record for record in site_records), "site data must retain author attribution")
    for record in site_records:
        author = str(record.get("author") or "")
        require("微信" not in author and not re.search(r"(?<!\d)1[3-9]\d{9}(?!\d)", author),
                f"site author field exposes contact details: {record['id']}")

    for public_path in PUBLIC_ASSETS:
        require(public_path.is_file(), f"missing public asset: {public_path.relative_to(ROOT)}")
        text = public_path.read_text(encoding="utf-8", errors="replace")
        for term in FORBIDDEN_PUBLIC_TERMS:
            require(term not in text, f"public asset exposes forbidden organizer label: {public_path.name}")
        require(not re.search(r"(?<!\d)1[3-9]\d{9}(?!\d)", text),
                f"public asset exposes a mobile number: {public_path.name}")
        require(not re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text),
                f"public asset exposes an email address: {public_path.name}")

    home = HOME.read_text(encoding="utf-8")
    new_href = 'href="./young-lawyers-ai-skills-2026.html"'
    old_href = 'href="./tcjtl-ai-legal-camp-2026.html"'
    require(new_href in home, "homepage missing young-lawyer collection banner")
    require(old_href in home, "homepage lost the existing camp banner")
    require(home.index(new_href) < home.index(old_href), "new banner must appear above the camp banner")
    require(home.index(old_href) < home.index('<section class="browse">'),
            "event banners must remain above Browse Skills")
    require("2303" in home, "homepage total was not updated to 2303")
    require("三路材料对照" not in home and "四层去重" not in home,
            "homepage banner must describe collection content, not ingestion process")
    require("style.css?v=2303-theme2" in home, "homepage must bust the cached banner palette")
    require("天驰君泰杭州分所第一届青训营暨 AI 法律服务产品设计训练营成果专题" in home,
            "camp banner must use the event name as its primary title")
    for term in FORBIDDEN_PUBLIC_TERMS:
        require(term not in home, "homepage exposes forbidden organizer label")

    page = PAGE.read_text(encoding="utf-8")
    require('id="live-demos"' in page, "topic page missing prioritized stage section")
    require('id="yl-featured-grid"' in page, "topic page missing stage work container")
    require("三路对照" not in page and "四层去重" not in page,
            "topic page must describe capabilities, not ingestion process")
    require("young-lawyers-event.css?v=2303-theme2" in page
            and "young-lawyers-event.js?v=2303-topic95-priority2" in page,
            "young-lawyer topic must bust cached theme and author assets")

    young_css = (ROOT / "docs" / "assets" / "young-lawyers-event.css").read_text(encoding="utf-8")
    camp_css = (ROOT / "docs" / "assets" / "camp.css").read_text(encoding="utf-8")
    site_css = (ROOT / "docs" / "assets" / "style.css").read_text(encoding="utf-8")
    require("--yl-accent: var(--accent);" in young_css, "young-lawyer topic must inherit the site accent")
    require("--camp-accent: var(--accent);" in camp_css, "camp topic must inherit the site accent")
    require("--event-accent: var(--accent);" in site_css, "event banners must inherit the site accent")
    require("event-banner--young" not in site_css, "individual banners must not define their own palette")
    require("#ffb86b" not in young_css and "#3bd29f" not in camp_css,
            "topic-specific accent colors must be removed")

    tcjtl = TCJTL_PAGE.read_text(encoding="utf-8")
    require("天驰君泰杭州分所第一届青训营" in tcjtl and "AI 法律服务产品设计训练营" in tcjtl,
            "camp primary title must use the full event name")
    require("两天共创 · 十项法律 AI 能力" in tcjtl,
            "camp former primary headline must become the subtitle")
    require("camp.css?v=2303-theme2" in tcjtl, "camp topic must bust the cached palette")

    common = (ROOT / "docs" / "assets" / "common.js").read_text(encoding="utf-8")
    require("young-lawyers-ai-skills-2026.html" not in common,
            "event topic must not occupy the global navigation")
    print("PASS: 217 library additions retained, 95-entry attributed topic, anonymization, index, and banner order")


if __name__ == "__main__":
    main()

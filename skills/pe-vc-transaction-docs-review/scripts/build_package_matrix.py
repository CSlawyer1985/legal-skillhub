#!/usr/bin/env python3
"""Build a conservative cross-document definitions, rights, facts and cap-table matrix."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

import build_document_map
import contract_clause_model
import contract_ontology
import extract_contract_text


ZH_DEFINITION_RE = re.compile(
    r"[“\"](?P<term>[^”\"]{1,80})[”\"]\s*(?:系指|是指|指|系)\s*(?P<value>[^。；;\n]{2,500})",
    re.IGNORECASE,
)
EN_DEFINITION_RE = re.compile(
    r"[“\"](?P<term>[^”\"]{1,80})[”\"]\s+(?:means|shall mean|has the meaning(?: given)?(?: to it)?(?: in)?)\s+(?P<value>[^.;\n]{2,500})",
    re.IGNORECASE,
)

AMOUNT_PATTERNS = [
    (
        "new_registered_capital",
        re.compile(r"新增注册资本(?:为|：|:)?\s*(?:人民币|RMB)?\s*(?P<amount>[0-9,，.]+)\s*(?P<unit>亿元|万元|元)", re.I),
    ),
    (
        "registered_capital",
        re.compile(r"(?<!新增)注册资本(?:为|：|:)?\s*(?:人民币|RMB)?\s*(?P<amount>[0-9,，.]+)\s*(?P<unit>亿元|万元|元)", re.I),
    ),
    (
        "investment_amount",
        re.compile(r"(?:投资款|投资金额|认购价款)(?:为|：|:)?\s*(?:人民币|RMB)?\s*(?P<amount>[0-9,，.]+)\s*(?P<unit>亿元|万元|元)", re.I),
    ),
    (
        "investment_amount",
        re.compile(r"投资人以\s*(?:人民币|RMB)?\s*(?P<amount>[0-9,，.]+)\s*(?P<unit>亿元|万元|元)\s*认购", re.I),
    ),
    (
        "pre_money_valuation",
        re.compile(r"(?:投前估值|pre-money valuation)(?:为|：|:)?\s*(?:人民币|RMB)?\s*(?P<amount>[0-9,，.]+)\s*(?P<unit>亿元|万元|元)", re.I),
    ),
    (
        "post_money_valuation",
        re.compile(r"(?:投后估值|post-money valuation)(?:为|：|:)?\s*(?:人民币|RMB)?\s*(?P<amount>[0-9,，.]+)\s*(?P<unit>亿元|万元|元)", re.I),
    ),
]

PERCENT_HOLDING_RE = re.compile(
    r"(?P<prefix>[^，,；;。\n]{1,60}?)(?:持有|持股)(?:公司|本公司)?\s*(?P<pct>[0-9]+(?:\.[0-9]+)?)\s*%",
    re.IGNORECASE,
)
DIRECT_ROLE_PERCENT_RE = re.compile(
    r"(?P<party>创始股东|创始人|投资人|投资者|员工持股平台|ESOP|founders?|investors?)\s*"
    r"(?P<pct>[0-9]+(?:\.[0-9]+)?)\s*%",
    re.IGNORECASE,
)

NEGATIVE_CUE_RE = re.compile(
    r"未(?:约定|赋予|设置|包含|规定|体现)|不(?:设(?:任何)?|享有|适用|包括)|不存在|没有|"
    r"无任何[^，,。；;]{0,16}(?:权|安排|条款)|"
    r"does\s+not|do\s+not|not\s+include|no\s+(?:separate|special|express)",
    re.IGNORECASE,
)
ADVERSATIVE_RE = re.compile(r"但(?:是)?|然而|不过|except|provided\s+that", re.IGNORECASE)
CONTROL_FILE_RE = re.compile(r"(?:matter[_ -]?instructions?|readme|next[_ -]?conversation|prompt|matter[_ -]?profile)", re.I)
LITIGATION_RE = re.compile(
    r"(?:向|提交|由)[^。；;\n]{0,40}(?:人民法院|法院)[^。；;\n]{0,20}(?:起诉|诉讼|审理|管辖)|"
    r"(?:诉讼解决|exclusive\s+jurisdiction\s+of[^.;\n]{0,80}courts?|submit[^.;\n]{0,80}courts?|litigation)",
    re.IGNORECASE,
)


def extract_file(path: Path) -> dict:
    if path.suffix.lower() == ".docx":
        return extract_contract_text.extract_docx(path, "full")
    if path.suffix.lower() == ".pdf":
        return extract_contract_text.extract_pdf(path)
    return extract_contract_text.extract_doc_or_other(path)


def normalize_term(value: object) -> str:
    return re.sub(r"[^0-9a-z\u3400-\u9fff]+", "", str(value or "").lower())


def extract_definitions(file_name: str, clauses: list[dict[str, object]]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    seen: set[tuple[str, str, str]] = set()
    for clause in clauses:
        text = str(clause["text"])
        for pattern in (ZH_DEFINITION_RE, EN_DEFINITION_RE):
            for match in pattern.finditer(text):
                term = match.group("term").strip()
                value = match.group("value").strip()
                key = (normalize_term(term), normalize_term(value), str(clause["clause_id"]))
                if key in seen:
                    continue
                seen.add(key)
                records.append(
                    {
                        "file": file_name,
                        "term": term,
                        "normalized_term": normalize_term(term),
                        "value": value,
                        "normalized_value": normalize_term(value),
                        "clause": clause["label"],
                        "location": clause["start_location"],
                    }
                )
    return records


def definition_conflicts(definitions: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for item in definitions:
        grouped[str(item["normalized_term"])].append(item)
    conflicts = []
    for normalized_term, items in grouped.items():
        if len({str(item["file"]) for item in items}) < 2:
            continue
        values = {str(item["normalized_value"]) for item in items}
        if len(values) <= 1:
            continue
        minimum_similarity = 1.0
        for index, left in enumerate(items):
            for right in items[index + 1 :]:
                minimum_similarity = min(
                    minimum_similarity,
                    contract_clause_model.text_similarity(left["value"], right["value"]),
                )
        if minimum_similarity >= 0.9:
            continue
        conflicts.append(
            {
                "type": "definition_mismatch",
                "term": items[0]["term"],
                "normalized_term": normalized_term,
                "minimum_similarity": round(minimum_similarity, 6),
                "occurrences": items,
                "review_required": True,
            }
        )
    return conflicts


def amount_to_yuan(amount: str, unit: str) -> str | None:
    multipliers = {"元": Decimal(1), "万元": Decimal(10000), "亿元": Decimal(100000000)}
    try:
        value = Decimal(amount.replace(",", "").replace("，", "")) * multipliers[unit]
    except (InvalidOperation, KeyError):
        return None
    return format(value.normalize(), "f")


def extract_amount_facts(file_name: str, clauses: list[dict[str, object]]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    seen: set[tuple[str, str, str]] = set()
    for clause in clauses:
        text = str(clause["text"])
        for fact_type, pattern in AMOUNT_PATTERNS:
            for match in pattern.finditer(text):
                amount = match.group("amount")
                unit = match.group("unit")
                normalized = amount_to_yuan(amount, unit)
                if normalized is None:
                    continue
                key = (fact_type, normalized, str(clause["clause_id"]))
                if key in seen:
                    continue
                seen.add(key)
                records.append(
                    {
                        "file": file_name,
                        "fact_type": fact_type,
                        "raw": match.group(0),
                        "value_yuan": normalized,
                        "clause": clause["label"],
                        "location": clause["start_location"],
                    }
                )
    return records


def fact_conflicts(facts: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for item in facts:
        grouped[str(item["fact_type"])].append(item)
    conflicts = []
    for fact_type, items in grouped.items():
        if len({str(item["file"]) for item in items}) < 2:
            continue
        if len({str(item["value_yuan"]) for item in items}) <= 1:
            continue
        conflicts.append(
            {
                "type": "numeric_fact_mismatch",
                "fact_type": fact_type,
                "occurrences": items,
                "review_required": True,
            }
        )
    return conflicts


def clean_party(value: str) -> str:
    text = re.sub(r"^(?:附件[^：:]{0,20}[：:]|交割后|其中|由|则|及|和)+", "", value.strip())
    text = re.sub(r".*[：:（(]", "", text)
    text = re.sub(r"(?:公司|本公司)?交割后$", "", text)
    text = re.sub(r"\s+", " ", text).strip(" ：:,，;；()（）")
    if len(text) > 35:
        text = text[-35:]
    return text


def extract_cap_table(file_name: str, clauses: list[dict[str, object]]) -> dict[str, object]:
    holdings: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for clause in clauses:
        text = str(clause["text"])
        matches = list(PERCENT_HOLDING_RE.finditer(text)) + list(DIRECT_ROLE_PERCENT_RE.finditer(text))
        for match in matches:
            raw_party = match.groupdict().get("party") or match.groupdict().get("prefix") or ""
            party = clean_party(raw_party)
            if not party:
                continue
            percentage = Decimal(match.group("pct"))
            key = (normalize_term(party), format(percentage.normalize(), "f"))
            if key in seen:
                continue
            seen.add(key)
            holdings.append(
                {
                    "file": file_name,
                    "party": party,
                    "normalized_party": normalize_term(party),
                    "percentage": float(percentage),
                    "clause": clause["label"],
                    "location": clause["start_location"],
                }
            )
    distinct_parties = {str(item["normalized_party"]) for item in holdings}
    total = sum(Decimal(str(item["percentage"])) for item in holdings) if holdings else Decimal(0)
    status = "insufficient_data"
    if len(distinct_parties) >= 2:
        if Decimal("99.95") <= total <= Decimal("100.05"):
            status = "balanced"
        elif total < Decimal("99.95"):
            status = "incomplete"
        else:
            status = "overallocated"
    return {
        "file": file_name,
        "holdings": holdings,
        "holding_count": len(holdings),
        "total_percentage": float(total),
        "status": status,
    }


def cap_table_conflicts(cap_tables: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for table in cap_tables:
        for item in table["holdings"]:
            grouped[str(item["normalized_party"])].append(item)
    conflicts = []
    for normalized_party, items in grouped.items():
        if len({str(item["file"]) for item in items}) < 2:
            continue
        if len({str(item["percentage"]) for item in items}) <= 1:
            continue
        conflicts.append(
            {
                "type": "cap_table_percentage_mismatch",
                "party": items[0]["party"],
                "normalized_party": normalized_party,
                "occurrences": items,
                "review_required": True,
            }
        )
    for table in cap_tables:
        if table["status"] in {"incomplete", "overallocated"}:
            conflicts.append(
                {
                    "type": "cap_table_total_mismatch",
                    "file": table["file"],
                    "total_percentage": table["total_percentage"],
                    "status": table["status"],
                    "review_required": True,
                }
            )
    return conflicts


def family_status(text: str, aliases: list[str]) -> dict[str, object]:
    text = re.sub(r"\s+", " ", text)
    sentences = [segment.strip() for segment in re.split(r"[。；;]+", text) if segment.strip()]
    positive: list[str] = []
    negative: list[str] = []
    for sentence in sentences:
        lowered = sentence.lower()
        for alias in aliases:
            alias_lower = alias.lower()
            start = 0
            while True:
                position = lowered.find(alias_lower, start)
                if position < 0:
                    break
                preceding = sentence[:position]
                cues = list(NEGATIVE_CUE_RE.finditer(preceding))
                is_negative = False
                if cues:
                    tail = preceding[cues[-1].end() :]
                    is_negative = not ADVERSATIVE_RE.search(tail)
                target = negative if is_negative else positive
                if sentence not in target:
                    target.append(sentence[:240])
                start = position + len(alias_lower)
    if positive and negative:
        status = "mixed"
    elif positive:
        status = "present"
    elif negative:
        status = "explicitly_absent"
    else:
        status = "unmentioned"
    return {"status": status, "positive_evidence": positive[:3], "negative_evidence": negative[:3]}


def build_rights_matrix(documents: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    conflicts: list[dict[str, object]] = []
    for family, aliases in contract_ontology.CLAUSE_FAMILIES.items():
        states = []
        for document in documents:
            state = family_status(str(document["text"]), aliases)
            states.append({"file": document["file"], **state})
        rows.append({"family": family, "documents": states})
        positive_files = {str(item["file"]) for item in states if item["positive_evidence"]}
        negative_files = {str(item["file"]) for item in states if item["negative_evidence"]}
        if any(positive_file != negative_file for positive_file in positive_files for negative_file in negative_files):
            conflicts.append(
                {
                    "type": "rights_presence_mismatch",
                    "family": family,
                    "documents": states,
                    "review_required": True,
                }
            )
    return rows, conflicts


def qualitative_facts(documents: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    facts = []
    for document in documents:
        text = str(document["text"]).lower()
        mechanisms = []
        if "仲裁" in text or "arbitration" in text:
            mechanisms.append("arbitration")
        if LITIGATION_RE.search(text):
            mechanisms.append("litigation")
        if mechanisms:
            facts.append({"file": document["file"], "fact_type": "dispute_mechanism", "values": mechanisms})
        governing = []
        if "中华人民共和国法律" in text or "prc law" in text or "laws of china" in text:
            governing.append("PRC")
        if "香港法律" in text or "hong kong law" in text:
            governing.append("Hong Kong")
        if "开曼" in text or "cayman" in text:
            governing.append("Cayman")
        if governing:
            facts.append({"file": document["file"], "fact_type": "governing_law", "values": governing})
    conflicts = []
    for fact_type in {str(item["fact_type"]) for item in facts}:
        items = [item for item in facts if item["fact_type"] == fact_type]
        signatures = {tuple(item["values"]) for item in items}
        if len(items) >= 2 and len(signatures) > 1:
            conflicts.append(
                {
                    "type": "qualitative_fact_mismatch",
                    "fact_type": fact_type,
                    "occurrences": items,
                    "review_required": True,
                }
            )
    return facts, conflicts


def build_matrix(paths: list[Path]) -> dict[str, object]:
    files, input_errors = build_document_map.collect_with_diagnostics(paths)
    documents: list[dict[str, object]] = []
    excluded_control_files: list[str] = []
    extraction_errors = []
    for error in input_errors:
        prefix, separator, raw_path = error.partition(": ")
        extraction_errors.append(f"{prefix}: {Path(raw_path).name}" if separator else error)
    definitions: list[dict[str, object]] = []
    facts: list[dict[str, object]] = []
    cap_tables: list[dict[str, object]] = []
    for path in files:
        classification = build_document_map.classify_with_evidence(path)
        if classification["type"] == "other" and CONTROL_FILE_RE.search(path.name):
            excluded_control_files.append(path.name)
            continue
        result = extract_file(path)
        if result.get("error") or not result.get("paragraphs"):
            extraction_errors.append(f"{path.name}: {result.get('error') or 'no extractable text'}")
            continue
        clauses = contract_clause_model.build_clauses(result["paragraphs"])
        full_text = "\n".join(str(paragraph.get("text", "")) for paragraph in result["paragraphs"])
        document = {
            "file": path.name,
            "document_type": classification["type"],
            "extraction_method": result.get("method"),
            "clause_count": len(clauses),
            "text": full_text,
        }
        documents.append(document)
        definitions.extend(extract_definitions(path.name, clauses))
        facts.extend(extract_amount_facts(path.name, clauses))
        cap_tables.append(extract_cap_table(path.name, clauses))

    if not documents:
        extraction_errors.append("no in-scope extractable transaction documents")

    rights_matrix, rights_conflicts = build_rights_matrix(documents)
    qualitative, qualitative_conflicts = qualitative_facts(documents)
    definition_mismatch = definition_conflicts(definitions)
    numeric_mismatch = fact_conflicts(facts)
    cap_table_mismatch = cap_table_conflicts(cap_tables)
    conflicts = [
        *definition_mismatch,
        *numeric_mismatch,
        *cap_table_mismatch,
        *rights_conflicts,
        *qualitative_conflicts,
    ]
    public_documents = [{key: value for key, value in document.items() if key != "text"} for document in documents]
    return {
        "scope": "cross-document candidate consistency matrix",
        "documents": public_documents,
        "document_count": len(documents),
        "excluded_control_files": excluded_control_files,
        "extraction_errors": extraction_errors,
        "definitions": definitions,
        "definition_conflicts": definition_mismatch,
        "numeric_facts": facts,
        "numeric_fact_conflicts": numeric_mismatch,
        "cap_tables": cap_tables,
        "cap_table_conflicts": cap_table_mismatch,
        "rights_matrix": rights_matrix,
        "rights_conflicts": rights_conflicts,
        "qualitative_facts": qualitative,
        "qualitative_fact_conflicts": qualitative_conflicts,
        "conflicts": conflicts,
        "conflict_count": len(conflicts),
        "limitations": [
            "All conflicts are candidate review leads, not legal conclusions.",
            "Definition and fact extraction is pattern-based and may miss tables, images, cross-references, or drafting variants.",
            "Cap-table arithmetic is evaluated only when at least two distinct percentage holdings are extractable.",
        ],
    }


def md_escape(value: object) -> str:
    return str(value or "").replace("|", "/").replace("\n", "<br>")


def as_markdown(result: dict[str, object]) -> str:
    lines = [
        "# Cross-Document Consistency Matrix",
        "",
        f"- Documents read: {result['document_count']}",
        f"- Extraction errors: {len(result['extraction_errors'])}",
        f"- Candidate conflicts: {result['conflict_count']}",
        "",
        "## Candidate Conflicts",
        "",
        "| Type | Subject | Evidence |",
        "|---|---|---|",
    ]
    for conflict in result["conflicts"]:
        subject = conflict.get("term") or conflict.get("fact_type") or conflict.get("party") or conflict.get("family") or conflict.get("file")
        evidence = conflict.get("occurrences") or conflict.get("documents") or conflict.get("total_percentage")
        lines.append(f"| {md_escape(conflict['type'])} | {md_escape(subject)} | {md_escape(json.dumps(evidence, ensure_ascii=False))} |")
    lines.extend(["", "## Rights Matrix", "", "| Family | " + " | ".join(doc["file"] for doc in result["documents"]) + " |"])
    lines.append("|---|" + "---|" * len(result["documents"]))
    for row in result["rights_matrix"]:
        states = {item["file"]: item["status"] for item in row["documents"]}
        lines.append("| " + md_escape(row["family"]) + " | " + " | ".join(md_escape(states.get(doc["file"], "-")) for doc in result["documents"]) + " |")
    if result["extraction_errors"]:
        lines.extend(["", "## Extraction Errors", ""])
        lines.extend(f"- {error}" for error in result["extraction_errors"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--format", choices=["json", "md"], default="json")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--strict", action="store_true", help="Fail if any in-scope file cannot be extracted.")
    parser.add_argument("--fail-on-conflict", action="store_true", help="Return non-zero when candidate conflicts are found.")
    args = parser.parse_args()
    result = build_matrix([path.expanduser() for path in args.inputs])
    rendered = json.dumps(result, ensure_ascii=False, indent=2) if args.format == "json" else as_markdown(result)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    if args.strict and result["extraction_errors"]:
        return 1
    if args.fail_on_conflict and result["conflict_count"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

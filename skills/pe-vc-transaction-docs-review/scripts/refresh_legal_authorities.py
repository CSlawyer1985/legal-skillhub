#!/usr/bin/env python3
"""Validate the legal-authority registry and optionally check official URL health."""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import json
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


DATA = Path(__file__).resolve().parents[1] / "references" / "legal-authorities.json"
ALLOWED_STATUSES = {
    "effective",
    "effective guidance",
    "not yet effective",
    "draft - nonbinding",
    "superseded/repealed",
    "status unverified",
}
REQUIRED_FIELDS = {
    "id",
    "title",
    "authority_level",
    "status",
    "promulgated_date",
    "effective_date",
    "official_url",
    "aliases",
    "topics",
    "provisions",
    "review_use",
    "caveat",
}


def parse_date(value: object) -> dt.date | None:
    if value in {None, ""}:
        return None
    return dt.date.fromisoformat(str(value))


def official_hostname(hostname: str, allowlist: list[str]) -> bool:
    hostname = hostname.lower().rstrip(".")
    return any(hostname == domain or hostname.endswith(f".{domain}") for domain in allowlist)


def validate_registry(data: dict, today: dt.date | None = None) -> dict[str, object]:
    today = today or dt.date.today()
    errors: list[str] = []
    warnings: list[str] = []
    if data.get("schema_version") != 2:
        errors.append("schema_version must be 2")
    allowlist = data.get("official_domain_allowlist")
    if not isinstance(allowlist, list) or not allowlist:
        errors.append("official_domain_allowlist must be a non-empty list")
        allowlist = []
    coverage = data.get("coverage_topics")
    if not isinstance(coverage, list) or not coverage:
        errors.append("coverage_topics must be a non-empty list")
        coverage = []
    coverage_matrix = data.get("coverage_matrix")
    if not isinstance(coverage_matrix, dict):
        errors.append("coverage_matrix must map every coverage topic to authority IDs")
        coverage_matrix = {}
    try:
        last_verified = parse_date(data.get("last_verified"))
    except ValueError:
        last_verified = None
        errors.append("last_verified must be an ISO date")
    age_days = (today - last_verified).days if last_verified else None
    if age_days is not None and age_days < 0:
        errors.append("last_verified cannot be in the future")
    if age_days is not None and age_days > 90:
        warnings.append(f"registry is {age_days} days old and requires official-source refresh")
    authorities = data.get("authorities")
    if not isinstance(authorities, list) or not authorities:
        errors.append("authorities must be a non-empty list")
        authorities = []
    identifiers: set[str] = set()
    authority_statuses: dict[str, str] = {}
    effective_count = 0
    draft_count = 0
    for index, authority in enumerate(authorities, start=1):
        label = str(authority.get("id") or f"row {index}")
        missing = REQUIRED_FIELDS - set(authority)
        if missing:
            errors.append(f"{label}: missing {sorted(missing)}")
        if label in identifiers:
            errors.append(f"duplicate authority id: {label}")
        identifiers.add(label)
        status = str(authority.get("status", ""))
        authority_statuses[label] = status
        if status not in ALLOWED_STATUSES:
            errors.append(f"{label}: invalid status {status!r}")
        if status.startswith("effective"):
            effective_count += 1
        if status == "draft - nonbinding":
            draft_count += 1
        try:
            promulgated = parse_date(authority.get("promulgated_date"))
            effective = parse_date(authority.get("effective_date"))
        except ValueError as exc:
            errors.append(f"{label}: invalid date: {exc}")
            continue
        if not promulgated:
            errors.append(f"{label}: promulgated_date is required")
        if status.startswith("effective"):
            if not effective:
                errors.append(f"{label}: effective authority requires effective_date")
            elif effective > today:
                errors.append(f"{label}: marked effective before effective_date {effective}")
        if status == "not yet effective" and (not effective or effective <= today):
            errors.append(f"{label}: not-yet-effective status conflicts with effective_date")
        if status == "draft - nonbinding" and effective:
            errors.append(f"{label}: draft must not have an effective_date")
        url = str(authority.get("official_url", ""))
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname:
            errors.append(f"{label}: official_url must be HTTPS")
        elif allowlist and not official_hostname(parsed.hostname, [str(domain) for domain in allowlist]):
            errors.append(f"{label}: non-official hostname {parsed.hostname}")
        if not isinstance(authority.get("aliases"), list) or not authority.get("aliases"):
            errors.append(f"{label}: aliases must be non-empty")
        if not isinstance(authority.get("topics"), list) or not authority.get("topics"):
            errors.append(f"{label}: topics must be non-empty")
    coverage_details = []
    if set(coverage_matrix) - set(coverage):
        errors.append(f"coverage_matrix has unknown topics: {sorted(set(coverage_matrix) - set(coverage))}")
    for topic in coverage:
        linked = coverage_matrix.get(topic)
        if not isinstance(linked, list) or not linked:
            errors.append(f"coverage topic has no linked authorities: {topic}")
            linked = []
        unknown = sorted({str(identifier) for identifier in linked} - identifiers)
        if unknown:
            errors.append(f"coverage topic {topic} references unknown authorities: {unknown}")
        current = [
            str(identifier)
            for identifier in linked
            if authority_statuses.get(str(identifier), "").startswith("effective")
        ]
        if linked and not current:
            errors.append(f"coverage topic has no effective authority: {topic}")
        coverage_details.append(
            {
                "topic": topic,
                "authority_ids": [str(identifier) for identifier in linked],
                "effective_authority_ids": current,
                "covered": bool(linked) and not unknown and bool(current),
            }
        )
    next_refresh_due = last_verified + dt.timedelta(days=90) if last_verified else None
    return {
        "ok": not errors,
        "schema_version": data.get("schema_version"),
        "last_verified": last_verified.isoformat() if last_verified else None,
        "age_days": age_days,
        "next_refresh_due": next_refresh_due.isoformat() if next_refresh_due else None,
        "authority_count": len(identifiers),
        "effective_count": effective_count,
        "draft_count": draft_count,
        "coverage_topic_count": len(coverage) if isinstance(coverage, list) else 0,
        "coverage_complete": bool(coverage_details) and all(item["covered"] for item in coverage_details),
        "coverage_details": coverage_details,
        "errors": errors,
        "warnings": warnings,
    }


def title_anchor(title: str) -> str:
    cleaned = re.sub(r"[《》（）()\s0-9—－-]", "", title)
    return cleaned[:8]


def check_url(authority: dict, timeout: float) -> dict[str, object]:
    authority_id = str(authority.get("id", ""))
    url = str(authority.get("official_url", ""))
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; VCPEAuthorityRefresh/1.0)",
            "Accept": "text/html,application/xhtml+xml,application/pdf,*/*;q=0.8",
        },
    )
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            status = int(getattr(response, "status", 200))
            final_url = response.geturl()
            body = response.read(512 * 1024)
            content_type = response.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        check_status = "broken" if exc.code in {404, 410} else "inconclusive"
        return {
            "id": authority_id,
            "url": url,
            "reachable": False,
            "check_status": check_status,
            "http_status": exc.code,
            "error": str(exc),
        }
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {
            "id": authority_id,
            "url": url,
            "reachable": False,
            "check_status": "inconclusive",
            "http_status": None,
            "error": str(exc),
        }
    anchor = title_anchor(str(authority.get("title", "")))
    anchor_match: bool | None = None
    if "html" in content_type.lower():
        decoded = body.decode("utf-8", errors="ignore")
        anchor_match = bool(anchor and anchor in decoded)
    return {
        "id": authority_id,
        "url": url,
        "final_url": final_url,
        "http_status": status,
        "content_type": content_type,
        "reachable": 200 <= status < 400,
        "check_status": "reachable" if 200 <= status < 400 else "inconclusive",
        "title_anchor": anchor,
        "title_anchor_match": anchor_match,
    }


def refresh_report(
    data: dict,
    *,
    check_urls: bool,
    timeout: float,
    workers: int,
    selected_ids: set[str] | None = None,
    require_all_reachable: bool = False,
) -> dict[str, object]:
    report = validate_registry(data)
    authorities = [item for item in data.get("authorities", []) if not selected_ids or item.get("id") in selected_ids]
    if selected_ids:
        found = {str(item.get("id")) for item in authorities}
        missing = sorted(selected_ids - found)
        if missing:
            report["errors"].append(f"unknown authority IDs: {missing}")
            report["ok"] = False
    checks: list[dict[str, object]] = []
    if check_urls and authorities:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(check_url, authority, timeout): authority for authority in authorities}
            for future in concurrent.futures.as_completed(futures):
                checks.append(future.result())
        checks.sort(key=lambda item: str(item["id"]))
        broken = [item for item in checks if item.get("check_status") == "broken"]
        inconclusive = [item for item in checks if item.get("check_status") == "inconclusive"]
        if broken:
            report["errors"].append(f"{len(broken)} official URL(s) returned 404/410")
            report["ok"] = False
        if inconclusive:
            message = f"{len(inconclusive)} official URL check(s) were blocked or inconclusive; verify those sources manually"
            if require_all_reachable:
                report["errors"].append(message)
                report["ok"] = False
            else:
                report["warnings"].append(message)
        unmatched = [item for item in checks if item.get("title_anchor_match") is False]
        if unmatched:
            report["warnings"].append(
                f"{len(unmatched)} reachable HTML page(s) did not expose the title anchor; manual content/status verification required"
            )
    report.update(
        {
            "checked_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "url_checks_requested": check_urls,
            "url_check_count": len(checks),
            "reachable_url_count": sum(item.get("check_status") == "reachable" for item in checks),
            "inconclusive_url_count": sum(item.get("check_status") == "inconclusive" for item in checks),
            "broken_url_count": sum(item.get("check_status") == "broken" for item in checks),
            "url_checks": checks,
            "refresh_note": "URL health does not by itself prove current legal status; update last_verified only after official content/status review.",
        }
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA)
    parser.add_argument("--check-urls", action="store_true")
    parser.add_argument("--id", action="append", dest="ids")
    parser.add_argument("--timeout", type=float, default=12.0)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--require-all-reachable", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.timeout <= 0 or args.workers < 1:
        print("--timeout and --workers must be positive", file=sys.stderr)
        return 2
    try:
        data = json.loads(args.data.read_text(encoding="utf-8"))
        report = refresh_report(
            data,
            check_urls=args.check_urls,
            timeout=args.timeout,
            workers=args.workers,
            selected_ids=set(args.ids) if args.ids else None,
            require_all_reachable=args.require_all_reachable,
        )
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Could not refresh legal authorities: {exc}", file=sys.stderr)
        return 2
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

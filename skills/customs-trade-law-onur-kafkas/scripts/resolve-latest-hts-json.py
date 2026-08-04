#!/usr/bin/env python3
"""
Resolve the latest HTS JSON distribution from Data.gov catalog metadata.

This is a non-authoritative helper. It discovers and prints metadata used by
the trade-law skill; legal reasoning and freshness analysis belong in the
methodology files and final work product.

Examples:
  python3 resolve-latest-hts-json.py
  python3 resolve-latest-hts-json.py --year 2026
  python3 resolve-latest-hts-json.py --metadata-file catalog-response.json --json
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_BASE_URL = "https://catalog.data.gov"
DEFAULT_QUERY = "Harmonized Tariff Schedule of the United States"
USER_AGENT = "trade-law-hts-json-resolver/1.0"


@dataclass(frozen=True)
class Distribution:
    title: str
    download_url: str
    format: str
    raw: dict[str, Any]


@dataclass(frozen=True)
class Dataset:
    title: str
    name: str
    catalog_url: str
    source_landing_url: str
    modified_or_harvested: str
    distributions: list[Distribution]
    raw: dict[str, Any]


@dataclass(frozen=True)
class Selection:
    dataset: Dataset
    distribution: Distribution
    revision_number: int | None
    reason: str


def fetch_json(url: str, timeout: int = 30) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def load_json_file(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def catalog_search_url(base_url: str, query: str, year: int, rows: int) -> str:
    params = {
        "q": f"{query} {year}",
        "per_page": str(rows),
    }
    return f"{base_url.rstrip('/')}/search?{urllib.parse.urlencode(params)}"


def ckan_catalog_search_url(base_url: str, query: str, year: int, rows: int) -> str:
    params = {
        "q": f"{query} {year}",
        "rows": str(rows),
    }
    return f"{base_url.rstrip('/')}/api/3/action/package_search?{urllib.parse.urlencode(params)}"


def fetch_catalog_payload(base_url: str, query: str, year: int, rows: int) -> dict[str, Any]:
    try:
        return fetch_json(catalog_search_url(base_url, query, year, rows))
    except Exception:
        # Compatibility fallback for older CKAN-shaped metadata mirrors.
        return fetch_json(ckan_catalog_search_url(base_url, query, year, rows))


def dataset_catalog_url(dataset: dict[str, Any], base_url: str) -> str:
    dcat = dataset.get("dcat") if isinstance(dataset.get("dcat"), dict) else {}
    name = string_value(
        dataset.get("name")
        or dataset.get("slug")
        or dataset.get("identifier")
        or dataset.get("id")
        or dcat.get("identifier")
        or dcat.get("@id")
    )
    if name:
        return f"{base_url.rstrip('/')}/dataset/{urllib.parse.quote(name)}"
    return base_url.rstrip("/")


def source_landing_url(dataset: dict[str, Any]) -> str:
    dcat = dataset.get("dcat") if isinstance(dataset.get("dcat"), dict) else {}
    return string_value(
        dataset.get("url")
        or dataset.get("landingPage")
        or dcat.get("landingPage")
        or dcat.get("accessURL")
    )


def string_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return ", ".join(string_value(item) for item in value if string_value(item))
    return str(value).strip()


def first_present(mapping: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = string_value(mapping.get(key))
        if value:
            return value
    return ""


def normalize_distribution(resource: dict[str, Any]) -> Distribution | None:
    title = first_present(resource, ("name", "title", "description"))
    download_url = first_present(resource, ("url", "downloadURL", "downloadUrl", "accessURL", "accessUrl"))
    fmt = first_present(resource, ("format", "mediaType", "mimetype"))
    if not download_url:
        return None
    return Distribution(
        title=title or download_url.rsplit("/", 1)[-1],
        download_url=download_url,
        format=fmt,
        raw=resource,
    )


def normalize_ckan_dataset(dataset: dict[str, Any], base_url: str) -> Dataset:
    dcat = dataset.get("dcat") if isinstance(dataset.get("dcat"), dict) else {}
    resources = dataset.get("resources") or dataset.get("distribution") or dcat.get("distribution") or []
    distributions = [
        normalized
        for resource in resources
        if isinstance(resource, dict)
        for normalized in [normalize_distribution(resource)]
        if normalized is not None
    ]
    modified = first_present(
        dataset,
        (
            "last_harvested_date",
            "metadata_modified",
            "metadata_created",
            "modified",
            "issued",
            "harvest_source_title",
            "harvest_object_id",
        ),
    ) or first_present(dcat, ("modified", "issued"))
    return Dataset(
        title=first_present(dataset, ("title", "name")) or first_present(dcat, ("title",)),
        name=string_value(dataset.get("name") or dataset.get("slug") or dataset.get("id") or dcat.get("identifier")),
        catalog_url=dataset_catalog_url(dataset, base_url),
        source_landing_url=source_landing_url(dataset),
        modified_or_harvested=modified,
        distributions=distributions,
        raw=dataset,
    )


def normalize_datasets(payload: dict[str, Any], base_url: str) -> list[Dataset]:
    if "result" in payload and isinstance(payload["result"], dict):
        result = payload["result"]
        records = result.get("results") or result.get("packages") or []
        return [normalize_ckan_dataset(record, base_url) for record in records if isinstance(record, dict)]

    if "dataset" in payload and isinstance(payload["dataset"], list):
        return [normalize_ckan_dataset(record, base_url) for record in payload["dataset"] if isinstance(record, dict)]

    if "results" in payload and isinstance(payload["results"], list):
        return [normalize_ckan_dataset(record, base_url) for record in payload["results"] if isinstance(record, dict)]

    if "title" in payload or "resources" in payload or "distribution" in payload:
        return [normalize_ckan_dataset(payload, base_url)]

    return []


def title_contains_hts(dataset: Dataset) -> bool:
    title = dataset.title.lower()
    return "harmonized tariff schedule" in title or "hts" in title


def has_year(text: str, year: int) -> bool:
    return str(year) in text


def is_json_distribution(distribution: Distribution) -> bool:
    haystack = " ".join(
        [
            distribution.title.lower(),
            distribution.format.lower(),
            distribution.download_url.lower(),
        ]
    )
    return "json" in haystack or haystack.endswith(".json")


def revision_number(distribution: Distribution) -> int | None:
    patterns = (
        r"\bHTS\s+Revision\s+(\d+)\s*\(JSON\)",
        r"\bRevision\s+(\d+)\b",
        r"_revision_(\d+)_json",
        r"revision[-_ ]?(\d+)",
    )
    haystack = f"{distribution.title} {distribution.download_url}"
    for pattern in patterns:
        match = re.search(pattern, haystack, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def is_basic_edition(distribution: Distribution) -> bool:
    haystack = f"{distribution.title} {distribution.download_url}".lower()
    return "basic edition" in haystack or "basic" in haystack


def select_latest_json(datasets: list[Dataset], year: int) -> Selection:
    relevant = [dataset for dataset in datasets if title_contains_hts(dataset) and has_year(dataset.title, year)]
    if not relevant:
        relevant = [dataset for dataset in datasets if title_contains_hts(dataset)]
    if not relevant:
        raise ValueError("No HTS dataset found in catalog metadata")

    candidates: list[tuple[Dataset, Distribution, int | None]] = []
    for dataset in relevant:
        for distribution in dataset.distributions:
            if is_json_distribution(distribution):
                candidates.append((dataset, distribution, revision_number(distribution)))

    current_year_revisions = [
        item
        for item in candidates
        if item[2] is not None
        and has_year(f"{item[0].title} {item[1].title} {item[1].download_url}", year)
    ]
    if current_year_revisions:
        dataset, distribution, rev = max(current_year_revisions, key=lambda item: item[2] or -1)
        return Selection(dataset, distribution, rev, "highest current-year HTS Revision N (JSON)")

    current_year_basic = [
        item
        for item in candidates
        if is_basic_edition(item[1])
        and has_year(f"{item[0].title} {item[1].title} {item[1].download_url}", year)
    ]
    if current_year_basic:
        dataset, distribution, rev = current_year_basic[0]
        return Selection(dataset, distribution, rev, "current-year Basic Edition (JSON); no current-year revision JSON found")

    any_revisions = [item for item in candidates if item[2] is not None]
    if any_revisions:
        dataset, distribution, rev = max(any_revisions, key=lambda item: item[2] or -1)
        return Selection(dataset, distribution, rev, "highest revision JSON found, but current-year match was not confirmed")

    if candidates:
        dataset, distribution, rev = candidates[0]
        return Selection(dataset, distribution, rev, "JSON distribution found, but revision number was not identified")

    raise ValueError("No JSON distribution found in HTS dataset metadata")


def selection_to_dict(selection: Selection, year: int) -> dict[str, Any]:
    return {
        "dataset_title": selection.dataset.title,
        "catalog_url": selection.dataset.catalog_url,
        "source_landing_url": selection.dataset.source_landing_url,
        "catalog_checked_or_harvested": selection.dataset.modified_or_harvested or "not available",
        "selected_revision_title": selection.distribution.title,
        "revision_number": selection.revision_number,
        "json_download_url": selection.distribution.download_url,
        "analysis_date": dt.date.today().isoformat(),
        "hts_year": year,
        "selection_reason": selection.reason,
    }


def print_human(result: dict[str, Any]) -> None:
    print("Latest HTS JSON selection")
    print(f"Dataset title: {result['dataset_title']}")
    print(f"Catalog URL: {result['catalog_url']}")
    print(f"Source landing URL: {result['source_landing_url'] or 'not available'}")
    print(f"Catalog checked/harvested: {result['catalog_checked_or_harvested']}")
    print(f"Selected revision: {result['selected_revision_title']}")
    print(f"Revision number: {result['revision_number'] if result['revision_number'] is not None else 'not identified'}")
    print(f"JSON download URL: {result['json_download_url']}")
    print(f"Analysis date: {result['analysis_date']}")
    print(f"HTS year: {result['hts_year']}")
    print(f"Selection reason: {result['selection_reason']}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=dt.date.today().year, help="HTS year to prefer")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Data.gov catalog base URL")
    parser.add_argument("--query", default=DEFAULT_QUERY, help="Catalog search query")
    parser.add_argument("--rows", type=int, default=25, help="Number of catalog rows to request")
    parser.add_argument("--metadata-file", help="Read catalog metadata JSON from a local file instead of fetching")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        if args.metadata_file:
            payload = load_json_file(args.metadata_file)
        else:
            payload = fetch_catalog_payload(args.base_url, args.query, args.year, args.rows)
        datasets = normalize_datasets(payload, args.base_url)
        selection = select_latest_json(datasets, args.year)
        result = selection_to_dict(selection, args.year)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_human(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

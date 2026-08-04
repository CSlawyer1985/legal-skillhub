#!/usr/bin/env python3
"""Validate legal category coverage declarations for baozheng-skills."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


REQUIRED_CATEGORIES = {
    "婚姻家庭": ["离婚"],
    "刑事案件": ["刑事", "取保候审"],
    "劳动纠纷": ["劳动", "仲裁"],
    "合同纠纷": ["合同", "违约"],
    "公司企业": ["公司", "股权"],
    "债权债务": ["债权", "借贷"],
    "房产纠纷": ["房产", "房屋"],
    "交通事故": ["交通事故", "车祸"],
    "继承": ["继承", "遗嘱"],
    "征地拆迁": ["征收", "拆迁"],
    "建筑工程": ["建筑", "工程"],
    "医疗纠纷": ["医疗纠纷", "医疗损害"],
    "损害赔偿": ["损害赔偿", "人身损害"],
    "行政纠纷": ["行政复议", "行政诉讼"],
    "环境保护": ["环境", "污染"],
    "知识产权": ["知识产权", "商标"],
    "保险纠纷": ["保险", "理赔"],
    "证券投资": ["证券", "投资"],
    "互联网纠纷": ["互联网", "网络侵权"],
    "人格尊严": ["人格", "名誉权"],
    "涉外纠纷": ["涉外", "送达"],
    "消费权益": ["消费", "退一赔三"],
}

REQUIRED_ROUTES = [
    "module-a-consultation.md",
    "module-b-complaint.md",
    "module-c-analysis.md",
    "module-d-criminal.md",
]


@dataclass(frozen=True)
class CoverageValidationResult:
    name: str
    missing: list[str]

    @property
    def passed(self) -> bool:
        return not self.missing


def resolve_skill_root(skill_root: str | None) -> Path:
    if skill_root:
        return Path(skill_root).resolve()
    return Path(__file__).resolve().parents[1]


def read_required_files(skill_root: Path) -> dict[str, str]:
    paths = {
        "coverage": skill_root / "references" / "shared-category-coverage.md",
        "activation": skill_root / "references" / "shared-activation-rules.md",
        "skill": skill_root / "SKILL.md",
        "readme": skill_root / "README.md",
    }
    return {name: path.read_text(encoding="utf-8") for name, path in paths.items()}


def validate_category(name: str, keywords: list[str], texts: dict[str, str]) -> CoverageValidationResult:
    missing: list[str] = []
    coverage_text = texts["coverage"]
    activation_text = texts["activation"]

    if name not in coverage_text:
        missing.append("coverage.category")

    for keyword in keywords:
        if keyword not in coverage_text and keyword not in activation_text:
            missing.append(f"keyword.{keyword}")

    return CoverageValidationResult(name=name, missing=missing)


def validate_routes(texts: dict[str, str]) -> CoverageValidationResult:
    combined = "\n".join(texts.values())
    missing = [route for route in REQUIRED_ROUTES if route not in combined]
    return CoverageValidationResult(name="routes", missing=missing)


def validate_version_marker(texts: dict[str, str]) -> CoverageValidationResult:
    missing: list[str] = []
    if "shared-category-coverage.md" not in texts["skill"]:
        missing.append("skill.reference")
    expected_count = len(REQUIRED_CATEGORIES)
    if f"{expected_count}类法律领域覆盖" not in texts["readme"]:
        missing.append(f"readme.coverage_note(expected {expected_count}类)")
    return CoverageValidationResult(name="version_marker", missing=missing)


def validate_category_coverage(skill_root: Path) -> list[CoverageValidationResult]:
    texts = read_required_files(skill_root)
    results = [
        validate_category(name, keywords, texts)
        for name, keywords in REQUIRED_CATEGORIES.items()
    ]
    results.append(validate_routes(texts))
    results.append(validate_version_marker(texts))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate legal category coverage declarations.")
    parser.add_argument("--skill-root", default=None, help="Path to baozheng-skills root")
    args = parser.parse_args()

    skill_root = resolve_skill_root(args.skill_root)
    results = validate_category_coverage(skill_root)
    failures = [item for item in results if not item.passed]

    for item in results:
        status = "OK" if item.passed else "FAIL"
        detail = "" if item.passed else " missing=" + ",".join(item.missing)
        print(f"{status} {item.name}{detail}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

# -*- coding: utf-8 -*-
"""
LexFolio CLI entry point.

Usage:
    python run.py input.md [-o output.pdf] [-s B] [-p noto] [--preset executive]
    python run.py input.md -t opinion         # use legal opinion template
    python run.py --demo -t memo              # generate demo with memo template
    python run.py --list-presets              # list all presets
    python run.py --list-templates            # list all templates
"""

import argparse
import os
import sys

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from engine.api import md_to_pdf
from engine.theme import ThemeLoader


DEMO_MARKDOWN = """\
---
doc_type: opinion
color_scheme: B
font_provider: noto
title: Legal Analysis on Cross-border Data Transfer Compliance
author: Jane Doe, Attorney at Law
date: June 15, 2026
ref_no: LEGAL-OP-2026-015
addressee: XX Corp.
confidential: true
firm_name_cn: "Example Law Firm"
firm_name_en: "Example Law Firm"
---

# I. Background

Example Law Firm (hereinafter "the Firm") is retained by XX Corp. (hereinafter "the Client") to provide legal analysis on the compliance of its cross-border data transfer practices. Based on the Personal Information Protection Law and the Data Security Law of the People's Republic of China, the Firm has conducted a compliance review of the Client's existing cross-border data transfer procedures.

## II. Legal Basis

### (1) Personal Information Protection Law

> Article 38: Where a personal information handler needs to provide personal information to an overseas recipient due to business or other needs, it shall meet one of the following conditions: passing a security assessment organized by the national cyberspace administration; obtaining personal information protection certification from a professional institution; or signing a standard contract with the overseas recipient.

> Article 40: Critical information infrastructure operators and personal information handlers processing personal information up to the quantity prescribed by the national cyberspace administration shall store personal information collected and generated within the territory of the People's Republic of China.

### (2) Relevant Case Law

> "The court holds that transferring personal information overseas without a security assessment violates the mandatory provisions of Article 38 of the Personal Information Protection Law, and such transfer lacks a lawful basis." -- (2025) Jing 0491 Min Chu 12345

### (3) Data Security Law

As a **data handler**, the Client shall comply with Article 21 of the Data Security Law regarding data classification and graded protection.

## III. Analysis and Recommendations

| Risk Level | Risk Item | Recommended Action |
|---|---|---|
| High | Cross-border transfer without security assessment | Immediately file for data export security assessment |
| Medium | Incomplete cross-border transfer contract terms | Supplement Standard Contractual Clauses (SCC) |
| Medium | Missing data classification labels | Establish internal data classification system |
| Low | Insufficient employee data protection awareness | Conduct data compliance training |

## IV. Key Highlights

**Analysis**: Data export security assessment is the most urgent compliance obligation. Under the Measures for Security Assessment of Outbound Data Cross-border Transfer, personal information handlers processing personal information of over 1 million individuals shall declare a data export security assessment when providing personal information overseas.

This is the **key** conclusion reached by the Firm based on existing regulations and judicial practice: the Client should complete the assessment filing within *90 days*.

## V. Conclusion

In summary, the Client is advised to complete the following three remediation tasks within **90 days**: first, initiate the data export security assessment filing procedure; second, sign standard contractual clauses compliant with national cyberspace administration standards with overseas recipients; third, establish a sound data classification and grading management system.

---

<!-- sigfooter -->
"""


def write_demo_file(output_dir: str) -> str:
    """Write the built-in demo markdown to a temporary .md file."""
    demo_path = os.path.join(output_dir, "_demo.md")
    with open(demo_path, "w", encoding="utf-8") as f:
        f.write(DEMO_MARKDOWN)
    return demo_path


def list_presets():
    """List all available typography presets."""
    theme = ThemeLoader()
    presets = theme.list_presets()
    print("[LexFolio] Available presets ({}):\n".format(len(presets)))
    print("  {:<14s} {:<10s} {:<8s} {}".format("Name", "Label", "Category", "Description"))
    print("  " + "-" * 70)
    for p in presets:
        print("  {:<14s} {:<10s} {:<8s} {}".format(
            p["name"], p["label"], p["category"], p["description"]
        ))
    print("\nUsage: python run.py input.md --preset executive")
    print("      or set in front matter: layout_preset: executive")


def list_templates():
    """List all available document templates."""
    theme = ThemeLoader()
    templates = theme.list_templates()
    print("[LexFolio] Available templates ({}):\n".format(len(templates)))
    print("  {:<12s} {:<12s} {}".format("Name", "Label", "Description"))
    print("  " + "-" * 60)
    for t in templates:
        print("  {:<12s} {:<12s} {}".format(
            t["name"], t["label"], t["description"]
        ))
    print("\nUsage: python run.py input.md -t opinion")
    print("      or set in front matter: template: opinion")


def main():
    parser = argparse.ArgumentParser(
        description="LexFolio - Markdown to PDF typesetting engine for legal documents"
    )
    parser.add_argument("input", nargs="?", help="Markdown input file path")
    parser.add_argument("-o", "--output", help="PDF output path (default: same name .pdf)")
    parser.add_argument("-s", "--scheme", choices=["A", "B", "C"],
                        help="Color scheme (A indigo / B teal / C cobalt)")
    parser.add_argument("-p", "--provider", choices=["noto", "founder"],
                        help="Font provider (noto: open-source Noto SC / "
                             "founder: alias of noto, kept for compatibility)")
    parser.add_argument("--preset",
                        choices=["standard", "executive", "mobile", "editorial",
                                 "academic", "deep", "matrix", "redline"],
                        help="Typography preset")
    parser.add_argument("-t", "--template",
                        choices=["opinion", "memo", "review", "analysis"],
                        help="Document template")
    parser.add_argument("--demo", action="store_true",
                        help="Generate PDF using built-in demo content")
    parser.add_argument("--list-presets", action="store_true",
                        help="List all available presets")
    parser.add_argument("--list-templates", action="store_true",
                        help="List all available templates")

    args = parser.parse_args()

    if args.list_presets:
        list_presets()
        return

    if args.list_templates:
        list_templates()
        return

    if args.demo:
        print("[LexFolio] Using built-in demo...")
        if args.template:
            print("[LexFolio] Template: {}".format(args.template))
        if args.preset and args.preset != "standard":
            print("[LexFolio] Preset: {}".format(args.preset))
        demo_path = write_demo_file(PROJECT_DIR)
        if args.output:
            out_path = args.output
        elif args.template:
            out_path = os.path.join(PROJECT_DIR, "_demo_{}.pdf".format(args.template))
        elif args.preset and args.preset != "standard":
            out_path = os.path.join(PROJECT_DIR, "_demo_{}.pdf".format(args.preset))
        else:
            out_path = os.path.join(PROJECT_DIR, "_demo_output.pdf")
        output = md_to_pdf(
            demo_path,
            output_path=out_path,
            color_scheme=args.scheme,
            font_provider=args.provider,
            preset=args.preset,
            template=args.template,
        )
        print("[LexFolio] PDF generated: {}".format(output))
        return

    if not args.input:
        parser.error("Please specify a Markdown input file, or use --demo")

    if not os.path.exists(args.input):
        print("[LexFolio] Error: file not found {}".format(args.input), file=sys.stderr)
        sys.exit(1)

    output = md_to_pdf(
        args.input,
        output_path=args.output,
        color_scheme=args.scheme,
        font_provider=args.provider,
        preset=args.preset,
        template=args.template,
    )
    print("[LexFolio] PDF generated: {}".format(output))


if __name__ == "__main__":
    main()

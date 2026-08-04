---
name: legal-tos-differ
description: Fetches Terms of Service documents, stores snapshots, and performs semantic diffing to identify meaningful legal changes across Privacy Risks, Financial Changes, and User Rights categories.
tools:
  - name: add_url
    description: Adds a URL to the tracked list of legal documents.
    arguments:
      - name: url
        description: "URL of the Terms of Service or legal document to track."
        type: string
        required: true
      - name: label
        description: "Human-readable label for the document (e.g., 'Acme Corp TOS')."
        type: string
        required: false
    execution:
      command: node {{SKILL_DIR}}/handler.js add --url "{{url}}" --label "{{label}}"
      output_format: markdown

  - name: list_tracked
    description: Lists all tracked URLs and their last snapshot dates.
    arguments: []
    execution:
      command: node {{SKILL_DIR}}/handler.js list
      output_format: markdown

  - name: fetch_current
    description: Fetches the current version of a tracked document and saves a snapshot without comparing.
    arguments:
      - name: url
        description: "URL to fetch (must be a tracked URL)."
        type: string
        required: true
    execution:
      command: node {{SKILL_DIR}}/handler.js fetch --url "{{url}}"
      output_format: markdown

  - name: diff
    description: Fetches the current version of a tracked document and outputs a semantic comparison prompt against the previous snapshot. The Claude Code runtime performs the analysis, categorizing changes into Privacy Risks, Financial Changes, and User Rights.
    arguments:
      - name: url
        description: "URL to diff (must be a tracked URL)."
        type: string
        required: true
    execution:
      command: node {{SKILL_DIR}}/handler.js diff --url "{{url}}"
      output_format: markdown

  - name: remove_url
    description: Removes a URL from the tracked list and deletes its snapshots.
    arguments:
      - name: url
        description: "URL to remove from tracking."
        type: string
        required: true
    execution:
      command: node {{SKILL_DIR}}/handler.js remove --url "{{url}}"
      output_format: markdown
---

# Legal/TOS Diff-er

This skill tracks changes in Terms of Service and legal documents by fetching pages, extracting the legal text, and comparing versions semantically.

## What It Does

- **Fetches** legal documents from tracked URLs
- **Extracts** clean legal text, stripping navigation, ads, and page noise
- **Stores** timestamped snapshots for historical comparison
- **Compares** versions using semantic analysis (not just text diffs)
- **Categorizes** changes into Privacy Risks, Financial Changes, and User Rights

## How It Works

1. Use `add_url` to start tracking a legal document
2. Use `fetch_current` to capture the first snapshot
3. Later, use `diff` to fetch the current version and compare it against the previous snapshot
4. The Claude Code runtime receives a structured comparison prompt and performs the semantic analysis

## Change Categories

| Category | Covers |
|----------|--------|
| **Privacy Risks** | Data collection, sharing, tracking, cookies, third-party data usage |
| **Financial Changes** | Pricing, fees, billing, refunds, payment terms, auto-renewal |
| **User Rights** | Account termination, content ownership, arbitration, governing law |

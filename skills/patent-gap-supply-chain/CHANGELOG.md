# Changelog

All notable changes to this skill are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/), adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-07-09

### Added
- Initial release of patent-gap-supply-chain skill
- 7-step workflow: trigger identification → patent gap confirmation → 5-lead parallel verification → fusion + confidence scoring → alternative-hypothesis check → counter-intelligence check → report output
- Bilingual trigger keywords (Chinese + English) in description for cross-locale agent triggering
- Applicability pre-check (Step 0): hardware / manufacturing / pharma / materials = strong; software / internet = weak; business-model innovation = not applicable
- `references/workflow.md`: detailed per-step operations with decision rules and tool invocation
- `references/checklists.md`: alternative-hypothesis checklist, counter-intelligence checklist, confidence scoring rules
- `examples/sample-output.md`: worked example showing the full report format for a fictional case
- Tool integration table covering tushare, PatSnap, Tianyancha, Qichacha, westock, WebSearch

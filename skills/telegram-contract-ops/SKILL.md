---
name: telegram-contract-ops
description: Telegram-based internal contract generation and eID intake workflow for Vietnamese operations. Use when setting up, migrating, or operating a bot that: (1) receives structured contract input in Telegram, (2) generates `.docx` contracts from a fixed company template, (3) receives Vietnamese electronic ID screenshots, OCRs key fields, and converts them into contract-ready input, and (4) routes behavior by Telegram group for contract workflows.
---

# Telegram Contract Ops

Use this skill for the combined Plan B + Plan C workflow.

## What this skill covers

- Parse standardized Telegram text blocks into contract data
- Generate `.docx` contracts from a company template
- Run Telegram bot flows for `/mauhopdong`, `/cccd`, `/cccd_debug`
- OCR Vietnamese electronic ID screenshots and convert them into Plan B input blocks
- Route contract behavior by Telegram group

## Current design boundary

### Plan B
- Input: structured Telegram-style `KEY: VALUE` block
- Output: `.docx` contract file

### Plan C
- Input: 1 screenshot of Vietnamese electronic ID from app
- OCR output fields:
  - `TEN`
  - `NGAY_SINH`
  - `CCCD`
  - `NGAY_CAP`
  - `THUONG_TRU`
  - `CHO_O_HIEN_TAI` when available
- Hardcode:
  - `NOI_CAP = CTCCS QLHC VTTXH`
- User confirms/edits block before final contract generation

## Keep these outside the packaged skill
- Telegram bot token
- group chat IDs
- `.env.telegram`
- `.env.telegram.groups`
- OCR debug session artifacts
- state files and logs

## Included references
- `references/architecture.md` - flow overview and routing
- `references/deployment.md` - migration/install checklist
- `references/input-template.md` - canonical Telegram input block
- `references/clawhub.md` - publish/install/update commands via ClawHub
- `references/troubleshooting.md` - common runtime and routing issues
- `references/windows.md` - Windows-specific guidance
- `references/macos.md` - macOS-specific guidance

## Included assets/scripts
Read these only when needed:
- `scripts/` for generator/parser/bot helpers
- `assets/` for original `.docx` template
- `assets/windows/` for Windows example env files and quick-start PowerShell wrapper

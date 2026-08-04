# Telegram Contract Ops Architecture

## Purpose
Handle internal contract creation in Telegram.

## Groups
- Management group: reminders only (Plan A, outside this skill)
- Contract group: contract generation + eID OCR intake

## Plan B
1. User requests `/mauhopdong`
2. Bot returns canonical input block
3. User pastes filled block
4. Parser validates and maps data
5. Generator produces `.docx`
6. Bot returns file to Telegram

## Plan C
1. User sends `/cccd` or `/cccd_debug`
2. Bot asks for one electronic ID screenshot from app
3. OCR runs using Apple Vision
4. eID parser extracts main fields
5. Bot returns editable Plan B block
6. User sends corrected/completed block
7. Plan B generator returns `.docx`

## Current implementation assets in workspace
- `telegram-planb-bot.js`
- `plan-b-telegram-template.txt`
- `plan-b-telegram-to-docx.js`
- `plan-b-docx-generate.py`
- `plan-c-ocr.swift`
- `plan-c-eid-parse.js`

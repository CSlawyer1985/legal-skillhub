# Connector Degradation Policy

## Status Labels

- Connected: tool call actually succeeded in this run.
- Configured but unverified: configuration or credential appears present, but no successful call was made.
- Unavailable: tool is absent, credential missing, call failed, or network/data source unavailable.

Never call a connector "connected" merely because an MCP config, API key, or user statement exists.

## Retry And Timeout Rule

- Retry the same read-only request at most two times, and only when the failure is transient rather than caused by permissions, login, parameters, CAPTCHA, payment, or unsupported scope.
- Stop a single request after 30 seconds when the tool permits timeout control. Mark it `CONNECTOR-001` and continue the reliable local work described in `references/faq-and-troubleshooting.md`.
- Never broaden the query, upload more files, or ask for passwords, tokens, or verification codes merely to make a retry succeed.

## Legal Research

Connected:

- Use legal database results only after checking authority level, effective
  status, version/effective date, and pinpoint. Record the query/check date.

Configured but unverified:

- Mark legal basis as "to be verified".
- Do not make final statutory/case claims beyond general legal reasoning.
- Use `references/legal-authorities.json` only as a dated local registry and run
  `scripts/legal_authority_lookup.py --check-freshness`; refresh official sources
  when the registry is stale or a draft may have become final.

Unavailable:

- Use local article digest and general legal knowledge.
- Mark specific legal authorities as "[pending legal research]".

## Enterprise / QCC Data

Connected:

- Build entity fact pack with data source and query time.

Configured but unverified:

- Ask for entity materials or mark "[pending entity verification]".

Unavailable:

- Do not invent entity facts.
- Prepare a verification checklist: registered name, USCC, registered capital, shareholder structure, contribution status, legal representative, UBO, litigation/administrative risks, equity pledge/freeze.

## Document Tools

If Word-comment insertion or tracked changes cannot be performed:

- Produce a comment plan CSV/markdown table.
- State that the original document was not modified.
- Keep proposed wording complete and paste-ready.

If PDF text extraction is empty:

- Treat the PDF as scanned/image-only until proven otherwise.
- Run `scripts/ocr_pdf.py` to select an available local engine; it can delegate
  to `scripts/ocr_pdf_macos.py` on macOS or use OCRmyPDF/Tesseract when available.
- If OCR is not run or fails, mark the file as not substantively reviewed and request an OCR text layer or Word/native source file.
- Report the applicable `OCR-*` problem number and the concrete next step from `references/faq-and-troubleshooting.md`.

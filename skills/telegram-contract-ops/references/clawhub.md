# ClawHub Publish / Install Notes

## Install CLI

```bash
npm i -g clawhub
```

## Login for publish

```bash
clawhub login
clawhub whoami
```

## Publish this skill

```bash
clawhub publish ./skills/telegram-contract-ops --slug telegram-contract-ops --name "Telegram Contract Ops" --version 1.0.0 --changelog "Initial release: Telegram contract generation, eID OCR intake, structured docx output"
```

## Install on a new machine

```bash
npm i -g clawhub
clawhub install telegram-contract-ops
```

## Upgrade on a machine that already has it

```bash
clawhub update telegram-contract-ops
```

## Install a specific version

```bash
clawhub install telegram-contract-ops --version 1.0.0
```

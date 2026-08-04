# Contributing to LexFolio

Thank you for your interest in contributing! This document covers the development setup and contribution process.

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/GantianBro/LexFolio.git
cd LexFolio

# Install dependencies (includes dev dependencies)
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Linting

```bash
ruff check .
```

### Generating a Demo PDF

```bash
python run.py --demo -t opinion
```

This creates `_demo_output.pdf` in the project root — use it to verify your changes visually.

## Contribution Process

1. **Fork** the repository and create a feature branch
2. **Write code** following the existing style (ruff-enforced)
3. **Add tests** for new features or bug fixes
4. **Run tests** to ensure nothing is broken
5. **Generate a demo PDF** to verify visual output if your change affects rendering
6. **Submit a Pull Request** with a clear description of what and why

## Code Style

- Python code follows [PEP 8](https://peps.python.org/pep-0008/) (enforced by ruff)
- All code comments and docstrings should be in **English**
- No Chinese characters in code files (use i18n for user-facing strings if needed)
- Use ASCII straight quotes (`"` and `'`) only — no full-width quotes in code

## Adding New Features

### New Document Template

1. Create a JSON file in `templates/` (e.g. `templates/report.json`)
2. Define `name`, `label`, `description`, `doc_type`, and default configurations
3. Add the template name to `run.py` CLI choices if needed

### New Typography Preset

1. Add a new entry in `theme.json` → `typography_presets`
2. Define `label`, `category`, `description`, and `overrides`
3. Add the preset name to `run.py` CLI choices

### New Color Scheme

1. Add a new entry in `theme.json` → `color.schemes`
2. Define `name`, `tagline`, `primary`, `secondary`, `accent`

## Font Policy

**Never commit commercial fonts to this repository.**

Only fonts with licenses that permit free redistribution (OFL, Apache, MIT) are allowed. If you need to test with commercial fonts, configure them in your local `theme.json` and add them to `.gitignore`.

## Reporting Issues

When reporting a bug, please include:

1. The Markdown input file (or a minimal reproducer)
2. The command you ran
3. The expected vs. actual output
4. Your Python version and OS

## Code of Conduct

Be respectful and constructive. Harassment or discrimination of any kind will not be tolerated.

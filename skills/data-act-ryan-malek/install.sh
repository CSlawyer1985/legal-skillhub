#!/usr/bin/env bash
# install.sh — install the EU Data Act Skill into Claude Code.
#
# Usage:
#   bash install.sh             # install for current user (~/.claude)
#   bash install.sh --uninstall # remove the install (does not delete this folder)
#   bash install.sh --check     # show install status without changing anything
#
# What it does:
#   1. Symlinks this folder to ~/.claude/skills/data-act-ryan-malek/ (so the skill auto-triggers)
#   2. Symlinks commands/data-act-ryan-malek.md to ~/.claude/commands/data-act-ryan-malek.md (so /data-act-ryan-malek works)
#
# The script uses symlinks so that updates to this folder propagate immediately.
# To install a fixed copy instead, set COPY=1 in the environment.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DEST="${HOME}/.claude/skills/data-act-ryan-malek"
CMD_DEST="${HOME}/.claude/commands/data-act-ryan-malek.md"
CMD_SRC="${SCRIPT_DIR}/commands/data-act-ryan-malek.md"

mode="${1:-install}"

case "$mode" in
  --uninstall|uninstall)
    echo "Removing skill links..."
    [[ -L "$SKILL_DEST" ]] && rm "$SKILL_DEST" && echo "  removed: $SKILL_DEST" || echo "  not a symlink (skipping): $SKILL_DEST"
    [[ -L "$CMD_DEST" ]] && rm "$CMD_DEST" && echo "  removed: $CMD_DEST" || echo "  not a symlink (skipping): $CMD_DEST"
    echo "Done. Source folder $SCRIPT_DIR is unchanged."
    exit 0
    ;;
  --check|check)
    echo "Source folder: $SCRIPT_DIR"
    if [[ -L "$SKILL_DEST" ]]; then
      target=$(readlink "$SKILL_DEST")
      if [[ "$target" == "$SCRIPT_DIR" ]]; then
        echo "  [OK] Skill symlink: $SKILL_DEST → $SCRIPT_DIR"
      else
        echo "  [WARN] Skill symlink points elsewhere: $SKILL_DEST → $target"
      fi
    elif [[ -e "$SKILL_DEST" ]]; then
      echo "  [WARN] Skill destination exists but is not a symlink: $SKILL_DEST"
    else
      echo "  [MISSING] Skill not installed at $SKILL_DEST"
    fi
    if [[ -L "$CMD_DEST" ]]; then
      target=$(readlink "$CMD_DEST")
      if [[ "$target" == "$CMD_SRC" ]]; then
        echo "  [OK] Slash-command symlink: $CMD_DEST → $CMD_SRC"
      else
        echo "  [WARN] Slash-command symlink points elsewhere: $CMD_DEST → $target"
      fi
    elif [[ -e "$CMD_DEST" ]]; then
      echo "  [WARN] Slash-command destination exists but is not a symlink: $CMD_DEST"
    else
      echo "  [MISSING] Slash command not installed at $CMD_DEST"
    fi
    if command -v pandoc >/dev/null 2>&1; then
      echo "  [OK] pandoc: $(pandoc --version | head -1)"
    else
      echo "  [MISSING] pandoc not installed (required for Word rendering)"
    fi
    if command -v python3 >/dev/null 2>&1; then
      echo "  [OK] python3: $(python3 --version 2>&1)"
    else
      echo "  [MISSING] python3 not installed (required for scripts)"
    fi
    exit 0
    ;;
  install|"")
    : # fall through
    ;;
  *)
    echo "Unknown option: $mode"
    echo "Usage: bash install.sh [--check | --uninstall]"
    exit 2
    ;;
esac

echo "Installing EU Data Act Skill..."
echo "  Source: $SCRIPT_DIR"
echo "  Skill destination: $SKILL_DEST"
echo "  Command destination: $CMD_DEST"
echo

# Create parent dirs
mkdir -p "${HOME}/.claude/skills" "${HOME}/.claude/commands"

# 1. Skill folder
if [[ -e "$SKILL_DEST" || -L "$SKILL_DEST" ]]; then
  echo "  $SKILL_DEST already exists. Replace? [y/N]"
  read -r reply
  if [[ "${reply,,}" != "y" ]]; then
    echo "  Skipped skill install."
  else
    rm -rf "$SKILL_DEST"
    if [[ "${COPY:-0}" == "1" ]]; then
      cp -R "$SCRIPT_DIR" "$SKILL_DEST"
      echo "  Copied folder → $SKILL_DEST"
    else
      ln -s "$SCRIPT_DIR" "$SKILL_DEST"
      echo "  Symlinked → $SKILL_DEST"
    fi
  fi
else
  if [[ "${COPY:-0}" == "1" ]]; then
    cp -R "$SCRIPT_DIR" "$SKILL_DEST"
    echo "  Copied folder → $SKILL_DEST"
  else
    ln -s "$SCRIPT_DIR" "$SKILL_DEST"
    echo "  Symlinked → $SKILL_DEST"
  fi
fi

# 2. Slash command file
if [[ -e "$CMD_DEST" || -L "$CMD_DEST" ]]; then
  echo "  $CMD_DEST already exists. Replace? [y/N]"
  read -r reply
  if [[ "${reply,,}" != "y" ]]; then
    echo "  Skipped command install."
  else
    rm -f "$CMD_DEST"
    if [[ "${COPY:-0}" == "1" ]]; then
      cp "$CMD_SRC" "$CMD_DEST"
      echo "  Copied command → $CMD_DEST"
    else
      ln -s "$CMD_SRC" "$CMD_DEST"
      echo "  Symlinked command → $CMD_DEST"
    fi
  fi
else
  if [[ "${COPY:-0}" == "1" ]]; then
    cp "$CMD_SRC" "$CMD_DEST"
    echo "  Copied command → $CMD_DEST"
  else
    ln -s "$CMD_SRC" "$CMD_DEST"
    echo "  Symlinked command → $CMD_DEST"
  fi
fi

echo
echo "Install complete."
echo

# --------------------------------------------------------------------------
# Dependency checks: pandoc (Word render), Python (scripts)
# --------------------------------------------------------------------------
if ! command -v pandoc >/dev/null 2>&1; then
  echo "WARNING: pandoc is NOT installed. Word rendering will fail until installed."
  case "$OSTYPE" in
    darwin*) echo "  Install on macOS:  brew install pandoc" ;;
    linux*)  echo "  Install on Linux:  sudo apt-get install pandoc  (or dnf / pacman / zypper)" ;;
    *)       echo "  Install:           https://pandoc.org/installing.html" ;;
  esac
  echo
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "WARNING: python3 is NOT on PATH. The skill's scripts require Python 3.10+."
  echo
fi

echo "Optional Python packages used by the scripts:"
echo "  pip install python-docx pypdf"
echo
echo "Verify install state any time with:"
echo "  bash $SCRIPT_DIR/install.sh --check"
echo
echo "Use in Claude Code:"
echo "  /data-act-ryan-malek classify [your offering description]"
echo "  /data-act-ryan-malek draft [what to draft]"
echo "  /data-act-ryan-malek lookup [Art. 25(2)(a)]"
echo "  /data-act-ryan-malek analyze [scenario]"
echo "  /data-act-ryan-malek audit [existing offering]"
echo
echo "Or just describe your task in chat — the skill auto-triggers on Data Act phrasing."

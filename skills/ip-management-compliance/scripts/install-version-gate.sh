#!/bin/sh
# 幂等安装版本漂移 pre-commit 闸门。仅当处于 git 仓库内时挂载（避免误建 .git）。
set -e

if ! command -v git >/dev/null 2>&1; then
  echo "未检测到 git，跳过安装。可手动校验版本：" >&2
  echo "  python ip-management-compliance/scripts/versions.py check" >&2
  exit 0
fi

ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$ROOT" ]; then
  echo "当前目录不是 git 仓库，跳过安装（pre-commit 闸门需 git 仓库才能激活）。" >&2
  echo "可手动校验版本：python ip-management-compliance/scripts/versions.py check" >&2
  exit 0
fi

HOOK_DIR="$ROOT/.git/hooks"
HOOK="$HOOK_DIR/pre-commit"
GATE="$ROOT/ip-management-compliance/scripts/pre-commit-version-gate"
MARKER="# version-gate: ip-management-compliance"

if [ ! -f "$GATE" ]; then
  echo "未找到 $GATE，跳过安装。" >&2
  exit 0
fi
chmod +x "$GATE" 2>/dev/null || true
mkdir -p "$HOOK_DIR"

if [ -f "$HOOK" ] && grep -qF "$MARKER" "$HOOK"; then
  echo "版本闸门已安装，跳过。"
  exit 0
fi

if [ -f "$HOOK" ]; then
  BACKUP="$HOOK_DIR/pre-commit.orig-$(date +%s)"
  cp "$HOOK" "$BACKUP"
  {
    printf '%s (chained)\n' "$MARKER"
    printf 'if [ -x "%s" ]; then "%s" || exit $?; fi\n' "$GATE" "$GATE"
    cat "$HOOK"
  } > "$HOOK.tmp"
  mv "$HOOK.tmp" "$HOOK"
  chmod +x "$HOOK"
  echo "已链式安装版本闸门（原 hook 备份于 $BACKUP）。"
else
  cp "$GATE" "$HOOK"
  chmod +x "$HOOK"
  echo "已安装版本闸门到 $HOOK。"
fi

#!/bin/sh
# One-Contract Rule Studio —— 一键启动
#
# 为什么需要它：交付说明此前只给了一条 `python3 scripts/open_rule_studio.py`，
# 而 macOS 自带的是 Python 3.9（且没有 jsonschema / referencing），照抄即失败。
# 本脚本负责挑一个 **≥3.10 且依赖齐备**的解释器，并在缺依赖时给出确切的安装命令，
# 不让人对着 "ModuleNotFoundError" 猜。
#
# 用法：
#   ./start.sh                          # 数据目录用默认（./.local_data）
#   ./start.sh --data-dir ~/某个空目录   # 指定外部数据目录（推荐；不得含真实客户资料）
#   ./start.sh --idle-timeout-seconds 3600
#
# 本脚本**不改动任何规则文件**，只挑选解释器并打开本地工作台。

set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
ENTRY="$HERE/scripts/open_rule_studio.py"

if [ ! -f "$ENTRY" ]; then
    echo "找不到 $ENTRY —— 请在解压出来的 one-contract 目录里运行本脚本。" >&2
    exit 2
fi

MIN_MAJOR=3
MIN_MINOR=10

ok_version() {
    "$1" -c "import sys; sys.exit(0 if sys.version_info[:2] >= ($MIN_MAJOR, $MIN_MINOR) else 1)" 2>/dev/null
}

has_deps() {
    "$1" -c "import jsonschema, referencing" 2>/dev/null
}

# 候选解释器：优先使用本目录已经准备好的隔离环境，再检查系统常见位置。
CANDIDATES="$HERE/.venv/bin/python python3"
for v in 3.13 3.12 3.11 3.10; do
    CANDIDATES="$CANDIDATES /opt/homebrew/bin/python$v /usr/local/bin/python$v"
done
if [ -d "$HOME/.pyenv/versions" ]; then
    for d in "$HOME"/.pyenv/versions/3.1[0-9]*; do
        [ -x "$d/bin/python" ] && CANDIDATES="$CANDIDATES $d/bin/python"
    done
fi

PY=""
for cand in $CANDIDATES; do
    command -v "$cand" >/dev/null 2>&1 || [ -x "$cand" ] || continue
    if ok_version "$cand" && has_deps "$cand"; then
        PY="$cand"
        break
    fi
done

if [ -z "$PY" ]; then
    echo "找不到可用的 Python（需要 ≥ ${MIN_MAJOR}.${MIN_MINOR} 且装有 jsonschema 与 referencing）。" >&2
    echo "" >&2
    echo "当前 python3 版本：$(command -v python3 >/dev/null 2>&1 && python3 -V 2>&1 || echo '未安装')" >&2
    echo "" >&2
    echo "请任选一种方式完成首次准备，然后再次双击或运行 start.sh：" >&2
    echo "" >&2
    echo "  方式一（推荐，不动系统）：" >&2
    echo "    python3.12 -m venv .venv" >&2
    echo "    ./.venv/bin/pip install -r scripts/requirements.txt" >&2
    echo "    ./start.sh" >&2
    echo "" >&2
    echo "  方式二（Homebrew，macOS）：" >&2
    echo "    brew install python@3.12" >&2
    echo "    /opt/homebrew/bin/python3.12 -m pip install jsonschema referencing" >&2
    echo "" >&2
    echo "  需要的两个依赖：jsonschema、referencing（其余均为 Python 标准库）。" >&2
    exit 3
fi

# `$PY` 后面**必须**用花括号闭合，且不能让它紧跟全角标点。
# macOS 自带 bash 3.2 在 **UTF-8 locale**（用户机器的默认）下会把多字节字符的
# 首字节吞进变量名：`$PY（` 被当成 `PY\xef`，于是 `set -u` 当场终止整个脚本
# （`line 77: PY: unbound variable`）——恰好在最该启动的那一刻崩，且只在
# LC_CTYPE=C 的 shell 里看不出来（我们此前的验证环境正是 C locale）。
echo "使用解释器：${PY}（$("${PY}" -V 2>&1)）"
# `-u`：不加的话，输出被重定向（写日志、交给别人代跑）时 URL 会滞留在缓冲区里，
# 人看不到地址就以为没启动。终端下本来就按行刷新，加上它只是让两种情形一致。
exec "$PY" -u "$ENTRY" "$@"

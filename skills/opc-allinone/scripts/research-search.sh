#!/usr/bin/env bash
set -euo pipefail

# Deep Research — CLI entry point
# Usage: ./search.sh -p "your research question" [options]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SKILL_FILE="$PROJECT_DIR/SKILL.md"

# Defaults
PROMPT=""
TASK_NAME=""
OUTPUT_DIR="$HOME/gemini-research"
MODEL="gemini-2.5-pro"
TIMEOUT=600
BACKGROUND=false
NOTIFY="auto"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

usage() {
    cat <<'USAGE'
Deep Research — Iterative multi-step web research via Gemini CLI

Usage:
  search.sh -p "research question" [options]

Required:
  -p, --prompt        Research question or topic

Options:
  -n, --task-name     Task name (default: timestamp)
  -o, --output-dir    Output directory (default: ~/gemini-research/)
  -m, --model         Gemini model (default: gemini-2.5-pro)
      --timeout       Timeout in seconds (default: 600)
  -b, --background    Run in background
      --notify        Notification: auto | none (default: auto)
  -h, --help          Show this help

Examples:
  search.sh -p "Latest developments in RISC-V consumer products 2026"
  search.sh -p "AI Agent 框架现状分析" -n "ai-agents" --background
  search.sh -p "Compare React vs Vue vs Svelte" -m gemini-2.5-flash
USAGE
    exit 0
}

log_info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -p|--prompt)     PROMPT="$2";     shift 2 ;;
        -n|--task-name)  TASK_NAME="$2";  shift 2 ;;
        -o|--output-dir) OUTPUT_DIR="$2"; shift 2 ;;
        -m|--model)      MODEL="$2";      shift 2 ;;
        --timeout)       TIMEOUT="$2";    shift 2 ;;
        -b|--background) BACKGROUND=true; shift ;;
        --notify)        NOTIFY="$2";     shift 2 ;;
        -h|--help)       usage ;;
        *)
            log_error "Unknown option: $1"
            usage
            ;;
    esac
done

# Validate required args
if [[ -z "$PROMPT" ]]; then
    log_error "Missing required argument: --prompt / -p"
    usage
fi

# Validate gemini CLI
if ! command -v gemini &>/dev/null; then
    log_error "gemini CLI not found in PATH"
    echo "Install: https://github.com/google-gemini/gemini-cli"
    exit 1
fi

# Validate SKILL.md exists
if [[ ! -f "$SKILL_FILE" ]]; then
    log_error "SKILL.md not found at $SKILL_FILE"
    exit 1
fi

# Generate task name if not provided
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
if [[ -z "$TASK_NAME" ]]; then
    TASK_NAME="research_${TIMESTAMP}"
else
    TASK_NAME="${TASK_NAME}_${TIMESTAMP}"
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

OUTPUT_FILE="$OUTPUT_DIR/${TASK_NAME}.md"
PID_FILE="$OUTPUT_DIR/${TASK_NAME}.pid"

# Extract SKILL.md body: skip YAML front matter (everything between the two --- lines)
SKILL_BODY="$(awk '/^---$/{n++; next} n>=2' "$SKILL_FILE")"

# Build the full prompt
FULL_PROMPT="$(cat <<PROMPT_EOF
${SKILL_BODY}

---

## Research Task

${PROMPT}

Please execute the 6-step research methodology above and produce the full report.
PROMPT_EOF
)"

# Notification function
send_notification() {
    local title="$1"
    local message="$2"

    case "$NOTIFY" in
        none)
            return 0
            ;;
        auto|*)
            send_system_notification "$title" "$message"
            ;;
    esac
}

send_system_notification() {
    local title="$1"
    local message="$2"

    case "$(uname -s)" in
        Darwin)
            osascript -e "display notification \"$message\" with title \"$title\"" 2>/dev/null || true
            ;;
        Linux)
            if command -v notify-send &>/dev/null; then
                notify-send "$title" "$message" 2>/dev/null || true
            fi
            ;;
    esac
}

# Run the research
run_research() {
    log_info "Starting deep search: $TASK_NAME"
    log_info "Model: $MODEL"
    log_info "Output: $OUTPUT_FILE"
    log_info "Timeout: ${TIMEOUT}s"
    echo ""

    local start_time
    start_time="$(date +%s)"

    if timeout "$TIMEOUT" gemini "$FULL_PROMPT" \
        --approval-mode yolo \
        -m "$MODEL" \
        --output-format text \
        2>/dev/null | tee "$OUTPUT_FILE"; then

        local end_time duration
        end_time="$(date +%s)"
        duration=$(( end_time - start_time ))

        log_ok "Research complete in ${duration}s"
        log_ok "Report saved to: $OUTPUT_FILE"

        send_notification \
            "Deep Research" \
            "Research complete: ${TASK_NAME} (${duration}s)"
    else
        local exit_code=$?
        if [[ $exit_code -eq 124 ]]; then
            log_error "Research timed out after ${TIMEOUT}s"
            send_notification \
                "Deep Research" \
                "Research timed out: ${TASK_NAME}"
        else
            log_error "Research failed with exit code $exit_code"
            send_notification \
                "Deep Research" \
                "Research failed: ${TASK_NAME}"
        fi
        return $exit_code
    fi
}

# Execute
if [[ "$BACKGROUND" == true ]]; then
    log_info "Running in background..."
    nohup bash -c "$(declare -f run_research send_notification send_system_notification log_info log_ok log_warn log_error); \
        TASK_NAME='$TASK_NAME' MODEL='$MODEL' OUTPUT_FILE='$OUTPUT_FILE' TIMEOUT='$TIMEOUT' \
        NOTIFY='$NOTIFY' \
        FULL_PROMPT=$(printf '%q' "$FULL_PROMPT") \
        RED='$RED' GREEN='$GREEN' YELLOW='$YELLOW' BLUE='$BLUE' NC='$NC' \
        run_research" \
        > "$OUTPUT_DIR/${TASK_NAME}.log" 2>&1 &
    BG_PID=$!
    echo "$BG_PID" > "$PID_FILE"
    log_ok "Background PID: $BG_PID"
    log_ok "PID file: $PID_FILE"
    log_ok "Log file: $OUTPUT_DIR/${TASK_NAME}.log"
else
    run_research
fi

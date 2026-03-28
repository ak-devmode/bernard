#!/usr/bin/env bash
# CC Dispatch wrapper — logs all Claude Code dispatches as JSONL.
#
# Usage:
#   bash tools/cc-dispatch.sh "summarize the repo"
#   bash tools/cc-dispatch.sh --session backend "implement pagination"
#
# Logs to: ~/.openclaw/logs/cc-dispatch.jsonl
# Format: {"ts":"...","task":"...","duration_ms":N,"exit_code":N,"output_chars":N}

set -euo pipefail

LOG_DIR="${HOME}/.openclaw/logs"
LOG_FILE="${LOG_DIR}/cc-dispatch.jsonl"
mkdir -p "${LOG_DIR}"

# Parse args
SESSION_FLAG=""
if [[ "${1:-}" == "--session" ]]; then
    SESSION_FLAG="-s ${2}"
    shift 2
fi

TASK="${*}"
if [[ -z "${TASK}" ]]; then
    echo "Usage: cc-dispatch.sh [--session name] \"task description\"" >&2
    exit 1
fi

# Timestamp
TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
START_MS=$(date +%s%3N 2>/dev/null || date +%s)

# Dispatch via acpx with JSON output
OUTPUT=$(acpx --format json claude ${SESSION_FLAG} exec "${TASK}" 2>&1) || EXIT_CODE=$?
EXIT_CODE=${EXIT_CODE:-0}

END_MS=$(date +%s%3N 2>/dev/null || date +%s)
DURATION_MS=$((END_MS - START_MS))
OUTPUT_CHARS=${#OUTPUT}

# Log entry
printf '{"ts":"%s","task":"%s","duration_ms":%d,"exit_code":%d,"output_chars":%d}\n' \
    "${TS}" \
    "$(echo "${TASK}" | sed 's/"/\\"/g')" \
    "${DURATION_MS}" \
    "${EXIT_CODE}" \
    "${OUTPUT_CHARS}" \
    >> "${LOG_FILE}"

# Return output to caller
echo "${OUTPUT}"
exit ${EXIT_CODE}

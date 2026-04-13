#!/usr/bin/env bash
# run-in-tmux.sh — Launch a geopol simulation in a detached tmux session
# with output logged to a file. Survives terminal crashes.
#
# Usage: ./scripts/run-in-tmux.sh <session-name> <logfile> <geopol-args...>
# Example: ./scripts/run-in-tmux.sh geopol-minimax /tmp/geopol-minimax.log --pool minimax --scenario iran-israel-war --report -v 3

set -euo pipefail

SESSION_NAME="${1:?Usage: $0 <session-name> <logfile> <geopol-args...>}"
LOGFILE="${2:?Usage: $0 <session-name> <logfile> <geopol-args...>}"
shift 2

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Kill any existing session with this name
tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true

# Ensure log directory exists and start fresh
mkdir -p "$(dirname "$LOGFILE")"
: > "$LOGFILE"

# Build the command to run inside tmux
# We use unbuffer (from expect) or script to disable output buffering so the
# log file gets lines in real time. Fall back to stdbuf, then raw.
if command -v unbuffer &>/dev/null; then
    WRAPPER="unbuffer"
elif command -v stdbuf &>/dev/null; then
    WRAPPER="stdbuf -oL -eL"
else
    WRAPPER=""
fi

CMD="cd '$REPO_DIR' && $WRAPPER geopol $* 2>&1 | tee '$LOGFILE'; echo '=== SIMULATION COMPLETE (exit \$?) ===' >> '$LOGFILE'"

# Launch in a detached tmux session
tmux new-session -d -s "$SESSION_NAME" bash -c "$CMD"

echo "Simulation launched in tmux session: $SESSION_NAME"
echo "Log file: $LOGFILE"
echo ""
echo "  Attach:  tmux attach -t $SESSION_NAME"
echo "  Follow:  tail -f $LOGFILE"
echo "  Kill:    tmux kill-session -t $SESSION_NAME"

#!/bin/bash
# Sync Google Sheet data with the Spectrum 2026 site
# Runs via cron every 30 minutes

cd /home/klh/Projects/football

LOGFILE="scripts/sync.log"
LOCKFILE="/tmp/spectrum-sync.lock"

# Prevent overlapping runs
if [ -f "$LOCKFILE" ]; then
  PID=$(cat "$LOCKFILE")
  if kill -0 "$PID" 2>/dev/null; then
    echo "=== Sync skipped at $(date) — previous run (PID $PID) still active ===" >> "$LOGFILE"
    exit 0
  else
    rm -f "$LOCKFILE"
  fi
fi

echo $$ > "$LOCKFILE"
trap "rm -f $LOCKFILE" EXIT

echo "=== Sync started at $(date) ===" >> "$LOGFILE"

/home/klh/.local/bin/claude -p "$(cat scripts/sync-prompt.md)" \
  --allowedTools 'Read,Write,Edit,Bash,Glob,Grep,mcp__google-sheets__*' \
  --max-turns 50 \
  >> "$LOGFILE" 2>&1

echo "=== Sync finished at $(date) ===" >> "$LOGFILE"
echo "" >> "$LOGFILE"

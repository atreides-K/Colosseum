#!/bin/bash
# Sync Google Sheet data with the Spectrum 2026 site
# Runs via cron every 4 hours

cd /home/klh/Projects/football

LOGFILE="scripts/sync.log"
echo "=== Sync started at $(date) ===" >> "$LOGFILE"

/home/klh/.local/bin/claude -p "$(cat scripts/sync-prompt.md)" \
  --allowedTools 'Read,Write,Edit,Bash,Glob,Grep,mcp__google-sheets__*' \
  --max-turns 50 \
  >> "$LOGFILE" 2>&1

echo "=== Sync finished at $(date) ===" >> "$LOGFILE"
echo "" >> "$LOGFILE"

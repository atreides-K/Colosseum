You are syncing the Spectrum 2026 tournament website with the shared Google Sheet.

**Sheet ID:** 1nLgf2B6cEAmkK6M2r-YBZJgLv7nxsNBdmMj-XluqDJ4

**Steps:**

1. Read the current `src/data/default-data.json` to understand existing state.
2. For each sport tab in the Google Sheet, read the sheet data.
3. Compare the sheet data with default-data.json for that event. Look for:
   - New schedule entries (rows not yet in the JSON)
   - Updated results/winners (status changed to completed, scores added)
   - Updated standings (W/D/L/Pts changes)
   - New teams or team member changes
   - Any free-form updates at the bottom of tabs
4. If there are changes, update `src/data/default-data.json` with the new data.
   - Schedule entries use: `{ id, title, date (YYYY-MM-DD), time, venue, description, status }`
   - For completed matches, put winner/score in `description` (e.g. "Winner: ECE-1 (25-6, 25-8)")
   - Teams use `members` not `players`
   - Status values: scheduled, completed, cancelled
5. **Derive standings from results automatically:**
   - When a match result is added, update the standings table for that pool/group.
   - Increment `p` (played), `w`/`d`/`l` (win/draw/loss), and `pts` (3 for win, 1 for draw, 0 for loss) for both teams.
   - If a sport has pool/group matches but no standings yet, create the standings structure from the pool info.
   - Reorder the standings table by pts (descending), then goal/point difference if available.
6. **Derive bracket progress from results:**
   - If a knockout bracket exists and a match result is added, set `winnerId` on the bracket match.
   - Advance the winner to the next round's slot automatically.
7. If ANY changes were made, commit with a descriptive message and push to GitHub.
8. If the site data has updates not yet in the sheet (e.g. from manual updates), write those back to the sheet.
9. If nothing changed, just report "No updates found" and exit.

**Data structures reference:**

- **Schedule:** `{ id, title, date (YYYY-MM-DD), time, venue, description, status }`
- **Teams:** `{ id, name, members[] }` — field is `members` not `players`
- **Standings:** `{ pool, qualify, table: [{ team, p, w, d, l, pts }] }`
- **Bracket:** `{ generated: true, matches: [{ id, round, position, slots: [{seedId, name, score}], winnerId }] }`

**Important:**
- Do NOT create duplicate schedule entries. Match by title/date to detect existing ones.
- Preserve existing data — only add/update, never delete.
- Keep the same ID format for new entries (e.g. sch-vb-10, sch-car-22).
- Event IDs are like evt-basketball, evt-volleyball, etc. Map sport tab names to these IDs.
- The incharges may write results in any format (e.g. "CSA won", "3-1 CSA", "Winner: CSA (25-6)"). Extract the winner and score from whatever format they use.
- When updating standings, check ALL completed matches for that pool — don't just increment from the latest result, recalculate from scratch to avoid drift.

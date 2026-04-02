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
5. If ANY changes were made, commit with a descriptive message and push to GitHub.
6. If the site data has updates not yet in the sheet (e.g. from manual updates), write those back to the sheet.
7. If nothing changed, just report "No updates found" and exit.

**Important:**
- Do NOT create duplicate schedule entries. Match by title/date to detect existing ones.
- Preserve existing data — only add/update, never delete.
- Keep the same ID format for new entries (e.g. sch-vb-10, sch-car-22).
- Event IDs are like evt-basketball, evt-volleyball, etc. Map sport tab names to these IDs.

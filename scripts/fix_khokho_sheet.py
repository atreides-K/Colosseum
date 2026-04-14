#!/usr/bin/env python3
"""Fix Kho-Kho Pool A standings (insert missing ICER row) and write sync log."""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta

CREDS_PATH = "/home/klh/.config/gcp/spectrum-492106-08db880f0334.json"
SHEET_ID = "1nLgf2B6cEAmkK6M2r-YBZJgLv7nxsNBdmMj-XluqDJ4"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def main():
    # Authenticate
    print("Authenticating with Google Sheets API...")
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SHEET_ID)

    # ── STEP 1: Fix Kho-Kho Pool A standings ──
    print("\n=== STEP 1: Fix Kho-Kho Pool A standings ===")
    kho = spreadsheet.worksheet("Kho-Kho")

    # Find Pool A standings location
    all_values = kho.get_all_values()
    pool_a_header_row = None
    for i, row in enumerate(all_values):
        if row[0] == "#" and row[1] == "Team" and row[2] == "P":
            # Check if the row above says "Pool A"
            if i > 0 and "Pool A" in all_values[i - 1][0]:
                pool_a_header_row = i + 1  # 1-indexed
                break

    if pool_a_header_row is None:
        print("ERROR: Could not find Pool A standings header row")
        return

    print(f"Found Pool A standings header at row {pool_a_header_row}")

    # Read current standings rows (header + up to 5 data rows)
    standings_start = pool_a_header_row + 1  # first data row after header
    print(f"Current Pool A data starts at row {standings_start}")

    # Show current state
    for i in range(standings_start - 1, min(standings_start + 3, len(all_values))):
        print(f"  Row {i+1}: {all_values[i][:7]}")

    # Check for merged cells in the Kho-Kho tab
    print("\nChecking for merged cells in the Kho-Kho tab...")
    sheet_metadata = spreadsheet.fetch_sheet_metadata()
    kho_sheet_id = kho.id
    merges = []
    for sheet in sheet_metadata.get("sheets", []):
        if sheet["properties"]["sheetId"] == kho_sheet_id:
            merges = sheet.get("merges", [])
            break

    if merges:
        print(f"Found {len(merges)} merged cell ranges in Kho-Kho tab")
        # Check if any merges overlap with Pool A standings area
        # Our write area: rows pool_a_header_row to pool_a_header_row+5, cols A-G (0-6)
        write_start_row = standings_start - 1  # 0-indexed
        write_end_row = standings_start + 4     # 0-indexed, exclusive
        conflicting = []
        for m in merges:
            mr_start = m.get("startRowIndex", 0)
            mr_end = m.get("endRowIndex", 0)
            mc_start = m.get("startColumnIndex", 0)
            mc_end = m.get("endColumnIndex", 0)
            # Check overlap with our write area (rows write_start_row..write_end_row, cols 0..7)
            if mr_start < write_end_row and mr_end > write_start_row and mc_start < 7:
                conflicting.append(m)
                print(f"  Conflicting merge: rows {mr_start}-{mr_end}, cols {mc_start}-{mc_end}")

        if conflicting:
            print("Unmerging conflicting cells before writing...")
            requests = []
            for m in conflicting:
                requests.append({
                    "unmergeCells": {
                        "range": {
                            "sheetId": kho_sheet_id,
                            "startRowIndex": m["startRowIndex"],
                            "endRowIndex": m["endRowIndex"],
                            "startColumnIndex": m["startColumnIndex"],
                            "endColumnIndex": m["endColumnIndex"],
                        }
                    }
                })
            spreadsheet.batch_update({"requests": requests})
            print("Unmerged successfully.")
        else:
            print("No conflicting merges in the standings area.")
    else:
        print("No merged cells found in Kho-Kho tab.")

    # Now insert the ICER row. Currently:
    #   Row standings_start:   1, Alumni, 1, 1, 0, 0, 2
    #   Row standings_start+1: 2, Civil,  2, 1, 0, 1, 2
    #   Row standings_start+2: 4, DESE,   0, 0, 0, 0, 0
    # We need to insert a row for ICER at standings_start+2 and push DESE down.

    # Insert a new row at position standings_start+2 (this shifts DESE down)
    icer_row_pos = standings_start + 2
    print(f"\nInserting new row at position {icer_row_pos} for ICER...")
    kho.insert_row(["3", "ICER", "1", "0", "0", "1", "0"], index=icer_row_pos)
    print("Inserted ICER row: #3, P=1, W=0, D=0, L=1, Pts=0")

    # DESE is now at row icer_row_pos+1, fix its rank to #4
    dese_row = icer_row_pos + 1
    print(f"Fixing DESE rank at row {dese_row} to #4...")
    kho.update_cell(dese_row, 1, "4")
    print("DESE rank fixed to #4.")

    print("\nPool A standings fix complete!")

    # ── STEP 2: Write sync log to README tab ──
    print("\n=== STEP 2: Write sync log to README tab ===")
    readme = spreadsheet.worksheet("README")
    readme_values = readme.get_all_values()

    # Find "SYNC LOG" section and the first empty row after log entries
    sync_log_row = None
    for i, row in enumerate(readme_values):
        if "SYNC LOG" in str(row[0]):
            sync_log_row = i + 1  # 1-indexed
            break

    if sync_log_row is None:
        print("ERROR: Could not find SYNC LOG section")
        return

    print(f"Found SYNC LOG header at row {sync_log_row}")

    # Find first empty row after the header row + column headers row + data rows
    first_empty = sync_log_row + 2  # skip header and column headers
    for i in range(sync_log_row + 1, len(readme_values)):  # 0-indexed
        row = readme_values[i]
        if any(cell.strip() for cell in row):
            first_empty = i + 2  # 1-indexed, next row after this one
        else:
            first_empty = i + 1  # 1-indexed, this empty row
            break
    else:
        first_empty = len(readme_values) + 1

    print(f"First empty row for new log entry: {first_empty}")

    # Get current IST time
    ist = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(ist)
    timestamp = now.strftime("2026-04-08 %H:%M IST")

    log_entry = [
        timestamp,
        "no changes",
        "Sheet and JSON already in sync. Fixed missing ICER row in Kho-Kho Pool A standings on sheet.",
    ]

    print(f"Writing log entry: {log_entry}")

    # Check for merges in README tab too
    readme_sheet_id = readme.id
    readme_merges = []
    for sheet in sheet_metadata.get("sheets", []):
        if sheet["properties"]["sheetId"] == readme_sheet_id:
            readme_merges = sheet.get("merges", [])
            break

    if readme_merges:
        write_row_0 = first_empty - 1  # 0-indexed
        conflicting_readme = [
            m for m in readme_merges
            if m.get("startRowIndex", 0) <= write_row_0 < m.get("endRowIndex", 0)
            and m.get("startColumnIndex", 0) < 3
        ]
        if conflicting_readme:
            print(f"Found {len(conflicting_readme)} conflicting merges in README sync log area, unmerging...")
            requests = [{
                "unmergeCells": {
                    "range": {
                        "sheetId": readme_sheet_id,
                        "startRowIndex": m["startRowIndex"],
                        "endRowIndex": m["endRowIndex"],
                        "startColumnIndex": m["startColumnIndex"],
                        "endColumnIndex": m["endColumnIndex"],
                    }
                }
            } for m in conflicting_readme]
            spreadsheet.batch_update({"requests": requests})
            print("Unmerged successfully.")

    cell_range = f"A{first_empty}:C{first_empty}"
    readme.update(cell_range, [log_entry])
    print(f"Sync log written to row {first_empty}.")

    print("\n=== All done! ===")


if __name__ == "__main__":
    main()

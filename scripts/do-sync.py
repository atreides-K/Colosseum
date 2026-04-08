#!/usr/bin/env python3
"""
Sync Google Sheet sport tabs with default-data.json for Spectrum 2026.

Reads each sport tab from the Google Sheet, compares with local JSON,
updates schedule entries, teams, standings, and bracket data.

Usage:
    python3 scripts/do-sync.py
    python3 scripts/do-sync.py --dry-run   # preview changes without writing
"""

import json
import os
import re
import sys
import unicodedata
from copy import deepcopy

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SHEET_ID = "1nLgf2B6cEAmkK6M2r-YBZJgLv7nxsNBdmMj-XluqDJ4"
CREDS_PATH = os.path.expanduser("~/.config/gcp/spectrum-492106-08db880f0334.json")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_PATH = os.path.join(PROJECT_DIR, "src", "data", "default-data.json")

# Sport abbreviations for generating schedule IDs
SPORT_ABBREV = {
    "basketball": "bb",
    "volleyball": "vb",
    "football": "fb",
    "carrom": "car",
    "chess": "ch",
    "badminton": "bad",
    "cycling": "cyc",
    "handball": "hb",
    "hockey": "hk",
    "kabaddi": "kab",
    "kho-kho": "kk",
    "lawn-tennis": "lt",
    "powerlifting": "pl",
    "snooker": "sn",
    "swimming": "sw",
    "table-tennis": "tt",
    "throwball": "tb",
    "athletics": "ath",
    "foosball": "foos",
    "ultimate-frisbee": "uf",
    "frisbee": "uf",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def strip_emoji(text):
    """Remove emoji and other non-alphanumeric leading chars from text."""
    if not text:
        return ""
    # Remove leading emoji/symbols
    cleaned = ""
    started = False
    for ch in text:
        cat = unicodedata.category(ch)
        if not started and cat.startswith("So"):
            continue
        started = True
        cleaned += ch
    return cleaned.strip()


TAB_TO_ID_OVERRIDES = {
    "ultimate frisbee": "evt-frisbee",
}

def tab_name_to_event_id(tab_name):
    """Convert a sheet tab name like 'Basketball' or 'Ultimate Frisbee' to 'evt-basketball'."""
    name = strip_emoji(tab_name).strip()
    # Remove trailing status like " — ONGOING", " - COMPLETED"
    name = re.split(r"\s*[—\-]\s*(ONGOING|COMPLETED|UPCOMING|CANCELLED)", name)[0].strip()
    key = name.lower()
    if key in TAB_TO_ID_OVERRIDES:
        return TAB_TO_ID_OVERRIDES[key]
    slug = key.replace(" ", "-")
    return f"evt-{slug}"


def normalize_title(title):
    """Normalize a schedule title for comparison."""
    if not title:
        return ""
    t = title.strip().lower()
    t = re.sub(r"\s+", " ", t)
    # Normalize common abbreviations for matching
    t = re.sub(r"\bsf(\d)", r"semi-final \1", t)
    t = re.sub(r"\bsemi[\s-]*final\s*(\d)", r"semi-final \1", t)
    t = re.sub(r"\bqf(\d)", r"quarter-final \1", t)
    t = re.sub(r"\bquarter[\s-]*final\s*(\d)", r"quarter-final \1", t)
    return t


def get_next_schedule_id(event, abbrev):
    """Generate the next schedule ID for an event."""
    existing_ids = [s.get("id", "") for s in event.get("schedule", [])]
    max_num = 0
    prefix = f"sch-{abbrev}-"
    for sid in existing_ids:
        if sid.startswith(prefix):
            rest = sid[len(prefix):]
            # Handle numeric and alphanumeric suffixes
            m = re.search(r"(\d+)$", rest)
            if m:
                max_num = max(max_num, int(m.group(1)))
    return max_num + 1


def parse_result(result_text):
    """
    Parse a result string in various formats and extract winner + score.
    Returns (winner_name, score_string) or (None, None).

    Formats handled:
    - "CSA won"
    - "3-1 CSA"
    - "Winner: CSA (25-6, 25-8)"
    - "ECE-1 beat CeNSE 2-0"
    - "CSA won 3-1"
    - "CSA def. ECE 25-6, 25-8"
    """
    if not result_text:
        return None, None

    text = result_text.strip()
    if not text:
        return None, None

    # "Winner: TEAM (score)"
    m = re.match(r"Winner:\s*(.+?)(?:\s*\((.+?)\))?\s*$", text, re.I)
    if m:
        return m.group(1).strip(), (m.group(2) or "").strip()

    # "TEAM won SCORE" or "TEAM won"
    m = re.match(r"(.+?)\s+won(?:\s+(.+))?\s*$", text, re.I)
    if m:
        return m.group(1).strip(), (m.group(2) or "").strip()

    # "TEAM beat OPPONENT SCORE"
    m = re.match(r"(.+?)\s+beat\s+.+?\s+([\d][\d\-,\s]+)\s*$", text, re.I)
    if m:
        return m.group(1).strip(), m.group(2).strip()

    # "TEAM beat OPPONENT"
    m = re.match(r"(.+?)\s+beat\s+(.+)", text, re.I)
    if m:
        return m.group(1).strip(), ""

    # "TEAM def. OPPONENT SCORE"
    m = re.match(r"(.+?)\s+def\.?\s+.+?\s+([\d][\d\-,\s]+)\s*$", text, re.I)
    if m:
        return m.group(1).strip(), m.group(2).strip()

    # "SCORE TEAM" e.g. "3-1 CSA"
    m = re.match(r"([\d]+\s*[-]\s*[\d]+)\s+(.+)\s*$", text)
    if m:
        return m.group(2).strip(), m.group(1).strip()

    return None, None


def build_description(existing_desc, winner, score):
    """Build a completed match description preserving pool/round info from existing."""
    prefix = ""
    if existing_desc:
        # Keep pool/group/round prefix from existing description
        m = re.match(r"((?:Pool|Group|Round|League|Quarter|Semi|Final|Women's|Men's)[^\|]*\|)\s*", existing_desc, re.I)
        if m:
            prefix = m.group(1) + " "
        elif existing_desc and "winner" not in existing_desc.lower():
            # Use existing description as prefix if it's a label
            if len(existing_desc) < 60 and not existing_desc.startswith("Winner"):
                prefix = existing_desc + " | "

    if score:
        return f"{prefix}Winner: {winner} ({score})"
    else:
        return f"{prefix}Winner: {winner}"


def parse_schedule_rows(rows):
    """
    Parse schedule data rows from a sheet tab.
    Expects column headers: #, Date, Time, Match/Title, Venue, Status, Result
    Returns list of dicts with: num, date, time, title, venue, status, result
    """
    entries = []
    for row in rows:
        if len(row) < 4:
            continue
        # Skip empty rows or sub-headers
        num = str(row[0]).strip() if len(row) > 0 else ""
        date = str(row[1]).strip() if len(row) > 1 else ""
        time_ = str(row[2]).strip() if len(row) > 2 else ""
        title = str(row[3]).strip() if len(row) > 3 else ""
        venue = str(row[4]).strip() if len(row) > 4 else ""
        status = str(row[5]).strip().lower() if len(row) > 5 else ""
        result = str(row[6]).strip() if len(row) > 6 else ""

        if not title or not date:
            continue
        # Skip if this looks like a header row
        if title.lower() in ("match/title", "match", "title", "match / title"):
            continue

        entries.append({
            "num": num,
            "date": normalize_date(date),
            "time": time_,
            "title": title,
            "venue": venue,
            "status": status if status in ("scheduled", "completed", "cancelled") else "",
            "result": result,
        })
    return entries


def normalize_date(date_str):
    """Normalize date to YYYY-MM-DD format. Handle common formats."""
    if not date_str:
        return ""
    date_str = date_str.strip()

    # Already YYYY-MM-DD
    if re.match(r"\d{4}-\d{2}-\d{2}$", date_str):
        return date_str

    # DD/MM/YYYY or DD-MM-YYYY
    m = re.match(r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})$", date_str)
    if m:
        d, mo, y = m.groups()
        return f"{y}-{int(mo):02d}-{int(d):02d}"

    # MM/DD/YYYY (if month > 12, swap)
    # "Apr 3, 2026" or "3 Apr 2026" etc.
    months = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }
    m = re.match(r"(\d{1,2})\s+(\w{3,9})\s+(\d{4})", date_str)
    if m:
        d, mon, y = m.groups()
        mo = months.get(mon[:3].lower())
        if mo:
            return f"{y}-{mo:02d}-{int(d):02d}"

    m = re.match(r"(\w{3,9})\s+(\d{1,2}),?\s+(\d{4})", date_str)
    if m:
        mon, d, y = m.groups()
        mo = months.get(mon[:3].lower())
        if mo:
            return f"{y}-{mo:02d}-{int(d):02d}"

    return date_str


def parse_teams_from_sheet(all_values):
    """
    Look for teams in column L+ (index 11+). Expects header row with
    'Team Name, Members' and data rows below.
    Returns list of {name, members[]}.
    """
    teams = []
    # Search for "Team Name" header in columns L-N (index 11-13)
    team_start_row = None
    team_col = None
    for i, row in enumerate(all_values):
        for j in range(11, min(len(row), 16)):
            cell = str(row[j]).strip().lower() if j < len(row) else ""
            if cell in ("team name", "team"):
                team_start_row = i + 1
                team_col = j
                break
        if team_start_row is not None:
            break

    if team_start_row is None:
        return teams

    members_col = team_col + 1

    for i in range(team_start_row, len(all_values)):
        row = all_values[i]
        name = str(row[team_col]).strip() if team_col < len(row) else ""
        if not name:
            continue
        members_str = str(row[members_col]).strip() if members_col < len(row) else ""
        members = [m.strip() for m in re.split(r"[,\n]", members_str) if m.strip()] if members_str else []
        teams.append({"name": name, "members": members})

    return teams


def parse_standings_section(all_values):
    """
    Look for STANDINGS section in the sheet data.
    Returns list of standings objects: {pool, qualify, table: [{team, p, w, d, l, pts}]}
    """
    standings = []
    stand_row = None
    for i, row in enumerate(all_values):
        for cell in row[:3]:
            if str(cell).strip().upper() == "STANDINGS":
                stand_row = i
                break
        if stand_row is not None:
            break

    if stand_row is None:
        return standings

    # Parse standings groups: look for pool headers and tables
    current_pool = None
    current_qualify = 1
    current_table = []
    i = stand_row + 1

    while i < len(all_values):
        row = all_values[i]
        first = str(row[0]).strip() if row else ""

        # Check for pool/group header
        pool_match = re.match(r"(Pool|Group)\s+\w+", first, re.I)
        if pool_match or (first and first.upper().startswith("POOL ") or first.upper().startswith("GROUP ")):
            # Save previous pool
            if current_pool and current_table:
                standings.append({
                    "pool": current_pool,
                    "qualify": current_qualify,
                    "table": current_table,
                })
            current_pool = first
            current_table = []
            # Check for qualify info
            for cell in row[1:]:
                qm = re.search(r"Top\s+(\d+)\s+qualify", str(cell), re.I)
                if qm:
                    current_qualify = int(qm.group(1))
            i += 1
            # Skip column header row (Team, P, W, D, L, Pts)
            if i < len(all_values):
                header_row = all_values[i]
                if header_row and str(header_row[0]).strip().lower() in ("team", "team name"):
                    i += 1
            continue

        # Check for table row: Team, P, W, D, L, Pts
        if current_pool and len(row) >= 6 and first:
            try:
                team_name = first
                p = int(row[1]) if row[1] else 0
                w = int(row[2]) if row[2] else 0
                d = int(row[3]) if row[3] else 0
                l_ = int(row[4]) if row[4] else 0
                pts = int(row[5]) if row[5] else 0
                current_table.append({
                    "team": team_name,
                    "p": p, "w": w, "d": d, "l": l_, "pts": pts,
                })
            except (ValueError, IndexError):
                pass

        # Empty row or new section — might end standings
        if not first and current_pool and current_table:
            standings.append({
                "pool": current_pool,
                "qualify": current_qualify,
                "table": current_table,
            })
            current_pool = None
            current_table = []

        # Stop if we hit another section header
        if first.upper() in ("BRACKET", "FREE-FORM UPDATES", "NOTES", "SCHEDULE"):
            break

        i += 1

    # Save last pool
    if current_pool and current_table:
        standings.append({
            "pool": current_pool,
            "qualify": current_qualify,
            "table": current_table,
        })

    return standings


def recalculate_standings(event):
    """
    Recalculate standings from completed schedule entries.
    Only recalculates if standings already exist (preserves pool structure).
    3 pts for win, 1 for draw, 0 for loss.
    """
    standings = event.get("standings", [])
    schedule = event.get("schedule", [])
    if not standings or not schedule:
        return

    for pool_obj in standings:
        pool_name = pool_obj["pool"]
        teams_in_pool = {entry["team"]: entry for entry in pool_obj["table"]}

        # Reset all stats
        for t in teams_in_pool.values():
            t["p"] = 0
            t["w"] = 0
            t["d"] = 0
            t["l"] = 0
            t["pts"] = 0

        # Find completed matches belonging to this pool
        for match in schedule:
            if match.get("status") != "completed":
                continue

            desc = match.get("description", "")
            title = match.get("title", "")

            # Determine if this match belongs to this pool
            belongs = False
            if pool_name.lower() in title.lower() or pool_name.lower() in desc.lower():
                belongs = True
            # Also check by pool prefix pattern: "Pool A: X vs Y"
            for pat in [pool_name.lower(), pool_name.lower().replace("pool ", "pool").replace("group ", "group")]:
                if pat in title.lower() or pat in desc.lower():
                    belongs = True

            if not belongs:
                continue

            # Extract team names from title (format: "Pool X: TeamA vs TeamB" or "TeamA vs TeamB")
            title_clean = re.sub(r"^(?:(?:Pool|Group)\s+\w+\s*:\s*)", "", title, flags=re.I)
            title_clean = re.sub(r"\s*\(.*?\)\s*$", "", title_clean)  # Remove trailing parenthetical
            vs_match = re.split(r"\s+vs\.?\s+", title_clean, flags=re.I)

            if len(vs_match) != 2:
                continue

            team_a = vs_match[0].strip()
            team_b = vs_match[1].strip()

            # Find matching team names in pool (fuzzy)
            ta = find_team_in_pool(team_a, teams_in_pool)
            tb = find_team_in_pool(team_b, teams_in_pool)

            if not ta or not tb:
                continue

            # Extract winner
            winner, _ = parse_result_from_description(desc)

            teams_in_pool[ta]["p"] += 1
            teams_in_pool[tb]["p"] += 1

            if winner:
                wt = find_team_in_pool(winner, teams_in_pool)
                if wt == ta:
                    teams_in_pool[ta]["w"] += 1
                    teams_in_pool[ta]["pts"] += 3
                    teams_in_pool[tb]["l"] += 1
                elif wt == tb:
                    teams_in_pool[tb]["w"] += 1
                    teams_in_pool[tb]["pts"] += 3
                    teams_in_pool[ta]["l"] += 1
                else:
                    # Draw or unknown
                    teams_in_pool[ta]["d"] += 1
                    teams_in_pool[ta]["pts"] += 1
                    teams_in_pool[tb]["d"] += 1
                    teams_in_pool[tb]["pts"] += 1
            elif "draw" in desc.lower() or "tie" in desc.lower():
                teams_in_pool[ta]["d"] += 1
                teams_in_pool[ta]["pts"] += 1
                teams_in_pool[tb]["d"] += 1
                teams_in_pool[tb]["pts"] += 1

        # Sort by pts descending
        pool_obj["table"] = sorted(
            pool_obj["table"],
            key=lambda t: (-t["pts"], -(t["w"]), t["l"]),
        )


def find_team_in_pool(name, teams_dict):
    """Find a team name in pool dict with fuzzy matching."""
    name_lower = name.strip().lower()
    for team_name in teams_dict:
        if team_name.lower() == name_lower:
            return team_name
    # Partial match
    for team_name in teams_dict:
        if name_lower in team_name.lower() or team_name.lower() in name_lower:
            return team_name
    return None


def parse_result_from_description(desc):
    """Extract winner and score from a description field."""
    if not desc:
        return None, None
    # "Winner: TEAM (score)"
    m = re.search(r"Winner:\s*(.+?)(?:\s*\((.+?)\))?\s*$", desc, re.I)
    if m:
        return m.group(1).strip(), (m.group(2) or "").strip()
    return parse_result(desc)


def update_bracket(event, match_title, winner_name):
    """
    If a bracket exists and a match result maps to a bracket match,
    update the winnerId and advance the winner to the next round.
    """
    bracket = event.get("bracket")
    if not bracket or not bracket.get("generated") or not bracket.get("matches"):
        return

    matches = bracket["matches"]

    # Try to find the bracket match by title reference
    # Schedule titles often have patterns like "SF1:", "Final:", "QF1:" etc.
    title_prefix = ""
    m = re.match(r"(SF\d+|QF\d+|Final|F\d*|R\d+M\d+)", match_title, re.I)
    if m:
        title_prefix = m.group(1).upper()

    updated_match = None
    for bm in matches:
        # Match by slot names containing the teams from the schedule title
        slot_names = [s.get("name", "") for s in bm.get("slots", [])]
        # Check if both teams in the bracket match appear in the schedule title
        if len(slot_names) == 2:
            t1 = slot_names[0].lower()
            t2 = slot_names[1].lower()
            title_lower = match_title.lower()
            if (t1 and t2 and
                (t1 in title_lower or any(w in title_lower for w in t1.split())) and
                (t2 in title_lower or any(w in title_lower for w in t2.split()))):
                updated_match = bm
                break

    if not updated_match:
        return

    # Set winnerId
    winner_lower = winner_name.lower()
    for slot in updated_match.get("slots", []):
        if winner_lower in slot.get("name", "").lower() or slot.get("name", "").lower() in winner_lower:
            updated_match["winnerId"] = slot.get("seedId") or slot.get("name")

            # Advance winner to next round
            next_round = updated_match["round"] + 1
            next_pos = updated_match["position"] // 2
            for nm in matches:
                if nm["round"] == next_round and nm["position"] == next_pos:
                    slot_idx = updated_match["position"] % 2
                    if slot_idx < len(nm.get("slots", [])):
                        nm["slots"][slot_idx]["name"] = slot.get("name", winner_name)
                        nm["slots"][slot_idx]["seedId"] = slot.get("seedId")
            break


# ---------------------------------------------------------------------------
# Main sync logic
# ---------------------------------------------------------------------------


def get_sheets_service():
    """Build an authenticated Google Sheets API service."""
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def fetch_all_tabs(service):
    """Fetch metadata for all tabs in the spreadsheet."""
    meta = service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    return [s["properties"]["title"] for s in meta.get("sheets", [])]


def fetch_tab_data(service, tab_name):
    """Fetch all cell values from a specific tab."""
    # Use a generous range to capture all data including side panels
    range_str = f"'{tab_name}'!A1:T200"
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=range_str,
            valueRenderOption="FORMATTED_VALUE",
        ).execute()
        return result.get("values", [])
    except Exception as e:
        print(f"Warning: could not read tab '{tab_name}': {e}", file=sys.stderr)
        return []


def find_event_by_id(events, event_id):
    """Find an event in the events list by ID."""
    for ev in events:
        if ev["id"] == event_id:
            return ev
    return None


def get_sport_slug(event_id):
    """Extract sport slug from event ID: evt-basketball -> basketball."""
    return event_id.replace("evt-", "")


def sync_tab(event, tab_values, abbrev, changes_log):
    """
    Sync a single sport tab's data into an event object.
    Returns number of changes made.
    """
    change_count = 0
    sport_name = event.get("sport", event["id"])

    # --- Find schedule section ---
    sched_start = None
    for i, row in enumerate(tab_values):
        first = str(row[0]).strip().upper() if row else ""
        if first == "SCHEDULE":
            sched_start = i + 1
            break
        # Also detect schedule by column header row
        if len(row) >= 4:
            cells = [str(c).strip().lower() for c in row[:7] if c]
            if "date" in cells and ("match" in " ".join(cells) or "title" in " ".join(cells)):
                sched_start = i + 1
                break

    # Find the header row (contains #, Date, Time, etc.)
    header_row_idx = None
    if sched_start is not None:
        # The row at sched_start might be the header, or schedule data
        for i in range(max(0, sched_start - 1), min(sched_start + 2, len(tab_values))):
            row = tab_values[i] if i < len(tab_values) else []
            cells = [str(c).strip().lower() for c in row[:7] if c]
            if "#" in cells or "date" in cells:
                header_row_idx = i
                break

    sched_data_start = (header_row_idx + 1) if header_row_idx is not None else sched_start

    # Find schedule end (next section or empty block)
    sched_end = len(tab_values)
    if sched_data_start is not None:
        empty_streak = 0
        for i in range(sched_data_start, len(tab_values)):
            row = tab_values[i]
            first = str(row[0]).strip().upper() if row else ""
            if any(first.startswith(kw) for kw in ("STANDINGS", "BRACKET", "FREE-FORM", "NOTES", "TEAMS")):
                sched_end = i
                break
            # Detect pool/group standings headers like "Pool 1", "Pool A", "Group B"
            if re.match(r"^(POOL|GROUP)\s", first):
                sched_end = i
                break
            # Detect "HOW TO UPDATE" instructions section
            if first.startswith("HOW TO UPDATE"):
                sched_end = i
                break
            if not any(str(c).strip() for c in row[:7]):
                empty_streak += 1
                if empty_streak >= 2:
                    sched_end = i - 1
                    break
            else:
                empty_streak = 0

    # Parse schedule rows
    if sched_data_start is not None:
        sheet_entries = parse_schedule_rows(tab_values[sched_data_start:sched_end])
    else:
        sheet_entries = []

    # Build lookup of existing schedule entries by normalized title+date
    existing_schedule = event.get("schedule", [])
    existing_lookup = {}
    for entry in existing_schedule:
        key = (normalize_title(entry.get("title", "")), entry.get("date", ""))
        existing_lookup[key] = entry

    results_updated = 0
    new_entries = 0
    next_num = get_next_schedule_id(event, abbrev)

    for se in sheet_entries:
        key = (normalize_title(se["title"]), se["date"])

        if key in existing_lookup:
            existing = existing_lookup[key]

            # Check if result needs updating
            if se["result"] and existing.get("status") != "completed":
                winner, score = parse_result(se["result"])
                if winner:
                    existing["status"] = "completed"
                    existing["description"] = build_description(
                        existing.get("description", ""), winner, score
                    )
                    results_updated += 1
                    change_count += 1

                    # Update bracket if applicable
                    update_bracket(event, existing.get("title", ""), winner)
            elif se["status"] == "completed" and existing.get("status") != "completed":
                # Status changed to completed without explicit result column
                if se["result"]:
                    winner, score = parse_result(se["result"])
                    if winner:
                        existing["status"] = "completed"
                        existing["description"] = build_description(
                            existing.get("description", ""), winner, score
                        )
                        results_updated += 1
                        change_count += 1

            # Update time/venue only if currently empty in JSON
            if se["time"] and not existing.get("time"):
                existing["time"] = se["time"]
                change_count += 1
            if se["venue"] and not existing.get("venue"):
                existing["venue"] = se["venue"]
                change_count += 1

        else:
            # New schedule entry
            new_id = f"sch-{abbrev}-{next_num}"
            next_num += 1

            new_entry = {
                "id": new_id,
                "title": se["title"],
                "date": se["date"],
                "time": se["time"],
                "venue": se["venue"],
                "description": "",
                "status": "scheduled",
            }

            # If it already has a result
            if se["result"]:
                winner, score = parse_result(se["result"])
                if winner:
                    new_entry["status"] = "completed"
                    new_entry["description"] = build_description("", winner, score)
            elif se["status"] == "completed":
                new_entry["status"] = "completed"

            existing_schedule.append(new_entry)
            new_entries += 1
            change_count += 1

    if "schedule" not in event and existing_schedule:
        event["schedule"] = existing_schedule

    # --- Parse teams ---
    sheet_teams = parse_teams_from_sheet(tab_values)
    if sheet_teams:
        existing_teams = event.get("teams", [])
        existing_team_names = {t["name"].lower() for t in existing_teams}
        teams_added = 0

        for st in sheet_teams:
            if st["name"].lower() not in existing_team_names:
                team_id = f"team-{abbrev}-{re.sub(r'[^a-z0-9]', '', st['name'].lower())}"
                existing_teams.append({
                    "id": team_id,
                    "name": st["name"],
                    "members": st["members"],
                })
                teams_added += 1
                change_count += 1

        if teams_added > 0:
            event["teams"] = existing_teams

    # --- Recalculate standings ---
    if event.get("standings"):
        old_standings = json.dumps(event["standings"])
        recalculate_standings(event)
        if json.dumps(event["standings"]) != old_standings:
            change_count += 1

    # --- Build change summary ---
    parts = []
    if results_updated:
        parts.append(f"{results_updated} results updated")
    if new_entries:
        parts.append(f"{new_entries} new schedule entries")
    if sheet_teams:
        teams_added_count = sum(
            1 for st in sheet_teams
            if st["name"].lower() not in {t["name"].lower() for t in event.get("teams", []) if t not in sheet_teams}
        )
    if parts:
        changes_log.append(f"{sport_name}: {', '.join(parts)}")

    return change_count


def main():
    dry_run = "--dry-run" in sys.argv

    # Load local data
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    original_data = json.dumps(data, ensure_ascii=False)
    events = data.get("events", [])

    # Build event ID lookup
    event_map = {ev["id"]: ev for ev in events}

    # Connect to Google Sheets
    service = get_sheets_service()
    tab_names = fetch_all_tabs(service)

    changes_log = []
    total_changes = 0

    for tab_name in tab_names:
        # Skip non-sport tabs
        event_id = tab_name_to_event_id(tab_name)
        sport_slug = get_sport_slug(event_id)

        if sport_slug not in SPORT_ABBREV:
            # Try extracting from row 2 of the tab
            continue

        event = event_map.get(event_id)
        if not event:
            print(f"Warning: no event found for tab '{tab_name}' (ID: {event_id})", file=sys.stderr)
            continue

        abbrev = SPORT_ABBREV[sport_slug]

        # Fetch tab data
        tab_values = fetch_tab_data(service, tab_name)
        if not tab_values or len(tab_values) < 3:
            continue

        # Check if row 2 has event ID override
        if len(tab_values) > 1:
            row2 = " ".join(str(c) for c in tab_values[1] if c)
            id_match = re.search(r"ID:\s*(evt-[\w-]+)", row2)
            if id_match:
                override_id = id_match.group(1)
                if override_id != event_id and override_id in event_map:
                    event = event_map[override_id]
                    sport_slug = get_sport_slug(override_id)
                    abbrev = SPORT_ABBREV.get(sport_slug, abbrev)

        changes = sync_tab(event, tab_values, abbrev, changes_log)
        total_changes += changes

    # Recalculate standings for all events that have them
    for ev in events:
        if ev.get("standings") and ev.get("schedule"):
            recalculate_standings(ev)

    has_changes = json.dumps(data, ensure_ascii=False) != original_data

    # Write back
    if has_changes and not dry_run:
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")

    # If standings were recalculated but not logged, add note
    if has_changes and not changes_log:
        changes_log.append("Standings recalculated")

    # Output summary
    summary = {
        "changes": changes_log,
        "has_changes": has_changes,
    }

    if dry_run:
        summary["dry_run"] = True

    print(json.dumps(summary))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Compare Google Sheet data with default-data.json and report all differences."""

import json
import re
import sys
from difflib import SequenceMatcher

SHEET_PATH = "/tmp/sheet_dump.json"
JSON_PATH = "/home/klh/Projects/football/src/data/default-data.json"

TAB_TO_EVENT = {
    "Athletics": "evt-athletics",
    "Badminton": "evt-badminton",
    "Basketball": "evt-basketball",
    "Carrom": "evt-carrom",
    "Chess": "evt-chess",
    "Cycling": "evt-cycling",
    "Football": "evt-football",
    "Foosball": "evt-foosball",
    "Ultimate Frisbee": "evt-frisbee",
    "Handball": "evt-handball",
    "Hockey": "evt-hockey",
    "Kabaddi": "evt-kabaddi",
    "Kho-Kho": "evt-kho-kho",
    "Lawn Tennis": "evt-lawn-tennis",
    "Powerlifting": "evt-powerlifting",
    "Snooker": "evt-snooker",
    "Swimming": "evt-swimming",
    "Table Tennis": "evt-table-tennis",
    "Throwball": "evt-throwball",
    "Volleyball": "evt-volleyball",
}

STATUS_MAP = {
    "COMPLETED": "completed",
    "ONGOING": "ongoing",
    "IN-PROGRESS": "in-progress",
    "UPCOMING": "upcoming",
}


def cell(row, idx, default=""):
    if idx < len(row):
        return str(row[idx]).strip()
    return default


def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def normalize_title(t):
    return re.sub(r'\s+', ' ', t.strip())


def parse_sheet_status(header_row):
    text = cell(header_row, 0).upper()
    for key, val in STATUS_MAP.items():
        if key in text:
            return val
    return None


def is_standings_header_next(rows, i):
    """Check if row i is a pool/group name with a standings header on the next row."""
    c0 = cell(rows[i], 0).lower()
    if not (c0.startswith("pool ") or c0.startswith("group ")):
        return False
    if i + 1 < len(rows):
        nxt = rows[i + 1]
        if cell(nxt, 0) == "#" and cell(nxt, 1).upper() == "TEAM":
            return True
    return False


def find_schedule_rows(rows):
    """Find all schedule data rows from a sheet tab."""
    schedule_entries = []

    # Find all schedule sections (some tabs have multiple: main + WOMEN'S SCHEDULE)
    section_starts = []
    for i, row in enumerate(rows):
        c0 = cell(row, 0).upper()
        # Must be a section header, not data
        if "SCHEDULE" in c0:
            # Verify it's a header: either only has text in col 0, or is clearly a label
            row_text = [str(c).strip() for c in row if str(c).strip()]
            if len(row_text) <= 3:  # Headers have 1-3 cells max
                section_starts.append(i)

    # Deduplicate (WOMEN'S SCHEDULE might match twice)
    section_starts = sorted(set(section_starts))

    for sec_idx, sched_start in enumerate(section_starts):
        # Find header row
        header_idx = sched_start + 1
        if header_idx >= len(rows):
            continue

        hrow = rows[header_idx]

        # Verify it's a schedule header row (has # and Date or Match columns)
        if not (cell(hrow, 0) == "#" and ("Date" in cell(hrow, 1) or "Match" in cell(hrow, 1) or cell(hrow, 1) == "Date")):
            continue

        # Determine right-side schedule offset for side-by-side layouts
        right_offset = None
        for j, c in enumerate(hrow):
            if j > 6 and str(c).strip() == "#":
                right_offset = j
                break

        # Determine the end of the next schedule section (if any)
        next_section_start = len(rows)
        if sec_idx + 1 < len(section_starts):
            next_section_start = section_starts[sec_idx + 1]

        # Parse rows after header
        for i in range(header_idx + 1, min(len(rows), next_section_start)):
            row = rows[i]
            c0 = cell(row, 0).upper()

            # Stop conditions
            if c0 in ("STANDINGS", "BRACKET", "TEAMS", "HOW TO UPDATE", "FREE-FORM UPDATES"):
                break
            if "STANDINGS" in c0 or "HOW TO UPDATE" in c0 or "FREE-FORM" in c0:
                break
            # Stop if we hit a pool/group standings table (no STANDINGS header)
            if is_standings_header_next(rows, i):
                break
            # Stop at empty row followed by pool name (inline standings)
            if not any(str(c).strip() for c in row):
                # Check if next non-empty row starts a standings table
                for peek in range(i + 1, min(i + 3, len(rows))):
                    if is_standings_header_next(rows, peek):
                        break
                else:
                    continue  # Just an empty row, keep going
                break  # Found standings table ahead, stop schedule parsing

            # Left section
            num = cell(row, 0)
            if num and num.isdigit():
                date = cell(row, 1)
                time_val = cell(row, 2)
                match_title = cell(row, 3)
                venue = cell(row, 4)
                status = cell(row, 5)
                result = cell(row, 6)

                # Skip rows where date is "UPDATED" or similar metadata
                if match_title and not date.upper().startswith("UPDATED"):
                    # Extra validation: match_title should not be a plain number (standings data)
                    if not re.match(r'^\d+$', match_title):
                        schedule_entries.append({
                            "num": int(num),
                            "date": date,
                            "time": time_val,
                            "title": match_title,
                            "venue": venue,
                            "status": status.lower() if status else "",
                            "result": result,
                            "row_idx": i,
                        })

            # Right section (side-by-side)
            if right_offset is not None:
                rnum = cell(row, right_offset)
                if rnum and rnum.isdigit():
                    rdate = cell(row, right_offset + 1)
                    rtime = cell(row, right_offset + 2)
                    rmatch = cell(row, right_offset + 3)
                    rvenue = cell(row, right_offset + 4)
                    rstatus = cell(row, right_offset + 5)
                    rresult = cell(row, right_offset + 6)

                    if rmatch and not re.match(r'^\d+$', rmatch):
                        schedule_entries.append({
                            "num": int(rnum),
                            "date": rdate,
                            "time": rtime,
                            "title": rmatch,
                            "venue": rvenue,
                            "status": rstatus.lower() if rstatus else "",
                            "result": rresult,
                            "row_idx": i,
                        })

    # Deduplicate entries with same title+date (can happen with side-by-side layouts)
    seen = set()
    deduped = []
    for e in schedule_entries:
        key = (normalize_title(e["title"]).lower(), e["date"])
        if key not in seen:
            seen.add(key)
            deduped.append(e)
    return deduped


def parse_standings_sections(rows):
    """Parse all standings tables from sheet."""
    standings = []
    i = 0
    in_standings = False
    
    while i < len(rows):
        c0 = cell(rows[i], 0)
        c0u = c0.upper()
        
        # Detect STANDINGS section
        if "STANDINGS" in c0u:
            in_standings = True
            i += 1
            continue
        
        # Stop at BRACKET or other sections
        if c0u in ("BRACKET", "TEAMS", "HOW TO UPDATE", "FREE-FORM UPDATES") and in_standings:
            in_standings = False
        if "BRACKET" in c0u or "HOW TO UPDATE" in c0u:
            in_standings = False
        
        # Check for pool name (also outside STANDINGS section for inline standings)
        is_pool_name = False
        pool_name = c0
        
        if pool_name and (
            pool_name.lower().startswith("pool ") or
            pool_name.lower().startswith("group ") or
            pool_name.lower() == "women's" or
            pool_name.lower().startswith("women's league") or
            pool_name.lower().startswith("round robin")
        ):
            # Exclude "WOMEN'S SCHEDULE" — that's a schedule section, not standings
            if "schedule" not in pool_name.lower():
                is_pool_name = True
        
        if is_pool_name:
            # Check for qualifier note
            qualify_note = ""
            for c in rows[i]:
                s = str(c).strip()
                if "qualif" in s.lower() or "top" in s.lower():
                    qualify_note = s

            # Next row should be header or directly data
            next_i = i + 1
            if next_i < len(rows):
                hdr = rows[next_i]
                data_start = next_i + 1
                # Check if next row is a header (#, Team, P, W, D, L, Pts)
                if cell(hdr, 0) == "#" and cell(hdr, 1).upper() == "TEAM":
                    data_start = next_i + 1
                # Or if next row is directly data (no header row)
                elif cell(hdr, 0).isdigit() and cell(hdr, 1):
                    data_start = next_i

                table = []
                for j in range(data_start, len(rows)):
                    trow = rows[j]
                    tnum = cell(trow, 0)
                    tteam = cell(trow, 1)
                    if not tteam or not tnum.isdigit():
                        break
                    table.append({
                        "team": tteam,
                        "p": cell(trow, 2),
                        "w": cell(trow, 3),
                        "d": cell(trow, 4),
                        "l": cell(trow, 5),
                        "pts": cell(trow, 6),
                    })
                if table:
                    standings.append({
                        "pool": pool_name,
                        "qualify": qualify_note,
                        "table": table,
                    })
                i = data_start + len(table)
                continue
        
        i += 1
    
    return standings


def parse_sheet_teams(rows, tab_name):
    """Parse teams from sheet tab."""
    teams = []
    
    # Method 1: Look for "TEAMS" section header
    for i, row in enumerate(rows):
        c0 = cell(row, 0).upper()
        if c0 == "TEAMS":
            # Next row has "Team Name", "Members"
            hdr_i = i + 1
            if hdr_i < len(rows) and cell(rows[hdr_i], 0).upper() in ("TEAM NAME", "TEAM"):
                for j in range(hdr_i + 1, len(rows)):
                    trow = rows[j]
                    tname = cell(trow, 0)
                    if not tname or tname.upper() in ("HOW TO UPDATE", "FREE-FORM UPDATES", "STANDINGS", "BRACKET"):
                        break
                    members_str = cell(trow, 1)
                    teams.append({
                        "name": tname,
                        "members": [m.strip() for m in members_str.split(",") if m.strip()] if members_str else [],
                    })
                return teams
    
    # Method 2: Side-by-side teams (team name column at offset)
    for i, row in enumerate(rows):
        for ci, cv in enumerate(row):
            sv = str(cv).strip()
            if sv.upper() == "TEAM NAME" and ci > 6:
                members_col = ci + 1
                for j in range(i + 1, len(rows)):
                    trow = rows[j]
                    tname = cell(trow, ci)
                    if not tname:
                        continue
                    if tname.upper() in ("HOW TO UPDATE", "FREE-FORM UPDATES", "STANDINGS", "BRACKET"):
                        break
                    members_str = cell(trow, members_col)
                    teams.append({
                        "name": tname,
                        "members": [m.strip() for m in members_str.split(",") if m.strip()] if members_str else [],
                    })
                return teams
    
    # Method 3: Side-by-side with just "Team Name" header in TEAMS column (Badminton style)
    for i, row in enumerate(rows):
        for ci, cv in enumerate(row):
            sv = str(cv).strip().upper()
            if sv == "TEAMS" and ci > 6:
                # Next row should have team names
                name_col = ci
                for j in range(i + 1, len(rows)):
                    trow = rows[j]
                    tname = cell(trow, name_col)
                    if not tname:
                        continue
                    if tname.upper() in ("HOW TO UPDATE", "FREE-FORM UPDATES"):
                        break
                    if tname.upper() == "TEAM NAME":
                        continue  # Skip sub-header
                    teams.append({
                        "name": tname,
                        "members": [],
                    })
                return teams
    
    # Method 4: Kho-Kho style - "Team Name" in TEAMS column at row 4
    for i, row in enumerate(rows):
        for ci, cv in enumerate(row):
            sv = str(cv).strip().upper()
            if sv == "TEAM NAME" and ci > 6:
                for j in range(i + 1, len(rows)):
                    trow = rows[j]
                    tname = cell(trow, ci)
                    if not tname:
                        continue
                    if tname.upper() in ("HOW TO UPDATE", "FREE-FORM UPDATES"):
                        break
                    teams.append({
                        "name": tname,
                        "members": [],
                    })
                return teams
    
    return teams


def match_schedule_entries(sheet_entries, json_entries):
    """Match sheet schedule entries to JSON entries by title similarity."""
    matches = []
    unmatched_sheet = list(range(len(sheet_entries)))
    unmatched_json = list(range(len(json_entries)))
    
    # First pass: high-confidence matches
    for si in list(unmatched_sheet):
        s_title = normalize_title(sheet_entries[si]["title"])
        best_match = None
        best_score = 0
        for ji in unmatched_json:
            j_title = normalize_title(json_entries[ji].get("title", ""))
            score = similar(s_title, j_title)
            if score > best_score:
                best_score = score
                best_match = ji
        
        if best_match is not None and best_score >= 0.65:
            matches.append((si, best_match, best_score))
            unmatched_sheet.remove(si)
            unmatched_json.remove(best_match)
    
    return matches, unmatched_sheet, unmatched_json


def compare_standings(sheet_standings, json_standings):
    diffs = []

    matched_json_pools = set()
    for ss in sheet_standings:
        s_pool = ss["pool"]
        matched = False
        for ji, js in enumerate(json_standings):
            if ji in matched_json_pools:
                continue
            j_pool = js.get("pool", "")
            # For short pool names (Pool A, Group B), require exact match
            # For longer names, allow fuzzy matching
            # Also match if one name contains the other (e.g. "Round Robin (Top 4...)" contains "Round Robin")
            is_exact = s_pool.lower() == j_pool.lower()
            sim = similar(s_pool, j_pool)
            short_name = len(s_pool) < 15 and len(j_pool) < 15
            contains = j_pool.lower() in s_pool.lower() or s_pool.lower() in j_pool.lower()
            if is_exact or (not short_name and sim >= 0.80) or (contains and len(min(s_pool, j_pool, key=len)) >= 8):
                matched = True
                s_table = ss["table"]
                j_table = js.get("table", [])
                
                if len(s_table) != len(j_table):
                    diffs.append(f"  STANDINGS Pool '{s_pool}': sheet has {len(s_table)} teams, JSON has {len(j_table)} teams")
                
                for st in s_table:
                    found = False
                    for jt in j_table:
                        if similar(st["team"], jt.get("team", "")) >= 0.75:
                            found = True
                            changes = []
                            for field in ["p", "w", "d", "l", "pts"]:
                                sv = str(st.get(field, "")).strip()
                                jv = str(jt.get(field, "")).strip()
                                if sv != jv:
                                    changes.append(f"{field.upper()}: sheet={sv} json={jv}")
                            if changes:
                                diffs.append(f"  STANDINGS Pool '{s_pool}', Team '{st['team']}': {', '.join(changes)}")
                            break
                    if not found:
                        diffs.append(f"  STANDINGS Pool '{s_pool}': Team '{st['team']}' in sheet not in JSON")
                
                for jt in j_table:
                    found = any(similar(st["team"], jt.get("team", "")) >= 0.75 for st in s_table)
                    if not found:
                        diffs.append(f"  STANDINGS Pool '{j_pool}': Team '{jt.get('team','')}' in JSON not in sheet")
                matched_json_pools.add(ji)
                break

        if not matched:
            teams_list = ", ".join(t["team"] for t in ss["table"][:5])
            diffs.append(f"  STANDINGS Pool '{s_pool}' ({len(ss['table'])} teams: {teams_list}...) in sheet, no match in JSON")
    
    for ji, js in enumerate(json_standings):
        if ji not in matched_json_pools:
            j_pool = js.get("pool", "")
            diffs.append(f"  STANDINGS Pool '{j_pool}' in JSON, no match in sheet")
    
    return diffs


def compare_teams(sheet_teams, json_teams):
    diffs = []
    if not sheet_teams and not json_teams:
        return diffs
    
    if len(sheet_teams) != len(json_teams):
        diffs.append(f"  TEAMS count: sheet={len(sheet_teams)}, json={len(json_teams)}")
    
    # Teams in sheet not in JSON
    for st in sheet_teams:
        best_score = max((similar(st["name"], jt["name"]) for jt in json_teams), default=0)
        if best_score < 0.6:
            diffs.append(f"  TEAMS '{st['name']}' in sheet not found in JSON")
    
    # Teams in JSON not in sheet
    for jt in json_teams:
        best_score = max((similar(jt["name"], st["name"]) for st in sheet_teams), default=0)
        if best_score < 0.6:
            diffs.append(f"  TEAMS '{jt['name']}' in JSON not found in sheet")
    
    # Member comparison for teams with members data
    for st in sheet_teams:
        if not st["members"]:
            continue
        best_jt = None
        best_score = 0
        for jt in json_teams:
            score = similar(st["name"], jt["name"])
            if score > best_score:
                best_score = score
                best_jt = jt
        if best_jt and best_score >= 0.6:
            s_members = set(m.strip() for m in st["members"] if m.strip())
            j_members = set(m.strip() for m in best_jt.get("members", []) if m.strip())
            if s_members != j_members:
                only_s = s_members - j_members
                only_j = j_members - s_members
                if only_s or only_j:
                    parts = []
                    if only_s:
                        parts.append(f"+sheet: {list(only_s)[:5]}")
                    if only_j:
                        parts.append(f"+json: {list(only_j)[:5]}")
                    diffs.append(f"  TEAMS '{st['name']}' members differ: {'; '.join(parts)}")
    
    return diffs


def main():
    with open(SHEET_PATH) as f:
        sheet_data = json.load(f)
    with open(JSON_PATH) as f:
        json_data = json.load(f)
    
    events_by_id = {e["id"]: e for e in json_data["events"]}
    total_diffs = 0
    
    for tab_name, event_id in sorted(TAB_TO_EVENT.items()):
        if tab_name not in sheet_data:
            print(f"\n{'='*70}")
            print(f"  {tab_name}: TAB NOT FOUND IN SHEET")
            total_diffs += 1
            continue
        
        if event_id not in events_by_id:
            print(f"\n{'='*70}")
            print(f"  {tab_name}: EVENT {event_id} NOT FOUND IN JSON")
            total_diffs += 1
            continue
        
        rows = sheet_data[tab_name]
        event = events_by_id[event_id]
        diffs = []
        
        # 1. Status
        sheet_status = parse_sheet_status(rows[0]) if rows else None
        json_status = event.get("status", "")
        if sheet_status and sheet_status != json_status:
            diffs.append(f"  STATUS: sheet='{sheet_status}' vs json='{json_status}'")
        
        # 2. Schedule
        sheet_schedule = find_schedule_rows(rows)
        json_schedule = event.get("schedule", [])
        
        if sheet_schedule or json_schedule:
            matches, unmatched_s, unmatched_j = match_schedule_entries(sheet_schedule, json_schedule)
            
            for si, ji, score in matches:
                se = sheet_schedule[si]
                je = json_schedule[ji]
                changes = []
                
                # Status
                s_status = se["status"]
                j_status = je.get("status", "")
                if s_status and j_status and s_status != j_status:
                    changes.append(f"status: sheet='{s_status}' json='{j_status}'")
                
                # Result/description
                s_result = se["result"]
                j_desc = je.get("description", "")
                if s_result and j_desc:
                    if "Winner:" in s_result and s_result != j_desc:
                        changes.append(f"result: sheet='{s_result}' json='{j_desc}'")
                    elif "Winner:" not in s_result and "Winner:" in j_desc:
                        # JSON has result but sheet doesn't
                        pass
                    elif s_result != j_desc and "Winner:" not in s_result and "Winner:" not in j_desc:
                        # Both are non-result descriptions that differ
                        if similar(s_result, j_desc) < 0.8:
                            changes.append(f"description: sheet='{s_result}' json='{j_desc}'")
                elif s_result and "Winner:" in s_result and not j_desc:
                    changes.append(f"result: sheet has '{s_result}', JSON has no description")
                
                # Date
                if se["date"] and je.get("date") and se["date"] != je.get("date"):
                    changes.append(f"date: sheet='{se['date']}' json='{je.get('date')}'")
                
                # Venue
                if se["venue"] and je.get("venue") and se["venue"].lower() != je.get("venue", "").lower():
                    changes.append(f"venue: sheet='{se['venue']}' json='{je.get('venue')}'")
                
                # Time
                if se["time"] and je.get("time") and se["time"] != je.get("time"):
                    changes.append(f"time: sheet='{se['time']}' json='{je.get('time')}'")
                
                if changes:
                    diffs.append(f"  SCHEDULE [{se['title']}]: {'; '.join(changes)}")
            
            for si in unmatched_s:
                se = sheet_schedule[si]
                if se["title"]:
                    diffs.append(f"  SCHEDULE NEW IN SHEET: #{se['num']} '{se['title']}' ({se['date']}) status={se['status']} result='{se['result']}'")
            
            for ji in unmatched_j:
                je = json_schedule[ji]
                if je.get("title"):
                    diffs.append(f"  SCHEDULE ONLY IN JSON: '{je['title']}' ({je.get('date','?')})")
        
        # 3. Standings
        sheet_standings = parse_standings_sections(rows)
        json_standings = event.get("standings", [])
        
        if sheet_standings or json_standings:
            st_diffs = compare_standings(sheet_standings, json_standings)
            diffs.extend(st_diffs)
        
        # 4. Teams
        sheet_teams = parse_sheet_teams(rows, tab_name)
        json_teams = event.get("teams", [])
        
        if sheet_teams or json_teams:
            t_diffs = compare_teams(sheet_teams, json_teams)
            if t_diffs:
                diffs.extend(t_diffs)
        
        # Output
        if diffs:
            print(f"\n{'='*70}")
            print(f"  {tab_name} ({event_id}) -- {len(diffs)} difference(s)")
            print(f"{'='*70}")
            for d in diffs:
                print(d)
            total_diffs += len(diffs)
        else:
            print(f"  {tab_name} ({event_id}) -- IN SYNC")
    
    print(f"\n{'='*70}")
    print(f"  TOTAL DIFFERENCES FOUND: {total_diffs}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()

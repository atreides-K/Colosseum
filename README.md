# SPECTRUM 2026

A Vue 3 SPA for **Spectrum 2026** — the annual inter-departmental sports tournament at IISc Bangalore, featuring 20 sporting events. Fully client-side with real event data, live schedules, results, and team rosters.

## Tech Stack

- Vue 3 (Composition API, `<script setup>`)
- Vue Router 4 (hash history)
- Vite 8
- Pure JavaScript (no TypeScript)
- PWA (manifest + service worker)
- Google Sheets MCP integration for live data sync

## Getting Started

```bash
npm install
npm run dev       # Start dev server with hot reload
npm run build     # Production build to dist/ (auto-generates rules + poster data)
npm run preview   # Preview production build locally
```

## Project Structure

```
src/
├── App.vue                    # Root — sidebar (desktop) + icon rail (mobile)
├── router.js                  # Routes: / (events), /home, /schedule, /events/:id
├── stores/tournament.js       # Reactive store with event data + pinned events (localStorage)
├── data/
│   ├── default-data.json      # Real event data (20 sports) — single source of truth
│   ├── rules.js               # Rules loader
│   ├── rules-data.json        # Auto-generated: rules markdown content
│   └── posters.json           # Auto-generated: poster filenames
├── utils/markdown.js          # Markdown-to-HTML renderer for rules
├── views/
│   ├── HomeView.vue           # Carousel, about, events grid, stats
│   ├── DashboardView.vue      # Events landing page with today's schedule
│   ├── EventDetailView.vue    # Event info, rules, teams, schedule, standings, bracket
│   ├── EventsView.vue         # All events grid with filtering
│   └── ScheduleView.vue       # Cross-event schedule (by date / by event / by dept)
└── style.css                  # Global CSS (dark theme, CSS custom properties)

events/                        # Source rules (PDFs + markdown)
├── <sport>/rules.md           # Full rulebook in markdown

public/
├── posters/                   # Sport-specific posters (shown on event detail pages)
├── rules/                     # Rulebook PDFs served for download
├── icons/                     # PWA icons (Spectrum logo)
├── manifest.json              # PWA manifest
└── sw.js                      # Service worker

scripts/
├── sync-prompt.md             # Prompt for automated sheet sync
└── sync-sheet.sh              # Cron script — syncs Google Sheet with site data

data/
└── Spectrum2026_Updates.xlsx   # Excel tracking sheet (one tab per sport)
```

## Features

### Core
- **Events landing page** (`/`) — today's schedule with pinned events shown first, collapsible "other events"
- **Event detail pages** — info (with poster sidebar), rules (markdown + PDF), teams/participants, schedule, standings (pool tables), bracket, notes
- **Schedule view** — three modes:
  - **By Date** — chronological, auto-scrolls to today, groups same-sport/same-time matches
  - **By Event** — grouped by sport
  - **By Dept** — search by department/team name to see all their matches across sports
- **Standings tab** — pool/group tables with W/D/L/Pts for league-stage sports
- **Bracket view** — single-elimination knockout brackets (e.g. Table Tennis 32-team)

### Mobile UX
- **Right-side icon rail** — floating frosted glass pill with page nav + pinned events, hides on scroll down
- **Floating schedule view switcher** — island-style bottom pill on schedule page
- **PWA install banner** — frosted top banner on every visit, dismissible per session
- **Responsive layout** — sidebar on desktop, icon rail on mobile

### Data Management
- **Google Sheets MCP** — read/write the shared Google Sheet directly from Claude Code
- **Automated sync** — cron job runs every 4 hours, invokes Claude Code CLI to sync sheet data with the site
- **Pinned events** — persisted in localStorage, shown first in today's schedule
- **Real event data** — schedules, results, teams, standings from actual Spectrum 2026 events

### Content
- **Sport posters** — auto-discovered from `public/posters/`, shown as sidebar on event detail Info tab
- **Rules rendering** — markdown compiled at build time, served with PDF download links
- **20 sports** — Athletics, Badminton, Basketball, Carrom, Chess, Cycling, Football, Foosball, Ultimate Frisbee, Handball, Hockey, Kabaddi, Kho-Kho, Lawn Tennis, Powerlifting, Snooker, Swimming, Table Tennis, Throwball, Volleyball

## Data Update Workflow

Three steps for every update:

1. **Update `src/data/default-data.json`** — single source of truth
2. **Update Google Sheet** (via MCP or manually) — shared with event incharges
3. **Commit and push** — triggers deployment

### Automated Sync (Google Sheet)

A cron job runs every 4 hours to sync the Google Sheet with the site:

```bash
# Manual trigger
./scripts/sync-sheet.sh

# Check logs
cat scripts/sync.log
```

**Setup:**
1. Google Sheets MCP configured in `.mcp.json` (project-scoped)
2. GCP Service Account with Sheets API access
3. Sheet shared with the service account email
4. Cron: `0 */4 * * * /home/klh/Projects/football/scripts/sync-sheet.sh`

### Google Sheet Structure

One tab per sport. Each tab has:
- **Schedule table** — Date, Time, Match, Status, Result
- **Standings table** — Pool groups with W/D/L/Pts
- **Teams table** — Team name + members
- **Free-form section** — event incharges can write updates in any format

## Adding Content

**Posters:** Drop images into `public/posters/` (named by sport, e.g. `football.jpeg`). Run `npm run build:posters`. They appear on the event detail page.

**Rules:** Add `events/<sport>/rules.md` + PDF to `public/rules/`. Set `hasRules: true` in the event data. Run `npm run build:rules`.

**Events:** Edit `src/data/default-data.json` for event metadata, schedules, teams, standings.

# SPECTRUM 2026

A Vue 3 SPA for **Spectrum 2026** — the annual inter-departmental sports tournament at IISc Bangalore, featuring 20 sporting events. Fully client-side with real event data, rules, and registration links.

## Tech Stack

- Vue 3 (Composition API, `<script setup>`)
- Vue Router 4 (hash history)
- Vite 8
- Pure JavaScript (no TypeScript)
- PWA (manifest + service worker)

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
├── App.vue                    # Root — collapsible sidebar with pinnable events
├── router.js                  # Routes: /, /dashboard, /events, /events/:id, /schedule
├── stores/tournament.js       # Reactive store with event data
├── data/
│   ├── default-data.json      # Real event data (20 sports)
│   ├── rules.js               # Rules loader
│   ├── rules-data.json        # Auto-generated: rules markdown content
│   └── posters.json           # Auto-generated: poster filenames
├── utils/markdown.js          # Markdown-to-HTML renderer for rules
├── views/
│   ├── HomeView.vue           # Landing page with carousel, about, events grid
│   ├── DashboardView.vue      # Pinned events with full details
│   ├── EventDetailView.vue    # Event info, rules, teams, schedule, bracket
│   ├── EventsView.vue         # All events grid with filtering
│   └── ScheduleView.vue       # Cross-event schedule
└── style.css                  # Global CSS (dark theme, CSS custom properties)

events/                        # Source event data (PDFs + markdown)
├── <sport>/
│   ├── event.md               # Structured event details
│   ├── rules.md               # Full rulebook in markdown
│   └── rules.pdf              # Original rulebook PDF

public/
├── posters/                   # Drop images here — auto-added to home carousel
├── rules/                     # Rulebook PDFs served for download
├── icons/                     # PWA icons
├── manifest.json              # PWA manifest
└── sw.js                      # Service worker
```

## Features

- **Home page** — auto-playing carousel (posters + info slides), about section, events grid, stats
- **Collapsible sidebar** — all 20 events listed, pinnable to top for quick access
- **Event details** — categories, format, venue, team size, guest rules, registration links, contacts
- **Rules tab** — rendered rulebook with PDF download link (15 sports)
- **Dashboard** — pinned events shown with full details, schedule, contacts, and action buttons
- **Schedule view** — cross-event schedule grouped by date or event
- **Registration links** — direct links to Google Forms / MS Forms for each sport
- **WhatsApp groups** — linked where available (5 sports)
- **PWA** — installable, works offline

## Adding Content

**Posters:** Drop images (jpg/png/webp) into `public/posters/` and rebuild. They auto-appear in the home carousel.

**Events:** Edit `src/data/default-data.json` for event metadata. Edit `events/<sport>/rules.md` for rulebook content.

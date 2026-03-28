# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- `npm run dev` — Start Vite dev server (hot reload)
- `npm run build` — Production build to `dist/` (runs `build:rules` + `build:posters` first)
- `npm run build:rules` — Generates `src/data/rules-data.json` from `events/*/rules.md`
- `npm run build:posters` — Generates `src/data/posters.json` from `public/posters/`
- `npm run preview` — Preview production build locally
- No test framework is configured yet

## Architecture

Vue 3 SPA for **SPECTRUM 2026** — a multi-sport institute tournament at IISc with 20 events. Fully client-side, viewer-only mode (no admin). localStorage is currently disabled — app always loads fresh from default data.

**Stack:** Vue 3 (Composition API, `<script setup>`), Vue Router 4 (hash history), Vite 8, pure JavaScript (no TypeScript). PWA enabled (manifest + service worker).

### State Management

A single reactive store in `src/stores/tournament.js` using Vue's `reactive()` — no Pinia/Vuex. localStorage persistence is commented out. All CRUD operations are exported as plain functions.

**Data model:** Each event has: `id`, `sport`, `icon`, `type` (team/individual), `status`, `venue`, `categories`, `teamSize`, `guestPlayers`, `format`, `registrationLink`, `registrationDeadline`, `whatsappLink`, `contacts[]`, `hasRules`. Operational fields (`teams[]`, `participants[]`, `schedule[]`, `notes[]`, `bracket{}`) are initialized at runtime by the store migration code, not stored in default-data.json.

**Sports (20):** Athletics, Badminton, Basketball, Carrom, Chess, Cycling, Football, Foosball, Ultimate Frisbee, Handball, Hockey, Kabaddi, Kho-Kho, Lawn Tennis, Powerlifting, Snooker, Swimming, Table Tennis, Throwball, Volleyball.

### Key Patterns

- **Viewer-only mode** — no admin toggle. All event data is read-only from `default-data.json`.
- **Views are self-contained** — each view in `src/views/` handles its own display and store interaction.
- **Global CSS only** — all styles live in `src/style.css` with CSS custom properties. No scoped styles. Dark theme.
- **Real event data** — `default-data.json` contains actual Spectrum 2026 event details extracted from PDFs. No dummy/mock data.
- **Rules rendering** — `events/*/rules.md` files are compiled to `src/data/rules-data.json` at build time. Rendered via `src/utils/markdown.js` (custom minimal renderer supporting headers, lists, tables, bold, images, links).
- **Poster auto-discovery** — images in `public/posters/` are auto-listed into `src/data/posters.json` at build time and displayed in the home page carousel.
- **Collapsible sidebar** — events listed with pin/unpin. Pinned events appear at top of sidebar and show full details on the dashboard.
- **Event detail tabs** — Info, Rules (with PDF download), Teams/Participants, Schedule, Bracket, Notes.

### Routing

Five routes in `src/router.js`: home (`/`), dashboard (`/dashboard`), events list (`/events`), event detail (`/events/:id`), schedule (`/schedule`).

### Build Pipeline

`npm run build` chains: `build:rules` (reads `events/*/rules.md` → JSON) → `build:posters` (reads `public/posters/` → JSON) → `vite build`. Rules PDFs are served from `public/rules/`. The cycling route map image is at `public/rules/cycling-route.png`.

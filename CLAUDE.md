# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- `npm run dev` — Start Vite dev server (hot reload)
- `npm run build` — Production build to `dist/`
- `npm run preview` — Preview production build locally
- No test framework is configured yet

## Architecture

Vue 3 SPA for managing "Spectrum" — a multi-sport institute tournament with 19 events. Fully client-side — no backend, all data persists in localStorage.

**Stack:** Vue 3 (Composition API, `<script setup>`), Vue Router 4 (hash history), Vite 8, pure JavaScript (no TypeScript).

### State Management

A single reactive store in `src/stores/tournament.js` using Vue's `reactive()` — no Pinia/Vuex. The store auto-saves to localStorage via a deep watcher. All CRUD operations are exported as plain functions from this file.

**Data model:** `tournamentName`, `isAdmin` (admin/viewer toggle), `events[]` where each event has: `sport`, `icon`, `type` (team/individual), `status` (upcoming/ongoing/completed), `teams[]` or `participants[]`, `volunteers[]`, `schedule[]`, `logistics{}`, `notes[]`.

**Sports:** Athletics, Basketball, Badminton, Carrom, Chess, Cycling, Football, Frisbee, Hockey, Lawn Tennis, Kho-Kho, Snooker, Swimming, Table Tennis, Volleyball, Powerlifting, Throwball, Handball, Foosball.

### Key Patterns

- **Admin/Viewer mode** — `store.isAdmin` toggles between admin (full CRUD) and viewer (read-only) modes. Toggle in sidebar. Admin-only UI is wrapped with `v-if="store.isAdmin"`.
- **Views are self-contained** — each view in `src/views/` handles its own forms, display, and store interaction. No shared components yet.
- **Global CSS only** — all styles live in `src/style.css` with CSS custom properties. No scoped styles in Vue SFCs. Dark theme with utility classes.
- **Dummy data** — `defaultState()` generates realistic dummy data for all 19 sports with teams/participants, volunteers, schedules, and logistics.
- **JSON import/export** — Settings page allows exporting/importing all data as JSON for sharing and persistence.

### Routing

Five routes defined in `src/router.js`: dashboard (`/`), events list (`/events`), event detail (`/events/:id`), schedule (`/schedule`), settings (`/settings`).

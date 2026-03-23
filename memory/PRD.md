# CineWorld Studio's - Product Requirements Document

## Original Problem Statement
Full-stack cinematic empire game where players create, produce, and release films, TV series, and anime.

## Core Architecture
- **Frontend**: React + Shadcn UI (port 3000)
- **Backend**: FastAPI + MongoDB (port 8001)
- **Integrations**: OpenAI GPT-4o-mini (text), GPT-Image-1 (poster gen), APScheduler (background jobs)

## Pipeline Flow (Updated March 23 2026)

### Film Pipeline - Visual Step Bar
```
[Idea] → [Trama] → [Location] → [Poster] → [Hype/Coming Soon] → [Casting] → [Script] → [Produzione] → [Uscita]
```

### Two Modes
- **Immediata**: Idea → Trama → Location → Casting → Script → Produzione → Uscita (skips Poster/Hype)
- **Coming Soon**: Idea → Trama → Location → Poster → STOP (timer) → Casting → Script → Produzione → Uscita

### Step Bar UI
- Current step: colored background + glow (yellow/purple/orange/cyan/green/blue/emerald)
- Completed steps: green checkmark
- Future steps: grey/dimmed
- Locked steps (during Coming Soon): lock icon + dark grey
- Scrollable horizontally on mobile
- Clicking a step navigates to the corresponding tab

### Coming Soon Flow Fix
- Films NO LONGER go backwards to `coming_soon` after shooting
- `choose-release-strategy` now sets `status: completed` with `release_pending: true`
- Scheduler handles `release_pending` films when timer expires

## Implemented Features

### Production Pipelines
- Film, TV Series, Anime production flows
- Coming Soon Interactive System with timer tiers
- Release Strategy System (Automatic +3% vs Manual +8%)
- Dynamic Notification System with severity levels
- Admin Maintenance Tool (repair + diagnose)

### Other Systems
- Box office, cinema/infrastructure revenue, cast system
- Social hub: chat, private messages, notifications
- Moderation, leaderboard, contests, challenges

## Bug Fixes (March 23 2026)
- **Flame icon missing import** → Added to lucide-react imports
- **expandedScreenplay state missing** → Added to ScreenplayTab
- **f.screenplay as object** → Defensive rendering with type check
- **One bad film crashes list** → try/catch per film in map()
- **ErrorBoundary** → Now shows actual error message
- **Coming Soon backwards flow** → Films go to `completed` + `release_pending` instead of back to `coming_soon`

## Known Issues
- (P2) Contest Page mobile layout broken (recurring)

## Backlog
- P1: Chat Evolution - Step 6 (mobile refinement + social quality)
- P1: Marketplace for TV/Anime rights
- P2: RBAC, CinePass + Stripe, PWA, Tutorial, Contest Page fix
- P3: Scommesse sui Coming Soon, Eventi globali
- Future: Push notifications (mobile), guerre tra Major

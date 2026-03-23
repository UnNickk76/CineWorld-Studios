# CineWorld Studio's - Product Requirements Document

## Original Problem Statement
Full-stack cinematic empire game where players create, produce, and release films, TV series, and anime.

## Core Architecture
- **Frontend**: React + Shadcn UI (port 3000)
- **Backend**: FastAPI + MongoDB (port 8001)
- **Integrations**: OpenAI GPT-4o-mini (text), GPT-Image-1 (poster gen), APScheduler (background jobs)

## Implemented Features

### Production Pipelines - Flow
**Film**: Creazione > Locandina > Coming Soon > `ready_for_casting` > Casting > Sceneggiatura > Pre-produzione > Shooting > Release
**Serie TV/Anime**: Concept > Locandina > Coming Soon > `ready_for_casting` > Casting > Sceneggiatura > Produzione > Release

### Coming Soon Interactive System
- Pre-Casting Phase with dynamic timer (Short/Medium/Long tiers)
- Dynamic Events via scheduler, Support/Boycott, Speed-Up (credit-based)
- Auto News, Scheduler auto-releases to `ready_for_casting`

### Release Strategy System
- Automatica (+3% guaranteed) vs Manuale (perfect timing = +8%)

### Dynamic Notification System (March 22 2026)
- **Notification Engine** (`notification_engine.py`): Narrative-style notifications
- **Severity**: Critical (red), Important (yellow), Positive (green)
- **Popup Priority System**: Critical=overlay, Important=toast, Positive=badge only
- **Anti-spam**: Max 1 popup every 7s, max 3 similar/hour, grouping within 30min
- **Click Navigation**: Context-aware links based on project status

### Admin Maintenance Tool (March 23 2026)
- **Endpoint**: `POST /api/admin/repair-database` (NeoMorpheus only)
- **Logical flow validation**: Checks consistency of project state machine
  - Films in casting without proposals -> reset to proposed
  - Films in screenplay without complete cast -> reset to proposed
  - Films in pre_production without screenplay -> reset to proposed
  - Coming Soon with expired timer -> released to ready_for_casting
  - Series with missing required data per status -> reset
- **Frontend**: Admin Panel > Manutenzione tab with detailed report UI
- **Stats**: Shows films/series analyzed, problems found, actions taken per category

### Dashboard "Prossimamente"
- Always visible with Coming Soon content, countdown, hype, interactive support/boycott

### Other Systems
- Box office, cinema/infrastructure revenue, cast system
- Social hub: chat, private messages, notifications
- Moderation, leaderboard, contests, challenges
- CinePass currency, admin panel

## Key API Endpoints
- `GET /api/notifications` - All notifications with severity
- `GET /api/notifications/popup` - Unread popup notifications
- `POST /api/admin/repair-database` - Database logical repair (admin only)
- `GET /api/film-pipeline/screenplay` - Screenplay films with auto-fix validation
- `GET /api/film-pipeline/all` - All projects with logical validation

## Key DB Fields
- Notifications: `severity`, `shown_popup`, `data.event_type`, `link`
- Film: `status`, `coming_soon_type`, `scheduled_release_at`, `cast`, `cast_proposals`, `screenplay`

## Bug Fixes (March 23 2026)
- **CRITICAL FIX**: ScreenplayTab crash - `expandedScreenplay` state was declared in CastingTab but NOT in ScreenplayTab. When rendering film with screenplay text, accessing `expandedScreenplay[f.id]` on undefined caused crash. Root cause of persistent "Qualcosa è andato storto" error.
- Improved ErrorBoundary and TabErrorBoundary to show actual error messages
- Added auto-fix validation to /film-pipeline/screenplay and /film-pipeline/all endpoints
- Created comprehensive admin repair-database endpoint with logical flow validation

## Bug Fixes (March 22 2026)
- Fixed scheduler auto_release_coming_soon: pre_casting -> ready_for_casting
- Fixed notification links: in-progress films -> /create-film, completed -> /films/{id}
- Reset admin password

## Known Issues
- (P2) Contest Page mobile layout broken (recurring)

## Backlog
- P1: Chat Evolution - Step 6 (mobile refinement + social quality)
- P1: Marketplace for TV/Anime rights
- P2: RBAC, CinePass + Stripe, PWA, Tutorial, Contest Page fix
- P3: Scommesse sui Coming Soon, Eventi globali
- Future: Push notifications (mobile), guerre tra Major

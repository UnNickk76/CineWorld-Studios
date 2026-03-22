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
- **Events**: Coming Soon (support/boycott/timer/completion), Production, Film Release, Social
- **Popup Priority System**:
  - Critical (boycotts, problems) = Prominent animated popup overlay
  - Important (phase complete, timer end) = Lightweight toast (sonner)
  - Positive (likes, hype) = Badge count only (no popup)
- **Anti-spam**: Max 1 popup every 7s, max 3 similar/hour, grouping within 30min
- **Click Navigation**:
  - In-progress films (coming_soon/casting/screenplay/production) -> `/create-film`
  - Completed films (high_revenue/flop) -> `/films/{id}`
  - Series -> `/create-series`
  - Chat/messages -> `/chat`
- **Bottom Navbar**: Sfide + TV removed, replaced with "Eventi" bell icon + badge

### Dashboard "Prossimamente"
- Always visible with Coming Soon content, countdown, hype, interactive support/boycott

### Other Systems
- Box office, cinema/infrastructure revenue, cast system
- Social hub: chat, private messages, notifications
- Moderation, leaderboard, contests, challenges
- CinePass currency, admin panel

## Key API Endpoints
- `GET /api/notifications` - All notifications with severity
- `GET /api/notifications/popup` - Unread popup notifications (marks shown_popup)
- `GET /api/notifications/count` - Unread count
- `POST /api/notifications/{id}/read` - Mark read
- `POST /api/coming-soon/{id}/interact` - Support/boycott (triggers notification)

## Key DB Fields
- Notifications: `severity` (critical/important/positive), `shown_popup`, `data.event_type`, `data.group_count`, `link`
- Film: `status`, `coming_soon_type`, `coming_soon_tier`, `scheduled_release_at`

## Bug Fixes (March 22 2026)
- Fixed scheduler auto_release_coming_soon: pre_casting -> ready_for_casting (not completed)
- Fixed notification links: in-progress films -> /create-film, completed -> /films/{id}
- Fixed existing DB notifications with wrong generic /films links
- Reset admin password

## Known Issues
- (P2) Contest Page mobile layout broken (recurring)

## Backlog
- P1: Chat Evolution - Step 6 (mobile refinement + social quality)
- P1: Marketplace for TV/Anime rights
- P2: RBAC, CinePass + Stripe, PWA, Tutorial, Contest Page fix
- P3: Scommesse sui Coming Soon, Eventi globali
- Future: Push notifications (mobile), guerre tra Major

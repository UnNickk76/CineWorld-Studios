# CineWorld Studio's - Product Requirements Document

## Original Problem Statement
Full-stack cinematic empire game where players create, produce, and release films, TV series, and anime. Features include cast management, screenplay writing, production pipelines, box office simulation, social hub, moderation, contests, and strategic release mechanics.

## Core Architecture
- **Frontend**: React + Shadcn UI (port 3000)
- **Backend**: FastAPI + MongoDB (port 8001)
- **Integrations**: OpenAI GPT-4o-mini (text), GPT-Image-1 (poster gen), APScheduler (background jobs)

## Implemented Features

### Production Pipelines - Flow
**Film**: Creazione > **Locandina** > **Coming Soon** > `ready_for_casting` > Casting > Sceneggiatura > Pre-produzione > Shooting > Release
**Serie TV/Anime**: Concept > **Locandina** > **Coming Soon** > `ready_for_casting` > Casting > Sceneggiatura > Produzione > Release

### Coming Soon Interactive System
- Pre-Casting Phase with dynamic timer (Short/Medium/Long tiers)
- Dynamic Events via scheduler, Support/Boycott, Speed-Up (credit-based with caps)
- Auto News, Scheduler auto-releases to `ready_for_casting` (NOT completed)

### Release Strategy System
- Automatica (+3% guaranteed) vs Manuale (perfect timing = +8%)

### Dynamic Notification System (March 22 2026)
- **Notification Engine** (`notification_engine.py`): Generates narrative-style notifications
- **Severity Levels**: Critical (red), Important (yellow), Positive (green)
- **Events that trigger notifications**:
  - Coming Soon: support, boycott, time changes, completion
  - Production: phase completed, problems
  - Film Release: high revenue, flop warning
  - Social: likes, messages, interactions
- **Real-time Popup**: Polls every 15s, shows animated popups on top-right
  - Auto-dismiss after 6 seconds
  - Color-coded by severity
  - Clickable (navigates to relevant page)
- **Anti-spam**: Max 3 similar notifications/hour, grouping within 30min window
- **NotificationsPage**: Filter tabs (Tutte/Critiche/Importanti/Positive), severity badges, colored borders
- **Bottom Navbar**: Sfide removed, Notifiche with bell icon + unread badge

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
- `POST /api/notifications/read-all` - Mark all read
- `POST /api/film-pipeline/{id}/launch-coming-soon` - Launch Coming Soon
- `POST /api/coming-soon/{id}/interact` - Support/boycott (triggers notification to owner)
- `POST /api/coming-soon/{id}/speed-up` - Speed-up timer
- `POST /api/film-pipeline/{id}/advance-to-casting` - Advance (proposed/coming_soon/ready_for_casting)

## Key DB Fields
- `status`: proposed | coming_soon | ready_for_casting | casting | screenplay | pre_production | shooting | completed
- `coming_soon_type`, `coming_soon_tier`, `coming_soon_completed`, `scheduled_release_at`
- Notifications: `severity` (critical/important/positive), `shown_popup`, `data.event_type`, `data.group_count`

## Bug Fixes (March 22 2026)
- **CRITICAL**: Fixed scheduler auto_release_coming_soon setting pre_casting films to 'completed' instead of 'ready_for_casting'
- Fixed advance-to-casting to accept ready_for_casting status
- Fixed corrupted data, reset admin password

## Known Issues
- (P2) Contest Page mobile layout broken (recurring)

## Backlog
- P1: Chat Evolution - Step 6 (mobile refinement + social quality)
- P1: Marketplace for TV/Anime rights
- P2: RBAC, CinePass + Stripe, PWA, Tutorial, Contest Page fix
- P3: Scommesse sui Coming Soon
- P3: Eventi globali
- Future: Push notifications (mobile), guerre tra Major

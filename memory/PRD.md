# CineWorld Studio's - Product Requirements Document

## Original Problem Statement
Full-stack cinematic empire game where players create, produce, and release films, TV series, and anime. Features include cast management, screenplay writing, production pipelines, box office simulation, social hub, moderation, contests, and strategic release mechanics.

## Core Architecture
- **Frontend**: React + Shadcn UI (port 3000)
- **Backend**: FastAPI + MongoDB (port 8001)
- **Integrations**: OpenAI GPT-4o-mini (text), GPT-Image-1 (poster gen), APScheduler (background jobs)

## Implemented Features

### Production Pipelines - Flow (March 2026)
**Film**: Creazione > **Locandina (obbligatoria)** > **Coming Soon** > `ready_for_casting` > Casting > Sceneggiatura > Pre-produzione > Shooting > Release
**Serie TV/Anime**: Concept > **Locandina (obbligatoria)** > **Coming Soon** > `ready_for_casting` > Casting > Sceneggiatura > Produzione > Release

### Coming Soon Interactive System (March 2026)
- **Pre-Casting Phase**: All projects enter Coming Soon BEFORE casting (dynamic timer based on tier)
- **Duration Tiers**: Short (2-6h), Medium (6-18h), Long (18-48h) with quality modifiers
- **Dynamic Events**: Random events via scheduler modify timer (+/- hours)
- **Support/Boycott**: Players can support (+hype) or boycott (-hype, penalties capped at -10%)
- **Speed-Up**: Credit-based with caps per tier
- **Auto News**: Template-based events generated per interaction
- **Scheduler**: `auto_release_coming_soon` sets films to `ready_for_casting` when timer expires (NOT completed)
- **UI**: Expandable cards with hype bar, audience expectations, news feed, Supporta/Boicotta buttons

### Release Strategy System (March 2026)
- **Automatica**: System calculates optimal release time. +3% revenue bonus guaranteed.
- **Manuale**: Player chooses 6h/12h/24h/48h. Perfect timing = +8% bonus.

### Dashboard "Prossimamente"
- ALWAYS visible (even with 0 items - shows placeholder)
- Shows all Coming Soon content (pre_casting + pre_release)
- Countdown timer, hype level, interactive support/boycott

### Other Systems
- Box office simulation, cinema/infrastructure revenue
- Cast system with skills, fame, hiring
- Social hub: chat, private messages, notifications
- Moderation/reporting system
- Leaderboard, contests, daily/weekly challenges
- CinePass currency, admin panel

## Key API Endpoints
- `POST /api/film-pipeline/{id}/launch-coming-soon` - Launch film into Coming Soon
- `POST /api/series-pipeline/{id}/launch-coming-soon` - Launch series/anime into Coming Soon
- `POST /api/coming-soon/{id}/interact` - Support or boycott
- `GET /api/coming-soon/{id}/details` - Full details
- `GET /api/coming-soon` - Public list
- `POST /api/film-pipeline/{id}/advance-to-casting` - Advance (accepts proposed, coming_soon, ready_for_casting)
- `POST /api/film-pipeline/{id}/choose-release-strategy` - Release strategy (post-shooting)
- `GET /api/film-pipeline/proposals` - Returns proposed + coming_soon + ready_for_casting films

## Key DB Fields
- `status`: 'proposed' | 'coming_soon' | 'ready_for_casting' | 'casting' | 'screenplay' | 'pre_production' | 'shooting' | 'completed' | 'discarded'
- `coming_soon_type`: 'pre_casting' (before casting) or null (before release, legacy)
- `coming_soon_tier`: 'short' | 'medium' | 'long'
- `coming_soon_completed`: boolean (set when timer expires)
- `scheduled_release_at`: ISO datetime when Coming Soon expires
- `hype_score`, `news_events[]`, `auto_comments[]`, `total_boycott_penalty`
- `release_strategy`: 'auto' | 'manual', `release_strategy_bonus_pct`

## Bug Fixes (March 22 2026)
- **CRITICAL**: Fixed scheduler auto_release_coming_soon setting pre_casting films to 'completed' instead of 'ready_for_casting'
- Fixed advance-to-casting to accept ready_for_casting status
- Fixed proposals endpoint to include ready_for_casting films
- Fixed pipeline counts to include ready_for_casting
- Fixed corrupted data (films stuck in wrong state)
- Reset admin password
- Applied same fixes to series/anime pipelines

## Known Issues
- (P2) Contest Page mobile layout broken (recurring)

## Backlog
- P1: Chat Evolution - Step 6 (mobile refinement + social quality)
- P1: Marketplace for TV/Anime rights
- P2: RBAC, CinePass + Stripe, PWA, Tutorial, Contest Page fix
- P3: Scommesse sui Coming Soon
- P3: Eventi globali

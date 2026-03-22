# CineWorld Studio's - Product Requirements Document

## Original Problem Statement
Full-stack cinematic empire game where players create, produce, and release films, TV series, and anime. Features include cast management, screenplay writing, production pipelines, box office simulation, social hub, moderation, contests, and strategic release mechanics.

## Core Architecture
- **Frontend**: React + Shadcn UI (port 3000)
- **Backend**: FastAPI + MongoDB (port 8001)
- **Integrations**: OpenAI GPT-4o-mini (text), GPT-Image-1 (poster gen), APScheduler (background jobs)

## User Personas
- Casual gamers who enjoy simulation/tycoon games
- Film/anime enthusiasts who want to roleplay as producers
- Italian-speaking primary audience

## Implemented Features

### Production Pipelines (Film, TV Series, Anime)
- Full pipeline: Proposal > Casting > Screenplay > Pre-Production > Shooting > Release
- Parallel project management
- Credit-based speed-ups
- AI poster generation
- Pre-screenplay from agency

### Dual Release System
- **Immediate Release**: Direct cinema/platform release with full quality calculation
- **Coming Soon Release**: Countdown timer, hype mechanic, "Prossimamente" dashboard section

### Release Strategy System (March 2026)
- **Automatica**: System calculates optimal release time based on quality/hype/competition. +3% revenue bonus guaranteed.
- **Manuale**: Player chooses 6h/12h/24h/48h release window. If "perfect timing": +8% revenue bonus.
- Applied to all 3 pipelines (Film, TV Series, Anime)

### Coming Soon Interactive System (March 2026 - NEW)
- **Support Action**: Increases hype, small quality boost at release. 65% success, 25% neutral, 10% backfire.
- **Boycott Action**: Decreases hype, possible quality penalty. 45% success, 30% fail, 25% backfire (Streisand effect).
- **Limits**: Max 3 actions/player/day, costs 1 CinePass each, diminishing returns.
- **Protection**: Max -10% penalty cap, high quality resists boycotts, high hype reduces negative effects.
- **Auto News**: Template-based news events generated per interaction (no AI).
- **Auto Comments**: Random audience comments generated per interaction.
- **UI**: Expandable Coming Soon cards with hype bar, audience expectations, news feed, comments, Supporta/Boicotta buttons.

### Coming Soon Timer Fix (March 2026)
- Scheduler uses proper datetime comparison (not string) to prevent premature releases
- `coming_soon_started_at` field tracks when countdown began
- Strategy bonus applied at auto-release

### Social Hub
- Real-time chat, private messages
- Notification system (likes, messages)
- Content reporting/moderation

### Game Systems
- Box office simulation with quality-based decay
- Cinema/infrastructure revenue
- Cast system with skills, fame, hiring
- Leaderboard, contests
- Daily/weekly challenges
- CinePass currency

### Admin Panel
- User management, film management
- Report/moderation handling

## Key API Endpoints
- `POST /api/coming-soon/{id}/interact` - Support or boycott Coming Soon content
- `GET /api/coming-soon/{id}/details` - Full details with news, comments, stats
- `POST /api/coming-soon/{id}/hype` - Legacy hype endpoint
- `POST /api/film-pipeline/{id}/choose-release-strategy` - Film release strategy
- `POST /api/series-pipeline/{id}/choose-release-strategy` - Series/anime release strategy
- `GET /api/coming-soon` - Public coming soon content list (enriched)

## Key DB Collections
- `film_projects`: Films (fields: release_type, release_strategy, release_strategy_bonus_pct, scheduled_release_at, news_events, auto_comments, total_boycott_penalty)
- `tv_series`: TV/Anime (same fields)
- `coming_soon_interactions`: Tracks player interactions (user_id, content_id, action, outcome, effects)
- `films`, `users`, `notifications`, `reports`, `infrastructure`

## Constants
- COMING_SOON_DAILY_LIMIT = 3
- COMING_SOON_INTERACT_COST = 1 CinePass

## Known Issues
- (P2) Contest Page mobile layout broken (recurring)

## Backlog (Priority Order)
- P1: Chat Evolution - Step 6 (mobile refinement + social quality)
- P1: Marketplace for TV/Anime rights
- P2: RBAC system
- P2: CinePass + Stripe integration
- P2: PWA support
- P2: Tutorial system
- P2: Contest Page mobile fix

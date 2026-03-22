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

### Release Strategy System (NEW - March 2026)
- **Automatica**: System calculates optimal release time based on quality/hype/competition. +3% revenue bonus guaranteed.
- **Manuale**: Player chooses 6h/12h/24h/48h release window. If "perfect timing" (based on hidden quality/hype/competition formulas): +8% revenue bonus.
- Applied to all 3 pipelines (Film, TV Series, Anime)

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
- `POST /api/film-pipeline/{id}/choose-release-strategy` - Film release strategy
- `POST /api/series-pipeline/{id}/choose-release-strategy` - Series/anime release strategy
- `GET /api/coming-soon` - Public coming soon content list
- `POST /api/coming-soon/{id}/hype` - Add hype to coming soon content
- `POST /api/film-pipeline/{id}/schedule-release` - Legacy schedule endpoint
- `POST /api/series-pipeline/{id}/schedule-release` - Legacy schedule endpoint

## Key DB Collections
- `film_projects`: Films in pipeline (fields: release_type, release_strategy, release_strategy_bonus_pct, scheduled_release_at, coming_soon_started_at)
- `tv_series`: TV/Anime in pipeline (same new fields)
- `films`: Released films
- `users`: Player accounts
- `notifications`, `reports`, `infrastructure`

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

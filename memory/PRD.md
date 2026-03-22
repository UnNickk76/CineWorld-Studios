# CineWorld Studio's - Product Requirements Document

## Original Problem Statement
Full-stack cinematic empire game where players create, produce, and release films, TV series, and anime. Features include cast management, screenplay writing, production pipelines, box office simulation, social hub, moderation, contests, and strategic release mechanics.

## Core Architecture
- **Frontend**: React + Shadcn UI (port 3000)
- **Backend**: FastAPI + MongoDB (port 8001)
- **Integrations**: OpenAI GPT-4o-mini (text), GPT-Image-1 (poster gen), APScheduler (background jobs)

## Implemented Features

### Production Pipelines - NEW FLOW (March 2026)
**Film**: Creazione > **Locandina (obbligatoria)** > **Coming Soon** > Casting > Sceneggiatura > Pre-produzione > Shooting > Release
**Serie TV/Anime**: Concept > **Locandina (obbligatoria)** > **Coming Soon** > Casting > Sceneggiatura > Produzione > Release

### Coming Soon Interactive System (March 2026)
- **Pre-Casting Phase**: All projects enter Coming Soon BEFORE casting (2h timer)
- **Support/Boycott**: Players can support (+hype) or boycott (-hype, penalties capped at -10%)
- **Risk System**: Actions have 65/25/10% (support) or 45/30/25% (boycott) success/neutral/backfire probabilities
- **Limits**: Max 3 actions/day/player, 1 CinePass each, diminishing returns
- **Auto News**: Template-based events generated per interaction
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
- `POST /api/film-pipeline/{id}/choose-release-strategy` - Release strategy (post-shooting)
- `GET /api/film-pipeline/proposals` - Returns proposed + coming_soon (pre_casting) films

## Key DB Fields
- `coming_soon_type`: 'pre_casting' (before casting) or null (before release, legacy)
- `scheduled_release_at`: ISO datetime when Coming Soon expires
- `hype_score`, `news_events[]`, `auto_comments[]`, `total_boycott_penalty`
- `release_strategy`: 'auto' | 'manual', `release_strategy_bonus_pct`

## Known Issues
- (P2) Contest Page mobile layout broken (recurring)

## Backlog
- P1: Chat Evolution - Step 6 (mobile refinement + social quality)
- P1: Marketplace for TV/Anime rights
- P2: RBAC, CinePass + Stripe, PWA, Tutorial, Contest Page fix

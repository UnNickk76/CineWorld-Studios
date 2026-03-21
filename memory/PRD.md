# CineWorld Studio's - PRD

## Original Problem Statement
A cinematic empire game where users produce films, manage TV stations, compete in challenges, and build a Hollywood-style business empire.

## Architecture
- **Frontend**: React (CRA) with Tailwind + Shadcn UI
- **Backend**: FastAPI + MongoDB (Motor async driver)
- **Scheduler**: APScheduler for background tasks
- **AI**: OpenAI GPT-4o-mini (text) + GPT-Image-1 (posters) via Emergent LLM Key

## Completed Features

### Core Game
- Full film/sequel/TV series/anime production pipelines
- TV station management, Cinema Journal, CineBoard, Hall of Fame, Festivals
- Infrastructure, Acting school, Friend system, chat, challenges, leaderboards

### Casting System (Unified)
- Casting Agency (recruit, manage, fire, send-to-school, transfer-from-school)
- Rich actor data for ALL 8,325 people
- Unified card format across ALL pipelines
- Guest Star Vocali for Anime and Animation films

### Release System
- Film release with poster, quality, box office
- Serie TV release card with quality, revenue, audience rating, comments
- Anime release card (pink theme)
- **Poster generation** for Series/Anime at release (background task with polling)

### Talent Scout System
- Talent Scout Attori + Sceneggiatori (infrastructure-gated)
- Scout tabs in Casting Agency when infrastructure owned
- Purchased screenplays usable in Film Pipeline creation

### Poster Management for Series/Anime (NEW - 2026-03-21)
- Generate/regenerate poster for completed series/anime
- Two modes: AI Automatica, AI + Prompt personalizzato
- Poster section expandable on completed series cards
- Automatic poster generation at release with polling

### Bug Fixes Applied
- TV Dashboard "0 emittenti" for legacy emittente_tv system
- Infrastructure unique_types missing studio_serie_tv/studio_anime
- Scout tab rendering missing in CastingAgencyPage
- timedelta import, MongoDB _id serialization fixes

## Backlog
- (P1) Guest Star per puntate singole Serie TV
- (P1) Marketplace diritti TV/Anime
- (P2) Fix layout mobile Contest Page
- (P2) RBAC, CinePass, Stripe, PWA, Tutorial, Component decomposition

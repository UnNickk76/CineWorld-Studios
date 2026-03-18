# CineWorld Studio's - Product Requirements Document

## Original Problem Statement
Cinematic empire game where players build film studios, produce films, hire cast, and compete on leaderboards.

## Core Architecture
- **Frontend:** React + Tailwind + Shadcn/UI
- **Backend:** FastAPI + MongoDB
- **AI:** OpenAI GPT-4o-mini (text) + GPT-Image-1 (images) via Emergent LLM Key
- **Scheduler:** APScheduler for autonomous game ops

## Credentials
- User: fandrex1@gmail.com / Ciaociao1

## What's Been Implemented

### Session 1 (March 18, 2026)
- Multi-Actor Casting, Quality v3 Balanced, Casting Agency sync fix
- Poster performance overhaul (base64 -> static files)
- Film Detail crash fix, source_recruit_id tracking

### Session 2 (March 18, 2026)
- **Production Menu UI:** Replaced single "Produci!" button with expandable 4-option menu (Film, Serie TV, Anime, La Tua TV)
- Locked buttons with lock icon, redirect to /infrastructure
- "X da sbloccare" indicator badge
- Menu uses framer-motion, backdrop overlay

### Session 3 (March 18, 2026)
- **Dashboard PRODUCI Fix:** PRODUCI card on Dashboard now opens production menu via shared ProductionMenuContext
- **TV Series Pipeline (Full):** Complete backend + frontend for TV series production
  - Backend: `/api/series-pipeline/*` endpoints (create, casting, screenplay AI, production, release)
  - 10 genres: Drama, Comedy, Thriller, Sci-Fi, Horror, Crime, Romance, Fantasy, Action, Medical
  - Quality calculation with breakdown (base, cast, screenplay, mastery bonuses)
  - XP/Fame rewards on completion
- **Anime Pipeline (Full):** Complete backend + frontend for anime production
  - 8 genres: Shonen, Seinen, Shojo, Mecha, Isekai, Slice of Life, Horror, Sports
  - Each genre has description, episode range, cost multiplier
  - Lower cost per episode ($80K vs $150K TV), longer production time
- **Emittente TV Page:** Management page with locked/unlocked states
  - Locked: Shows requirements (Level 18, Fame 200, $5M)
  - Unlocked: Palinsesto with 3 timeslots (Daytime/Prime Time/Late Night), stats, series list
- **Testing:** 100% pass rate (iteration 89: 9+15 tests, iteration 90: 11+9 tests)

---

## PLANNED FEATURES

### P0 - SEQUEL / SAGHE (Rework) - NOT STARTED
**Requisiti:** Livello 8 + 50 Fama
- Pipeline ridotta: Casting (riconferma cast con sconto) -> Sceneggiatura -> Produzione -> Release
- Bonus saga crescente: Sequel 2 = +5%, Sequel 3 = +8%, fino a +15%
- Rischio "saga fatigue": dal capitolo 4, malus se qualita' bassa
- Max 5 sequel per saga (6 capitoli totali)

### P1 - EMITTENTE TV BROADCAST SYSTEM - NOT STARTED
- Broadcast endpoint: assign series to timeslot, daily episode airing
- Audience calculation based on quality, timeslot, emittente reach
- Ad revenue per episode (CPM model)
- Season renewal/cancellation system
- See /app/memory/EMITTENTE_TV_DESIGN.md for full design

### P1 - MARKETPLACE TV/ANIME - NOT STARTED
- Extend marketplace to trade TV series and anime rights

---

## Known Issues
- **(P2) Contest Page Mobile Layout** - Recurring issue, /games may not render correctly on some mobile devices

## Backlog (P2)
- Refactor server.py (monolithic, 16k+ lines)
- Refactor FilmPipeline.jsx (1700+ lines)
- Refactor Dashboard.jsx
- Stripe integration, PWA, Tutorial popup
- Casting Agency as visitable building
- Admin RBAC System
- CinePass speed-ups

## Key Files
- `/app/backend/server.py` - Main backend
- `/app/backend/routes/series_pipeline.py` - TV Series & Anime pipeline
- `/app/backend/routes/film_pipeline.py` - Film pipeline
- `/app/backend/game_systems.py` - Infrastructure types
- `/app/frontend/src/App.js` - Main app, production menu
- `/app/frontend/src/contexts/index.jsx` - ProductionMenuContext
- `/app/frontend/src/pages/SeriesTVPipeline.jsx` - TV Series pipeline UI
- `/app/frontend/src/pages/AnimePipeline.jsx` - Anime pipeline UI
- `/app/frontend/src/pages/EmittenteTVPage.jsx` - TV Network page
- `/app/frontend/src/pages/Dashboard.jsx` - Dashboard with PRODUCI card
- `/app/memory/EMITTENTE_TV_DESIGN.md` - TV Network design doc

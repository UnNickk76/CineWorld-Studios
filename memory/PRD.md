# CineWorld Studio's - Product Requirements Document

## Original Problem Statement
Cinematic empire game where players build film studios, produce films, hire cast, and compete on leaderboards. The user wants strategic depth, unpredictability, and polished UI/UX.

## Core Architecture
- **Frontend:** React + Tailwind + Shadcn/UI
- **Backend:** FastAPI + MongoDB
- **AI:** OpenAI GPT-4o-mini (text) + GPT-Image-1 (images) via Emergent LLM Key
- **Scheduler:** APScheduler for autonomous game ops

## Key Systems Implemented
- Film Pipeline (propose > casting > screenplay > pre-production > shooting > release)
- Equipment & Sponsor systems
- CineBoard leaderboards (Daily, Weekly, Top 50, Attendance)
- Emerging Screenplays marketplace
- CinePass credits & daily contests
- Festivals & Awards
- Infrastructure (buildings)
- Chat, Friends, Social Feed
- Performance: batch endpoints, caching, 28+ indexes, static poster files

## What's Been Implemented

### Session March 18, 2026 - Part 2
- **Bug Fix: Casting Agency hired status** - Backend `/api/production-studio/casting` now returns `hired` and `hire_action` per recruit. Frontend greys out hired recruits with "Nel cast" or "A scuola" badges.
- **Bug Fix: Acting School slot counter** - Fixed confusing "Tutti gli slot occupati" message. Now shows correct count per section (training slots vs casting slots).
- **Bug Fix: Film Detail page crash** - Fixed missing `TrendingDown` and `RotateCcw` imports in FilmDetail.jsx.
- **Performance: Poster extraction to disk** - Extracted 22 base64 posters (31MB) from MongoDB to static files. New `/api/posters/{filename}` endpoint with 1-week cache headers.

### Session March 18, 2026 - Part 1
- **Film Quality Score v2 ("Alchemy Formula")** - Overhauled for unpredictability. Best investments: 13% masterpiece, 34% excellent, 38% good, 15% mediocre/bad.
- **Migration recalculate_quality_v2** - All 36 films recalculated (avg 74.2 → 49.6).

### Previously Completed
- Release-relative trend bars on CineBoard
- Screenplay purchase flow fix
- Full-stack performance optimization (batch endpoint, caching, indexes)
- "Full Package" pipeline flow fix
- Deployment login fix
- IMDb score recalibration (v5 formula)

## Credentials
- User: fandrex1@gmail.com / Ciaociao1

## Pending Issues
- None critical

## Upcoming Tasks (P1)
- Casting Agency (new building for other players)
- Admin RBAC System
- CinePass cost for speed-ups in pipeline
- Pre-engagement system: hired actors should appear in player's films for a contract duration. Cost varies by skills and duration. When contract expires, actor returns to public pool.

## Future/Backlog (P2)
- Refactor server.py (monolithic, 16k+ lines)
- Refactor FilmPipeline.jsx (1700+ lines)
- Refactor Dashboard.jsx
- Stripe integration
- PWA support
- Tutorial popup

## Key Files
- `/app/backend/routes/film_pipeline.py` - Pipeline logic + quality formula v2
- `/app/backend/server.py` - Migrations, routes, batch endpoints, poster serving
- `/app/backend/game_systems.py` - IMDb formula, game calculations
- `/app/backend/routes/acting_school.py` - Acting school training system
- `/app/backend/static/posters/` - Static poster files (31MB)
- `/app/frontend/src/components/ProductionStudioPanel.jsx` - Production Studio with casting
- `/app/frontend/src/pages/InfrastructurePage.jsx` - Infrastructure + school
- `/app/frontend/src/pages/FilmDetail.jsx` - Film detail with posterSrc()
- `/app/frontend/src/pages/Dashboard.jsx` - Main dashboard
- `/app/frontend/src/pages/CineBoard.jsx` - Leaderboards

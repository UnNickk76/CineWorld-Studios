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

### Completed (Latest Session - March 18, 2026)
- **Film Quality Score v2 ("Alchemy Formula"):** Overhauled to introduce unpredictability. Investments set the floor (~65 max deterministic), but random "alchemy" factors (director vision, audience reception, cast chemistry, critics, market timing, lightning events) create wide variance. Best investments: 13% masterpiece, 34% excellent, 38% good, 15% mediocre/bad.
- **Migration recalculate_quality_v2:** Applied new formula to all 36 existing films. Average quality dropped from 74.2 to 49.6 with realistic spread.
- **CRITICAL BUG FIX: Film Detail Page crash** - Fixed missing `TrendingDown` and `RotateCcw` imports in FilmDetail.jsx that caused "QUALCOSA E ANDATO STORTO" error.
- **MAJOR PERFORMANCE FIX: Poster extraction to disk** - Extracted 22 base64 posters (31MB) from MongoDB to static files on disk. New `/api/posters/{filename}` endpoint with 1-week cache headers. All poster generation code updated to save to disk. Frontend uses `posterSrc()` helper.
- **Bug fixes in social feed:** Fixed KeyError for missing user_id and AttributeError for non-dict cast items.

### Previously Completed
- Release-relative trend bars on CineBoard
- Screenplay purchase flow fix
- Full-stack performance optimization (batch endpoint, caching, indexes)
- "Full Package" pipeline flow fix
- Deployment login fix
- IMDb score recalibration (v5 formula)

## Quality Score v2 Distribution
| Scenario | Mean | Masterpiece % | Excellent % | Good % | Mediocre/Bad % |
|----------|------|---------------|-------------|--------|----------------|
| Best investments | 69.5 | 13% | 34% | 38% | 15% |
| Good investments | 57.3 | 2% | 16% | 39% | 43% |
| Average | 35.5 | 0% | 1% | 7% | 92% |

## Credentials
- User: fandrex1@gmail.com / Ciaociao1

## Pending Issues
- None critical

## Upcoming Tasks (P1)
- Casting Agency (new building for other players)
- Admin RBAC System
- CinePass cost for speed-ups in pipeline

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
- `/app/backend/static/posters/` - Static poster files (31MB)
- `/app/frontend/src/pages/FilmDetail.jsx` - Film detail with posterSrc() helper
- `/app/frontend/src/pages/Dashboard.jsx` - Main dashboard with posterSrc()
- `/app/frontend/src/pages/MyFilms.jsx` - Film grid with posterSrc()
- `/app/frontend/src/pages/CineBoard.jsx` - Leaderboards using poster_url directly
- `/app/frontend/src/contexts/index.jsx` - Auth + caching context

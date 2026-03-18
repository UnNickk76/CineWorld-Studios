# CineWorld Studio's - Product Requirements Document

## Original Problem Statement
Cinematic empire game where players build film studios, produce films, hire cast, and compete on leaderboards. The user wants strategic depth, unpredictability, and polished UI/UX.

## Core Architecture
- **Frontend:** React + Tailwind + Shadcn/UI
- **Backend:** FastAPI + MongoDB
- **AI:** OpenAI GPT-4o-mini (text) + GPT-Image-1 (images) via Emergent LLM Key
- **Scheduler:** APScheduler for autonomous game ops

## What's Been Implemented

### Session March 18, 2026 - Latest
- **Multi-Actor Casting System:** Fixed bug where only 1 actor could be hired. Now actors stay 'available' after hiring another. Actor cards are clickable directly (no ThumbsUp). Rejected actors show 'Rinegozia' button with 30% cost increase. Non-actor roles keep 'Scegli' button.
- **Film Quality v3 Balanced:** Formula uses base_mult=4.8 (between old 5.5 and v2's 4.0). Average quality ~66% (between old 74% and v2's 50%). 25% masterpieces for best investments.
- **Casting Agency Hired Status:** Recruits in Production Studio now show hired/school badge when already used.
- **Poster Performance:** 22 base64 posters extracted to static files. New `/api/posters/{filename}` endpoint with 1-week cache.
- **Film Detail Fix:** Added missing TrendingDown/RotateCcw imports.
- **Acting School Slot Counter:** Fixed confusing 'Tutti gli slot occupati' message.

## Key Formulas
### Film Quality v3 (Balanced)
- base_quality = pre_imdb * 4.8
- Cast/role/tech with diminishing returns (max ~20 combined)
- Director vision: gaussian(±22, stdev=9) - biggest swing factor
- Audience: gaussian(±20, stdev=8)
- Chemistry, genre trend, critic, timing, lightning events

| Scenario | Mean | Masterpiece % | Excellent % | Good % |
|----------|------|---------------|-------------|--------|
| Best | 75.9 | 25% | 42% | 26% |
| Good | 63.1 | 6% | 26% | 41% |
| Average | 40.1 | 0% | 1% | 13% |

## Credentials
- User: fandrex1@gmail.com / Ciaociao1

## Known Issues
- Screenplay/poster generation can fail with transient AI API errors (not a code bug)

## Upcoming Tasks (P1)
- Pre-engagement system: hired actors appear in player's films for contract duration
- Casting Agency as a new building for other players
- Admin RBAC System
- CinePass cost for speed-ups in pipeline

## Future/Backlog (P2)
- Refactor server.py (monolithic, 16k+ lines)
- Refactor FilmPipeline.jsx (1700+ lines)
- Stripe, PWA, Tutorial popup

## Key Files
- `/app/backend/routes/film_pipeline.py` - Pipeline, casting, quality formula, renegotiate endpoint
- `/app/backend/server.py` - Migrations, routes, batch endpoints, poster serving
- `/app/backend/game_systems.py` - IMDb formula
- `/app/backend/routes/acting_school.py` - Acting school
- `/app/frontend/src/pages/FilmPipeline.jsx` - Pipeline UI, casting, renegotiation
- `/app/frontend/src/components/ProductionStudioPanel.jsx` - Production Studio casting
- `/app/frontend/src/pages/Dashboard.jsx` - Main dashboard

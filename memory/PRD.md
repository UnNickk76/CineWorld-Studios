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
- Rich actor data for ALL 8,325 people (actors, directors, screenwriters, composers)
- **Unified card format** across ALL pipelines: avatar, name, gender, stars, fame badge, nationality, age, skill avg, film count, genre badges (2+1), agency name, skill toggle with color bars
- Agency actors shown in market views of all pipelines
- Guest Star Vocali for Anime and Animation films (famous only, optional, bonus)

### Release System
- Film release with poster, quality, box office
- **Serie TV release card**: quality, revenue, audience rating, audience comments (positive/mixed/negative with ratings), cast, XP/fame bonuses
- **Anime release card**: same as Serie TV with pink theme
- Poster generation task queued for series/anime on release

### Bug Fixes Applied
- Revenue drop, Dashboard scores, Cinema Journal posters, Collect All $0
- Empty Series Market, Serie TV "Dal Mercato" crash
- Rich actor data enrichment, hired actors genre enrichment
- Actor salary scaling for series (15% of film cost)

## Backlog
- (P1) Guest Star per puntate singole nelle Serie TV
- (P1) Talent Scout infrastructure (Screenwriters + Young Actors)
- (P1) Marketplace diritti TV/Anime
- (P1) Miglioramento sistema chat
- (P2) Contest Page mobile layout fix
- (P2) RBAC, CinePass, Stripe, PWA, Tutorial, Component decomposition

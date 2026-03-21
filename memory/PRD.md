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

### Dynamic Release Events System (NEW - 2026-03-21)
- 19 eventi narrativi unici al rilascio film (scandalo, successo virale, selezione festival, flop, endorsement celebrity, ecc.)
- Tre tipi: positivo, negativo, neutro con 3 livelli di rarità
- Ogni evento modifica qualità e incassi del film
- Descrizioni personalizzate con titolo del film
- Bias qualità: film migliori = più probabilità eventi positivi
- Frontend: card evento colorata nel risultato rilascio (verde/rosso/ambra), badge RARO per eventi rari

### Poster Management for Series/Anime
- Generate/regenerate poster for completed series/anime
- Two modes: AI Automatica, AI + Prompt personalizzato
- Automatic poster generation at release with background task + polling

### Talent Scout System
- Talent Scout Attori + Sceneggiatori (infrastructure-gated)
- Scout tabs in Casting Agency when infrastructure owned
- Purchased screenplays usable in Film Pipeline creation

### Bug Fixes Applied
- TV Dashboard "0 emittenti" for legacy emittente_tv system
- Infrastructure unique_types missing studio_serie_tv/studio_anime
- Scout tab rendering missing in CastingAgencyPage

## Backlog
- (P1) Guest Star per puntate singole Serie TV
- (P1) Marketplace diritti TV/Anime
- (P2) Fix layout mobile Contest Page
- (P2) RBAC, CinePass, Stripe, PWA, Tutorial, Component decomposition

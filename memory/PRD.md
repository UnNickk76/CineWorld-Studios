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

### March 18, 2026 (Session 1)
- **Multi-Actor Casting:** Click-to-hire with renegotiation (+30% cost).
- **Quality v3 Balanced:** base_mult=4.8, avg ~66% quality with alchemy formula.
- **Casting Agency sync fix:** Dismiss student -> hire record removed -> recruit available.
- **Poster performance:** 22 base64 posters -> static files, /api/posters/{filename} with 1-week cache.
- **Film Detail crash fix:** Missing icon imports.
- **source_recruit_id tracking:** Students store recruit origin.

### March 18, 2026 (Session 2)
- **Production Menu UI (P0 Complete):** Replaced single "Produci!" button in mobile bottom nav with expandable production menu showing 4 options:
  - **Film** (always available, navigates to /create-film)
  - **Serie TV** (locked/unlocked based on studio_serie_tv ownership)
  - **Anime** (locked/unlocked based on studio_anime ownership)
  - **La Tua TV** (locked/unlocked based on emittente_tv ownership)
- Locked buttons show lock icon and redirect to /infrastructure
- Menu uses framer-motion slide-up animation with backdrop overlay
- Hamburger menu also updated with locked state for new items
- Backend endpoint `/api/production-studios/unlock-status` provides unlock data
- Placeholder pages for /create-series, /create-anime, /my-tv show requirements when locked
- **Testing:** 100% pass rate (9/9 backend, 15/15 frontend)

---

## Upcoming Tasks (P0)
- **Full Sequel Pipeline:** Rework sequel creation to use reduced Film Pipeline (inherits cast/crew, quality bonus from parent)
- **Full TV Series Pipeline:** Full production pipeline for TV Series with pilot episode + daily episodes with AI mini-plots
- **Full Anime Pipeline:** Unique production pipeline for Anime with distinct mechanics

## Upcoming Tasks (P1)
- **Build TV Network Feature:** "La Tua TV" page with broadcast schedule, audience ratings, ad revenue
- **Marketplace for TV/Anime:** Extend marketplace for trading TV series and anime rights
- Pre-engagement system for hired actors
- Casting Agency as new building for other players
- Admin RBAC System
- CinePass cost for speed-ups in pipeline

---

## PLANNED FEATURES (Approved by User)

### P1 - SEQUEL / SAGHE (Rework)
**Requisiti:** Livello 8 + 50 Fama
- Pipeline ridotta: Casting (riconferma cast con sconto) -> Sceneggiatura -> Produzione -> Release
- Bonus saga crescente: Sequel 2 = +5%, Sequel 3 = +8%, fino a +15%
- Rischio "saga fatigue": dal capitolo 4, malus se qualita' bassa
- Max 5 sequel per saga (6 capitoli totali)

### P1 - SERIE TV (Rework Completo)
**Requisiti:** Livello 12 + 100 Fama
- Pipeline COMPLETA per stagione: Casting -> Sceneggiatura -> Equipment/VFX -> Produzione -> Release
- 6-13 episodi per stagione, ogni giorno una puntata con mini-trama AI
- Cast fisso + guest star, rinnovo o cancellazione dopo ogni stagione

### P1 - ANIME (Identita' Propria)
**Requisiti:** Livello 15 + 150 Fama
- Pipeline completa come Serie TV
- Sottogeneri: Shonen, Seinen, Shojo, Mecha, Isekai
- Costi bassi ma tempi lunghi, pubblico di nicchia fedele

### P2 - EMITTENTE TV (Nuova Infrastruttura)
- Slot: Prime Time, Daytime, Late Night
- Palinsesto settimanale, audience per episodio
- Entrate pubblicitarie, esclusive, competizione tra emittenti
- Livelli emittente: piu' slot, piu' reach

---

## Known Issues
- **(P2) Contest Page Mobile Layout** - Recurring issue, mobile /games may not render correctly

## Backlog (P2)
- Refactor server.py (monolithic, 16k+ lines)
- Refactor FilmPipeline.jsx (1700+ lines)
- Refactor Dashboard.jsx
- Stripe integration
- PWA support
- Tutorial popup

## Key Files
- `/app/backend/server.py` - Main backend, migrations, endpoints
- `/app/backend/game_systems.py` - Infrastructure types, game mechanics
- `/app/backend/routes/film_pipeline.py` - Film pipeline, casting, quality
- `/app/backend/routes/acting_school.py` - Acting school + hire cleanup
- `/app/frontend/src/App.js` - Main app, bottom nav, production menu
- `/app/frontend/src/pages/FilmPipeline.jsx` - Film pipeline UI
- `/app/frontend/src/pages/SeriesTVPipeline.jsx` - Placeholder
- `/app/frontend/src/pages/AnimePipeline.jsx` - Placeholder
- `/app/frontend/src/pages/EmittenteTVPage.jsx` - Placeholder

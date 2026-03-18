# CineWorld Studio's - Product Requirements Document

## Original Problem Statement
Cinematic empire game where players build film studios, produce films, hire cast, and compete on leaderboards.

## Core Architecture
- **Frontend:** React + Tailwind + Shadcn/UI + Framer Motion
- **Backend:** FastAPI + MongoDB
- **AI:** OpenAI GPT-4o-mini (text) + GPT-Image-1 (images) via Emergent LLM Key
- **Scheduler:** APScheduler for autonomous game ops

## Credentials
- User: fandrex1@gmail.com / Ciaociao1

---

## What's Been Implemented

### Session 1 (March 18)
- Multi-Actor Casting, Quality v3, Casting sync fix, Poster performance overhaul

### Session 2 (March 18)
- Production Menu UI (4 buttons), Menu animations, unlock indicator

### Session 3 (March 18)
- Dashboard PRODUCI card opens production menu via shared context
- TV Series Pipeline (full), Anime Pipeline (full), Emittente TV placeholder

### Session 4 (March 18)
- **CineBoard Popup Menu:** Trophy button in top navbar opens dropdown with 3 options:
  - Film (all existing rankings at /social)
  - Serie TV (weekly trend at /social?view=series)
  - Anime (weekly trend at /social?view=anime)
- Backend: `/api/cineboard/series-weekly` and `/api/cineboard/anime-weekly` endpoints
- **Sequel Pipeline (P0 COMPLETE):**
  - Backend: `/api/sequel-pipeline/*` - create, confirm-cast, write-screenplay, start-production, release, discard
  - Select parent film, inherit cast with 30% discount, AI screenplay, 5-min quick production
  - Saga bonus system: +5% (cap.2), +8% (cap.3), +12% (cap.4), +15% (cap.5-6)
  - Saga fatigue: from cap.4, malus -8% if parent quality < 60
  - Max 5 sequels per saga (6 chapters total)
- **Production Menu Updated:** 5 buttons in 3-column grid (Film, Sequel, Serie TV, Anime, La Tua TV)
- **Emittente TV Broadcast System (P1 COMPLETE):**
  - Backend: `/api/emittente-tv/*` - broadcasts, assign, remove, air-episode, stats
  - 3 timeslots: Daytime (x0.5 audience, $5K/g), Prime Time (x1.5, $15K/g), Late Night (x0.8, $8K/g)
  - Assign series to slots, air episodes, earn ad revenue ($50 CPM)
  - Frontend: Full management page with palinsesto, assignment panel, stats
- **Testing:** 100% pass rate across all iterations (89-91)

---

### Session 5 (March 18)
- **"I Miei Film" Popup Menu:** Bottom nav "I Miei" button opens popup with 3 options (Film, Serie TV, Anime)
- **MyFilms.jsx Refactored:** Handles `?view=` parameter (film/series/anime) for dynamic content display
- **Release/System Notes Updated** in backend

### Session 6 (March 18)
- **Removed "FILM IN ATTESA DI RILASCIO" card** from Dashboard (user request - no longer needed)
- **Added "ULTIMI AGGIORNAMENTI" section** in its place: shows 5 latest releases from ALL players with poster, title, producer name
- **Added 3 horizontal sections** at bottom of Dashboard: "I Miei Film" (5 posters), "Le Mie Serie TV" (5 posters), "I Miei Anime" (5 posters), each with "Vedi Tutti" button
- **Backend extended**: `/api/dashboard/batch` now returns `my_series`, `my_anime`, `recent_releases` with producer info
- **Verified** via testing agent: 100% pass rate (iteration 92 + 93)
- **Updated** Release Notes (v0.091, v0.092) and System Notes

## COMPLETED P0/P1 TASKS
- [x] Production Menu UI (5 buttons)
- [x] TV Series Pipeline
- [x] Anime Pipeline
- [x] Sequel Pipeline (saga bonus + fatigue)
- [x] CineBoard Series/Anime Trend Classifiche
- [x] CineBoard Popup Menu (Film, Serie TV, Anime)
- [x] Emittente TV Broadcast System
- [x] "I Miei Film" Popup Menu (Film, Serie TV, Anime)
- [x] MyFilms.jsx dynamic view (?view= parameter)
- [x] Emittente TV Live Ratings + Storico Episodi + Momentum
- [x] Dashboard "Ultimi Aggiornamenti" (rilasci da tutti i player)
- [x] Dashboard 3 sezioni orizzontali (Film, Serie TV, Anime con 5 poster)
- [x] Dashboard cleanup (removed pending films card)

## Remaining Tasks

### P1 - MARKETPLACE TV/ANIME - NOT STARTED
- Extend marketplace to trade TV series and anime rights
- Buy/sell completed series between players

### P1 - Sequel integration in film pipeline
- Show sequel count on film detail pages
- Allow sequel creation from film detail page directly

### P1 - Emittente TV Automation
- Scheduler auto-airs episodes daily (currently manual)
- Notification system for aired episodes

### P2 - Known Issues
- Contest Page Mobile Layout (/games) - recurring mobile rendering issue

### P2 - Refactoring
- Refactor server.py (16k+ lines → modular routes)
- Refactor FilmPipeline.jsx (1700+ lines)
- Refactor Dashboard.jsx

### P2 - Future Features
- Casting Agency as visitable building
- Admin RBAC System
- CinePass speed-ups
- Stripe integration, PWA, Tutorial popup

## Key Files
- `/app/backend/server.py` - Main backend + cineboard endpoints
- `/app/backend/routes/series_pipeline.py` - TV Series & Anime pipeline
- `/app/backend/routes/sequel_pipeline.py` - Sequel pipeline
- `/app/backend/routes/emittente_tv.py` - Broadcast system
- `/app/backend/routes/film_pipeline.py` - Film pipeline
- `/app/backend/game_systems.py` - Infrastructure types
- `/app/frontend/src/App.js` - Main app, production menu, cineboard popup
- `/app/frontend/src/contexts/index.jsx` - ProductionMenuContext
- `/app/frontend/src/pages/SeriesTVPipeline.jsx` - TV Series pipeline UI
- `/app/frontend/src/pages/AnimePipeline.jsx` - Anime pipeline UI
- `/app/frontend/src/pages/SequelPipeline.jsx` - Sequel pipeline UI
- `/app/frontend/src/pages/EmittenteTVPage.jsx` - TV Network management
- `/app/frontend/src/pages/CineBoard.jsx` - CineBoard with series/anime views

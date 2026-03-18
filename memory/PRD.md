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

## What's Been Implemented (March 18, 2026)
- **Multi-Actor Casting:** Actors stay available after hiring one. Click-to-hire. Renegotiation for rejected actors (+30% cost).
- **Quality v3 Balanced:** base_mult=4.8, avg ~66% quality. Alchemy formula with director vision, audience, chemistry, critics, timing, lightning.
- **Casting Agency sync fix:** Dismiss student → hire record removed → recruit available again.
- **Poster performance:** 22 base64 posters extracted to static files, /api/posters/{filename} with 1-week cache.
- **Film Detail crash fix:** Missing TrendingDown/RotateCcw imports.
- **source_recruit_id tracking:** Students store recruit origin for cleanup.

---

## Upcoming Tasks (P1)
- Pre-engagement system for hired actors
- Casting Agency as new building for other players
- Admin RBAC System
- CinePass cost for speed-ups in pipeline

---

## PLANNED FEATURES (Approved by User - March 18, 2026)

### P1 — SEQUEL / SAGHE (Rework)
**Requisiti:** Livello 8 + 50 Fama
- Pipeline ridotta: Casting (riconferma cast originale con sconto o cambia) → Sceneggiatura → Produzione → Release
- Bonus saga crescente: Sequel 2 = +5%, Sequel 3 = +8%, fino a +15% al capitolo 5
- Rischio "saga fatigue": dal capitolo 4, malus crescente se qualità precedenti era bassa
- Poster coerente: riprende stile del film originale
- Max 5 sequel per saga (6 capitoli totali)

### P1 — SERIE TV (Rework Completo)
**Requisiti:** Livello 12 + 100 Fama
- **Pipeline COMPLETA per stagione:** Casting → Sceneggiatura → Equipment/VFX → Produzione → Release
- **Sistema a stagioni:** 6-13 episodi per stagione
- **Ogni giorno una puntata** con mini-trama generata AI (una mini sinossi per episodio)
- **Cast fisso + guest star:** Cast principale resta, guest star per stagione
- **Qualità legata a cast/sceneggiatura/equipment** come i film
- **Rinnovo o cancellazione:** Dopo ogni stagione, in base agli ascolti
- **Preparazione Emittente TV:** campo `broadcast_status` (non_trasmessa, in_onda, conclusa), `broadcast_channel`

### P1 — ANIME (Identità Propria)
**Requisiti:** Livello 15 + 150 Fama
- **Pipeline completa** come Serie TV
- **Sottogeneri specifici:** Shonen, Seinen, Shojo, Mecha, Isekai
- **Costi più bassi** ma tempi di produzione più lunghi
- **Pubblico di nicchia ma fedele:** Meno ascolti iniziali, decay molto più lento, fan base più forte
- **Ogni giorno una puntata** con mini-trama AI
- **Merchandise bonus** (futuro): entrate extra da merchandise
- Studio di Animazione necessario (futuro edificio, per ora usa Production Studio)

### P2 — EMITTENTE TV (Nuova Infrastruttura)
**Concetto:** Edificio dove trasmettere serie TV e anime
- **Slot di programmazione:** Prime Time, Daytime, Late Night (audience diversa)
- **Palinsesto settimanale:** Il giocatore sceglie cosa trasmettere in ogni slot
- **Audience rating per episodio:** Ascolti variano in base a slot, qualità, genere, competizione
- **Entrate pubblicitarie:** Revenue proporzionale agli ascolti
- **Esclusive:** Serie in esclusiva su un'emittente generano più ascolti
- **Competizione tra emittenti:** Se due giocatori trasmettono alla stessa ora, si dividono il pubblico
- **Livelli emittente:** Più livelli = più slot, più reach, accordi pubblicitari migliori
- Campo `audience_rating` per episodio, `broadcast_channel`, `timeslot`

---

## Backlog (P2)
- Refactor server.py (monolithic, 16k+ lines)
- Refactor FilmPipeline.jsx (1700+ lines)
- Refactor Dashboard.jsx
- Stripe integration
- PWA support
- Tutorial popup

## Key Files
- `/app/backend/routes/film_pipeline.py` - Pipeline, casting, quality formula, renegotiate
- `/app/backend/routes/acting_school.py` - Acting school + dismiss with hire cleanup
- `/app/backend/server.py` - Migrations, casting agency, poster serving, sequel/series/anime endpoints
- `/app/frontend/src/pages/FilmPipeline.jsx` - Pipeline UI, casting
- `/app/frontend/src/components/ProductionStudioPanel.jsx` - Production Studio + casting agency
- `/app/frontend/src/pages/InfrastructurePage.jsx` - Infrastructure buildings
- `/app/frontend/src/pages/Dashboard.jsx` - Main dashboard
- `/app/frontend/src/pages/CineBoard.jsx` - Leaderboards

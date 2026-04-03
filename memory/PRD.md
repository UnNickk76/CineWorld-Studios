# CineWorld Studio's — PRD

## Problema Originale
Gioco browser-based di simulazione studio cinematografico. Full-stack React + FastAPI + MongoDB.

## Architettura
```
/app/backend/
├── server.py (monolite in refactoring)
├── cast_system.py (ACTOR_SKILLS, GENRE_SKILL_MAPPING)
├── challenge_system.py
├── game_systems.py
├── scheduler_tasks.py (revenue giornaliero, sponsor impact, premiere decay)
├── database.py (fix deploy: override=False, env priority)
├── routes/
│   ├── sponsors.py (sistema sponsor completo)
│   ├── la_prima.py (sistema premiere completo - backend + frontend)
│   ├── cast.py, casting_agency.py, acting_school.py
│   ├── film_pipeline.py (quality genre-aware)
│   ├── series_pipeline.py, sequel_pipeline.py
│   ├── cinepass.py, films.py, film_engagement.py
│   └── ... (altre route)
/app/frontend/ (React)
├── src/components/LaPremiereSection.jsx (Premiere UI component)
├── src/pages/FilmDetail.jsx (integra LaPremiereSection)
```

## Integrazioni
- OpenAI GPT-4o-mini (Text) + GPT-Image-1 (Image) — Emergent LLM Key
- MongoDB Atlas (prod) / Local MongoDB (dev)

## Completato

### Fix Deploy Railway + Emergent (Apr 2026)
- **Dockerfile**: Aggiunto `GENERATE_SOURCEMAP=false` per ridurre consumo memoria durante build
- **database.py**: Fix `load_dotenv(override=False)`, priorità env vars K8s su .env file, fallback DB_NAME da env
- **server.py**: Fix mount build dir condizionale (evita crash quando build non esiste)

### Sistema "La Prima" — Premiere (Apr 2026)
- **STEP 1-2**: Backend — Modello premiere, 48 città con pesi e generi, calcolo impatto nascosto
- **STEP 3-4**: Backend — Boost/decay revenue iniziale, sistema outcome (standing_ovation, warm, mixed, lukewarm)
- **STEP 5-6**: Backend — Sistema eventi notifiche post-prima, integrazione scheduler_tasks
- **STEP 7**: Frontend — `LaPremiereSection.jsx` completo: enable, configurazione città/data/delay, countdown, outcome, placeholder immagine 16:9. Integrato in FilmDetail.jsx
- **STEP 8**: Verifica regole — Solo film (no serie/anime), solo status eligibili (coming_soon, completed, pending_release), validazione città, non modificabile dopo setup, errori chiari

### Sistema Sponsor (Apr 2026)
- Modello, endpoint, deal, impatto revenue, memoria performance (Steps 1-5 completi)

### Skill System Refactoring (Apr 2026)
- Unificazione ACTOR_SKILLS (13 skill), fix scuola, quality genre-aware

## In Progress
- Step 14 Modularizzazione GAME CORE (PAUSED)

## Backlog (P1)
- 20 poster film mancanti/404
- Modularizzazione endpoint rimanenti in server.py
- Sistema "Previsioni Festival"
- Marketplace diritti TV/Anime

## Backlog (P2+)
- Contest Page Mobile Layout rotto
- Velion features (Mood, Chat, Levels, AI Memory)
- CinePass + Stripe, Push notifications, RBAC
- Eventi globali, Guerre tra Major

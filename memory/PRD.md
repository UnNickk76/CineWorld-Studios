# CineWorld Studio's — PRD

## Problema Originale
Gioco browser-based di simulazione studio cinematografico. Full-stack React + FastAPI + MongoDB.

## Refactoring in corso
Modularizzazione graduale di `server.py` in route files separati. Attualmente a Step 14 (GAME CORE: films, film_engagement, production_studio) — **PAUSED**.

## Architettura
```
/app/backend/
├── server.py (monolite in refactoring)
├── cast_system.py (generazione cast, ACTOR_SKILLS, GENRE_SKILL_MAPPING)
├── challenge_system.py
├── game_systems.py
├── emerging_screenplays.py
├── database.py
├── routes/
│   ├── cast.py
│   ├── casting_agency.py
│   ├── acting_school.py
│   ├── film_pipeline.py
│   ├── series_pipeline.py
│   ├── sequel_pipeline.py
│   ├── cinepass.py
│   ├── films.py (creato, da popolare — Step 14)
│   ├── film_engagement.py (creato, da popolare — Step 14)
│   └── ... (altre route)
/app/frontend/ (React)
```

## Integrazioni 3rd Party
- OpenAI GPT-4o-mini (Text Generation) — Emergent LLM Key
- OpenAI GPT-Image-1 (Image Generation) — Emergent LLM Key
- MongoDB Atlas

## Completato

### Skill System Refactoring (Apr 2026)
- **STEP 1**: Unificazione sistema skill attori — rimosso ACTOR_SKILL_NAMES (10 skill inglesi), ora usa SOLO ACTOR_SKILLS (13 skill codificate). Aggiunto LEGACY_SKILL_MAPPING + conversione on-read. Migrati 6 documenti DB legacy.
- **STEP 2**: Fix scuola di recitazione — generate_final_skills() ora genera 8 skill su 13 (non 13 su 13). Initial skills sono sottoinsieme delle final.
- **STEP 3**: Skill reali nella qualità film — formula genre-aware (70% genre_avg + 30% full_avg) invece di media generica. Debug log + advanced_factors._skill_debug.
- **STEP 4**: Verifica coerenza — corretti game_systems.py, cinepass.py, server.py (SKILL_TYPES + enrollment scuola). Zero documenti legacy rimasti.

### Report generati
- `/api/static/report_skill_system.txt` — Analisi pre-refactoring
- `/api/static/report_skill_refactoring.txt` — Report post-refactoring

## In Progress
- Step 14 Modularizzazione GAME CORE (PAUSED)

## Backlog (P1)
- 20 poster film mancanti/404 (rigenerazione AI)
- Modularizzazione endpoint rimanenti in server.py
- Sistema "Previsioni Festival"
- Marketplace diritti TV/Anime

## Backlog (P2+)
- Contest Page Mobile Layout rotto (ricorrente 14+)
- Velion Mood Indicator
- Chat Evolution
- CinePass + Stripe
- Push notifications
- Velion Levels
- RBAC
- Eventi globali
- Guerre tra Major
- Velion AI Memory

## Credenziali Test
- User: fandrex1@gmail.com / Ciaociao1
- Admin: test@cineworld.com / test123

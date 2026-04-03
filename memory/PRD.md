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
├── database.py
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

### Sistema "La Prima" — Premiere (Apr 2026)
- **STEP 1-2**: Backend — Modello premiere, 48 città con pesi e generi, calcolo impatto nascosto
- **STEP 3-4**: Backend — Boost/decay revenue iniziale, sistema outcome (standing_ovation, warm, mixed, lukewarm)
- **STEP 5-6**: Backend — Sistema eventi notifiche post-prima, integrazione scheduler_tasks
- **STEP 7**: Frontend — `LaPremiereSection.jsx` completo: enable, configurazione città/data/delay, countdown, outcome, placeholder immagine 16:9. Integrato in FilmDetail.jsx
- **STEP 8**: Verifica regole — Solo film (no serie/anime), solo status eligibili (coming_soon, completed, pending_release), validazione città, non modificabile dopo setup, errori chiari

### Sistema Sponsor (Apr 2026)
- **STEP 1**: Modello sponsor con tier A/B/C, 48 sponsor generati, 3 endpoint (list, detail, stats)
- **STEP 2**: Aggiunta/rimozione sponsor ai progetti (max 6, solo in status validi), ordinamento per affinità genere
- **STEP 3**: Calcolo deal — `deal_value = base_offer × (1 + hype/100) × memory_modifier × genre_bonus`. Deal accreditato ai fondi utente
- **STEP 4**: Impatto economico — marketing_boost sui primi 3 giorni, rev_share sottratto giornalmente. Applicato in scheduler_tasks.py
- **STEP 5**: Memoria sponsor — storico deal in `sponsor_deals`, avg_performance aggiornata, bonus/malus su offerte future (+15% max se positivo, -20% se negativo)

### Skill System Refactoring (Apr 2026)
- Unificazione su ACTOR_SKILLS (13 skill, 8 per membro)
- Fix scuola recitazione (8/13)
- Quality film genre-aware (70% genre + 30% full)
- Zero legacy rimasti

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

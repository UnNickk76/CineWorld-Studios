# CineMaster - Product Requirements Document

## Original Problem Statement
Full-stack cinematic management game (React + FastAPI + MongoDB).

## Architecture
- Frontend: React (CRA + craco) + Tailwind CSS v3 + Shadcn UI + Framer Motion
- Backend: FastAPI + MongoDB Atlas
- 3rd Party: OpenAI GPT-4o-mini, GPT-Image-1 via Emergent LLM Key, APScheduler
- Deploy: Dockerfile multi-stage (single service on Railway) + Emergent native

## Credentials
- Admin account: fandrex1@gmail.com / Fandrel2776
- Emilians account: emiliano.andreola1@gmail.com / Emiliano.77
- Test admin: test@cineworld.com / test123
- Other users temporary password: CineWorld2026!

## Railway/Emergent Deploy Config
- Dockerfile builds React + serves via FastAPI
- `REACT_APP_BACKEND_URL=""` in build (relative paths)
- `--extra-index-url` for emergentintegrations
- Health check: `/health` (app-level) + `/api/health` (api_router)
- `railway.toml`: healthcheckPath=/health, healthcheckTimeout=120

## DB Config
- MONGO_URL=mongodb+srv://fandrex1_db_user:Cineworld123@cluster0.6q21tmr.mongodb.net/cineworld
- DB_NAME=cineworld (default "test" in database.py)
- JWT_SECRET=cineworld-studio-secret-key-2024-secure

## Completed (this session)
- [2026-04-01] Production data extraction (13 users, 110 films, 86 posters, festivals, challenges, etc.)
- [2026-04-01] Infrastructure recovery: NeoMorpheus 12 items, Emilians 7 items, TV stations, series
- [2026-04-01] Admin export endpoint: GET /api/admin/export-db
- [2026-04-01] JSON backup in /app/backup_produzione/
- [2026-04-01] Health check fix: /api/health added for Emergent deploy
- [2026-04-01] Startup refactor: heavy init deferred to background tasks
- [2026-04-01] Poster regeneration: POST /api/series/{id}/generate-poster, POST /api/anime/{id}/generate-poster
- [2026-04-01] Bug fix: /series/my now queries db.tv_series (correct collection)
- [2026-04-01] SagasSeriesPage: poster thumbnails + "Rigenera Locandina" buttons
- [2026-04-01] uploads directory: os.makedirs at server start + StaticFiles mount
- [2026-04-01] Production loop fix: finalize_production, release_production, prevent_series_loop utilities
- [2026-04-01] database.py: connection timeouts (2s), clean config
- [2026-04-01] auth login: bcrypt.checkpw direct + error logging

## Upcoming (P1)
- Sistema "Previsioni Festival"
- Marketplace TV/Anime rights

## Backlog (P2+)
- Contest Page mobile layout (broken, recurrence 13+)
- Velion features, CinePass+Stripe, Push notifications, RBAC, Eventi globali, Guerre tra Major, Velion AI Memory

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

## Completed
- [2026-04-01] Production data extraction (13 users, 110 films, 86 posters, festivals, challenges, etc.)
- [2026-04-01] Infrastructure recovery, Admin export endpoint, JSON backup
- [2026-04-01] Health check fix, Startup refactor, Poster regeneration endpoints
- [2026-04-01] Bug fixes: /series/my collection, production loops, uploads directory
- [2026-04-01] database.py: clean config, auth login: bcrypt.checkpw direct
- [2026-04-02] **LOGIN FIX**: Root cause was 2.7MB base64 avatar in user document. Added persist_base64_avatar() to convert base64 to file. Login: 29s/2.7MB → 0.7s/990B
- [2026-04-02] **POSTER COMPRESSION**: Auto-compression in poster_storage.py (800x1200 JPEG q82). Compressed 44 existing posters: 38MB → 3MB (92% reduction). Updated DB refs .png → .jpg. Also fixed avatar generation to save directly to file.

## Upcoming (P1)
- Sistema "Previsioni Festival"
- Marketplace TV/Anime rights

## Backlog (P2+)
- Contest Page mobile layout (broken, recurrence 14+)
- Velion features, CinePass+Stripe, Push notifications, RBAC, Eventi globali, Guerre tra Major, Velion AI Memory

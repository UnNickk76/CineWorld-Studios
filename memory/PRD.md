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
- DB_NAME=cineworld
- JWT_SECRET=cineworld-studio-secret-key-2024-secure

## Completed
- [2026-04-01] Production data extraction (13 users, 110 films, 86 posters, festivals, challenges, etc.)
- [2026-04-01] Infrastructure recovery, Admin export endpoint, JSON backup
- [2026-04-01] Health check fix, Startup refactor, Poster regeneration endpoints
- [2026-04-01] Bug fixes: /series/my collection, production loops, uploads directory
- [2026-04-01] database.py: clean config, auth login: bcrypt.checkpw direct
- [2026-04-02] **LOGIN FIX**: Root cause: 2.7MB base64 avatar. Added persist_base64_avatar(). Login 29s/2.7MB → 0.7s/990B
- [2026-04-02] **POSTER COMPRESSION**: Auto-compression in poster_storage.py (800x1200 JPEG q82) for NEW posters only. Compressed 44 existing disk posters: 38MB → 3MB
- [2026-04-02] **API RESPONSE OPTIMIZATION**: Root cause of missing films/series/anime: MongoDB responses too large (daily_revenues 60KB/film, cast 15KB, attendance_history 21KB). Added inclusive projections to /films/my, /dashboard/batch, /films/my/featured excluding heavy fields for list views. Results: /films/my 1.4MB→31KB (0.86s), /dashboard/batch 321KB→13KB (1.4s), /featured 18KB→4.8KB (0.66s). Film detail page still returns all fields.
- [2026-04-02] **POSTER ENDPOINT HARDENED**: Now tries both .png and .jpg extensions for fallback serving
- [2026-04-02] **DB POSTER URLs RESTORED**: Reverted poster_url changes (.png→.jpg→original) using production backup as source of truth

## IMPORTANT: DB Sync Issue
The .it production site uses data that includes 23 film posters and 4 series posters NOT present in MongoDB Atlas. These were only on the .it server's local disk. Migration from .it to Atlas/preview/Railway requires syncing these files. The .it DB is the source of truth.

## Upcoming (P1)
- Sistema "Previsioni Festival"
- Marketplace TV/Anime rights

## Backlog (P2+)
- Contest Page mobile layout (broken, recurrence 14+)
- Velion features, CinePass+Stripe, Push notifications, RBAC, Eventi globali, Guerre tra Major, Velion AI Memory

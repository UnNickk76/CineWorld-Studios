# CineMaster - Product Requirements Document

## Original Problem Statement
Full-stack cinematic management game (React + FastAPI + MongoDB). Players manage film studios, compete in PvP arenas, and build entertainment empires.

## Architecture
- **Frontend**: React (CRA + craco) + Tailwind CSS + Shadcn UI + Framer Motion → builds to `frontend/build/`
- **Backend**: FastAPI + MongoDB
- **3rd Party**: OpenAI GPT-4o-mini (text), GPT-Image-1 (images) via Emergent LLM Key, APScheduler
- **Path Resolution**: Strictly relative paths (`../`, `./`). NO `@/` aliases.
- **PostCSS**: Uses `@tailwindcss/postcss` plugin
- **Deploy**: Dockerfile multi-stage (Node build frontend → Python serve backend + static files)

## Credentials
- Test account: fandrex1@gmail.com / Ciaociao1

## Completed Features
- OutcomePopup fix (framer-motion overlay instead of Radix Dialog)
- MongoDB dump export
- Full `@/` alias removal across entire frontend
- PostCSS config fix (`@tailwindcss/postcss`)
- Dockerfile multi-stage per Railway deploy
- Unconditional SPA serving in FastAPI (catch-all route always registered)
- Fixed `emergentintegrations` install (extra-index-url in Dockerfile)
- Added gcc for native Python deps compilation
- Proper CMD exec form for Railway $PORT expansion

## Railway Deploy Configuration
- `Dockerfile` at repo root handles both frontend build and backend setup
- **CRITICAL**: `--extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/` required for emergentintegrations
- `REACT_APP_BACKEND_URL=""` by default (relative paths for same-domain deploy)
- Railway provides `PORT` env var automatically
- Required env vars: `MONGO_URL`, `DB_NAME`, `JWT_SECRET`, `EMERGENT_LLM_KEY`, `CORS_ORIGINS`

## Upcoming Tasks (P1)
- Sistema "Previsioni Festival" (betting on festival winners)
- Marketplace for TV/Anime rights

## Backlog (P2+)
- Contest Page mobile layout (recurring issue 12+ times)
- Velion Mood Indicator, Chat Evolution, CinePass+Stripe
- Push notifications, Velion Levels, RBAC
- Eventi globali, Guerre tra Major, Velion AI Memory

## Constraints
- User forbids testing_agent_v3_fork usage (save credits)
- No refactoring of server.py
- Language: Italiano
- Never use `@/` imports — always relative paths

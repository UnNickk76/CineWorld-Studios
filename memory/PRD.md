# CineMaster - Product Requirements Document

## Original Problem Statement
Full-stack cinematic management game (React + FastAPI + MongoDB). Players manage film studios, compete in PvP arenas, and build entertainment empires.

## Architecture
- **Frontend**: React + Tailwind CSS + Shadcn UI + Framer Motion
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
- PostCSS config fix for Railway build (`@tailwindcss/postcss`)
- Dockerfile per Railway deploy — multi-stage build
- **Unconditional SPA serving** — FastAPI always registers catch-all route for frontend, searches build dir at startup, excludes /api/*, /health, /docs

## Railway Deploy Configuration
- `Dockerfile` at repo root handles both frontend build and backend setup
- `REACT_APP_BACKEND_URL=""` by default (relative paths for same-domain deploy)
- Can override via Docker build arg: `--build-arg REACT_APP_BACKEND_URL=https://your-domain.com`
- Railway provides `PORT` env var automatically — CMD uses `${PORT:-8001}`
- Required env vars on Railway: `MONGO_URL`, `DB_NAME`, `JWT_SECRET`, `EMERGENT_LLM_KEY`, `CORS_ORIGINS`

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

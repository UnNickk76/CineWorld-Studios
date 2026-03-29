# CineMaster - Product Requirements Document

## Original Problem Statement
Full-stack cinematic management game (React + FastAPI + MongoDB). Players manage film studios, compete in PvP arenas, and build entertainment empires.

## Architecture
- **Frontend**: React (CRA + craco) + Tailwind CSS v3 + Shadcn UI + Framer Motion → builds to `frontend/build/`
- **Backend**: FastAPI + MongoDB
- **3rd Party**: OpenAI GPT-4o-mini (text), GPT-Image-1 (images) via Emergent LLM Key, APScheduler
- **Path Resolution**: Strictly relative paths (`../`, `./`). NO `@/` aliases.
- **PostCSS**: Uses `tailwindcss` v3 directly (NOT @tailwindcss/postcss v4!)
- **Deploy**: Dockerfile multi-stage (Node build frontend → Python serve backend + static files)

## Credentials
- Test account: fandrex1@gmail.com / Ciaociao1

## Completed Features
- OutcomePopup fix (framer-motion overlay instead of Radix Dialog)
- MongoDB dump export
- Full `@/` alias removal across entire frontend
- **Fixed Tailwind PostCSS conflict**: removed @tailwindcss/postcss v4 (was bringing tailwindcss v4 as transitive dep, breaking v3 project). Restored `tailwindcss: {}` in postcss.config.js
- Dockerfile multi-stage per Railway deploy with emergentintegrations extra-index-url
- Unconditional SPA serving in FastAPI

## Railway Deploy Configuration
- `Dockerfile` at repo root handles both frontend build and backend setup
- `--extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/` for emergentintegrations
- `REACT_APP_BACKEND_URL=""` by default (relative paths for same-domain deploy)
- Railway provides `PORT` env var automatically
- Required env vars: `MONGO_URL`, `DB_NAME`, `JWT_SECRET`, `EMERGENT_LLM_KEY`, `CORS_ORIGINS`

## IMPORTANT: Do NOT install @tailwindcss/postcss
The project uses Tailwind CSS v3. The @tailwindcss/postcss package is for v4 only and brings tailwindcss@4 as a transitive dependency, which breaks the entire build.

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

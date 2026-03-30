# CineMaster - Product Requirements Document

## Original Problem Statement
Full-stack cinematic management game (React + FastAPI + MongoDB).

## Architecture
- Frontend: React (CRA + craco) + Tailwind CSS v3 + Shadcn UI + Framer Motion → `frontend/build/`
- Backend: FastAPI + MongoDB
- 3rd Party: OpenAI GPT-4o-mini, GPT-Image-1 via Emergent LLM Key, APScheduler
- Path Resolution: Relative paths only. NO `@/` aliases
- PostCSS: `tailwindcss: {}` (v3 — do NOT use @tailwindcss/postcss v4)
- Deploy: Dockerfile multi-stage

## Credentials
- Test account: fandrex1@gmail.com / Ciaociao1

## Railway Deploy — Key Config
- Dockerfile: `RUN REACT_APP_BACKEND_URL="" yarn build` (shell var overrides .env)
- `--extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/` for emergentintegrations
- CMD: `uvicorn server:app --host 0.0.0.0 --port ${PORT:-8001}`
- Required env vars: MONGO_URL, DB_NAME, JWT_SECRET, EMERGENT_LLM_KEY, CORS_ORIGINS

## CRITICAL: REACT_APP_BACKEND_URL
- craco.config.js loads .env via `require("dotenv").config()` BEFORE CRA's env loading
- .env.production does NOT override because dotenv already set the var
- MUST use shell env var in build command: `REACT_APP_BACKEND_URL="" yarn build`
- Empty string = relative paths (/api/...) = correct for same-domain Railway deploy

## Completed
- OutcomePopup fix, MongoDB dump, @/ alias removal
- PostCSS v3/v4 conflict resolved
- Dockerfile with emergentintegrations, gcc, proper CMD
- Unconditional SPA serving in FastAPI
- **Fixed blank page: REACT_APP_BACKEND_URL="" in build**

## Upcoming (P1)
- Sistema "Previsioni Festival"
- Marketplace TV/Anime rights

## Backlog (P2+)
- Contest Page mobile layout
- Velion features, CinePass+Stripe, Push notifications, RBAC, Eventi globali

## Constraints
- No testing_agent (save credits), No server.py refactoring, Language: Italiano

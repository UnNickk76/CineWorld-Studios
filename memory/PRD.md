# CineMaster - Product Requirements Document

## Original Problem Statement
Full-stack cinematic management game (React + FastAPI + MongoDB).

## Architecture
- Frontend: React (CRA + craco) + Tailwind CSS v3 + Shadcn UI + Framer Motion
- Backend: FastAPI + MongoDB Atlas
- 3rd Party: OpenAI GPT-4o-mini, GPT-Image-1 via Emergent LLM Key, APScheduler
- Path Resolution: Relative paths only. NO `@/` aliases
- PostCSS: `tailwindcss: {}` (v3 — do NOT use @tailwindcss/postcss v4)
- Deploy: Dockerfile multi-stage (single service on Railway)

## Credentials
- Admin account: fandrex1@gmail.com / Fandrel2776
- Other users temporary password: CineWorld2026!

## Railway Deploy — Key Config
- Dockerfile: `RUN REACT_APP_BACKEND_URL="" npm run build` (shell var overrides .env)
- `--extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/` for emergentintegrations
- CMD: `uvicorn server:app --host 0.0.0.0 --port ${PORT:-8001}`
- Required env vars: MONGO_URL, DB_NAME, JWT_SECRET, EMERGENT_LLM_KEY, CORS_ORIGINS

## CRITICAL: REACT_APP_BACKEND_URL
- craco.config.js loads .env via `require("dotenv").config()` BEFORE CRA's env loading
- MUST use shell env var in build command: `REACT_APP_BACKEND_URL="" npm run build`
- Empty string = relative paths (/api/...) = correct for same-domain Railway deploy

## Completed
- OutcomePopup fix, MongoDB dump, @/ alias removal
- PostCSS v3/v4 conflict resolved
- Dockerfile with emergentintegrations, gcc, proper CMD
- Unconditional SPA serving in FastAPI
- Fixed blank page: REACT_APP_BACKEND_URL="" in build
- **[2026-04-01] Production data extraction from live API to MongoDB Atlas**
  - 13 users migrated (comprehensive data from leaderboard + admin endpoints)
  - 110 films migrated (full 74-field detail per film)
  - 86 poster files recovered (binary images)
  - Festivals, challenges, events, release notes, system notes, cinema news migrated
  - Likes collection reconstructed from film data
  - Migration `fix_fandrex_password_v1` disabled to preserve production password

## Data Migration Notes (2026-04-01)
### Successfully migrated via REST API:
- users (13), films (110), poster_files (86), challenges (8), festivals (3)
- festival_awards (7), cinema_news (10), emerging_screenplays (10), events (8)
- release_notes (129), system_notes (10), virtual_reviews (50), likes (8)
- film_comments (1), film_drafts (5), majors (1), infrastructure (1), system_config (1)

### NOT migrated (no global REST API available):
- chat_messages, chat_rooms (user-specific, no list-all endpoint)
- friendships, follows (no global endpoint)
- notifications (user-specific)
- Other users' series, drafts, pre-films (only admin's accessible)
- 20 posters returned 404 (missing on production too)

### Password handling:
- Admin (fandrex1@gmail.com): production password preserved (Fandrel2776)
- All other users: temporary password set (CineWorld2026!)

## Upcoming (P1)
- Sistema "Previsioni Festival" (scommesse vincitori festival)
- Marketplace TV/Anime rights

## Backlog (P2+)
- Contest Page mobile layout (broken - recurrence 13+)
- Velion features, CinePass+Stripe, Push notifications, RBAC, Eventi globali, Guerre tra Major, Velion AI Memory

## Constraints
- No testing_agent (save credits)
- No server.py refactoring without explicit permission
- Language: Italiano

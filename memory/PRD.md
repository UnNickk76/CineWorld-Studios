# CineMaster - Product Requirements Document

## Original Problem Statement
Full-stack cinematic management game (React + FastAPI + MongoDB).

## Architecture
- Frontend: React (CRA + craco) + Tailwind CSS v3 + Shadcn UI + Framer Motion
- Backend: FastAPI + MongoDB Atlas
- 3rd Party: OpenAI GPT-4o-mini, GPT-Image-1 via Emergent LLM Key, APScheduler
- Deploy: Emergent native (.it) + Railway (test)

## Credentials
- Admin account: fandrex1@gmail.com / Fandrel2776
- Emilians account: emiliano.andreola1@gmail.com / Emiliano.77
- Test admin: test@cineworld.com / test123
- Other users temporary password: CineWorld2026!

## DB Config
- MONGO_URL read via dotenv_values() directly from .env (override=True for load_dotenv)
- Atlas: mongodb+srv://fandrex1_db_user:Cineworld123@cluster0.6q21tmr.mongodb.net/cineworld
- JWT_SECRET=cineworld-studio-secret-key-2024-secure

## Completed (this session 2026-04-02)
- **LOGIN FIX**: Base64 avatar 2.7MB → file on disk. Login 29s → 0.7s
- **API OPTIMIZATION**: Inclusive projections for list endpoints. /films/my 1.4MB→31KB, /dashboard/batch 321KB→13KB
- **POSTER COMPRESSION**: Auto-compression for new posters (800x1200 JPEG q82). Compressed 44 disk posters: 38MB→3MB
- **POSTER SYNC**: Downloaded 4 missing series posters from .it site
- **POSTER ENDPOINT**: Fallback .png/.jpg extension handling
- **DEPLOY FIX (passlib)**: Removed passlib==1.7.4 from requirements.txt (incompatible with bcrypt 4.1.3)
- **DEPLOY FIX (MONGO_URL)**: database.py reads MONGO_URL via dotenv_values() to bypass Emergent's env override + load_dotenv(override=True) for JWT_SECRET etc.
- **STORAGE OPTIMIZATION**: MongoDB Atlas 357MB → 50MB (86% reduction). Compressed poster binary data in MongoDB + drop/recreate collections to reclaim dead space (cinema_news 89MB→0MB, poster_files 206MB→9MB)
- **DIAGNOSTIC ENDPOINT**: GET /api/debug/login-check for deployment debugging
- **MODULARIZATION Step 1 (Cast/People)**: Moved 17 Cast/People endpoints from server.py → routes/cast.py. Includes: /actors, /directors, /screenwriters, /composers, /cast/available, /cast/search-advanced, /cast/skill-list, /cast/offer, /cast/rejections, /cast/renegotiate, /cast/skills, /cast/initialize, /cast/stats, /cast/new-arrivals, /cast/bonus-preview, /cast/affinity-preview, /actor-roles. Also moved: REJECTION_REASONS, ACTOR_ROLES constants, calculate_rejection_chance(), initialize_cast_pool_if_needed(). Old code commented out in server.py (not deleted).
- **MODULARIZATION Step 2 (Film Drafts & Pre-Films)**: Moved 16 endpoints from server.py → routes/film_pipeline.py. Includes: /films/drafts (CRUD + resume), /pre-films (CRUD + engage, release, convert, check-rescissions, process-rescission, dismiss-cast, public/expired), /negotiations/{id}/renegotiate. Also moved: FilmDraft, PreFilmCreate, PreEngagementRequest, ReleaseCastRequest models + PRE_FILM_DURATION_DAYS, PRE_ENGAGEMENT_ADVANCE_PERCENT, CAST_PATIENCE_DAYS constants + calculate_release_penalty(). RenegotiateRequest renamed to PreFilmNegotiateRequest (avoids naming conflict). Old code commented out.

- **MODULARIZATION Step 3 (Series/Saga)**: Moved 8 endpoints from server.py → routes/series_pipeline.py. Includes: /saga/can-create, /films/{id}/can-create-sequel, /films/{id}/create-sequel, /series/can-create, /series/create, /series/my, /series/{id}, /series/{id}/permanent. Also moved: SAGA/SERIES/ANIME_REQUIRED constants, CreateSequelRequest, CreateSeriesRequest models. Old code commented out.
- **MODULARIZATION Step 4 (Users/Chat/Social)**: Moved 26 endpoints. Users (13) → routes/users.py (new): /users/heartbeat, /users/online, /users/presence, /users/search, /users/all, /users/all-players, /users/{id}, /users/{id}/social-card, /users/{id}/full-profile, /users/set-timezone, /users/{id}/badges, /players/{id}/profile, /user/is-creator. Chat (9) → routes/chat.py (new): /chat/bots, /chat/rooms (GET+POST), /chat/direct/{id}, /chat/rooms/{id}/messages, /chat/messages, /chat/messages/{id}/image (DELETE), /chat/upload-image, /chat-images/{filename}. Social (4) → routes/social.py (append): /reports, /creator/messages (GET+reply+mark-read). Old code commented out.
- **MODULARIZATION Step 5 (Festivals)**: Moved 35 endpoints from server.py → routes/festivals.py (new). Old code commented out.
- **MODULARIZATION Step 6 (Challenges/PVP)**: Moved 22 endpoints from server.py → routes/challenges.py (new). Includes: daily/weekly challenges (GET + claim), PVP (send, respond, submit-result, pending), challenge system (types, skills, my-films, create, join, waiting, my, leaderboard, limits, detail, stats, cancel, toggle-offline, offline-battle, resend). Also moved: ChallengeRequest, ChallengeResponse, ChallengeCreate models. Old code commented out.

## 20 Film Posters Missing
These posters don't exist anywhere (404 on .it too). Need AI regeneration:
- Referenced by films but never backed up to MongoDB

## Upcoming (P1)
- Modularizzazione server.py — prossimi gruppi (dopo conferma utente per ogni step)
- Sistema "Previsioni Festival"
- Marketplace TV/Anime rights

## Backlog (P2+)
- Contest Page mobile layout (broken, recurrence 14+)
- Velion features, CinePass+Stripe, Push notifications, RBAC, Eventi globali, Guerre tra Major, Velion AI Memory

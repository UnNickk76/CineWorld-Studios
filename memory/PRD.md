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

- **MODULARIZATION Step 7 (AI/Poster/Trailer)**: Moved 15 route decorators (14 endpoint functions) + 1 background task from server.py → routes/ai.py (new, 1054 lines). Includes: /ai/screenplay, /ai/poster/start, /ai/poster/status/{task_id}, /ai/poster, /ai/translate, /ai/soundtrack-description, /ai/generate-trailer, /ai/trailer-cost, /trailers/{film_id}.mp4, /films/{film_id}/trailer-status, /films/{film_id}/reset-trailer, /films/{film_id}/poster, /series/{series_id}/generate-poster, /anime/{series_id}/generate-poster, /films/{film_id}/regenerate-poster. Also moved: ScreenplayRequest, PosterRequest, TranslationRequest, SoundtrackRequest, TrailerRequest models + POSTER_GENRE_THEMES, POSTER_DEFAULT_THEMES, POSTER_PATTERNS, GENRE_POSTER_IMAGES constants + _overlay_poster_text(), _generate_fallback_poster(), generate_trailer_task_sora2() helpers + poster_tasks dict. EMERGENT_LLM_KEY properly ported. Old code commented out. server.py: 19589→18592 lines. Also fixed pre-existing bug: added `from game_state import online_users` import in server.py.
- **MODULARIZATION Step 9 (Economy/Revenue)**: Moved 13 endpoints from server.py → routes/economy.py (new, 1015 lines). Includes: /stats/detailed, /statistics/global, /statistics/my, /dashboard/batch, /revenue/pending-all, /revenue/collect-all, /films/{film_id}/hourly-revenue, /films/{film_id}/process-hourly-revenue, /films/process-all-hourly, /player/rating-stats, /catchup/process, /activity/heartbeat, /admin/add-cinepass. Dependencies imported from game_systems. Old code commented out. server.py now ~18594 lines.

- **MODULARIZATION Step 10 (Dashboard/Stats)**: Moved 20 endpoints from server.py → routes/dashboard.py (new, 1771 lines). Includes: /cineboard/attendance, /cinema-news, /discovered-stars, /journal/virtual-reviews, /journal/other-news, /release-notes (GET), /release-notes (POST creator), /release-notes/unread-count, /release-notes/mark-read, /admin/release-notes (POST), /leaderboard/local/{country}, /cineboard/now-playing, /cineboard/hall-of-fame, /cineboard/daily, /cineboard/weekly, /cineboard/series-weekly, /cineboard/anime-weekly, /cineboard/tv-stations-alltime, /cineboard/tv-stations-weekly, /cineboard/tv-stations-daily. Also moved: RELEASE_NOTES data, DEFAULT_SYSTEM_NOTES, TTLCache class, calculate_cineboard_score(), NewReleaseNote model, initialize_release_notes(), initialize_system_notes(). Old code commented out. 18/20 endpoints return 200 OK; 2 (now-playing, hall-of-fame) are slow due to pre-existing heavy MongoDB queries (not a regression). (2026-04-02)

- **PERFORMANCE FIX (CineBoard)**: Ottimizzati `cineboard/now-playing` e `cineboard/hall-of-fame` in `routes/dashboard.py`. Aggiunta projection mirata (esclusi `daily_revenues` 63KB, `attendance_history` 21KB, `cast`, `screenplay`, `ai_interactions`, `hourly_revenues`, `cinema_distribution` per film). Rimosso `liked_by` dalla projection principale, sostituito con query parallela via `asyncio.gather`. Aggiunta cache TTL 60s per hall-of-fame. Aggiunti indici MongoDB `(status, cineboard_score)` e `liked_by`. Rimosso dead code (codice duplicato) alla fine di dashboard.py. **now-playing: 65.5s → 1.2s (53x)**, **hall-of-fame: 101.6s → 1.2s (85x)**. (2026-04-02)

- **MODULARIZATION Step 11 (Premiere/Tour)**: Moved 8 endpoints from server.py → routes/premiere.py (new). Includes: /premiere/invite, /premiere/invites, /premiere/view/{invite_id}, /tour/featured, /tour/cinema/{cinema_id}, /tour/cinema/{cinema_id}/visit, /tour/cinema/{cinema_id}/review, /tour/my-visits. Also moved: PremierInviteRequest model. Dependencies: INFRASTRUCTURE_TYPES, calculate_tour_rating from game_systems. Old code commented out. (2026-04-02)

- **MODULARIZATION Step 12 (Coming Soon + Major + Emerging Screenplays)**: Moved 16 endpoints from server.py → 3 new route files. `routes/coming_soon.py` (5): hype, interact, details, investigate-boycott, speed-up + helpers/constants. `routes/major.py` (5): my, create, invite, accept, challenge + models. `routes/emerging_screenplays.py` (6): list, count, mark-seen, detail, accept, admin/diagnose-screenplay + expire_old_screenplays. Old code commented out. (2026-04-02)

- **MODULARIZATION Step 14 (Game Core — Films, Engagement, Production Studio)**: Moved ~57 endpoints from server.py → 3 new route files. `routes/films.py` (28 endpoints): POST /films, GET /films/my, /films/pending, /films/shooting, /films/shooting/config, POST /films/{id}/start-shooting, /films/{id}/end-shooting-early, /films/{id}/release, GET /films/my/featured, /films/my/for-sequel, /films/cinema-journal, /films/available-for-rental, /films/my-available, /films/{id}/release-cinematic, /films/{id}, /films/{id}/distribution, DELETE /films/{id}, /films/{id}/permanent, /film-projects/{id}/permanent, GET /films/{id}/duration-status, POST /films/{id}/extend, /films/{id}/early-withdraw, GET /films/{id}/rerelease-status, POST /films/{id}/rerelease, /films/{id}/check-star-discoveries, /films/{id}/evolve-cast-skills, GET /films/{id}/event-bonus, GET /distribution/config + process_shooting_progress scheduler function + models (StartShootingRequest, FilmReleaseRequest). `routes/film_engagement.py` (15 endpoints): GET /films/{id}/actions, POST /films/{id}/action/create-star, /films/{id}/action/skill-boost, /films/{id}/user-rating, GET /films/{id}/ratings, /advertising/platforms, POST /films/{id}/advertise, /films/{id}/rate, /films/{id}/comment, GET /films/{id}/comments, /films/{id}/virtual-audience, POST /films/{id}/update-virtual-audience, GET /films/reviews-board, /films/{id}/tier-expectations. `routes/production_studio.py` (9 endpoints): GET /production-studio/status, /production-studios/unlock-status, POST /production-studio/pre-production/{id}, /production-studio/remaster/{id}, GET /production-studio/casting, POST /production-studio/casting/hire, /production-studio/generate-draft, GET /production-studio/drafts, DELETE /production-studio/drafts/{id} + models (PreProductionRequest, CastingHireRequest, StudioDraftRequest). Router ordering: film_engagement_router before films_router to prevent {film_id} from capturing static paths. Old code commented out. server.py ~17084 lines, ~9620 [MOVED] lines. (2026-04-02)

- **MODULARIZATION Step 15 (Events + Stars)**: Moved 5 endpoints from server.py → 2 new route files. `routes/events.py` (2): GET /events/active, GET /events/all. `routes/stars.py` (3): POST /stars/{id}/hire, GET /stars/hired, DELETE /stars/hired/{id}. Dependencies: game_systems (WORLD_EVENTS, get_active_world_events). 4 endpoint già spostati nello Step 14 (event-bonus, actions, create-star, skill-boost) lasciati nei file attuali. Old code commented out. (2026-04-02)

## 20 Film Posters Missing
These posters don't exist anywhere (404 on .it too). Need AI regeneration:
- Referenced by films but never backed up to MongoDB

- **BUGFIX Pipeline + Data Integrity (Step 15.5)**: (1) Screenplay: confermato che NON si perde — tutti gli update usano `$set`. (2) Pipeline: aggiunto guard atomico in `process_shooting_progress` (`update_one` con filtro `status: 'shooting'`) + skip per film con status cambiato. (3) Elementi fantasma: aggiunto filtro `status != 'deleted'` su `GET /films/{id}`, `/films/my`, `/films/cinema-journal`. (4) Debug: aggiunto log `[FILM CREATE]`, `[FILM SHOOTING]`, `[FILM RELEASE]`, `[PIPELINE]` con id+status per tracciamento. (2026-04-02)

## Upcoming (P1)
- Modularizzazione server.py — Step 16+ (attendere indicazioni utente per il prossimo gruppo)
- Sistema "Previsioni Festival"
- Marketplace TV/Anime rights

## Backlog (P2+)
- Contest Page mobile layout (broken, recurrence 14+)
- Velion features, CinePass+Stripe, Push notifications, RBAC, Eventi globali, Guerre tra Major, Velion AI Memory

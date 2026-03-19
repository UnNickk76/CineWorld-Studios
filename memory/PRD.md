# CineWorld Studio's - PRD

## Original Problem Statement
A cinematic empire game where users produce films, manage TV stations, compete in challenges, and build a Hollywood-style business empire.

## Core Requirements
- Film production pipeline (films, sequels, TV series, anime)
- Netflix-style TV station management
- Revenue/economy system with realistic box office simulation
- Social features (friends, chat, challenges)
- Leaderboards and festivals
- Persistent poster storage (MongoDB)
- **Casting Agency** with personal actors, genre specializations, XP/fame bonuses

## Architecture
- **Frontend**: React (CRA) with Tailwind + Shadcn UI
- **Backend**: FastAPI + MongoDB (Motor async driver)
- **Scheduler**: APScheduler for background tasks
- **AI**: OpenAI GPT-4o-mini (text) + GPT-Image-1 (posters) via Emergent LLM Key

## Key Data Models
- **users**: id, nickname, funds, total_lifetime_revenue, likeability_score, interaction_score, character_score
- **films**: id, user_id, title, total_revenue, realistic_box_office, agency_actors_count
- **agency_actors**: id, user_id, name, skills, skill_caps, hidden_talent, strong_genres, adaptable_genre, agency_name, films_worked
- **agency_recruits_log**: user_id, recruit_id, actor_id, week
- **poster_files**: filename, data, content_type, created_at
- **poster_tasks**: _id (task_id), status, poster_url, film_id
- **infrastructure**: owner_id, type, total_revenue, city, level

## Completed Features
- Full film production pipeline with sequel support
- TV series and anime production
- TV station management
- Poster persistence in MongoDB + async regeneration
- Friend system, chat, challenges, leaderboards
- Revenue collection system
- Cinema Journal, CineBoard, Hall of Fame, Festivals
- Infrastructure (cinemas, studios, etc.)
- Acting school

## Session Fixes (March 19, 2026)
### Bug Fixes
1. **Cinema Journal Posters**: Removed `poster_url: 0` from projection queries
2. **Dashboard Scores**: Added likeability/interaction/character scores to batch response
3. **Revenue Drop Fix (P0)**: Scheduler uses `max(current, calculated)` to never decrease total_revenue
4. **Revenue Display**: All endpoints use `max()` pattern instead of `or` for revenue

### New Feature: Casting Agency System
- **Agency Management Page** (`/casting-agency`): View actors, recruit from weekly pool, fire actors
- **Auto-naming**: Agency named after player's production house + "Agency"
- **Level System**: Lv1 = max 12 actors, 8 weekly recruits. Scales with level.
- **Genre Specializations**: Each actor has 2 strong genres + 1 adaptable genre
- **Dual Casting Flow**: Film/Series/Anime pipelines show "Dalla tua Agenzia" / "Dal Mercato" choice
- **XP/Fame Bonus**: 1 actor=+25%, 2=+35%, 3=+50%, 4+=+70% XP and fame
- **Actor Growth**: Skills improve gradually after each film, respecting hidden talent caps
- **Fire → Market**: Fired actors join global pool, available for anyone
- **School Integration**: School students available for casting (continue training + bonus)
- **Navigation**: "Agenzia" button added to production menu

## Pending Issues
- Contest Page mobile layout broken (P2)

## Backlog (P1)
- Marketplace for TV/Anime rights
- Improve chat system
- Agency actors appear in global market casting proposals

## Future (P2)
- RBAC system
- CinePass speed-up for pipeline steps
- Stripe integration
- PWA functionality
- Tutorial system
- Component decomposition
- Clickable agency name on actor cards

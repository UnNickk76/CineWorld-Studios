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
- **Rich Actor Data** across all 8,245 people (actors, directors, screenwriters, composers)

## Architecture
- **Frontend**: React (CRA) with Tailwind + Shadcn UI
- **Backend**: FastAPI + MongoDB (Motor async driver)
- **Scheduler**: APScheduler for background tasks
- **AI**: OpenAI GPT-4o-mini (text) + GPT-Image-1 (posters) via Emergent LLM Key

## Key Data Models
- **users**: id, nickname, funds, total_lifetime_revenue, likeability_score, interaction_score, character_score
- **films**: id, user_id, title, total_revenue, realistic_box_office, agency_actors_count
- **people**: id, name, type, skills, skill_caps, hidden_talent, strong_genres, strong_genres_names, adaptable_genre, adaptable_genre_name, gender, age, nationality, fame_score, fame_category
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
- Casting Agency system (recruit, manage, fire actors)
- Rich actor data for ALL 8,245 people (actors + directors + screenwriters + composers)
- Genre badges (strong + adaptable) in all casting UIs
- Gender icons on actor cards
- Revenue bug fix ($12.6M -> $93M+)
- Dashboard scores fix (Like/Social/Char)
- Cinema Journal posters fix
- Collect All $0 fix
- Empty Series Market fix
- Release Notes & System Notes updated

## Session Fixes (March 19, 2026 - Fork 2)
### Completed
1. **Rich Actor Data - Film Pipeline**: Enriched existing cast proposals with latest people data (strong_genres, adaptable_genre, skill_caps, hidden_talent) via batch lookup in `get_casting_films` endpoint
2. **Full People Migration**: Migrated all 6,187 non-actor people (2,061 directors, 2,062 screenwriters, 2,064 composers) to rich data model with genre preferences and skill caps
3. **PersonMeta Component Update**: Added genre badges (emerald for strong genres, amber for adaptable) to the shared PersonMeta component in FilmPipeline.jsx

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
- Casting Agency building (visual representation/upgrade path)

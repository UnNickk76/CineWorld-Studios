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

## Architecture
- **Frontend**: React (CRA) with Tailwind + Shadcn UI
- **Backend**: FastAPI + MongoDB (Motor async driver)
- **Scheduler**: APScheduler for background tasks
- **AI**: OpenAI GPT-4o-mini (text) + GPT-Image-1 (posters) via Emergent LLM Key

## Key Data Models
- **users**: id, nickname, funds, total_lifetime_revenue, likeability_score, interaction_score, character_score
- **films**: id, user_id, title, total_revenue, realistic_box_office, opening_day_revenue, quality_score, poster_url
- **poster_files**: filename, data (binary), content_type, created_at
- **poster_tasks**: _id (task_id), status, poster_url, film_id
- **infrastructure**: owner_id, type, total_revenue, city, level

## Completed Features
- Full film production pipeline
- TV series and anime production
- TV station management
- Poster persistence in MongoDB
- Async poster regeneration
- Friend system, chat, challenges
- Revenue collection system
- Cinema Journal, CineBoard, Hall of Fame
- Festival/Awards system
- Infrastructure (cinemas, studios, etc.)

## Session Fixes (March 19, 2026)
1. **Cinema Journal Posters**: Removed `poster_url: 0` from projection queries - posters now show
2. **Dashboard Scores**: Added likeability_score, interaction_score, character_score to dashboard batch response
3. **Revenue Drop Fix (P0)**: Scheduler now uses `max(current_total, realistic_box_office)` to never decrease total_revenue
4. **Revenue Display Fix**: All display logic changed from `or` to `max()` pattern across all endpoints

## Known Issues (Resolved)
- ~~Revenue drops after scheduler runs~~ FIXED
- ~~Like/Social/Char always show 50~~ FIXED  
- ~~Cinema Journal missing posters~~ FIXED

## Pending Issues
- Contest Page mobile layout broken (P2)

## Backlog (P1)
- Marketplace for TV/Anime rights
- Casting Agency building
- Improve chat system

## Future (P2)
- RBAC system
- CinePass speed-up for pipeline steps
- Stripe integration
- PWA functionality
- Tutorial system
- Component decomposition

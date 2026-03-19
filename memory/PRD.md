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
- **Guest Star Vocali** system for Anime and Animation films
- **Agency ↔ School** bidirectional transfer system

## Architecture
- **Frontend**: React (CRA) with Tailwind + Shadcn UI
- **Backend**: FastAPI + MongoDB (Motor async driver)
- **Scheduler**: APScheduler for background tasks
- **AI**: OpenAI GPT-4o-mini (text) + GPT-Image-1 (posters) via Emergent LLM Key

## Key Data Models
- **users**: id, nickname, funds, total_lifetime_revenue, likeability_score, interaction_score, character_score
- **films**: id, user_id, title, total_revenue, realistic_box_office, agency_actors_count
- **people**: id, name, type, skills, skill_caps, hidden_talent, strong_genres, strong_genres_names, adaptable_genre, adaptable_genre_name, gender, age, nationality, fame_score, fame_category
- **agency_actors**: id, user_id, name, skills, skill_caps, hidden_talent, strong_genres, adaptable_genre, agency_name, films_worked, from_school
- **casting_school_students**: id, user_id, name, base_skills, skill_caps, status, from_agency
- **tv_series**: id, user_id, title, type (tv_series/anime), cast (with is_guest_star flag)

## Completed Features

### Core Game
- Full film production pipeline with sequel support
- TV series and anime production
- TV station management
- Poster persistence in MongoDB + async regeneration
- Friend system, chat, challenges, leaderboards
- Revenue collection system
- Cinema Journal, CineBoard, Hall of Fame, Festivals
- Infrastructure (cinemas, studios, etc.)
- Acting school

### Casting System
- Casting Agency (recruit, manage, fire actors)
- Rich actor data for ALL 8,245 people
- Genre badges (strong + adaptable) in all casting UIs
- Gender icons on actor cards
- Agency actors visible in all market casting views ("I tuoi Attori" section)

### Guest Star Vocali (March 19, 2026)
- **Anime**: Casting is now Guest Star Vocali — only famous/superstar actors, optional, expensive (2x cost), gives quality+fame bonus on release
- **Film Animation**: Same guest star system for animation genre films
- Backend returns `is_guest_star_mode: true` and `can_skip: true` for anime
- Anime can advance to screenplay without any cast
- Guest star bonus: +3-6% quality per star + +5 fame per star on release

### Agency ↔ School Transfer (March 19, 2026)
- **Agenzia → Scuola**: "Manda a Scuola" button on agency actors (cost: $50K-$400K based on stars, 30 days pre-paid training)
- **Scuola → Agenzia**: "Trasferisci in Agenzia" button on school students
- New "Scuola" tab in Casting Agency page showing transferable students
- Actors transferred retain all skills, genres, and training progress

### Bug Fixes
- Revenue drop fix ($12.6M -> $93M+)
- Dashboard scores fix (Like/Social/Char)
- Cinema Journal posters fix
- Collect All $0 fix
- Empty Series Market fix
- Serie TV "Dal Mercato" crash fix (destructuring error)
- Rich actor data enrichment for existing cast proposals
- Full people migration (directors, screenwriters, composers)

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

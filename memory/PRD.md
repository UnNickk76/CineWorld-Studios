# CineWorld Studio's - Product Requirements Document

## Original Problem Statement
A full-stack movie studio simulation game where players create films, hire cast, manage budgets, and compete on leaderboards. Built with React frontend + FastAPI backend + MongoDB.

## User Personas
- **Primary:** Italian-speaking gamer who enjoys management/simulation games
- **Use case:** Create and manage a virtual movie production house

## Core Requirements
1. Film creation wizard (12 steps: title, equipment, cast, screenplay, poster, review)
2. Cast management with skills, fame, rejection/negotiation system
3. AI-powered screenplay and poster generation (OpenAI GPT-4o + GPT-Image-1)
4. Box office simulation with quality scoring and tier system
5. Social features (chat, leaderboard, CineBoard)
6. Emerging Screenwriters marketplace (pre-written screenplays with cast packages)
7. Draft/save system for incomplete films
8. Pre-engagement system for cast members
9. Multiple screenwriters support (1-5 per film)

## Architecture
```
/app/
├── backend/
│   ├── server.py           # Main FastAPI server (14K+ lines)
│   ├── game_systems.py     # Game mechanics
│   ├── cast_system.py      # Cast generation/management
│   └── routes/             # Auth, notifications, social, infrastructure, minigames
├── frontend/
│   └── src/
│       ├── App.js          # Main app with routing
│       ├── contexts/       # Auth, Language, Player contexts
│       └── pages/
│           ├── Dashboard.jsx
│           ├── FilmWizard.jsx       # Core film creation (1840+ lines)
│           ├── FilmDetail.jsx
│           ├── CineBoard.jsx        # Film rankings & social
│           └── EmergingScreenplays.jsx
```

## 3rd Party Integrations
- **OpenAI GPT-4o** (Text): Screenplay generation via Emergent LLM Key
- **OpenAI GPT-Image-1** (Image): Poster generation via Emergent LLM Key
- **Pillow (PIL)**: Fallback poster generation
- **APScheduler**: Background jobs
- **Resend**: Email service (requires user API key)

## What's Been Implemented (Complete)
- Complete film creation wizard with 12 steps
- Emerging Screenwriters feature
- AI poster generation with fallback
- Cast rejection/negotiation system
- Sequel/saga system
- Draft save/resume functionality
- Social features (chat, leaderboard, CineBoard)
- Minigames and challenges
- Multiple screenwriters (1-5) per film
- MongoDB indexes for performance
- CineBoard performance optimization (45MB → 37KB responses)
- Cast migration system (old skill system cleanup)
- Bottom nav: CineBoard + Bozze icons

## Bug Fixes (March 14, 2026)
- FIXED: Step 12 wizard error for emerging screenplays (actors format {id,role,fee} → {actor_id,role})
- FIXED: AI poster polling resilience (try/catch per poll, functional state updates)
- FIXED: CineBoard N+1 query problem (bulk fetches, field projections)
- FIXED: Owner avatar_url base64 bloating responses (2.6MB per owner → limited projection)
- FIXED: Cast IMDb ratings migration (zero ratings recalculated)
- FIXED: Cast skills normalization (all 8 skills, range 1-100)

## Known Issues
- **Production environment down** (external infrastructure issue - BLOCKED)
- Infrastructure Market feature disabled (P1)

## Backlog
- P1: Re-enable Infrastructure Market
- P2: CineCoins Purchase System (Stripe)
- P2: Major Studio Activities
- P3: Robust Data Migration Script

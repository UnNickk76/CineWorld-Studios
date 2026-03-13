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

## Architecture
```
/app/
├── backend/
│   ├── server.py           # Main FastAPI server (13,940 lines)
│   ├── game_systems.py     # Game mechanics
│   ├── cast_system.py      # Cast generation/management
│   ├── emerging_screenplays.py  # Screenplay generation helpers
│   ├── social_system.py    # Social features
│   └── routes/             # Auth, notifications, social, infrastructure, minigames
├── frontend/
│   └── src/
│       ├── App.js          # Main app with routing
│       ├── contexts/       # Auth, Language, Player contexts
│       └── pages/
│           ├── Dashboard.jsx
│           ├── FilmWizard.jsx       # Core film creation (1790 lines)
│           ├── FilmDetail.jsx
│           ├── EmergingScreenplays.jsx
│           └── [other pages]
```

## 3rd Party Integrations
- **OpenAI GPT-4o** (Text): Screenplay generation via Emergent LLM Key
- **OpenAI GPT-Image-1** (Image): Poster generation via Emergent LLM Key
- **Pillow (PIL)**: Fallback poster generation with dynamic genre-themed images
- **APScheduler**: Background jobs (revenue updates, screenplay generation, etc.)
- **Resend**: Email service (requires user API key)

## What's Been Implemented
- Complete film creation wizard with 12 steps
- Emerging Screenwriters feature (marketplace, purchase, locked wizard steps)
- AI poster generation with automatic fallback to Pillow-generated posters
- Cast rejection/negotiation system
- Sequel/saga system
- Draft save/resume functionality
- Social features (chat, leaderboard, CineBoard)
- Minigames and challenges
- Infrastructure system (disabled)

## Known Issues
- **Production environment down** (external infrastructure issue - BLOCKED)
- Infrastructure Market feature disabled (P1)

## Completed Bug Fixes (March 13, 2026)
- **FIXED:** Error at step 12 for emerging screenplay films - actors were sent as {id, role, fee} instead of {actor_id, role}
- **FIXED:** AI poster generation made more robust with try/catch on polling, functional state updates
- **FIXED:** FilmDetail crash (ReferenceError: BACKEND_URL is not defined)
- **FIXED:** Draft system for emerging screenplays
- **FIXED:** Various UI/UX issues (locked step overlay, mobile layout, navigation)

## Backlog
- P1: Re-enable Infrastructure Market
- P2: CineCoins Purchase System (Stripe)
- P2: Major Studio Activities
- P3: Robust Data Migration Script

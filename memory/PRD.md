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
10. Acting School (train actors from scratch with hidden talent system)

## Architecture
```
/app/
├── backend/
│   ├── server.py           # Main FastAPI server (14K+ lines)
│   ├── game_systems.py     # Game mechanics, infrastructure types
│   ├── cast_system.py      # Cast generation/management (13 actor skills)
│   ├── social_system.py    # Notifications, friendships (acting_school type added)
│   ├── routes/
│   │   ├── acting_school.py  # Acting School feature
│   │   ├── infrastructure.py # Infrastructure purchase/upgrade
│   │   ├── notifications.py  # Notification CRUD (supports broadcast user_id='all')
│   │   ├── auth.py
│   │   ├── social.py
│   │   └── minigames.py
│   └── ...
├── frontend/
│   └── src/
│       ├── App.js
│       ├── constants/index.js  # SKILL_TRANSLATIONS (all skills for actors/directors/screenwriters/composers)
│       ├── contexts/
│       └── pages/
│           ├── Dashboard.jsx
│           ├── FilmWizard.jsx
│           ├── CineBoard.jsx
│           ├── ActingSchool.jsx
│           ├── NotificationsPage.jsx  # Interactive popup for acting_school notifications
│           └── ...
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
- CineBoard performance optimization (lazy poster loading)
- Dedicated poster endpoint GET /api/films/{film_id}/poster
- Infrastructure purchase/upgrade system with level tracking
- **Acting School (Scuola di Recitazione)** — COMPLETE:
  - Infrastructure type cinema_school with training slots based on level
  - Daily recruit generation (6/day, age 16-60, 3-5 initial skills)
  - Hidden talent system (growth speed + final skill ceiling)
  - Training duration 10-20 days, completion with Keep/Release
  - Personal cast actors appear first in FilmWizard
  - Social notifications on completion
- **Interactive Notification Popup** — COMPLETE (March 14, 2026):
  - Clicking acting_school notification opens popup with actor skills
  - Released actors: "Ingaggia" button → navigate to film creation
  - Kept actors: info message "nel cast privato del produttore"
  - Broadcast notifications (user_id='all') visible to all players
  - All 13 skill translations displayed in Italian

## Known Issues / Pending
- **"Voci del Pubblico" section is empty** (P1)
- **"Major Studios" not working correctly** (P1)

## Planned Features (NOT YET IMPLEMENTED)
### P0: Gameplay expansion ideas (user-discussed, not yet committed):
1. Festival del Cinema & Premi (weekly competitions, voting)
2. Missioni Giornaliere/Settimanali (daily tasks with rewards)
3. Collaborazioni tra Giocatori (co-productions, actor trading, 1v1 challenges)
4. Carriera Attori Dinamica (skills improve/decline based on film outcomes)
5. Eventi Stagionali a Tempo Limitato (themed events)
6. Gestione Major Studio Attiva (guild objectives, rankings)

### P1: Fix Major Studios functionality
### P1: Fix Voci del Pubblico (empty section)
### P2: CineCoins Purchase System (Stripe)
### P2: Major Studio Activities (deeper gameplay)

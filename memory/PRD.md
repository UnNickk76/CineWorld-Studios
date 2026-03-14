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
│   ├── social_system.py    # Notifications, friendships (acting_school type)
│   ├── routes/
│   │   ├── acting_school.py  # Acting School endpoints
│   │   ├── infrastructure.py # Infrastructure purchase/upgrade (level field)
│   │   ├── notifications.py  # Supports broadcast user_id='all'
│   │   ├── auth.py / social.py / minigames.py
│   └── ...
├── frontend/src/
│   ├── App.js
│   ├── constants/index.js     # SKILL_TRANSLATIONS (all roles)
│   └── pages/
│       ├── InfrastructurePage.jsx  # School-specific UI in detail dialog
│       ├── ActingSchool.jsx        # Standalone school page
│       ├── NotificationsPage.jsx   # Interactive actor popup
│       └── ...
```

## What's Been Implemented (Complete)
- Complete film creation wizard with 12 steps
- Emerging Screenwriters, AI poster generation, cast rejection/negotiation
- Sequel/saga, draft save/resume, social features, minigames
- Multiple screenwriters (1-5), CineBoard performance optimization
- Infrastructure purchase/upgrade with level tracking
- **Acting School** — COMPLETE:
  - Infrastructure type cinema_school with slots based on level
  - Daily recruit generation (6/day, age 16-60, 3-5 initial skills)
  - Hidden talent system, training 10-20 days, Keep/Release
  - Personal cast actors appear first in FilmWizard
- **School UI in Infrastructure Detail** — COMPLETE (March 14, 2026):
  - Custom dialog for cinema_school showing recruits, trainees, kept actors
  - Training progress bars with all 13 skills translated
  - Upgrade section with cost and player level requirements
  - $200K train button, Keep/Release buttons for graduated actors
- **Interactive Notification Popup** — COMPLETE:
  - Clickable acting_school notifications with skill popup
  - Released actors: "Ingaggia" button → film creation
  - Broadcast notifications (user_id='all')

## Known Issues / Pending
- **"Voci del Pubblico" empty** (P1)
- **"Major Studios" not working** (P1)

## Planned Features
### P0 (discussed gameplay expansion):
1. Festival del Cinema & Premi
2. Missioni Giornaliere/Settimanali
3. Collaborazioni tra Giocatori
4. Carriera Attori Dinamica
5. Eventi Stagionali
6. Major Studio Attiva

### P1: Fix Major Studios / Voci del Pubblico
### P2: CineCoins Purchase (Stripe)

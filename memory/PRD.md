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
- CineBoard performance optimization (39MB → 37KB responses + lazy poster loading)
- Cast migration system (old skill system cleanup)
- Bottom nav: CineBoard (coppa icon) + Bozze icons
- Dedicated poster endpoint GET /api/films/{film_id}/poster with Cache-Control

## Bug Fixes (March 14, 2026)
- FIXED: Step 12 wizard error for emerging screenplays (actors format)
- FIXED: AI poster polling resilience
- FIXED: CineBoard N+1 query problem (bulk fetches)
- FIXED: Owner avatar_url base64 bloating responses (2.6MB per owner)
- FIXED: Cast IMDb ratings migration
- FIXED: Cast skills normalization (all 8 skills, range 1-100)
- FIXED: Bozze button in bottom nav navigating to wrong route (/film-drafts → /drafts)
- FIXED: CineBoard poster loading via dedicated endpoint (lazy loading)
- FIXED: CineBoard navbar icon changed to Trophy

## Known Issues / Pending
- 🔴 **Major crash** — clicking on majors shows "Something went wrong"
- 🔴 **Infrastructure feature disabled** — needs reactivation
- 🟡 **Voci del pubblico** — section shows nothing
- 🟡 **Production environment down** (external infrastructure issue)

## Planned Features (NOT YET IMPLEMENTED)

### P0: Scuola di Recitazione (Acting School) — DETAILED SPEC
A complete actor training system within the Infrastructure feature:

**Infrastructure Levels & Training Slots (exponential):**
- Level 1: 1 actor training slot
- Level 5: 2 actors simultaneously
- Scaling exponentially up to 20 max concurrent trainees

**Trainee Generation:**
- Age range: 16-60 years old
- Initial skills: very low (3-5 visible skills out of 8)
- Initial assessment: "promising" or "less promising" label
- Even "less promising" actors can become great (hidden talent)

**Hidden Talent System:**
- Every actor has a hidden talent score (unknown to player)
- Talent determines: growth speed, final skill ceiling, skill distribution
- A "less promising" actor can have max talent → exponential growth
- Training duration: 10-20 days based on talent (high talent = faster)

**Growth Mechanics:**
- Skills grow over 10-20 real days
- Growth curve based on hidden talent (linear for low talent, exponential for high)
- Final skills will be uniform with existing database actors (not all 100s)
- Skills use the existing 1-100 system with 8 skills per actor

**Completion Options:**
1. **Keep Engaged:** Monthly salary (lower than normal hiring costs), actor appears first in film wizard cast list (optional selection), usable in own films at no additional cost, engagement for variable duration
2. **Release:** Actor becomes available to all players for normal hiring

**Notifications:**
- When actor completes training, social notification:
  - If kept: "[Player] has trained a potential star [Actor Name] (clickable popup with all skills) — will use in their films"
  - If released: "[Player] has trained a potential star [Actor Name] (clickable popup with skills + Hire button)"
- Hire button in popup: choose 1+ films, fixed cost engagement

### P1: Fix Major Studios Crash
### P1: Reactivate Infrastructure Market  
### P2: CineCoins Purchase System (Stripe)
### P2: Fix Voci del Pubblico (empty section)
### P3: Robust Data Migration Script

# CineWorld Studio's - Product Requirements Document

## Original Problem Statement
Movie studio simulation game. React + FastAPI + MongoDB.

## Architecture
```
/app/backend/
├── server.py             # Main server (14K+ lines)
├── game_systems.py       # Game mechanics, infrastructure types
├── cast_system.py        # Cast generation (13 actor skills)
├── social_system.py      # Notifications (acting_school type)
├── routes/
│   ├── cinepass.py       # CinePass system, contests, login rewards
│   ├── acting_school.py  # Acting School feature
│   ├── infrastructure.py # Infrastructure CRUD (CinePass enforced)
│   ├── notifications.py  # Broadcast support (user_id='all')
│   ├── auth.py / social.py / minigames.py
/app/frontend/src/
├── App.js                # Routes, header w/ CinePass badge, login popup
├── components/
│   ├── LoginRewardPopup.jsx    # 7-day login reward popup
│   ├── CinePassConfirmDialog.jsx # Reusable CinePass confirmation
├── pages/
│   ├── ContestsPage.jsx        # Daily contests (replaces MiniGames)
│   ├── InfrastructurePage.jsx  # School UI + CinePass costs
│   ├── FilmWizard.jsx          # CinePass confirm on create
│   ├── ActingSchool.jsx / Dashboard.jsx / CineBoard.jsx / ...
```

## What's Been Implemented
- Film creation wizard, AI screenplay/poster (GPT-4o, GPT-Image-1)
- Cast management, rejection/negotiation, pre-engagement
- Multiple screenwriters (1-5), sequel/saga, drafts
- CineBoard with lazy poster loading
- Infrastructure purchase/upgrade with levels
- Acting School (recruits, training, keep/release, personal cast)
- Interactive notification popup for acting school actors
- **CinePass System** — COMPLETE (March 14, 2026):
  - Secondary currency, 100 default per user
  - Costs: create film (20), infrastructure (8-20), pre-engage (5), screenplay (10), school recruit (3)
  - Daily login rewards: 3→5→7→10→14→19→35 CinePass (7-day streak)
  - 15-day consecutive bonus (+15)
  - Auto popup on first daily login
  - Daily contests (3/day, random from 4 types, max 50/day)
  - Contest types: Budget Guess, Cast Match, Box Office Prediction, Speed Producer
  - Replaced minigames completely
  - CinePass badge in header
  - Italian timezone noon reset (12:00)

## Known Issues
- "Voci del Pubblico" empty (P1)
- "Major Studios" not working (P1)

## Planned Features
### P0: Gameplay expansion (discussed):
1. Festival del Cinema & Premi
2. Missioni Giornaliere/Settimanali
3. Collaborazioni tra Giocatori
4. Carriera Attori Dinamica
5. Eventi Stagionali
6. Major Studio Attiva

### P1: Fix Major Studios / Voci del Pubblico
### P2: CineCoins Purchase (Stripe) — CinePass buyable with real money

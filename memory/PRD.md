# CineWorld Studio's - Product Requirements Document

## Overview
CineWorld Studio's is a multiplayer online film production simulation game with strong social features, level progression, and infrastructure management.

## Original Problem Statement
Create a multiplayer online film production game with user profiles, film creation wizard, mini-games, social interactions, level progression system, infrastructure ownership, and AI-powered content generation.

## What's Been Implemented

### Authentication & Profile
- [x] JWT-based authentication (register/login)
- [x] Age verification (18+ required)
- [x] Gender selection (male/female)
- [x] 20 Modern Avatars (DiceBear v9)
- [x] AI Avatar Generation (GPT Image 1)
- [x] Custom Avatar URL Input
- [x] Multi-language support (IT, EN, ES, FR, DE)
- [x] Auto-login via localStorage
- [x] Player reset function

### Level & XP System (NEW - March 2026)
- [x] **Infinite level system** starting from Level 0
- [x] **Exponential XP growth**: 100 XP for Lv1, +50% each level
- [x] **XP Sources**:
  - Mini-games: 5 XP per play, +15 XP for winning (80%+ correct)
  - Film release: 50 XP base, +200 for hit (80%+), +500 for blockbuster (90%+)
  - Likes given/received: 2-3 XP
  - Infrastructure purchase: 100 XP
  - Daily login: 25 XP
- [x] **Level visible in navbar** with progress bar
- [x] **Level badge** next to player name

### Fame System (NEW)
- [x] **Fame score 0-100** starting at 50
- [x] **Fame tiers**: Unknown, Emerging, Notable, Famous, Star, Legend
- [x] **Fame changes based on film performance**:
  - Quality 90+: +15-25 fame
  - Quality 80-89: +8-13 fame
  - Quality 70-79: +3-6 fame
  - Quality 30-49: -5 to -8 fame
  - Quality <30: -10 to -15 fame
- [x] **Fame affects infrastructure revenue** (multiplier 0.8x to 1.5x)

### Mini-Games System (UPDATED)
- [x] **5 Games**: Film Trivia, Guess the Genre, Director Match, Box Office Bet, Release Year
- [x] **NEW: 4 plays per game every 4 hours** (cooldown system)
- [x] **Translated in 5 languages**
- [x] **XP rewards** for playing and winning

### Infrastructure System (NEW)
- [x] **11 Infrastructure Types**:
  1. Cinema (Lv.5, Fame 20) - $2M - 4 screens
  2. Drive-In Theater (Lv.8, Fame 25) - $1.5M - 2 screens
  3. Small Shopping Mall Cinema (Lv.10, Fame 30) - $5M - 6 screens, 3D
  4. Production Studio (Lv.15, Fame 40) - $8M - 15% production discount
  5. Medium Shopping Mall Multiplex (Lv.20, Fame 50) - $15M - 10 screens
  6. Cinema School (Lv.25, Fame 55) - $12M - Train actors
  7. Cinema Museum (Lv.30, Fame 60) - $20M - Fame bonus
  8. Large Shopping Mall IMAX (Lv.35, Fame 65) - $35M - 16 screens, IMAX
  9. VIP Luxury Cinema (Lv.40, Fame 70) - $25M - 3x ticket prices
  10. Film Festival Venue (Lv.45, Fame 75) - $40M - Host festivals
  11. Theme Park (Lv.50, Fame 80) - $100M - Full attraction park

- [x] **World Cities** in 10 countries with different wealth/cost multipliers
- [x] **First cinema must be in player's language country**
- [x] **Cinema Management**:
  - Set ticket prices (adult, child, 3D, IMAX)
  - Set food/drink prices
  - Show own films or buy from other players
  - Daily revenue based on fame, film quality, city wealth

### Cinema School (NEW)
- [x] **Enroll students** with random characteristics
- [x] **Train students daily** to improve skills
- [x] **Give attention** to prevent students from leaving
- [x] **Graduate students** (min 30 days) to become personal actors
- [x] **Personal actors** can be used in your films at reduced cost

### Leaderboard System (NEW)
- [x] **Global leaderboard** ranking all players
- [x] **Local leaderboard** by country (where player has infrastructure)
- [x] **Composite score**: Level (30%) + Fame (40%) + Revenue (30%)
- [x] **Top player is NOT necessarily highest level**
- [x] **Medals** for top 3 (gold/silver/bronze)

### Player Public Profiles (NEW)
- [x] **View other players' stats**
- [x] **See level, fame, films count, infrastructure count**
- [x] **Send direct messages** from profile

### Film Production
- [x] 10-step wizard for film creation
- [x] 16 genres with 6 sub-genres each
- [x] **IMDb-style rating** (1-10) for each film
- [x] **AI-generated user interactions** (less weight on sales)
- [x] **Fame changes** based on film success/failure
- [x] **XP rewards** for film releases
- [x] Sponsor selection, equipment, locations
- [x] Cast with roles and fame categories
- [x] Gender visible next to all cast names
- [x] AI screenplay and poster generation

### Social Features
- [x] Social feed with film likes
- [x] Chat with public/private rooms
- [x] Bot moderators
- [x] Cinema Journal with rankings and voting

## Technical Architecture

```
/app/
├── backend/
│   ├── server.py           # Main FastAPI app (~3500 lines)
│   ├── game_systems.py     # Level, Fame, Infrastructure logic (NEW)
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── App.js          # Main React app (~2500 lines)
│   │   └── components/ui/  # Shadcn components
│   └── .env
└── memory/
    └── PRD.md
```

## API Endpoints Summary

### Level/Fame/Infrastructure (NEW)
- `GET /api/player/level-info` - Get level, XP, fame, progress
- `GET /api/player/fame` - Get fame tier and benefits
- `GET /api/infrastructure/types` - All 11 infrastructure types
- `GET /api/infrastructure/cities` - World cities with costs
- `GET /api/infrastructure/my` - Player's owned infrastructure
- `POST /api/infrastructure/purchase` - Buy new infrastructure
- `GET /api/infrastructure/{id}` - Infrastructure details
- `PUT /api/infrastructure/{id}/prices` - Update prices
- `POST /api/infrastructure/{id}/add-film` - Add film to cinema
- `POST /api/infrastructure/{id}/buy-film` - Buy other player's film
- `GET /api/minigames/cooldowns` - Cooldown status for all games

### Cinema School (NEW)
- `GET /api/cinema-school/{id}/students` - List students
- `POST /api/cinema-school/{id}/enroll` - Enroll new student
- `POST /api/cinema-school/{id}/train` - Train all students
- `POST /api/cinema-school/{id}/give-attention/{student_id}` - Prevent leaving
- `POST /api/cinema-school/{id}/graduate/{student_id}` - Graduate to actor
- `GET /api/actors/personal` - Your trained actors

### Leaderboard (NEW)
- `GET /api/leaderboard/global` - Global rankings
- `GET /api/leaderboard/local/{country}` - Country rankings
- `GET /api/players/{id}/profile` - Public player profile

## Test Results (March 9, 2026)
- Backend: 100% (12/12 tests passed)
- Frontend: 100% (all features verified)
- Level/XP system: PASS
- Infrastructure system: PASS
- Leaderboard system: PASS
- Cinema School: PASS

## P1 Features (Next Phase)
- [ ] Star Discovery System with news announcements
- [ ] Skill evolution over time for cast
- [ ] Negative rating penalty system
- [ ] Image sharing in chat
- [ ] Automatic chat translation

## P2 Features (Backlog)
- [ ] Voice messages in chat
- [ ] Detailed box office by state/city
- [ ] PvP challenges
- [ ] Film trailers
- [ ] Award ceremonies
- [ ] Seasonal events

## 3rd Party Integrations
- OpenAI GPT-5.2 (Text) via Emergent LLM Key
- GPT Image 1 (Images) via Emergent LLM Key
- Google Translate API (Planned)

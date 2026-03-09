# CineWorld Studio's - Product Requirements Document

## Overview
CineWorld Studio's is a multiplayer online film production simulation game with level progression, infrastructure ownership, hourly revenue system, world events, and cinema touring.

## What's Been Implemented (March 2026)

### Authentication & Profile
- [x] JWT-based authentication
- [x] Age/gender verification (18+)
- [x] **AI-Generated Avatars** (default at registration)
- [x] **Custom URL Avatars** (paste any image URL)
- [x] **No preset avatars** - only AI or custom
- [x] Multi-language support (IT, EN, ES, FR, DE)

### Level & XP System
- [x] Infinite level system from Level 0
- [x] Exponential XP growth (+50% per level)
- [x] XP from: mini-games, films, likes, infrastructure, tours
- [x] Level visible in navbar with progress bar

### Fame System (0-100)
- [x] 6 tiers: Unknown → Legend
- [x] Fame changes based on film performance
- [x] Fame affects infrastructure revenue

### World Events System (NEW)
- [x] **8 World Events** with seasonal bonuses:
  1. **Cannes Film Festival** (May) - Drama +50%, Art +100%, France cinema +100%
  2. **Oscar Season** (Feb) - All genres +20%, USA cinema +80%, Fame +50%
  3. **Venice Film Festival** (Sep) - Drama +40%, Documentary +60%, Italy cinema +100%
  4. **Berlin Festival** (Feb) - Indie +50%, Germany cinema +80%
  5. **Summer Blockbuster** (Jun-Aug) - Action +60%, Animation +70%, Revenue +30%
  6. **Holiday Season** (Dec-Jan) - Family +80%, Comedy +40%, Revenue +50%
  7. **Halloween Horror** (Oct) - Horror +150%, Night screenings +40%
  8. **Valentine's Day** (Feb) - Romance +100%, Couples attendance +60%
- [x] Events affect revenue multipliers for genres and countries
- [x] Active events shown in Tour page banner

### Cinema Tour System (NEW)
- [x] **Visit other players' cinemas** for XP
- [x] **Leave reviews** (1-5 stars + comment)
- [x] **Tour Rating Score** (0-100) based on:
  - Infrastructure type, custom logo, films showing
  - Visitor count, city prestige, reviews
- [x] **Tier system**: Legendary, Excellent, Great, Good, Average, Needs Improvement
- [x] **Featured cinemas list** sorted by rating
- [x] **My visits today** tracking
- [x] XP rewards: +5 for visiting, +10 for reviewing
- [x] Fame bonus for cinema owners with good reviews

### Hourly Revenue System
- [x] Revenue calculated hourly (not daily)
- [x] 15+ factors including quality, cast, genre, time, weather, events
- [x] World event bonuses applied automatically

### Film Duration System
- [x] Dynamic film duration based on performance
- [x] Extension for successful films (+fame, +revenue)
- [x] Early withdrawal for failing films (-fame, -revenue penalty)

### Star Discovery & Skill Evolution
- [x] Unknown actors can become stars
- [x] Cast skills evolve based on film quality
- [x] Breakthrough and decline chances

### Infrastructure System
- [x] 11 types from Cinema (Lv5) to Theme Park (Lv50)
- [x] World cities with wealth/cost multipliers
- [x] Cinema School for training personal actors

### Mini-Games
- [x] 5 games with 4 plays per type every 4 hours
- [x] XP and monetary rewards

### Social Features
- [x] Chat with public/private rooms
- [x] Bot moderators
- [x] Cinema Journal with star ratings
- [x] Leaderboard (global/local)

## API Endpoints

### World Events (NEW)
- `GET /api/events/active` - Currently active events
- `GET /api/events/all` - All possible events
- `GET /api/films/{id}/event-bonus` - Event bonuses for a film

### Cinema Tour (NEW)
- `GET /api/tour/featured` - Featured cinemas
- `GET /api/tour/cinema/{id}` - Cinema details
- `POST /api/tour/cinema/{id}/visit` - Record visit (+5 XP)
- `POST /api/tour/cinema/{id}/review` - Leave review (+10 XP)
- `GET /api/tour/my-visits` - User's tour history

### Avatars (UPDATED)
- `GET /api/avatars` - Returns AI/URL options only (no presets)
- `POST /api/avatar/generate` - Generate AI avatar
- `PUT /api/auth/avatar` - Update avatar URL

## Test Results (March 9, 2026)
- Backend: 100% (12 tests passed)
- Frontend: 100% (all features verified)
- World Events: 8 events defined, date-based activation
- Cinema Tour: Full functionality ready
- Avatars: Presets removed, AI/URL only

## P1 Features (Next)
- [ ] Image sharing in chat
- [ ] Automatic chat translation
- [ ] Film trailers

## P2 Features (Backlog)
- [ ] Voice messages
- [ ] Award ceremonies
- [ ] PvP challenges

## Tech Stack
- **Backend**: FastAPI, Python, MongoDB, WebSockets
- **Frontend**: React, TailwindCSS, Shadcn/UI
- **AI**: GPT-5.2 (text), GPT Image 1 (avatars)

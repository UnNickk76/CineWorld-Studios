# CineWorld Studio's - Product Requirements Document

## Overview
CineWorld Studio's is a multiplayer online film production simulation game with level progression, infrastructure ownership, hourly revenue system, and social features.

## What's Been Implemented (March 2026)

### Authentication & Profile
- [x] JWT-based authentication
- [x] Age/gender verification
- [x] 20 Modern Avatars + AI Generation + Custom URL
- [x] Multi-language support (IT, EN, ES, FR, DE)

### Level & XP System
- [x] Infinite level system from Level 0
- [x] Exponential XP growth (+50% per level)
- [x] XP from: mini-games, films, likes, infrastructure
- [x] Level visible in navbar with progress bar

### Fame System (0-100)
- [x] 6 tiers: Unknown → Legend
- [x] Fame changes based on film performance
- [x] Fame affects infrastructure revenue (0.8x to 1.5x)

### Hourly Revenue System (NEW)
- [x] **Revenue calculated HOURLY** (not daily)
- [x] **15+ Factors affecting revenue:**
  - Quality score, IMDb rating
  - Cast fame average, Director skill
  - Genre popularity (seasonal bonuses)
  - Time of day (peak: 19:00-21:00)
  - Day of week (weekend bonus)
  - Days in theater decay curve
  - Competition from other films
  - Unpredictability (±25%)
  - Weather factor
  - Special events (2% chance: Premiere, Festival, Celebrity Visit)
- [x] "Incassa Ora" button to collect hourly revenue

### Film Duration System (NEW)
- [x] **Dynamic film duration** based on performance score
- [x] **Extension** (up to 14 days) for successful films:
  - Quality 80+, IMDb 7+, high satisfaction
  - Earns extra fame (+0.5 per day)
  - Earns extra revenue bonus
- [x] **Early withdrawal** for failing films:
  - Quality <40, IMDb <4, poor satisfaction
  - Fame penalty (-0.3 per day early)
  - Revenue penalty ($20k per day)
- [x] Performance reasons displayed in UI

### Star Discovery System (NEW)
- [x] Unknown actors can become "Rising Stars"
- [x] Chance based on film quality (75+) and actor skills
- [x] Announcement broadcast in chat
- [x] Fame bonus to discovering player (+5)

### Skill Evolution System (NEW)
- [x] Cast skills evolve based on film quality
- [x] Role importance affects changes (protagonist > cameo)
- [x] Breakthrough chance (+0.5-1.0 skill)
- [x] Decline chance (injury/burnout: -0.3-0.7)

### Negative Rating Penalty (NEW)
- [x] Track ratio of negative ratings (<2.5 stars)
- [x] If >60% negative: -5% quality penalty on own films
- [x] If >80% negative: -10% quality penalty
- [x] Encourages fair rating behavior

### Infrastructure System
- [x] 11 types from Cinema (Lv5) to Theme Park (Lv50)
- [x] World cities with wealth/cost multipliers
- [x] Cinema management (tickets, food prices)
- [x] Cinema School for training personal actors

### Mini-Games
- [x] 5 games with 4 plays per type every 4 hours
- [x] XP rewards for playing and winning
- [x] Translated in 5 languages

### Social Features
- [x] Chat with public/private rooms
- [x] Bot moderators
- [x] Cinema Journal with star ratings
- [x] Leaderboard (global/local)
- [x] Player public profiles

## API Endpoints

### Hourly Revenue (NEW)
- `GET /api/films/{id}/hourly-revenue` - Get current hourly estimate
- `POST /api/films/{id}/process-hourly-revenue` - Collect hourly revenue
- `POST /api/films/process-all-hourly` - Process all films at once

### Film Duration (NEW)
- `GET /api/films/{id}/duration-status` - Get extension/withdrawal status
- `POST /api/films/{id}/extend` - Extend successful film
- `POST /api/films/{id}/early-withdraw` - Withdraw failing film

### Cast Evolution (NEW)
- `POST /api/films/{id}/check-star-discoveries` - Find new stars
- `POST /api/films/{id}/evolve-cast-skills` - Evolve skills

### Rating Penalty (NEW)
- `GET /api/player/rating-stats` - Check penalty status

## Test Results (March 9, 2026)
- Backend: 100% (16 tests passed)
- Frontend: 100% (all features verified)
- Critical bug fixed: datetime parsing

## P1 Features (Next)
- [ ] Image sharing in chat
- [ ] Automatic chat translation
- [ ] Tour of other players' cinemas

## P2 Features (Backlog)
- [ ] Voice messages
- [ ] Film trailers
- [ ] Award ceremonies
- [ ] PvP challenges

## Tech Stack
- **Backend**: FastAPI, Python, MongoDB, WebSockets
- **Frontend**: React, TailwindCSS, Shadcn/UI
- **AI**: GPT-5.2 (text), GPT Image 1 (images)

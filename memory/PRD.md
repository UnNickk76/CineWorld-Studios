# CineWorld Studio's - Product Requirements Document

## Overview
CineWorld Studio's is a multiplayer online film production simulation game with strong social features.

## Original Problem Statement
Create a multiplayer online film production game with user profiles, film creation wizard, mini-games, social interactions, and AI-powered content generation.

## What's Been Implemented (March 2026)

### Authentication & Profile
- [x] JWT-based authentication (register/login)
- [x] Age verification (18+ required) with adult content warning
- [x] Gender selection
- [x] **20 Modern Avatars** (DiceBear v9: Notionists, Lorelei, Personas, Thumbs, Bottts-neutral, Glass)
- [x] Multi-language support (IT, EN, ES, FR, DE)
- [x] Auto-login via localStorage
- [x] Player reset function

### Film Production (10-Step Wizard)
- [x] Title, genre, release date, weeks in theater
- [x] **16 Genres**: Action, Comedy, Drama, Horror, Sci-Fi, Romance, Thriller, Animation, Documentary, Fantasy, Musical, Western, War, Noir, Adventure, Biographical
- [x] **Sub-genres system**: 6 sub-genres per genre, max 3 selectable
- [x] Sponsor selection with budget offers
- [x] Equipment packages (Basic to Hollywood Elite)
- [x] Multiple filming locations
- [x] Screenwriter/Director selection with skills
- [x] **Actor Role System**: Protagonist, Co-protagonist, Antagonist, Supporting, Cameo
- [x] Extras management
- [x] AI screenplay generation (GPT-5.2)
- [x] AI poster generation (GPT Image 1)
- [x] In-film advertising options
- [x] Film withdrawal from theaters

### Mini Games (FULLY PLAYABLE & TRANSLATED)
- [x] **5 Games**: Film Trivia, Guess the Genre, Director Match, Box Office Bet, Release Year
- [x] **Translated in 5 languages**: IT, EN, ES, FR, DE
- [x] Real questions with scoring
- [x] Cooldown system between plays
- [x] Variable rewards ($5k-$100k)

### Social Features
- [x] Social feed with film likes
- [x] Public chat rooms (General, Producers Lounge, Box Office Talk)
- [x] **Private messaging (DM)**
- [x] **Online users tracking** with heartbeat
- [x] Public/Private chat tabs

### Cast System
- [x] International names (10 nationalities)
- [x] Skills system (1-10) with change indicators
- [x] Unique names per nationality

### Box Office
- [x] Opening day immediate revenue
- [x] Daily revenue based on audience satisfaction
- [x] Variable theater duration

## Recent Updates (March 8-9, 2026)
1. **Avatar System Overhaul**: Replaced old avatars with 20 modern DiceBear v9 styles
2. **Mini-game Translations**: All questions translated in IT, EN, ES, FR, DE
3. **Genre Expansion**: Added 6 new genres (Musical, Western, War, Noir, Adventure, Biographical)
4. **Sub-genre System**: Each genre now has 6 sub-genres, players can select up to 3
5. **Actor Roles**: New system to assign roles (Protagonist, Co-protagonist, Antagonist, Supporting, Cameo)
6. **Chat Moderator Bots**: 3 bots (CineMaster MOD, FilmGuide MOD, CineNews BOT) with auto-responses
7. **Same-Day Film Release**: Films can now be released on the same day of creation
8. **Auto Film Announcements**: CineNews bot announces new film releases in General chat (translated)

## API Endpoints
- POST /api/auth/register, login, /me, /profile, /reset
- GET /api/avatars - Returns 20 modern avatars
- GET /api/genres - Returns 16 genres with sub-genres
- GET /api/actor-roles - Returns 5 actor roles with translations
- GET /api/actors, /directors, /screenwriters, /sponsors, /locations, /equipment
- POST /api/films, GET /api/films/my, /films/{id}, DELETE /api/films/{id}
- GET /api/films/social/feed, POST /api/films/{id}/like
- GET /api/minigames, POST /api/minigames/{id}/start (returns translated questions)
- GET /api/challenges, /statistics/global, /statistics/my
- POST /api/users/heartbeat, GET /api/users/online, /users/all
- GET /api/chat/rooms, POST /api/chat/direct/{user_id}, /chat/messages

## Test Results (March 8, 2026)
- Backend: 100% (18/18 tests passed)
- Frontend: 100% (all UI features working)
- All 6 new features verified working

## P1 Features (Next Phase)
- [ ] Image sharing in chat with moderation
- [ ] Voice messages
- [ ] Automatic chat translation
- [ ] PvP challenges

## P2 Features (Backlog)
- [ ] Custom avatar upload
- [ ] Film trailers
- [ ] Award ceremonies
- [ ] Seasonal events
- [ ] Skill evolution over time

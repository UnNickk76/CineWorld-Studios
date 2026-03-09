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
- [x] **20 Modern Avatars** (DiceBear v9: Avataaars with gender-appropriate styles)
- [x] **AI Avatar Generation** (GPT Image 1 via emergentintegrations)
- [x] **Custom Avatar URL Input** (users can paste any image URL)
- [x] Multi-language support (IT, EN, ES, FR, DE)
- [x] Auto-login via localStorage
- [x] Player reset function

### Film Production (10-Step Wizard)
- [x] Title, genre, release date, weeks in theater
- [x] **16 Genres**: Action, Comedy, Drama, Horror, Sci-Fi, Romance, Thriller, Animation, Documentary, Fantasy, Musical, Western, War, Noir, Adventure, Biographical
- [x] **Sub-genres system**: 6 sub-genres per genre, max 3 selectable
- [x] Sponsor selection with budget offers
- [x] Equipment packages (Basic to Hollywood Elite) - **Costs +20%**
- [x] Multiple filming locations - **Costs +20%**
- [x] Screenwriter/Director selection with skills and **gender icons (♂/♀)**
- [x] **Actor Role System**: Protagonist, Co-protagonist, Antagonist, Supporting, Cameo
- [x] **Gender visible next to all cast names**
- [x] Extras management
- [x] AI screenplay generation (GPT-5.2)
- [x] AI poster generation (GPT Image 1)
- [x] In-film advertising options
- [x] Film withdrawal from theaters

### Cast System
- [x] International names (10 nationalities)
- [x] Skills system (1-10) with change indicators
- [x] **Gender field (male/female)** for all cast members
- [x] **Gender-appropriate avatars** (long hair/accessories for female, short hair/beard for male)
- [x] **Fame Categories**: Unknown, Rising Star, Famous, Superstar with appropriate costs
- [x] **All cast costs increased by 20%**

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
- [x] **Chat Moderator Bots**: CineMaster, FilmGuide, CineNews

### Cinema Journal
- [x] Newspaper-style page with films ranked by quality
- [x] Star ratings (0-5 with half stars)
- [x] Comments section
- [x] **Main cast display with gender icons**
- [x] Film descriptions and genres

### Box Office
- [x] Opening day immediate revenue
- [x] Daily revenue based on audience satisfaction
- [x] Variable theater duration
- [x] Same-day film release allowed

## Recent Updates (March 9, 2026)
1. **Gender Icons**: Added ♂/♀ icons next to all cast names in FilmWizard, CinemaJournal, and FilmDetail
2. **Cost Increase**: All equipment, location, and cast costs increased by 20%
3. **AI Avatar Generation**: Users can generate custom avatars using GPT Image 1
4. **Custom Avatar URL**: Users can paste any image URL as their avatar
5. **Profile Avatar Replacement**: Full UI for changing avatars (preset, AI, or custom URL)
6. **FilmDetail Cast Section**: New section showing director, screenwriter, and full cast with gender icons and roles

## API Endpoints
- POST /api/auth/register, login, /me, /profile, /reset
- PUT /api/auth/avatar - Update user avatar
- POST /api/avatar/generate - Generate AI avatar
- GET /api/avatars - Returns 20 modern avatars
- GET /api/genres - Returns 16 genres with sub-genres
- GET /api/actor-roles - Returns 5 actor roles with translations
- GET /api/actors, /directors, /screenwriters - Returns cast with gender field
- GET /api/sponsors, /locations, /equipment - All costs +20%
- POST /api/films, GET /api/films/my, /films/{id}, DELETE /api/films/{id}
- GET /api/films/cinema-journal - Films with main_cast including gender
- GET /api/films/social/feed, POST /api/films/{id}/like
- POST /api/films/{id}/rate, /comment
- GET /api/minigames, POST /api/minigames/{id}/start
- GET /api/challenges, /statistics/global, /statistics/my
- POST /api/users/heartbeat, GET /api/users/online, /users/all
- GET /api/chat/rooms, POST /api/chat/direct/{user_id}, /chat/messages

## Test Results (March 9, 2026)
- Backend: 100% (10/10 tests passed)
- Frontend: All UI features verified working
- Gender icons visible in FilmWizard, CinemaJournal, FilmDetail
- Avatar selection and custom URL working
- Costs properly increased by 20%

## P1 Features (Next Phase)
- [ ] Star Discovery System: Announce when unknown actor becomes superstar
- [ ] Skill Evolution: Cast skills improve/worsen over time with notifications
- [ ] Negative Rating Penalty: Too many negative ratings affect rater's films
- [ ] Image sharing in chat with moderation
- [ ] Automatic chat translation

## P2 Features (Backlog)
- [ ] Voice messages in chat
- [ ] Detailed box office statistics by country/city
- [ ] PvP challenges
- [ ] Player reputation scores impact gameplay
- [ ] Film trailers
- [ ] Award ceremonies
- [ ] Seasonal events

## Technical Stack
- **Backend**: FastAPI, Python, MongoDB (motor), WebSockets, JWT
- **Frontend**: React, JavaScript, TailwindCSS, Shadcn/UI, axios
- **AI**: OpenAI GPT-5.2 (text), GPT Image 1 (images) via emergentintegrations
- **Architecture**: SPA with RESTful backend and WebSocket for real-time chat

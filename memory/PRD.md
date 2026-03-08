# CineWorld Studio's - Product Requirements Document

## Overview
CineWorld Studio's is a multiplayer online film production simulation game with strong social community features.

## Original Problem Statement
Create a multiplayer online film production game with:
- User profiles (nickname, production house, owner name, age, gender)
- Multi-language support (IT, EN, ES, FR, DE)
- Real-time daily box office tracking
- Film creation wizard with multiple steps
- Social interactions (likes, chat, mini games)
- AI-powered screenplay and poster generation

## User Personas
1. **Casual Gamer**: Wants a quick, engaging film creation experience
2. **Tycoon Enthusiast**: Enjoys managing budgets, sponsors, and maximizing revenue
3. **Social Player**: Interacts with others, explores films, plays mini games

## Core Requirements (Static)
### Authentication (18+ Community)
- [x] Email/Password registration with JWT
- [x] Age verification (18+ required)
- [x] Gender selection
- [x] Adult content warning
- [x] Terms acceptance checkbox
- [x] Auto-login via localStorage

### Film Production
- [x] 10-step film creation wizard
- [x] Title gives initial audience interest points
- [x] Sponsor selection with budget offers
- [x] Equipment packages (Basic to Hollywood Elite)
- [x] Multiple filming locations
- [x] Screenwriter, Director, Actor selection with skills (1-10 rating)
- [x] International names for all cast/crew (10+ nationalities)
- [x] Skill changes visible (green up, red down)
- [x] Extras management
- [x] AI screenplay generation (OpenAI GPT-5.2)
- [x] AI poster generation (GPT Image 1)
- [x] In-film advertising options
- [x] Film withdrawal from theaters

### Box Office System
- [x] Opening day immediate revenue
- [x] Daily revenue based on audience satisfaction
- [x] Actual theater duration varies with satisfaction
- [x] Sponsor revenue share calculation

### Social Features
- [x] Social feed with likes
- [x] Likes affect quality scores and player scores
- [x] Public chat rooms (General, Producers Lounge, Box Office Talk)
- [x] Private messaging / Direct Messages
- [x] Online users tracking with heartbeat
- [x] Public/Private chat tabs

### Mini Games (FULLY PLAYABLE)
- [x] Film Trivia ($5k-$50k) - Real movie questions
- [x] Guess the Genre ($3k-$30k) - Genre matching
- [x] Director Match ($4k-$40k) - Director identification
- [x] Box Office Bet ($10k-$100k) - Revenue comparisons
- [x] Release Year ($6k-$60k) - Year guessing
- [x] Cooldown system between plays
- [x] Scoring based on correct answers

### Challenges
- [x] Daily Challenges (Social Butterfly, Chatterbox, Gamer, Explorer)
- [x] Weekly Challenges (Producer, Mogul, Fan Favorite, Champion)
- [x] Progress tracking and rewards

### Player Scores
- [x] Likeability Score (affected by likes received)
- [x] Interaction Score (affected by messages, likes given)
- [x] Character Score (affected by community behavior)

### Profile & Avatars
- [x] 20 preset avatars (male, female, fantasy)
- [x] Player reset function
- [x] Language selection

## What's Been Implemented (March 2026)
- [x] Complete authentication flow with age/gender
- [x] Adult content warning
- [x] Dashboard with stats, player scores, challenges
- [x] 10-step film creation wizard
- [x] International names for cast/crew (10 nationalities: USA, Italy, Spain, France, Germany, Japan, China, UK, Brazil, India)
- [x] Skills system (1-10) with change indicators
- [x] My Films page with withdraw option
- [x] Film detail page with box office
- [x] Opening day revenue + daily tracking
- [x] Social feed with like functionality
- [x] Mini Games page (5 games) - FULLY PLAYABLE with real questions
- [x] Daily & Weekly challenges
- [x] Chat system with public rooms + private DMs
- [x] Online users tracking
- [x] Statistics page
- [x] Profile page with 20 avatars
- [x] Player reset function
- [x] Multi-language interface (IT, EN, ES, FR, DE)
- [x] Auto-login via localStorage
- [x] CSS media queries for mobile logo positioning

## P0 Features (Completed)
- [x] Chat avanzata con utenti online e DM
- [x] Mini-giochi realmente giocabili
- [x] Feed social con film altri giocatori
- [x] Nomi cast diversificati per nazionalità
- [x] Ritiro film dalle sale
- [x] Auto-login

## P1 Features (Next Phase)
- [ ] Voice message transcription
- [ ] Image sharing in chat with moderation
- [ ] PvP challenges system
- [ ] Automatic chat translation

## P2 Features
- [ ] Custom avatar upload with moderation
- [ ] Film trailers
- [ ] Award ceremonies
- [ ] Seasonal events
- [ ] Skill evolution over time (automatic)

## Technical Notes
- Backend: FastAPI on port 8001
- Frontend: React on port 3000
- Database: MongoDB with persistent people (actors/directors/screenwriters)
- AI: OpenAI GPT-5.2 + GPT Image 1 via Emergent LLM Key
- Routes order: Specific routes (/users/all, /users/search) before parameterized routes (/users/{id})

## API Endpoints
- POST /api/auth/register - User registration
- POST /api/auth/login - User login
- GET /api/auth/me - Get current user
- PUT /api/auth/profile - Update profile
- POST /api/auth/reset - Reset player progress
- GET /api/avatars - Get preset avatars
- GET /api/actors - Get actors list
- GET /api/directors - Get directors list
- GET /api/screenwriters - Get screenwriters list
- GET /api/sponsors - Get sponsors list
- GET /api/locations - Get filming locations
- GET /api/equipment - Get equipment packages
- POST /api/films - Create film
- GET /api/films/my - Get user's films
- GET /api/films/{id} - Get film details
- DELETE /api/films/{id} - Withdraw film from theaters
- GET /api/films/social/feed - Get social feed
- POST /api/films/{id}/like - Toggle like on film
- GET /api/minigames - Get available games
- POST /api/minigames/{id}/start - Start game session
- POST /api/minigames/submit - Submit answers
- GET /api/challenges - Get daily/weekly challenges
- GET /api/statistics/global - Get global stats
- GET /api/statistics/my - Get user stats
- POST /api/users/heartbeat - Update online status
- GET /api/users/online - Get online users
- GET /api/users/all - Get all users
- GET /api/users/{id} - Get user profile
- GET /api/chat/rooms - Get chat rooms
- POST /api/chat/direct/{user_id} - Start DM
- GET /api/chat/rooms/{id}/messages - Get messages
- POST /api/chat/messages - Send message
- POST /api/ai/screenplay - Generate screenplay
- POST /api/ai/poster - Generate poster

## Test Results (March 8, 2026)
- Backend: 100% (20/20 API tests passed)
- Frontend: 100% (all UI features working)
- All 6 requested features verified working

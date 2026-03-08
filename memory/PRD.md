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

### Film Production
- [x] 10-step film creation wizard
- [x] Title gives initial audience interest points
- [x] Sponsor selection with budget offers
- [x] Equipment packages (Basic to Hollywood Elite)
- [x] Multiple filming locations
- [x] Screenwriter, Director, Actor selection with skills (1-10 rating)
- [x] International names for all cast/crew
- [x] Skill changes visible (green up, red down)
- [x] Extras management
- [x] AI screenplay generation (OpenAI GPT-5.2)
- [x] AI poster generation (GPT Image 1)
- [x] In-film advertising options

### Box Office System
- [x] Opening day immediate revenue
- [x] Daily revenue based on audience satisfaction
- [x] Actual theater duration varies with satisfaction
- [x] Sponsor revenue share calculation

### Social Features
- [x] Social feed with likes
- [x] Likes affect quality scores and player scores
- [x] Public chat rooms (General, Producers Lounge, Box Office Talk)
- [x] Private messaging

### Mini Games
- [x] Film Trivia ($5k-$50k)
- [x] Guess the Poster ($3k-$30k)
- [x] Script Match ($4k-$40k)
- [x] Box Office Bet ($10k-$100k)
- [x] Casting Puzzle ($6k-$60k)
- [x] Cooldown system between plays

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

## What's Been Implemented (Jan 2026)
- [x] Complete authentication flow with age/gender
- [x] Adult content warning
- [x] Dashboard with stats, player scores, challenges
- [x] 10-step film creation wizard
- [x] International names for cast/crew
- [x] Skills system (1-10) with change indicators
- [x] My Films page
- [x] Film detail page with box office
- [x] Opening day revenue + daily tracking
- [x] Social feed with like functionality
- [x] Mini Games page (5 games)
- [x] Daily & Weekly challenges
- [x] Chat system with public rooms
- [x] Statistics page
- [x] Profile page with 20 avatars
- [x] Player reset function
- [x] Multi-language interface (IT, EN, ES, FR, DE)

## P0 Features (Next Phase)
- [ ] Real-time chat with WebSocket
- [ ] Voice message transcription
- [ ] Image sharing in chat with moderation
- [ ] PvP challenges system

## P1 Features
- [ ] Star creation system for actors
- [ ] Age demographics per film
- [ ] Advanced box office analytics
- [ ] Skill evolution over time (automatic)

## P2 Features
- [ ] Custom avatar upload with moderation
- [ ] Film trailers
- [ ] Award ceremonies
- [ ] Seasonal events

## Technical Notes
- Backend: FastAPI on port 8001
- Frontend: React on port 3000
- Database: MongoDB with persistent people (actors/directors/screenwriters)
- AI: OpenAI GPT-5.2 + GPT Image 1 via Emergent LLM Key

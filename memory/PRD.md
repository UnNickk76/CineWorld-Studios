# CineWorld Studio's - Product Requirements Document

## Overview
CineWorld Studio's is a multiplayer online film production simulation game where players manage their own production houses, create films, and compete on a global box office.

## Original Problem Statement
Create a multiplayer online film production game with:
- User profiles (nickname, production house, owner name)
- Multi-language support (IT, EN, ES, FR, DE)
- Real-time daily box office tracking
- Film creation wizard with multiple steps
- Social interactions (likes, chat)
- AI-powered screenplay and poster generation

## User Personas
1. **Casual Gamer**: Wants a quick, engaging film creation experience
2. **Tycoon Enthusiast**: Enjoys managing budgets, sponsors, and maximizing revenue
3. **Social Player**: Interacts with others, explores films, uses chat features

## Core Requirements
### Authentication
- [x] Email/Password registration with JWT
- [x] User profile: nickname, production house name, owner name
- [x] Language preference selection

### Film Production
- [x] 10-step film creation wizard
- [x] Title & Genre selection (step 1)
- [x] Sponsor selection with budget offers
- [x] Equipment packages (Basic to Hollywood Elite)
- [x] Multiple filming locations
- [x] Screenwriter, Director, Actor selection with skills
- [x] Extras management
- [x] AI screenplay generation (OpenAI GPT-5.2)
- [x] AI poster generation (GPT Image 1)
- [x] In-film advertising options

### Box Office System
- [x] Revenue tracking by country and city
- [x] Daily revenue simulation
- [x] Sponsor revenue share calculation
- [x] Quality score affects earnings

### Social Features
- [x] Social feed with films from all players
- [x] Like system affecting quality scores
- [x] Public chat rooms (General, Producers Lounge, Box Office Talk)
- [x] Private messaging

### Statistics
- [x] Personal stats (films, revenue, likes, avg quality)
- [x] Global stats (total films, users, box office)
- [x] Genre distribution

## Architecture

### Backend (FastAPI)
- MongoDB for data persistence
- JWT authentication
- RESTful API with /api prefix
- Socket.IO for real-time chat
- Integration with emergentintegrations library for AI

### Frontend (React)
- Shadcn/UI components
- Dark cinematic theme (Bebas Neue + Manrope fonts)
- Responsive design
- Framer Motion animations
- Real-time updates

## What's Been Implemented (Jan 2026)
- [x] Complete authentication flow
- [x] Dashboard with stats and quick actions
- [x] 10-step film creation wizard
- [x] My Films page with film listing
- [x] Film detail page with box office breakdown
- [x] Social feed with like functionality
- [x] Chat system with public rooms
- [x] Statistics page (personal and global)
- [x] Profile page with settings
- [x] Multi-language interface (IT, EN, ES, FR, DE)
- [x] AI screenplay generation endpoint
- [x] AI poster generation endpoint
- [x] Translation endpoint

## P0 Features (Next Phase)
- [ ] Daily revenue automation (scheduled task)
- [ ] WebSocket real-time chat updates
- [ ] Voice message transcription in chat
- [ ] Image sharing in chat

## P1 Features
- [ ] Actor/Director trust level system
- [ ] Star creation mechanism
- [ ] Age demographics per film
- [ ] Advanced box office analytics

## P2 Features
- [ ] Custom avatar upload with moderation
- [ ] Film trailers
- [ ] Award ceremonies
- [ ] Seasonal events

## Technical Notes
- Backend: FastAPI on port 8001
- Frontend: React on port 3000
- Database: MongoDB
- AI: OpenAI GPT-5.2 + GPT Image 1 via Emergent LLM Key

# CineWorld Studio's - PRD

## Original Problem Statement
A cinematic empire game where users produce films, manage TV stations, compete in challenges, and build a Hollywood-style business empire.

## Core Requirements
- Film production pipeline (films, sequels, TV series, anime)
- Netflix-style TV station management
- Revenue/economy system with realistic box office simulation
- Social features (friends, chat, challenges)
- Leaderboards and festivals
- Persistent poster storage (MongoDB)
- **Casting Agency** with personal actors, genre specializations, XP/fame bonuses
- **Rich Actor Data** across all 8,245 people (actors, directors, screenwriters, composers)
- **Guest Star Vocali** system for Anime and Animation films
- **Agency <-> School** bidirectional transfer system

## Architecture
- **Frontend**: React (CRA) with Tailwind + Shadcn UI
- **Backend**: FastAPI + MongoDB (Motor async driver)
- **Scheduler**: APScheduler for background tasks
- **AI**: OpenAI GPT-4o-mini (text) + GPT-Image-1 (posters) via Emergent LLM Key

## Completed Features

### Core Game
- Full film production pipeline with sequel support
- TV series and anime production
- TV station management, Cinema Journal, CineBoard, Hall of Fame, Festivals
- Infrastructure (cinemas, studios, etc.), Acting school
- Friend system, chat, challenges, leaderboards, revenue collection

### Casting System
- Casting Agency (recruit, manage, fire actors)
- Rich actor data for ALL 8,245 people
- Genre badges (2 strong + 1 adaptable) on ALL actors in ALL pipelines
- Gender icons, skill toggle buttons with color-coded skill bars
- Agency actors in all market casting views ("I tuoi Attori" section)
- Hired actors enriched with people data (genres, skills) from DB

### Guest Star Vocali (March 19, 2026)
- Anime: Guest Star casting - only famous/superstar, optional, 2x cost, quality+fame bonus
- Film Animation: same guest star system
- Can advance to screenplay without cast for anime

### Agency <-> School Transfer (March 19, 2026)
- Agenzia -> Scuola: send actor to school (cost $50K-$400K)
- Scuola -> Agenzia: transfer student to agency
- New "Scuola" tab in Casting Agency page

### Bug Fixes
- Revenue drop fix, Dashboard scores, Cinema Journal posters, Collect All $0
- Empty Series Market, Serie TV "Dal Mercato" crash (destructuring error)
- Rich actor data enrichment for existing cast proposals
- Full people migration, \u2022 literal rendering fix

## Backlog
- (P1) Guest Star per puntate singole nelle Serie TV
- (P1) Marketplace diritti TV/Anime
- (P1) Miglioramento sistema chat
- (P2) Contest Page mobile layout fix
- (P2) RBAC, CinePass, Stripe, PWA, Tutorial, Component decomposition
- (P2) Casting Agency building visual

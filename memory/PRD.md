# CineWorld Studio's - PRD

## Original Problem Statement
CineWorld Studio's is a cinematic simulation game. Players manage a film production house, create films with a cast system, compete in challenges, and grow their studio.

## Core Requirements
- Film creation wizard with cast selection (actors, directors, screenwriters, composers)
- Cast system with 50 unique skills (8 per member), IMDb rating, Star/Famous status
- Challenge system (1v1 only, with $50K participation cost and $100K prize)
- Festival system, cinema journal, social features, friends
- Infrastructure and marketplace (currently paused)
- Italian-only language

## Architecture
- **Backend:** FastAPI + MongoDB + APScheduler
- **Frontend:** React + TailwindCSS + Shadcn/UI + Framer Motion
- **Integrations:** OpenAI GPT-4o (text), GPT-Image-1 (poster), Resend (email)

## Key DB Collections
- `users`, `films`, `people` (cast), `challenges`, `notifications`, `release_notes`

## What's Been Implemented (v0.097)
- Complete cast system overhaul (8 skills/50 total, IMDb rating, Star/Famous)
- Advanced cast search by skill
- Age filter for actors (Giovani, 18-30, 31-50, 51+)
- Fixed film info bar during creation (title + genre)
- 1v1 challenges re-enabled with cost/prize system ($50K/$100K)
- 2v2/3v3/4v4/FFA removed
- Marketplace paused
- Drafts menu separated from pre-engagement
- System release notes updated to v0.097
- ErrorBoundary, global loading spinners
- Italian-only language enforcement

## Paused Features
- Infrastructure section (UI disabled)
- Marketplace (UI disabled) 
- Trailer generation (disabled)

## Backlog / Future Tasks
- (P0) Cast data migration for existing player saves
- (P1) Re-enable Infrastructure interactively
- (P2) CineCoins purchase system (Stripe)
- (P2) Major activities system
- (P3) Robust data migration scripts
- Refactor: Extract film creation logic from server.py
- Refactor: Create useFilmWizard custom hook

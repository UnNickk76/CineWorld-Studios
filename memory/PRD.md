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

## What's Been Implemented

### v0.098 (2026-03-12) - Fix Cast & Data Migration
- Migrazione completa: 8000 cast aggiornati con 8 skill ciascuno (0-100)
- Rating IMDb calcolato per tutti in base a skill/fama/esperienza
- Fame, is_star, fame_badge calcolati per tutti
- Spinner caricamento aggiunto a 15+ pagine
- Release notes aggiornate

### v0.097 (2026-03-12) - Sfide 1v1 & UI Improvements
- Sfide 1v1 riabilitate con costo/premio ($50K/$100K)
- Filtri età attori, barra info film fissa, marketplace in pausa
- Menu bozze separato da pre-ingaggi

### Previous versions
- Cast system overhaul (8 skills/50 total pool)
- Advanced cast search by skill
- ErrorBoundary, global loading spinners
- Italian-only language enforcement
- Disabled: Infrastructure, Marketplace, Trailer generation

## Paused Features
- Infrastructure section (UI disabled)
- Marketplace (UI disabled) 
- Trailer generation (disabled)

## Backlog / Future Tasks
- (P1) Re-enable Infrastructure interactively
- (P2) CineCoins purchase system (Stripe)
- (P2) Major activities system
- (P3) Robust data migration scripts
- Refactor: Extract film creation logic from server.py
- Refactor: Create useFilmWizard custom hook

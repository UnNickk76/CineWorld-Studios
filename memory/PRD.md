# CineWorld Studio's - PRD

## Original Problem Statement
CineWorld Studio's is a cinematic simulation game. Players manage a film production house, create films with a cast system, compete in challenges, and grow their studio.

## Architecture
- **Backend:** FastAPI + MongoDB + APScheduler
- **Frontend:** React + TailwindCSS + Shadcn/UI + Framer Motion
- **Integrations:** OpenAI GPT-4o (text), GPT-Image-1 (poster), Resend (email)

## What's Been Implemented

### v0.110 - Sceneggiature Emergenti & Bug Fixes (2026-03-13)
- Sceneggiature Emergenti con pausa/autosave, locandina classica, UI fixes
- **Critical Fix**: `BACKEND_URL` non definito in FilmDetail.jsx causava crash su tutti i film con trailer
- **Critical Fix**: Error handling robusto in loadFilm + optional chaining su director/screenwriter/composer/cast
- **Fix**: route catch-all /api/, MessageCircle import, errori Pydantic

### Previous (v0.101-v0.109)
- Wizard 12 step, 88+ location, sponsor dinamici, locandine AI
- Mobile nav, password change, poster polling, sfide manche automatiche

## Backlog
- (P0) Sito produzione DOWN - bloccato su supporto Emergent
- (P1) Riattivazione Infrastrutture
- (P2) Sistema acquisto CineCoins (Stripe)
- (P2) Attivita delle Major
- (P3) Script migrazione dati permanente

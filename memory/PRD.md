# CineWorld Studio's - PRD

## Original Problem Statement
CineWorld Studio's is a cinematic simulation game. Players manage a film production house, create films with a cast system, compete in challenges, and grow their studio.

## Architecture
- **Backend:** FastAPI + MongoDB + APScheduler
- **Frontend:** React + TailwindCSS + Shadcn/UI + Framer Motion
- **Integrations:** OpenAI GPT-4o (text), GPT-Image-1 (poster), Resend (email)

## What's Been Implemented

### v0.110 - Sceneggiature Emergenti & Bug Fixes (2026-03-13)
- **Sceneggiature Emergenti**: sceneggiature pronte con cast, rating IMDb, costi
  - Due opzioni: Solo Sceneggiatura / Pacchetto Completo
  - Integrazione FilmWizard con step bloccati (banner non invasivo)
  - Pausa e auto-save preservano contesto sceneggiatura acquistata
  - 20% sceneggiatori nuovi, scadenza 24-48h, scheduler ogni 2h
- **Locandina Classica**: fallback Pillow con gradiente tematico + testo overlay
- **FilmDetail error handling**: try/catch in loadFilm, pagina "Film non trovato" invece di crash ErrorBoundary
- **UI Fixes**: titolo mobile pt-16, hamburger menu, pallino notifica, errori Pydantic
- Release Notes v0.110

### Previous (v0.101-v0.109)
- Wizard 12 step, 88+ location, sponsor dinamici, locandine AI
- Mobile nav, password change, poster polling, sfide manche automatiche
- Animazioni battaglia, economia, colonna sonora, sfide 1v1

## Backlog
- (P0) Sito produzione DOWN (errori 520) - bloccato su supporto Emergent
- (P1) Riattivazione Infrastrutture
- (P2) Sistema acquisto CineCoins (Stripe)
- (P2) Attivita delle Major
- (P3) Script migrazione dati permanente
- Refactor: FilmWizard.jsx, server.py

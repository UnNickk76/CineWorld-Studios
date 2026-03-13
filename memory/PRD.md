# CineWorld Studio's - PRD

## Original Problem Statement
CineWorld Studio's is a cinematic simulation game. Players manage a film production house, create films with a cast system, compete in challenges, and grow their studio.

## Architecture
- **Backend:** FastAPI + MongoDB + APScheduler
- **Frontend:** React + TailwindCSS + Shadcn/UI + Framer Motion
- **Integrations:** OpenAI GPT-4o (text), GPT-Image-1 (poster), Resend (email)

## What's Been Implemented

### v0.110 - Sceneggiature Emergenti & UI Fixes (2026-03-13)
- **Sceneggiature Emergenti**: nuova sezione con sceneggiature pronte da produrre
  - 3-10 attive, generate ogni 2h, scadenza 24-48h
  - Rating IMDb per trama e trama+cast, due opzioni d'acquisto
  - Integrazione FilmWizard con step bloccati/sbloccati (banner non invasivo)
  - 20% sceneggiatori nuovi → pool permanente
- **Locandina Classica**: pulsante fallback con gradiente tematico + testo overlay (Pillow)
- **UI Fixes**: titolo pagina su mobile (pt-16), locked step banner, hamburger menu, pallino rosso notifica
- **Bug Fix**: errore creazione film (Pydantic validation → stringa), route catch-all /api/
- Release Notes v0.110, 6 nuovi endpoint API

### Previous (v0.101-v0.109)
- Wizard 12 step, 88+ location, sponsor dinamici, locandine AI con testo
- Mobile nav, password change, poster polling, sfide manche automatiche
- Animazioni battaglia, economia, colonna sonora, sfide 1v1

## Active Users (6)
- emiliano.andreola1@gmail.com, fandrex1@gmail.com, michi.me.1d@gmail.com
- demo@cineworld.com, fabriidesi@gmail.com, benedettavecchioni@outlook.it

## Backlog
- (P0) Sito produzione DOWN (errori 520) - bloccato su supporto Emergent
- (P1) Riattivazione Infrastrutture
- (P2) Sistema acquisto CineCoins (Stripe)
- (P2) Attivita delle Major
- (P3) Script migrazione dati permanente
- Refactor: FilmWizard.jsx, server.py

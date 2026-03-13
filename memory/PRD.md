# CineWorld Studio's - PRD

## Original Problem Statement
CineWorld Studio's is a cinematic simulation game. Players manage a film production house, create films with a cast system, compete in challenges, and grow their studio.

## Architecture
- **Backend:** FastAPI + MongoDB + APScheduler
- **Frontend:** React + TailwindCSS + Shadcn/UI + Framer Motion
- **Integrations:** OpenAI GPT-4o (text), GPT-Image-1 (poster), Resend (email)

## What's Been Implemented

### v0.110 - Sceneggiature Emergenti + Poster Fallback (2026-03-13)
- **Nuova sezione "Sceneggiature Emergenti"**: sceneggiature pronte da produrre con cast pre-scelto
  - 3-10 sceneggiature attive, generate ogni 2h dallo scheduler, scadenza 24-48h
  - Ogni sceneggiatura ha: titolo, genere, sinossi, sceneggiatore (20% nuovi talenti permanenti), cast proposto (regista, 3-5 attori, compositore), location, equipaggiamento
  - Rating IMDb per trama sola e trama+cast
  - Due opzioni d'acquisto: "Solo Sceneggiatura" (cast libero, sceneggiatore bloccato) e "Pacchetto Completo" (tutto bloccato tranne locandina)
  - Solo 1 giocatore può acquistare ogni sceneggiatura
  - Card Dashboard con badge notifica rosso per nuove sceneggiature
  - Integrazione con FilmWizard: step bloccati/sbloccati in base all'opzione scelta
- **Poster Fallback con Pillow**: quando l'AI non funziona, genera locandine con gradiente tematico per genere + overlay testo (titolo, regista, attori)
- Backend: 6 nuovi endpoint API (list, count, detail, accept, mark-seen + fallback poster)
- File: `emerging_screenplays.py` (150+ template sinossi/titoli per 16 generi), `EmergingScreenplays.jsx`
- Test: 100% backend (14/14), 100% frontend

### v0.109 - Fix Regressione Preview (2026-03-13)
- Fix route catch-all in server.py per escludere path /api/
- Fix import MessageCircle in FilmDetail.jsx

### Previous versions (v0.101-v0.108)
- Wizard film 12 step, 88+ location, sponsor dinamici, locandine AI con testo
- Mobile nav, password change, poster polling, sfide manche automatiche
- Animazioni battaglia, economia ricalibrata, colonna sonora, sfide 1v1

## Active Users (6)
- emiliano.andreola1@gmail.com, fandrex1@gmail.com, michi.me.1d@gmail.com
- demo@cineworld.com, fabriidesi@gmail.com, benedettavecchioni@outlook.it

## Note
- Preview usa database separato dal gioco live
- Sito produzione DOWN (errori 520) - in attesa supporto Emergent

## Backlog
- (P0) Sito produzione inaccessibile - bloccato su supporto Emergent
- (P1) Riattivazione Infrastrutture
- (P2) Sistema acquisto CineCoins (Stripe)
- (P2) Attivita delle Major
- (P3) Script migrazione dati permanente
- Refactor: FilmWizard.jsx, server.py

# CineWorld Studio's - PRD

## Original Problem Statement
CineWorld Studio's is a cinematic simulation game. Players manage a film production house, create films with a cast system, compete in challenges, and grow their studio.

## Architecture
- **Backend:** FastAPI + MongoDB + APScheduler
- **Frontend:** React + TailwindCSS + Shadcn/UI + Framer Motion
- **Integrations:** OpenAI GPT-4o (text), GPT-Image-1 (poster), Resend (email)

## What's Been Implemented

### v0.103 - Manche Automatiche, Studio View & Pulizia (2026-03-12)
- Sfide 1vs1: manche avanzano automaticamente (rimosso pulsante MANCHE SUCCESSIVA)
- Rimosso pulsante "Aggiorna" dalla board sfide, sostituito con "Storico"
- Popup giocatore: nuovo pulsante "Visita Studio" con vista completa della casa di produzione (Box Office, tutti i film, generi, premi, miglior film)
- Locandine ridimensionate 50%: griglia 10 colonne su desktop (grid-cols-4 sm:6 md:8 lg:10)
- Fix pagina Pre-Ingaggio: risolto crash dovuto a GENRES_LIST mancante
- Pulizia database: rimossi 49 utenti test, mantenuti solo 6 utenti reali
- Release notes v0.103 aggiunte

### v0.102 - Griglia Locandine, Header Fissi & Fix AI Poster (2026-03-12)
- Fix generazione locandine AI: compressione JPEG (12x piu leggero), retry, prompt con titolo+attori
- Header sezioni sticky con backdrop-blur durante lo scroll
- Dashboard mostra 10 film in evidenza

### v0.101 - Animazioni Battaglia, Booster & Fix Notifiche
- Animazioni battaglia skill, vittoria/sconfitta
- Sistema Booster per sfide
- Popup sfida al login per utenti offline

### v0.100 - Ricalibrazione Economia & Colonna Sonora
- Costi film 3x, incasso iniziale 10x
- Rating colonna sonora + 25% impatto su rating film

### Previous versions
- v0.099: Sfide offline/online separate
- v0.098: Fix cast 8 skill, IMDb rating, migrazione 8000 cast
- v0.097: Sfide 1v1 riabilitate ($50K/$100K), filtri eta

## Active Users (6)
- emiliano.andreola1@gmail.com (Emilians) - 5 film
- fandrex1@gmail.com (NeoMorpheus) - 5 film
- michi.me.1d@gmail.com (mic) - 4 film
- demo@cineworld.com (DemoUser) - 2 film
- fabriidesi@gmail.com (fabbro) - 1 film
- benedettavecchioni@outlook.it (Benny) - 0 film

## Paused Features
- Infrastructure section, Marketplace, Trailer generation

## Backlog
- (P1) Riattivazione Infrastrutture
- (P1) Migliorare locandine AI con testo (titolo + attori) - esplorativo
- (P2) Sistema acquisto CineCoins (Stripe)
- (P2) Attivita delle Major
- Refactor server.py, ChallengesPage.jsx

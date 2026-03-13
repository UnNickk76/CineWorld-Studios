# CineWorld Studio's - PRD

## Original Problem Statement
CineWorld Studio's is a cinematic simulation game. Players manage a film production house, create films with a cast system, compete in challenges, and grow their studio.

## Architecture
- **Backend:** FastAPI + MongoDB + APScheduler
- **Frontend:** React + TailwindCSS + Shadcn/UI + Framer Motion
- **Integrations:** OpenAI GPT-4o (text), GPT-Image-1 (poster), Resend (email)

## What's Been Implemented

### v0.104 - Ottimizzazione Mobile (2026-03-13)
- Navbar mobile: nascosti icone secondari (Major, Social, Journal, Chat, Utenti Online), solo essenziali visibili
- Griglia film mobile: 3 colonne (da 4), locandine piu grandi e leggibili
- Touch targets migliorati: pulsanti Ads/Trash piu grandi su mobile
- Card azioni Dashboard compatte su mobile (padding ridotto)
- Poster generation: indicatore di progresso "Generazione in corso... ~20s", retry automatico frontend, gestione timeout esplicita
- Testi poster generation tradotti in italiano

### v0.103 - Manche Automatiche, Studio View & Pulizia (2026-03-12)
- Sfide 1vs1: manche avanzano automaticamente
- Rimosso pulsante "Aggiorna" dalla board sfide
- Popup giocatore: "Visita Studio" con vista completa casa di produzione
- Locandine ridimensionate 50%: griglia 10 colonne su desktop
- Fix pagina Pre-Ingaggio: import GENRES_LIST
- Pulizia database: rimossi utenti test

### v0.102 - Griglia Locandine, Header Fissi & Fix AI Poster (2026-03-12)
- Fix generazione locandine AI: compressione JPEG (12x piu leggero), retry backend, prompt con titolo+attori
- Header sezioni sticky con backdrop-blur
- Dashboard mostra 10 film in evidenza

### Previous versions
- v0.101: Animazioni battaglia, sistema booster, popup sfide
- v0.100: Ricalibrazione economia, colonna sonora
- v0.099: Sfide offline/online
- v0.098: Fix cast 8 skill, migrazione 8000 cast
- v0.097: Sfide 1v1, filtri eta

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
- (P2) Sistema acquisto CineCoins (Stripe)
- (P2) Attivita delle Major
- Refactor server.py, ChallengesPage.jsx

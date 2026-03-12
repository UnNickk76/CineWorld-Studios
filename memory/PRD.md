# CineWorld Studio's - PRD

## Original Problem Statement
CineWorld Studio's is a cinematic simulation game. Players manage a film production house, create films with a cast system, compete in challenges, and grow their studio.

## Architecture
- **Backend:** FastAPI + MongoDB + APScheduler
- **Frontend:** React + TailwindCSS + Shadcn/UI + Framer Motion
- **Integrations:** OpenAI GPT-4o (text), GPT-Image-1 (poster), Resend (email)

## What's Been Implemented

### v0.102 - Griglia Locandine 6 Colonne, Header Fissi & Fix AI Poster
- Griglia film: 3 col (mobile) / 4 (sm) / 5 (md) / 6 (lg) su Dashboard e I Miei Film
- Header sezioni "I MIEI FILM" sticky con backdrop-blur durante lo scroll
- Dashboard mostra 6 film in evidenza (prima 4)
- Fix generazione locandine AI: compressione JPEG (12x piu leggero), retry automatico, prompt migliorato
- Locandine AI ora includono titolo film e nomi attori nel prompt

### v0.101 - Animazioni Battaglia, Booster & Fix Notifiche
- Animazioni battaglia: skill si rivelano una per volta con frasi epiche italiane
- Animazione vittoria (confetti) e sconfitta (effetto drammatico)
- Sistema Booster: +20% skill su un film (costo esponenziale inversamente proporzionale alla qualita)
- Tasto Contro-Sfida a fine match
- Popup sfida al login per utenti offline
- Fix routing notifiche (ogni tipo -> pagina corretta)

### v0.100 - Ricalibrazione Economia & Colonna Sonora
- Costi film 3x, incasso iniziale 10x base
- Rating colonna sonora visibile + 25% impatto su rating film
- Boost esponenziale colonna sonora primi 3 giorni al botteghino

### Previous versions
- v0.099: Sfide offline/online separate
- v0.098: Fix cast 8 skill, IMDb rating, migrazione 8000 cast
- v0.097: Sfide 1v1 riabilitate ($50K/$100K), filtri eta, barra info film

## Paused Features
- Infrastructure section, Marketplace, Trailer generation

## Backlog
- (P1) Riattivazione Infrastrutture
- (P2) Sistema acquisto CineCoins (Stripe)
- (P2) Attivita delle Major
- Refactor server.py, custom hook useFilmWizard

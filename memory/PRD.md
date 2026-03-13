# CineWorld Studio's - PRD

## Original Problem Statement
CineWorld Studio's is a cinematic simulation game. Players manage a film production house, create films with a cast system, compete in challenges, and grow their studio.

## Architecture
- **Backend:** FastAPI + MongoDB + APScheduler
- **Frontend:** React + TailwindCSS + Shadcn/UI + Framer Motion
- **Integrations:** OpenAI GPT-4o (text), GPT-Image-1 (poster), Resend (email)

## What's Been Implemented

### v0.105 - Mobile Nav, Password Change, Poster Polling (2026-03-13)
- Barra navigazione inferiore mobile: Home, Film, Social, Sfide, Chat, Notifiche
- Navbar superiore mobile: solo icone essenziali, secondari nascosti
- Cambio password dal profilo utente (backend + frontend)
- Generazione locandine AI: sistema a polling (start + status) per evitare timeout su mobile
- Fix JSX parsing error per Online Users Panel Dialog

### v0.104 - Ottimizzazione Mobile (2026-03-13)
- Griglia film mobile: 3 colonne, touch targets migliorati
- Card azioni Dashboard compatte
- Poster generation: indicatore progresso, retry frontend, timeout 120s

### v0.103 - Manche Automatiche, Studio View & Pulizia (2026-03-12)
- Sfide manche automatiche, Visita Studio popup, Pre-Ingaggio fix
- Pulizia utenti test, release notes v0.103

### v0.102 - Griglia Locandine, Header Fissi & Fix AI Poster (2026-03-12)
- JPEG compression (12x smaller), header sticky, 10 film featured

### Previous versions
- v0.101: Animazioni battaglia, booster, popup sfide
- v0.100: Economia ricalibrata, colonna sonora
- v0.097-099: Sfide 1v1, filtri eta, cast migration

## Active Users (6)
- emiliano.andreola1@gmail.com (Emilians), fandrex1@gmail.com (NeoMorpheus)
- michi.me.1d@gmail.com (mic), demo@cineworld.com (DemoUser)
- fabriidesi@gmail.com (fabbro), benedettavecchioni@outlook.it (Benny)

## Note
- Preview usa database separato dal gioco live (progressi non sincronizzati)

## Backlog
- (P1) Riattivazione Infrastrutture
- (P2) Sistema acquisto CineCoins (Stripe)
- (P2) Attivita delle Major
- Refactor server.py, ChallengesPage.jsx

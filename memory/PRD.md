# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica. Proprietà di **Andreola Fabio**.

## Versione Attuale: v0.090

## Funzionalità Implementate (Ultime)

### v0.090 - Fluidità Navigazione & Ottimizzazioni - 11/03/2026
- **Transizioni di Pagina Animate**: PageTransition + AnimatePresence in ProtectedRoute per transizioni fluide tra pagine
- **Code-Splitting**: React.lazy() per ReleaseNotes, TutorialPage, CreditsPage con Suspense + PageSkeleton fallback
- **Ottimizzazione Polling API**: TopNavbar non ri-esegue tutte le API su ogni cambio pagina (da ~8 a ~2 chiamate per navigazione)
- **Rimozione Polling Duplicato**: ChatPage non duplica più il polling di /users/online (già gestito da TopNavbar)
- **CSS Transizioni Smooth**: Bottoni e link con transizioni 150ms per hover e interazioni

### v0.089 - Manche Singole, Notifiche Cliccabili & Film Uscito - 11/03/2026
- **Report Manche Singole**: Navigazione Avanti/Indietro tra le 3 manche della sfida, una per pagina
- **Notifiche Cliccabili**: Ogni notifica porta al contenuto (sfida, film, trailer, festival, social)
- **Notifica Film Uscito**: Nuova notifica con qualità e incasso quando il film esce
- **Sfide Offline Default**: `accept_offline_challenges=true` per tutti (nuovi e esistenti)

### v0.087 - Battaglie 3 Manche, Fix Qualità & Rinegoziazione
- 3 manche film-vs-film con 8 skill battles + spareggio gradimento pubblico
- Fix qualità film (base 42, distribuzione bilanciata)
- Rinegoziazione cast (fino a 3 tentativi)

### v0.085 - Poster AI, Popup IMDb, Bonus Online
- Poster GPT Image 1, Popup IMDb 6 fattori, Bonus Online +15%, Dashboard pulita

### v0.083 - Mini-Giochi VS 1v1 & Fix Stabilità
- Mini-Giochi VS, Fix BattleAnimation, Fix Pydantic, Script migrazione

## Architettura
- Backend: FastAPI + MongoDB (motor), server.py (~15.6k righe)
- Frontend: React + TailwindCSS + Shadcn/UI, App.js (~15k righe)
- AI: OpenAI GPT-4o (text), GPT Image 1 (poster) via Emergent LLM Key
- Battle: challenge_system.py (3 manche x 8 skill + tiebreaker)
- DB: films, users, user_infrastructures, challenges, minigame_versus, rejections, notifications
- Animations: framer-motion per transizioni di pagina

## Backlog

### P0 - Critico
- [ ] Refactoring server.py e App.js (>15k righe ciascuno) - URGENTE

### P1 - Prossimi
- [ ] Completamento Gameplay Contest Live (matchmaking, classifiche)
- [ ] Attività delle Major (espansione)

### P2 - Futuri
- [ ] Sistema Acquisto CineCoins (Stripe)
- [ ] Classifiche VS e sistema ELO

### P3 - Backlog
- [ ] Scalabilità (Redis, load balancer)

## Credenziali di Test
- TestPlayer1: test1@test.com / Test1234!
- TestPlayer2: test2@test.com / Test1234!

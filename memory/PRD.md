# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica. Proprietà di **Andreola Fabio**.

## Versione Attuale: v0.091

## Funzionalità Implementate (Ultime)

### v0.091 - Fix Hamburger, Trailer Sora 2, Grafica Sfide, Cast Espanso - 11/03/2026
- **Hamburger visibile su web**: Rimosso `lg:hidden`, ora visibile su tutti gli schermi (mobile + desktop)
- **Generazione Trailer Sora 2**: Sostituito FFmpeg con Sora 2 AI per generare trailer video reali dalla trama. Durate: 4s, 8s, 12s. Costo variabile: base 10k, esponenziale per durata e rating. Rimborso automatico in caso di errore.
- **Nuovo endpoint /api/ai/trailer-cost**: Preview costo trailer prima della generazione
- **Sfide Offline - Grafica Uniforme**: Card offline ridisegnata con stile identico alle sfide online (gradient, icona, freccia)
- **Cast Espanso**: Aggiunte 13 nuove nazionalità (Russia, Australia, Nigeria, Turkey, Sweden, Argentina, Canada, Poland, Thailand, Egypt, Iran, South Africa). Pool iniziale aumentato da 2000 a 4000+. Generazione giornaliera da 10-20 a 25-50 per tipo.
- **Rinegoziazione Cast**: Verificata funzionante in entrambi i flussi (FilmWizard e PreEngagement)
- **Sfide Offline Default ON**: Confermato attivo, badge "Accepting" visibile

### v0.090 - Fluidità Navigazione & Ottimizzazioni - 11/03/2026
- Transizioni di Pagina Animate con PageTransition + AnimatePresence
- Code-Splitting con React.lazy() per ReleaseNotes, TutorialPage, CreditsPage
- Ottimizzazione Polling API (da ~8 a ~2 chiamate per navigazione)
- CSS Transizioni Smooth per bottoni e link

### Versioni Precedenti
- v0.089: Report Manche Singole, Notifiche Cliccabili, Notifica Film Uscito, Sfide Offline Default
- v0.087: Battaglie 3 Manche, Fix Qualità Film, Rinegoziazione Cast
- v0.085: Poster AI GPT Image 1, Popup IMDb, Bonus Online
- v0.083: Mini-Giochi VS 1v1, Fix BattleAnimation, Fix Pydantic

## Architettura
- Backend: FastAPI + MongoDB (motor), server.py (~15.6k righe)
- Frontend: React + TailwindCSS + Shadcn/UI, App.js (~15k righe)
- AI: OpenAI GPT-4o (text), GPT Image 1 (poster), Sora 2 (trailer) via Emergent LLM Key
- Battle: challenge_system.py (3 manche x 8 skill + tiebreaker)
- Cast: cast_system.py (25 nazionalità, 4000+ pool)
- DB: films, users, user_infrastructures, challenges, minigame_versus, rejections, negotiations, notifications
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

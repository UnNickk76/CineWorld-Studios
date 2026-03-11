# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica. Proprietà di **Andreola Fabio**.

## Versione Attuale: v0.085

## Funzionalità Implementate

### v0.085 - Poster AI, Battaglie 8 Skill & Popup IMDb - 11/03/2026 (COMPLETATO)
- **Locandine AI (GPT Image 1)**: Poster generati dall'AI coerenti con titolo, genere e descrizione del film
- **Sistema Battaglie 8 Skill**: Ogni sfida ha 8 mini-battaglie (Regia, Fotografia, Sceneggiatura, Recitazione, Colonna Sonora, Effetti Speciali, Montaggio, Carisma) con commenti coerenti
- **Meccanica Upset**: Film con skill inferiori possono vincere raramente (3-15% probabilità)
- **Popup IMDb**: Cliccando sul punteggio IMDb mostra 6 fattori di valutazione dettagliati
- **Bonus Online**: +15% ricompense per chi gioca sfide in modalità online
- **Dashboard pulita**: Rimosse statistiche contest dalla dashboard, mantenute nei mini-giochi
- **Rimosso tasto Aggiorna** dalla sezione sfide VS

### v0.083 - Mini-Giochi VS 1v1 & Fix Stabilità - 11/03/2026 (COMPLETATO)
- Mini-Giochi VS 1v1 competitivo con 5 endpoint backend + UI completa
- Fix BattleAnimation (Chiudi/Salta/Continua)
- Fix Pydantic FilmResponse + script migrazione dati (45 film, 41 utenti)
- Miglioramento mobile dialogs

### Versioni precedenti (v0.080-v0.082)
- Sfide Offline VS AI, Upgrade Infrastrutture, Statistiche Cinema
- Locandine/Trailer Gratuiti, Contest, Revenue Infrastruttura
- GlobalPlayerPopup, Mini-Giochi AI, Note di Rilascio

## Architettura
- Backend: FastAPI + MongoDB (motor), server.py (~15.5k righe)
- Frontend: React + TailwindCSS + Shadcn/UI, App.js (~14.9k righe)
- AI: OpenAI GPT-4o (text), GPT Image 1 (poster) via Emergent LLM Key
- Media: FFmpeg (trailer)
- DB Collections: films, users, user_infrastructures, challenges, minigame_versus, notifications

## API Endpoints Chiave
- `POST /api/ai/poster` - Genera poster AI con GPT Image 1
- `POST /api/minigames/versus/create` - Crea sfida VS mini-giochi
- `POST /api/minigames/versus/{id}/answer` - Risposte VS
- `GET /api/minigames/versus/pending` - Sfide aperte
- `POST /api/challenges/offline-battle` - Sfida offline vs AI

## Backlog

### P0 - Critico
- [ ] **Refactoring Critico**: server.py e App.js monolitici

### P1 - Prossimi
- [ ] **Completamento Gameplay Contest Live**: matchmaking avanzato, classifiche
- [ ] **Attività delle Major**: espandere sistema attività

### P2 - Futuri
- [ ] Sistema Acquisto CineCoins (Stripe)
- [ ] Classifiche VS e sistema ELO per mini-giochi

### P3 - Backlog
- [ ] Scalabilità (Redis, load balancer)

## Credenziali di Test
- TestPlayer1: test1@test.com / Test1234!
- TestPlayer2: test2@test.com / Test1234!

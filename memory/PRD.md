# CineWorld Studio's — PRD

## Problema Originale
Sistema di produzione cinematografica con pipeline completa, PvP, infrastrutture, arena, guerre Major, e sistema minigiochi competitivo.

## Architettura
- **Frontend**: React + Tailwind + Shadcn/UI + Framer Motion
- **Backend**: FastAPI + MongoDB
- **Background**: `apscheduler` per loop economia

## Funzionalita Completate

### Core + Eventi + Infra + Arena + Guerra (DONE precedentemente)
### Data Integrity System (DONE)

### Sistema Minigiochi v3 (DONE)
12 minigiochi in file separati (`/components/games/*Game.jsx`) con props `{ mode, onComplete(score) }`

### Refactoring Minigiochi (DONE)
- `MiniGames.jsx` puro re-export, zero duplicazione

### P1 Blocco Completo (DONE - 2026-04-07)

#### 1. MiniGamesPage — Modalita Solo + Classifiche + Statistiche
- Route `/minigiochi` con 4 tab: Solo, VS 1v1, Classifica, Stats
- **Solo**: Griglia 12 giochi, click per giocare, salvataggio punteggio + best score
- **Classifiche**: Per gioco (sempre/settimana) + Globale, top 50
- **Stats**: Record, media, partite per ogni gioco
- Backend: `/api/arcade/solo/submit`, `/api/arcade/solo/stats`, `/api/arcade/leaderboard/{game_id}`, `/api/arcade/leaderboard-global`

#### 2. VS 1v1 Minigiochi
- Tab VS 1v1 con sub-tab: Lancia, Aperte, Storico
- **Lancia**: Scegli gioco, gioca, punteggio registrato, sfida pubblicata
- **Aperte**: Vedi sfide di altri, "Accetta" per giocare lo stesso gioco
- **Storico**: Tutte le sfide con stato (Vittoria/Sconfitta/Pareggio/In attesa)
- Sistema puntate con crediti (opzionale), pot winner-takes-all
- Backend: `/api/arcade/vs/create`, `/api/arcade/vs/{id}/submit-creator`, `/api/arcade/vs/{id}/join`, `/api/arcade/vs/{id}/submit-opponent`, `/api/arcade/vs/pending`, `/api/arcade/vs/my`

#### 3. Chat Integration Sfide Minigioco
- Bottone "Sfida" nel profilo utente (UserProfileModal) nella chat
- Bottone sfida (icona Gamepad2) nella lista utenti online
- Game Picker Dialog: scegli quale minigioco lanciare
- Messaggio tipo `minigame_challenge` nella chat con card speciale e bottone "Gioca"
- Notifica push al destinatario
- Backend: `/api/arcade/chat-challenge` (crea sfida + messaggio chat + notifica)

## File Chiave
- `/app/frontend/src/components/games/*Game.jsx` (12 minigiochi separati)
- `/app/frontend/src/components/MiniGames.jsx` (re-export)
- `/app/frontend/src/pages/MiniGamesPage.jsx` (Solo + VS + Classifiche + Stats)
- `/app/frontend/src/pages/ContestPage.jsx` (12 step contest)
- `/app/frontend/src/pages/ChatPage.jsx` (Chat con sfide minigioco)
- `/app/backend/routes/minigames_arcade.py` (Solo + VS + Chat Challenge API)
- `/app/backend/routes/contest.py` (12 step contest)

## DB Collections Nuove
- `arcade_solo_plays`: { id, user_id, nickname, game_id, score, played_at }
- `arcade_vs`: { id, game_id, game_name, bet, creator_id, creator_nickname, creator_score, opponent_id, opponent_nickname, opponent_score, status, winner_id, is_chat_challenge, created_at, expires_at, completed_at }

## Backlog

### P2 — Miglioramenti Minigiochi
- [ ] Streak system (3/5/10 win = bonus/badge/reward)
- [ ] Puntate con hype oltre a crediti
- [ ] Status player (online/in partita/occupato)
- [ ] Titoli player (Maestro del Ciak, Re dello Snake, etc)
- [ ] Cooldown reward per modalita solo

### P3
- [ ] Sistema "Previsioni Festival" (scommesse vincitori)
- [ ] Marketplace TV/Anime rights
- [ ] Velion Mood, Chat Evolution, CinePass+Stripe, Push, Velion Levels

## Credenziali Test
- NeoMorpheus: fandrex1@gmail.com / Fandrel2776

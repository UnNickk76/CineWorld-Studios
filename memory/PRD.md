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
### Sistema Minigiochi v3 + Refactoring (DONE)
### P1 Blocco Completo - MiniGamesPage + VS + Chat (DONE)

### P2 Blocco Completo (DONE - 2026-04-07)

#### 1. Streak System
- Tracciamento vittorie consecutive VS per ogni utente
- Campi `vs_streak`, `best_vs_streak`, `vs_wins`, `vs_losses` su utente
- Milestones: 3 vittorie (+$5,000), 5 vittorie (+$15,000), 10 vittorie (+$50,000)
- Notifica in-app al raggiungimento del milestone
- StreakBadge visuale (giallo/arancione/rosso in base al livello)
- Banner streak in tab VS con record e W/L ratio

#### 2. Titoli Player
- 12 titoli unici legati ai giochi, sbloccati al raggiungimento di una soglia di punteggio
- Titoli: Maestro del Ciak, Mente Cinematica, Occhio di Falco, Dita di Fuoco, Riflessi da Stunt, Regista Preciso, Maestro delle Luci, Casting Director, Montatore Leggendario, Operatore Stellare, Caos Controllato, Serpente d'Argento
- Badge gialli nella sezione Stats e header pagina
- Collection `arcade_titles`: { user_id, game_id, title, earned_at }

#### 3. Status Online/In Partita
- 3 stati: `idle` (online), `playing` (in gioco solo), `in_vs` (in VS 1v1)
- Aggiornamento automatico all'ingresso/uscita da un minigioco
- Visibile nella lista utenti della chat ("In gioco" cyan, "In VS 1v1" viola)
- Campo `game_status` nella collection users, esposto nell'endpoint presence

#### 4. Reward Modalita Solo con Cooldown
- Ogni partita solo assegna: +1-3 hype, +5-15 XP, rare volte crediti ($100-$500)
- Cooldown 4 ore per gioco (collection `arcade_solo_cooldowns`)
- Icona regalo verde (Gift) indica reward disponibile
- "Reward in cooldown" mostrato nei risultati quando non disponibile
- Risultato completo: score, best, reward, new_title

## File Chiave
- `/app/frontend/src/components/games/*Game.jsx` (12 minigiochi)
- `/app/frontend/src/components/MiniGames.jsx` (re-export)
- `/app/frontend/src/pages/MiniGamesPage.jsx` (Solo + VS + Classifiche + Stats + Streak + Titoli)
- `/app/frontend/src/pages/ContestPage.jsx` (12 step contest)
- `/app/frontend/src/pages/ChatPage.jsx` (Chat con sfide + status gioco)
- `/app/backend/routes/minigames_arcade.py` (Full API: Solo/VS/Chat/Streak/Titles/Status)
- `/app/backend/routes/contest.py` (12 step contest)
- `/app/backend/routes/users.py` (Presence con game_status)

## DB Collections
- `arcade_solo_plays`: { id, user_id, nickname, game_id, score, played_at }
- `arcade_solo_cooldowns`: { user_id, game_id, last_reward_at }
- `arcade_vs`: { id, game_id, game_name, bet, creator_*, opponent_*, status, winner_id, ... }
- `arcade_titles`: { user_id, game_id, title, earned_at }
- `users` (campi aggiunti): game_status, vs_streak, best_vs_streak, vs_wins, vs_losses

## Backlog

### P3
- [ ] Sistema "Previsioni Festival" (scommesse vincitori)
- [ ] Marketplace TV/Anime rights
- [ ] Velion Mood, Chat Evolution, CinePass+Stripe, Push, Velion Levels

## Credenziali Test
- NeoMorpheus: fandrex1@gmail.com / Fandrel2776

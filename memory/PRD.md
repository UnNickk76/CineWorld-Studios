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

### Sistema Minigiochi v3 (DONE - 2026-04-07)
**12 minigiochi in file separati (`/components/games/*Game.jsx`):**
1. TapCiak — ciak cadenti fullscreen, spawn 1-5, velocita variabile
2. Memory Pro — 40 carte (20 coppie) icone cinema Lucide, flip, combo bonus, 60s
3. Stop Perfetto — barra velocissima (200px/s), zona verde 8%, stop immediato
4. Spam Click — 4s, feedback animato con flash
5. Reaction Game — 3 round, tempo reazione
6. Shot Perfect — soggetto mobile, tappa quando centrato
7. Light Setup — slider luce, raggiungi target
8. Cast Match — scegli attore corretto, timer 15s
9. Editing Cut — tappa nel momento giusto del montaggio
10. Follow Cam — segui stella col dito
11. Chaos Premiere (BONUS) — tap caotico: ciak/stelle/ticket/bombe, shake, 10s
12. Reel Snake (BONUS) — snake game, swipe, 30s, velocita crescente

### Refactoring Minigiochi (DONE - 2026-04-07)
- 12 componenti separati in `/components/games/*Game.jsx`
- Ogni componente accetta `{ mode, onComplete(score) }`
- Zero logica DB nei componenti, delegano al genitore
- `MiniGames.jsx` e ora un puro file di re-export
- `ContestPage.jsx` aggiornato per usare `onComplete`

**Contest 12 step:**
- Step 1-10: minigiochi, max 30 crediti (3/step)
- Step 11-12: bonus, max 10 crediti ciascuno (10/step)
- Totale: max 50 crediti/giorno
- Backend: TOTAL_STEPS=12, cooldown 2min tra step

**Test Lab:** Usa gli stessi componenti reali, zero duplicazioni (in pausa)

## File Chiave
- `/app/frontend/src/components/games/*Game.jsx` (12 minigiochi separati)
- `/app/frontend/src/components/MiniGames.jsx` (re-export centralizzato)
- `/app/frontend/src/pages/ContestPage.jsx` (12 step contest)
- `/app/frontend/src/pages/AdminPage.jsx` (Admin + TestLab)
- `/app/backend/routes/contest.py` (12 step, reward differenziate)

## Backlog

### P1 — Blocco 2: MinigiochiPage + Solo + Classifiche
- [ ] MinigiochiPage.jsx con sezioni Gioca Solo, Classifiche, Statistiche
- [ ] Reward solo: hype/EXP/denaro piccoli, crediti rari (cooldown 1-20gg)
- [ ] Classifiche globali/settimanali/per gioco
- [ ] Titoli player (Maestro del Ciak, Re dello Snake, etc)

### P2 — Blocco 3: 1vs1 + Puntate + Chat
- [ ] Tab "Minigiochi VS" nella board sfide esistente (mantenere icona spade)
- [ ] Match 1vs1: stesso gioco, stesso timer, vince chi fa piu punti
- [ ] Puntate crediti/hype, winner prende tutto
- [ ] Streak system (3/5/10 win = bonus/badge/reward)
- [ ] Chat integration: sfida da popup, notifica live, quick challenge
- [ ] Status player (online/in partita/occupato)
- [ ] La sfida 1vs1 esistente rimane come 13esimo minigioco

### P3
- [ ] Sistema "Previsioni Festival" (scommesse vincitori)
- [ ] Marketplace TV/Anime rights
- [ ] Velion Mood, Chat Evolution, CinePass+Stripe, Push, Velion Levels

## Credenziali Test
- NeoMorpheus: fandrex1@gmail.com / Fandrel2776

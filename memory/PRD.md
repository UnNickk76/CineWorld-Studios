# CineWorld Studio's — PRD

## Problema Originale
Sistema di produzione cinematografica con pipeline completa. Esperienza utente visiva, cinematografica e immersiva con PvP, infrastrutture, arena e guerre tra Major.

## Architettura
- **Frontend**: React + Tailwind + Shadcn/UI + Framer Motion
- **Backend**: FastAPI + MongoDB
- **Background**: `apscheduler` per il loop economia (ogni 10min)

## Funzionalita Completate

### Core (DONE precedentemente)
- La Prima, Content Template, Cinema Journal, Guest + Tutorial, DB fixes, Major, Timing Cinematici

### Sistema Eventi + Infrastrutture + Arena + Guerra (DONE)
- event_pressure, trigger sigmoide, Arena Mirata, Major Warfare, Infra Detail

### Data Integrity System (DONE)
- Auto-scan, API recovery, transazioni atomiche film

### Sistema Contest Mini-giochi v2 (DONE - 2026-04-07)
- **MiniGames.jsx condiviso**: TapCiak (ciak cadenti, spawn random), MemoryPro (40 carte, 20 coppie, combo bonus, 45s timer), StopPerfetto (barra velocissima, zona verde piccola, stop immediato), SpamClick (4s, feedback animato), ReactionGame (NUOVO — tempo reazione, 3 round)
- **ContestPage.jsx**: 5 step con mini-giochi reali, punteggio cumulativo, reward
- **Backend**: TOTAL_STEPS=5, cooldown 3min
- Zero codice duplicato

### Test Lab Sandbox Visiva v2 (DONE - 2026-04-07)
- Usa mini-giochi REALI da MiniGames.jsx (non duplicati/mock)
- Film Pipeline INTERATTIVA (4 step con scelte: sceneggiatura, hype, location, rilascio)
- Arena MANUALE (3 azioni: supporta, boicotta, contromossa)
- Major MANUALE (3 azioni: sfida, recluta, investi)
- Eventi usano VelionCinematicEvent reale con mock data
- Storico leggibile con replay cliccabile
- Fix useRef import
- Zero DB, zero JSON, mobile-first

## File Chiave
- `/app/frontend/src/components/MiniGames.jsx` (6 mini-giochi condivisi)
- `/app/frontend/src/pages/ContestPage.jsx` (5 step con mini-giochi)
- `/app/frontend/src/pages/AdminPage.jsx` (Admin + TestLab)
- `/app/backend/routes/contest.py` (TOTAL_STEPS=5)

## Backlog

### P1
- [ ] Sistema "Previsioni Festival" (scommesse vincitori)

### P2
- [ ] Marketplace TV/Anime rights

### P3
- [ ] Velion Mood, Chat Evolution, CinePass+Stripe, Push, Velion Levels, Eventi globali, Velion AI Memory

## Credenziali Test
- Utente: NeoMorpheus (fandrex1@gmail.com / Fandrel2776)

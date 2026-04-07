# CineWorld Studio's — PRD

## Problema Originale
Sistema di produzione cinematografica con pipeline completa. Esperienza utente visiva, cinematografica e immersiva con PvP, infrastrutture, arena e guerre tra Major.

## Architettura
- **Frontend**: React + Tailwind + Shadcn/UI + Framer Motion
- **Backend**: FastAPI + MongoDB
- **Background**: `apscheduler` per il loop economia (ogni 10min)

## Funzionalita Completate

### Core (DONE precedentemente)
- La Prima, Content Template, Cinema Journal ULTRA, Guest + Tutorial
- DB Bloat Fix, Pulizia server.py, Soft Expansion Major
- Timing Cinematici, Serie TV/Anime nel Auto-Tick
- Throttling Coda, Anti-Spam Notifiche, Major con navbar interna

### Sistema Eventi Avanzato a Pressione (DONE - 2026-04-06)
- event_pressure per utente, trigger sigmoide
- Rarita basata su pressione (common->legendary)
- Star Birth legata a eventi

### Pagina EVENTI con 4 Categorie (DONE - 2026-04-06)
- 5 tab: TUTTI, LEGGENDARI, EPICI, RARI, COMUNI
- Bottone "Rivedi Evento" per replay cinematico

### FASE 1 & 2: Infrastrutture, Arena, Guerra (DONE - 2026-04-07)
- Arena Mirata (3 endpoint), Major Warfare temporizzato (4 endpoint), Infra Detail API (3 endpoint)
- Frontend: 4 sub-tab infra, tab Mirata PvP, Guerra evoluta Major

### Refactor Eventi Scalabile (DONE - 2026-04-07)
- Cooldown 6h per player, selezione film pesata

### Data Integrity System (DONE - 2026-04-07)
- Auto-scan all'avvio, API di recovery, UI fallback per film corrotti
- Transazioni atomiche per creazione/transizioni di stato film

### Sistema Contest Mini-giochi (DONE - 2026-04-07)
- 11 step giornalieri con 5 mini-giochi: TapCiak, Memory, Timing, SpamClick, Quiz
- Ricompense in crediti (MAX_DAILY_CREDITS = 20), reset 09:00 UTC, cooldown 5min
- Backend: `/api/contest/progress`, `/api/contest/complete-step`
- Frontend: `/contest` route

### Test Lab System (DONE - 2026-04-07)
- Sistema di test in-memory (no DB) per Admin Panel
- 7 test simulati: Film Pipeline, Contest, Eventi (3 tipi), Arena, Major
- Backend: `/api/admin/test/{type}` endpoints, `/api/admin/test/reports` storico
- Frontend: Tab "Test Lab" in AdminPage con griglia bottoni, report JSON, storico, effetto blackout CSS

## Backlog Prioritizzato

### P1
- [ ] Sistema "Previsioni Festival" (scommesse vincitori)

### P2
- [ ] Marketplace TV/Anime rights

### P3
- [ ] Velion Mood, Chat Evolution, CinePass+Stripe, Push, Velion Levels, Eventi globali, Velion AI Memory

## File Chiave
- `/app/backend/models/contest.py` (Schema contest)
- `/app/backend/routes/contest.py` (API contest)
- `/app/frontend/src/pages/ContestPage.jsx` (Mini-giochi)
- `/app/frontend/src/pages/AdminPage.jsx` (Admin + Test Lab)
- `/app/backend/server.py` (Test Lab endpoints in fondo)

## Credenziali Test
- Utente: NeoMorpheus (fandrex1@gmail.com / Fandrel2776)

## 3rd Party
- Stripe, Gemini Nano Banana (Emergent LLM Key)

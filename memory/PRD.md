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
**Cambio logica**: eventi calcolati per PLAYER (1 estrazione), NON per film
- Cooldown 6h per player (MIN_HOURS_BETWEEN_EVENTS = 6, configurabile)
- Selezione film pesata: peso = hype + quality + (imdb*10)
- Film migliori ricevono piu eventi proporzionalmente
- Scalabile: N eventi = f(N player), non f(N film)
- Rimossa query 12h cooldown per film (non piu necessaria)
- Pressure read/update 1 sola volta per player per tick

## Backlog Prioritizzato

### P1
- [ ] Sistema "Previsioni Festival" (scommesse vincitori)

### P2
- [ ] Contest Page Mobile Layout fix (bug ricorrente 16+ segnalazioni)
- [ ] Marketplace TV/Anime rights

### P3
- [ ] Velion Mood, Chat Evolution, CinePass+Stripe, Push, Velion Levels, Eventi globali, Velion AI Memory

## File Chiave
- `/app/backend/scheduler_tasks.py` (Auto-tick + pressure per-player + weighted selection)
- `/app/backend/event_templates.py` (INFRA_EVENTS, WAR_EVENTS, STRATEGIC_ABILITIES)
- `/app/backend/routes/pvp.py` (Arena mirata)
- `/app/backend/routes/major.py` (Major Warfare)
- `/app/backend/routes/infrastructure.py` (Infra detail API)
- `/app/frontend/src/pages/InfrastructurePage.jsx` (4 sub-tab)
- `/app/frontend/src/pages/PvPArenaPage.jsx` (Tab Mirata)
- `/app/frontend/src/pages/MajorPage.jsx` (Guerra evoluta)

## Credenziali Test
- Utente: NeoMorpheus (fandrex1@gmail.com / Fandrel2776)

## 3rd Party
- Stripe, Gemini Nano Banana (Emergent LLM Key)

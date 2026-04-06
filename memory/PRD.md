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
- Rarita basata su pressione (common→legendary)
- Star Birth legata a eventi

### Pagina EVENTI con 4 Categorie (DONE - 2026-04-06)
- 5 tab: TUTTI, LEGGENDARI, EPICI, RARI, COMUNI
- Bottone "Rivedi Evento" per replay cinematico

### Sequenza Cinematica (DONE - 2026-04-06)
- Velion laterale, glow animato, skip bloccato 4s

### Distribuzione Temporizzata Eventi (DONE - 2026-04-06)
- 1° dopo 2min, 2° 10min, 3° 20min, 4° 35min

### FASE 1 & 2: Infrastrutture, Arena, Guerra (DONE - 2026-04-07)

**Backend — Arena Mirata (pvp.py)**:
- `POST /api/pvp/arena-attack`: Attacco mirato a categoria infra (cinema/tv/commerciale/agenzie)
- Abilita strategiche difensive: Div. Legale (blocca attacco), Div. Operativa (riduce danni), Div. Investigativa (identifica attaccante)
- Costo: 4 CP, Cooldown: 12h per target, richiede Div. Operativa Lv1+
- `GET /api/pvp/arena-targets`: Lista bersagli con categorie disponibili
- `GET /api/pvp/arena-history`: Cronologia attacchi mirati (inviati/ricevuti)

**Backend — Major Warfare (major.py)**:
- `POST /api/major/war/declare`: Guerra temporizzata 24/48/72h, costo $1M, founder only
- `GET /api/major/war/active`: Stato guerra attiva con auto-resolve a scadenza
- `POST /api/major/war/strike`: Colpo durante guerra (infra/film/fame), 3 CP, cooldown 2h
- `POST /api/major/war/calculate`: Guerra rapida (calcolo istantaneo, legacy)
- Score tracking, events log, winner determination

**Backend — Infra Detail API (infrastructure.py)**:
- `GET /api/infrastructure/{id}/events`: Eventi e attacchi arena per infra
- `GET /api/infrastructure/{id}/security`: Livello minaccia, difese attive, statistiche 7g
- `GET /api/infrastructure/{id}/influence`: Bonus categoria, impatto su progetti attivi

**Frontend — InfrastructurePage.jsx**:
- 4 sub-tab nel dialog dettaglio: Panoramica, Eventi, Sicurezza, Influenza
- Panoramica: stats, upgrade, film in programmazione (esistente, riorganizzato)
- Eventi: eventi infra + attacchi arena subiti
- Sicurezza: livello minaccia, difese PvP, statistiche 7g, blocchi legali
- Influenza: categoria, bonus attivi, combo multiplier, progetti in corso

**Frontend — PvPArenaPage.jsx**:
- Nuovo tab "Mirata" accanto ad Arena e Report
- Lista bersagli con categorie attaccabili (Cinema/TV/Commerciale/Agenzie)
- Feedback attacco con effetti e difese avversarie
- Cronologia attacchi mirati

**Frontend — MajorPage.jsx (sezione Guerra)**:
- Pannello guerra attiva con: score in tempo reale, timer, colpi disponibili
- 3 tipi di colpo: Infrastrutture, Film, Fama
- Selettore durata: 24h Blitz, 48h Standard, 72h Epica
- Log eventi di guerra
- Storico guerre con badge W/L/LIVE

**event_templates.py**:
- INFRA_EVENTS: eventi per cinema, commerciale, studi, agenzie, strategico
- WAR_EVENTS: morale, propaganda, sabotaggio, leaks, trionfo
- ARENA_ATTACK_EFFECTS: effetti per categoria
- STRATEGIC_ABILITIES: pvp_operative, pvp_investigative, pvp_legal

## Backlog Prioritizzato

### P1
- [ ] Sistema "Previsioni Festival" (scommesse vincitori)

### P2
- [ ] Contest Page Mobile Layout fix (bug ricorrente 16+ segnalazioni)
- [ ] Marketplace TV/Anime rights

### P3
- [ ] Velion Mood, Chat Evolution, CinePass+Stripe, Push, Velion Levels, Eventi globali, Velion AI Memory

## File Chiave
- `/app/backend/event_templates.py` (INFRA_EVENTS, WAR_EVENTS, STRATEGIC_ABILITIES)
- `/app/backend/scheduler_tasks.py` (Auto-tick + pressure + infra events)
- `/app/backend/routes/pvp.py` (Arena mirata + abilita strategiche)
- `/app/backend/routes/major.py` (Major Warfare temporizzato)
- `/app/backend/routes/infrastructure.py` (Infra detail API: events/security/influence)
- `/app/frontend/src/pages/InfrastructurePage.jsx` (4 sub-tab dettaglio)
- `/app/frontend/src/pages/PvPArenaPage.jsx` (Tab Mirata)
- `/app/frontend/src/pages/MajorPage.jsx` (Guerra evoluta)

## Credenziali Test
- Utente: NeoMorpheus (fandrex1@gmail.com / Fandrel2776)

## 3rd Party
- Stripe, Gemini Nano Banana (Emergent LLM Key)

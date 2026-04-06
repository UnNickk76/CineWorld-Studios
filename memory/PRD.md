# CineWorld Studio's — PRD

## Problema Originale
Sistema di produzione cinematografica con pipeline completa. Esperienza utente visiva, cinematografica e immersiva.

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

**Backend — Sistema "event_pressure" (sostituisce frequenza fissa)**:
- Ogni utente ha `event_pressure` in collection `event_pressure`
- Pressione aumenta nel tempo: +2/ora senza eventi, +0.5/progetto/ora, bonus hype/qualita
- Trigger evento basato su funzione sigmoide (NO deterministico, NO garanzie)
- Dopo evento: reset parziale (legendary -85%, epic -70%, rare -50%, common -30%)
- Rarità basata su pressione: piu alta = piu chance di epic/legendary

**Rarità eventi (non prevedibili)**:
- Common: frequenti ma variabili (6-48h)
- Rare: ogni 2-5 giorni circa
- Epic: ogni 5-10 giorni circa
- Legendary: ogni 7-20 giorni (NON garantiti)
- Possibili giorni senza eventi o burst ravvicinati

**Impatto aumentato**: audience_mod fino a +2000/-400, hype_mod fino a +45, fame_mod fino a +60, revenue_mod fino a +60%

**Star Birth legata a eventi**:
- Legendary: 20-30% crea nuova star
- Epic: 10-15%
- Rare: 5%
- Common: 1-2%
- Star salvata con `star_origin_event` per tracciabilita

### Pagina EVENTI con 4 Categorie (DONE - 2026-04-06)

**Frontend — EventHistoryPage.jsx reworked**:
- 5 tab: TUTTI, LEGGENDARI (Crown), EPICI (Gem), RARI (Flame), COMUNI (CircleDot)
- Card con: titolo film/serie, descrizione, effetti, badge tipo (FILM/SERIE/ANIME), timestamp
- Bottone "Rivedi Evento" per epic/legendary → replay cinematico completo (solo visivo)
- Conteggio per categoria nei tab
- Tab scroll orizzontale mobile-first

### Sequenza Cinematica Aggiornata (DONE - 2026-04-06)

**VelionCinematicEvent.jsx reworked**:
- Black screen: 3s (epic), 5s (legendary)
- Matrix rain: minimo 8s (epic), 10s (legendary)
- Velion laterale sinistro, grande (w-32/h-40 mobile, w-40/h-48 desktop)
- Glow animato + idle animation (float + drop-shadow pulse)
- Niente fumetto — testo separato in card a destra
- Effetti mostrati con badge colorati
- Skip bloccato 4 secondi, auto-close 8s legendary, 6s epic

### Distribuzione Temporizzata Eventi (DONE - 2026-04-06)

**AutoTickNotifications.jsx reworked**:
- 1° evento cinematico: dopo 2 min dal login
- 2° evento: dopo 10 min
- 3° evento: dopo 20 min
- 4° evento: dopo 35 min
- Logout: reset completo timer
- Notifica: mostra solo ultima + badge rosso con conteggio totale
- Click badge → pagina EVENTI
- Common/rare: compressi nel contatore; epic/legendary: sempre mostrati

### Navbar "EVENTI" (DONE - 2026-04-06)
- Icona Sparkles gialla nella top navbar
- Badge rosso con conteggio non-letti
- Voce "Eventi" nel menu hamburger
- Reset contatore all'apertura pagina

## Backlog Prioritizzato

### P1
- [ ] Sistema "Previsioni Festival" (scommesse vincitori)
- [ ] Marketplace TV/Anime rights

### P2
- [ ] Contest Page Mobile Layout fix (bug ricorrente 16+ segnalazioni)

### P3
- [ ] Velion Mood, Chat Evolution, CinePass+Stripe, Push, Velion Levels, Eventi globali, Velion AI Memory

## File Chiave
- `/app/backend/event_templates.py` (Pressure system + event generation)
- `/app/backend/scheduler_tasks.py` (Auto-tick + pressure integration)
- `/app/backend/routes/economy.py` (API events/history + throttling)
- `/app/frontend/src/pages/EventHistoryPage.jsx` (Pagina EVENTI con 4 tab)
- `/app/frontend/src/components/VelionCinematicEvent.jsx` (Cinematic reworked)
- `/app/frontend/src/components/MatrixOverlay.jsx` (8s+ matrix)
- `/app/frontend/src/components/AutoTickNotifications.jsx` (Timed distribution)

## Credenziali Test
- Utente: NeoMorpheus (fandrex1@gmail.com / Fandrel2776)

## 3rd Party
- Stripe, Gemini Nano Banana (Emergent LLM Key)

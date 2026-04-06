# CineWorld Studio's — PRD

## Problema Originale
Sistema di produzione cinematografica con pipeline completa (sviluppo -> rilascio -> sala). L'obiettivo e' un'esperienza utente visiva, cinematografica e immersiva. Include "La Prima" (anteprime live), Content Template fullscreen, e Cinema Journal.

## Architettura
- **Frontend**: React + Tailwind + Shadcn/UI + Framer Motion
- **Backend**: FastAPI + MongoDB
- **Pattern UI**: Overlay su immagini template (position: absolute + %)
- **Background**: `apscheduler` per il loop dell'economia di gioco in background

## Funzionalita Completate

### La Prima (DONE)
- Dashboard section con eventi live
- CineBoard rankings (Live, Totali, Media Mista)
- LaPrimaPopup con template grafico + overlay dinamici

### Content Template (DONE - 2025-04-05)
- `ContentTemplate.jsx` fullscreen per Film/Serie/Anime

### Cinema Journal ULTRA (DONE - 2025-04-05)
- 3 tab: LIVE | NEWS | PUBBLICO

### Sistema Guest con Tutorial Guidato (DONE - 2026-04-05)
- Guest user creation, tutorial 13 step, conversione account

### DB MongoDB Bloat Fix & Ottimizzazione (DONE - 2026-04-06)
- DB da ~300MB -> 118MB (-61%)

### Pulizia Architettura server.py (DONE - 2026-04-06)
- Da 17289 -> 10069 righe (-41.8%)

### Sistema Automatico Incassi + Star + Skill (DONE - 2026-04-06)
- auto_revenue_tick ogni 10min, star discovery, AutoTickNotifications.jsx

### Soft Expansion Major - Backend + Frontend (DONE - 2026-04-06)
- 5 endpoint admin, MajorPage.jsx, Guerra, Bonus

### Sistema Eventi Completo + Cinematic UI (DONE - 2026-04-06)
- ~100 template in 4 tier, MatrixOverlay.jsx, VelionCinematicEvent.jsx

### Timing Eventi Cinematici Rallentato (DONE - 2026-04-06)
- Sequenza fadeout 800ms -> nero 500ms -> Matrix 2000-3000ms -> card 800ms delay

### Allineamento Serie TV/Anime al Sistema Auto-Tick (DONE - 2026-04-06)
- auto_revenue_tick processa sia films che tv_series collection
- Revenue, star discovery, skill progression, eventi cinematici per serie/anime

### Throttling Coda Eventi Cinematici (DONE - 2026-04-06)
- Backend: max 1 evento cinematico per 60s per utente (collection `event_throttle`)
- Backlog max 2 eventi, excess eliminati automaticamente
- Prima apertura con backlog > 1: mostrato solo il piu importante (rarita piu alta)
- Frontend semplificato: niente piu queue client-side, il backend gestisce tutto

### Cronologia Eventi con Replay (DONE - 2026-04-06)
- **Backend**: collection `event_history` per log permanente di ogni evento generato
- Campi: user_id, project_id, project_type (film/series/anime), title, rarity, description, effects, actor_name, created_at
- **API**: `GET /api/events/history?limit=50` (max 100)
- **Frontend**: `EventHistoryPage.jsx` con:
  - Card colorate per rarita (grigio/blu/viola/oro)
  - Filtri per rarita (Tutti, Leggendario, Epico, Raro, Comune)
  - Badge tipo progetto (FILM rosso, SERIE cyan, ANIME rosa)
  - Effetti mostrati (incassi, hype, fama)
  - Timestamp relativo
  - Bottone "Rivedi" per epic/legendary: replay cinematico visivo senza riapplicare effetti
- **Accesso**: icona History nella top navbar + bottone nel menu hamburger
- **Rotta**: `/event-history`

### Badge Tipo Progetto su Eventi Velion (DONE - 2026-04-06)
- Badge in alto a destra della card evento: FILM (rosso) / SERIE (cyan) / ANIME (rosa)
- Animato con delay 1.4s (appare dopo la card)
- Campo `project_type` aggiunto a tutti gli ev_record in auto_revenue_tick

## Backlog Prioritizzato

### P1 (Importante)
- [ ] Sistema "Previsioni Festival" (scommesse vincitori)
- [ ] Marketplace TV/Anime rights
- [ ] Ottimizzare /api/films/cinema-journal (N+1 query)

### P2 (Medio)
- [ ] Contest Page Mobile Layout fix (16+ segnalazioni, BUG RICORRENTE)
- [ ] Hall of Fame nel Journal
- [ ] Journal: film di altri giocatori nel LIVE

### P3 (Futuro)
- [ ] Velion Mood Indicator
- [ ] Chat Evolution
- [ ] CinePass + Stripe
- [ ] Push notifications
- [ ] Velion Levels
- [ ] Eventi globali (Major Wars espansi)
- [ ] Velion AI Memory

## File Chiave
- `/app/frontend/src/pages/EventHistoryPage.jsx` (Cronologia Eventi)
- `/app/frontend/src/components/VelionCinematicEvent.jsx` (Cinematic + badge tipo)
- `/app/frontend/src/components/MatrixOverlay.jsx` (Canvas effect)
- `/app/frontend/src/components/AutoTickNotifications.jsx` (Polling throttled)
- `/app/backend/scheduler_tasks.py` (Auto-tick economy + series + event_history)
- `/app/backend/routes/economy.py` (API events/history + throttling)
- `/app/backend/event_templates.py` (Template eventi)
- `/app/backend/server.py` (main server)

## Credenziali Test
- Utente: NeoMorpheus (fandrex1@gmail.com / Fandrel2776)

## 3rd Party Integrations
- Stripe (Pagamenti)
- Gemini Nano Banana (Generazione Logo Major e Profilo via Emergent LLM Key)

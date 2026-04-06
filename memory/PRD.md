# CineWorld Studio's — PRD

## Problema Originale
Sistema di produzione cinematografica con pipeline completa (sviluppo -> rilascio -> sala). L'obiettivo e' un'esperienza utente visiva, cinematografica e immersiva.

## Architettura
- **Frontend**: React + Tailwind + Shadcn/UI + Framer Motion
- **Backend**: FastAPI + MongoDB
- **Background**: `apscheduler` per il loop dell'economia di gioco (ogni 10min)

## Funzionalita Completate

### La Prima (DONE)
### Content Template (DONE)
### Cinema Journal ULTRA (DONE)
### Sistema Guest con Tutorial Guidato (DONE)
### DB MongoDB Bloat Fix (DONE)
### Pulizia server.py (DONE)
### Sistema Automatico Incassi + Star + Skill (DONE)
### Soft Expansion Major (DONE)
### Sistema Eventi Completo + Cinematic UI (DONE)
### Timing Eventi Cinematici Rallentato (DONE)
### Allineamento Serie TV/Anime al Sistema Auto-Tick (DONE)

### Throttling Coda Eventi Cinematici (DONE - 2026-04-06)
- Backend: max 1 evento cinematico per 60s per utente (collection `event_throttle`)
- Backlog max 2 eventi, excess eliminati automaticamente
- Prima apertura con backlog > 1: solo rarita piu alta servita

### Cronologia Eventi con Replay (DONE - 2026-04-06)
- Collection `event_history` per log permanente
- API: `GET /api/events/history?limit=50`
- Frontend: `EventHistoryPage.jsx` con card per rarita, filtri, badge tipo, effetti, replay cinematico
- Accesso: icona History nella top nav + menu hamburger
- Rotta: `/event-history`

### Badge Tipo Progetto su Eventi Velion (DONE - 2026-04-06)
- Badge FILM (rosso) / SERIE (cyan) / ANIME (rosa) in alto a destra della card

### Sistema Anti-Spam Notifiche (DONE - 2026-04-06)
- **Limite visivo**: se eventi <= 3 mostrati normalmente; se > 3 mostra solo il piu recente + badge rosso con conteggio
- **Badge contatore rosso**: sull'icona History nella top navbar, mostra numero eventi non letti (animate-pulse)
- **Click comportamento**: click su badge/icona → apre pagina /event-history
- **Reset contatore**: azzerato quando utente entra in /event-history
- **Priorita**: epic/legendary → sempre mostrati via cinematic; common/rare → compressi nel contatore
- **Anti-spam**: max 1 toast ogni 5 secondi, coda invisibile per gli altri
- **Nessun evento perso**: tutto salvato in event_history
- Sincronizzazione via sessionStorage + custom event `cw-unread-update`

## Backlog Prioritizzato

### P1
- [ ] Sistema "Previsioni Festival" (scommesse vincitori)
- [ ] Marketplace TV/Anime rights

### P2
- [ ] Contest Page Mobile Layout fix (bug ricorrente 16+ segnalazioni)
- [ ] Hall of Fame nel Journal
- [ ] Journal: film di altri giocatori nel LIVE

### P3
- [ ] Velion Mood Indicator
- [ ] Chat Evolution
- [ ] CinePass + Stripe
- [ ] Push notifications
- [ ] Velion Levels
- [ ] Eventi globali (Major Wars espansi)
- [ ] Velion AI Memory

## File Chiave
- `/app/frontend/src/pages/EventHistoryPage.jsx`
- `/app/frontend/src/components/VelionCinematicEvent.jsx`
- `/app/frontend/src/components/MatrixOverlay.jsx`
- `/app/frontend/src/components/AutoTickNotifications.jsx`
- `/app/backend/scheduler_tasks.py`
- `/app/backend/routes/economy.py`
- `/app/backend/event_templates.py`
- `/app/backend/server.py`

## Credenziali Test
- Utente: NeoMorpheus (fandrex1@gmail.com / Fandrel2776)

## 3rd Party Integrations
- Stripe (Pagamenti)
- Gemini Nano Banana (Generazione Logo via Emergent LLM Key)

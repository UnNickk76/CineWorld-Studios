# CineWorld Studio's — PRD

## Problema Originale
Sistema di produzione cinematografica con pipeline completa (sviluppo -> rilascio -> sala). Esperienza utente visiva, cinematografica e immersiva.

## Architettura
- **Frontend**: React + Tailwind + Shadcn/UI + Framer Motion
- **Backend**: FastAPI + MongoDB
- **Background**: `apscheduler` per il loop economia (ogni 10min)

## Funzionalita Completate

### Core Features (DONE precedentemente)
- La Prima, Content Template, Cinema Journal ULTRA, Sistema Guest + Tutorial
- DB Bloat Fix, Pulizia server.py, Auto Incassi + Star + Skill
- Soft Expansion Major, Sistema Eventi + Cinematic UI
- Timing Cinematici Rallentato, Serie TV/Anime nel Auto-Tick
- Throttling Coda Eventi, Cronologia Eventi + Replay, Badge Tipo Progetto
- Sistema Anti-Spam Notifiche (badge, coda 5s, compressione >3 eventi)

### Pagina Major con Navbar Interna (DONE - 2026-04-06)
- **Navbar sticky** sotto header "MAJOR" con 5 sezioni navigabili:
  - Panoramica (Home icon): card Major, bonus, sfida settimanale
  - Attivita (Zap icon): co-produzione e attivita Major
  - Membri (Users icon): lista membri + inviti (Founder/Vice)
  - Gestione (Settings icon): livello studio, ruoli, bonus reparti, eventi (solo Founder)
  - Guerra (Swords icon): dichiarazione, storico guerre
- **Scroll-spy**: IntersectionObserver aggiorna tab attivo durante scroll manuale
- **Click su tab**: scroll automatico alla sezione corrispondente
- **Mobile-first**: navbar compatta con scroll orizzontale, sempre visibile
- Sezione "Gestione" visibile solo al Founder
- View "Non sei in una Major" quando utente non ha Major (senza navbar)
- Codice ridotto da 919 a ~580 righe (dedup tab inviti con map)
- Zero modifiche ai contenuti, solo struttura e navigazione

## Backlog Prioritizzato

### P1
- [ ] Sistema "Previsioni Festival" (scommesse vincitori)
- [ ] Marketplace TV/Anime rights

### P2
- [ ] Contest Page Mobile Layout fix (bug ricorrente 16+ segnalazioni)
- [ ] Hall of Fame nel Journal
- [ ] Journal: film di altri giocatori nel LIVE

### P3
- [ ] Velion Mood Indicator, Chat Evolution, CinePass+Stripe
- [ ] Push notifications, Velion Levels, Eventi globali, Velion AI Memory

## File Chiave
- `/app/frontend/src/pages/MajorPage.jsx` (Major con navbar interna)
- `/app/frontend/src/pages/EventHistoryPage.jsx`
- `/app/frontend/src/components/VelionCinematicEvent.jsx`
- `/app/frontend/src/components/AutoTickNotifications.jsx`
- `/app/backend/scheduler_tasks.py`
- `/app/backend/routes/economy.py`
- `/app/backend/event_templates.py`

## Credenziali Test
- Utente: NeoMorpheus (fandrex1@gmail.com / Fandrel2776)

## 3rd Party Integrations
- Stripe (Pagamenti)
- Gemini Nano Banana (Logo via Emergent LLM Key)

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
- Layout: Header arcuato -> Info -> Commenti (3) -> Divisore oro -> Azioni -> Recensioni Journal -> Trama -> Trailer
- Header "IN PROGRAMMAZIONE" in badge arcuato rosso/oro
- Recensioni stile Journal (Variety=rosso/Award, Empire=blu/Crown, Hollywood R.=oro/Newspaper)
- Bottone Trailer ridotto 60%, cyan, con icone Film+Clapperboard e stelline animate
- Nessuno scroll pagina (tutto in 1 viewport)

### Cinema Journal ULTRA (DONE - 2025-04-05)
- 3 tab: LIVE | NEWS | PUBBLICO
- Tab LIVE: eventi personalizzati dai film dell'utente, rotazione ciclica 7 template
- Tab NEWS: merge cinema-news + other-news con badge categoria
- Tab PUBBLICO: 50 virtual reviews con rating stelle
- Fix performance: virtual-reviews da 30s -> 1s (batch query)

### Sistema Guest con Tutorial Guidato (DONE - 2026-04-05)
- Guest user creation con is_guest, tutorial_step (0-6), tutorial_completed
- Endpoint tutorial-step, tutorial-skip, convert account
- Componente GuestTutorial.jsx con Velion assistente (7 step guidati)
- Free speedups (3 gratis) per il primo film del guest
- Modale conversione account a fine tutorial
- Timer conversione 20min attivo SOLO dopo completamento tutorial
- Tutorial esteso a 13 step (0-12)

### Content Template Series (DONE - 2025-04-05)
- Template series con background blue/silver theme
- Bottoni trasparenti (aree cliccabili)
- Reviews: IGN, COLLIDER, ENTERTAINMENT W.

### DB MongoDB Bloat Fix & Ottimizzazione (DONE - 2026-04-06)
- Root cause: discoverer_avatar (base64 3MB) in cinema_news + poster_url base64
- DB da ~300MB -> 118MB dataSize (-61%)

### Pulizia Architettura server.py (DONE - 2026-04-06)
- Rimosse ~7200 righe di codice morto/commentato
- Da 17289 -> 10069 righe (-41.8%)
- Zero regressioni

### Sistema Automatico Incassi + Star + Skill (DONE - 2026-04-06)
- Rimosso bottone "INCASSA ORA" e card incassi da Dashboard
- Creato auto_revenue_tick in scheduler_tasks.py (ogni 10min)
- Star discovery bilanciata (0.5-1% max 1 star a tick)
- AutoTickNotifications.jsx con polling + toast animati

### Soft Expansion Major - Backend + Frontend (DONE - 2026-04-06)
- **Backend**: 5 endpoint admin in routes/major.py
- **Frontend** MajorPage.jsx aggiornato con Sezione Admin, Guerra, Bonus
- Documenti futuri: /app/features_future/ con 4 file .md

### Collegamento Eventi Cinematici a Gameplay Reale (DONE - 2026-04-06)
- Trigger automatico per film IN SALA + COMING SOON (solo rare+)
- Cooldown 12h per titolo, probabilita 30% base + modificatore qualita
- Effetti applicati al DB reale: revenue +/- %, hype_score +/- %, fame +/- %
- Anti-spam frontend: 20s tra cinematici, coda eventi

### Sistema Eventi Completo + Cinematic UI (DONE - 2026-04-06)
- **Backend**: `event_templates.py` con ~100 template in 4 tier
- **Frontend**: MatrixOverlay.jsx, VelionCinematicEvent.jsx, AutoTickNotifications.jsx
- Common/rare: toast notification standard; Epic/Legendary: animazione cinematica completa

### Dashboard Tour Velion (DONE - 2026-04-06)
- DashboardTour.jsx: 14 step con frecce animate

### Tutorial Riutilizzabile (DONE - 2026-04-06)
- tutorialSteps.js (6 step) + TutorialModal.jsx

### Timing Eventi Cinematici Rallentato (DONE - 2026-04-06)
- Sequenza: fadeout 800ms -> schermo nero 500ms -> Matrix rain (min 2000ms epic, 3000ms legendary) -> card evento (800ms delay)
- Durata totale minima ~4-5 secondi
- Skip bloccato per 2.5s, coda eventi con 3s gap
- Auto-close: legendary 8s, epic 6s, common 3.5s

### Allineamento Serie TV/Anime al Sistema Auto-Tick (DONE - 2026-04-06)
- `auto_revenue_tick()` ora processa sia `films` che `tv_series` collection
- Serie TV/Anime con status `completed`/`released` ricevono: revenue passiva, star discovery, skill progression, eventi cinematici
- Revenue basata su qualita, audience rating, episode count con decay temporale
- Hype e star flags aggiornati nella collection corretta (`tv_series`)
- Frontend aggiornato per mostrare conteggio separato film/serie nei toast revenue
- Testato: utente con 49 film + 6 serie riceve revenue combinata correttamente

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
- `/app/frontend/src/pages/MajorPage.jsx`
- `/app/backend/routes/major.py`
- `/app/backend/scheduler_tasks.py` (Auto-tick economy + series)
- `/app/frontend/src/components/ContentTemplate.jsx`
- `/app/frontend/src/components/VelionCinematicEvent.jsx`
- `/app/frontend/src/components/MatrixOverlay.jsx`
- `/app/frontend/src/components/AutoTickNotifications.jsx`
- `/app/backend/event_templates.py`
- `/app/backend/server.py`

## Credenziali Test
- Utente: NeoMorpheus (fandrex1@gmail.com / Fandrel2776)

## 3rd Party Integrations
- Stripe (Pagamenti)
- Gemini Nano Banana (Generazione Logo Major e Profilo via Emergent LLM Key)

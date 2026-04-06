# CineWorld Studio's — PRD

## Problema Originale
Sistema di produzione cinematografica con pipeline completa (sviluppo → rilascio → sala). L'obiettivo e' un'esperienza utente visiva, cinematografica e immersiva. Include "La Prima" (anteprime live), Content Template fullscreen, e Cinema Journal.

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
- **Backend**: 5 endpoint admin in routes/major.py:
  - POST /api/major/set-level (studio/mini_major/major)
  - POST /api/major/set-role (manager/member, founder only)
  - POST /api/major/set-bonuses (marketing/casting/production 0-25)
  - POST /api/major/trigger-event (random event, 6h cooldown)
  - POST /api/major/war/calculate (score-based, 24h cooldown)
  - GET /api/major/wars (storico)
  - GET /api/major/all (senza logo base64, fix performance 2.6MB->85 bytes)
- **Frontend** MajorPage.jsx aggiornato:
  - Sezione Admin (solo founder): Livello Studio, Ruoli Membri, Bonus Reparti (slider 0-25), Evento Major (trigger + display attivo)
  - Sezione Guerra: Dichiara Guerra (dropdown avversario + bottone), Storico Guerre (win/loss)
  - Caricamento dati guerra non-bloccante (fix page loading stuck)
- **Documenti futuri**: /app/features_future/ con 4 file .md (contracts, franchise, streaming, acquisitions)

### Tutorial Riutilizzabile (DONE - 2026-04-06)
- Creato `frontend/src/data/tutorialSteps.js` (6 step: Benvenuto, Produzione, Coming Soon, Rilascio, Eventi, Crescita)
- Creato `frontend/src/components/TutorialModal.jsx` (componente generico leggero)
- Integrato in 3 punti: Login ("Come si gioca?"), Top Nav (icona HelpCircle), bottone "?" vicino Velion, menu hamburger
- Zero dipendenze aggiunte, zero modifiche backend, mobile-first

## Backlog Prioritizzato

### P0 (Critico)
- [x] Tutti i P0 precedenti completati (vedi sopra)
- [x] Soft Expansion Major Backend + Frontend (2026-04-06)

### P1 (Importante)
- [ ] Azioni Proprietario Serie TV (verificare integrazione con auto-tick)
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
- `/app/frontend/src/pages/MajorPage.jsx` (UI Major + Admin + Guerra)
- `/app/backend/routes/major.py` (Endpoint Major completi)
- `/app/backend/scheduler_tasks.py` (Auto-tick economy)
- `/app/frontend/src/components/ContentTemplate.jsx`
- `/app/frontend/src/pages/CinemaJournal.jsx`
- `/app/frontend/src/components/GuestTutorial.jsx`
- `/app/backend/server.py` (main server)

## Credenziali Test
- Utente: NeoMorpheus (fandrex1@gmail.com / Fandrel2776)

## 3rd Party Integrations
- Stripe (Pagamenti)
- Gemini Nano Banana (Generazione Logo Major e Profilo via Emergent LLM Key)

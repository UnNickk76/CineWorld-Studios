# CineWorld Studio's — PRD

## Problema Originale
Sistema di produzione cinematografica con pipeline completa (sviluppo → rilascio → sala). L'obiettivo è un'esperienza utente visiva, cinematografica e immersiva. Include "La Prima" (anteprime live), Content Template fullscreen, e Cinema Journal.

## Architettura
- **Frontend**: React + Tailwind + Shadcn/UI + Framer Motion
- **Backend**: FastAPI + MongoDB
- **Pattern UI**: Overlay su immagini template (position: absolute + %)

## Funzionalita Completate

### La Prima (DONE)
- Dashboard section con eventi live
- CineBoard rankings (Live, Totali, Media Mista)
- LaPrimaPopup con template grafico + overlay dinamici

### Content Template (DONE — 2025-04-05)
- `ContentTemplate.jsx` fullscreen per Film/Serie/Anime
- Layout: Header arcuato → Info → Commenti (3) → Divisore oro → Azioni → Recensioni Journal → Trama → Trailer
- Header "IN PROGRAMMAZIONE" in badge arcuato rosso/oro
- Recensioni stile Journal (Variety=rosso/Award, Empire=blu/Crown, Hollywood R.=oro/Newspaper)
- Bottone Trailer ridotto 60%, cyan, con icone Film+Clapperboard e stelline animate
- Nessuno scroll pagina (tutto in 1 viewport)

### Cinema Journal ULTRA (DONE — 2025-04-05)
- 3 tab: LIVE | NEWS | PUBBLICO
- Tab LIVE: eventi personalizzati dai film dell'utente, rotazione ciclica 7 template
- Tab NEWS: merge cinema-news + other-news con badge categoria
- Tab PUBBLICO: 50 virtual reviews con rating stelle
- Fix performance: virtual-reviews da 30s → 1s (batch query)
- Rimossa chiamata cinema-journal (troppo lenta)

### Sistema Guest con Tutorial Guidato (DONE — 2026-04-05)
- Guest user creation con is_guest, tutorial_step (0-6), tutorial_completed
- Endpoint tutorial-step, tutorial-skip, convert account
- Componente GuestTutorial.jsx con Velion assistente (7 step guidati)
- Free speedups (3 gratis) per il primo film del guest
- Modale conversione account a fine tutorial
- Timer conversione 20min attivo SOLO dopo completamento tutorial
- Fix popup Cast & Crew: mostra il ruolo (Protagonista, Supporto, Co-Protagonista...) invece del numero progressivo
- Gestito sia film (`role_in_film`) che serie (`role`) dato che il cast arriva come array piatto

### Content Template Series (DONE — 2025-04-05)
- Template series con background `series-template.jpg` (blue/silver theme)
- Bottoni INCASSA ORA, CREA STELLA, BOOST CREW trasparenti (aree cliccabili)
- Bottone TRAILER trasparente
- Reviews: IGN, COLLIDER, ENTERTAINMENT W.
- Fix `screenplay` oggetto {text, generated_at} normalizzato
- Fix commenti series {text, sentiment, rating} normalizzati
- Status "completed" mappato come "IN PROGRAMMAZIONE"

## Backlog Prioritizzato

### P0 (Critico)
- [x] Content Template layout fix
- [x] Cinema Journal ULTRA light
- [x] Fix navigazione Serie TV dalla Dashboard → ora apre `/series/:id` (2026-04-05)
- [x] Verifica sblocco "Le Mie TV!" → confermato funzionante (API e UI OK) (2026-04-05)
- [x] Fix Coming Soon timer: transizioni forward-only, no reset a idea/proposed (2026-04-05)
- [x] Fix UI Tutorial Guest Mobile: hooks error + freccia fuori viewport + z-index Velion (2026-04-05)
- [x] Fix "Inizia ora" → Guest Login diretto, target cliccabili nel tutorial, Velion come immagine (2026-04-05)
- [x] Velion grande e prominente nel tutorial: posizione dinamica per step, animazioni diverse, layout speech+character come produzione (2026-04-05)
- [x] Fix speech bubble blocca dropdown: step con target → Velion grande in alto + bubble a lato, dropdown libero. Form conversione con Velion animato (2026-04-05)
- [x] Popup "Dona Ora": compare 2h dopo primo login giornaliero, max 1 volta ogni 24h solari, z-index 150 sopra tutorial (2026-04-05)

### P1 (Importante)
- [ ] Modularizzazione server.py (17k+ righe)
- [ ] Sistema "Previsioni Festival" (scommesse vincitori)
- [ ] Marketplace TV/Anime rights
- [ ] Ottimizzare /api/films/cinema-journal (N+1 query)

### P2 (Medio)
- [ ] Contest Page Mobile Layout fix (16+ segnalazioni)
- [ ] Hall of Fame nel Journal (quando discovered-stars ha dati)
- [ ] Journal: film di altri giocatori nel LIVE (multi-utente)

### P3 (Futuro)
- [ ] Velion Mood Indicator
- [ ] Chat Evolution
- [ ] CinePass + Stripe
- [ ] Push notifications
- [ ] Velion Levels
- [ ] Eventi globali
- [ ] Guerre tra Major
- [ ] Velion AI Memory

## File Chiave
- `/app/frontend/src/components/ContentTemplate.jsx`
- `/app/frontend/src/styles/content-template.css`
- `/app/frontend/src/pages/CinemaJournal.jsx`
- `/app/frontend/src/pages/FilmDetail.jsx`
- `/app/frontend/src/pages/SeriesDetail.jsx`
- `/app/frontend/src/components/LaPrimaPopup.jsx`
- `/app/backend/routes/dashboard.py` (virtual-reviews fix)
- `/app/backend/server.py` (monolite 17k+)

## Credenziali Test
- Utente: NeoMorpheus (fandrex1@gmail.com / Fandrel2776)

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
- [x] DB MongoDB Bloat Fix & Ottimizzazione (2026-04-06):
  - Root cause: `discoverer_avatar` (base64 3MB) in cinema_news + `poster_url` base64 in infrastructure.films_showing
  - Fix codice: rimosso avatar base64 da cinema_news insert (server.py), sanitizzato poster_url in infrastructure.py (2 punti), protetto suggestions/bug_reports, aggiunto persist_base64_avatar in auth.py PUT avatar
  - Pulizia dati: 80 cinema_news puliti, infrastructure.films_showing pulita, 71 guest inattivi rimossi, 6 infra duplicate rimosse, 8 film_drafts puliti
  - Risultato: DB da ~300MB → 118MB dataSize (-61%)
- [x] Fix "LE MIE TV! sparisce" (2026-04-06): fetch TV stations era annidato nel try/catch di `/catchup/process` — se catchup falliva, TV mai caricate. Separati tutti i fetch in blocchi try/catch indipendenti in Dashboard.jsx
- [x] Fix UI Tutorial Guest Mobile: hooks error + freccia fuori viewport + z-index Velion (2026-04-05)
- [x] Fix "Inizia ora" → Guest Login diretto, target cliccabili nel tutorial, Velion come immagine (2026-04-05)
- [x] Velion grande e prominente nel tutorial: posizione dinamica per step, animazioni diverse, layout speech+character come produzione (2026-04-05)
- [x] Fix speech bubble blocca dropdown: step con target → Velion grande in alto + bubble a lato, dropdown libero. Form conversione con Velion animato (2026-04-05)
- [x] Popup "Dona Ora": compare 2h dopo primo login giornaliero, max 1 volta ogni 24h solari, z-index 150 sopra tutorial (2026-04-05)
- [x] Tutorial Guest completo 11 step: guida passo-passo dalla Dashboard al rilascio film con auto-advance, Velion grande in posizione variabile, form mai bloccato (2026-04-05)
- [x] Step finale celebrativo (Step 10): Velion grande con anello dorato pulsante, particelle scintillanti animate, titolo "Congratulazioni!" gradient dorato, messaggio completo multilinea (Serie TV, Arena, Chat, etc.), "CineWorld Studio's!!!", bottone "Continua l'avventura!" → layout ottimizzato mobile con whitespace-pre-line (2026-04-05)

- [x] Bottone "Registrati" fisso per utenti guest: badge rosso CTA con pulse, posizionato sopra bottom nav, apre modale conversione esistente. Tooltip prima volta "Salva i tuoi progressi". Nascosto per utenti registrati (2026-04-05)
- [x] Conversione progetti guest in marketplace: progetti con status>=production e quality>=40 convertiti (owner=null, is_market=True, production_house="Studio Indipendente", prezzo auto=500k*(1+quality/100)). Resto eliminato. Sicurezza: solo guest (2026-04-05)
- [x] Modale conversione guest ad alta conversione: due fasi — Phase 1 "Non perdere il tuo studio" con stats dinamici (film creati, CW$ guadagnati), loss aversion ("Se esci ora, perderai tutto"), CTA giallo/oro con pulse; Phase 2 form registrazione. Animazioni fade-in + haptic + scale. Non bloccante (2026-04-05)
- [x] Fix tutorial step 1: freccia ora punta su "Film" nel dropdown PRODUCI (target: prod-menu-film, fallback: bottom-nav-produci) (2026-04-05)
- [x] Nuovo step 7 "Apri il tuo film!": guida utente a cliccare sul film nel carousel dopo creazione proposta. Auto-advance 6→7 rileva form chiuso + film nel carousel (2026-04-05)
- [x] Tutorial esteso da 12 a 13 step (0-12): backend TUTORIAL_STEPS aggiornato, threshold completamento ≥12 (2026-04-05)
- [x] Fix target illuminazione: Step 3→release-mode-selector, Step 5→pre-screenplay-input, Steps 8-10→selettori doppi proposte+cinematica (2026-04-05)
- [x] Speedup nella vista cinematica: aggiunta velocizzazione al HypeStep in FilmPopup.jsx con GRATIS per guest (2026-04-05)

### P1 (Importante)
- [ ] Endpoint backend Azioni Proprietario Serie TV (Incassa, Crea Stella, Boost)
- [x] Modularizzazione server.py — Pulizia conservativa (2026-04-06): rimossi 7201 righe di codice [MOVED] commentato, fixati 3 import mancanti (CHAT_BOTS, parse_date_with_timezone, RELEASE_NOTES dead code). Da 17289 → 10069 righe (-41.8%). Zero regressioni, 12/12 endpoint critici verificati.
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
- `/app/backend/routes/dashboard.py` (virtual-reviews fix, cinema-news esclude discoverer_avatar)
- `/app/frontend/src/components/GuestTutorial.jsx` (Tutorial Guest 12 step + finale celebrativo)
- `/app/backend/routes/auth.py` (TUTORIAL_STEPS 0-11, tutorial-step, tutorial-skip, convert, persist_base64_avatar)
- `/app/backend/routes/infrastructure.py` (films_showing sanitizzato da base64)
- `/app/backend/server.py` (cinema_news insert senza discoverer_avatar)

## Credenziali Test
- Utente: NeoMorpheus (fandrex1@gmail.com / Fandrel2776)

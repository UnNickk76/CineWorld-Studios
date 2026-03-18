# CineWorld Studio's - PRD

## Architettura
- Frontend: React + Tailwind + Shadcn/UI
- Backend: FastAPI + MongoDB
- Integrazioni: OpenAI GPT-4o, GPT-Image-1, Emergent LLM Key

## Funzionalità Completate (16 Mar 2026)

### Sistema Distribuzione Film (FASE 1)
- Film dopo creazione -> `pending_release` -> Dashboard SEMPRE visibile (max 6)
- Popup rilascio: Nazionale/Continentale/Mondiale
- Pulsante "Porta in Studio di Produzione" (se possiede studio)
- Pulsante rapido "IN ATTESA" nella griglia con pallino rosso

### Studio di Produzione (FASE 2)
- 3 pannelli: Pre-Produzione, Post-Produzione, Agenzia Casting
- Bug fix: `owner_id` vs `user_id` (5 query corrette)

### Agenzia Casting Migliorata
- Nomi reali per nazionalità (fix bug "Unknown")
- Click talento → popup "Usa Subito" / "Invia a Scuola"
- Cast filtrato per livello/fama del giocatore

### Integrazione Studio nel Film Wizard (FASE 3)
- Bozze Sceneggiatura AI con CinePass gratis + bonus qualità

### Sistema Riprese Film (NUOVO - 16 Mar 2026)
- Flusso: `pending_release` → `shooting` (1-10 giorni) → `ready_to_release` → `in_theaters`
- Rilascio diretto: -30% costo, qualità max 5.8 IMDb, incassi -40%
- Bonus riprese: curva logaritmica 10%-40% (1-10 giorni)
- Eventi casuali giornalieri: Giornata Perfetta (+2%), Ritardo Meteo (-1%), Improvvisazione Geniale (+3%), ecc.
- Chiusura anticipata: giorni_rimanenti × 2 CinePass
- Costo riprese: budget × 15% × giorni
- Dashboard: pulsante "Ciak, si Gira!" con badge + sezione progresso con mini locandine, barre, eventi
- Scheduler: processo ogni ora (1 giorno simulato per ora)

### Locandine Classiche con Sfondi per Genere (NUOVO - 16 Mar 2026)
- 8 generi con sfondi fotografici: Thriller, Romance, Comedy, Fantasy, Adventure, Noir, Horror, Drama
- Testo in sovraimpressione: titolo film (grande) + "un film [casa di produzione]" (piccolo, dorato)
- Altri generi: sistema gradient esistente con testo overlay
- production_house_name auto-iniettato dall'utente autenticato

### Immagini Regista per Ciak, si Gira! (NUOVO - 16 Mar 2026)
- Due foto regista (maschio/femmina) mostrate random nel dialog di conferma riprese
- Immagini in /app/frontend/public/images/shooting/

### Popup Donazione (NUOVO - 16 Mar 2026)
- Mostrato solo al primo login nelle 24h (localStorage 'donatePopupLastShown')

### Badge Generi Cliccabili (NUOVO - 16 Mar 2026)
- Nei profili giocatori, cliccando un genere filtra i film di quella categoria
- Formato "Film recenti": locandina, titolo, genere, qualità, incassi

### Refactoring Backend (16 Mar 2026)
- `server.py`: ridotto da 15,557 a 11,608 righe (-25%)
- `server_utils.py` (NUOVO): costanti condivise + helper functions (1,195 righe)
- `routes/challenges.py` (NUOVO): sistema sfide (991 righe)
- `routes/festivals.py` (NUOVO): festival ufficiali + personalizzati (2,039 righe)

### Tutorial (16 step) + Note di Sistema (3 note)

## Key DB Schema
- infrastructure: `owner_id` (NON user_id)
- films.status: pending_release | shooting | ready_to_release | in_theaters
- films.shooting_days, shooting_days_completed, shooting_events, shooting_bonus
- casting_hires: traccia ingaggi settimanali
- studio_drafts: bozze sceneggiatura

### Fix Stabilità Sessione (17 Mar 2026)
- Auto-login ora cancella il token SOLO su errore 401 (non su errori di rete/timeout/5xx)
- Interceptor 401 usa logout debounced (3 secondi) con verifica `/auth/me` prima di sloggare
- Gestione richieste parallele: qualsiasi risposta positiva cancella il logout in attesa
- File modificato: `frontend/src/contexts/index.jsx`
- Test: 11/11 passati (navigazione, reload, navigazione rapida)

### Acting School Potenziata (17 Mar 2026)
- Nuova sezione "Studenti dall'Agenzia Casting" nella Scuola di Recitazione
- Capacità legata al livello scuola (formula: 2 + livello)
- Attributo 'età' aggiunto a tutti gli attori (casting agency recruits + students)
- Skill migliorano nel tempo in base al potenziale nascosto (0.6-1.0)
- Costo giornaliero formazione: $30K + livello × $5K (primo giorno gratuito)
- Pulsante "Diploma" dopo 24 ore di formazione
- Messaggio "Potenziale massimo raggiunto" quando tutte le skill sono al cap
- Pulsanti: Diploma, Paga formazione, Rimuovi
- Collection: `casting_school_students`
- Endpoint: GET /acting-school/casting-students, POST /graduate/{id}, POST /pay-training/{id}, POST /dismiss/{id}
- Test: 8/8 backend + UI completo verificato

### Nuovo Sistema Film Pipeline - Fase 1 (17 Mar 2026)
- **6 sottomenu a icone** fissi in alto con badge conteggio + popup info
- **Step 1 (Creazione)**: Titolo + genere + sottogenere + pre-sceneggiatura (100-500 char) + location
- **Step 2 (Proposte)**: Pre-valutazione IMDb basata su genere, sinossi, location, fattore nascosto + tasti Scarta/Prosegui
- **Step 3 (Casting)**: Agenti propongono cast con timer (10-60min), speed-up a crediti, selezione per ruolo
- **Backend**: `/app/backend/routes/film_pipeline.py` con 9 endpoint, collection `film_projects`
- **Frontend**: `/app/frontend/src/pages/FilmPipeline.jsx` con 3 tab funzionali + 3 placeholder (Fase 2)
- **Limiti**: Max film simultanei basato su livello (Lv1=2, Lv5=4, Lv10=6)
- **Costi**: 1-3 CinePass per step + costi in denaro variabili
- **Marketplace**: Film scartati disponibili per altri giocatori a -30%
- Rotta: `/create-film`
- Test: 12/13 backend + tutti UI verificati

### Bug Fix Batch (17 Mar 2026)
1. **Casting Students nella Infrastruttura**: Sezione visibile sia in /acting-school che nel dettaglio infrastruttura
2. **Blocco acquisto duplicato**: Scuola e Studio di Produzione ora mostrano "Già posseduto" se già acquistati, backend blocca con errore
3. **Box Office $NaN fix**: Corretto rendering separando box_office da budget_guess tramite `challenge_type`, aggiunto `film_genre` al posto di `genre`
4. **Trivia shuffle**: Risposte ora mescolate, la corretta non è più sempre la prima
5. **Cast Match skill hints**: Aggiunte skill rilevanti al genere per ogni attore + attori shufflati
6. **Box Office film query**: Aggiunto status `in_theaters` alla query
- Test: 100% backend + frontend verificato

### Produzione Avanzata (17 Mar 2026)
- Co-Protagonista aggiunto come 5o ruolo attore (peso qualita: 1.2, crescita: 1.0)
- ROLE_VALUES: Protagonista(1.5), Co-Protagonista(1.2), Antagonista(1.3), Supporto(0.7), Cameo(0.3)
- Comparse: slider 50-1000, sweet spot per genere, bonus/penalita automatico
- CGI: 6-7 pacchetti per genere (horror, sci_fi, action, fantasy, adventure, war) + default
- VFX: 4 pacchetti per genere + default, costi solo denaro
- Calcolo qualita: ora include role_weighted, cgi_bonus, vfx_bonus, extras_bonus, soundtrack
- Test: 100% (9/9 backend, 8/8 frontend - iteration 78)

### Feature Batch (17 Mar 2026)
- Cast cliccabile/espandibile con skill bars colorate (verde/giallo/rosso)
- Dropdown ruolo attore: Protagonista/Antagonista/Supporto/Cameo (obbligatorio)
- Punteggio Colonna Sonora: skill compositore influenzano qualita finale (+0-8 punti)
- Pre-Ingaggio RIMOSSO completamente (nav, route, dashboard card)
- Sceneggiature: rimossa opzione "Solo Sceneggiatura", solo "Pacchetto Completo" con sconto 40-50%
- Test: 100% (12/12 backend, 8/8 frontend - iteration 77)

### Bug Fix Batch - Casting/Dashboard/Studio (17 Mar 2026)

### Fase 3 Pipeline Completata (17 Mar 2026)
- **Sottogeneri**: da Select dropdown a badge cliccabili (max 3) con contatore
- **Location**: raggruppate per categoria (Studi, Citta, Natura, Storici) con filtri e selezione multipla
- **Marketplace Film**: nuova pagina /marketplace con ricerca, griglia film, dettagli + acquisto
- **Fattori Nascosti Avanzati**: chimica cast, trend genere, critica, tempismo mercato, eventi virali/scandali
- **Speed-Up Ciak**: gia implementato (50%, 80%, istantaneo)
- Backend: subgenres/locations come array, bonus multi-sottogenere (+0.3) e multi-location (+0.2/loc)
- Test: 100% (8/8 backend, tutti frontend)

### Mercato Film (17 Mar 2026)
- Nuova pagina Marketplace sostituisce Bozze (obsolete con la pipeline)
- Backend già implementato: scarta film → vendita al 70% → acquisto da altri giocatori
- Fix bug: aggiunto `status_before_discard` nel discard endpoint
- Frontend: griglia film con poster, genere, fase, prezzo, dialog dettagli + acquisto
- Ricerca per titolo/genere, notifica al venditore
- Nav aggiornata: "Bozze" → "Mercato" (icona Store)
- **"Produci!"** sostituisce "Crea Film" in nav bar (top + card dashboard) con icona Clapperboard
- Menu a tendina (Select dropdown) per genere e sottogenere nella pipeline (sostituiti bottoni griglia)
- Card "IN ATTESA" rimossa dalla dashboard (funzionalità inclusa nella pipeline)
- Card "CIAK!" aggiornata: naviga a `/create-film?tab=shooting` (link diretto al tab riprese)
- Vecchio FilmWizard (`/create`) ora reindirizza a FilmPipeline
- Tutti i link `navigate('/create')` aggiornati a `navigate('/create-film')`
- Supporto query param `?tab=` nella FilmPipeline per navigazione diretta ai tab
- Test: 100% frontend verificato (9/9 test)

### Casting Avanzato v2 (17 Mar 2026 - msg #507)
- **Dettagli Attori Enrichiti**: genere, eta, nazionalita con icona Globe, fame label, trend crescita, badge "Collaboratore"
- **Casting Dinamico**: logica fame-based
- **Proposte Raddoppiate**: max attori da 8 a 16
- **Bottom Nav Mobile**: "Produci!" button allargato, aggiunto "Mercato"
- Backend: `generate_cast_proposals` riscritto
- Frontend: componenti GenderIcon, FameLabel, GrowthTrend, PersonMeta
- Test: 100% backend + frontend (iteration 79)

### Sistema Equipment e Sponsor (18 Mar 2026)
- **Equipment**: ~10 pacchetti attrezzature (base/pro/premium) selezionabili durante il Casting. Impattano il punteggio finale del film. Popup con checkbox, costi e descrizioni. Backend: GET /api/film-pipeline/{id}/equipment-options, POST /api/film-pipeline/{id}/select-equipment
- **Sponsor**: ~20 proposte sponsor selezionabili in Pre-Produzione (da 1 a max 6, basato su fama). Offrono denaro immediato ma prendono % sugli incassi orari. La fama sponsor aumenta l'affluenza al cinema (NON il punteggio IMDb). Nomi sponsor visibili nel popup di rilascio film. Backend: GET /api/film-pipeline/{id}/sponsor-offers, POST /api/film-pipeline/{id}/select-sponsors
- Frontend: Popup sponsor completo con selezione multipla, riepilogo costi/revenue share/affluenza, summary dopo selezione
- Test: 100% backend + frontend (iteration 80)

### CineBoard Leaderboard Overhaul (18 Mar 2026)
- Rimossa tab "Hall of Fame", sostituite con "Giornaliera" e "Settimanale"
- 4 tab: Giornaliera, Settimanale, In Sala (Top 50), Affluenze
- Backend: GET /api/cineboard/daily (ordinato per daily_revenue), GET /api/cineboard/weekly (ordinato per weekly_revenue)
- UI: Revenue giornaliera/settimanale mostrata nel formato "$XM oggi" / "$XM sett."
- **Barre trend relative al rilascio (18 Mar 2026):**
  - Daily: 6 barre verdi per blocchi 4 ore dal rilascio (0-4h, 4-8h, 8-12h, 12-16h, 16-20h, 20-24h)
  - Weekly: 7 barre viola per i primi 7 giorni dal rilascio (G1-G7)
  - Pattern decadimento basato su qualità film (90%+: 0.92, 80%+: 0.85, 65%+: 0.78, <65: 0.70)
  - Backend: calcolo trend basato su opening_revenue × decay^day
  - Frontend: barre con altezza in pixel proporzionale, tooltip con revenue, labels sotto ogni barra
- Test: 100% backend (17/17) + frontend verificato

### Admin Tools (18 Mar 2026)
- **POST /api/admin/add-money**: Aggiunge/rimuove denaro a un utente (solo admin). Params: `{nickname, amount}`
- **POST /api/admin/repair-films**: Ripara film incompleti (poster, recensioni, IMDb, box_office). Params opzionali: `{nickname}` per filtrare per utente
- **Release Notes aggiornate**: RELEASE_NOTES portate alla v0.136 con tutte le feature recenti (Equipment, Sponsor, CineBoard, Poster, Casting v2, Mercato, Pipeline)
- **System Notes auto-init**: Se il DB deploy non ha system notes, vengono create automaticamente 10 note di default al primo avvio

### Decadimento Esponenziale Affluenza & Revenue (18 Mar 2026)
- **Affluenza**: Film nuovi hanno boost iniziale 2.5x (giorno 1), 1.8x (giorni 2-3), 1.2x (prima settimana)
- **Decadimento basato su qualita**: Capolavori (90+): -1.5%/giorno, Eccellenti (80-89): -4%/giorno, Buoni (65-79): -7%/giorno, Mediocri (<65): -12%/giorno
- **IMDb boost**: Film con IMDb alto ricevono più affluenza iniziale (moltiplicatore 0.5-3.0x)
- **Revenue decadimento**: Stesso schema di decadimento per incassi box office
- **Daily revenues tracciati** ogni 10 minuti per classifica giornaliera
- Fix: $40M migrazione usa campo `funds` (non `money`)
- Fix: Rimborso automatico sceneggiature orfane
- Fix: Film con status errato convertiti a `in_theaters`

## Task Prossimi
- **(P1)** Nuova Infrastruttura: Agenzia di Casting (uso da altri giocatori a pagamento)
- **(P2)** Layout mobile pagina Contest
- **(P1)** Sistema ruoli Admin (RBAC)

## Backlog
- Ulteriore refactoring server.py (ancora ~15K righe - estrarre film routes, admin, AI, users)
- Refactoring FilmPipeline.jsx (>1200 righe - decomposizione in sub-components)
- Refactoring Dashboard.jsx
- Runware, Stripe, PWA, Tutorial popup

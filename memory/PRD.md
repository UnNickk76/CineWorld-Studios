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

### Bug Fix Batch (17 Mar 2026)
1. **Casting Students nella Infrastruttura**: Sezione visibile sia in /acting-school che nel dettaglio infrastruttura
2. **Blocco acquisto duplicato**: Scuola e Studio di Produzione ora mostrano "Già posseduto" se già acquistati, backend blocca con errore
3. **Box Office $NaN fix**: Corretto rendering separando box_office da budget_guess tramite `challenge_type`, aggiunto `film_genre` al posto di `genre`
4. **Trivia shuffle**: Risposte ora mescolate, la corretta non è più sempre la prima
5. **Cast Match skill hints**: Aggiunte skill rilevanti al genere per ogni attore + attori shufflati
6. **Box Office film query**: Aggiunto status `in_theaters` alla query
- Test: 100% backend + frontend verificato

## Task Prossimi
- Acting School Potenziata (età attori, sezione dedicata, miglioramento skill, diploma)
- Sistema ruoli Admin (RBAC)
- Layout mobile pagina Contest

## Backlog
- Ulteriore refactoring server.py (ancora 11,608 righe - estrarre film routes, admin, AI, users)
- Runware, Stripe, PWA, Tutorial popup

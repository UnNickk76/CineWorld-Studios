# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica. Proprietà di **Andreola Fabio**.

## Versione Attuale: v0.065

## Funzionalità Implementate (Ultime)

### v0.065 - Bonus Visione Cerimonie - 10/03/2026 (COMPLETATO)
- **Bonus Entrate per Visione Live**:
  - Fino a +10% bonus sulle entrate guardando le cerimonie
  - 6 minuti di visione = +1% bonus
  - 60 minuti totali = +10% (massimo)
  - Tracking tempo di visione in tempo reale
  - Indicatore bonus visibile durante la live
- **Notifiche Motivazionali**:
  - Messaggi che ricordano del bonus ("Guarda in diretta per +10% bonus!")
  - Notifiche aggiornate in tutte le lingue

### v0.064 - Festival System Update & Cinema Revenue - 10/03/2026 (COMPLETATO)
- **Date Festival Aggiornate**:
  - Golden Stars Awards: Giorno 10 del mese
  - Spotlight Awards: Giorno 20 del mese
  - Cinema Excellence Awards: Giorno 30 (28 per febbraio)
- **Cerimonia Live con Chat Pubblica**:
  - Nuovo modale per visualizzare la cerimonia in diretta
  - Chat pubblica in tempo reale per commentare
  - Sistema di "Papabili" vincitori con probabilità calcolate
  - Indicatore viewers count
  - Rate limiting sulla chat (1 messaggio ogni 5 secondi)
- **Audio TTS per Annunci**:
  - Integrazione OpenAI Text-to-Speech per annunci vincitori
  - Voci diverse per lingua (onyx EN, nova IT, coral ES, shimmer FR, echo DE)
  - Pulsante "Annuncia" con riproduzione audio automatica
  - Indicatore visivo "Audio in riproduzione"
- **Sottotitoli Sincronizzati**:
  - Overlay full-screen con testo dell'annuncio
  - Animazioni entrance con Framer Motion
  - Nome categoria evidenziato in giallo
  - Badge vincitore con trofei animati
  - Wave audio animata durante riproduzione
  - Sottotitoli nella lingua scelta dal player
- **Effetti Visivi Extra**:
  - Confetti dorati da canvas-confetti (burst laterali + centrale)
  - Spotlight animato con raggi di luce
  - Particelle dorate fluttuanti
  - Animazione pulse sui vincitori
- **Sistema Fusi Orari**:
  - Cerimonie sempre alle 21:30 ora locale del player
  - Supporto 50+ timezone mondiali
  - Rilevamento automatico timezone dal browser
- **Notifiche Premiazione**:
  - 6 ore prima: "📢 Cerimonia tra 6 ore!"
  - 3 ore prima: "⏰ Cerimonia tra 3 ore!"
  - 1 ora prima: "🔔 Cerimonia tra 1 ora!"
  - Inizio: "🎬 Sta iniziando ORA!"
  - Indicatore LIVE/countdown nell'header
  - Polling ogni minuto
- **Nuovi Endpoint API**:
  - `GET /api/festivals/{id}/live-ceremony` - Dati cerimonia live
  - `POST /api/festivals/ceremony/chat` - Invia messaggio in chat
  - `POST /api/festivals/{id}/join-ceremony` - Unisciti come spettatore
  - `POST /api/festivals/{id}/announce-winner/{category}` - Annuncia vincitore
  - `POST /api/festivals/tts-announcement` - Genera audio TTS
  - `POST /api/festivals/{id}/announce-with-audio/{category}` - Annuncia con audio
- **Campo Composer nei Film**: Aggiunto `composer_id` al modello FilmCreate per nomination soundtrack
- **Fix Cinema Revenue**: Sistemato il calcolo dei profitti dei cinema nelle infrastrutture
  - Revenue basata su popolazione città, livello cinema, qualità film
  - Minimo garantito per livello
  - Logging migliorato

### v0.063 - Sistema Sottotitoli e Sequel - 10/03/2026 (COMPLETATO)
- **Campo Sottotitolo**: Aggiunto campo opzionale `subtitle` nella creazione di Film e Pre-Film
  - Obbligatorio quando si crea un sequel
  - Esempio: "La Vendetta", "Il Ritorno"
- **Sistema Sequel Migliorato**:
  - Checkbox "Questo è un sequel" nel wizard di creazione
  - Dropdown per selezionare il film originale
  - Genere ereditato automaticamente dal film parent
  - Massimo 5 sequel per saga
- **Bonus/Malus Sequel basati su performance del film originale**:
  - Film originale qualità >= 85: +35% base + 2% per sequel successivo
  - Film originale qualità >= 70: +20% base + 1% per sequel
  - Film originale qualità >= 55: +10% (fedeltà franchise)
  - Film originale qualità >= 40: -5% base, peggiora con più sequel
  - Film originale qualità < 40: -30% base, -10% per sequel
  - Bonus aggiuntivo basato sul tier del film originale
- **Indicatore Visivo Sequel**: Badge "SEQUEL #X" sui poster dei film
  - Nella card del film (lista)
  - Nella pagina dettaglio con info sul bonus applicato
- **Nuovo Endpoint API**:
  - `GET /api/films/my/for-sequel` - Lista film disponibili per sequel
- **Fix Generazione AI**:
  - Corretto import libreria LLM per synopsis (`LlmChat` invece di `OpenAILLM`)
  - Timeout axios aumentato a 2 minuti per generazioni lunghe
  - Aggiunto logging dettagliato per debug
  - Messaggi di errore più informativi nel frontend

### v0.062 - Selettore Lingua Login/Registrazione - 10/03/2026 (COMPLETATO)
- **Selettore lingua nelle pagine di autenticazione**: Pulsanti IT/EN in alto a destra
  - Cambio istantaneo della lingua dell'interfaccia
  - Traduzione automatica di tutti i testi (label, pulsanti, placeholder)
  - La preferenza viene salvata in localStorage

### v0.061 - Sistema Pre-Ingaggio Completato - 10/03/2026 (COMPLETATO)
- **Integrazione Film Creation**: Il cast pre-ingaggiato viene caricato automaticamente nel wizard di creazione film
- **Pulsante "Congeda"**: Per licenziare cast pre-ingaggiato durante la creazione film
  - Modal con dettaglio: anticipo perso + penale aggiuntiva + costo totale
  - Penale variabile 10-60% basata su fama + tempo trascorso
- **Sistema Rescissione Automatica**: 
  - Dopo 15 giorni, il cast può decidere di rescindere
  - Probabilità crescente con il passare del tempo
  - Rimborso automatico dell'anticipo al produttore
- **Fix bug**: Gestione campi mancanti (fame) nel database

### v0.060 - Sistema Pre-Ingaggio Cast - 10/03/2026 (COMPLETATO)
- **Pre-Film**: Crea bozza con titolo, genere e sceneggiatura (20-200 caratteri)
  - Durata 20 giorni, poi l'idea diventa pubblica
- **Pre-Ingaggio Cast**: Ingaggia Sceneggiatori, Registi, Musicisti, Attori prima di creare il film
  - Anticipo 30% della fee concordata
  - Sistema di rifiuto e rinegoziazione
- **Rinegoziazione**: Dopo il rifiuto, 2 opzioni:
  - Offerta libera
  - Accetta la richiesta del cast
  - Possibile rifiuto definitivo al secondo tentativo
- **Rilascia Cast**: Penale variabile 10-60% basata su fama + tempo trascorso
- **Board Idee Pubbliche**: Le bozze scadute diventano visibili ad altri produttori
- **Menu aggiornato**: "Bozze & Pre-Ingaggi" nel menu laterale
- **Nuovi Endpoint API**:
  - `POST /api/pre-films` - Crea pre-film
  - `GET /api/pre-films` - Lista pre-film
  - `POST /api/pre-films/{id}/engage` - Pre-ingaggia cast
  - `POST /api/negotiations/{id}/renegotiate` - Rinegozia
  - `POST /api/pre-films/{id}/release` - Rilascia cast
  - `POST /api/pre-films/{id}/convert` - Converti in film

### v0.059 - Recupero Password e Nickname - 10/03/2026 (COMPLETATO)
- **Recupero Password via Email**: Link "Password dimenticata?" nella pagina login
  - Inserisci email → ricevi link di reset (valido 1 ora)
  - Pagina dedicata per impostare nuova password
- **Recupero Nickname via Email**: Link "Nickname dimenticato?" nella pagina login
  - Inserisci email → ricevi email con il tuo nickname
- **Endpoint API**:
  - `POST /api/auth/recovery/request` - Richiedi recupero (password o nickname)
  - `POST /api/auth/recovery/reset-password` - Conferma reset password con token
  - `GET /api/auth/recovery/verify-token/{token}` - Verifica validità token
- **Nota**: Richiede configurazione Resend API key in `.env`

### v0.058 - Notifiche Release Notes & Trailer Gratuiti - 10/03/2026 (COMPLETATO)
- **Sistema 5 Tier Film**: Capolavoro, Epico, Eccellente, Promettente, Possibile Flop
  - Calcolo tier basato su qualità, cast, sceneggiatura, IMDb rating e fattore fortuna
  - Bonus/malus immediati all'opening day (-20% a +40%)
  - Bonus/malus giornalieri sui revenue
- **Pop-up Tier alla Creazione**: Popup festoso/triste che appare dopo la creazione del film mostrando il tier ottenuto
- **Pop-up Fine Programmazione**: Quando il proprietario visita un film terminato (withdrawn/completed), appare un popup che confronta aspettative vs risultato effettivo
  - Mostra revenue previsto vs effettivo
  - Barra di performance con percentuale delle aspettative
  - Messaggi speciali per sorprese (es. Flop diventato successo)
- **Sistema Like Migliorato**:
  - Blocco self-like (non puoi mettere like ai tuoi film)
  - Modal "Chi ha messo Like" al click sul numero di likes
  - Lista utenti con avatar, nickname, casa di produzione e data del like
  - Pulsante like in tutte le liste (CineBoard, Film Detail, ecc.)
- **Puntino Rosso Release Notes**:
  - Notifica nel menu quando ci sono nuove release notes non lette
  - Auto-reset quando l'utente visita la pagina Release Notes
  - Endpoint `/api/release-notes/unread-count` per contare non lette
  - Endpoint `/api/release-notes/mark-read` per marcare come lette
- **Bug Fix Trailer**:
  - ✅ **VERIFICATO FUNZIONANTE** - Trailer generato con successo in ~3 minuti
  - Generazione trailer ora GRATUITA (rimosso costo $50k)
  - Migliorato caricamento chiave API nel background task
  - Validazione duration (deve essere 4, 8 o 12 secondi)
  - Logging migliorato per debug

### v0.056 - Box Office Realistico - 10/03/2026 (COMPLETATO)
- **Revenue Realistici**: Incassi calcolati in base a ore in sala × opening_day × decay × qualità
- **Stima Finale**: Proiezione guadagni a 4 settimane basata su trend attuale
- **Aggiornamento ogni 10 minuti**: Il box office viene ricalcolato in tempo reale
- **Fix Bug ADV**: Corretto il bug che moltiplicava esponenzialmente i revenue

### v0.055 - Riscossione Rapida - 10/03/2026 (COMPLETATO)
- **Riscossione ogni minuto**: Gli incassi da film e infrastrutture ora sono riscuotibili ogni minuto invece che ogni ora
- **Cumulabilità 6 ore**: Massima cumulabilità aumentata da 4 a 6 ore

### v0.054 - Fix Incassi e Sistema Link - 10/03/2026 (COMPLETATO)
- **Fix Bug Incassi Pendenti**: Risolto bug che mostrava sempre $0 negli incassi da riscuotere
- **Fix Date Timezone**: Gestione corretta di date con/senza timezone per calcoli revenue
- **Sistema URL Manager**: Salva automaticamente l'URL corrente del gioco nel database
- **Banner Notifica**: Mostra notifica gialla quando il link del gioco cambia con pulsante copia
- **Endpoint /api/game-url**: GET per ottenere URL corrente, POST per aggiornare

### v0.053 - Sistema Affluenza Cinema (CineBoard) - 10/03/2026 (COMPLETATO)
- **Tab Attendance nella CineBoard**: Nuovo tab per visualizzare statistiche di affluenza ai cinema
- **Global Stats**: Film in sala, Cinema totali, Spettatori attuali, Media per cinema
- **Top 20 Most Screened (Now)**: Classifica film più programmati attualmente
- **Top 20 Most Screened (All-Time)**: Classifica storica proiezioni totali
- **Fix Bug Dashboard**: Risolto errore 500 su `/api/films/my` causato da dati incompleti
- **Fix Bug Scheduler**: Corretto nome collection `infrastructures` → `infrastructure`
- **Impatto su ranking**: L'affluenza influisce sul `cineboard_score` dei film

### v0.052 - Dashboard Finanziaria Completa - 09/03/2026 (COMPLETATO)
- **Pulsante "Riscuoti Tutto"**: Raccoglie incassi da tutti i film in sala + infrastrutture in un click
- **Box Pending Revenue**: Mostra totale da riscuotere diviso per Film e Infrastrutture
- **Bilancio Finanziario**: 3 box con Speso (rosso), Guadagnato (verde), Profitto/Perdita
- **Breakdown dettagliato**: Costi film vs infrastrutture, revenue film vs infrastrutture
- **Indicatore visivo**: TrendingUp verde se in profitto, TrendingDown arancione se in perdita
- **Aggiornamento auto**: Pending revenue aggiornato ogni minuto

### v0.051 - Sistema Feedback & Bug Report - 09/03/2026 (COMPLETATO)
- **Nuova pagina** `/feedback` per suggerimenti e segnalazione bug
- **Suggerimenti**: Titolo, descrizione, categoria (feature/improvement/ui/gameplay/other), sistema voti
- **Bug Report**: Titolo, descrizione, gravità (low/medium/high/critical), passi per riprodurre
- **Notifica broadcast** a tutti i player (23 utenti notificati)
- **Endpoint admin**: `GET /api/admin/feedback-summary` per riepilogo
- **Reward XP** per suggerimenti (5 XP) e bug report (5-25 XP in base a gravità)

### v0.050 - Release Notes Dinamiche - 09/03/2026 (COMPLETATO)
- **Database MongoDB**: Note di rilascio salvate nel database invece che nel codice
- **Auto-increment versione**: Nuove release ottengono automaticamente la versione successiva
- **Endpoint admin**: `POST /api/admin/release-notes` per aggiungere nuove release
- **Sincronizzazione**: Lista statica migrata al DB allo startup

### v0.049 - Sistema Autonomo 24/7 - 09/03/2026 (COMPLETATO)
- **APScheduler integrato**: Task automatici senza intervento dell'Agent
- **8 job schedulati**:
  - `update_films_revenue`: Aggiorna ricavi film ogni ora
  - `update_leaderboard`: Ricalcola classifiche ogni 4 ore
  - `update_cinema_revenue`: Aggiorna ricavi cinema ogni 6 ore
  - `reset_daily_challenges`: Reset sfide giornaliere a mezzanotte
  - `cleanup_rejections`: Pulizia rifiuti cast scaduti (24h)
  - `generate_cast`: Genera nuovi membri cast ogni giorno alle 06:00
  - `cleanup_hired_stars`: Pulisce star ingaggiate non usate (7 giorni)
  - `reset_weekly_challenges`: Reset sfide settimanali ogni lunedì
- **Endpoint monitoring**: `GET /api/admin/scheduler-status`
- **Nuovo file**: `/app/backend/scheduler_tasks.py`

### v0.048 - Sistema Rifiuto Ingaggio Cast - 09/03/2026 (COMPLETATO)
- **Backend**: Endpoint `POST /api/cast/offer` per fare offerte ai membri del cast
- **Backend**: Endpoint `GET /api/cast/rejections` per ottenere lista rifiuti (ultime 24h)
- **Backend**: 23 motivazioni di rifiuto in italiano e inglese
- **Backend**: Calcolo probabilità rifiuto basato su: livello giocatore, fama cast, ricavi, genere film
- **Frontend**: Modal "Offerta Rifiutata" con nome, motivazione, stelle e fama
- **Frontend**: Card con badge "Ha rifiutato" e visivamente disabilitata
- **Persistenza**: Rifiuto memorizzato per 24 ore (non richiederlo di nuovo)

### v0.047 - Sistema Ingaggio Star - 09/03/2026 (COMPLETATO)
- **Sezione dedicata "Stelle Scoperte"** con pagina completa
- **Card star cliccabili** per vedere skill dettagliate
- **Sistema ingaggio anticipato**: paghi ora, disponibile nel prossimo film
- **Costo calcolato** su fama, skill e stelle
- **Star ingaggiate** mostrate in verde nel wizard
- **Pagina Release Notes** con versioning (0.000 → 0.047)
- **48 release documentate** nella storia

### v0.046 - Trailer in Chat & Giornale
- Annunci trailer automatici in chat via CineBot
- Sezione "Nuovi Trailer" nel Cinema Journal
- Click su trailer naviga al film

### v0.045 - Boost Introiti & Sponsor
- +30% introiti primo giorno
- +10% introiti giorni successivi
- 200 sponsor totali (40 a rotazione)
- Budget sponsor aumentato +40%

### v0.044 - Cast Pool Espanso
- 200 cast members per tipo nel wizard
- 2000+ membri totali nel database
- Generazione automatica giornaliera

### v0.043-v0.042 - Sistema Film Incompleti
- Autosave ogni 30 secondi
- Board Film Incompleti (Bozze)
- Pausa/Riprendi creazione film

### v0.041-v0.040 - CineBoard & Fix Trailer
- CineBoard classifiche
- Timeout automatico trailer stuck

## API Endpoints Nuovi

### Sistema Livelli Film & Like
```
GET  /api/films/{film_id}/tier-expectations  - Verifica aspettative vs risultato (solo owner)
                                               Returns: { tier, expected_revenue, actual_revenue, ratio, met_expectations, exceeded, message }
GET  /api/films/{film_id}/likes              - Lista utenti che hanno messo like
                                               Returns: { likers: [{ user_id, nickname, avatar_url, production_house, liked_at }] }
POST /api/films/{film_id}/like               - Metti/togli like a un film (blocca self-like)
                                               Returns: { liked: bool, likes_count: int }
```

### Stelle Scoperte & Ingaggio
```
GET  /api/discovered-stars     - Lista star scoperte con costo ingaggio
POST /api/stars/{id}/hire      - Ingaggia star per prossimo film
GET  /api/stars/hired          - Star ingaggiate (non ancora usate)
DELETE /api/stars/hired/{id}   - Rilascia star ingaggiata
```

### Release Notes
```
GET  /api/release-notes        - Storico versioni e cambiamenti
```

### Sistema Scheduler (Autonomo 24/7)
```
GET  /api/admin/scheduler-status  - Stato dei job schedulati
                                    Returns: { scheduler_running, jobs_count, jobs[] }
```

### Sistema URL/Redirect
```
GET  /api/game-url              - Ottiene URL corrente del gioco (pubblico, no auth)
POST /api/game-url              - Aggiorna URL corrente { url: string }
GET  /api/redirect-to-game      - Redirect 302 all'URL corrente
```

### Sistema Affluenza Cinema
```
GET  /api/cineboard/attendance    - Dati affluenza per CineBoard
                                    Returns: { global_stats, top_now_playing, top_all_time }
GET  /api/films/{id}/distribution - Distribuzione cinema per film specifico
                                    Returns: { countries[], total_cinemas, total_attendance }
```

### Sistema Rifiuto Cast
```
POST /api/cast/offer           - Fai un'offerta a un membro del cast
                                 Body: { person_id, person_type, film_genre }
                                 Returns: { accepted, reason, stars, fame, already_refused }
GET  /api/cast/rejections      - Lista rifiuti ultime 24h per l'utente corrente
                                 Returns: { rejections: [], refused_ids: [] }
```

## Menu Principale
1. Dashboard
2. I Miei Film
3. Crea Film
4. Bozze
5. Saghe e Serie
6. Infrastrutture
7. Mercato
8. Tour Cinema
9. **Giornale del Cinema**
10. **Stelle Scoperte** (NUOVO)
11. Festival
12. CineBoard
13. Mini Giochi
14. Classifica
15. Chat
16. **Note di Rilascio** (NUOVO)
17. Tutorial
18. Crediti

## Architettura
- Backend: FastAPI + MongoDB
- Frontend: React + TailwindCSS + Shadcn/UI
- AI: OpenAI GPT-4o, Gemini Nano Banana, Sora 2
- Versione: v0.057

## Backlog

### P0 - Critico
- [ ] **Refactoring Critico**: `server.py` (~10700 righe) e `App.js` (~10100 righe) - URGENTE

### P1 - Priorità Alta
- [ ] **Impatto Affluenza su Rating**: L'affluenza deve incidere dinamicamente sulla valutazione dei film
- [ ] **Cinema Distribution Page**: Aggiungere sezione nella pagina dettaglio film con lista cinema dove è in programmazione
- [ ] **Attività delle Major**: Co-Produzioni, Sfide tra Major
- [ ] **Sistema Acquisto CineCoins**: Integrazione Stripe per acquisto valuta di gioco (IN PAUSA)

### P2 - Future
- [ ] Mini-giochi Versus tra giocatori
- [ ] Cerimonie di premiazione "Live"
- [ ] Traduzione categorie festival

## Note Tecniche

### Formula Costo Ingaggio Star
```python
base_cost = 100000  # $100k
fame_mult = 1 + (fame_score / 100)
skill_mult = 1 + (avg_skill / 100)
hire_cost = base_cost * fame_mult * skill_mult * stars
```

### Versioning
- Formato: `0.XXX`
- Incremento: +0.001 per ogni feature/fix
- Storia: 48 release dalla v0.000

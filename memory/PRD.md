# CineWorld Studio's — PRD

## Pipeline V3 Film — Completa
10 step, CWSv 1-10, 14 file calcolo.

## Pipeline V3 Serie TV & Anime — Completa
9 step, CWSv serie+episodi, titoli AI, cliffhanger, scheduling TV complesso.

## CWSv System
Film: 5 file (idea/hype/cast/production + quality.py). Serie: 1 file (quality_series.py).

## CWTrend System
Score dinamico 1-10. File: calc_cwtrend.py. Indipendente dalla qualità.
**CWTrend Sparkline** — Aggiunto mini-grafico SVG (ultimi 7gg) nel popup "Dati Cinema" (CinemaStatsModal). Backend: `GET /api/pipeline-v2/films/{id}/theater-stats` ora ritorna `cwtrend_history` array con 7 punti dati.

## Rinnovo Stagione — Implementato (16/04/2026)
- S2/S3/... creata da serie completata/in_tv/catalog
- CWSv base parte da S1 ±10%
- Lock 30 giorni reali prima del release
- Speedup CP: 15CP=dimezza(15g), 30CP=immediato
- Cast e poster ereditati dalla stagione precedente
- Endpoint: POST /api/pipeline-series-v3/series/{id}/renew-season
- **UI integrata in "La Mia TV" — tab "Completate"**

## Sezione La Mia TV — Implementata (17/04/2026)
- Pagina completa a `/my-tv` con 4 tab: In Onda, Completate, Catalogo, In Produzione
- Stats bar: serie in onda, completate, episodi trasmessi, incasso totale
- **AiringCard**: poster, progress bar episodi, bottone "Trasmetti" per broadcast
- **CompletedCard**: con bottone "Rinnova S2/S3..." e stato rinnovo
- **CatalogCard**: bottone "Invia in TV" per spostare da catalogo a TV
- **PipelineCard**: mostra progetti in lavorazione con stato pipeline
- Backend: `GET /api/pipeline-series-v3/tv/my-dashboard`
- Backend: `POST /api/pipeline-series-v3/tv/send-to-tv/{id}`

## Prossimamente Dashboard — Implementato
- GET /prossimamente: serie in pipeline + serie in_tv con conteggio ep trasmessi
- Sezione "IN ARRIVO SU TV" nella Dashboard con poster, titolo, ep count

## ProducerProfileModal — Implementato + Aggiornato (17/04/2026)
Modal con stats produttore, filmografia, CWSv medio, badge.
- **Segui Produttore**: bottone Follow/Unfollow con check stato `GET /api/players/{id}/is-following`
- **Confronta con me**: bottone apre CompareProducersModal
- Chat e Sfida buttons

## Confronto Produttori — Implementato (17/04/2026)
- `CompareProducersModal.jsx` — side-by-side di 8 metriche (Film, Serie TV, Anime, CWSv, Revenue, Fama, Livello, Punteggio)
- Winner highlight (verde) per ogni metrica
- Miglior produzione comparison
- Backend: `GET /api/players/compare?p1={id}&p2={id}`
- Accessibile da: PlayerProfilePopup ("Confronta con me") e ProducerProfileModal

## Scheduling TV Serie
4 politiche: 1/giorno, 3/giorno, 2 mezze stagioni, tutta insieme.

## Bug Fix — Ghost Film "The Gratch" (17/04/2026)
- Causa: collection `sequels` non pulita durante admin reset → startup migration ricreava film
- Fix: aggiunto `sequels` alla lista `content_collections` in `admin_recovery.py`

## Bug Fix — Timer Bypass max_step_reached (16/04/2026)
- Step precedenti completati non bloccano più l'avanzamento

## Arena PvP v2 — Rework Completo (17/04/2026)
### Limiti Dinamici
- Base: 10 azioni/ora (tutti)
- +3/ora per livello Divisione Operativa
- +2/ora per livello Divisione Investigativa
- +1/ora per livello Divisione Legale
- Max ~35 azioni/ora per chi investe

### Diminishing Returns
- Max 7 azioni su stesso player in 24h
- Dopo 2: 75%, dopo 3: 50%, dopo 4: 25%, dopo 5: 10%, dopo 6: 5%, dopo 7+: 2%

### 3 Divisioni PvP (fix bonus):
- **Operativa**: +3% successo/livello, riduzione costi (corretto: attacco, non difesa)
- **Investigativa**: Rivela attaccante (50-95%), contrattacco auto (Lv2+), riduzione costi 5%/lv
- **Legale**: Blocca attacchi (15-45%), difesa gratuita (Lv3+), protegge fama

### Azioni Espanse
- 8 supporti: +Premiere Esclusiva, Partnership Brand, Virale TikTok, Red Carpet
- 6 boicottaggi: +Accusa Plagio, Campagna Stampa Negativa

### Sistema Rivalità
- 4+ boicottaggi reciproci in 7gg = Rivali
- Rivalità: +20% danni reciproci

### V3 Pipeline nell'Arena
- Film V3 da step "hype" in poi
- Serie/Anime V3 da step "hype" in poi

### Animazioni Impatto
- ParticleBurst: esplosione di particelle per boicottaggi riusciti/ritorti
- ImpactFlash: flash radiale colorato
- Spring animations con scale/rotate
- Badge rivalità animato
- Warning diminishing returns

### Notifiche
- Supporto ricevuto, Boicottaggio subito (con/senza identità attaccante), Attacco bloccato, Contrattacco

## Backlog
### P0
- (nessuno — tutti P0 completati!)

### P1
- (Tutti P1 completati!)

## Pagina "I Miei Contenuti" — Implementata (17/04/2026)
- 4 tab: Film, Saghe e Sequel, Serie TV, Anime
- Griglia locandine piccole (4 colonne mobile, 8+ desktop)
- Popup 6 opzioni su click (proprietario): Visualizza, ADV, Rigenera locandina, Ritira, Vendi, Elimina
- Conferma eliminazione non-standard, conferma vendita con bottone nero
- "I Suoi Contenuti" — vista pubblica per altri player (no azioni, solo griglia + dettaglio)
- Route: `/films?tab=film|saghe|serie|anime` e `/player/:id/content`
- Backend: `GET /api/players/{id}/films` e `GET /api/players/{id}/series`

### P2
- (Tutti P2 implementati!)

## Mercato Unificato v2 — Implementato (17/04/2026)
- 5 sezioni: Film, Serie TV, Anime, Infrastrutture, Diritti TV
- 3 tipi vendita: Prezzo Fisso, Asta (24-72h), Offerta Libera
- Commissione 10% al sistema
- Storico transazioni con stats
- "Affare del Giorno" system
- Diritti TV: vendita diritti di trasmissione con royalties 5-15%
- Routes: `/market`, `/marketplace`
- Backend: `GET /api/market/browse`, `POST /api/market/list`, `POST /api/market/buy`, `POST /api/market/bid`, `POST /api/market/offer`, `POST /api/market/tv-rights/list`, `POST /api/market/tv-rights/buy/{id}`

## Medaglie Produttore — Implementato (17/04/2026)
- 27 medaglie in 7 categorie: Produzione, Qualità, Business, PvP, Genere, Social, Infrastrutture
- 4 tier: Bronzo, Argento, Oro, Leggendaria
- Check automatico dopo azioni chiave
- Routes: `/medals`, `/challenges`
- Backend: `GET /api/medals/my`, `GET /api/medals/player/{id}`

## Sfide Settimanali — Implementato (17/04/2026)
- 12 sfide nel pool, 3 selezionate random per settimana
- Ricompense: Fondi, CinePass, XP, Fama
- Progress tracking automatico
- Backend: `GET /api/challenges/weekly`, `POST /api/challenges/weekly/{id}/claim`

### Refactoring
- Pulizia codice legacy (`film_pipeline_legacy.py`, vecchi endpoint)
- Riorganizzazione `scheduler_tasks.py` (file troppo grande, >2200 righe)

## Game Hooks — Implementato (17/04/2026)
- `game_hooks.py` centralizza trigger per medaglie e sfide
- Hook inseriti in: release film V3, release serie, PvP support/boycott/defend, market sell/buy, follow, broadcast episodi
- Medaglie si sbloccano automaticamente dopo azioni chiave

## Festival Cinematografici — Implementato (17/04/2026)
- Creazione automatica quando ci sono 3+ film recenti (ultimi 30gg)
- 8 categorie: Miglior Film, Regia, Attore, Sceneggiatura, Colonna Sonora, Serie TV, Anime, Rivelazione
- Votazione: 1 voto per categoria, 1 volta sola
- Durata: 5 giorni, poi chiusura automatica con premi (15 fama + $500K ai vincitori)
- Backend: `GET /api/festivals/current`, `POST /api/festivals/{id}/vote`, `GET /api/festivals/results/{id}`

## Classifica Settimanale Sfide — Implementato (17/04/2026)
- Classifica chi ha completato più sfide nella settimana
- Backend: `GET /api/challenges/leaderboard`

## Valutazione Venditore — Implementato (17/04/2026)
- Rating 0-5 basato su transazioni completate: Nuovo→Principiante→Venditore→Commerciante→Esperto→Leggenda
- Backend: `GET /api/market/seller-rating/{user_id}`

## Affare del Giorno + Aste — Scheduler Automatico (17/04/2026)
- Job giornaliero alle 08:00 UTC
- Seleziona listing random con -30% sconto come "Affare del Giorno"
- Chiude aste scadute: trasferisce item al vincitore, rimborsa sconfitti
- Chiude festival scaduti e assegna premi ai vincitori


## Bug Fix: Ruoli Permanenti CO_ADMIN/MOD — Risolto (17/04/2026)
- Causa: `set-perm-badge` in `server.py` salvava ruoli in minuscolo (`co_admin`, `moderator`) ma `auth_utils.py` li aspetta maiuscolo (`CO_ADMIN`, `MOD`)
- Fix: Corretta capitalizzazione in endpoint + aggiornata label mapping
- Aggiunta migrazione DB per correggere utenti esistenti con ruoli minuscoli
- Testato: Assegnazione/rimozione badge con tutti i percorsi di fallback

## Backlog Prioritizzato
- (P1) Refactoring `scheduler_tasks.py` — dividere in moduli specializzati
- (P2) Definire permessi operativi per ruolo MOD
- (P2) Notifiche push per follower
- (P2) Personalizzazione avatar produttore
- (P2) Tornei PvP mensili con bracket eliminazione diretta
- (P3) Pulizia legacy: `film_pipeline_legacy.py`, `pipeline_v2.py`


## Contratti Esclusivi Agenzie — Implementato (18/04/2026)
### Backend
- `GET /api/pipeline-v3/exclusive-contracts` — Lista 30 agenzie con stato contratto
- `POST /api/pipeline-v3/sign-exclusive-contract` — Firma contratto (10-25 CP, 30gg)
- Collezione DB: `exclusive_contracts` con `{user_id, agency_id, signed_at, expires_at, exclusive_actor}`
- Max 2 contratti attivi contemporaneamente
- Costo scala con reputazione: Rep 90+ = 25CP, 80+ = 20CP, 70+ = 15CP, <70 = 10CP
- Genera automaticamente 1 attore esclusivo 4+ stelle (gratis durante il contratto)
- Auto-sblocca come Partner (preferred) alla firma

### Vantaggi Esclusivo vs Partner vs Free
| Feature | Free | Partner (5CP) | Esclusivo (10-25CP/mese) |
|---------|------|--------------|--------------------------|
| Stelle minime | 0 | 3+ | 4+ |
| Proposte cast | x1 (6) | x2 (12) | x3 (18) |
| Sconto costi | 0% | -10% | -20% |
| Attore esclusivo | No | No | Si (gratis) |

### Frontend
- Nuovo tab "Contratti Agenzie" in `CastingAgencyPage.jsx`
- Card contratti attivi con countdown giorni, attore esclusivo, stats vantaggi
- Lista agenzie con bottone "Firma" e costo CP

## Fix Avatar Persistenza + Logo Studio + Layout Dashboard — Implementato (18/04/2026)

### Fix Avatar che Sparisce
- Causa: `PUT /auth/avatar` convertiva base64 data URI in file locale (`/app/backend/uploads/avatars/`). Al restart del container, i file vengono persi → avatar 404.
- Fix: `PUT /auth/avatar` ora mantiene base64 in MongoDB (persistente). `POST /avatar/generate` gia salvava in DB — rimosso il doppio-save nel frontend.

### Logo Casa di Produzione (AI)
- Nuovo endpoint `POST /api/logo/generate` — genera logo AI (GPT Image 1) per la casa di produzione
- Salva come base64 PNG 128x128 in `logo_url` nel DB utente
- Frontend ProfilePage: sezione "Logo Casa di Produzione" con generatore AI e preset stili
- Preset: Minimalista dorato, Stile Hollywood classico, Moderno neon cinema, Elegante bianco nero

### Fix Nickname Maiuscolo
- Causa: font `Bebas_Neue` nel Dashboard forzava tutto in uppercase
- Fix: rimosso `font-['Bebas_Neue']`, usa font bold standard che preserva il case originale (NeoMorpheus)

### Layout Dashboard — Avatar + Nickname + Logo + Casa Produzione
- Avatar grande (w-10 h-10) + Nickname + Badge ruolo sulla stessa riga
- Sotto: Logo mini (w-3.5) + Nome casa di produzione
- Tutto cliccabile per espandere le stats

### Logo Ovunque (componente `StudioName`)
- Creato componente riusabile `/components/StudioName.jsx`
- Integrato in: Dashboard, FriendsPage (3 tab), ContentTemplate (scheda film), FilmDetailV3
- Backend: `logo_url` incluso in producer fetch per film rilasciati e liste film
- Fix ruoli CO_ADMIN/MOD nel badge display (ora controlla uppercase)

- In CastPhase: badge dorato "ESCLUSIVO" su proposte da agenzie con contratto
- Attore esclusivo in cima con badge "ESCLUSIVO" e costo GRATIS

## Bug Fix: Hype 100% Animation Loop — Risolto (18/04/2026)
- **Causa root**: `onWowAnimationComplete` in `PipelineV3.jsx` usava `useCallback([], [])` con stale closure. Quando l'animazione WOW finiva, `completeAdvance` catturava `selected.id = null` dal mount iniziale, quindi la chiamata API falliva silenziosamente e il film restava in hype.
- **Fix**: Salvato `{ nextState, pid }` in `pendingAdvanceRef`. `onWowAnimationComplete` ora fa la chiamata API inline usando il pid dal ref, eliminando ogni dipendenza da closure stale.
- **Testato**: Advance hype→cast via API confermato funzionante.

## Bug Fix: Film Legacy senza Hype Timers — Risolto (18/04/2026)
- Migrazione automatica `backfill_hype_timers_v1` aggiunta al server startup
- Film V3 in stato `hype` senza `hype_started_at` ricevono timer retroattivi già completati
- Film oltre lo step hype ricevono timer nel passato

## Admin Maintenance V3 — Implementato (18/04/2026)
- Sistema manutenzione aggiornato per supportare Pipeline V3 (`pipeline_state` vs `status`)
- Diagnosi V3: rileva hype timer mancanti, ciak/finalcut bloccati, flag STUCK/BROKEN
- `force_step` V3: avanza allo step successivo con auto-fill timer e dati mancanti
- `complete_project` V3: forza rilascio con qualità calcolata (max 85%)
- `reset_step` V3: torna allo step precedente
- `auto_fix` V3: ripara timer mancanti e cast placeholder
- Testato: diagnosi, force_step, complete_project tutti verificati via API

## CRc (Cast Rank CineWorld) — Implementato (18/04/2026)
- Nuovo sistema di valutazione cast 0-100 (non percentuale): `CRc`
- Formula: `avg_skill * 0.6 + fame * 0.2 + stars * 4`
- Mostrato accanto al nome nella NpcCard e nel SkillsModal con colori a soglia (giallo/verde/ambra/rosso)
- Backend: `_calc_crc_from_npc()` in pipeline_v3.py
- Cast proposals ora ordinati per CRc decrescente

## Cast Filtraggio per Livello — Implementato (18/04/2026)
- V3 `cast-proposals` ora filtra cast per livello/fama del giocatore (come V2)
- `fame_cap_base = min(40 + level*2 + fame*0.05, 95)` — max 2 star picks sopra il cap
- Cast scoring basato su genere film (genre_skill_weight)
- Giocatori bassi livello vedranno cast meno forti

## Skills 8 nel Modal — Verificato (18/04/2026)
- SkillsModal mostra esattamente 8 skills (slice 0-8)
- Backend genera 8 skills per membro (SKILLS_PER_MEMBER = 8 in cast_system.py)
- `cast-proposals` e `select-cast-member` passano gender, fame_category, primary_skills, crc

## Bug Fix: Animazione Release Bloccata — Risolto (18/04/2026)
- Causa: `releasePhase` restava a `'wow'` dopo `setSelected(null)`. Quando l'utente selezionava un nuovo progetto, l'overlay si riattivava.
- Fix: `onWowDone` resetta `releasePhase` a `'idle'`. `selectProject` resetta release state. Safety check per reset automatico se `releasePhase` è inconsistente.

## Sistema Agenzie Integrato in V3 — Implementato (18/04/2026)
### Agenzia del Player in Pipeline V3
- Nuovo endpoint `GET /api/pipeline-v3/films/{pid}/my-agency-actors`
  - Mostra attori dell'agenzia personale + studenti scuola
  - Sconto automatico: -15% agenzia, -30% attori di ritorno (fedeltà)
  - CRc calcolato per ogni attore
  - Flag `is_returning` per chi ha già lavorato con il produttore
- Nuovo endpoint `POST /api/pipeline-v3/films/{pid}/cast-agency-actor`
  - Casting diretto di attori dall'agenzia nel progetto V3
  - Supporta source `agency` e `school`
  - Gestione fondi automatica con sconto applicato

### Agenzie NPC in Pipeline V3
- Nuovo endpoint `GET /api/pipeline-v3/films/{pid}/npc-agency-proposals`
  - 30 agenzie NPC (Cinecittà Talent, Hollywood Prime, Tokyo Star, etc.)
  - Filtrate per genere film (agenzie con specializzazione matching al top)
  - Numero agenzie scala con livello player (3 + livello/10)
  - Ogni agenzia propone cast dal pool globale con nome agenzia visibile

### Frontend CastPhase.jsx — 3 Sorgenti Cast
- Tab **Mercato**: pool globale filtrato per livello (come prima)
- Tab **La Mia Agenzia**: attori propri con sconto e badge "Ritorno"/"Agenzia"
- Tab **Agenzie NPC**: proposte da agenzie con nome, regione, reputazione
- Cast selezionato mostra badge viola "Agenzia" e verde "Ritorno"

## Bonus Chimica Cast — Implementato (18/04/2026)
- Coppie di attori che hanno lavorato insieme in film precedenti danno bonus CWSv
- Calcolo: `_calc_chemistry_pairs()` analizza cast corrente vs film passati del produttore
- Bonus: +0.5% per coppia, max +3.0% (6 coppie)
- Integrato in `calc_quality_cast.py` sezione CHIMICA
- Frontend: sezione verde "Chimica Cast (+CWSv)" mostra coppie e bonus %
- Ricalcolato automaticamente ogni volta che il cast cambia

## Agenzie Preferite (Partner) — Implementato (18/04/2026)
- Player sblocca agenzie NPC come partner per 5 CinePass
- Endpoint: `POST /api/pipeline-v3/unlock-agency` + `GET /api/pipeline-v3/preferred-agencies`
- Vantaggi partner: cast 3+ stelle, doppio numero proposte, -10% costi
- Agenzie preferite sempre incluse nelle proposte (priority)
- Frontend: pannello gestione con lock/unlock, badge Partner/stella
- Collezione DB: `preferred_agencies` con `{user_id, agency_id, unlocked_at}`


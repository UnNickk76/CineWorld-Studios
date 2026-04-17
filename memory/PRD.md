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

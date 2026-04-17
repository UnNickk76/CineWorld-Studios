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
- Sfide settimanali, Festival, Concorrenza
- Fase Market (film + serie + anime)
- Medaglie produttore (es. "Maestro dell'horror", "Re degli Incassi")
- Storico CWTrend sparkline con dati storici reali (attualmente calcolato deterministicamente)

### Refactoring
- Pulizia codice legacy (`film_pipeline_legacy.py`, vecchi endpoint)
- Riorganizzazione `scheduler_tasks.py` (file troppo grande, >2200 righe)

# CineWorld Studio's — PRD

## Pipeline V3 Film — Completa
10 step sequenziali con CWSv (CineWorld Studio's voto) 1.0-10.
14 file calcolo dedicati in `/app/backend/utils/calc_*.py`.

## Pipeline V3 Serie TV & Anime — In Sviluppo (16/04/2026)

### Backend Completato
- **Router**: `/app/backend/routes/pipeline_series_v3.py` — state machine 9 step
- **CWSv Serie**: `/app/backend/utils/calc_quality_series.py`
- **16 generi TV** + **18 generi Anime** con range episodi per genere
- **Titoli episodi AI** generati da GPT-4o-mini, coerenti con titolo/trama
- **CWSv per episodio**: variazione ±8% dal voto serie, cliffhanger ±12% ultimi 2 ep
- **Filler malus** per anime con troppi episodi
- **Opening/Ending bonus** per anime (compositore)
- **Prossimamente TV**: toggle che decide se la serie va in Dashboard o solo in "I Miei"
- **Binge vs Settimanale**: scheduling distribuzione

### Step Pipeline Serie V3
| # | Step | Descrizione |
|---|---|---|
| 0 | Idea | Titolo, genere, sottogeneri, sinossi, N° episodi, locations, poster |
| 1 | Hype | Timer progressivo, velocizzazione CP |
| 2 | Cast | Showrunner, sceneggiatori (3), attori (8), compositore, guest star |
| 3 | Prep | Formato (miniserie/stagionale/lunga/maratona), durata ep, CGI/VFX |
| 4 | Ciak | Timer real-time (30min/ep TV, 20min/ep anime), velocizzazione |
| 5 | FinalCut | Post-produzione, calcolo CWSv episodi |
| 6 | Marketing | Sponsor, marketing, toggle "Prossimamente TV" |
| 7 | Distribution | Binge vs settimanale, canale, delay release |
| 8 | Release | Riepilogo + CWSv finale + destinazione (TV o Catalogo) |

### Frontend — Da Completare
- Pagine `SeriesTVPipelineV3.jsx` e `AnimePipelineV3.jsx`
- Adattamento componenti V3 film per serie
- Integrazione episodi con titoli AI nel flusso
- Sezione "Prossimamente" nella Dashboard

## CWSv System
- 5 file calcolo film: `calc_quality_idea/hype/cast/production.py` + `calc_quality.py`
- 1 file calcolo serie: `calc_quality_series.py`
- Voto 1.0-10, X.0 senza decimale
- Pre-voto visibile ad ogni step
- Step 6/7/8 non influenzano CWSv → futuro "voto Andamento"

## Backlog
### P0
- Frontend pipeline Serie TV/Anime V3 (pagine + componenti)
- Voto Andamento (dinamico)

### P1
- Rinnovo stagione (S2 parte da CWSv S1 ±10%)
- CinemaStatsModal + ProducerProfileModal dati reali
- Fase 3 Market: vendite TV/Anime

### P2
- Sfide settimanali, Festival
- Concorrenza, Ripetitività genere

## Promemoria
- Serie TV/Anime: stessa base CWSv con varianti (episodi, cliffhanger, filler, OST)
- Voto Andamento: sviluppo futuro
- Personalità città: influenza Andamento
- season_number nella struttura DB per supporto rinnovo stagioni

# CineWorld Studio's — PRD

## Pipeline V3 Film — Completa
10 step sequenziali con CWSv. 14 file calcolo in `/app/backend/utils/calc_*.py`.

## Pipeline V3 Serie TV & Anime — Completata (16/04/2026)

### Backend
- **Router**: `/app/backend/routes/pipeline_series_v3.py` — state machine 9 step
- **CWSv Serie**: `/app/backend/utils/calc_quality_series.py`
- 16 generi TV + 18 generi Anime
- Titoli episodi AI (GPT-4o-mini), CWSv per episodio, cliffhanger ±12%
- Filler malus anime, Opening/Ending bonus compositore
- Prossimamente TV toggle, Binge vs Settimanale

### Frontend
- **Componente condiviso**: `/app/frontend/src/components/v3/PipelineSeriesV3.jsx`
- **Pagine**: `SeriesTVPipelineV3.jsx`, `AnimePipelineV3.jsx`
- Routing aggiornato in App.js (`/create-series`, `/create-anime`)
- 9 step UI: Idea (con generi + episodi + titoli AI) → Hype → Cast → Prep → Ciak → FinalCut → Marketing (toggle Prossimamente) → Distribuzione TV (Binge/Settimanale) → Uscita

### API Endpoints
- `POST /api/pipeline-series-v3/create` — Crea progetto
- `GET /api/pipeline-series-v3/projects` — Lista progetti
- `GET /api/pipeline-series-v3/projects/{pid}` — Dettaglio
- `POST /api/pipeline-series-v3/projects/{pid}/save-idea` — Salva idea
- `POST /api/pipeline-series-v3/projects/{pid}/advance` — Avanza step
- `GET /api/pipeline-series-v3/projects/{pid}/prevoto` — Pre-voto CWSv
- `POST /api/pipeline-series-v3/projects/{pid}/generate-episode-titles` — Titoli AI
- `POST /api/pipeline-series-v3/projects/{pid}/save-marketing-data` — Marketing + Prossimamente
- `POST /api/pipeline-series-v3/projects/{pid}/save-distribution` — Binge/Settimanale
- `POST /api/pipeline-series-v3/projects/{pid}/confirm-release` — Release finale

## Backlog
### P0
- Voto Andamento (dinamico): CWSv + marketing/sponsor/hype/distribuzione
- Rinnovo Stagione (S2 da CWSv S1 ±10%)

### P1
- CinemaStatsModal + ProducerProfileModal dati reali
- Integrazione "Prossimamente" sezioni Dashboard (serie/anime)

### P2
- Sfide settimanali, Festival, Concorrenza
- Fase Market (film + serie + anime)

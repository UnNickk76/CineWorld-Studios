# CineWorld Studio - PRD

## Problema Originale
Gioco browser di simulazione cinematografica. L'utente gestisce uno studio, produce film/serie/anime, gestisce una rete TV.

## Architettura
- **Frontend**: React (SPA), pagine in `/app/frontend/src/pages/`
- **Backend**: FastAPI, routes in `/app/backend/routes/`
- **Database**: MongoDB

## Funzionalità Implementate

### Core
- Auth (login/register), Dashboard, Profilo
- Sistema fondi, Moneta virtuale, Daily bonus

### Pipeline V2 (Film/Serie/Anime)
- Produzione multi-step (concept -> script -> cast -> filming -> post -> release)
- Sistema stagioni multiple con franchise fatigue
- Generazione episodi persistente (titolo, trama, tipo: normal/peak/filler/plot_twist/season_finale)
- Cast con animatori/doppiatori per anime
- UI stile Netflix per episodi

### Emittente TV (Palinsesto)
- Creazione stazione TV con infrastruttura
- Aggiunta contenuti (film/serie/anime) al palinsesto
- **[NUOVO] Sistema Broadcast Episodi**:
  - Trasmissione in tempo reale (1 ep ogni X giorni, configurabile)
  - Modalità Binge (tutti gli episodi subito)
  - Auto-avanzamento basato su timestamp reale
  - Performance per-episodio (viewers, revenue, rating)
  - Post-stagione: Repliche (audience al 40%) o Ritiro
  - Backward compatible con entry legacy
  - Revenue accreditato automaticamente all'utente
- Sezioni Netflix, Classifica stazioni, Marketplace

### Minigiochi Arcade
- TapCiak, SceneFlip, CatchTheStar, Velion AI

### Admin
- Tool Migrazione V1 -> V2

## API Key per Broadcast TV
- `POST /api/tv-stations/start-broadcast` - Avvia trasmissione (station_id, content_id, air_interval_days)
- `GET /api/tv-stations/{sid}/broadcast/{cid}` - Dettaglio episodi trasmissione
- `POST /api/tv-stations/retire-series` - Ritira serie
- `POST /api/tv-stations/start-reruns` - Avvia repliche (40% audience)

## Backlog

### P1
- Fix minigiochi residui (TapCiak, ecc.)
- Fase 3 Mercato: vendita serie/anime e distribuzione

### P2
- Sfida della Settimana (minigioco rotante con premi)

### P3
- Previsioni Festival
- Marketplace diritti TV/Anime
- Velion Mood, Chat Evolution, CinePass+Stripe
- Push notifications, Velion Livelli

## Credenziali Test
- Email: fandrex1@gmail.com
- Password: Fandrel2776
- Nickname: NeoMorpheus

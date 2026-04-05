# CineWorld Studio's — PRD

## Problema Originale
Simulatore di produzione cinematografica. L'utente gestisce uno studio, produce film, e partecipa a eventi live come "La Prima" (premiere).

## Architettura
- **Frontend**: React (Vite) + Tailwind + Shadcn/UI
- **Backend**: FastAPI + MongoDB
- **Auth**: JWT custom + Guest login

## Funzionalità Implementate

### Core Game
- Pipeline film a 6 step (layout cinematografico immersivo con animazioni CSS)
- Guest login
- Dashboard con sezioni: La Prima, Prossimamente, Ultimi Aggiornamenti
- CineBoard con classifiche: Film, Serie, Anime, TV Stations, **La Prima**

### La Prima (Completata — 2026-04-05)
- **Backend**: Endpoint enable/setup/live/active/rankings/cities in `routes/la_prima.py`
- **Frontend Dashboard**: `LaPrimaSection` con layout **orizzontale scrollabile**, card compatte da 140px
- **Popup TEMPLATE-BASED**: Usa `la-prima-template.jpg` come background, dati dinamici posizionati con CSS absolute %
  - Poster, titolo, città, timer, hype, spettatori attuali/totali, sinossi → overlay
  - Count-up animato, micro-jitter spettatori, reazioni pubblico random
  - Grafico trend bezier SVG con punti colorati
  - Ingresso cinematografico (scale 0.95→1, 320ms)
  - "LA PRIMA IN CORSO!", stats row, brand e OK! → dal template image
- **CineBoard La Prima**: 3 tab (Spettatori Live, Spettatori Totali, Media Mista)

### Fix e Ripristini (2026-04-05)
- Film "K" ripristinato nella collection `films` (era in `film_projects` completed ma mai inserito in `films`)
- Card La Prima compattata da full-width a 140px con scroll orizzontale

## Backlog Prioritizzato

### P0 (Completati)
- [x] Guest Login
- [x] Fix stati pipeline (sponsor, ciak)
- [x] Redesign FilmPipeline (6 step cinematografico)
- [x] Fix endpoint /api/coming-soon
- [x] La Prima: backend + Dashboard + CineBoard + Popup LIVE
- [x] La Prima: popup TEMPLATE-BASED (immagine template come sfondo)
- [x] La Prima: card compatta scrollabile orizzontalmente
- [x] Ripristino film K perso

### P1 (Prossimi)
- [ ] Modularizzazione server.py (17k+ righe)
- [ ] Sistema "Previsioni Festival"
- [ ] Marketplace TV/Anime rights

### P2
- [ ] Contest Page Mobile Layout (16+ segnalazioni)

### P3 (Futuro)
- [ ] Velion Mood Indicator
- [ ] Chat Evolution
- [ ] CinePass + Stripe
- [ ] Push notifications
- [ ] Velion Levels
- [ ] Eventi globali
- [ ] Guerre tra Major
- [ ] Velion AI Memory

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
- **Frontend Dashboard**: `LaPrimaSection` sopra "Prossimamente", card interattive con poster/stats
- **Popup cinematografico**: `LaPrimaPopup` con template dorato/nero
  - Badge "LIVE ORA" pulsante
  - Count-up animato su hype e spettatori
  - Micro-jitter spettatori ogni 5-8s con delta "+X spettatori negli ultimi minuti"
  - Reazioni pubblico random (12 frasi, rotazione ogni 8-12s)
  - Grafico trend bezier con punti colorati (oro=positivo, rosso=negativo)
  - Particelle CSS (3 tipi: rise, drift, twinkle)
  - Ingresso cinematografico (scale 0.94→1, 350ms)
  - Glow dorato sui bordi, tende rosse laterali, spotlight
  - Brand "CineWorld Studio's" in fondo
- **CineBoard La Prima**: 3 tab (Spettatori Live, Spettatori Totali, Media Mista)

## Backlog Prioritizzato

### P0 (Completati)
- [x] Guest Login
- [x] Fix stati pipeline (sponsor, ciak)
- [x] Redesign FilmPipeline (6 step cinematografico)
- [x] Fix endpoint /api/coming-soon
- [x] La Prima: backend + Dashboard + CineBoard + Popup LIVE

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

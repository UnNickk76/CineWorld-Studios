# CineWorld Studio's — PRD

## Problema Originale
Simulatore di produzione cinematografica. L'utente gestisce uno studio, produce film, e partecipa a eventi live come "La Prima" (premiere).

## Architettura
- **Frontend**: React (Vite) + Tailwind + Shadcn/UI
- **Backend**: FastAPI + MongoDB
- **Auth**: JWT custom + Guest login

## Funzionalità Implementate

### Core Game
- Pipeline film a 6 step (layout cinematografico immersivo)
- Guest login
- Dashboard con sezioni: La Prima, Prossimamente, Ultimi Aggiornamenti
- CineBoard con classifiche: Film, Serie, Anime, TV Stations, La Prima

### Content Template Unico (Completato — 2026-04-05)
- **Template-based fullscreen** per Film/Serie/Anime usando `content-template.jpg` come sfondo
- **Stato "IN PROGRAMMAZIONE"**: poster, titolo, genere, cinema, incassi, like, commenti, azioni, recensioni, trailer
- **Stato "COMING SOON"**: poster, titolo, genere, hype, sinossi (no incassi/spettatori)
- **Sub-popup cinematici** (stile oro/nero CSS, no template):
  - Commenti → popup completo con avatar, nomi, testo, rating
  - Sceneggiatura → popup testo
  - Cast & Crew → popup lista con avatar e ruoli
  - Trailer → popup (funzionalità in sviluppo)
- **Azioni proprietario**: Incassa Ora, Crea Stella, Boost Crew
- **Recensioni**: Variety, Empire, The Hollywood Reporter (generate da qualità/hype)
- **Integrato in** FilmDetail.jsx e SeriesDetail.jsx

### La Prima (Completata — 2026-04-05)
- Backend: endpoint enable/setup/live/active/rankings/cities
- Dashboard: LaPrimaSection con scroll orizzontale, card compatte 140px
- Popup TEMPLATE-BASED con dati live, animazioni CSS, reazioni pubblico
- CineBoard La Prima: 3 tab classifiche

## Backlog Prioritizzato

### P0 (Completati)
- [x] Guest Login
- [x] Fix stati pipeline (sponsor, ciak)
- [x] Redesign FilmPipeline (6 step cinematografico)
- [x] Fix endpoint /api/coming-soon
- [x] La Prima: backend + Dashboard + CineBoard + Popup LIVE
- [x] Content Template unico per Film/Serie/Anime
- [x] Sub-popup cinematici (Commenti, Sceneggiatura, Cast, Trailer)
- [x] Ripristino film K

### P1 (Prossimi)
- [ ] Modularizzazione server.py (17k+ righe)
- [ ] Sistema "Previsioni Festival"
- [ ] Marketplace TV/Anime rights

### P2
- [ ] Contest Page Mobile Layout (16+ segnalazioni)

### P3 (Futuro)
- [ ] Velion Mood Indicator, Chat Evolution, CinePass+Stripe
- [ ] Push notifications, Velion Levels, Eventi globali
- [ ] Guerre tra Major, Velion AI Memory

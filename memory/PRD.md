# CineWorld Studio's — PRD

## Pipeline V3 — Completa

### Step Finale — Riepilogo Costi
- Breakdown completo di ogni voce ($1M-$200M + 5-30CP max)
- Rientro sponsor sottratto
- "Vuoi rivedere qualcosa?" — 5-6 opzioni reali di risparmio
- "Ci pensa Velion" — auto-ottimizzazione 8-15%
- Conferma con "Confermi spendendo $X e XCP?"
- Velocizzazioni GIA scalate al momento (non nel totale)

### Fix Timer Restart
- Timer CIAK/FinalCut NON si riavviano tornando indietro
- Solo se `*_started_at` non esiste vengono creati

### File Calcoli Dedicati (9 totali)
- `calc_shooting.py` — Durata riprese
- `calc_film_duration.py` — Durata effettiva film
- `calc_finalcut.py` — Durata Final Cut + messaggi
- `calc_speedup.py` — Costi velocizzazione
- `calc_sponsors.py` — Sponsor proposals
- `calc_distribution.py` — Zone geografiche + costi
- `calc_defaults.py` — Auto-fill step saltati
- `calc_production_cost.py` — Costo totale + savings + Velion
- `calc_adv.py` — Logica campagne pubblicitarie (ADV)

### Film Detail V3 Modal (Post-Release) — Completato 16/04/2026
Layout identico al V2 "The Gratch" (ContentTemplate.jsx):
- Header "AL CINEMA" verde con pulsante X
- Poster thumbnail + Info box affiancati (titolo, studio, trama)
- Titolo grande giallo in Bebas Neue
- "una produzione [Studio]" in italico dorato
- Data bar: FILM | ⭐ score | ⏱ durata (bordo fuchsia)
- Status bar cyan glowing: "IN SALA - X giorni - Y rimanenti"
- "COSA NE PENSANO I GIORNALI" — VARIETY, EMPIRE, HOLLYWOOD R. (box verdi)
- "PUBBLICO & EVENTI" — bullet points celesti
- "SCENEGGIATURA COMPLETA" — sezione scrollabile
- 3 Pulsanti azione post-release:
  - LANCIA PUBBLICITA (ADV) — Panel con 6 piattaforme, selezione giorni
  - RITIRA DALLE SALE (arancione) — Conferma con warning
  - ELIMINA FILM (rosso) — Conferma con eliminazione permanente

### Bug Fix: NoneType Crash — Corretto 16/04/2026
- Risolto crash `quality_score: None` in economy.py, game_systems.py, server.py, virtual_audience.py, theater_life.py, film_engagement.py
- V3 films hanno quality_score=null, ora gestito con `or` fallback

## Backlog
- (P0) Motore calcolo qualita totale (`calc_quality.py`) — quality_score attualmente mockato come `null`
- (P1) CinemaStatsModal + ProducerProfileModal — collegare dati reali
- (P1) Fase 3 Mercato: vendita serie/anime
- (P2) Sfide settimanali (minigame rotanti con premi extra)
- (P2) Previsioni Festival e Marketplace diritti TV/Anime

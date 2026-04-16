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
- Header poster con gradient overlay e badge stato (AL CINEMA / FUORI SALA)
- Grid statistiche: Sala (giorni), Incasso, Likes, Cinema
- Barra qualità (se disponibile)
- Sezione Produttore con badge "TUO" per film di proprietà
- Cast & Crew espandibile con skill dettagliate per ogni membro
- Trama/Synopsis collassabile
- Zone distribuzione
- Sponsor con contributo
- Recensioni pubblico virtuale
- 3 Pulsanti azione post-release:
  - ADV (Pubblicità) — Panel con 6 piattaforme, selezione giorni, costo totale
  - Ritira dalle Sale (arancione) — Conferma con warning
  - Elimina Film (rosso) — Conferma con warning eliminazione permanente

### Bug Fix: Dashboard Batch Endpoint — Corretto 16/04/2026
- Risolto crash `quality_score: None` nei film V3 in economy.py
- Risolto crash cast V3 (dict vs list) in game_systems.py
- Risolto crash virtual-audience endpoint in server.py
- Risolto crash theater_life.py backfill con quality_score None

## Backlog
- (P0) Motore calcolo qualità totale (`calc_quality.py`) — quality_score attualmente mockato come `null`
- (P1) CinemaStatsModal + ProducerProfileModal — collegare dati reali
- (P1) Fase 3 Mercato: vendita serie/anime
- (P2) Sfide settimanali (minigame rotanti con premi extra)
- (P2) Previsioni Festival e Marketplace diritti TV/Anime

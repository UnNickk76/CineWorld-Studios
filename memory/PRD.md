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

### File Calcoli Dedicati (8 totali)
- `calc_shooting.py` — Durata riprese
- `calc_film_duration.py` — Durata effettiva film
- `calc_finalcut.py` — Durata Final Cut + messaggi
- `calc_speedup.py` — Costi velocizzazione
- `calc_sponsors.py` — Sponsor proposals
- `calc_distribution.py` — Zone geografiche + costi
- `calc_defaults.py` — Auto-fill step saltati
- `calc_production_cost.py` — Costo totale + savings + Velion

## Backlog
- (P0) Motore calcolo qualita totale
- (P1) CinemaStatsModal + ProducerProfileModal
- (P1) Fase 3 Mercato: vendita serie/anime

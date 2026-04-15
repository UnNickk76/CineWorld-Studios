# CineWorld Studio's — PRD

## Pipeline V3 — 10 Step Completi
```
IDEA → HYPE → CAST → PREP → CIAK → FINAL CUT → SPONSOR & MARKETING → LA PRIMA → DISTRIB. → USCITA
```

### Distribuzione — Sistema Zone Geografico
- **Mondiale**: $200K + 20CP (tutto)
- **Continenti**: Europa, Nord America, Sud America, Asia, Africa, Oceania
  - Bulk: 1=5CP, 2=8CP, 3=10CP, 4=12CP, 5=14CP, 6=16CP
- **Nazioni**: espandibili dentro ogni continente (12 EU, 3 NA, 5 SA, 10 Asia, 6 Africa, 2 Oceania)
  - Bulk: 1=3CP, 2-3=5CP, 4-6=6CP, 7-10=8CP, 11+=10CP
- **Citta**: 20-60 per continente (217 totali), spunta "Seleziona/Deseleziona tutte"
  - Bulk: 1-2=2CP, 3-5=4CP, 6-10=6CP, 11-20=8CP, 21+=10CP
- Combinabile: es. tutto Nord America + solo Roma
- Singole scelte = piu valore esponenziale
- Velion Intelligence Distribuzione (placeholder consigli)
- Durata programmazione in sala (7-60 giorni)
- File: `calc_distribution.py`

### File Calcoli
- `calc_shooting.py`, `calc_film_duration.py`, `calc_finalcut.py`
- `calc_speedup.py`, `calc_sponsors.py`, `calc_distribution.py`, `calc_defaults.py`

### RICORDARE A FINE STEP:
- Riepilogo costi pre-rilascio (1M-200M + 5-25 CP)
- Rientro sponsor sottratto dal costo totale
- File `calc_production_cost.py`

## Backlog
- (P0) Riepilogo costi pre-rilascio
- (P0) Motore calcolo qualita totale
- (P1) CinemaStatsModal + ProducerProfileModal

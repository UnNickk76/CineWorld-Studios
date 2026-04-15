# CineWorld Studio's — PRD

## Pipeline V3 — 10 Step con Timer Reali e Sponsor

### Flusso completo:
```
IDEA → HYPE → CAST → PREP → CIAK → FINAL CUT → SPONSOR & MARKETING → LA PRIMA → DISTRIB. → USCITA
```

### Sponsor (dentro Marketing step)
- 0-15 sponsor si presentano (basato su formato, hype, cast)
- Max 6 selezionabili, conferma con OK
- Soldi NON accreditati subito (anti-exploit scarta film)
- Rientro sponsor sottratto dal costo totale nel riepilogo pre-rilascio
- File: `calc_sponsors.py`

### Scarta Film
- Bottone in ogni step ESCLUSO Idea
- Conferma custom (non di sistema)
- Film va nel market esistente

### Timer Reali:
- CIAK: 1 giorno = 1 ora reale (3-40h)
- Final Cut: 3-48h

### Ricordare per fine step:
- Riepilogo costi pre-rilascio (1M-200M + 5-25 CP)
- Click possibile solo con fondi sufficienti
- Rientro sponsor sottratto dal costo
- File: `calc_production_cost.py` (da creare)

## File Calcoli Dedicati
- `calc_shooting.py` — Durata riprese
- `calc_film_duration.py` — Durata effettiva film
- `calc_finalcut.py` — Durata Final Cut + messaggi
- `calc_speedup.py` — Costi velocizzazione
- `calc_sponsors.py` — Sponsor proposals e offerte

## Backlog
- (P0) Riepilogo costi pre-rilascio + calc_production_cost.py
- (P0) Motore calcolo qualita totale
- (P1) CinemaStatsModal + ProducerProfileModal
- (P1) Fase 3 Mercato: vendita serie/anime

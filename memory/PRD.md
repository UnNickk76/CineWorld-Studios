# CineWorld Studio's — PRD

## Prodotto
Browser game gestionale cinematografico Full-Stack (FastAPI + React + MongoDB).

## Pipeline V3 — 10 Step con Timer Reali
```
IDEA → HYPE → CAST → PREP → CIAK → FINAL CUT → MARKETING → LA PRIMA → DISTRIB. → USCITA
```

### Timer Reali:
- **CIAK**: 1 giorno = 1 ora reale (3-40h)
- **Final Cut**: 3-48h basato su formato, genere, CGI/VFX, giorni riprese

### Final Cut — Post-Produzione
- Timer reale con countdown (ore/minuti/secondi)
- ~100 messaggi rotanti in *corsivo* durante il montaggio
- Durata effettiva film mostrata al completamento (header + sezione dedicata)
- Velocizzazioni a pagamento CP con costo decrescente

### Bottone Advance — FREEZATO in ogni step finche non completo

### File Calcoli Dedicati
- `calc_shooting.py` — Durata riprese (3-40 giorni)
- `calc_film_duration.py` — Durata effettiva film (minuti)
- `calc_finalcut.py` — Durata Final Cut (3-48h) + messaggi rotanti
- `calc_speedup.py` — Costi velocizzazione unificati

## Backlog
- (P0) Motore calcolo qualita totale
- (P1) CinemaStatsModal + ProducerProfileModal
- (P1) Fase 3 Mercato: vendita serie/anime
- (P2) Sfida della Settimana

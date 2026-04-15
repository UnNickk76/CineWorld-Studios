# CineWorld Studio's — PRD

## Prodotto
Browser game gestionale cinematografico Full-Stack (FastAPI + React + MongoDB).

## Pipeline V3 — 10 Step Visivi
```
IDEA → HYPE → CAST → PREP → CIAK → FINAL CUT → MARKETING → LA PRIMA → DISTRIB. → USCITA
```

### Bottone Advance — FREEZATO in ogni step finche non completo:
- IDEA: serve poster + screenplay
- HYPE: serve configurazione hype
- CAST: serve almeno un regista o attore
- PREP: serve formato film + conferma
- CIAK: serve timer completato (tempo reale)
- FINAL CUT: serve note montaggio
- MARKETING: serve conferma marketing
- LA PRIMA/DISTRIB: sempre passabile

### CIAK — Timer Reale
- 1 giorno di riprese = 1 ora reale
- Range: 3-40 giorni = 3-40 ore reali
- Countdown live (ore/minuti/secondi rimanenti)
- Barra progresso 0-100% basata su tempo reale
- Speedup riduce tempo reale rimanente (non simulato)
- Al completamento timer: bottone advance si sblocca

### File Calcoli Dedicati
- `/app/backend/utils/calc_shooting.py` — Durata riprese (3-40 giorni)
- `/app/backend/utils/calc_film_duration.py` — Durata effettiva film (minuti)
- `/app/backend/utils/calc_speedup.py` — Costi velocizzazione unificati

### Sistema Velocizzazione Unificato (tutti gli step)
- Costi base: 25%=10CP, 50%=15CP, 75%=20CP, 100%=25CP
- Costo diminuisce inversamente al progresso
- Per CIAK: riduce tempo reale rimanente

### Pre-Produzione — Formato Film
- Cortometraggio (25-40 min), Medio (50-80 min), Standard (90-120 min), Epico (130-180 min), Kolossal (150-240 min)

## Backlog
- (P0) Motore calcolo qualita totale
- (P1) CinemaStatsModal + ProducerProfileModal
- (P1) Fase 3 Mercato: vendita serie/anime
- (P2) Sfida della Settimana

## Integrazioni
- Emergent LLM Key (AI Poster, AI Screenplay)
- Stripe (Payments)

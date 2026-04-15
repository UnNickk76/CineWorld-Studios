# CineWorld Studio's — PRD

## Prodotto
Browser game gestionale cinematografico Full-Stack (FastAPI + React + MongoDB).

## Pipeline V3 — 10 Step Visivi
```
IDEA → HYPE → CAST → PREP → CIAK → FINAL CUT → MARKETING → LA PRIMA → DISTRIB. → USCITA
```

### IdeaPhase — Flusso Sequenziale con OK Checkpoint
- FASE 0: Titolo + Genere + Sottogeneri (max 3) + Pretrama (min 50 char) + Ambientazione → OK
- FASE 1: Locandina AI → OK (film entra in PROSSIMAMENTE dopo questo OK)
- FASE 2: Sceneggiatura AI/manuale → OK → Avanti HYPE si sblocca

### Hype — Barra 0-100% + Velocizzazioni a Pagamento
- Configura strategia (Sprint/Bilanciata/Costruzione) + durata
- Barra avanzamento 0-100% con progresso automatico
- Velocizza: costo CP decresce esponenzialmente col progresso

### Cast
- Auto-cast: 1 regista, 1 sceneggiatore, 5 attori, 1 compositore
- Ruoli: generico (default), protagonista, antagonista, Co Protagonista, supporto
- Click su nome mostra modal Skills

### Pre-Produzione
- **Formato Film**: Cortometraggio (25-40min), Medio (50-80min), Standard (90-120min), Epico (130-180min), Kolossal (150-240min)
- Attrezzature, CGI, VFX, Comparse
- Calcolo automatico giorni riprese (3-40 giorni)

### CIAK — Riprese
- Durata riprese calcolata (basata su formato, genere, cast, attrezzature)
- Barra progresso 0-100% con giorno attuale/totale
- Velocizzazioni a pagamento CP (stesso sistema Hype)

### Final Cut
- Note montaggio + avvio
- Barra progresso montaggio 0-100%
- **Durata effettiva film** mostrata al completamento
- Velocizzazioni a pagamento CP

### La Prima
- Se premiere: barra progresso + velocizzazioni a pagamento CP
- Se diretto: salta alla distribuzione

## File Calcoli Dedicati
- `/app/backend/utils/calc_shooting.py` — Durata riprese (3-40 giorni)
- `/app/backend/utils/calc_film_duration.py` — Durata effettiva film (minuti)
- `/app/backend/utils/calc_speedup.py` — Costi velocizzazione unificati

## Endpoint Chiave V3
- POST /api/pipeline-v3/films/{pid}/save-prep-full (accetta film_format, ritorna shooting_days)
- GET /api/pipeline-v3/films/{pid}/shooting-estimate
- GET /api/pipeline-v3/films/{pid}/film-duration
- POST /api/pipeline-v3/films/{pid}/speedup (costo CP da calc_speedup)

## Backlog
- (P0) Motore calcolo qualita totale in file dedicato
- (P1) CinemaStatsModal + ProducerProfileModal dati reali
- (P1) Fase 3 Mercato: vendita serie/anime
- (P2) Sfida della Settimana
- (P3) Previsioni Festival, Marketplace diritti TV/Anime

## Integrazioni
- Emergent LLM Key (AI Poster, AI Screenplay)
- Stripe (Payments)

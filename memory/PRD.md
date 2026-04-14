# CineWorld Studio's — PRD

## Prodotto
Browser game gestionale cinematografico Full-Stack (FastAPI + React + MongoDB).

## Pipeline V2 — 9 Step Visivi (SEMPRE visibili)
```
IDEA → HYPE → CAST → PREP → CIAK → FINAL CUT → MARKETING → LA PRIMA → USCITA
```

### Backend State Flow:
```
draft → idea → proposed → hype → casting → prep → shooting → postproduction → sponsorship → marketing → distribution → release_pending → released → completed
```

### Step Mapping (0-8):
0: IDEA | 1: HYPE | 2: CAST | 3: PREP | 4: CIAK | 5: FINAL CUT | 6: MARKETING | 7: LA PRIMA | 8: USCITA

### Marketing = Hub (step 6)
- Mostra pacchetti marketing
- Dopo conferma marketing: mostra scelta rilascio (La Prima / Diretto) come sub-phase
- Scelta salva `release_type` via `set-release-type` endpoint
- Pulsante "Prosegui alla Distribuzione" avanza a `distribution`

### Differenza La Prima vs Diretto
- La Prima: "Immediato" disabilitato nella distribuzione
- Diretto: "Immediato" disponibile

### Quality Score
- **Preview (frontend)**: `safeAverage()` — MAI salvata
- **Calcolo reale**: SOLO in `confirm-final-release`
- **Invisibile fino uscita**

## Endpoint Chiave
- POST /api/pipeline-v2/films/{pid}/save-marketing — Salva packages, NON avanza step
- POST /api/pipeline-v2/films/{pid}/set-release-type — Salva release_type, NON avanza step
- POST /api/pipeline-v2/films/{pid}/choose-premiere — marketing → distribution (release_type=premiere)
- POST /api/pipeline-v2/films/{pid}/choose-direct-release — marketing → distribution (release_type=direct)
- POST /api/pipeline-v2/films/{pid}/schedule-release — distribution → release_pending
- POST /api/pipeline-v2/films/{pid}/confirm-final-release — release_pending → released (calcolo reale)

## Backlog
- (P1) CinemaStatsModal + ProducerProfileModal
- (P1) Fase 3 Mercato: vendita serie/anime
- (P2) Sfida della Settimana
- (P3) Previsioni Festival, Marketplace diritti TV/Anime

## Integrazioni
- Emergent LLM Key (AI Avatar, Poster, Screenplay)
- Stripe (Payments)

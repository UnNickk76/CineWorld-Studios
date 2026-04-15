# CineWorld Studio's — PRD

## Prodotto
Browser game gestionale cinematografico Full-Stack (FastAPI + React + MongoDB).

## Pipeline V3 — 10 Step Visivi (SEMPRE visibili nello Stepper)
```
IDEA → HYPE → CAST → PREP → CIAK → FINAL CUT → MARKETING → LA PRIMA → DISTRIB. → USCITA
```

### Backend State Flow (V3):
```
idea → hype → cast → prep → ciak → finalcut → marketing → la_prima → distribution → release_pending → released
```

### Step Mapping (0-9):
0: IDEA | 1: HYPE | 2: CAST | 3: PREP | 4: CIAK | 5: FINAL CUT | 6: MARKETING | 7: LA PRIMA | 8: DISTRIB. | 9: USCITA

### IdeaPhase — Flusso Sequenziale con OK Checkpoint:
- FASE 0: Titolo + Genere + Sottogeneri (max 3 tag) + Pretrama (min 50 char) + Ambientazione → OK (giallo, frozen finche' incompleto)
- FASE 1: Locandina AI (genera da pretrama o prompt custom) → OK (frozen finche' no poster). Dopo OK locandina il film entra in PROSSIMAMENTE FILM nella dashboard.
- FASE 2: Sceneggiatura AI (1000-2000 char, scrollabile) oppure manuale (min 100 char) → OK (frozen finche' vuota)
- Dopo FASE 2 OK → bottone "Avanti HYPE" si sblocca

### Marketing = Hub (step 6)
- Mostra pacchetti marketing
- Scelta rilascio (La Prima / Diretto) come sub-phase
- Pulsante avanza a distribuzione

### La Prima (step 7)
- Se premiere: preparazione evento con velocizzazioni
- Se diretto: messaggio semplice, avanza alla distribuzione

### Quality Score
- Calcoli qualita' **in file separato** (NON nei componenti pipeline)
- **Invisibile fino uscita** — mostra "n.d." durante il pipeline

## Prossimamente Film (Dashboard)
- Film V3 con poster appaiono in "PROSSIMAMENTE FILM" dopo conferma OK locandina
- Badge stato colorato per pipeline_state (Idea=amber, Hype=orange, Cast=cyan, etc.)
- Card poster-style, scrollabili lateralmente, dal piu recente
- Tutti i player visibili

## Endpoint Chiave V3
- POST /api/pipeline-v3/films/create
- POST /api/pipeline-v3/films/{pid}/save-idea (accetta subgenres, locations)
- POST /api/pipeline-v3/films/{pid}/advance (next_state)
- POST /api/pipeline-v3/films/{pid}/generate-poster
- POST /api/pipeline-v3/films/{pid}/generate-screenplay (AI con Emergent LLM Key)
- POST /api/pipeline-v3/films/{pid}/confirm-release
- GET /api/coming-soon (include V3 films con poster)

## Architettura Frontend V3
- `PipelineV3.jsx` — Orchestratore principale
- `V3Shared.jsx` — Costanti, StepperBar, V3_STEPS (10 step con LA PRIMA)
- `IdeaPhase.jsx` — Flusso sequenziale (Titolo/Genere → Poster → Script)
- `CastPhase.jsx` — Selezione NPC attori
- `Phases.jsx` — Hype, Prep, Ciak, FinalCut, Marketing, LaPrima, Distribution, StepFinale
- `ComingSoonSection.jsx` — Dashboard sezione "Prossimamente" con badge colorati

## Architettura Backend V3
- `routes/pipeline_v3.py` — State machine, AI poster/screenplay, advance
- `routes/series_pipeline.py` — Include query V3 nel /coming-soon endpoint

## Backlog
- (P0) Motore calcolo qualita' in file dedicato (dopo 100% verifica UI)
- (P1) CinemaStatsModal + ProducerProfileModal — dati reali
- (P1) Fase 3 Mercato: vendita serie/anime
- (P2) Sfida della Settimana
- (P3) Previsioni Festival, Marketplace diritti TV/Anime

## Integrazioni
- Emergent LLM Key (AI Poster via OpenAI Image Gen, AI Screenplay via LlmChat)
- Stripe (Payments)

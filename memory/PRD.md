# CineWorld Studio's - PRD

## Problema Originale
Piattaforma di simulazione cinematografica (tycoon). I giocatori creano film, gestiscono cast, producono e rilasciano film nei cinema virtuali.

## Architettura
- Frontend: React + Tailwind + Shadcn UI
- Backend: FastAPI + MongoDB
- Integrazioni: Gemini Nano Banana (LLM), Stripe (Payments)

## Implementato

### Pipeline Film V2 (2026-04-08) - NEW
- Nuova pipeline completa con 9 macro-step: IDEA → HYPE → CAST → PREP → CIAK → FINAL CUT → MARKETING → LA PRIMA → USCITA
- State machine anti-bug con: pipeline_state, pipeline_substate, pipeline_ui_step
- Sistema lock (pipeline_locked) anti-race condition
- Snapshot/checkpoint ad ogni transizione (pipeline_history, pipeline_snapshots)
- Timer persistenti (pipeline_timers) per hype, riprese, post-produzione, premiere
- Metriche persistenti (pipeline_metrics) per hype_score, agency_interest, cast_quality
- Flags persistenti (pipeline_flags) per has_poster, has_screenplay, cast_locked, etc.
- 30 NPC Agencies con specializzazioni, reputazione, regione
- Agency waves durante hype (3 ondate di proposte)
- Strategia hype (sprint/bilanciata/costruzione_lenta) con impatto su agenzie e quality
- Speedup con micro-malus invisibili
- Marketing packages (5 livelli) + Sponsor selection
- La Prima con 15 citta e countdown
- Quality score finale: base deterministica (~65) + alchimia random (~±35) - speedup malus
- Backup legacy pipeline in /app/backend/feature_future_or_backup/

### Files Backend V2
- /app/backend/routes/pipeline_v2.py (State machine + tutti gli endpoint)
- /app/backend/server.py (Routing V2 registrato)

### Files Frontend V2
- /app/frontend/src/pages/PipelineV2.jsx (UI completa 9 fasi, mobile-first)
- /app/frontend/src/App.js (Routes /create, /pipeline-v2 -> PipelineV2)

### Fix Bug Critico: Film nel Limbo / Pipeline Infinita (2026-04-08)
- Root cause 1: scheduler_tasks.py VALID_FILM_STATUSES mancava stati italiani
- Root cause 2: admin_recover_all_films resettava film LIMBO indietro
- Fix: Force-release + stati aggiunti + dati retroattivi corretti

### Preview Read-Only Step Pipeline (2026-04-08)
- Step completati cliccabili nella barra stepper legacy
- Pannello read-only per ogni fase

### Minigiochi (precedente)
- CineDrive, SuperCine Pro, Flipper Pro, MatrixDodge con overlay PNG
- Contest giornaliero con 12 minigiochi random

## Backlog
### P0 (In Attesa)
- [ ] Integrazione ultimi 2 Minigiochi (in attesa codice utente)

### P1
- [ ] Fix bug nei singoli minigiochi (TapCiak etc.)
- [ ] Bilanciamento economia Solo mode
- [ ] Fix reward contest (14 step)

### P2
- [ ] Sfida della Settimana (minigioco rotante con premi extra)

### P3
- [ ] Previsioni Festival
- [ ] Marketplace TV/Anime rights
- [ ] Velion Mood, Chat Evolution, CinePass+Stripe, Push, Velion Levels

## Credenziali Test
- NeoMorpheus: fandrex1@gmail.com / Fandrel2776

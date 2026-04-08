# CineWorld Studio's - PRD

## Problema Originale
Piattaforma di simulazione cinematografica (tycoon). I giocatori creano film, gestiscono cast, producono e rilasciano film nei cinema virtuali.

## Architettura
- Frontend: React + Tailwind + Shadcn UI
- Backend: FastAPI + MongoDB
- Integrazioni: Gemini Nano Banana (LLM), Stripe (Payments)

## Implementato

### Pipeline Film V2 - BLINDATA (2026-04-08)
- Nuova pipeline completa con 9 macro-step: IDEA -> HYPE -> CAST -> PREP -> CIAK -> FINAL CUT -> MARKETING -> LA PRIMA -> USCITA
- State machine anti-bug con: pipeline_state, pipeline_substate, pipeline_ui_step
- Sistema lock (pipeline_locked) anti-race condition con stale-lock recovery automatico (30s)
- Idempotenza su TUTTI gli endpoint di transizione (double-click safe)
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
- Quality score finale: base deterministica (~65) + alchimia random (~+/-35) - speedup malus
- Fix pre_imdb_score: ora calcolato correttamente (era sempre 0 per key mismatch)
- Anti double-click nel frontend: richieste POST identiche bloccate se pendenti
- Admin: diagnose + force-unlock + force-unlock-all
- Backup legacy pipeline in /app/backend/feature_future_or_backup/
- Retrocompatibilita: film v1/legacy non toccati, query V2 filtrano per pipeline_version=2

### Blindature Applicate (2026-04-08)
1. Idempotenza backend: ogni endpoint di transizione gestisce silenziosamente le chiamate duplicate
2. Stale lock recovery: lock automaticamente rimosso dopo 30 secondi
3. Anti double-click frontend: Set() globale blocca POST concorrenti identici
4. Timer protection: ogni fase con timer verifica la scadenza prima di avanzare
5. Retrocompatibilita: separazione totale v1/v2 a livello di query DB

### Test Validati via Curl (2026-04-08)
- Flow completo create -> idea -> propose -> hype -> cast -> prep -> ciak -> finalcut -> marketing -> premiere -> release
- Idempotenza verificata su: propose, setup-hype, launch-hype, complete-hype, lock-cast, start-ciak, complete-ciak, complete-finalcut, save-sponsors, choose-premiere, choose-direct-release, setup-premiere, complete-premiere, release
- Timer blocking verificato (hype, shooting, postprod, premiere)
- Pre-IMDb scoring (risultato 6.6/10 corretto)
- Quality scoring (risultato 31-48 range corretto)
- Admin diagnose/force-unlock funzionanti
- Retrocompatibilita (5 film legacy non toccati)

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
- [ ] Integrazione Arena e Dashboard per Pipeline V2
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

# CineWorld Studio's - PRD

## Problema Originale
Piattaforma di simulazione cinematografica (tycoon). I giocatori creano film, gestiscono cast, producono e rilasciano film nei cinema virtuali.

## Architettura
- Frontend: React + Tailwind + Shadcn UI
- Backend: FastAPI + MongoDB
- Integrazioni: Gemini Nano Banana (LLM), Stripe (Payments)

## Implementato

### Pipeline Film V2 - BLINDATA (2026-04-08)
- State machine anti-bug con lock/snapshot/idempotenza
- 9 macro-step: IDEA -> HYPE -> CAST -> PREP -> CIAK -> FINAL CUT -> MARKETING -> LA PRIMA -> USCITA
- Chaos test 30/30 PASS (spam, refresh, timer edge, stale lock, multi-tab, retry)
- Board iniziale con card tratteggiata "Nuovo Film" + film in pipeline

### Sottogeneri Dinamici + Genere Storico (2026-04-08)
- Nuovo genere: "historical" (storico) con 10 sottogeneri
- 19 generi totali con 10 sottogeneri ciascuno (190 sottogeneri)
- Max 3 sottogeneri selezionabili via chips UI
- Impatto reale su:
  - Pre-IMDb: bonus sinergia (+1.5 max), malus clash (-1.5 max)
  - Quality Score: bonus sottogenere amplificato
  - Eventi Shooting: 12+ eventi specifici per sottogenere
  - Marketing: moltiplicatore affinity per sottogenere
  - Audience targeting: mapping sottogenere → target demografico
- STRONG_COMBOS: 30+ combinazioni forti (es: thriller+psicologico +1.2)
- WEAK_COMBOS: 12+ combinazioni deboli (es: comedy+tragico -0.8)
- Card board mostrano sottogeneri come mini-tag
- Retrocompatibilità: subgenres=[] per film esistenti

### Edit/Sblocco Step (2026-04-09)
- Icona Edit (pencil) sugli step completati nella StepperBar
- Contatore "X/3 modifiche" visibile nella UI
- Backend endpoint `POST /api/pipeline-v2/films/{pid}/edit-step`
- Rollback sicuro dello stato pipeline allo step selezionato
- Max 3 sblocchi totali per film (prima del rilascio)
- Step timer-based (CIAK, FINAL CUT, USCITA) non modificabili
- Snapshot e history tracciano ogni edit per audit
- Ricalcolo automatico Pre-IMDb quando si modificano i dati dell'IDEA

### Prossimamente V2 + Edit Step UX (2026-04-09)
- Film V2 con locandina visibili in "Prossimamente" con badge stato (Hype, Cast, ecc.)
- Edit Step: click step completato nella stepper → pagina read-only freezata
- Bottone matita "Modifica" + contatore X/3 + modale conferma Cineox+Velion
- Step timer-based (CIAK, FINAL CUT) non modificabili

## Backlog
### P0 (In Attesa)
- [ ] Integrazione ultimi 2 Minigiochi (in attesa codice utente)

### P1
- [ ] Integrazione Arena e Dashboard per Pipeline V2
- [ ] Fix bug nei singoli minigiochi (TapCiak etc.)

### P2
- [ ] Sfida della Settimana (minigioco rotante con premi extra)

### P3
- [ ] Previsioni Festival, Marketplace TV/Anime, Velion Mood, Chat Evolution, CinePass+Stripe, Push, Velion Levels

## Credenziali Test
- NeoMorpheus: fandrex1@gmail.com / Fandrel2776

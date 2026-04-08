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
- 19 generi totali con 10 sottogeneri ciascuno (190 sottogeneri)
- Max 3 sottogeneri selezionabili via chips UI
- Impatto reale su Pre-IMDb, Quality Score, Eventi Shooting, Marketing, Audience targeting
- STRONG_COMBOS/WEAK_COMBOS per sinergie/clash

### Edit/Sblocco Step (2026-04-09)
- Max 3 sblocchi totali per film, rollback sicuro, ricalcolo Pre-IMDb

### Prossimamente V2 + Dashboard (2026-04-09)
- Film V2 visibili in "Prossimamente" con badge stato

### Sistema Speedup 4 Livelli (2026-04-09)
- Costi dinamici basati sul timer rimanente (25/50/75/100%)

### Effetto Matrix + Hype Live (2026-04-09)
- Barre progresso live interpolate per Hype e Agenzie
- Effetto Matrix cinematografico nella fase Hype

### CineConfirm Modale (2026-04-09)
- Modale globale stile Cineox/Velion al posto di window.confirm

### Rivoluzione Casting (2026-04-09)
- NPC reali dal DB (24.200+ NPC), 8 skill per ruolo, limiti ruoli, fame tiers
- Proposte: 30 attori, 10 registi, 10 sceneggiatori, 8 compositori
- Refresh proposals, compatibilita genere, bonus/malus skill

### Job Periodico NPC Cast (2026-04-09)
- APScheduler job giornaliero (06:00 UTC) per generare nuovi NPC
- Fix campo `role_type` (era `type`) e `writer` (era `screenwriter`) per compatibilita Pipeline V2
- Refresh 5% pool ogni 12 giorni + generazione giornaliera 10-20 per tipo

## Backlog

### P1
- [ ] Integrazione Arena per film V2
- [ ] Fix minigiochi residui (TapCiak, ecc.) - da verificare se ci sono bug reali

### P2
- [ ] Sfida della Settimana (minigioco rotante con premi extra)

### P3
- [ ] Previsioni Festival
- [ ] Marketplace TV/Anime rights
- [ ] Velion Mood Indicator, Chat Evolution, CinePass+Stripe, Push notifications, Velion Livelli

## Credenziali Test
- NeoMorpheus: fandrex1@gmail.com / Fandrel2776

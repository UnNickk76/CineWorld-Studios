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

### Sottogeneri Dinamici + Genere Storico (2026-04-08)
- 19 generi con 10 sottogeneri ciascuno

### Edit/Sblocco Step (2026-04-09)
- Max 3 sblocchi totali per film

### Dashboard V2 + Speedup 4 Livelli + Hype Live (2026-04-09)

### CineConfirm Modale (2026-04-09)

### Rivoluzione Casting con NPC Reali (2026-04-09)
- 24.200+ NPC dal DB, 8 skill per ruolo, limiti ruoli, fame tiers

### Job Periodico NPC Cast (2026-04-09)
- APScheduler job giornaliero (06:00 UTC)

### SISTEMA CHIMICHE ATTORI (2026-04-09)
- calculate_chemistry() con 7 fattori + bonus collaborazione passata
- calculate_cast_chemistry() aggregazione tutte le coppie
- Endpoint GET /cast-chemistry: costo 1 credito, solo indicatori (no numeri)
- Integrato in: select-cast, lock-cast, complete-ciak (eventi), qualita finale
- Impatto: -15 a +15 punti qualita, eventi shooting dinamici
- UI: ChemistryPanel con verde/giallo/rosso, pallini per membro

### FIX UI Cast (2026-04-09)
- Genere: ♂ blu / ♀ rosa / ⚧ grigio (fix mapping male/female vs M/F)
- IMDb rating mostrato nelle proposal cards (formato X.X su scala 10)
- Chimica ridotta a 1 credito

## Backlog

### P1
- [ ] Integrazione Arena per film V2
- [ ] Fix minigiochi residui (TapCiak, ecc.)

### P2
- [ ] Sfida della Settimana (minigioco rotante con premi extra)

### P3
- [ ] Previsioni Festival
- [ ] Marketplace TV/Anime rights
- [ ] Velion Mood Indicator, Chat Evolution, CinePass+Stripe, Push notifications, Velion Livelli

## Credenziali Test
- NeoMorpheus: fandrex1@gmail.com / Fandrel2776

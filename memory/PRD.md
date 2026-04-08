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
- Fix campo role_type e writer per Pipeline V2

### SISTEMA CHIMICHE ATTORI (2026-04-09) - NUOVO
- Funzione `calculate_chemistry(actorA, actorB, genre, subgenres)`: score -100/+100
  - Basata su: compatibilita skill, gap fama, affinita genere/sottogenere, eta, nazionalita, stelle, personalita
- Funzione `calculate_cast_chemistry(cast_list)`: media pesata tutte le coppie
  - Include film passati insieme (bonus collaborazione dal DB)
- Endpoint `GET /films/{pid}/cast-chemistry`: costo 3 crediti, restituisce solo indicatori (no numeri)
- Integrato in: select-cast, lock-cast, complete-ciak (eventi), qualita finale
- Impatto gameplay:
  - Qualita film finale: -15 a +15 punti basati sulla chimica reale (sostituisce random)
  - Eventi shooting: litigi/abbandoni se chimica < -30, boost se > +40
  - Hype: boost extra con chimica alta
- UI: Pannello ChemistryPanel con indicatori verde/giallo/rosso
  - Pallino chimica per ogni membro del cast selezionato
  - Dettaglio coppie espandibile
  - Best/worst pair evidenziati

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

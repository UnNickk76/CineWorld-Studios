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

### Sottogeneri Dinamici + Genere Storico (2026-04-08)

### Edit/Sblocco Step (2026-04-09)

### Dashboard V2 + Speedup 4 Livelli + Hype Live (2026-04-09)

### CineConfirm Modale (2026-04-09)

### Rivoluzione Casting con NPC Reali (2026-04-09)

### Job Periodico NPC Cast (2026-04-09)

### SISTEMA CHIMICHE ATTORI (2026-04-09)
- 7 fattori + bonus collaborazione, costo 1 credito

### FIX UI Cast (2026-04-09)
- Genere colorizzato (blu/rosa), IMDb nelle card, stelline gialle

### SISTEMA RUOLI ATTORI (2026-04-09) - NUOVO
- Dropdown selezione ruolo: protagonista/co-protagonista/antagonista/supporto/cameo/generico
- Costo 2 crediti per assegnazione ruolo attore
- Bonus/malus basati su: ruolo x genere x skill x fama x stelle
- GENRE_ROLE_AFFINITY: ruoli ottimali per genere (es. antagonista bonus horror/thriller)
- Skill affinity per ruolo (protagonista->charisma, antagonista->emotional_depth)
- Fame interaction (star in cameo = hype gold, star in generico = malus)
- Impatto su: quality_bonus, hype_bonus, imdb_weight
- Integrato nella quality finale del film (+role_quality_total * 0.4)
- Cast selezionato sparisce dalla lista proposte
- Ruolo mostrato nel CastSlot UI (badge viola)

### FIX Pagina Contest Minigiochi (2026-04-09) - NUOVO
- Fix navbar che copriva il titolo: aggiunto pt-20 (80px top padding)
- Fix scroll bloccato: aggiunto pb-40 (160px bottom padding) per bottom nav
- Fix CinePass non accreditati: cambiato $inc da campo `credits` a `cinepass`
- Sistema sblocco temporale: 1 step extra ogni 4 ore automaticamente (calc_time_unlocked_step)
- Testo UI aggiornato da "crediti" a "CinePass" per consistenza
- Padding corretto anche nella vista gioco attivo (pt-20 pb-40)

### SISTEMA DISTRIBUZIONE USCITA V2 (2026-04-09) - NUOVO
- Scelta data di uscita: Immediato, 24h, 2-7 giorni (Immediato/24h freezati per film La Prima)
- Scelta zone di distribuzione: 14 zone raggruppate per continente + Mondiale
- Costi: fondi in-game + CinePass (1-5 CP per zona, 5 CP Mondiale)
- Hype multiplier variabile per data (bell curve: 3-4 giorni = ottimo, immediato = basso)
- Revenue multiplier basato su zone scelte (USA=x2, World=x3.5)
- Programmazione durante La Prima: configurabile ma rilascio bloccato fino a fine timer
- Rilascio differito: film va in "Prossimamente" con countdown
- StepperBar aggiornata: step USCITA cliccabile/animato durante premiere_live
- Backend: GET /release-zones, POST /schedule-release, rilascio usa schedule per calcolo revenue

### FIX StepperBar (2026-04-09)
- Aggiunto padding destro (pr-6) per evitare che l'ultimo step sia tagliato
- Step USCITA visibile e cliccabile durante premiere_live (allowScheduleStep + pulse animation)

## Backlog

### P1
- [ ] Fix minigiochi residui (TapCiak, ecc.)

### P2
- [ ] Sfida della Settimana (minigioco rotante con premi extra)

### P3
- [ ] Previsioni Festival
- [ ] Marketplace TV/Anime rights
- [ ] Velion Mood Indicator, Chat Evolution, CinePass+Stripe, Push notifications, Velion Livelli

## Credenziali Test
- NeoMorpheus: fandrex1@gmail.com / Fandrel2776

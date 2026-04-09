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

### RILASCIO CINEMATOGRAFICO ULTRA (2026-04-09) - NUOVO
- Riscrittura totale CinematicReleaseOverlay.jsx con 9 fasi in 6.5 secondi
- Flow: Blackout → Cinepresa viva → Proiettore acceso → Schermo cinema → Countdown vintage 3-2-1 → Locandina → Titoli → Flash fotografo → Exit
- Colore proiettore dinamico per genere (horror=rosso, comedy=oro, drama=blu, ecc.)
- Flag anti-replay: release_sequence_played=true nel DB, non riscatta su refresh
- Endpoint POST /mark-release-played per marcare sequenza vista
- Differenza La Prima (flash piu glamour) vs Cinema (piu pulito)
- CSS puro + JS leggero, zero librerie, GPU friendly
- Fallback: se locandina mancante, mostra titolo in gold su gradiente

### SISTEMA SERIE TV & ANIME (2026-04-09) - NUOVO
Backend:
- Campo content_type (film/serie_tv/anime) in creazione progetto
- Endpoint set-episodes (range 8-24, solo per serie/anime)
- Formula qualita: qualita_base * (1 - ((episodi - 8) * 0.02))
- Endpoint set-release-mode (binge/daily/weekly) — scelta definitiva non modificabile
- Generazione automatica lista episodi con date rilascio calcolate
- Endpoint get episodes con auto-unlock basato su tempo
- Endpoint new-season: eredita cast, fanbase, bonus/malus, departure dinamica
- Cast: max 50% modificabile, minimo 50% deve restare
- Season bonus/malus basato su qualita stagione precedente
Frontend:
- Selettore content_type nella creazione (Film/Serie TV/Anime)
- Slider episodi (8-24) con indicatore qualita percentuale
- Badge SERIE/ANIME nelle card del board + header film
- EpisodeManager: scelta modalita rilascio, griglia episodi con stato, progress bar
- Sezione Nuova Stagione con slider episodi e info departure/bonus
- Slider episodi pre-rilascio nella UscitaPhase

### FIX & COMPLETAMENTO Logica Stagioni (2026-04-09) - NUOVO
Backend:
- Fix: screenplay_weight ora moltiplica il bonus sceneggiatura nel calcolo qualità al rilascio
- Fix: franchise_fatigue ora riduce la qualità finale proporzionalmente (S3: -6%, S4: -12%, S5: -18%, cap -50%)
- Fix: Aggiunto check stato — new-season richiede pipeline_state='released'/'completed' (prima si poteva creare da draft)
- Fix: AI screenplay ora usa prev_screenplay_summary per continuità narrativa tra stagioni
- Formula qualità serie: base*sw → +alchemy → *ep_factor → +season_bonus → *(1-ff)

### TOOL MIGRAZIONE ADMIN V1→V2 (2026-04-09) - NUOVO
Backend (/app/backend/routes/admin_migration.py):
- GET /api/admin/migration/scan — Scansiona e classifica tutti i progetti
- GET /api/admin/migration/preview/{pid} — Anteprima migrazione con dati preservati/resettati
- POST /api/admin/migration/migrate/{pid} — Migrazione singola (con force_state e force_discard)
- POST /api/admin/migration/migrate-all — Batch migrazione tutti i progetti eligibili
- Categorie: A_COMPLETED, B_STUCK, C_SYSTEM, D_V2_STUCK, OK
- Preserva: cast, sceneggiatura, poster, locations, costi, hype
Frontend (Tab Migrazione in AdminPage.jsx):
- Tab "Migrazione" nel pannello admin
- Scansiona DB → categorie + summary cards
- Anteprima, Migra/Fix, Scarta, Force State per progetto
- Batch "Migra Tutti" per migrazione massiva
- Funziona su qualsiasi DB a cui l'app è connessa

### SISTEMA EPISODI COMPLETO (2026-04-09) - NUOVO
Backend (/app/backend/routes/pipeline_v2.py):
- Generazione ricca episodi UNA SOLA VOLTA con titolo, trama, tipo nascosto
- 5 tipi: normal, peak, filler, plot_twist, season_finale
- Ogni tipo modifica hype (+15 finale, +12 twist, +8 peak, -3 filler), audience (x1.8 finale, x1.5 twist), qualita
- Anime: piu peak, bonus audience su picchi. Serie TV: bonus audience continuita seconda meta
- Watch episode: calcola rating + audience + hype con trend dinamico
- Valutazione finale serie: media + trend (1a vs 2a meta) + peso finale
- Endpoint enrich per episodi vecchio formato
- Protezione: no ri-generazione, no doppio-watch, scelta modo irreversibile
Frontend (PipelineV2.jsx):
- EpisodeCard Netflix-style: titolo, trama, tipo icon, stato, data, rating, audience
- Progress bar doppia: rilascio (cyan) + visti (emerald)
- Stats card: rating medio, audience totale, hype, visti
- Bottone PlayCircle per guardare, Eye per gia visti
- Current episode highlight con barra accent colorata
- Enrich button per episodi vecchi formato
- Selector modalita (binge/daily/weekly) con icone e descrizioni

### CAST ANIME DEDICATO (2026-04-09) - NUOVO
Backend:
- Ruoli anime: animators (disegnatori, max 3) e voice_actors (doppiatori, max 5)
- Pesi qualita diversi: anime → dir 20%, animators 25%, voice_actors 20%, comp 10%, attori 8%
- Pesi serie_tv: dir 30%, attori 10% each, screenwriters 15%, comp 5%
- Proposte cast: anime genera proposte per animator e voice_actor da pool NPC esistenti
- Lock cast: anime richiede 1 regista + 1 disegnatore minimo (non 2 attori)
- Malus: -15% senza disegnatore, -10% senza doppiatori (anime only)
- Nuova stagione: eredita animators e voice_actors
Frontend:
- Tabs cast dinamici in base a content_type
- Anime mostra tabs: Registi, Sceneggiatori, Disegnatori, Doppiatori, Attori (opz.), Compositori
- Riepilogo cast mostra Disegnatore e Doppiatore con icone Palette e Megaphone

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

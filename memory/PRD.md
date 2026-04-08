# CineWorld Studio's — PRD

## Problema Originale
Sistema di produzione cinematografica con pipeline completa, PvP, infrastrutture, arena, guerre Major, e sistema minigiochi competitivo.

## Architettura
- **Frontend**: React + Tailwind + Shadcn/UI + Framer Motion
- **Backend**: FastAPI + MongoDB
- **Background**: `apscheduler` per loop economia

## Funzionalita Completate

### Core + Eventi + Infra + Arena + Guerra (DONE precedentemente)
### Data Integrity System (DONE)
### Sistema Minigiochi v3 + Refactoring (DONE)
### P1 + P2 Blocco Completo (DONE precedentemente)
### Unificazione Hub Minigiochi + Sfide (DONE - 2026-04-07)
### MATRIX DODGE — Minigioco Pro (DONE - 2026-04-07)
### Player Neo Premium Upgrade (DONE - 2026-04-07)
### AUTO CINEMATOGRAFICA — CineDrive Base + PRO (DONE - 2026-04-08)
- Engine canvas condiviso (`cineDriveEngine.js`): prospettiva semi-top, 6 palette neon/synthwave, auto dettagliata, 6 tipi ostacoli cinema, 4 bonus
- Base: 3 corsie, near miss, combo, shield, slowmo, countdown, game over
- PRO ASSURDA: 6 scenari rotanti, turbo bar, 5 eventi speciali, boss wave, star rating
- Backend: registrati `cine_drive` e `cine_drive_pro` in ARCADE_GAMES con titoli "Pilota Neon" e "Re della Strada"

### SUPERCINE — PRO ASSURDA (DONE - 2026-04-08)
- Platformer cinematografico epico, 7 zone tematiche, ~100 stelle, segreti, powerup
- Zone: Backlot Arcade, Set Fantasy, Stunt Pro, Camera Crane, Set Segreto, Studio Collapsato, Premiere Finish
- Player: Regista cartoon animato (corsa, salto, idle, megafono)
- Meccaniche: coyote time, jump buffer, salto variabile, checkpoint, invulnerabilità
- Ostacoli cinema: droni, boom mic, ciak ribelli, carrelli regia
- Powerup: Sprint, MegaCiak, Stella Premiere
- Rank: D → LEGENDARY DIRECTOR (basato su tempo, stelle, danni, segreti)
- Backend: registrato `supercine_pro` in ARCADE_GAMES con titolo "Legendary Director" @800
- HUD, intro, pausa, game over, risultati finali con rank e statistiche
- Controlli mobile: tasti direzionali + salto | Desktop: frecce + spazio

### Neo PNG Overlay (DONE - 2026-04-08)
- Immagini PNG caricate (neo_idle, neo_sx, neo_dx) in `/assets/matrix/`
- Overlay DOM su canvas con z-index 999/1000, direction detection, drop-shadow glow
- Applicato a MatrixDodgeGame e MatrixDodgeProGame

### CineDrive PNG Upgrade (DONE - 2026-04-08)
- PNG sfondo città e PNG auto integrate come layer DOM sopra canvas
- Ostacoli e bonus restano in canvas per leggibilità

## File Chiave
- `/app/frontend/src/components/games/matrixDodgeEngine.js` (Engine condiviso Matrix)
- `/app/frontend/src/components/games/MatrixDodgeGame.jsx` (Base)
- `/app/frontend/src/components/games/MatrixDodgeProGame.jsx` (PRO ASSURDA)
- `/app/frontend/src/components/games/matrixDodge.css` (Stili Matrix)
- `/app/frontend/src/components/games/cineDriveEngine.js` (Engine condiviso CineDrive)
- `/app/frontend/src/components/games/CineDriveGame.jsx` (Base)
- `/app/frontend/src/components/games/CineDriveProGame.jsx` (PRO ASSURDA)
- `/app/frontend/src/components/games/cineDrive.css` (Stili CineDrive)
- `/app/frontend/src/components/MiniGames.jsx` (Barrel export 16 giochi)
- `/app/frontend/src/pages/MiniGamesPage.jsx` (Hub 5-tab)
- `/app/frontend/src/pages/ContestPage.jsx` (14 step contest)
- `/app/backend/routes/minigames_arcade.py` (API 16 giochi)

### Fix Bug Critico: Film nel Limbo / Pipeline Infinita (DONE - 2026-04-08)
- Root cause 1: `scheduler_tasks.py` `VALID_FILM_STATUSES` non includeva `sponsor`, `ciak`, `produzione`, `prima`, `uscita` -> lo scheduler li classificava come "invalidi" e li resettava a `proposed`
- Root cause 2: `admin_recover_all_films` resettava i film LIMBO a stati precedenti (`pending_release`/`proposed`) causando loop infiniti, invece di rilasciarli
- Fix: Aggiunto stati mancanti allo scheduler + riscritto recovery per force-release in `films` collection
- Fix retroattivo: "Noccioline!" ripristinato a `produzione`, "Forest Gram" rilasciato forzatamente

### Preview Read-Only Step Pipeline (DONE - 2026-04-08)
- Step completati nella barra stepper ora cliccabili
- Pannello read-only per ogni fase (IDEA, HYPE, CAST, PRODUZIONE, LA PRIMA, USCITA)
- Toggle on/off + bottone X per chiudere

## Backlog
### P0 (In Attesa)
- [ ] Integrazione ultimi 2 Minigiochi (in attesa codice utente)

### P1 (Bug e Bilanciamento)
- [ ] Fix bug nei singoli minigiochi (TapCiak etc.)
- [ ] Bilanciamento economia Solo mode (hype, xp, funds, cooldown)
- [ ] Fix reward contest (14 step)

### P2
- [ ] Sfida della Settimana (minigioco rotante con premi extra)

### P3
- [ ] Sistema "Previsioni Festival"
- [ ] Marketplace TV/Anime rights
- [ ] Velion Mood, Chat Evolution, CinePass+Stripe, Push, Velion Levels

## Credenziali Test
- NeoMorpheus: fandrex1@gmail.com / Fandrel2776

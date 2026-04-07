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

#### Cambiamenti UI/UX
1. **MiniGamesPage** ora hub unico con **5 tab**:
   - Solo (14 minigiochi arcade)
   - VS Mini (sfide minigiochi 1v1)
   - **1v1 Film** (ChallengesPage embedded con prop `embedded`)
   - Classifiche (globale + per gioco)
   - Stats (summary + per gioco con titoli)

2. **Navbar top**: Icona cambiata da Swords a Gamepad2, punta a `/minigiochi`
3. **Bottom nav**: "Arena" sostituito con "Giochi" -> `/minigiochi`
4. **Dashboard**: Card "SFIDE" -> "Minigiochi + Sfide" con icona Gamepad2 cyan
5. **Menu hamburger**: Label aggiornata "Minigiochi + Sfide"
6. **Redirect**: `/challenges` e `/pvp-arena` redirectano a `/minigiochi`
7. **Fix mobile**: padding-top corretto (`pt-14`) per evitare overlap con navbar

### MATRIX DODGE — Minigioco Pro (DONE - 2026-04-07)

#### Due varianti implementate:
1. **Matrix Dodge** (Base) — Minigioco survival dodge in stile Matrix
   - Pioggia caratteri Matrix (katakana + hex), sfondo nero, glow verdi
   - Player: silhouette Neo disegnata in canvas (testa, corpo, mantello)
   - Proiettili con trail luminoso, diversi pattern (random, burst, wall_gap, diagonal, fan, ghost)
   - Near Miss detection con cooldown anti-exploit
   - Auto Bullet Time (barra caricata dai near miss)
   - Difficolta progressiva (velocita, spawn rate, pattern)
   - 3 HP con invulnerabilita temporanea post-hit
   - Screen shake e flash rosso su colpo
   - Vibrazione dispositivo su near miss/hit
   - Punteggio: survive + dodge + nearMiss + combo + bulletTime + noHitBonus
   - Capped a 999 (compatibile backend)

2. **Matrix Dodge PRO** (PRO ASSURDA) — Versione estesa
   - Tutto dalla base +
   - **DASH**: pulsante touch, 80px laterale, invulnerabilita breve, cooldown 2.5s
   - **Bullet Time Manuale**: pulsante touch, costa 50 dalla barra
   - **Afterimages**: cloni digitali durante combo alta e bullet time
   - **5 Eventi Speciali**: GLITCH STORM, RED PILL, SYSTEM BREAK, AGENT RUSH, CODE FRACTURE
   - **Elite Wave**: ondata intensificata dopo soglia punteggio/tempo
   - **WOW Finish**: "THE ONE?" con animazione se score >= 600
   - Contest mode: 60s (vs 45s della base)

#### Architettura tecnica:
- `matrixDodgeEngine.js` — costanti, helper, rendering, collision condivisi
- `MatrixDodgeGame.jsx` — componente base
- `MatrixDodgeProGame.jsx` — componente PRO
- `matrixDodge.css` — stili condivisi (animazioni, glow, shake, buttons, wow)

#### Integrazione:
- MiniGames.jsx barrel: export MatrixDodge, MatrixDodgePro
- MiniGamesPage.jsx: GAME_ICONS + GAME_COMPONENTS + Binary icon
- ContestPage.jsx: aggiunto agli STEPS (14 step totali)
- minigames_arcade.py: ARCADE_GAMES + GAME_TITLES
  - matrix_dodge: "Neo Digitale" (threshold 300)
  - matrix_dodge_pro: "THE ONE" (threshold 500)

#### ChallengesPage
- Aggiunta prop `embedded` per rimuovere padding esterno quando renderizzata in tab
- Backward-compatible: senza prop funziona come prima

## File Chiave
- `/app/frontend/src/pages/MiniGamesPage.jsx` (Hub 5-tab: Solo+VS+1v1Film+Top+Stats)
- `/app/frontend/src/pages/ChallengesPage.jsx` (1v1 Film, embedded-ready)
- `/app/frontend/src/pages/ContestPage.jsx` (14 step contest)
- `/app/frontend/src/pages/Dashboard.jsx` (Card aggiornata)
- `/app/frontend/src/App.js` (Navbar, bottom nav, routes, redirect)
- `/app/frontend/src/components/MiniGames.jsx` (Barrel export 14 giochi)
- `/app/frontend/src/components/games/MatrixDodgeGame.jsx` (Base)
- `/app/frontend/src/components/games/MatrixDodgeProGame.jsx` (PRO ASSURDA)
- `/app/frontend/src/components/games/matrixDodgeEngine.js` (Engine condiviso)
- `/app/frontend/src/components/games/matrixDodge.css` (Stili condivisi)
- `/app/backend/routes/minigames_arcade.py` (API complete, 14 giochi)

## Backlog
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

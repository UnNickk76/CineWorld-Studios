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

#### Player "The One" — Dettagli implementazione:
- Silhouette Neo dettagliata in canvas: testa glow, collo, spalle curve (quadraticCurveTo), torso giacca, risvolti, falde mantello (bezierCurveTo), braccia piegate al gomito, gambe separate
- **Glow dinamico**: intensita aumenta con combo e bullet time (min 6, max 22 shadowBlur)
- **Trail digitale**: ultime 3 posizioni renderate come ghost semitrasparenti (no shadowBlur per performance)
- **Breathing idle**: oscillazione scala via sin(time*2.5) * 0.012
- **Tilt movimento**: rotazione basata su velocita laterale, lerp fluido
- **Hit glitch**: distorsione translate+skew per 0.15s quando colpito
- **Energia digitale**: particelle random durante BT o combo >= 10
- **Colori adattivi**: verde (#00ff41) base, ciano (#00e5ff) durante BT, verde-ciano (#00ffcc) combo alta
- **Head highlight**: riflesso bianco sulla testa
- **Performance ottimizzata**: ghost trail salta effetti costosi (shadowBlur, highlight, lapels, panels, particles)

## File Chiave
- `/app/frontend/src/components/games/matrixDodgeEngine.js` (Engine condiviso, renderPlayer + renderPlayerTrail)
- `/app/frontend/src/components/games/MatrixDodgeGame.jsx` (Base)
- `/app/frontend/src/components/games/MatrixDodgeProGame.jsx` (PRO ASSURDA)
- `/app/frontend/src/components/games/matrixDodge.css` (Stili condivisi)
- `/app/frontend/src/components/MiniGames.jsx` (Barrel export 14 giochi)
- `/app/frontend/src/pages/MiniGamesPage.jsx` (Hub 5-tab)
- `/app/frontend/src/pages/ContestPage.jsx` (14 step contest)
- `/app/backend/routes/minigames_arcade.py` (API 14 giochi)

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

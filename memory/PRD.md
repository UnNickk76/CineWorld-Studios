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
   - Solo (12 minigiochi arcade)
   - VS Mini (sfide minigiochi 1v1)
   - **1v1 Film** (ChallengesPage embedded con prop `embedded`)
   - Classifiche (globale + per gioco)
   - Stats (summary + per gioco con titoli)

2. **Navbar top**: Icona cambiata da Swords a Gamepad2, punta a `/minigiochi`

3. **Bottom nav**: "Arena" sostituito con "Giochi" → `/minigiochi`

4. **Dashboard**: Card "SFIDE" → "Minigiochi + Sfide" con icona Gamepad2 cyan

5. **Menu hamburger**: Label aggiornata "Minigiochi + Sfide"

6. **Redirect**: `/challenges` e `/pvp-arena` redirectano a `/minigiochi`

7. **Fix mobile**: padding-top corretto (`pt-14`) per evitare overlap con navbar

#### ChallengesPage
- Aggiunta prop `embedded` per rimuovere padding esterno quando renderizzata in tab
- Backward-compatible: senza prop funziona come prima

## File Chiave
- `/app/frontend/src/pages/MiniGamesPage.jsx` (Hub 5-tab: Solo+VS+1v1Film+Top+Stats)
- `/app/frontend/src/pages/ChallengesPage.jsx` (1v1 Film, embedded-ready)
- `/app/frontend/src/pages/ContestPage.jsx` (12 step contest)
- `/app/frontend/src/pages/Dashboard.jsx` (Card aggiornata)
- `/app/frontend/src/App.js` (Navbar, bottom nav, routes, redirect)
- `/app/backend/routes/minigames_arcade.py` (API complete)

## Backlog
### P3
- [ ] Sistema "Previsioni Festival"
- [ ] Marketplace TV/Anime rights
- [ ] Velion Mood, Chat Evolution, CinePass+Stripe, Push, Velion Levels

## Credenziali Test
- NeoMorpheus: fandrex1@gmail.com / Fandrel2776
